"""Comprehensive Error Handling with Fallback Strategies"""

from typing import Optional, Dict, Any, Callable, Type, Tuple
from functools import wraps
from datetime import datetime
import logging
import traceback


# Configure logging
logger = logging.getLogger(__name__)


class ErrorHandler:
    """
    Centralized error handling with fallback strategies.
    Provides graceful degradation and recovery for various failure scenarios.
    """
    
    def __init__(self):
        self.fallback_handlers = {}
        self.error_counts = {}
        self.max_retries = 3
    
    def register_fallback(
        self,
        error_type: Type[Exception],
        handler: Callable[[Exception], Any]
    ):
        """
        Register a fallback handler for a specific error type.
        
        Args:
            error_type: Exception type to handle
            handler: Function that takes the exception and returns a fallback value
        """
        self.fallback_handlers[error_type] = handler
    
    def handle(
        self,
        error: Exception,
        context: Optional[Dict[str, Any]] = None
    ) -> Any:
        """
        Handle an error with registered fallback strategies.
        
        Args:
            error: The exception to handle
            context: Additional context about the error
        
        Returns:
            Fallback value or raises the error if no handler is registered
        """
        error_type = type(error)
        
        # Log the error
        logger.error(
            f"Error occurred: {error_type.__name__}: {str(error)}",
            extra={"context": context, "traceback": traceback.format_exc()}
        )
        
        # Increment error count
        error_key = f"{error_type.__name__}:{str(error)}"
        self.error_counts[error_key] = self.error_counts.get(error_key, 0) + 1
        
        # Find and execute fallback handler
        for registered_type, handler in self.fallback_handlers.items():
            if isinstance(error, registered_type):
                try:
                    return handler(error)
                except Exception as fallback_error:
                    logger.error(
                        f"Fallback handler failed for {error_type.__name__}: {fallback_error}"
                    )
                    continue
        
        # No handler found - re-raise
        raise error
    
    def get_error_stats(self) -> Dict[str, int]:
        """Get error statistics"""
        return self.error_counts.copy()
    
    def clear_error_stats(self):
        """Clear error statistics"""
        self.error_counts.clear()


# Global error handler instance
error_handler = ErrorHandler()


# Fallback responses for common scenarios
class FallbackResponses:
    """Standardized fallback responses for various failure scenarios"""
    
    @staticmethod
    def generic_error() -> Dict[str, Any]:
        """Generic error response"""
        return {
            "intent": "unknown",
            "confidence": 0.0,
            "selected_action": "PROVIDE_INFO",
            "suggested_response": "I apologize, but I'm having some technical difficulties. Let me connect you with a human representative who can better assist you.",
            "requires_approval": True,
            "error": "technical_difficulty",
            "fallback_used": True
        }
    
    @staticmethod
    def model_unavailable() -> Dict[str, Any]:
        """Fallback when AI model is unavailable"""
        return {
            "intent": "unknown",
            "confidence": 0.0,
            "selected_action": "HUMAN_INTERVENTION",
            "suggested_response": "I'm currently experiencing some technical issues. Please hold while I connect you with a team member who can help you right away.",
            "requires_approval": True,
            "error": "model_unavailable",
            "fallback_used": True
        }
    
    @staticmethod
    def database_error() -> Dict[str, Any]:
        """Fallback when database is unavailable"""
        return {
            "intent": "unknown",
            "confidence": 0.0,
            "selected_action": "PROVIDE_INFO",
            "suggested_response": "I apologize, but I'm having trouble accessing our systems. Let me connect you with someone who can assist you.",
            "requires_approval": True,
            "error": "database_error",
            "fallback_used": True
        }
    
    @staticmethod
    def timeout_error() -> Dict[str, Any]:
        """Fallback when operation times out"""
        return {
            "intent": "unknown",
            "confidence": 0.0,
            "selected_action": "HUMAN_INTERVENTION",
            "suggested_response": "I apologize for the delay. Let me connect you with a team member who can help you immediately.",
            "requires_approval": True,
            "error": "timeout",
            "fallback_used": True
        }
    
    @staticmethod
    def validation_error(message: str) -> Dict[str, Any]:
        """Fallback when validation fails"""
        return {
            "intent": "unknown",
            "confidence": 0.0,
            "selected_action": "COLLECT_INFO",
            "suggested_response": f"I apologize, but I need more information. {message}",
            "requires_approval": False,
            "error": "validation_error",
            "fallback_used": True
        }
    
    @staticmethod
    def business_context_not_found(business_type: str) -> Dict[str, Any]:
        """Fallback when business context is not found"""
        return {
            "intent": "general_inquiry",
            "confidence": 0.5,
            "selected_action": "PROVIDE_INFO",
            "suggested_response": "I'd be happy to help you. How can I assist you today?",
            "requires_approval": False,
            "error": "business_context_not_found",
            "fallback_used": True,
            "business_type": business_type
        }


# Register default fallback handlers
error_handler.register_fallback(
    ConnectionError,
    lambda e: FallbackResponses.database_error()
)

error_handler.register_fallback(
    TimeoutError,
    lambda e: FallbackResponses.timeout_error()
)

error_handler.register_fallback(
    ValueError,
    lambda e: FallbackResponses.validation_error(str(e))
)


# Decorator for error handling
def handle_errors(
    fallback_response: Optional[Callable[[Exception], Dict[str, Any]]] = None,
    log_error: bool = True,
    raise_on_error: bool = False
):
    """
    Decorator for automatic error handling with fallbacks.
    
    Args:
        fallback_response: Function that returns fallback response
        log_error: Whether to log errors
        raise_on_error: Whether to re-raise errors after handling
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if log_error:
                    logger.error(
                        f"Error in {func.__name__}: {e}",
                        extra={"args": args, "kwargs": kwargs}
                    )
                
                # Use provided fallback or error handler
                if fallback_response:
                    result = fallback_response(e)
                else:
                    try:
                        result = error_handler.handle(e, context={"function": func.__name__})
                    except Exception:
                        result = FallbackResponses.generic_error()
                
                # Mark as fallback
                if isinstance(result, dict):
                    result["fallback_used"] = True
                    result["original_error"] = str(e)
                
                if raise_on_error:
                    raise e
                
                return result
        return wrapper
    return decorator


# Circuit breaker pattern for preventing cascading failures
class CircuitBreaker:
    """
    Circuit breaker to prevent cascading failures.
    Opens circuit after too many failures, allows limited traffic for recovery.
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        timeout: int = 60,
        half_open_attempts: int = 3
    ):
        """
        Initialize circuit breaker.
        
        Args:
            failure_threshold: Number of failures before opening circuit
            timeout: Seconds to wait before attempting recovery
            half_open_attempts: Number of attempts to try in half-open state
        """
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.half_open_attempts = half_open_attempts
        
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "closed"  # closed, open, half_open
        self.half_open_count = 0
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function with circuit breaker protection.
        
        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
        
        Returns:
            Function result or raises CircuitBreakerOpenError
        """
        if self.state == "open":
            # Check if we should attempt recovery
            if (datetime.now() - self.last_failure_time).total_seconds() > self.timeout:
                self.state = "half_open"
                self.half_open_count = 0
                logger.info("Circuit breaker entering half-open state")
            else:
                raise CircuitBreakerOpenError("Circuit breaker is open")
        
        try:
            result = func(*args, **kwargs)
            
            # Success - reset or move to closed
            if self.state == "half_open":
                self.half_open_count += 1
                if self.half_open_count >= self.half_open_attempts:
                    self.state = "closed"
                    self.failure_count = 0
                    logger.info("Circuit breaker closed after successful recovery")
            else:
                self.failure_count = 0
            
            return result
        
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = datetime.now()
            
            if self.failure_count >= self.failure_threshold:
                self.state = "open"
                logger.warning(
                    f"Circuit breaker opened after {self.failure_count} failures"
                )
            
            raise e


class CircuitBreakerOpenError(Exception):
    """Raised when circuit breaker is open"""
    pass


# Retry decorator with exponential backoff
def retry_with_fallback(
    max_retries: int = 3,
    fallback: Optional[Callable] = None,
    exceptions: Tuple[Type[Exception], ...] = (Exception,)
):
    """
    Decorator for retrying functions with exponential backoff and fallback.
    
    Args:
        max_retries: Maximum number of retry attempts
        fallback: Fallback function to call if all retries fail
        exceptions: Tuple of exception types to catch and retry
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            import time
            
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if attempt == max_retries - 1:
                        # Last attempt failed
                        if fallback:
                            return fallback(e)
                        raise e
                    
                    # Wait before retry
                    wait_time = 2 ** attempt
                    logger.warning(
                        f"Attempt {attempt + 1}/{max_retries} failed for {func.__name__}: {e}. "
                        f"Retrying in {wait_time}s..."
                    )
                    time.sleep(wait_time)
        
        return wrapper
    return decorator