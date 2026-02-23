from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Callable, AsyncGenerator
from sqlalchemy.orm import Session
from app.models.models import Integration, Business
import asyncio
import json
from enum import Enum


class SyncStatus(Enum):
    """Status of data synchronization"""
    IDLE = "idle"
    SYNCING = "syncing"
    SUCCESS = "success"
    ERROR = "error"
    PARTIAL = "partial"


class SyncDirection(Enum):
    """Direction of data synchronization"""
    PULL = "pull"  # Pull data from external system
    PUSH = "push"  # Push data to external system
    BIDIRECTIONAL = "bidirectional"  # Sync both ways


class BaseIntegration(ABC):
    """
    Abstract Base Class for all external service integrations.
    Defines common methods for managing integration lifecycle.
    
    Enhanced with:
    - Universal integration capabilities
    - Real-time synchronization support
    - Event-driven architecture
    """
    def __init__(self, db: Session, business_id: int, integration_config: Dict[str, Any]):
        self.db = db
        self.business_id = business_id
        self.config = integration_config
        self.provider = integration_config.get("provider", "unknown")
        self.name = integration_config.get("name", "Unnamed Integration")
        
        # Sync capabilities
        self._sync_status = SyncStatus.IDLE
        self._last_sync_time = None
        self._sync_callbacks: List[Callable] = []
        self._event_queue: asyncio.Queue = None

    @abstractmethod
    async def connect(self) -> bool:
        """Establishes a connection to the external service."""
        pass

    @abstractmethod
    async def is_connected(self) -> bool:
        """Checks if the integration is currently active and authenticated."""
        pass

    @abstractmethod
    async def authenticate(self, credentials: Dict[str, Any]) -> bool:
        """Performs authentication with the external service."""
        pass

    @abstractmethod
    async def disconnect(self) -> bool:
        """Closes the connection to the external service."""
        pass
    
    async def sync_data(
        self,
        direction: SyncDirection = SyncDirection.BIDIRECTIONAL,
        data_filter: Optional[Dict[str, Any]] = None,
        real_time: bool = False
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Synchronize data between the platform and the external system.
        
        Args:
            direction: Direction of sync (pull, push, or bidirectional)
            data_filter: Optional filter to limit what data is synced
            real_time: Whether to enable real-time sync events
            
        Yields:
            Sync progress updates and results
        """
        self._sync_status = SyncStatus.SYNCING
        
        try:
            yield {
                "type": "sync_started",
                "direction": direction.value,
                "timestamp": datetime.now().isoformat()
            }
            
            # Perform sync based on direction
            if direction in [SyncDirection.PULL, SyncDirection.BIDIRECTIONAL]:
                async for update in self._pull_data(data_filter):
                    yield update
            
            if direction in [SyncDirection.PUSH, SyncDirection.BIDIRECTIONAL]:
                async for update in self._push_data(data_filter):
                    yield update
            
            self._last_sync_time = datetime.now()
            self._sync_status = SyncStatus.SUCCESS
            
            yield {
                "type": "sync_completed",
                "status": "success",
                "timestamp": self._last_sync_time.isoformat()
            }
            
        except Exception as e:
            self._sync_status = SyncStatus.ERROR
            yield {
                "type": "sync_error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def _pull_data(
        self,
        data_filter: Optional[Dict[str, Any]] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Pull data from external system.
        Override in concrete implementations.
        """
        yield {
            "type": "pull_skipped",
            "reason": "Not implemented for this integration"
        }
    
    async def _push_data(
        self,
        data_filter: Optional[Dict[str, Any]] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Push data to external system.
        Override in concrete implementations.
        """
        yield {
            "type": "push_skipped",
            "reason": "Not implemented for this integration"
        }
    
    def register_sync_callback(self, callback: Callable):
        """Register a callback to be called on sync events."""
        self._sync_callbacks.append(callback)
    
    async def _notify_callbacks(self, event: Dict[str, Any]):
        """Notify all registered callbacks of a sync event."""
        for callback in self._sync_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(event)
                else:
                    callback(event)
            except Exception as e:
                print(f"Error in sync callback: {e}")
    
    def get_sync_status(self) -> Dict[str, Any]:
        """Get current synchronization status."""
        return {
            "status": self._sync_status.value,
            "last_sync_time": self._last_sync_time.isoformat() if self._last_sync_time else None,
            "integration": self.name
        }
    
    async def subscribe_to_events(self) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Subscribe to real-time events from the external system.
        Override in concrete implementations that support webhooks or event streams.
        """
        yield {
            "type": "event_subscription_skipped",
            "reason": "Not implemented for this integration"
        }

class POSIntegrationInterface(ABC):
    """Interface for Point-of-Sale (POS) system integrations."""
    @abstractmethod
    async def get_menu_items(self) -> List[Dict[str, Any]]:
        """Retrieves menu items from the POS system."""
        pass

    @abstractmethod
    async def send_order(self, order_details: Dict[str, Any]) -> Dict[str, Any]:
        """Sends an order to the POS system."""
        pass

    @abstractmethod
    async def get_order_status(self, order_id: str) -> Dict[str, Any]:
        """Retrieves the status of an order from the POS system."""
        pass

class PMSIntegrationInterface(ABC):
    """Interface for Property Management System (PMS) integrations (e.g., Hotels)."""
    @abstractmethod
    async def get_room_availability(self, check_in: datetime, check_out: datetime, room_type: str) -> List[Dict[str, Any]]:
        """Checks room availability for specified dates and room type."""
        pass

    @abstractmethod
    async def book_room(self, booking_details: Dict[str, Any]) -> Dict[str, Any]:
        """Books a room in the PMS."""
        pass

    @abstractmethod
    async def modify_booking(self, booking_id: str, new_details: Dict[str, Any]) -> Dict[str, Any]:
        """Modifies an existing room booking."""
        pass

    @abstractmethod
    async def cancel_booking(self, booking_id: str) -> bool:
        """Cancels a room booking."""
        pass

class EHRIntegrationInterface(ABC):
    """Interface for Electronic Health Record (EHR) system integrations."""
    @abstractmethod
    async def get_patient_record(self, patient_id: str) -> Dict[str, Any]:
        """Retrieves a patient's health record."""
        pass

    @abstractmethod
    async def schedule_appointment(self, appointment_details: Dict[str, Any]) -> Dict[str, Any]:
        """Schedules a patient appointment in the EHR."""
        pass

    @abstractmethod
    async def get_provider_availability(self, provider_id: str, date: datetime) -> List[Dict[str, Any]]:
        """Retrieves a provider's availability."""
        pass

# Factory function to get appropriate integration instance
def get_integration_instance(db: Session, business_id: int, integration_type: str, integration_config: Dict[str, Any]) -> Optional[BaseIntegration]:
    """
    Factory function to return an instance of a specific integration.
    This is where concrete implementations would be plugged in.
    """
    if integration_type == "mock_pos":
        from app.services.integrations.mock_pos import MockPOSIntegration
        return MockPOSIntegration(db, business_id, integration_config)
    elif integration_type == "mock_pms":
        # Example: return MockPMSIntegration(db, business_id, integration_config)
        pass
    elif integration_type == "mock_ehr":
        # Example: return MockEHRIntegration(db, business_id, integration_config)
        pass
    # Add more concrete implementations here based on integration_type
    
    print(f"Warning: No concrete integration found for type: {integration_type}")
    return None


class UniversalIntegrationAdapter:
    """
    Universal adapter for connecting to any REST/GraphQL API-based system.
    Enables plug-and-play integration with most modern SaaS applications.
    """
    
    def __init__(self, db: Session, business_id: int, config: Dict[str, Any]):
        self.db = db
        self.business_id = business_id
        self.config = config
        
        # API configuration
        self.base_url = config.get("base_url", "")
        self.api_type = config.get("api_type", "rest")  # rest or graphql
        self.auth_type = config.get("auth_type", "bearer")  # bearer, basic, api_key, oauth2
        self.auth_credentials = config.get("auth_credentials", {})
        
        # Headers and mapping
        self.default_headers = config.get("default_headers", {})
        self.field_mappings = config.get("field_mappings", {})
        self.endpoints = config.get("endpoints", {})
        
        # HTTP client (using aiohttp for async requests)
        self._http_client = None
    
    async def _get_http_client(self):
        """Get or create HTTP client."""
        if self._http_client is None:
            import aiohttp
            self._http_client = aiohttp.ClientSession(
                headers=self.default_headers,
                timeout=aiohttp.ClientTimeout(total=30)
            )
        return self._http_client
    
    async def _add_auth_headers(self, headers: Dict[str, str]) -> Dict[str, str]:
        """Add authentication headers based on auth type."""
        auth_headers = headers.copy()
        
        if self.auth_type == "bearer":
            token = self.auth_credentials.get("token")
            if token:
                auth_headers["Authorization"] = f"Bearer {token}"
        
        elif self.auth_type == "basic":
            username = self.auth_credentials.get("username")
            password = self.auth_credentials.get("password")
            if username and password:
                import base64
                credentials = base64.b64encode(f"{username}:{password}".encode()).decode()
                auth_headers["Authorization"] = f"Basic {credentials}"
        
        elif self.auth_type == "api_key":
            api_key = self.auth_credentials.get("api_key")
            header_name = self.auth_credentials.get("api_key_header", "X-API-Key")
            if api_key:
                auth_headers[header_name] = api_key
        
        elif self.auth_type == "oauth2":
            access_token = self.auth_credentials.get("access_token")
            if access_token:
                auth_headers["Authorization"] = f"Bearer {access_token}"
        
        return auth_headers
    
    async def make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Make an HTTP request to the integrated API.
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE, etc.)
            endpoint: API endpoint (relative to base_url)
            data: Request body data
            params: Query parameters
            headers: Additional headers
            
        Returns:
            Response data
        """
        client = await self._get_http_client()
        
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        auth_headers = await self._add_auth_headers(headers or {})
        
        try:
            if self.api_type == "graphql":
                # GraphQL request
                if method != "POST":
                    raise ValueError("GraphQL requests must use POST method")
                
                response = await client.post(
                    url,
                    json={"query": data.get("query"), "variables": data.get("variables", {})},
                    headers=auth_headers
                )
            else:
                # REST request
                response = await client.request(
                    method.upper(),
                    url,
                    json=data,
                    params=params,
                    headers=auth_headers
                )
            
            response_data = await response.json()
            
            return {
                "status": response.status,
                "success": 200 <= response.status < 300,
                "data": response_data
            }
            
        except Exception as e:
            return {
                "status": 500,
                "success": False,
                "error": str(e)
            }
    
    async def transform_data(
        self,
        data: Dict[str, Any],
        direction: str = "to_external"
    ) -> Dict[str, Any]:
        """
        Transform data according to field mappings.
        
        Args:
            data: Data to transform
            direction: "to_external" or "from_external"
            
        Returns:
            Transformed data
        """
        if direction == "to_external":
            # Map internal field names to external field names
            transformed = {}
            for internal_field, external_field in self.field_mappings.items():
                if internal_field in data:
                    transformed[external_field] = data[internal_field]
            return transformed
        else:
            # Map external field names to internal field names
            transformed = {}
            for internal_field, external_field in self.field_mappings.items():
                if external_field in data:
                    transformed[internal_field] = data[external_field]
            return transformed
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test the connection to the external API."""
        test_endpoint = self.config.get("test_endpoint", "/")
        
        result = await self.make_request("GET", test_endpoint)
        
        return {
            "connected": result["success"],
            "status": result["status"],
            "details": result
        }
    
    async def close(self):
        """Close the HTTP client."""
        if self._http_client:
            await self._http_client.close()
            self._http_client = None


class IntegrationConflictResolver:
    """
    Resolves conflicts when synchronizing data between multiple systems.
    Handles data inconsistencies, version conflicts, and merge strategies.
    """
    
    def __init__(self):
        self._merge_strategies = {
            "latest_wins": self._merge_latest_wins,
            "preserve_source": self._merge_preserve_source,
            "preserve_target": self._merge_preserve_target,
            "smart_merge": self._smart_merge
        }
    
    async def resolve_conflict(
        self,
        source_data: Dict[str, Any],
        target_data: Dict[str, Any],
        conflict_type: str,
        strategy: str = "smart_merge"
    ) -> Dict[str, Any]:
        """
        Resolve data conflicts between source and target systems.
        
        Args:
            source_data: Data from source system
            target_data: Data from target system
            conflict_type: Type of conflict
            strategy: Merge strategy to use
            
        Returns:
            Resolved data
        """
        if strategy not in self._merge_strategies:
            strategy = "smart_merge"
        
        resolver = self._merge_strategies[strategy]
        return await resolver(source_data, target_data, conflict_type)
    
    async def _merge_latest_wins(
        self,
        source_data: Dict[str, Any],
        target_data: Dict[str, Any],
        conflict_type: str
    ) -> Dict[str, Any]:
        """Use the most recently modified data."""
        source_timestamp = source_data.get("modified_at", source_data.get("timestamp", ""))
        target_timestamp = target_data.get("modified_at", target_data.get("timestamp", ""))
        
        if source_timestamp >= target_timestamp:
            return source_data
        else:
            return target_data
    
    async def _merge_preserve_source(
        self,
        source_data: Dict[str, Any],
        target_data: Dict[str, Any],
        conflict_type: str
    ) -> Dict[str, Any]:
        """Always preserve source data."""
        return source_data
    
    async def _merge_preserve_target(
        self,
        source_data: Dict[str, Any],
        target_data: Dict[str, Any],
        conflict_type: str
    ) -> Dict[str, Any]:
        """Always preserve target data."""
        return target_data
    
    async def _smart_merge(
        self,
        source_data: Dict[str, Any],
        target_data: Dict[str, Any],
        conflict_type: str
    ) -> Dict[str, Any]:
        """
        Intelligent merge that considers data semantics and business logic.
        Combines data from both sources based on heuristics.
        """
        merged = target_data.copy()
        
        # Merge strategies based on conflict type
        if conflict_type == "field_value":
            # Use the most recently modified value
            if source_data.get("modified_at") > target_data.get("modified_at"):
                merged.update(source_data)
        
        elif conflict_type == "missing_fields":
            # Fill in missing fields from either source
            for key, value in source_data.items():
                if key not in merged or not merged[key]:
                    merged[key] = value
        
        elif conflict_type == "version_conflict":
            # Use higher version number
            source_version = source_data.get("version", 0)
            target_version = target_data.get("version", 0)
            
            if source_version > target_version:
                merged.update(source_data)
        
        else:
            # Default: merge all fields, source overwrites target
            merged.update(source_data)
        
        # Add merge metadata
        merged["_merge_info"] = {
            "merged_at": datetime.now().isoformat(),
            "strategy": "smart_merge",
            "conflict_type": conflict_type
        }
        
        return merged


# Singleton instance
conflict_resolver = IntegrationConflictResolver()

# Singleton instance
integration_service = None  # Will be initialized with DB session


def get_integration_service(db: Session) -> 'IntegrationService':
    """Factory function to get IntegrationService instance with DB session"""
    global integration_service
    if integration_service is None:
        integration_service = IntegrationService(db)
    return integration_service


class IntegrationService:
    """
    Manages all integrations for a business.
    Provides methods to list, retrieve, and interact with configured integrations.
    """
    def __init__(self, db: Session):
        self.db = db
        self._active_sync_tasks: Dict[str, asyncio.Task] = {}
        self._sync_status: Dict[str, Dict[str, Any]] = {}

    def get_business_integrations(self, business_id: int) -> List[Integration]:
        """Retrieves all active integrations for a given business."""
        return self.db.query(Integration).filter(
            Integration.business_id == business_id,
            Integration.status == "active"
        ).all()

    def get_integration_by_type(self, business_id: int, integration_type: str) -> Optional[BaseIntegration]:
        """
        Retrieves a specific integration by its type for a business.
        Returns an instantiated integration client.
        """
        integration_db = self.db.query(Integration).filter(
            Integration.business_id == business_id,
            Integration.integration_type == integration_type,
            Integration.status == "active"
        ).first()

        if integration_db:
            return get_integration_instance(self.db, business_id, integration_type, integration_db.configuration)
        return None
    
    async def sync_all_integrations(
        self,
        business_id: int,
        direction: SyncDirection = SyncDirection.BIDIRECTIONAL
    ) -> Dict[str, Any]:
        """
        Synchronize all active integrations for a business.
        
        Args:
            business_id: Business ID
            direction: Direction of synchronization
            
        Returns:
            Dictionary with sync results for all integrations
        """
        integrations = self.get_business_integrations(business_id)
        sync_results = {}
        
        for integration in integrations:
            integration_type = integration.integration_type
            sync_results[integration_type] = await self.sync_integration(
                business_id,
                integration_type,
                direction
            )
        
        return {
            "business_id": business_id,
            "sync_timestamp": datetime.now().isoformat(),
            "integrations_synced": len(integrations),
            "results": sync_results
        }
    
    async def sync_integration(
        self,
        business_id: int,
        integration_type: str,
        direction: SyncDirection = SyncDirection.BIDIRECTIONAL
    ) -> Dict[str, Any]:
        """
        Synchronize a specific integration.
        
        Args:
            business_id: Business ID
            integration_type: Type of integration
            direction: Direction of synchronization
            
        Returns:
            Dictionary with sync result
        """
        try:
            integration = self.get_integration_by_type(business_id, integration_type)
            
            if not integration:
                return {
                    "success": False,
                    "message": f"No active integration found for type: {integration_type}"
                }
            
            # Check if already syncing
            sync_key = f"{business_id}_{integration_type}"
            if sync_key in self._active_sync_tasks:
                return {
                    "success": False,
                    "message": "Sync already in progress",
                    "status": "syncing"
                }
            
            # Create sync task
            async def sync_task():
                sync_events = []
                async for event in integration.sync_data(direction):
                    sync_events.append(event)
                return sync_events
            
            # Start sync task
            sync_task_obj = asyncio.create_task(sync_task())
            self._active_sync_tasks[sync_key] = sync_task_obj
            
            # Wait for completion (in production, you might want to return immediately)
            sync_events = await sync_task_obj
            
            # Update status
            self._sync_status[sync_key] = {
                "status": "completed",
                "last_sync": datetime.now().isoformat(),
                "events": sync_events
            }
            
            return {
                "success": True,
                "integration_type": integration_type,
                "direction": direction.value,
                "events": sync_events
            }
            
        except Exception as e:
            return {
                "success": False,
                "integration_type": integration_type,
                "error": str(e)
            }
    
    async def get_sync_status(
        self,
        business_id: int,
        integration_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get synchronization status for integrations.
        
        Args:
            business_id: Business ID
            integration_type: Optional specific integration type
            
        Returns:
            Dictionary with sync status
        """
        if integration_type:
            sync_key = f"{business_id}_{integration_type}"
            return self._sync_status.get(sync_key, {"status": "unknown"})
        else:
            # Return status for all integrations
            status_dict = {}
            for key, value in self._sync_status.items():
                if key.startswith(f"{business_id}_"):
                    integration_type = key.replace(f"{business_id}_", "")
                    status_dict[integration_type] = value
            return status_dict
    
    async def test_all_integrations(self, business_id: int) -> Dict[str, Any]:
        """
        Test all integrations for a business.
        
        Args:
            business_id: Business ID
            
        Returns:
            Dictionary with test results for all integrations
        """
        integrations = self.get_business_integrations(business_id)
        test_results = {}
        
        for integration in integrations:
            integration_type = integration.integration_type
            try:
                integration_instance = get_integration_instance(
                    self.db, 
                    business_id, 
                    integration_type, 
                    integration.configuration
                )
                
                if integration_instance:
                    is_connected = await integration_instance.is_connected()
                    test_results[integration_type] = {
                        "connected": is_connected,
                        "status": integration.status
                    }
                else:
                    test_results[integration_type] = {
                        "connected": False,
                        "status": "error"
                    }
            except Exception as e:
                test_results[integration_type] = {
                    "connected": False,
                    "error": str(e)
                }
        
        return {
            "business_id": business_id,
            "test_timestamp": datetime.now().isoformat(),
            "integrations_tested": len(integrations),
            "results": test_results
        }

# Singleton instance
integration_service = IntegrationService(None) # DB session will be injected per request

