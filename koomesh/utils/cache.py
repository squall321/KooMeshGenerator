"""
Caching System for KooMeshGenerator
====================================

This module provides caching mechanisms to improve performance:
- File-based cache for geometry analysis
- Memory cache for frequently accessed data
- Configuration cache
- Automatic cache invalidation

Usage:
    >>> from koomesh.utils.cache import GeometryCache
    >>> cache = GeometryCache()
    >>> info = cache.get_or_compute(step_file, analyzer.analyze)
"""

import hashlib
import json
import pickle
from pathlib import Path
from typing import Any, Callable, Optional, Dict
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """
    Cache entry metadata

    Attributes:
        key: Cache key
        created: Creation timestamp
        accessed: Last access timestamp
        access_count: Number of accesses
        size_bytes: Size in bytes
    """
    key: str
    created: datetime
    accessed: datetime
    access_count: int = 0
    size_bytes: int = 0

    def is_expired(self, ttl_seconds: int) -> bool:
        """Check if entry is expired"""
        age = (datetime.now() - self.created).total_seconds()
        return age > ttl_seconds

    def update_access(self):
        """Update access metadata"""
        self.accessed = datetime.now()
        self.access_count += 1


class CacheManager:
    """
    Base cache manager with file-based storage

    Features:
    - File-based persistent cache
    - TTL (time-to-live) support
    - Automatic cleanup
    - Cache statistics
    """

    def __init__(
        self,
        cache_dir: Path,
        ttl_seconds: int = 86400,  # 24 hours
        max_size_mb: int = 1000,  # 1 GB
    ):
        """
        Initialize cache manager

        Args:
            cache_dir: Directory for cache files
            ttl_seconds: Time-to-live for cache entries
            max_size_mb: Maximum cache size in MB
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self.ttl_seconds = ttl_seconds
        self.max_size_bytes = max_size_mb * 1024 * 1024

        self.metadata_file = self.cache_dir / 'metadata.json'
        self.entries: Dict[str, CacheEntry] = {}

        self._load_metadata()

    def _load_metadata(self):
        """Load cache metadata"""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r') as f:
                    data = json.load(f)

                for key, entry_data in data.items():
                    entry_data['created'] = datetime.fromisoformat(entry_data['created'])
                    entry_data['accessed'] = datetime.fromisoformat(entry_data['accessed'])
                    self.entries[key] = CacheEntry(**entry_data)

            except Exception as e:
                logger.warning(f"Failed to load cache metadata: {e}")
                self.entries = {}

    def _save_metadata(self):
        """Save cache metadata"""
        try:
            data = {}
            for key, entry in self.entries.items():
                entry_dict = asdict(entry)
                entry_dict['created'] = entry.created.isoformat()
                entry_dict['accessed'] = entry.accessed.isoformat()
                data[key] = entry_dict

            with open(self.metadata_file, 'w') as f:
                json.dump(data, f, indent=2)

        except Exception as e:
            logger.error(f"Failed to save cache metadata: {e}")

    def _get_cache_path(self, key: str) -> Path:
        """Get cache file path for key"""
        return self.cache_dir / f"{key}.cache"

    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found/expired
        """
        if key not in self.entries:
            return None

        entry = self.entries[key]

        # Check if expired
        if entry.is_expired(self.ttl_seconds):
            self.delete(key)
            return None

        # Load cached value
        cache_path = self._get_cache_path(key)
        if not cache_path.exists():
            del self.entries[key]
            return None

        try:
            with open(cache_path, 'rb') as f:
                value = pickle.load(f)

            # Update access metadata
            entry.update_access()
            self._save_metadata()

            logger.debug(f"Cache hit: {key}")
            return value

        except Exception as e:
            logger.warning(f"Failed to load cache entry {key}: {e}")
            self.delete(key)
            return None

    def set(self, key: str, value: Any) -> bool:
        """
        Set value in cache

        Args:
            key: Cache key
            value: Value to cache

        Returns:
            True if successful
        """
        try:
            # Serialize value
            cache_path = self._get_cache_path(key)
            with open(cache_path, 'wb') as f:
                pickle.dump(value, f)

            # Update metadata
            size_bytes = cache_path.stat().st_size
            now = datetime.now()

            self.entries[key] = CacheEntry(
                key=key,
                created=now,
                accessed=now,
                size_bytes=size_bytes
            )

            self._save_metadata()

            # Check cache size and cleanup if needed
            self._cleanup_if_needed()

            logger.debug(f"Cache set: {key} ({size_bytes} bytes)")
            return True

        except Exception as e:
            logger.error(f"Failed to set cache entry {key}: {e}")
            return False

    def delete(self, key: str):
        """Delete cache entry"""
        cache_path = self._get_cache_path(key)
        if cache_path.exists():
            cache_path.unlink()

        if key in self.entries:
            del self.entries[key]

        self._save_metadata()

    def clear(self):
        """Clear all cache entries"""
        for cache_file in self.cache_dir.glob('*.cache'):
            cache_file.unlink()

        self.entries.clear()
        self._save_metadata()

    def _cleanup_if_needed(self):
        """Cleanup old entries if cache size exceeds limit"""
        total_size = sum(e.size_bytes for e in self.entries.values())

        if total_size > self.max_size_bytes:
            logger.info(f"Cache size ({total_size / 1024 / 1024:.2f}MB) exceeds limit, cleaning up...")

            # Sort by last access time (oldest first)
            sorted_entries = sorted(
                self.entries.items(),
                key=lambda x: x[1].accessed
            )

            # Remove old entries until under limit
            for key, entry in sorted_entries:
                if total_size <= self.max_size_bytes * 0.8:  # Remove until 80% of limit
                    break

                self.delete(key)
                total_size -= entry.size_bytes

    def cleanup_expired(self):
        """Remove expired entries"""
        expired_keys = [
            key for key, entry in self.entries.items()
            if entry.is_expired(self.ttl_seconds)
        ]

        for key in expired_keys:
            self.delete(key)

        if expired_keys:
            logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_size = sum(e.size_bytes for e in self.entries.values())
        total_accesses = sum(e.access_count for e in self.entries.values())

        return {
            'total_entries': len(self.entries),
            'total_size_mb': total_size / 1024 / 1024,
            'total_accesses': total_accesses,
            'avg_entry_size_kb': (total_size / len(self.entries) / 1024) if self.entries else 0,
            'cache_dir': str(self.cache_dir),
            'ttl_seconds': self.ttl_seconds,
            'max_size_mb': self.max_size_bytes / 1024 / 1024,
        }

    def print_stats(self):
        """Print cache statistics"""
        stats = self.get_stats()
        print(f"\n{'='*60}")
        print(f"Cache Statistics")
        print(f"{'='*60}")
        print(f"Total Entries:     {stats['total_entries']}")
        print(f"Total Size:        {stats['total_size_mb']:.2f} MB")
        print(f"Total Accesses:    {stats['total_accesses']}")
        print(f"Avg Entry Size:    {stats['avg_entry_size_kb']:.2f} KB")
        print(f"Cache Directory:   {stats['cache_dir']}")
        print(f"TTL:               {stats['ttl_seconds']} seconds")
        print(f"Max Size:          {stats['max_size_mb']:.0f} MB")
        print(f"{'='*60}\n")


class GeometryCache(CacheManager):
    """
    Cache for geometry analysis results

    Automatically caches geometry information based on file hash.
    """

    def __init__(self, cache_dir: Optional[Path] = None):
        """Initialize geometry cache"""
        if cache_dir is None:
            cache_dir = Path.home() / '.koomesh' / 'cache' / 'geometry'

        super().__init__(
            cache_dir=cache_dir,
            ttl_seconds=7 * 86400,  # 7 days
            max_size_mb=500  # 500 MB
        )

    def get_file_hash(self, filepath: Path) -> str:
        """
        Get hash of file for cache key

        Args:
            filepath: Path to file

        Returns:
            SHA256 hash of file
        """
        sha256 = hashlib.sha256()

        with open(filepath, 'rb') as f:
            # Read file in chunks to handle large files
            for chunk in iter(lambda: f.read(8192), b''):
                sha256.update(chunk)

        return sha256.hexdigest()

    def get_or_compute(
        self,
        filepath: Path,
        compute_func: Callable,
        force_recompute: bool = False
    ) -> Any:
        """
        Get cached result or compute and cache

        Args:
            filepath: Path to geometry file
            compute_func: Function to compute result
            force_recompute: Force recomputation even if cached

        Returns:
            Computation result

        Example:
            >>> cache = GeometryCache()
            >>> info = cache.get_or_compute(
            ...     "part.step",
            ...     lambda f: analyzer.analyze(f)
            ... )
        """
        # Generate cache key from file hash
        key = self.get_file_hash(filepath)

        # Check cache
        if not force_recompute:
            cached_value = self.get(key)
            if cached_value is not None:
                logger.info(f"Using cached geometry analysis for {filepath.name}")
                return cached_value

        # Compute result
        logger.info(f"Computing geometry analysis for {filepath.name}")
        result = compute_func(filepath)

        # Cache result
        self.set(key, result)

        return result


class ConfigCache(CacheManager):
    """Cache for configuration validation results"""

    def __init__(self, cache_dir: Optional[Path] = None):
        """Initialize config cache"""
        if cache_dir is None:
            cache_dir = Path.home() / '.koomesh' / 'cache' / 'config'

        super().__init__(
            cache_dir=cache_dir,
            ttl_seconds=86400,  # 1 day
            max_size_mb=50  # 50 MB
        )

    def get_config_hash(self, config_dict: Dict) -> str:
        """Get hash of configuration"""
        config_str = json.dumps(config_dict, sort_keys=True)
        return hashlib.sha256(config_str.encode()).hexdigest()


class MemoryCache:
    """
    Simple in-memory cache with LRU eviction

    For frequently accessed small data that doesn't need persistence.
    """

    def __init__(self, max_entries: int = 100):
        """
        Initialize memory cache

        Args:
            max_entries: Maximum number of entries
        """
        self.max_entries = max_entries
        self.cache: Dict[str, Any] = {}
        self.access_order: list = []

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if key in self.cache:
            # Update LRU order
            self.access_order.remove(key)
            self.access_order.append(key)
            return self.cache[key]
        return None

    def set(self, key: str, value: Any):
        """Set value in cache"""
        # Remove if already exists
        if key in self.cache:
            self.access_order.remove(key)

        # Add new entry
        self.cache[key] = value
        self.access_order.append(key)

        # Evict oldest if needed
        if len(self.cache) > self.max_entries:
            oldest_key = self.access_order.pop(0)
            del self.cache[oldest_key]

    def clear(self):
        """Clear cache"""
        self.cache.clear()
        self.access_order.clear()

    def __len__(self):
        return len(self.cache)


# Global cache instances
_geometry_cache: Optional[GeometryCache] = None
_config_cache: Optional[ConfigCache] = None


def get_geometry_cache() -> GeometryCache:
    """Get global geometry cache instance"""
    global _geometry_cache
    if _geometry_cache is None:
        _geometry_cache = GeometryCache()
    return _geometry_cache


def get_config_cache() -> ConfigCache:
    """Get global config cache instance"""
    global _config_cache
    if _config_cache is None:
        _config_cache = ConfigCache()
    return _config_cache


def clear_all_caches():
    """Clear all global caches"""
    if _geometry_cache:
        _geometry_cache.clear()
    if _config_cache:
        _config_cache.clear()
