"""
Conversation State Management
Handles order state, conversation memory, and error handling for the AI agent.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum
import asyncio
from dataclasses import dataclass, field


# =============================================================================
# CUSTOM EXCEPTION CLASSES
# =============================================================================

class ReasoningError(Exception):
    """Base error for reasoning failures"""
    def __init__(self, message: str, recoverable: bool = True):
        self.message = message
        self.recoverable = recoverable
        super().__init__(message)


class SafetyViolationError(ReasoningError):
    """Deterministic safety trigger - requires escalation"""
    def __init__(self, message: str, trigger_type: str = None, requires_911: bool = False):
        super().__init__(message, recoverable=False)
        self.trigger_type = trigger_type
        self.requires_911 = requires_911


class ModelInvocationError(ReasoningError):
    """Model API failure"""
    def __init__(self, message: str, retry_count: int = 0):
        super().__init__(message, recoverable=True)
        self.retry_count = retry_count


class ParseError(ReasoningError):
    """Failed to parse model response"""
    def __init__(self, message: str, raw_response: str = None):
        super().__init__(message, recoverable=True)
        self.raw_response = raw_response


class ValidationError(ReasoningError):
    """Invalid data or state"""
    def __init__(self, message: str, field: str = None, value: Any = None):
        super().__init__(message, recoverable=True)
        self.field = field
        self.value = value


# =============================================================================
# ORDER STATE MANAGEMENT
# =============================================================================

class OrderStatus(str, Enum):
    """Order status states"""
    EMPTY = "empty"
    BUILDING = "building"
    PENDING_CONFIRMATION = "pending_confirmation"
    CONFIRMED = "confirmed"
    SUBMITTED = "submitted"
    CANCELLED = "cancelled"


@dataclass
class OrderItem:
    """Represents a single item in an order"""
    name: str
    price: float
    quantity: int = 1
    menu_item_id: Optional[int] = None
    special_requests: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "price": self.price,
            "quantity": self.quantity,
            "menu_item_id": self.menu_item_id,
            "special_requests": self.special_requests
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "OrderItem":
        return cls(
            name=data.get("name", ""),
            price=data.get("price", 0),
            quantity=data.get("quantity", 1),
            menu_item_id=data.get("menu_item_id"),
            special_requests=data.get("special_requests")
        )


class OrderState:
    """
    Manages order state with proper tracking and validation.
    
    This fixes the race condition where:
    - User: "I want a burger" -> PLACE_ORDER
    - User: "Actually, make it two burgers" -> PLACE_ORDER (adds duplicate)
    - User: "Confirm" -> CONFIRM_ORDER (ambiguous)
    """
    
    def __init__(self):
        self.items: List[OrderItem] = []
        self.status: OrderStatus = OrderStatus.EMPTY
        self.customer_name: Optional[str] = None
        self.customer_phone: Optional[str] = None
        self.delivery_method: Optional[str] = None  # "pickup" or "delivery"
        self.delivery_address: Optional[str] = None
        self.created_at: datetime = datetime.utcnow()
        self.confirmed_at: Optional[datetime] = None
        self.total_amount: float = 0.0
        self._last_modified_item: Optional[str] = None
    
    def add_item(self, name: str, price: float, quantity: int = 1, 
                 menu_item_id: int = None, special_requests: str = None) -> Dict[str, Any]:
        """
        Add or update an item in the order.
        Returns info about what happened.
        """
        if self.status == OrderStatus.CONFIRMED:
            raise ValidationError(
                "Cannot add items to a confirmed order",
                field="status",
                value=self.status
            )
        
        if self.status == OrderStatus.EMPTY:
            self.status = OrderStatus.BUILDING
        
        # Check if item already exists
        existing = next((item for item in self.items if item.name.lower() == name.lower()), None)
        
        if existing:
            # Update quantity of existing item
            existing.quantity += quantity
            existing.special_requests = special_requests or existing.special_requests
            self._last_modified_item = name
            self._recalculate_total()
            return {
                "action": "updated",
                "item": existing.to_dict(),
                "message": f"Updated {name} to {existing.quantity}x"
            }
        else:
            # Add new item
            new_item = OrderItem(
                name=name,
                price=price,
                quantity=quantity,
                menu_item_id=menu_item_id,
                special_requests=special_requests
            )
            self.items.append(new_item)
            self._last_modified_item = name
            self._recalculate_total()
            return {
                "action": "added",
                "item": new_item.to_dict(),
                "message": f"Added {quantity}x {name}"
            }
    
    def remove_item(self, name: str) -> Dict[str, Any]:
        """Remove an item from the order."""
        if self.status == OrderStatus.CONFIRMED:
            raise ValidationError("Cannot remove items from a confirmed order")
        
        for i, item in enumerate(self.items):
            if item.name.lower() == name.lower():
                removed = self.items.pop(i)
                self._recalculate_total()
                
                if not self.items:
                    self.status = OrderStatus.EMPTY
                
                return {
                    "action": "removed",
                    "item": removed.to_dict(),
                    "message": f"Removed {name} from order"
                }
        
        return {
            "action": "not_found",
            "item": None,
            "message": f"{name} not found in order"
        }
    
    def update_quantity(self, name: str, quantity: int) -> Dict[str, Any]:
        """Update quantity of an item. If quantity is 0, removes the item."""
        if quantity <= 0:
            return self.remove_item(name)
        
        for item in self.items:
            if item.name.lower() == name.lower():
                item.quantity = quantity
                self._recalculate_total()
                return {
                    "action": "updated",
                    "item": item.to_dict(),
                    "message": f"Set {name} to {quantity}x"
                }
        
        return {
            "action": "not_found",
            "item": None,
            "message": f"{name} not found in order"
        }
    
    def set_delivery_method(self, method: str, address: str = None) -> None:
        """Set delivery method (pickup or delivery)."""
        if method.lower() not in ["pickup", "delivery", "pick up"]:
            raise ValidationError(
                f"Invalid delivery method: {method}",
                field="delivery_method",
                value=method
            )
        
        self.delivery_method = "pickup" if "pick" in method.lower() else "delivery"
        self.delivery_address = address if self.delivery_method == "delivery" else None
    
    def set_customer_info(self, name: str = None, phone: str = None) -> None:
        """Set customer information."""
        if name:
            self.customer_name = name
        if phone:
            self.customer_phone = phone
    
    def request_confirmation(self) -> Dict[str, Any]:
        """Mark order as pending confirmation and return summary."""
        if not self.items:
            raise ValidationError("Cannot confirm an empty order")
        
        self.status = OrderStatus.PENDING_CONFIRMATION
        return self.get_summary()
    
    def confirm(self) -> Dict[str, Any]:
        """
        Confirm the order for submission.
        Returns order data ready for database persistence.
        """
        if not self.items:
            raise ValidationError("Cannot confirm an empty order")
        
        if self.status == OrderStatus.CONFIRMED:
            raise ValidationError("Order is already confirmed")
        
        self.status = OrderStatus.CONFIRMED
        self.confirmed_at = datetime.utcnow()
        
        return {
            "items": [item.to_dict() for item in self.items],
            "total_amount": self.total_amount,
            "customer_name": self.customer_name,
            "customer_phone": self.customer_phone,
            "delivery_method": self.delivery_method,
            "delivery_address": self.delivery_address,
            "confirmed_at": self.confirmed_at.isoformat()
        }
    
    def submit(self) -> None:
        """Mark order as submitted to database."""
        if self.status != OrderStatus.CONFIRMED:
            raise ValidationError("Order must be confirmed before submission")
        self.status = OrderStatus.SUBMITTED
    
    def cancel(self, reason: str = None) -> None:
        """Cancel the order."""
        self.status = OrderStatus.CANCELLED
    
    def clear(self) -> None:
        """Reset the order state."""
        self.items = []
        self.status = OrderStatus.EMPTY
        self.customer_name = None
        self.customer_phone = None
        self.delivery_method = None
        self.delivery_address = None
        self.confirmed_at = None
        self.total_amount = 0.0
        self._last_modified_item = None
    
    def _recalculate_total(self) -> None:
        """Recalculate the total amount."""
        self.total_amount = sum(item.price * item.quantity for item in self.items)
    
    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of the current order."""
        return {
            "items": [item.to_dict() for item in self.items],
            "item_count": sum(item.quantity for item in self.items),
            "total_amount": self.total_amount,
            "status": self.status,
            "customer_name": self.customer_name,
            "customer_phone": self.customer_phone,
            "delivery_method": self.delivery_method,
            "is_ready_for_confirmation": (
                len(self.items) > 0 and 
                self.status in [OrderStatus.BUILDING, OrderStatus.PENDING_CONFIRMATION]
            ),
            "is_ready_for_submission": (
                self.status == OrderStatus.CONFIRMED and
                self.customer_name is not None and
                self.customer_phone is not None
            ),
            "missing_info": self._get_missing_info()
        }
    
    def _get_missing_info(self) -> List[str]:
        """Get list of missing information for order completion."""
        missing = []
        if not self.customer_name:
            missing.append("customer_name")
        if not self.customer_phone:
            missing.append("customer_phone")
        if not self.delivery_method:
            missing.append("delivery_method")
        return missing
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize order state for session storage."""
        return {
            "items": [item.to_dict() for item in self.items],
            "status": self.status,
            "customer_name": self.customer_name,
            "customer_phone": self.customer_phone,
            "delivery_method": self.delivery_method,
            "delivery_address": self.delivery_address,
            "total_amount": self.total_amount,
            "created_at": self.created_at.isoformat(),
            "confirmed_at": self.confirmed_at.isoformat() if self.confirmed_at else None,
            "last_modified_item": self._last_modified_item
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "OrderState":
        """Deserialize order state from session storage."""
        state = cls()
        state.items = [OrderItem.from_dict(item) for item in data.get("items", [])]
        state.status = OrderStatus(data.get("status", OrderStatus.EMPTY))
        state.customer_name = data.get("customer_name")
        state.customer_phone = data.get("customer_phone")
        state.delivery_method = data.get("delivery_method")
        state.delivery_address = data.get("delivery_address")
        state.total_amount = data.get("total_amount", 0)
        state._last_modified_item = data.get("last_modified_item")
        
        if data.get("created_at"):
            try:
                state.created_at = datetime.fromisoformat(data["created_at"])
            except:
                pass
        
        if data.get("confirmed_at"):
            try:
                state.confirmed_at = datetime.fromisoformat(data["confirmed_at"])
            except:
                pass
        
        return state


# =============================================================================
# CONVERSATION MEMORY
# =============================================================================

class ConversationMemory:
    """
    Tracks state across conversation turns.
    Implements the memory_update functionality from reasoning results.
    """
    
    def __init__(self):
        self.collected_fields: Dict[str, Any] = {}
        self.order_state: OrderState = OrderState()
        self.interaction_count: int = 0
        self.intent_history: List[str] = []
        self.action_history: List[str] = []
        self.sentiment_history: List[str] = []
        self.escalation_count: int = 0
        self.price_mentioned: bool = False
        self.questions_asked: List[str] = []
        self.last_intent: Optional[str] = None
        self.last_action: Optional[str] = None
        self.pending_confirmation: Optional[Dict[str, Any]] = None
        self.session_start: datetime = datetime.utcnow()
    
    def update(self, reasoning_result: Dict[str, Any]) -> None:
        """Update memory from reasoning result."""
        self.interaction_count += 1
        
        # Track intent and action
        intent = reasoning_result.get("intent")
        action = reasoning_result.get("selected_action")
        
        if intent:
            self.intent_history.append(intent)
            self.last_intent = intent
        
        if action:
            self.action_history.append(action)
            self.last_action = action
        
        # Track sentiment
        sentiment = reasoning_result.get("sentiment")
        if sentiment:
            self.sentiment_history.append(sentiment)
        
        # Track escalation
        if reasoning_result.get("requires_approval"):
            self.escalation_count += 1
        
        # Apply memory updates from reasoning
        memory_update = reasoning_result.get("memory_update", {})
        if memory_update and memory_update.get("key"):
            key = memory_update.get("key")
            value = memory_update.get("value")
            
            if key == "collect_field":
                # Collect a specific field
                if isinstance(value, dict):
                    self.collected_fields.update(value)
            elif key == "price_mentioned":
                self.price_mentioned = True
            elif key == "question_asked":
                if value and value not in self.questions_asked:
                    self.questions_asked.append(value)
            elif key == "escalation":
                self.escalation_count += 1
        
        # Extract entities to collected fields
        entities = reasoning_result.get("entities", {})
        for field, value in entities.items():
            if value is not None and value != "":
                self.collected_fields[field] = value
    
    def update_order(self, action: str, entities: Dict[str, Any], menu_data: List[Dict] = None) -> Dict[str, Any]:
        """
        Update order state based on action and entities.
        Returns result of the order operation.
        """
        menu_item = entities.get("menu_item") or entities.get("service")
        quantity = entities.get("quantity", 1)
        if not isinstance(quantity, int) or quantity < 1:
            quantity = 1
        
        delivery_method = entities.get("delivery_method")
        customer_name = entities.get("customer_name")
        customer_phone = entities.get("customer_phone")
        
        # Handle delivery method
        if delivery_method:
            self.order_state.set_delivery_method(delivery_method)
        
        # Handle customer info
        if customer_name or customer_phone:
            self.order_state.set_customer_info(customer_name, customer_phone)
        
        if action == "PLACE_ORDER":
            if not menu_item:
                return {"error": "No menu item specified", "action": "none"}
            
            # Find price from menu data
            price = 0
            menu_item_id = None
            if menu_data:
                menu_lower = menu_item.lower()
                for item in menu_data:
                    if menu_lower in item.get("name", "").lower() or item.get("name", "").lower() in menu_lower:
                        price = item.get("price", 0)
                        menu_item_id = item.get("id")
                        break
            
            return self.order_state.add_item(
                name=menu_item,
                price=price,
                quantity=quantity,
                menu_item_id=menu_item_id
            )
        
        elif action == "CONFIRM_ORDER":
            try:
                if self.order_state.status == OrderStatus.CONFIRMED:
                    return {"error": "Order already confirmed", "action": "none"}
                
                # Set status to pending confirmation first
                summary = self.order_state.request_confirmation()
                
                # Then confirm
                return self.order_state.confirm()
            except ValidationError as e:
                return {"error": str(e), "action": "none"}
        
        elif action == "CANCEL_ORDER":
            self.order_state.cancel()
            return {"action": "cancelled", "message": "Order cancelled"}
        
        return {"action": "none", "message": "No order action taken"}
    
    def has_collected(self, field: str) -> bool:
        """Check if a field has been collected."""
        return field in self.collected_fields and self.collected_fields[field] is not None
    
    def get_context_for_prompt(self) -> str:
        """Get memory as context string for the next turn."""
        context_parts = []
        
        if self.collected_fields:
            collected = ", ".join([f"{k}: {v}" for k, v in self.collected_fields.items() if v])
            context_parts.append(f"Already collected: {collected}")
        
        if self.price_mentioned:
            context_parts.append("Price has already been mentioned")
        
        if self.questions_asked:
            context_parts.append(f"Questions already asked: {', '.join(self.questions_asked[-3:])}")
        
        if self.order_state.items:
            items = ", ".join([f"{i.quantity}x {i.name}" for i in self.order_state.items])
            context_parts.append(f"Current order: {items}")
        
        if self.escalation_count > 0:
            context_parts.append(f"Previous escalations: {self.escalation_count}")
        
        return " | ".join(context_parts) if context_parts else "No previous context"
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize memory for session storage."""
        return {
            "collected_fields": self.collected_fields,
            "order_state": self.order_state.to_dict(),
            "interaction_count": self.interaction_count,
            "intent_history": self.intent_history[-10:],  # Keep last 10
            "action_history": self.action_history[-10:],
            "sentiment_history": self.sentiment_history[-10:],
            "escalation_count": self.escalation_count,
            "price_mentioned": self.price_mentioned,
            "questions_asked": self.questions_asked,
            "last_intent": self.last_intent,
            "last_action": self.last_action,
            "pending_confirmation": self.pending_confirmation,
            "session_start": self.session_start.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConversationMemory":
        """Deserialize memory from session storage."""
        memory = cls()
        memory.collected_fields = data.get("collected_fields", {})
        memory.order_state = OrderState.from_dict(data.get("order_state", {}))
        memory.interaction_count = data.get("interaction_count", 0)
        memory.intent_history = data.get("intent_history", [])
        memory.action_history = data.get("action_history", [])
        memory.sentiment_history = data.get("sentiment_history", [])
        memory.escalation_count = data.get("escalation_count", 0)
        memory.price_mentioned = data.get("price_mentioned", False)
        memory.questions_asked = data.get("questions_asked", [])
        memory.last_intent = data.get("last_intent")
        memory.last_action = data.get("last_action")
        memory.pending_confirmation = data.get("pending_confirmation")
        
        if data.get("session_start"):
            try:
                memory.session_start = datetime.fromisoformat(data["session_start"])
            except:
                pass
        
        return memory


# =============================================================================
# RETRY LOGIC
# =============================================================================

class RetryConfig:
    """Configuration for retry behavior."""
    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 30.0,
        exponential_base: float = 2.0,
        jitter: bool = True
    ):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter


async def retry_with_backoff(
    func,
    config: RetryConfig = None,
    exceptions: tuple = (Exception,),
    on_retry: callable = None
):
    """
    Retry a function with exponential backoff.
    
    Args:
        func: Async function to retry
        config: RetryConfig instance
        exceptions: Tuple of exceptions to catch
        on_retry: Optional callback(retry_count, exception, delay)
    
    Returns:
        Result of successful function call
    
    Raises:
        Last exception after all retries exhausted
    """
    import random
    
    if config is None:
        config = RetryConfig()
    
    last_exception = None
    
    for attempt in range(config.max_retries + 1):
        try:
            return await func()
        except exceptions as e:
            last_exception = e
            
            if attempt == config.max_retries:
                raise
            
            # Calculate delay with exponential backoff
            delay = min(
                config.base_delay * (config.exponential_base ** attempt),
                config.max_delay
            )
            
            # Add jitter
            if config.jitter:
                delay = delay * (0.5 + random.random())
            
            # Log retry
            if on_retry:
                on_retry(attempt + 1, e, delay)
            
            await asyncio.sleep(delay)
    
    raise last_exception
