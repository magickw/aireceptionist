"""Redis Caching Service for Business Context and Templates"""

import json
import hashlib
from typing import Optional, Dict, Any, List
from datetime import timedelta
from functools import wraps

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False


class CacheService:
    """
    Redis-based caching service for business context, templates, and other frequently accessed data.
    Provides automatic serialization, TTL management, and cache invalidation.
    """
    
    def __init__(self, redis_url: str = None, default_ttl: int = 300):
        """
        Initialize cache service.
        
        Args:
            redis_url: Redis connection URL
            default_ttl: Default time-to-live in seconds (5 minutes)
        """
        self.default_ttl = default_ttl
        self.client = None
        
        if REDIS_AVAILABLE and redis_url:
            try:
                self.client = redis.from_url(redis_url, decode_responses=True)
                # Test connection
                self.client.ping()
                print("[CacheService] Connected to Redis")
            except Exception as e:
                print(f"[CacheService] Failed to connect to Redis: {e}")
                self.client = None
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            key: Cache key
        
        Returns:
            Cached value or None if not found
        """
        if not self.client:
            return None
        
        try:
            value = self.client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            print(f"[CacheService] Error getting key '{key}': {e}")
            return None
    
    def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """
        Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache (must be JSON-serializable)
            ttl: Time-to-live in seconds (uses default if not provided)
        
        Returns:
            True if successful, False otherwise
        """
        if not self.client:
            return False
        
        try:
            serialized = json.dumps(value)
            ttl = ttl or self.default_ttl
            self.client.setex(key, ttl, serialized)
            return True
        except Exception as e:
            print(f"[CacheService] Error setting key '{key}': {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """
        Delete key from cache.
        
        Args:
            key: Cache key
        
        Returns:
            True if successful, False otherwise
        """
        if not self.client:
            return False
        
        try:
            self.client.delete(key)
            return True
        except Exception as e:
            print(f"[CacheService] Error deleting key '{key}': {e}")
            return False
    
    def delete_pattern(self, pattern: str) -> int:
        """
        Delete all keys matching a pattern.
        
        Args:
            pattern: Redis key pattern (e.g., "business:*")
        
        Returns:
            Number of keys deleted
        """
        if not self.client:
            return 0
        
        try:
            keys = self.client.keys(pattern)
            if keys:
                return self.client.delete(*keys)
            return 0
        except Exception as e:
            print(f"[CacheService] Error deleting pattern '{pattern}': {e}")
            return 0
    
    def exists(self, key: str) -> bool:
        """
        Check if key exists in cache.
        
        Args:
            key: Cache key
        
        Returns:
            True if key exists, False otherwise
        """
        if not self.client:
            return False
        
        try:
            return bool(self.client.exists(key))
        except Exception as e:
            print(f"[CacheService] Error checking key '{key}': {e}")
            return False
    
    def clear_all(self) -> bool:
        """
        Clear all cached data.
        
        Returns:
            True if successful, False otherwise
        """
        if not self.client:
            return False
        
        try:
            self.client.flushdb()
            return True
        except Exception as e:
            print(f"[CacheService] Error clearing cache: {e}")
            return False
    
    def get_or_set(
        self,
        key: str,
        value_func: callable,
        ttl: Optional[int] = None
    ) -> Any:
        """
        Get value from cache or compute and cache it.
        
        Args:
            key: Cache key
            value_func: Function to compute value if not in cache
            ttl: Time-to-live in seconds
        
        Returns:
            Cached or computed value
        """
        value = self.get(key)
        if value is not None:
            return value
        
        # Compute value
        value = value_func()
        
        # Cache it
        self.set(key, value, ttl)
        
        return value


# Business-specific cache keys
class CacheKeys:
    """Standardized cache keys for different data types"""
    
    @staticmethod
    def business_context(business_id: int) -> str:
        """Cache key for business context"""
        return f"business:context:{business_id}"
    
    @staticmethod
    def business_template(business_type: str) -> str:
        """Cache key for business template"""
        return f"business:template:{business_type}"
    
    @staticmethod
    def menu_items(business_id: int) -> str:
        """Cache key for menu items"""
        return f"business:menu:{business_id}"
    
    @staticmethod
    def knowledge_base(business_id: int, query_hash: str) -> str:
        """Cache key for knowledge base results"""
        return f"kb:{business_id}:{query_hash}"
    
    @staticmethod
    def intent_classification(business_type: str) -> str:
        """Cache key for intent classifications"""
        return f"intent:class:{business_type}"
    
    @staticmethod
    def session_state(session_id: str) -> str:
        """Cache key for session state"""
        return f"session:state:{session_id}"


# Decorator for caching function results
def cached_result(
    cache_service: CacheService,
    key_func: callable,
    ttl: Optional[int] = None
):
    """
    Decorator to cache function results.
    
    Args:
        cache_service: CacheService instance
        key_func: Function to generate cache key from function arguments
        ttl: Time-to-live in seconds
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            key = key_func(*args, **kwargs)
            
            # Try to get from cache
            cached = cache_service.get(key)
            if cached is not None:
                return cached
            
            # Compute result
            result = func(*args, **kwargs)
            
            # Cache it
            cache_service.set(key, result, ttl)
            
            return result
        return wrapper
    return decorator


# Singleton instance (initialized later with Redis URL)
cache_service: Optional[CacheService] = None


def init_cache(redis_url: str = None, default_ttl: int = 300) -> CacheService:
    """
    Initialize the global cache service.
    
    Args:
        redis_url: Redis connection URL
        default_ttl: Default time-to-live in seconds
    
    Returns:
        CacheService instance
    """
    global cache_service
    cache_service = CacheService(redis_url, default_ttl)
    return cache_service


def get_cache() -> Optional[CacheService]:
    """
    Get the global cache service instance.
    
    Returns:
        CacheService instance or None if not initialized
    """
    return cache_service


# Helper function to create hash from data
def create_hash(data: Any) -> str:
    """Create MD5 hash of data for cache keys"""
    serialized = json.dumps(data, sort_keys=True)
    return hashlib.md5(serialized.encode()).hexdigest()[:16]