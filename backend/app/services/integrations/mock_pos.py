from typing import Dict, Any, List
from datetime import datetime, timedelta
from app.services.integration_service import BaseIntegration, POSIntegrationInterface
from sqlalchemy.orm import Session

class MockPOSIntegration(BaseIntegration, POSIntegrationInterface):
    """
    A mock implementation of a Point-of-Sale (POS) system integration.
    Simulates sending orders and retrieving menu items.
    """
    def __init__(self, db: Session, business_id: int, integration_config: Dict[str, Any]):
        super().__init__(db, business_id, integration_config)
        self.is_mock_connected = False
        # Mock data for demonstration
        self.mock_menu_items = [
            {"id": 101, "name": "Burger", "price": 12.50, "category": "Main Course", "inventory": 100},
            {"id": 102, "name": "Fries", "price": 4.00, "category": "Side", "inventory": 100},
            {"id": 103, "name": "Coke", "price": 3.00, "category": "Drink", "inventory": 100},
            {"id": 104, "name": "Salad", "price": 9.00, "category": "Main Course", "inventory": 50},
            {"id": 105, "name": "Water", "price": 2.00, "category": "Drink", "inventory": 200},
            {"id": 106, "name": "Pizza", "price": 15.00, "category": "Main Course", "inventory": 70},
        ]
        self.mock_orders: Dict[str, Dict[str, Any]] = {} # {order_id: order_details}

    async def connect(self) -> bool:
        """Simulate connecting to the mock POS."""
        print(f"MockPOSIntegration: Simulating connection for business {self.business_id}")
        self.is_mock_connected = True
        return True

    async def is_connected(self) -> bool:
        """Simulate checking connection status."""
        return self.is_mock_connected

    async def authenticate(self, credentials: Dict[str, Any]) -> bool:
        """
        Simulate authentication. For mock, any credentials make it "authenticate".
        In a real scenario, this would validate API keys/tokens.
        """
        print(f"MockPOSIntegration: Simulating authentication with credentials: {credentials}")
        if credentials:
            self.is_mock_connected = True
            await self.update_status("active")
            return True
        await self.update_status("failed", "No credentials provided")
        return False

    async def disconnect(self) -> bool:
        """Simulate disconnecting."""
        print(f"MockPOSIntegration: Simulating disconnection for business {self.business_id}")
        self.is_mock_connected = False
        await self.update_status("disconnected")
        return True

    async def get_menu_items(self) -> List[Dict[str, Any]]:
        """Retrieves mock menu items."""
        if not self.is_mock_connected:
            raise Exception("Mock POS not connected")
        print(f"MockPOSIntegration: Retrieving mock menu items for business {self.business_id}")
        return self.mock_menu_items

    async def send_order(self, order_details: Dict[str, Any]) -> Dict[str, Any]:
        """Simulates sending an order to the POS."""
        if not self.is_mock_connected:
            raise Exception("Mock POS not connected")
        
        order_id = f"mock_pos_order_{len(self.mock_orders) + 1}"
        processed_order = {
            "order_id": order_id,
            "status": "placed",
            "timestamp": datetime.now().isoformat(),
            **order_details
        }
        self.mock_orders[order_id] = processed_order
        print(f"MockPOSIntegration: Order {order_id} simulated as placed for business {self.business_id}")
        return processed_order

    async def get_order_status(self, order_id: str) -> Dict[str, Any]:
        """Retrieves mock order status."""
        if not self.is_mock_connected:
            raise Exception("Mock POS not connected")
        
        order = self.mock_orders.get(order_id)
        if order:
            print(f"MockPOSIntegration: Retrieving status for order {order_id} for business {self.business_id}")
            return {"order_id": order_id, "status": order["status"], "details": order}
        
        raise Exception(f"Order {order_id} not found in mock POS")

    # Additional mock methods could be added here for more complex scenarios
    async def process_payment(self, amount: float, method: str) -> Dict[str, Any]:
        """Simulates processing a payment."""
        if not self.is_mock_connected:
            raise Exception("Mock POS not connected")
        payment_id = f"mock_payment_{len(self.mock_orders) + 1}" # Reusing order counter for payment id
        return {"payment_id": payment_id, "amount": amount, "method": method, "status": "approved", "timestamp": datetime.now().isoformat()}