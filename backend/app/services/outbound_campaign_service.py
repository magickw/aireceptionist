from typing import Dict, Any, List, Optional
from datetime import datetime, timezone, timedelta, time as dt_time
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from app.models.models import (
    Customer,
    Business,
    CallSession,
    Campaign,
    CampaignCall,
    Appointment,
)
from app.core.config import settings
from app.core.logging import get_logger
import asyncio
import urllib.parse

logger = get_logger("outbound_campaign")

# Default host used when building WebSocket/callback URLs for Twilio.
_DEFAULT_HOST = "receptium.onrender.com"


class OutboundCampaignService:
    """
    Service for managing proactive AI outreach campaigns.
    Allows businesses to trigger AI calls for appointment reminders,
    follow-ups, or promotions.
    """

    def __init__(self, db: Session):
        self.db = db

    # ------------------------------------------------------------------
    # Campaign CRUD
    # ------------------------------------------------------------------

    async def create_campaign(
        self,
        business_id: int,
        name: str,
        campaign_type: str,
        briefing: str,
        target_criteria: Optional[Dict[str, Any]] = None,
        schedule: Optional[Dict[str, Any]] = None,
        max_concurrent: int = 3,
        max_retries: int = 2,
    ) -> Dict[str, Any]:
        """Create a new outbound campaign, resolve targets, and persist CampaignCall rows."""

        campaign = Campaign(
            business_id=business_id,
            name=name,
            campaign_type=campaign_type,
            briefing=briefing,
            target_criteria=target_criteria,
            schedule=schedule,
            max_concurrent_calls=max_concurrent,
            max_retries=max_retries,
            status="draft",
        )
        self.db.add(campaign)
        self.db.flush()  # get campaign.id before creating calls

        # Resolve target customers --
        targets = self._resolve_targets(business_id, target_criteria)

        for customer in targets:
            campaign_call = CampaignCall(
                campaign_id=campaign.id,
                customer_id=customer.id,
                status="pending",
                attempt_number=1,
            )
            self.db.add(campaign_call)

        campaign.total_targets = len(targets)
        self.db.commit()
        self.db.refresh(campaign)

        logger.info(
            f"Campaign {campaign.id} created for business {business_id} "
            f"with {len(targets)} targets"
        )

        return {
            "id": campaign.id,
            "name": campaign.name,
            "campaign_type": campaign.campaign_type,
            "status": campaign.status,
            "total_targets": campaign.total_targets,
            "max_concurrent_calls": campaign.max_concurrent_calls,
            "max_retries": campaign.max_retries,
            "created_at": campaign.created_at.isoformat() if campaign.created_at else None,
        }

    async def start_campaign(self, campaign_id: int) -> Dict[str, Any]:
        """Transition a campaign to 'running' state."""

        campaign = self._get_campaign_or_raise(campaign_id)

        if campaign.status not in ("draft", "paused"):
            raise ValueError(
                f"Cannot start campaign in '{campaign.status}' status. "
                "Must be 'draft' or 'paused'."
            )

        campaign.status = "running"
        campaign.started_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(campaign)

        logger.info(f"Campaign {campaign_id} started")
        return {"id": campaign.id, "status": campaign.status}

    async def pause_campaign(self, campaign_id: int) -> Dict[str, Any]:
        """Pause a running campaign."""

        campaign = self._get_campaign_or_raise(campaign_id)

        if campaign.status != "running":
            raise ValueError(
                f"Cannot pause campaign in '{campaign.status}' status. "
                "Must be 'running'."
            )

        campaign.status = "paused"
        self.db.commit()
        self.db.refresh(campaign)

        logger.info(f"Campaign {campaign_id} paused")
        return {"id": campaign.id, "status": campaign.status}

    async def cancel_campaign(self, campaign_id: int) -> Dict[str, Any]:
        """Cancel a campaign and mark all pending calls as cancelled."""

        campaign = self._get_campaign_or_raise(campaign_id)

        if campaign.status in ("completed", "cancelled"):
            raise ValueError(f"Campaign is already '{campaign.status}'")

        campaign.status = "cancelled"

        # Cancel all pending calls within this campaign
        pending_calls = (
            self.db.query(CampaignCall)
            .filter(
                CampaignCall.campaign_id == campaign_id,
                CampaignCall.status == "pending",
            )
            .all()
        )
        cancelled_count = 0
        for cc in pending_calls:
            cc.status = "failed"
            cc.outcome = "cancelled"
            cc.outcome_details = "Campaign cancelled"
            cancelled_count += 1

        self.db.commit()

        logger.info(
            f"Campaign {campaign_id} cancelled, {cancelled_count} pending calls dropped"
        )
        return {
            "id": campaign.id,
            "status": campaign.status,
            "calls_cancelled": cancelled_count,
        }

    # ------------------------------------------------------------------
    # Campaign execution
    # ------------------------------------------------------------------

    async def execute_campaign(self, campaign_id: int) -> None:
        """
        Main execution loop for a campaign.
        Fetches pending calls, respects the configured time window, and
        limits concurrency with an asyncio.Semaphore.
        """

        campaign = self._get_campaign_or_raise(campaign_id)

        if campaign.status != "running":
            logger.warning(
                f"Skipping campaign {campaign_id} execution -- status is '{campaign.status}'"
            )
            return

        # ---- Time window enforcement ----
        schedule = campaign.schedule or {}
        start_str = schedule.get("start_time", "09:00")
        end_str = schedule.get("end_time", "17:00")

        start_h, start_m = (int(p) for p in start_str.split(":"))
        end_h, end_m = (int(p) for p in end_str.split(":"))

        now = datetime.now(timezone.utc)
        window_start = dt_time(start_h, start_m)
        window_end = dt_time(end_h, end_m)
        current_time = now.time()

        if not (window_start <= current_time <= window_end):
            logger.info(
                f"Campaign {campaign_id}: outside calling window "
                f"({start_str}-{end_str}), current UTC time {current_time.strftime('%H:%M')}"
            )
            return

        # ---- Gather pending calls ----
        pending_calls = (
            self.db.query(CampaignCall)
            .filter(
                CampaignCall.campaign_id == campaign_id,
                CampaignCall.status == "pending",
            )
            .all()
        )

        if not pending_calls:
            # All calls processed -- mark campaign complete
            campaign.status = "completed"
            campaign.completed_at = datetime.now(timezone.utc)
            self.db.commit()
            logger.info(f"Campaign {campaign_id} completed -- no more pending calls")
            return

        max_concurrent = campaign.max_concurrent_calls or 3
        semaphore = asyncio.Semaphore(max_concurrent)

        async def _wrapped(cc: CampaignCall):
            async with semaphore:
                await self._execute_single_call(cc, campaign)

        tasks = [_wrapped(cc) for cc in pending_calls]
        await asyncio.gather(*tasks, return_exceptions=True)

        # Refresh metrics after the batch
        self._refresh_campaign_metrics(campaign)
        self.db.commit()

    async def _execute_single_call(
        self, campaign_call: CampaignCall, campaign: Campaign
    ) -> None:
        """Initiate a single outbound call via Twilio REST API."""

        customer = (
            self.db.query(Customer)
            .filter(Customer.id == campaign_call.customer_id)
            .first()
        )
        if not customer or not customer.phone:
            campaign_call.status = "failed"
            campaign_call.outcome = "no_phone"
            campaign_call.outcome_details = "Customer has no phone number on file"
            self.db.commit()
            logger.warning(
                f"CampaignCall {campaign_call.id}: skipped -- customer has no phone"
            )
            return

        try:
            from twilio.rest import Client

            client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)

            host = _DEFAULT_HOST
            encoded_briefing = urllib.parse.quote(campaign.briefing or "", safe="")
            ws_url = (
                f"wss://{host}/api/twilio/ws"
                f"?business_id={campaign.business_id}"
                f"&campaign_id={campaign.id}"
                f"&campaign_call_id={campaign_call.id}"
                f"&briefing={encoded_briefing}"
            )

            twiml = (
                f'<Response><Connect><Stream url="{ws_url}"/></Connect></Response>'
            )

            campaign_call.status = "calling"
            campaign_call.called_at = datetime.now(timezone.utc)
            self.db.commit()

            call = client.calls.create(
                to=customer.phone,
                from_=settings.TWILIO_PHONE_NUMBER,
                twiml=twiml,
                status_callback=f"https://{host}/api/twilio/outbound-status",
                status_callback_event=["completed"],
            )

            campaign_call.call_session_id = call.sid
            campaign_call.status = "answered"
            self.db.commit()

            logger.info(
                f"CampaignCall {campaign_call.id}: call placed to {customer.phone} "
                f"(SID {call.sid})"
            )

        except ImportError:
            campaign_call.status = "failed"
            campaign_call.outcome = "error"
            campaign_call.outcome_details = "Twilio library not installed"
            self.db.commit()
            logger.error(
                f"CampaignCall {campaign_call.id}: Twilio library not available"
            )

        except Exception as exc:
            logger.error(
                f"CampaignCall {campaign_call.id}: call failed -- {exc}"
            )
            campaign_call.status = "failed"
            campaign_call.outcome = "error"
            campaign_call.outcome_details = str(exc)[:500]

            # Retry logic
            if campaign_call.attempt_number < (campaign.max_retries or 2):
                campaign_call.attempt_number += 1
                campaign_call.status = "pending"  # re-queue for next run
                logger.info(
                    f"CampaignCall {campaign_call.id}: will retry "
                    f"(attempt {campaign_call.attempt_number})"
                )

            self.db.commit()

    # ------------------------------------------------------------------
    # Target resolution
    # ------------------------------------------------------------------

    def _resolve_targets(
        self, business_id: int, target_criteria: Optional[Dict[str, Any]]
    ) -> List[Customer]:
        """
        Build a customer queryset filtered by optional target criteria:
        - customer_ids: explicit list of customer IDs
        - min_days_since_last_visit: customers who haven't interacted in N+ days
        - loyalty_tier: exact tier match (e.g. "standard", "silver")
        - churn_risk_above: churn_risk > threshold (0.0-1.0)
        """

        query = self.db.query(Customer).filter(
            Customer.business_id == business_id
        )

        if not target_criteria:
            return query.all()

        # Explicit customer list takes priority
        customer_ids = target_criteria.get("customer_ids")
        if customer_ids:
            query = query.filter(Customer.id.in_(customer_ids))
            return query.all()

        # Days since last interaction
        min_days = target_criteria.get("min_days_since_last_visit")
        if min_days is not None:
            cutoff = datetime.now(timezone.utc) - timedelta(days=int(min_days))
            query = query.filter(
                (Customer.last_interaction == None)  # noqa: E711
                | (Customer.last_interaction <= cutoff)
            )

        # Loyalty tier filter
        loyalty_tier = target_criteria.get("loyalty_tier")
        if loyalty_tier:
            query = query.filter(Customer.loyalty_tier == loyalty_tier)

        # Churn risk threshold
        churn_risk_above = target_criteria.get("churn_risk_above")
        if churn_risk_above is not None:
            query = query.filter(Customer.churn_risk > float(churn_risk_above))

        return query.all()

    # ------------------------------------------------------------------
    # Appointment reminders (auto-campaign)
    # ------------------------------------------------------------------

    async def trigger_appointment_reminders(
        self, business_id: int
    ) -> Dict[str, Any]:
        """
        Automatically create and start a campaign targeting customers with
        appointments scheduled for tomorrow.
        """

        tomorrow = datetime.now(timezone.utc).date() + timedelta(days=1)
        tomorrow_start = datetime.combine(tomorrow, dt_time.min).replace(
            tzinfo=timezone.utc
        )
        tomorrow_end = datetime.combine(tomorrow, dt_time.max).replace(
            tzinfo=timezone.utc
        )

        appointments = (
            self.db.query(Appointment)
            .filter(
                Appointment.business_id == business_id,
                Appointment.appointment_time >= tomorrow_start,
                Appointment.appointment_time <= tomorrow_end,
                Appointment.status == "scheduled",
                Appointment.reminder_sent == False,  # noqa: E712
            )
            .all()
        )

        if not appointments:
            logger.info(
                f"No pending appointments for business {business_id} tomorrow"
            )
            return {
                "campaign_type": "appointment_reminder",
                "target_date": tomorrow.isoformat(),
                "calls_triggered": 0,
            }

        # Collect unique customer IDs that have a phone number
        customer_ids: List[int] = []
        briefing_parts: List[str] = []
        for appt in appointments:
            if appt.customer_id and appt.customer_id not in customer_ids:
                customer_ids.append(appt.customer_id)
            time_str = appt.appointment_time.strftime("%I:%M %p")
            briefing_parts.append(
                f"- {appt.customer_name}: appointment at {time_str}"
                + (f" for {appt.service_type}" if appt.service_type else "")
            )

        briefing = (
            "You are calling to remind customers about their appointment tomorrow. "
            "Be friendly and confirm they can still make it. If they need to reschedule, "
            "offer to help. Appointment details:\n"
            + "\n".join(briefing_parts)
        )

        # Create the campaign
        campaign_data = await self.create_campaign(
            business_id=business_id,
            name=f"Appointment Reminders - {tomorrow.isoformat()}",
            campaign_type="appointment_reminder",
            briefing=briefing,
            target_criteria={"customer_ids": customer_ids},
            schedule={"start_time": "09:00", "end_time": "17:00"},
        )

        # Auto-start
        await self.start_campaign(campaign_data["id"])

        # Mark appointments as reminded
        for appt in appointments:
            appt.reminder_sent = True
        self.db.commit()

        logger.info(
            f"Business {business_id}: appointment reminder campaign "
            f"{campaign_data['id']} created with {len(customer_ids)} targets"
        )

        return {
            "campaign_type": "appointment_reminder",
            "target_date": tomorrow.isoformat(),
            "calls_triggered": len(customer_ids),
            "campaign_id": campaign_data["id"],
        }

    # ------------------------------------------------------------------
    # Scheduler entry point
    # ------------------------------------------------------------------

    async def process_pending_campaigns(self) -> None:
        """
        Called periodically by the scheduler.
        Finds all campaigns in 'running' status and executes them.
        """

        running_campaigns = (
            self.db.query(Campaign)
            .filter(Campaign.status == "running")
            .all()
        )

        if not running_campaigns:
            return

        logger.info(
            f"Processing {len(running_campaigns)} running campaign(s)"
        )

        for campaign in running_campaigns:
            try:
                await self.execute_campaign(campaign.id)
            except Exception as exc:
                logger.error(
                    f"Error executing campaign {campaign.id}: {exc}"
                )

    # ------------------------------------------------------------------
    # Read helpers
    # ------------------------------------------------------------------

    async def get_campaign_details(
        self, campaign_id: int
    ) -> Dict[str, Any]:
        """Return full campaign details including call counts by status."""

        campaign = self._get_campaign_or_raise(campaign_id)

        # Aggregate call counts by status
        status_counts_raw = (
            self.db.query(CampaignCall.status, func.count(CampaignCall.id))
            .filter(CampaignCall.campaign_id == campaign_id)
            .group_by(CampaignCall.status)
            .all()
        )
        calls_by_status: Dict[str, int] = {
            status: count for status, count in status_counts_raw
        }

        return {
            "id": campaign.id,
            "business_id": campaign.business_id,
            "name": campaign.name,
            "campaign_type": campaign.campaign_type,
            "status": campaign.status,
            "briefing": campaign.briefing,
            "target_criteria": campaign.target_criteria,
            "schedule": campaign.schedule,
            "max_concurrent_calls": campaign.max_concurrent_calls,
            "max_retries": campaign.max_retries,
            "total_targets": campaign.total_targets,
            "calls_made": campaign.calls_made,
            "calls_answered": campaign.calls_answered,
            "calls_successful": campaign.calls_successful,
            "calls_by_status": calls_by_status,
            "started_at": campaign.started_at.isoformat() if campaign.started_at else None,
            "completed_at": campaign.completed_at.isoformat() if campaign.completed_at else None,
            "created_at": campaign.created_at.isoformat() if campaign.created_at else None,
        }

    async def get_outbound_stats(
        self, business_id: int
    ) -> Dict[str, Any]:
        """Aggregate real outbound statistics from campaigns and calls."""

        # Total campaigns
        total_campaigns = (
            self.db.query(func.count(Campaign.id))
            .filter(Campaign.business_id == business_id)
            .scalar()
        ) or 0

        # Active (running) campaigns
        active_campaigns = (
            self.db.query(func.count(Campaign.id))
            .filter(
                Campaign.business_id == business_id,
                Campaign.status == "running",
            )
            .scalar()
        ) or 0

        # Total outbound calls placed (via CampaignCall)
        campaign_ids_subquery = (
            self.db.query(Campaign.id)
            .filter(Campaign.business_id == business_id)
            .subquery()
        )

        total_outbound_calls = (
            self.db.query(func.count(CampaignCall.id))
            .filter(CampaignCall.campaign_id.in_(
                self.db.query(Campaign.id).filter(
                    Campaign.business_id == business_id
                )
            ))
            .scalar()
        ) or 0

        # Calls that were answered
        successful_contacts = (
            self.db.query(func.count(CampaignCall.id))
            .filter(
                CampaignCall.campaign_id.in_(
                    self.db.query(Campaign.id).filter(
                        Campaign.business_id == business_id
                    )
                ),
                CampaignCall.status.in_(["answered", "completed"]),
            )
            .scalar()
        ) or 0

        # Calls with a positive outcome
        successful_outcomes = (
            self.db.query(func.count(CampaignCall.id))
            .filter(
                CampaignCall.campaign_id.in_(
                    self.db.query(Campaign.id).filter(
                        Campaign.business_id == business_id
                    )
                ),
                CampaignCall.outcome.in_(["confirmed", "callback_requested"]),
            )
            .scalar()
        ) or 0

        conversion_rate = (
            round(successful_outcomes / total_outbound_calls, 4)
            if total_outbound_calls > 0
            else 0.0
        )

        return {
            "total_campaigns": total_campaigns,
            "active_campaigns": active_campaigns,
            "total_outbound_calls": total_outbound_calls,
            "successful_contacts": successful_contacts,
            "successful_outcomes": successful_outcomes,
            "conversion_rate": conversion_rate,
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_campaign_or_raise(self, campaign_id: int) -> Campaign:
        """Fetch a campaign by ID or raise ValueError."""

        campaign = (
            self.db.query(Campaign).filter(Campaign.id == campaign_id).first()
        )
        if not campaign:
            raise ValueError(f"Campaign {campaign_id} not found")
        return campaign

    def _refresh_campaign_metrics(self, campaign: Campaign) -> None:
        """Re-compute aggregate counters on the Campaign row from CampaignCall data."""

        rows = (
            self.db.query(CampaignCall.status, func.count(CampaignCall.id))
            .filter(CampaignCall.campaign_id == campaign.id)
            .group_by(CampaignCall.status)
            .all()
        )
        counts: Dict[str, int] = {status: cnt for status, cnt in rows}

        campaign.calls_made = sum(
            counts.get(s, 0)
            for s in ("calling", "answered", "no_answer", "failed", "completed")
        )
        campaign.calls_answered = sum(
            counts.get(s, 0) for s in ("answered", "completed")
        )
        campaign.calls_successful = counts.get("completed", 0)
