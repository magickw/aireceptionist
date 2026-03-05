"""Unit tests for CRM Integration Service"""

import pytest
from unittest.mock import Mock, patch, AsyncMock

from app.services.crm_integration import CRMIntegrationService


@pytest.fixture
def crm_service():
    """Create a CRM integration service instance"""
    return CRMIntegrationService()


class TestSalesforceIntegration:
    """Test cases for Salesforce CRM integration"""
    
    @pytest.mark.asyncio
    async def test_create_salesforce_contact_success(self, crm_service):
        """Test successful Salesforce contact creation"""
        # Configure service credentials
        crm_service.sf_username = "test@example.com"
        crm_service.sf_password = "password123"
        crm_service.sf_security_token = "token123"
        
        # Mock aiohttp ClientSession
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_auth_response = Mock()
            mock_auth_response.status = 200
            mock_auth_response.json = AsyncMock(return_value={
                "access_token": "test_access_token",
                "instance_url": "https://test.salesforce.com"
            })
            
            mock_contact_response = Mock()
            mock_contact_response.status = 201
            mock_contact_response.json = AsyncMock(return_value={
                "id": "003xx000003ABC"
            })
            
            # Create a proper async context manager mock
            mock_auth_response.__aenter__ = AsyncMock(return_value=mock_auth_response)
            mock_auth_response.__aexit__ = AsyncMock(return_value=None)
            
            mock_contact_response.__aenter__ = AsyncMock(return_value=mock_contact_response)
            mock_contact_response.__aexit__ = AsyncMock(return_value=None)
            
            mock_session = AsyncMock()
            mock_session.post = Mock(side_effect=[
                mock_auth_response,
                mock_contact_response
            ])
            mock_session.__aenter__.return_value = mock_session
            mock_session.__aexit__.return_value = None
            mock_session_class.return_value = mock_session
            
            result = await crm_service.create_salesforce_contact(
                first_name="John",
                last_name="Doe",
                email="john@example.com",
                phone="555-1234"
            )
            
            assert result["success"] is True
            assert result["contact_id"] == "003xx000003ABC"
    
    @pytest.mark.asyncio
    @patch('aiohttp.ClientSession')
    async def test_create_salesforce_contact_not_configured(self, mock_session_class, crm_service):
        """Test Salesforce contact creation without configuration"""
        # No credentials set
        crm_service.sf_username = None
        crm_service.sf_password = None
        crm_service.sf_security_token = None
        
        result = await crm_service.create_salesforce_contact(
            first_name="John",
            last_name="Doe",
            email="john@example.com"
        )
        
        assert result["success"] is False
        assert "not configured" in result["error"].lower()
    
    @pytest.mark.asyncio
    async def test_create_salesforce_contact_auth_failure(self, crm_service):
        """Test Salesforce contact creation with authentication failure"""
        crm_service.sf_username = "test@example.com"
        crm_service.sf_password = "password123"
        crm_service.sf_security_token = "token123"
        
        # Mock failed authentication
        mock_auth_response = Mock()
        mock_auth_response.status = 401
        mock_auth_response.json = AsyncMock(return_value={"error": "invalid_grant"})
        
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_auth_response.__aenter__ = AsyncMock(return_value=mock_auth_response)
            mock_auth_response.__aexit__ = AsyncMock(return_value=None)
            
            mock_session = AsyncMock()
            mock_session.post = Mock(return_value=mock_auth_response)
            mock_session.__aenter__.return_value = mock_session
            mock_session.__aexit__.return_value = None
            mock_session_class.return_value = mock_session
            
            result = await crm_service.create_salesforce_contact(
                first_name="John",
                last_name="Doe",
                email="john@example.com"
            )
            
            assert result["success"] is False
            assert "authentication failed" in result["error"].lower()


class TestHubSpotIntegration:
    """Test cases for HubSpot CRM integration"""
    
    @pytest.mark.asyncio
    async def test_create_hubspot_contact_success(self, crm_service):
        """Test successful HubSpot contact creation"""
        # Configure HubSpot
        crm_service.hs_api_key = "test_api_key"
        
        # Mock search response (contact doesn't exist)
        mock_search_response = Mock()
        mock_search_response.status = 200
        mock_search_response.json = AsyncMock(return_value={"results": []})
        
        # Mock creation response
        mock_create_response = Mock()
        mock_create_response.status = 201
        mock_create_response.json = AsyncMock(return_value={
            "id": "12345"
        })
        
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_search_response.__aenter__ = AsyncMock(return_value=mock_search_response)
            mock_search_response.__aexit__ = AsyncMock(return_value=None)
            
            mock_create_response.__aenter__ = AsyncMock(return_value=mock_create_response)
            mock_create_response.__aexit__ = AsyncMock(return_value=None)
            
            mock_session = AsyncMock()
            mock_session.post = Mock(side_effect=[
                mock_search_response,
                mock_create_response
            ])
            mock_session.__aenter__.return_value = mock_session
            mock_session.__aexit__.return_value = None
            mock_session_class.return_value = mock_session
            
            result = await crm_service.create_hubspot_contact(
                email="john@example.com",
                first_name="John",
                last_name="Doe"
            )
            
            assert result["success"] is True
            assert result["contact_id"] == "12345"
            assert result["created"] is True
    
    @pytest.mark.asyncio
    async def test_create_hubspot_contact_exists(self, crm_service):
        """Test HubSpot contact creation when contact already exists"""
        crm_service.hs_api_key = "test_api_key"
        
        # Mock search response (contact exists)
        mock_search_response = Mock()
        mock_search_response.status = 200
        mock_search_response.json = AsyncMock(return_value={
            "results": [{
                "id": "12345",
                "properties": {
                    "email": "john@example.com"
                }
            }]
        })
        
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_search_response.__aenter__ = AsyncMock(return_value=mock_search_response)
            mock_search_response.__aexit__ = AsyncMock(return_value=None)
            
            mock_session = AsyncMock()
            mock_session.post = Mock(return_value=mock_search_response)
            mock_session.__aenter__.return_value = mock_session
            mock_session.__aexit__.return_value = None
            mock_session_class.return_value = mock_session
            
            result = await crm_service.create_hubspot_contact(
                email="john@example.com",
                first_name="John",
                last_name="Doe"
            )
            
            assert result["success"] is True
            assert result["contact_id"] == "12345"
            assert result["created"] is False
    
    @pytest.mark.asyncio
    async def test_create_hubspot_contact_not_configured(self, crm_service):
        """Test HubSpot contact creation without configuration"""
        crm_service.hs_api_key = None
        
        result = await crm_service.create_hubspot_contact(
            email="john@example.com",
            first_name="John"
        )
        
        assert result["success"] is False
        assert "not configured" in result["error"].lower()


class TestCRMServiceInitialization:
    """Test cases for CRM service initialization"""
    
    def test_initialization_from_settings(self):
        """Test service initialization from settings"""
        from app.core.config import settings
        
        service = CRMIntegrationService()
        
        # Service should try to get credentials from settings or environment
        assert hasattr(service, 'sf_username')
        assert hasattr(service, 'sf_password')
        assert hasattr(service, 'sf_security_token')
        assert hasattr(service, 'hs_api_key')


class TestCRMErrorHandling:
    """Test cases for CRM error handling"""
    
    @pytest.mark.asyncio
    @patch('aiohttp.ClientSession')
    async def test_salesforce_network_error(self, mock_session_class, crm_service):
        """Test Salesforce contact creation with network error"""
        crm_service.sf_username = "test@example.com"
        crm_service.sf_password = "password123"
        crm_service.sf_security_token = "token123"
        
        # Mock network error
        mock_session = AsyncMock()
        mock_session.post = Mock(side_effect=Exception("Network error"))
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_session_class.return_value = mock_session
        
        result = await crm_service.create_salesforce_contact(
            first_name="John",
            last_name="Doe",
            email="john@example.com"
        )
        
        assert result["success"] is False
        assert "error" in result
    
    @pytest.mark.asyncio
    @patch('aiohttp.ClientSession')
    async def test_hubspot_network_error(self, mock_session_class, crm_service):
        """Test HubSpot contact creation with network error"""
        crm_service.hs_api_key = "test_api_key"
        
        mock_session = AsyncMock()
        mock_session.post = Mock(side_effect=Exception("Network error"))
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_session_class.return_value = mock_session
        
        result = await crm_service.create_hubspot_contact(
            email="john@example.com",
            first_name="John"
        )
        
        assert result["success"] is False
        assert "error" in result


class TestCRMDataValidation:
    """Test cases for CRM data validation"""
    
    @pytest.mark.asyncio
    async def test_salesforce_contact_with_company(self, crm_service):
        """Test Salesforce contact creation with company information"""
        crm_service.sf_username = "test@example.com"
        crm_service.sf_password = "password123"
        crm_service.sf_security_token = "token123"
        
        mock_auth_response = Mock()
        mock_auth_response.status = 200
        mock_auth_response.json = AsyncMock(return_value={
            "access_token": "test_access_token",
            "instance_url": "https://test.salesforce.com"
        })
        
        mock_contact_response = Mock()
        mock_contact_response.status = 201
        mock_contact_response.json = AsyncMock(return_value={"id": "003xx000003ABC"})
        
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_auth_response.__aenter__ = AsyncMock(return_value=mock_auth_response)
            mock_auth_response.__aexit__ = AsyncMock(return_value=None)
            
            mock_contact_response.__aenter__ = AsyncMock(return_value=mock_contact_response)
            mock_contact_response.__aexit__ = AsyncMock(return_value=None)
            
            mock_session = AsyncMock()
            mock_session.post = Mock(side_effect=[
                mock_auth_response,
                mock_contact_response
            ])
            mock_session.__aenter__.return_value = mock_session
            mock_session.__aexit__.return_value = None
            mock_session_class.return_value = mock_session
            
            result = await crm_service.create_salesforce_contact(
                first_name="John",
                last_name="Doe",
                email="john@example.com",
                company="Acme Corp"
            )
            
            assert result["success"] is True
            assert result["contact_id"] == "003xx000003ABC"
    
    @pytest.mark.asyncio
    async def test_salesforce_contact_minimal_data(self, crm_service):
        """Test Salesforce contact creation with minimal required data"""
        crm_service.sf_username = "test@example.com"
        crm_service.sf_password = "password123"
        crm_service.sf_security_token = "token123"
        
        mock_auth_response = Mock()
        mock_auth_response.status = 200
        mock_auth_response.json = AsyncMock(return_value={
            "access_token": "test_access_token",
            "instance_url": "https://test.salesforce.com"
        })
        
        mock_contact_response = Mock()
        mock_contact_response.status = 201
        mock_contact_response.json = AsyncMock(return_value={"id": "003xx000003ABC"})
        
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_auth_response.__aenter__ = AsyncMock(return_value=mock_auth_response)
            mock_auth_response.__aexit__ = AsyncMock(return_value=None)
            
            mock_contact_response.__aenter__ = AsyncMock(return_value=mock_contact_response)
            mock_contact_response.__aexit__ = AsyncMock(return_value=None)
            
            mock_session = AsyncMock()
            mock_session.post = Mock(side_effect=[
                mock_auth_response,
                mock_contact_response
            ])
            mock_session.__aenter__.return_value = mock_session
            mock_session.__aexit__.return_value = None
            mock_session_class.return_value = mock_session
            
            result = await crm_service.create_salesforce_contact(
                first_name="Jane",
                last_name="Smith",
                email="jane@example.com"
            )
            
            assert result["success"] is True
            assert result["contact_id"] == "003xx000003ABC"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])