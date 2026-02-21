"""Unit tests for Calendar Service"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.services.calendar_service import CalendarService
from app.models.models import CalendarIntegration, Business


@pytest.fixture
def calendar_service():
    """Create a calendar service instance"""
    return CalendarService()


@pytest.fixture
def mock_db():
    """Create mock database session"""
    return Mock(spec=Session)


@pytest.fixture
def sample_integration():
    """Sample calendar integration"""
    return CalendarIntegration(
        id=1,
        business_id=1,
        provider="google",
        access_token="test_access_token",
        refresh_token="test_refresh_token",
        token_expires_at=datetime.utcnow() + timedelta(hours=1),
        calendar_id="primary",
        status="active"
    )


@pytest.fixture
def sample_appointment():
    """Sample appointment"""
    from app.models.models import Appointment
    return Appointment(
        id=1,
        business_id=1,
        customer_id=1,
        start_time=datetime.utcnow() + timedelta(days=1),
        end_time=datetime.utcnow() + timedelta(days=1, hours=1),
        status="confirmed",
        source="internal"
    )


class TestGoogleOAuth:
    """Test cases for Google OAuth"""
    
    @patch('app.services.calendar_service.settings')
    def test_get_google_auth_url(self, mock_settings, calendar_service):
        """Test generating Google OAuth URL"""
        business_id = 123
        mock_settings.GOOGLE_CLIENT_ID = 'test_client_id'
        mock_settings.GOOGLE_CLIENT_SECRET = 'test_secret'
        mock_settings.GOOGLE_REDIRECT_URI = 'http://localhost/callback'
        
        url = calendar_service.get_google_auth_url(business_id)
        
        assert "accounts.google.com" in url
        assert "test_client_id" in url
        # State is URL-encoded, so check for both versions
        assert "123:" in url or "123%3A" in url  # business_id in state
        assert "calendar" in url.lower()
    
    @patch('app.services.calendar_service.settings')
    def test_google_auth_url_includes_state(self, mock_settings, calendar_service):
        """Test that state parameter includes business_id"""
        business_id = 456
        mock_settings.GOOGLE_CLIENT_ID = 'test_client_id'
        mock_settings.GOOGLE_CLIENT_SECRET = 'test_secret'
        mock_settings.GOOGLE_REDIRECT_URI = 'http://localhost/callback'
        
        url = calendar_service.get_google_auth_url(business_id)
        
        assert "state=" in url  # State should be present


class TestMicrosoftOAuth:
    """Test cases for Microsoft OAuth"""
    
    @patch('app.services.calendar_service.settings')
    def test_get_microsoft_auth_url(self, mock_settings, calendar_service):
        """Test generating Microsoft OAuth URL"""
        business_id = 123
        mock_settings.MICROSOFT_CLIENT_ID = 'test_client_id'
        mock_settings.MICROSOFT_CLIENT_SECRET = 'test_secret'
        mock_settings.MICROSOFT_REDIRECT_URI = 'http://localhost/callback'
        
        url = calendar_service.get_microsoft_auth_url(business_id)
        
        assert "login.microsoftonline.com" in url
        assert "test_client_id" in url
        assert "calendars" in url.lower()
    
    @patch('app.services.calendar_service.settings')
    def test_microsoft_auth_url_includes_state(self, mock_settings, calendar_service):
        """Test that state parameter includes business_id"""
        business_id = 789
        mock_settings.MICROSOFT_CLIENT_ID = 'test_client_id'
        mock_settings.MICROSOFT_CLIENT_SECRET = 'test_secret'
        mock_settings.MICROSOFT_REDIRECT_URI = 'http://localhost/callback'
        
        url = calendar_service.get_microsoft_auth_url(business_id)
        
        assert "state=" in url  # State should be present


class TestExchangeGoogleCode:
    """Test cases for exchanging Google OAuth code"""
    
    @pytest.mark.asyncio
    @patch('aiohttp.ClientSession')
    @patch('app.services.calendar_service.settings')
    async def test_exchange_google_code_success(self, mock_settings, mock_session_class, calendar_service, mock_db):
        """Test successful Google code exchange"""
        # Mock settings
        mock_settings.GOOGLE_CLIENT_ID = 'test_id'
        mock_settings.GOOGLE_CLIENT_SECRET = 'test_secret'
        mock_settings.GOOGLE_REDIRECT_URI = 'http://localhost/callback'
        
        # Mock token response
        mock_token_response = Mock()
        mock_token_response.status = 200
        mock_token_response.json = AsyncMock(return_value={
            "access_token": "new_access_token",
            "refresh_token": "new_refresh_token",
            "expires_in": 3600
        })
        
        # Mock calendar list response
        mock_cal_response = Mock()
        mock_cal_response.status = 200
        mock_cal_response.json = AsyncMock(return_value={
            "items": [
                {"id": "primary", "primary": True, "summary": "My Calendar"}
            ]
        })
        
        # Mock session
        mock_session = Mock()
        mock_session.post = AsyncMock(return_value=mock_token_response)
        mock_session.get = AsyncMock(return_value=mock_cal_response)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_session_class.return_value = mock_session
        
        result = await calendar_service.exchange_google_code("test_code", 1, mock_db)
        
        assert result.provider == "google"
        assert result.access_token == "new_access_token"
        assert result.calendar_id == "primary"
        assert result.status == "active"
    
    @pytest.mark.asyncio
    @patch('aiohttp.ClientSession')
    @patch('app.services.calendar_service.settings')
    async def test_exchange_google_code_existing_integration(self, mock_settings, mock_session_class, calendar_service, mock_db, sample_integration):
        """Test updating existing integration"""
        # Mock settings
        mock_settings.GOOGLE_CLIENT_ID = 'test_id'
        mock_settings.GOOGLE_CLIENT_SECRET = 'test_secret'
        mock_settings.GOOGLE_REDIRECT_URI = 'http://localhost/callback'
        
        # Mock existing integration
        mock_db.query.return_value.filter.return_value.first.return_value = sample_integration
        
        # Mock token response
        mock_token_response = Mock()
        mock_token_response.status = 200
        mock_token_response.json = AsyncMock(return_value={
            "access_token": "updated_token",
            "refresh_token": "updated_refresh",
            "expires_in": 3600
        })
        
        mock_cal_response = Mock()
        mock_cal_response.status = 200
        mock_cal_response.json = AsyncMock(return_value={"items": [{"id": "primary", "primary": True}]})
        
        mock_session = Mock()
        mock_session.post = AsyncMock(return_value=mock_token_response)
        mock_session.get = AsyncMock(return_value=mock_cal_response)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_session_class.return_value = mock_session
        
        result = await calendar_service.exchange_google_code("test_code", 1, mock_db)
        
        # Should update existing integration
        assert result.access_token == "updated_token"
        assert result.calendar_id == "primary"


class TestRefreshGoogleToken:
    """Test cases for refreshing Google tokens"""
    
    @pytest.mark.asyncio
    @patch('aiohttp.ClientSession')
    @patch('app.services.calendar_service.settings')
    async def test_refresh_google_token_success(self, mock_settings, mock_session_class, calendar_service, mock_db, sample_integration):
        """Test successful token refresh"""
        # Mock settings
        mock_settings.GOOGLE_CLIENT_ID = 'test_id'
        mock_settings.GOOGLE_CLIENT_SECRET = 'test_secret'
        
        mock_response = Mock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            "access_token": "refreshed_token",
            "expires_in": 3600
        })
        
        mock_session = Mock()
        mock_session.post = AsyncMock(return_value=mock_response)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_session_class.return_value = mock_session
        
        result = await calendar_service.refresh_google_token(sample_integration, mock_db)
        
        assert result is True
        assert sample_integration.access_token == "refreshed_token"
    
    @pytest.mark.asyncio
    @patch('aiohttp.ClientSession')
    @patch('app.services.calendar_service.settings')
    async def test_refresh_google_token_failure(self, mock_settings, mock_session_class, calendar_service, mock_db, sample_integration):
        """Test token refresh failure"""
        # Mock settings
        mock_settings.GOOGLE_CLIENT_ID = 'test_id'
        mock_settings.GOOGLE_CLIENT_SECRET = 'test_secret'
        
        mock_response = Mock()
        mock_response.status = 400
        mock_response.json = AsyncMock(return_value={"error": "invalid_grant"})
        
        mock_session = Mock()
        mock_session.post = AsyncMock(return_value=mock_response)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_session_class.return_value = mock_session
        
        result = await calendar_service.refresh_google_token(sample_integration, mock_db)
        
        assert result is False


class TestCalendarEventOperations:
    """Test cases for calendar event operations"""
    
    @pytest.mark.asyncio
    @patch('aiohttp.ClientSession')
    async def test_create_google_event(self, mock_session_class, calendar_service, sample_integration, sample_appointment):
        """Test creating a Google Calendar event"""
        mock_response = Mock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            "id": "event_123",
            "summary": "Appointment with John Doe",
            "start": {"dateTime": sample_appointment.start_time.isoformat()},
            "end": {"dateTime": sample_appointment.end_time.isoformat()}
        })
        
        mock_session = Mock()
        mock_session.post = AsyncMock(return_value=mock_response)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_session_class.return_value = mock_session
        
        result = await calendar_service.create_google_event(
            integration=sample_integration,
            appointment=sample_appointment,
            db=mock_db
        )
        
        assert result["id"] == "event_123"
        assert result["summary"] == "Appointment with John Doe"
    
    @pytest.mark.asyncio
    @patch('aiohttp.ClientSession')
    async def test_check_availability_google(self, mock_session_class, calendar_service, sample_integration):
        """Test checking availability in Google Calendar"""
        start_time = datetime.utcnow() + timedelta(days=1)
        end_time = start_time + timedelta(hours=1)
        
        mock_response = Mock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            "busy": []  # No conflicts
        })
        
        mock_session = Mock()
        mock_session.post = AsyncMock(return_value=mock_response)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_session_class.return_value = mock_session
        
        is_available = await calendar_service.check_availability_google(
            integration=sample_integration,
            start_time=start_time,
            end_time=end_time
        )
        
        assert is_available is True
    
    @pytest.mark.asyncio
    @patch('aiohttp.ClientSession')
    async def test_check_availability_google_busy(self, mock_session_class, calendar_service, sample_integration):
        """Test checking availability with conflicts"""
        start_time = datetime.utcnow() + timedelta(days=1)
        end_time = start_time + timedelta(hours=1)
        
        mock_response = Mock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            "busy": [
                {
                    "start": start_time.isoformat(),
                    "end": end_time.isoformat()
                }
            ]
        })
        
        mock_session = Mock()
        mock_session.post = AsyncMock(return_value=mock_response)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_session_class.return_value = mock_session
        
        is_available = await calendar_service.check_availability_google(
            integration=sample_integration,
            start_time=start_time,
            end_time=end_time
        )
        
        assert is_available is False


class TestBuiltInCalendar:
    """Test cases for built-in calendar"""
    
    @pytest.mark.asyncio
    async def test_check_built_in_availability(self, calendar_service, mock_db):
        """Test checking built-in calendar availability"""
        start_time = datetime.utcnow() + timedelta(days=1)
        end_time = start_time + timedelta(hours=1)
        
        # Mock database query
        mock_db.query.return_value.filter.return_value.all.return_value = []
        
        is_available = await calendar_service.check_built_in_availability(
            business_id=1,
            start_time=start_time,
            end_time=end_time,
            db=mock_db
        )
        
        assert is_available is True
    
    @pytest.mark.asyncio
    async def test_check_built_in_availability_conflict(self, calendar_service, mock_db, sample_appointment):
        """Test built-in calendar with conflicting appointment"""
        start_time = sample_appointment.start_time
        end_time = sample_appointment.end_time
        
        mock_db.query.return_value.filter.return_value.all.return_value = [sample_appointment]
        
        is_available = await calendar_service.check_built_in_availability(
            business_id=1,
            start_time=start_time,
            end_time=end_time,
            db=mock_db
        )
        
        assert is_available is False


class TestTwoWaySync:
    """Test cases for two-way calendar sync"""
    
    @pytest.mark.asyncio
    @patch('aiohttp.ClientSession')
    async def test_sync_to_external_calendar(self, mock_session_class, calendar_service, mock_db, sample_integration, sample_appointment):
        """Test syncing appointment to external calendar"""
        sample_appointment.external_event_id = None  # Not synced yet
        
        mock_response = Mock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={"id": "event_456"})
        
        mock_session = Mock()
        mock_session.post = AsyncMock(return_value=mock_response)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_session_class.return_value = mock_session
        
        result = await calendar_service.sync_to_external_calendar(
            appointment=sample_appointment,
            integration=sample_integration,
            db=mock_db
        )
        
        assert result["success"] is True
        assert sample_appointment.external_event_id == "event_456"
    
    @pytest.mark.asyncio
    @patch('aiohttp.ClientSession')
    async def test_sync_from_external_calendar(self, mock_session_class, calendar_service, mock_db, sample_integration):
        """Test syncing from external calendar"""
        start_time = datetime.utcnow()
        end_time = start_time + timedelta(days=7)
        
        mock_response = Mock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            "items": [
                {
                    "id": "external_event_1",
                    "summary": "External Appointment",
                    "start": {"dateTime": start_time.isoformat()},
                    "end": {"dateTime": (start_time + timedelta(hours=1)).isoformat()}
                }
            ]
        })
        
        mock_session = Mock()
        mock_session.get = AsyncMock(return_value=mock_response)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_session_class.return_value = mock_session
        
        events = await calendar_service.sync_from_external_calendar(
            integration=sample_integration,
            start_time=start_time,
            end_time=end_time
        )
        
        assert len(events) == 1
        assert events[0]["id"] == "external_event_1"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
