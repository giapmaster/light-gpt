"""
Memory backend implementations for LightCrew framework.
"""

import json
import asyncio
from typing import Any, Dict, List, Optional

from .memory_manager import MemoryBackend
from ..utils.logger import get_logger


logger = get_logger(__name__)


# Re-export InMemoryBackend from memory_manager for convenience
from .memory_manager import InMemoryBackend


class RedisBackend(MemoryBackend):
    """Redis backend for production use."""
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        password: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize Redis backend.
        
        Args:
            host: Redis host
            port: Redis port
            db: Redis database number
            password: Redis password
            **kwargs: Additional Redis connection parameters
        """
        self.host = host
        self.port = port
        self.db = db
        self.password = password
        self.kwargs = kwargs
        self._redis = None
        self._connected = False
    
    async def _connect(self):
        """Connect to Redis."""
        if self._connected:
            return
        
        try:
            import redis.asyncio as redis
            
            self._redis = redis.Redis(
                host=self.host,
                port=self.port,
                db=self.db,
                password=self.password,
                decode_responses=True,
                **self.kwargs
            )
            
            # Test connection
            await self._redis.ping()
            self._connected = True
            logger.info(f"Connected to Redis at {self.host}:{self.port}")
            
        except ImportError:
            raise ImportError("Redis package not installed. Install with: pip install redis")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise
    
    async def store(self, key: str, value: Any, ttl: Optional[float] = None) -> bool:
        """Store a value in Redis."""
        await self._connect()
        
        try:
            # Serialize value
            serialized_value = json.dumps(value, default=str)
            
            if ttl is not None:
                await self._redis.setex(key, int(ttl), serialized_value)
            else:
                await self._redis.set(key, serialized_value)
            
            logger.debug(f"Stored in Redis: {key}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store in Redis {key}: {e}")
            return False
    
    async def retrieve(self, key: str) -> Optional[Any]:
        """Retrieve a value from Redis."""
        await self._connect()
        
        try:
            value = await self._redis.get(key)
            if value is None:
                return None
            
            # Deserialize value
            deserialized_value = json.loads(value)
            logger.debug(f"Retrieved from Redis: {key}")
            return deserialized_value
            
        except Exception as e:
            logger.error(f"Failed to retrieve from Redis {key}: {e}")
            return None
    
    async def delete(self, key: str) -> bool:
        """Delete a value from Redis."""
        await self._connect()
        
        try:
            result = await self._redis.delete(key)
            logger.debug(f"Deleted from Redis: {key}")
            return result > 0
            
        except Exception as e:
            logger.error(f"Failed to delete from Redis {key}: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if a key exists in Redis."""
        await self._connect()
        
        try:
            result = await self._redis.exists(key)
            return result > 0
            
        except Exception as e:
            logger.error(f"Failed to check existence in Redis {key}: {e}")
            return False
    
    async def clear(self) -> bool:
        """Clear all keys in the Redis database."""
        await self._connect()
        
        try:
            await self._redis.flushdb()
            logger.info("Cleared Redis database")
            return True
            
        except Exception as e:
            logger.error(f"Failed to clear Redis database: {e}")
            return False
    
    async def keys(self, pattern: str = "*") -> List[str]:
        """Get all keys matching a pattern in Redis."""
        await self._connect()
        
        try:
            keys = await self._redis.keys(pattern)
            return keys
            
        except Exception as e:
            logger.error(f"Failed to get keys from Redis with pattern {pattern}: {e}")
            return []
    
    async def close(self):
        """Close Redis connection."""
        if self._redis:
            await self._redis.close()
            self._connected = False
            logger.info("Closed Redis connection")


class FileBackend(MemoryBackend):
    """File-based backend for persistence without external dependencies."""
    
    def __init__(self, file_path: str = "lightcrew_memory.json"):
        """
        Initialize file backend.
        
        Args:
            file_path: Path to the storage file
        """
        self.file_path = file_path
        self._data: Dict[str, Any] = {}
        self._lock = asyncio.Lock()
        self._loaded = False
    
    async def _load_data(self):
        """Load data from file."""
        if self._loaded:
            return
        
        try:
            import os
            if os.path.exists(self.file_path):
                with open(self.file_path, 'r') as f:
                    self._data = json.load(f)
                logger.info(f"Loaded memory data from {self.file_path}")
            else:
                self._data = {}
                logger.info(f"Memory file {self.file_path} not found, starting fresh")
            
            self._loaded = True
            
        except Exception as e:
            logger.error(f"Failed to load memory data: {e}")
            self._data = {}
            self._loaded = True
    
    async def _save_data(self):
        """Save data to file."""
        try:
            import os
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.file_path) or '.', exist_ok=True)
            
            with open(self.file_path, 'w') as f:
                json.dump(self._data, f, indent=2, default=str)
            
            logger.debug(f"Saved memory data to {self.file_path}")
            
        except Exception as e:
            logger.error(f"Failed to save memory data: {e}")
    
    async def store(self, key: str, value: Any, ttl: Optional[float] = None) -> bool:
        """Store a value in file."""
        async with self._lock:
            await self._load_data()
            
            try:
                # Store with timestamp for TTL support
                import time
                item_data = {
                    "value": value,
                    "timestamp": time.time(),
                    "ttl": ttl
                }
                
                self._data[key] = item_data
                await self._save_data()
                
                logger.debug(f"Stored in file: {key}")
                return True
                
            except Exception as e:
                logger.error(f"Failed to store in file {key}: {e}")
                return False
    
    async def retrieve(self, key: str) -> Optional[Any]:
        """Retrieve a value from file."""
        async with self._lock:
            await self._load_data()
            
            try:
                item_data = self._data.get(key)
                if item_data is None:
                    return None
                
                # Check TTL
                if item_data.get("ttl") is not None:
                    import time
                    elapsed = time.time() - item_data["timestamp"]
                    if elapsed > item_data["ttl"]:
                        # Expired, remove and return None
                        del self._data[key]
                        await self._save_data()
                        return None
                
                logger.debug(f"Retrieved from file: {key}")
                return item_data["value"]
                
            except Exception as e:
                logger.error(f"Failed to retrieve from file {key}: {e}")
                return None
    
    async def delete(self, key: str) -> bool:
        """Delete a value from file."""
        async with self._lock:
            await self._load_data()
            
            try:
                if key in self._data:
                    del self._data[key]
                    await self._save_data()
                    logger.debug(f"Deleted from file: {key}")
                    return True
                return False
                
            except Exception as e:
                logger.error(f"Failed to delete from file {key}: {e}")
                return False
    
    async def exists(self, key: str) -> bool:
        """Check if a key exists in file."""
        async with self._lock:
            await self._load_data()
            
            try:
                if key not in self._data:
                    return False
                
                # Check TTL
                item_data = self._data[key]
                if item_data.get("ttl") is not None:
                    import time
                    elapsed = time.time() - item_data["timestamp"]
                    if elapsed > item_data["ttl"]:
                        # Expired, remove
                        del self._data[key]
                        await self._save_data()
                        return False
                
                return True
                
            except Exception as e:
                logger.error(f"Failed to check existence in file {key}: {e}")
                return False
    
    async def clear(self) -> bool:
        """Clear all data in file."""
        async with self._lock:
            try:
                self._data = {}
                await self._save_data()
                logger.info("Cleared file memory")
                return True
                
            except Exception as e:
                logger.error(f"Failed to clear file memory: {e}")
                return False
    
    async def keys(self, pattern: str = "*") -> List[str]:
        """Get all keys matching a pattern in file."""
        async with self._lock:
            await self._load_data()
            
            try:
                import fnmatch
                import time
                
                # Filter out expired keys and match pattern
                valid_keys = []
                expired_keys = []
                
                for key, item_data in self._data.items():
                    # Check TTL
                    if item_data.get("ttl") is not None:
                        elapsed = time.time() - item_data["timestamp"]
                        if elapsed > item_data["ttl"]:
                            expired_keys.append(key)
                            continue
                    
                    # Check pattern
                    if pattern == "*" or fnmatch.fnmatch(key, pattern):
                        valid_keys.append(key)
                
                # Remove expired keys
                for key in expired_keys:
                    del self._data[key]
                
                if expired_keys:
                    await self._save_data()
                
                return valid_keys
                
            except Exception as e:
                logger.error(f"Failed to get keys from file with pattern {pattern}: {e}")
                return []