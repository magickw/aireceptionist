from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime

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

class CRMIntegrationInterface(ABC):
    """Interface for Customer Relationship Management (CRM) system integrations."""
    
    @abstractmethod
    async def get_customer(self, email: str = None, phone: str = None) -> Optional[Dict[str, Any]]:
        """Retrieves a customer profile from the CRM."""
        pass

    @abstractmethod
    async def create_customer(self, customer_data: Dict[str, Any]) -> Dict[str, Any]:
        """Creates a new customer in the CRM."""
        pass

    @abstractmethod
    async def log_interaction(self, customer_id: str, interaction_type: str, details: Dict[str, Any]) -> bool:
        """Logs an interaction (call, message) to the customer's timeline."""
        pass

class CalendarIntegrationInterface(ABC):
    """Interface for Calendar/Scheduling system integrations."""
    
    @abstractmethod
    async def check_availability(self, start_time: datetime, end_time: datetime) -> bool:
        """Checks if a specific time slot is available."""
        pass

    @abstractmethod
    async def list_available_slots(self, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Lists available time slots within a date range."""
        pass

    @abstractmethod
    async def book_appointment(self, appointment_details: Dict[str, Any]) -> Dict[str, Any]:
        """Books an appointment on the calendar."""
        pass
