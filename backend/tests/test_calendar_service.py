"""Unit tests for Calendar Service - Simplified and Fixed"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.services.calendar_service import CalendarService
from app.models.models import CalendarIntegration


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


class MockAiohttpResponse:
    """Mock aiohttp response with async context manager support"""
    def __init__(self, status, json_data):
        self.status = status
        self._json_data = json_data
    
    async def json(self):
        return self._json_data
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, *args):
        pass


class TestGoogleOAuth:
    """Test cases for Google OAuth"""
    
    def test_get_google_auth_url(self, calendar_service):
        """Test generating Google OAuth URL"""
        business_id = 123
        
        # Patch instance attributes
        calendar_service.GOOGLE_CLIENT_ID = 'test_client_id'
        calendar_service.GOOGLE_CLIENT_SECRET = 'test_secret'
        calendar_service.GOOGLE_REDIRECT_URI = 'http://localhost/callback'
        
        url = calendar_service.get_google_auth_url(business_id)
        
        assert "accounts.google.com" in url
        assert "test_client_id" in url
        assert "123:" in url or "123%3A" in url
        assert "calendar" in url.lower()
    
    def test_google_auth_url_includes_state(self, calendar_service):
        """Test that state parameter includes business_id"""
        business_id = 456
        
        # Patch instance attributes
        calendar_service.GOOGLE_CLIENT_ID = 'test_client_id'
        calendar_service.GOOGLE_CLIENT_SECRET = 'test_secret'
        calendar_service.GOOGLE_REDIRECT_URI = 'http://localhost/callback'
        
        url = calendar_service.get_google_auth_url(business_id)
        
        assert "state=" in url


class TestMicrosoftOAuth:
    """Test cases for Microsoft OAuth"""
    
    def test_get_microsoft_auth_url(self, calendar_service):
        """Test generating Microsoft OAuth URL"""
        business_id = 123
        
        # Patch instance attributes
        calendar_service.MICROSOFT_CLIENT_ID = 'test_client_id'
        calendar_service.MICROSOFT_CLIENT_SECRET = 'test_secret'
        calendar_service.MICROSOFT_REDIRECT_URI = 'http://localhost/callback'
        
        url = calendar_service.get_microsoft_auth_url(business_id)
        
        assert "login.microsoftonline.com" in url
        assert "test_client_id" in url
        assert "calendars" in url.lower()
    
    def test_microsoft_auth_url_includes_state(self, calendar_service):
        """Test that state parameter includes business_id"""
        business_id = 789
        
        # Patch instance attributes
        calendar_service.MICROSOFT_CLIENT_ID = 'test_client_id'
        calendar_service.MICROSOFT_CLIENT_SECRET = 'test_secret'
        calendar_service.MICROSOFT_REDIRECT_URI = 'http://localhost/callback'
        
        url = calendar_service.get_microsoft_auth_url(business_id)
        
        assert "state=" in url


class TestCheckAvailability:
    """Test cases for checking availability"""
    
    @pytest.mark.asyncio
    @patch('aiohttp.ClientSession')
    async def test_check_availability_free(self, mock_session_class, calendar_service, sample_integration):
        """Test checking availability when slot is free"""
        start_time = datetime.utcnow() + timedelta(days=1)
        end_time = start_time + timedelta(hours=1)
        
        # Mock response
        mock_response = MockAiohttpResponse(
            status=200,
            json_data={"busy": []}
        )
        
        # Mock session
        mock_session = AsyncMock()
        mock_session.get = AsyncMock(return_value=mock_response)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        
        # Mock ClientSession
        mock_session_instance = AsyncMock()
        mock_session_instance.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session_instance.__aexit__ = AsyncMock(return_value=None)
        mock_session_instance.get = AsyncMock(return_value=mock_response)
        
        mock_session_class.return_value = mock_session_instance
        
        is_available = await calendar_service.check_availability(
            integration=sample_integration,
            start_time=start_time,
            end_time=end_time
        )
        
        assert is_available is True
    
    @pytest.mark.asyncio
    @patch('aiohttp.ClientSession')
    async def test_check_availability_busy(self, mock_session_class, calendar_service, sample_integration):
        """Test checking availability when slot is busy"""
        start_time = datetime.utcnow() + timedelta(days=1)
        end_time = start_time + timedelta(hours=1)
        
        # Mock response
        mock_response = MockAiohttpResponse(
            status=200,
            json_data={
                "busy": [
                    {
                        "start": start_time.isoformat(),
                        "end": end_time.isoformat()
                    }
                ]
            }
        )
        
        # Mock session
        mock_session = AsyncMock()
        mock_session.get = AsyncMock(return_value=mock_response)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        
        # Mock ClientSession
        mock_session_instance = AsyncMock()
        mock_session_instance.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session_instance.__aexit__ = AsyncMock(return_value=None)
        mock_session_instance.get = AsyncMock(return_value=mock_response)
        
        mock_session_class.return_value = mock_session_instance
        
        is_available = await calendar_service.check_availability(
            integration=sample_integration,
            start_time=start_time,
            end_time=end_time
        )
        
        assert is_available is False


class TestCalendarEventOperations:
    """Test cases for calendar event operations"""
    
    @pytest.mark.asyncio
    @patch('aiohttp.ClientSession')
    async def test_create_calendar_event(self, mock_session_class, calendar_service, sample_integration):
        """Test creating a calendar event"""
        summary = "Test Appointment"
        description = "Test description"
        start_time = datetime.utcnow() + timedelta(days=1)
        end_time = start_time + timedelta(hours=1)
        
        # Mock response
        mock_response = MockAiohttpResponse(
            status=200,
            json_data={
                "id": "event_123",
                "summary": summary,
                "start": {"dateTime": start_time.isoformat()},
                "end": {"dateTime": end_time.isoformat()}
            }
        )
        
        # Mock session
        mock_session = AsyncMock()
        mock_session.post = AsyncMock(return_value=mock_response)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        
        # Mock ClientSession
        mock_session_instance = AsyncMock()
        mock_session_instance.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session_instance.__aexit__ = AsyncMock(return_value=None)
        mock_session_instance.post = AsyncMock(return_value=mock_response)
        
        mock_session_class.return_value = mock_session_instance
        
        result = await calendar_service.create_calendar_event(
            integration=sample_integration,
            summary=summary,
            description=description,
            start_time=start_time,
            end_time=end_time,
            attendees=None
        )
        
        assert result["id"] == "event_123"
        assert result["summary"] == summary


if __name__ == "__main__":
    pytest.main([__file__, "-v"])