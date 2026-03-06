"""
Unit tests for OutboundCampaignService.

Tests cover:
- test_create_campaign: verify Campaign and CampaignCall records created
- test_resolve_targets: verify customer query with criteria filters
- test_start_pause_cancel_campaign: test state transitions
- test_time_window_enforcement: verify calls only execute within window
- test_get_outbound_stats: verify real stats calculation
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch, PropertyMock
from datetime import datetime, timezone, timedelta, time as dt_time

from app.services.outbound_campaign_service import OutboundCampaignService


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_campaign_mock(
    id=1,
    business_id=1,
    name="Test Campaign",
    campaign_type="follow_up",
    status="draft",
    briefing="Hello, this is a follow-up call.",
    target_criteria=None,
    schedule=None,
    max_concurrent_calls=3,
    max_retries=2,
    total_targets=0,
    calls_made=0,
    calls_answered=0,
    calls_successful=0,
    created_at=None,
    started_at=None,
    completed_at=None,
):
    """Return a MagicMock that behaves like a Campaign ORM instance."""
    campaign = MagicMock()
    campaign.id = id
    campaign.business_id = business_id
    campaign.name = name
    campaign.campaign_type = campaign_type
    campaign.status = status
    campaign.briefing = briefing
    campaign.target_criteria = target_criteria
    campaign.schedule = schedule or {"start_time": "09:00", "end_time": "17:00"}
    campaign.max_concurrent_calls = max_concurrent_calls
    campaign.max_retries = max_retries
    campaign.total_targets = total_targets
    campaign.calls_made = calls_made
    campaign.calls_answered = calls_answered
    campaign.calls_successful = calls_successful
    campaign.created_at = created_at or datetime(2026, 3, 1, tzinfo=timezone.utc)
    campaign.started_at = started_at
    campaign.completed_at = completed_at
    return campaign


def _make_customer_mock(id=1, business_id=1, phone="+1234567890", name="John Doe",
                        loyalty_tier="standard", churn_risk=0.3, last_interaction=None):
    """Return a MagicMock that behaves like a Customer ORM instance."""
    customer = MagicMock()
    customer.id = id
    customer.business_id = business_id
    customer.phone = phone
    customer.name = name
    customer.loyalty_tier = loyalty_tier
    customer.churn_risk = churn_risk
    customer.last_interaction = last_interaction
    return customer


def _make_campaign_call_mock(id=1, campaign_id=1, customer_id=1, status="pending",
                             attempt_number=1, outcome=None, outcome_details=None):
    """Return a MagicMock that behaves like a CampaignCall ORM instance."""
    cc = MagicMock()
    cc.id = id
    cc.campaign_id = campaign_id
    cc.customer_id = customer_id
    cc.status = status
    cc.attempt_number = attempt_number
    cc.outcome = outcome
    cc.outcome_details = outcome_details
    return cc


@pytest.fixture
def mock_db():
    """Mock database session with all common methods."""
    db = MagicMock()
    db.commit = MagicMock()
    db.refresh = MagicMock()
    db.add = MagicMock()
    db.flush = MagicMock()
    db.rollback = MagicMock()
    return db


@pytest.fixture
def service(mock_db):
    """Create an OutboundCampaignService with a mock DB."""
    return OutboundCampaignService(db=mock_db)


# ---------------------------------------------------------------------------
# test_create_campaign
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_create_campaign(service, mock_db):
    """create_campaign should persist a Campaign and CampaignCall records for each target."""

    # Mock _resolve_targets to return 2 customers
    customer1 = _make_customer_mock(id=10, phone="+1111111111")
    customer2 = _make_customer_mock(id=20, phone="+2222222222")

    with patch.object(service, "_resolve_targets", return_value=[customer1, customer2]):
        # Mock the Campaign constructor behavior via db.flush / db.refresh
        added_objects = []
        original_add = mock_db.add

        def track_add(obj):
            added_objects.append(obj)

        mock_db.add.side_effect = track_add

        # When flush is called, simulate setting campaign.id
        def fake_flush():
            for obj in added_objects:
                if not hasattr(obj, '_is_campaign_call'):
                    obj.id = 99  # simulate auto-generated ID

        mock_db.flush.side_effect = fake_flush

        with patch("app.services.outbound_campaign_service.Campaign") as MockCampaign, \
             patch("app.services.outbound_campaign_service.CampaignCall") as MockCampaignCall:

            campaign_instance = _make_campaign_mock(id=99, total_targets=2, name="Follow-up Campaign", campaign_type="follow_up", status="draft")
            MockCampaign.return_value = campaign_instance

            cc1 = _make_campaign_call_mock(id=1, campaign_id=99, customer_id=10)
            cc2 = _make_campaign_call_mock(id=2, campaign_id=99, customer_id=20)
            MockCampaignCall.side_effect = [cc1, cc2]

            result = await service.create_campaign(
                business_id=1,
                name="Follow-up Campaign",
                campaign_type="follow_up",
                briefing="Hello, following up on your visit.",
                target_criteria={"loyalty_tier": "standard"},
                max_concurrent=5,
                max_retries=3,
            )

    assert result["name"] == "Follow-up Campaign"
    assert result["campaign_type"] == "follow_up"
    assert result["status"] == "draft"
    assert result["total_targets"] == 2
    mock_db.commit.assert_called()


# ---------------------------------------------------------------------------
# test_resolve_targets
# ---------------------------------------------------------------------------

def test_resolve_targets_no_criteria(service, mock_db):
    """With no criteria, all customers for the business should be returned."""

    customer1 = _make_customer_mock(id=1)
    customer2 = _make_customer_mock(id=2)

    query_mock = MagicMock()
    mock_db.query.return_value = query_mock
    query_mock.filter.return_value = query_mock
    query_mock.all.return_value = [customer1, customer2]

    targets = service._resolve_targets(business_id=1, target_criteria=None)

    assert len(targets) == 2


def test_resolve_targets_with_customer_ids(service, mock_db):
    """With explicit customer_ids, only those customers should be returned."""

    customer1 = _make_customer_mock(id=10)

    query_mock = MagicMock()
    mock_db.query.return_value = query_mock
    query_mock.filter.return_value = query_mock
    query_mock.all.return_value = [customer1]

    targets = service._resolve_targets(
        business_id=1,
        target_criteria={"customer_ids": [10]}
    )

    assert len(targets) == 1
    assert targets[0].id == 10


def test_resolve_targets_with_loyalty_tier(service, mock_db):
    """With loyalty_tier criteria, only matching customers should be returned."""

    gold_customer = _make_customer_mock(id=5, loyalty_tier="gold")

    query_mock = MagicMock()
    mock_db.query.return_value = query_mock
    query_mock.filter.return_value = query_mock
    query_mock.all.return_value = [gold_customer]

    targets = service._resolve_targets(
        business_id=1,
        target_criteria={"loyalty_tier": "gold"}
    )

    assert len(targets) == 1
    assert targets[0].loyalty_tier == "gold"


# ---------------------------------------------------------------------------
# test_start_pause_cancel_campaign
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_start_campaign_from_draft(service, mock_db):
    """Starting a draft campaign should transition its status to 'running'."""

    campaign = _make_campaign_mock(id=1, status="draft")
    mock_db.query.return_value.filter.return_value.first.return_value = campaign

    result = await service.start_campaign(campaign_id=1)

    assert campaign.status == "running"
    assert result["status"] == "running"
    mock_db.commit.assert_called()


@pytest.mark.asyncio
async def test_start_campaign_from_paused(service, mock_db):
    """Starting a paused campaign should transition to 'running'."""

    campaign = _make_campaign_mock(id=1, status="paused")
    mock_db.query.return_value.filter.return_value.first.return_value = campaign

    result = await service.start_campaign(campaign_id=1)

    assert campaign.status == "running"
    assert result["status"] == "running"


@pytest.mark.asyncio
async def test_start_campaign_invalid_status(service, mock_db):
    """Starting a completed campaign should raise ValueError."""

    campaign = _make_campaign_mock(id=1, status="completed")
    mock_db.query.return_value.filter.return_value.first.return_value = campaign

    with pytest.raises(ValueError, match="Cannot start campaign"):
        await service.start_campaign(campaign_id=1)


@pytest.mark.asyncio
async def test_pause_campaign(service, mock_db):
    """Pausing a running campaign should transition to 'paused'."""

    campaign = _make_campaign_mock(id=1, status="running")
    mock_db.query.return_value.filter.return_value.first.return_value = campaign

    result = await service.pause_campaign(campaign_id=1)

    assert campaign.status == "paused"
    assert result["status"] == "paused"
    mock_db.commit.assert_called()


@pytest.mark.asyncio
async def test_pause_campaign_not_running(service, mock_db):
    """Pausing a non-running campaign should raise ValueError."""

    campaign = _make_campaign_mock(id=1, status="draft")
    mock_db.query.return_value.filter.return_value.first.return_value = campaign

    with pytest.raises(ValueError, match="Cannot pause campaign"):
        await service.pause_campaign(campaign_id=1)


@pytest.mark.asyncio
async def test_cancel_campaign(service, mock_db):
    """Cancelling a campaign should mark it cancelled and cancel all pending calls."""

    campaign = _make_campaign_mock(id=1, status="running")
    mock_db.query.return_value.filter.return_value.first.return_value = campaign

    pending_call_1 = _make_campaign_call_mock(id=10, status="pending")
    pending_call_2 = _make_campaign_call_mock(id=11, status="pending")

    # Set up the chained query for pending calls
    # First call to db.query is for campaign, second is for pending CampaignCalls
    campaign_query = MagicMock()
    campaign_query.filter.return_value.first.return_value = campaign

    calls_query = MagicMock()
    calls_query.filter.return_value = calls_query
    calls_query.all.return_value = [pending_call_1, pending_call_2]

    mock_db.query.side_effect = [campaign_query, calls_query]

    result = await service.cancel_campaign(campaign_id=1)

    assert campaign.status == "cancelled"
    assert result["calls_cancelled"] == 2
    assert pending_call_1.status == "failed"
    assert pending_call_1.outcome == "cancelled"
    assert pending_call_2.status == "failed"


@pytest.mark.asyncio
async def test_cancel_already_cancelled(service, mock_db):
    """Cancelling an already cancelled campaign should raise ValueError."""

    campaign = _make_campaign_mock(id=1, status="cancelled")
    mock_db.query.return_value.filter.return_value.first.return_value = campaign

    with pytest.raises(ValueError, match="already"):
        await service.cancel_campaign(campaign_id=1)


# ---------------------------------------------------------------------------
# test_time_window_enforcement
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_time_window_enforcement_outside_window(service, mock_db):
    """execute_campaign should skip execution when current time is outside the window."""

    campaign = _make_campaign_mock(
        id=1,
        status="running",
        schedule={"start_time": "09:00", "end_time": "10:00"},
    )
    mock_db.query.return_value.filter.return_value.first.return_value = campaign

    # Patch datetime to return a time outside the window (23:00 UTC)
    fake_now = datetime(2026, 3, 4, 23, 0, 0, tzinfo=timezone.utc)
    with patch("app.services.outbound_campaign_service.datetime") as mock_dt:
        mock_dt.now.return_value = fake_now
        mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)

        await service.execute_campaign(campaign_id=1)

    # The campaign should still be running (not completed), and no calls should be queried
    assert campaign.status == "running"


@pytest.mark.asyncio
async def test_time_window_enforcement_inside_window(service, mock_db):
    """execute_campaign should proceed when current time is inside the window."""

    campaign = _make_campaign_mock(
        id=1,
        status="running",
        schedule={"start_time": "08:00", "end_time": "18:00"},
    )

    # First query: get campaign
    campaign_query = MagicMock()
    campaign_query.filter.return_value.first.return_value = campaign

    # Second query: get pending calls (return empty to auto-complete)
    calls_query = MagicMock()
    calls_query.filter.return_value = calls_query
    calls_query.all.return_value = []  # No pending calls

    mock_db.query.side_effect = [campaign_query, calls_query]

    # Patch datetime to return a time inside the window (12:00 UTC)
    fake_now = datetime(2026, 3, 4, 12, 0, 0, tzinfo=timezone.utc)
    with patch("app.services.outbound_campaign_service.datetime") as mock_dt:
        mock_dt.now.return_value = fake_now
        mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)

        await service.execute_campaign(campaign_id=1)

    # With no pending calls, the campaign should be marked completed
    assert campaign.status == "completed"


@pytest.mark.asyncio
async def test_execute_campaign_not_running(service, mock_db):
    """execute_campaign should skip if campaign status is not 'running'."""

    campaign = _make_campaign_mock(id=1, status="paused")
    mock_db.query.return_value.filter.return_value.first.return_value = campaign

    await service.execute_campaign(campaign_id=1)

    # Status should remain unchanged
    assert campaign.status == "paused"


# ---------------------------------------------------------------------------
# test_get_outbound_stats
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_outbound_stats(service, mock_db):
    """get_outbound_stats should aggregate campaign and call metrics."""

    # We need to mock 5 separate db.query calls within get_outbound_stats.
    # Each call chain: db.query(func.count(...)).filter(...).scalar()

    # Build mock query chains for each of the 5 scalar queries
    def make_scalar_query(value):
        q = MagicMock()
        q.filter.return_value = q
        q.scalar.return_value = value
        return q

    # Also need to mock the subquery for campaign_ids
    subquery_mock = MagicMock()

    # total_campaigns = 5
    q1 = make_scalar_query(5)
    # active_campaigns = 2
    q2 = make_scalar_query(2)
    # campaign_ids subquery (not a scalar, but used internally)
    q_sub = MagicMock()
    q_sub.filter.return_value = q_sub
    q_sub.subquery.return_value = subquery_mock
    # total_outbound_calls = 20
    q3 = make_scalar_query(20)
    # successful_contacts = 15
    q4 = make_scalar_query(15)
    # successful_outcomes = 8
    q5 = make_scalar_query(8)

    # The method queries db.query multiple times. We need to set up the
    # side_effect to handle all calls including internal subquery calls.
    # The internal campaign_id subquery calls db.query(Campaign.id).filter(...)
    # which are used inside .in_() -- these don't need to return a scalar
    # but need to be valid mock objects.

    inner_campaign_q = MagicMock()
    inner_campaign_q.filter.return_value = inner_campaign_q

    mock_db.query.side_effect = [
        q1,              # total_campaigns
        q2,              # active_campaigns
        q_sub,           # campaign_ids_subquery (unused except structurally)
        q3,              # total_outbound_calls
        inner_campaign_q,  # inner query for Campaign.id
        q4,              # successful_contacts
        inner_campaign_q,  # inner query for Campaign.id
        q5,              # successful_outcomes
        inner_campaign_q,  # inner query for Campaign.id
    ]

    result = await service.get_outbound_stats(business_id=1)

    assert result["total_campaigns"] == 5
    assert result["active_campaigns"] == 2
    assert result["total_outbound_calls"] == 20
    assert result["successful_contacts"] == 15
    assert result["successful_outcomes"] == 8
    assert result["conversion_rate"] == round(8 / 20, 4)


@pytest.mark.asyncio
async def test_get_outbound_stats_empty(service, mock_db):
    """get_outbound_stats with no campaigns should return zeroes."""

    def make_scalar_query(value):
        q = MagicMock()
        q.filter.return_value = q
        q.scalar.return_value = value
        return q

    inner_campaign_q = MagicMock()
    inner_campaign_q.filter.return_value = inner_campaign_q

    q_sub = MagicMock()
    q_sub.filter.return_value = q_sub
    q_sub.subquery.return_value = MagicMock()

    mock_db.query.side_effect = [
        make_scalar_query(0),   # total_campaigns
        make_scalar_query(0),   # active_campaigns
        q_sub,                  # campaign_ids_subquery
        make_scalar_query(0),   # total_outbound_calls
        inner_campaign_q,
        make_scalar_query(0),   # successful_contacts
        inner_campaign_q,
        make_scalar_query(0),   # successful_outcomes
        inner_campaign_q,
    ]

    result = await service.get_outbound_stats(business_id=1)

    assert result["total_campaigns"] == 0
    assert result["conversion_rate"] == 0.0


# ---------------------------------------------------------------------------
# test_get_campaign_or_raise
# ---------------------------------------------------------------------------

def test_get_campaign_or_raise_found(service, mock_db):
    """_get_campaign_or_raise should return the campaign when it exists."""

    campaign = _make_campaign_mock(id=5)
    mock_db.query.return_value.filter.return_value.first.return_value = campaign

    result = service._get_campaign_or_raise(5)
    assert result.id == 5


def test_get_campaign_or_raise_not_found(service, mock_db):
    """_get_campaign_or_raise should raise ValueError when campaign not found."""

    mock_db.query.return_value.filter.return_value.first.return_value = None

    with pytest.raises(ValueError, match="Campaign 999 not found"):
        service._get_campaign_or_raise(999)
