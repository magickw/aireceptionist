from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from app.models.models import Integration, Business

class BaseIntegration(ABC):
    """
    Abstract Base Class for all external service integrations.
    Defines common methods for managing integration lifecycle.
    """
    def __init__(self, db: Session, business_id: int, integration_config: Dict[str, Any]):
        self.db = db
        self.business_id = business_id
        self.config = integration_config
        self.provider = integration_config.get("provider", "unknown")
        self.name = integration_config.get("name", "Unnamed Integration")

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

    async def update_status(self, status: str, error_message: Optional[str] = None):
        """Updates the status of the integration in the database."""
        db_integration = self.db.query(Integration).filter(Integration.id == self.config["id"]).first()
        if db_integration:
            db_integration.status = status
            db_integration.error_message = error_message
            self.db.commit()
            self.db.refresh(db_integration)

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

class IntegrationService:
    """
    Manages all integrations for a business.
    Provides methods to list, retrieve, and interact with configured integrations.
    """
    def __init__(self, db: Session):
        self.db = db

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

# Singleton instance
integration_service = IntegrationService(None) # DB session will be injected per request

