"""
Service for caching results to improve performance.
"""
import os
import time
import hashlib
import pickle
from typing import Any, Dict, Optional, Tuple, TypeVar, Callable, List

import diskcache

T = TypeVar('T')


class CacheService:
    """
    Service for caching results to improve performance.
    """

    def __init__(self, cache_dir: str = ".cache", ttl: int = 3600):
        """
        Initialize the CacheService.

        Args:
            cache_dir: The directory to store cache files.
            ttl: Time-to-live for cache entries in seconds (default: 1 hour).
        """
        os.makedirs(cache_dir, exist_ok=True)
        self._cache = diskcache.Cache(cache_dir)
        self._ttl = ttl
        self._memory_cache: Dict[str, Tuple[Any, float]] = {}

    def get(self, key: str) -> Optional[Any]:
        """
        Get a value from the cache.

        Args:
            key: The cache key.

        Returns:
            Optional[Any]: The cached value, or None if not found or expired.
        """
        # Try memory cache first
        if key in self._memory_cache:
            value, expiry = self._memory_cache[key]
            if expiry > time.time():
                return value
            else:
                # Remove expired entry
                del self._memory_cache[key]

        # Try disk cache
        try:
            return self._cache.get(key)
        except Exception as e:
            print(f"Error getting cache entry for {key}: {e}")
            return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None, memory_only: bool = False) -> None:
        """
        Set a value in the cache.

        Args:
            key: The cache key.
            value: The value to cache.
            ttl: Time-to-live in seconds. If None, use the default TTL.
            memory_only: Whether to store the value only in memory.
        """
        ttl = ttl or self._ttl
        expiry = time.time() + ttl

        # Store in memory cache
        self._memory_cache[key] = (value, expiry)

        # Store in disk cache if not memory_only
        if not memory_only:
            try:
                self._cache.set(key, value, expire=ttl)
            except Exception as e:
                print(f"Error setting cache entry for {key}: {e}")

    def delete(self, key: str) -> bool:
        """
        Delete a value from the cache.

        Args:
            key: The cache key.

        Returns:
            bool: True if the key was deleted, False otherwise.
        """
        # Remove from memory cache
        if key in self._memory_cache:
            del self._memory_cache[key]

        # Remove from disk cache
        try:
            return self._cache.delete(key)
        except Exception as e:
            print(f"Error deleting cache entry for {key}: {e}")
            return False

    def clear(self) -> None:
        """Clear all cache entries."""
        self._memory_cache.clear()
        try:
            self._cache.clear()
        except Exception as e:
            print(f"Error clearing cache: {e}")

    def cached(self, ttl: Optional[int] = None, key_prefix: str = "") -> Callable:
        """
        Decorator for caching function results.

        Args:
            ttl: Time-to-live in seconds. If None, use the default TTL.
            key_prefix: Prefix for the cache key.

        Returns:
            Callable: The decorated function.
        """
        def decorator(func: Callable) -> Callable:
            def wrapper(*args: Any, **kwargs: Any) -> Any:
                # Generate a cache key based on the function name, arguments, and key_prefix
                key_parts = [key_prefix, func.__name__]
                
                # Add args to key
                for arg in args:
                    try:
                        key_parts.append(str(arg))
                    except Exception:
                        # If we can't convert to string, use the hash of the pickled object
                        key_parts.append(hashlib.md5(pickle.dumps(arg)).hexdigest())
                
                # Add kwargs to key
                for k, v in sorted(kwargs.items()):
                    key_parts.append(k)
                    try:
                        key_parts.append(str(v))
                    except Exception:
                        # If we can't convert to string, use the hash of the pickled object
                        key_parts.append(hashlib.md5(pickle.dumps(v)).hexdigest())
                
                cache_key = ":".join(key_parts)
                
                # Try to get from cache
                cached_value = self.get(cache_key)
                if cached_value is not None:
                    return cached_value
                
                # Call the function and cache the result
                result = func(*args, **kwargs)
                self.set(cache_key, result, ttl=ttl)
                return result
            
            return wrapper
        
        return decorator

    def invalidate_by_prefix(self, prefix: str) -> int:
        """
        Invalidate all cache entries with keys starting with the given prefix.

        Args:
            prefix: The prefix to match.

        Returns:
            int: The number of entries invalidated.
        """
        count = 0
        
        # Invalidate memory cache
        keys_to_delete = [k for k in self._memory_cache.keys() if k.startswith(prefix)]
        for key in keys_to_delete:
            del self._memory_cache[key]
            count += 1
        
        # Invalidate disk cache
        try:
            for key in self._cache.iterkeys():
                if key.startswith(prefix):
                    self._cache.delete(key)
                    count += 1
        except Exception as e:
            print(f"Error invalidating cache entries with prefix {prefix}: {e}")
        
        return count

    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dict[str, Any]: Cache statistics.
        """
        stats = {
            "memory_cache_size": len(self._memory_cache),
            "memory_cache_keys": list(self._memory_cache.keys()),
        }
        
        try:
            stats.update({
                "disk_cache_size": len(self._cache),
                "disk_cache_directory": self._cache.directory,
                "disk_cache_disk_size": self._cache.volume(),
            })
        except Exception as e:
            print(f"Error getting disk cache stats: {e}")
        
        return stats
