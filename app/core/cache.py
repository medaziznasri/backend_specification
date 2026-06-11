import time
import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

class SimpleCache:

    
    def __init__(self, default_ttl: int = 300):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self.default_ttl = default_ttl

    def get(self, key: str) -> Optional[Any]:
        if key not in self._cache:
            return None
        
        item = self._cache[key]
        if time.time() > item["expires_at"]:
            logger.debug(f"Cache miss (expired): {key}")
            del self._cache[key]
            return None
        
        logger.debug(f"Cache hit: {key}")
        return item["value"]

    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        ttl = ttl if ttl is not None else self.default_ttl
        self._cache[key] = {
            "value": value,
            "expires_at": time.time() + ttl
        }
        logger.debug(f"Cache set: {key} (ttl={ttl}s)")

    def clear(self):
        self._cache.clear()

cache = SimpleCache(default_ttl=600)
