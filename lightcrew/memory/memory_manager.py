"""
Memory management for LightCrew framework.
"""

import asyncio
import json
import time
from typing import Any, Dict, List, Optional, Union
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timedelta

from ..utils.logger import get_logger


logger = get_logger(__name__)


@dataclass
class MemoryItem:
    """A single memory item."""
    key: str
    value: Any
    timestamp: datetime
    ttl: Optional[float] = None  # Time to live in seconds
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
    
    @property
    def is_expired(self) -> bool:
        """Check if the memory item has expired."""
        if self.ttl is None:
            return False
        return (datetime.now() - self.timestamp).total_seconds() > self.ttl


class MemoryBackend(ABC):
    """Abstract base class for memory backends."""
    
    @abstractmethod
    async def store(self, key: str, value: Any, ttl: Optional[float] = None) -> bool:
        """Store a value in memory."""
        pass
    
    @abstractmethod
    async def retrieve(self, key: str) -> Optional[Any]:
        """Retrieve a value from memory."""
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete a value from memory."""
        pass
    
    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Check if a key exists in memory."""
        pass
    
    @abstractmethod
    async def clear(self) -> bool:
        """Clear all memory."""
        pass
    
    @abstractmethod
    async def keys(self, pattern: str = "*") -> List[str]:
        """Get all keys matching a pattern."""
        pass


class InMemoryBackend(MemoryBackend):
    """In-memory backend for development and testing."""
    
    def __init__(self):
        self._storage: Dict[str, MemoryItem] = {}
        self._lock = asyncio.Lock()
    
    async def store(self, key: str, value: Any, ttl: Optional[float] = None) -> bool:
        """Store a value in memory."""
        async with self._lock:
            try:
                item = MemoryItem(
                    key=key,
                    value=value,
                    timestamp=datetime.now(),
                    ttl=ttl
                )
                self._storage[key] = item
                logger.debug(f"Stored memory item: {key}")
                return True
            except Exception as e:
                logger.error(f"Failed to store memory item {key}: {e}")
                return False
    
    async def retrieve(self, key: str) -> Optional[Any]:
        """Retrieve a value from memory."""
        async with self._lock:
            try:
                item = self._storage.get(key)
                if item is None:
                    return None
                
                # Check expiration
                if item.is_expired:
                    del self._storage[key]
                    logger.debug(f"Memory item expired and removed: {key}")
                    return None
                
                logger.debug(f"Retrieved memory item: {key}")
                return item.value
            except Exception as e:
                logger.error(f"Failed to retrieve memory item {key}: {e}")
                return None
    
    async def delete(self, key: str) -> bool:
        """Delete a value from memory."""
        async with self._lock:
            try:
                if key in self._storage:
                    del self._storage[key]
                    logger.debug(f"Deleted memory item: {key}")
                    return True
                return False
            except Exception as e:
                logger.error(f"Failed to delete memory item {key}: {e}")
                return False
    
    async def exists(self, key: str) -> bool:
        """Check if a key exists in memory."""
        async with self._lock:
            item = self._storage.get(key)
            if item is None:
                return False
            
            # Check expiration
            if item.is_expired:
                del self._storage[key]
                return False
            
            return True
    
    async def clear(self) -> bool:
        """Clear all memory."""
        async with self._lock:
            try:
                self._storage.clear()
                logger.info("Cleared all memory")
                return True
            except Exception as e:
                logger.error(f"Failed to clear memory: {e}")
                return False
    
    async def keys(self, pattern: str = "*") -> List[str]:
        """Get all keys matching a pattern."""
        async with self._lock:
            try:
                # Simple pattern matching (only supports * wildcard)
                if pattern == "*":
                    keys = list(self._storage.keys())
                else:
                    # Basic pattern matching
                    import fnmatch
                    keys = [k for k in self._storage.keys() if fnmatch.fnmatch(k, pattern)]
                
                # Filter out expired items
                valid_keys = []
                for key in keys:
                    item = self._storage.get(key)
                    if item and not item.is_expired:
                        valid_keys.append(key)
                    elif item and item.is_expired:
                        del self._storage[key]
                
                return valid_keys
            except Exception as e:
                logger.error(f"Failed to get keys with pattern {pattern}: {e}")
                return []
    
    async def cleanup_expired(self):
        """Remove expired items from memory."""
        async with self._lock:
            expired_keys = []
            for key, item in self._storage.items():
                if item.is_expired:
                    expired_keys.append(key)
            
            for key in expired_keys:
                del self._storage[key]
            
            if expired_keys:
                logger.info(f"Cleaned up {len(expired_keys)} expired memory items")


class MemoryManager:
    """
    Lightweight memory manager with pluggable backends.
    
    Example:
        >>> memory = MemoryManager()
        >>> await memory.store("key", "value")
        >>> value = await memory.retrieve("key")
    """
    
    def __init__(
        self,
        backend: Optional[MemoryBackend] = None,
        default_ttl: Optional[float] = None,
        auto_cleanup: bool = True,
        cleanup_interval: float = 300.0  # 5 minutes
    ):
        """
        Initialize memory manager.
        
        Args:
            backend: Memory backend to use (defaults to InMemoryBackend)
            default_ttl: Default TTL for stored items in seconds
            auto_cleanup: Whether to automatically cleanup expired items
            cleanup_interval: Interval between cleanup runs in seconds
        """
        self.backend = backend or InMemoryBackend()
        self.default_ttl = default_ttl
        self.auto_cleanup = auto_cleanup
        self.cleanup_interval = cleanup_interval
        
        # Statistics
        self.stats = {
            "stores": 0,
            "retrievals": 0,
            "hits": 0,
            "misses": 0,
            "deletes": 0
        }
        
        # Start cleanup task if enabled
        self._cleanup_task = None
        if auto_cleanup and isinstance(self.backend, InMemoryBackend):
            self._start_cleanup_task()
        
        logger.info(f"Memory manager initialized with {self.backend.__class__.__name__}")
    
    def _start_cleanup_task(self):
        """Start the automatic cleanup task."""
        async def cleanup_loop():
            while True:
                try:
                    await asyncio.sleep(self.cleanup_interval)
                    if isinstance(self.backend, InMemoryBackend):
                        await self.backend.cleanup_expired()
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"Cleanup task error: {e}")
        
        self._cleanup_task = asyncio.create_task(cleanup_loop())
    
    async def store(
        self, 
        key: str, 
        value: Any, 
        ttl: Optional[float] = None,
        namespace: str = "default"
    ) -> bool:
        """
        Store a value in memory.
        
        Args:
            key: Storage key
            value: Value to store
            ttl: Time to live in seconds (uses default_ttl if None)
            namespace: Namespace for the key
            
        Returns:
            True if successful, False otherwise
        """
        full_key = f"{namespace}:{key}"
        effective_ttl = ttl if ttl is not None else self.default_ttl
        
        try:
            success = await self.backend.store(full_key, value, effective_ttl)
            if success:
                self.stats["stores"] += 1
            return success
        except Exception as e:
            logger.error(f"Failed to store {full_key}: {e}")
            return False
    
    async def retrieve(self, key: str, namespace: str = "default") -> Optional[Any]:
        """
        Retrieve a value from memory.
        
        Args:
            key: Storage key
            namespace: Namespace for the key
            
        Returns:
            The stored value or None if not found
        """
        full_key = f"{namespace}:{key}"
        
        try:
            self.stats["retrievals"] += 1
            value = await self.backend.retrieve(full_key)
            
            if value is not None:
                self.stats["hits"] += 1
            else:
                self.stats["misses"] += 1
            
            return value
        except Exception as e:
            logger.error(f"Failed to retrieve {full_key}: {e}")
            self.stats["misses"] += 1
            return None
    
    async def delete(self, key: str, namespace: str = "default") -> bool:
        """
        Delete a value from memory.
        
        Args:
            key: Storage key
            namespace: Namespace for the key
            
        Returns:
            True if successful, False otherwise
        """
        full_key = f"{namespace}:{key}"
        
        try:
            success = await self.backend.delete(full_key)
            if success:
                self.stats["deletes"] += 1
            return success
        except Exception as e:
            logger.error(f"Failed to delete {full_key}: {e}")
            return False
    
    async def exists(self, key: str, namespace: str = "default") -> bool:
        """Check if a key exists in memory."""
        full_key = f"{namespace}:{key}"
        
        try:
            return await self.backend.exists(full_key)
        except Exception as e:
            logger.error(f"Failed to check existence of {full_key}: {e}")
            return False
    
    async def clear(self, namespace: Optional[str] = None) -> bool:
        """
        Clear memory.
        
        Args:
            namespace: If provided, only clear keys in this namespace
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if namespace is None:
                return await self.backend.clear()
            else:
                # Clear specific namespace
                keys = await self.backend.keys(f"{namespace}:*")
                for key in keys:
                    await self.backend.delete(key)
                return True
        except Exception as e:
            logger.error(f"Failed to clear memory: {e}")
            return False
    
    async def keys(self, pattern: str = "*", namespace: str = "default") -> List[str]:
        """
        Get keys matching a pattern.
        
        Args:
            pattern: Pattern to match
            namespace: Namespace to search in
            
        Returns:
            List of matching keys (without namespace prefix)
        """
        try:
            full_pattern = f"{namespace}:{pattern}"
            full_keys = await self.backend.keys(full_pattern)
            
            # Remove namespace prefix
            prefix = f"{namespace}:"
            return [key[len(prefix):] for key in full_keys if key.startswith(prefix)]
        except Exception as e:
            logger.error(f"Failed to get keys: {e}")
            return []
    
    def get_stats(self) -> Dict[str, Any]:
        """Get memory statistics."""
        hit_rate = (
            self.stats["hits"] / self.stats["retrievals"] 
            if self.stats["retrievals"] > 0 else 0
        )
        
        return {
            **self.stats,
            "hit_rate": hit_rate,
            "backend": self.backend.__class__.__name__,
            "default_ttl": self.default_ttl,
            "auto_cleanup": self.auto_cleanup
        }
    
    async def close(self):
        """Close the memory manager and cleanup resources."""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Memory manager closed")
    
    def __del__(self):
        """Cleanup when object is destroyed."""
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()