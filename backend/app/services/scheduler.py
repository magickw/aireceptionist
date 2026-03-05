"""
Scheduler Service - APScheduler-based task scheduling for campaigns and reminders.
"""
import asyncio
from datetime import datetime, timezone, time as dt_time
from typing import Optional
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from app.core.logging import get_logger

logger = get_logger("scheduler")

_scheduler: Optional[AsyncIOScheduler] = None


async def _run_pending_campaigns():
    """Check for and execute pending campaigns every 5 minutes."""
    try:
        from app.db.session import SessionLocal
        from app.services.outbound_campaign_service import OutboundCampaignService

        db = SessionLocal()
        try:
            service = OutboundCampaignService(db)
            await service.process_pending_campaigns()
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Campaign runner error: {e}")


async def _run_appointment_reminders():
    """Daily 6pm job: trigger reminder calls for tomorrow's appointments."""
    try:
        from app.db.session import SessionLocal
        from app.models.models import Business

        db = SessionLocal()
        try:
            businesses = db.query(Business).filter(Business.status == "active").all()
            from app.services.outbound_campaign_service import OutboundCampaignService
            service = OutboundCampaignService(db)

            for business in businesses:
                try:
                    await service.trigger_appointment_reminders(business.id)
                except Exception as e:
                    logger.error(f"Reminder error for business {business.id}: {e}")
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Appointment reminder runner error: {e}")


def start_scheduler():
    """Initialize and start the APScheduler."""
    global _scheduler

    if _scheduler is not None:
        logger.warning("Scheduler already running")
        return

    _scheduler = AsyncIOScheduler()

    # Campaign runner: every 5 minutes
    _scheduler.add_job(
        _run_pending_campaigns,
        IntervalTrigger(minutes=5),
        id="campaign_runner",
        name="Process pending campaigns",
        replace_existing=True,
    )

    # Appointment reminders: daily at 6pm UTC
    _scheduler.add_job(
        _run_appointment_reminders,
        CronTrigger(hour=18, minute=0),
        id="appointment_reminders",
        name="Send appointment reminders",
        replace_existing=True,
    )

    _scheduler.start()
    logger.info("Scheduler started with campaign runner (5min) and reminder job (daily 6pm)")


def stop_scheduler():
    """Shutdown the scheduler."""
    global _scheduler
    if _scheduler:
        _scheduler.shutdown(wait=False)
        _scheduler = None
        logger.info("Scheduler stopped")
