#!/usr/bin/env python3
"""
Compilation Database Cache Module

Provides caching layer for parsed compilation database results to achieve
<30ms per-file parsing speed (vs 1-3s cold parse with clang).

Requirements:
- REQ-F-39: Cache parsed compilation database results to achieve <30ms per-file parsing speed
- REQ-F-41: Validate compilation database freshness (detect source file changes requiring regeneration)

Cache Design:
- Storage: JSON files at .claude/cache/llt-compdb/
- Cache key: SHA256(file path) + last modified timestamp
- Freshness: Compare source file mtime with cached mtime
- Auto-invalidation: Return None if source file modified since cache entry
"""

import hashlib
import json
import logging
import os
import time
from pathlib import Path
from typing import Dict, List, Optional

# Configure logging
logger = logging.getLogger(__name__)

# Cache directory location
CACHE_DIR = Path.home() / ".claude" / "cache" / "llt-compdb"


def get_cached_methods(file_path: Path) -> Optional[List[Dict]]:
    """
    Retrieve cached method results if fresh.

    Performance target: <30ms (JSON read + validation)

    Args:
        file_path: Path to source file to check cache for

    Returns:
        List of method metadata dicts if cache hit and fresh, None otherwise.

    Example:
        >>> methods = get_cached_methods(Path("MyClass.h"))
        >>> if methods is None:
        ...     # Cache miss - parse with clang
        ...     methods = extract_methods_with_clang(...)
        ...     cache_methods(Path("MyClass.h"), methods)
    """
    start_time = time.perf_counter()

    file_path = Path(file_path).resolve()

    if not file_path.exists():
        logger.debug(f"Source file not found: {file_path}")
        return None

    # Get cache file path
    cache_file = _get_cache_file_path(file_path)

    if not cache_file.exists():
        logger.debug(f"Cache miss: {file_path.name} (no cache entry)")
        return None

    try:
        # Read cache entry (fast JSON read)
        with open(cache_file, 'r', encoding='utf-8') as f:
            cache_entry = json.load(f)

        # Validate cache structure
        if not _validate_cache_entry(cache_entry):
            logger.warning(f"Invalid cache entry for {file_path.name}, invalidating")
            invalidate_cache(file_path)
            return None

        # Check freshness: compare source file mtime with cached mtime
        current_mtime = file_path.stat().st_mtime
        cached_mtime = cache_entry['metadata']['mtime']

        if current_mtime != cached_mtime:
            logger.debug(
                f"Cache stale: {file_path.name} "
                f"(mtime changed: {cached_mtime} -> {current_mtime})"
            )
            invalidate_cache(file_path)
            return None

        # Cache hit - return methods
        elapsed_ms = (time.perf_counter() - start_time) * 1000
        logger.info(
            f"Cache hit: {file_path.name} ({len(cache_entry['methods'])} methods, "
            f"{elapsed_ms:.1f}ms)"
        )

        # Verify performance requirement
        if elapsed_ms > 30:
            logger.warning(
                f"Cache hit exceeded 30ms target: {elapsed_ms:.1f}ms for {file_path.name}"
            )

        return cache_entry['methods']

    except Exception as e:
        logger.warning(f"Error reading cache for {file_path.name}: {e}")
        return None


def cache_methods(file_path: Path, methods: List[Dict]) -> bool:
    """
    Store parsed method results in cache.

    Cache entry structure:
    {
        "metadata": {
            "file_path": "/absolute/path/to/file.h",
            "mtime": 1234567890.123,
            "cached_at": 1234567890.456,
            "method_count": 5
        },
        "methods": [
            {
                "name": "GetValue",
                "return_type": "int",
                "params": [...],
                "is_const": true,
                "mangled_name": "_ZN7MyClass8GetValueEv",
                ...
            }
        ]
    }

    Args:
        file_path: Path to source file
        methods: List of method metadata dicts from clang or regex parser

    Returns:
        True if caching succeeded, False otherwise.

    Example:
        >>> methods = extract_methods_with_clang(header_path, compdb_path)
        >>> cache_methods(header_path, methods)
        True
    """
    file_path = Path(file_path).resolve()

    if not file_path.exists():
        logger.error(f"Cannot cache non-existent file: {file_path}")
        return False

    # Ensure cache directory exists
    _ensure_cache_dir()

    # Get cache file path
    cache_file = _get_cache_file_path(file_path)

    try:
        # Get file metadata
        file_stat = file_path.stat()
        current_mtime = file_stat.st_mtime

        # Build cache entry
        cache_entry = {
            'metadata': {
                'file_path': str(file_path),
                'mtime': current_mtime,
                'cached_at': time.time(),
                'method_count': len(methods)
            },
            'methods': methods
        }

        # Write cache file (efficient JSON without pretty-printing)
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(cache_entry, f, separators=(',', ':'))

        logger.debug(
            f"Cached {len(methods)} methods for {file_path.name} "
            f"at {cache_file}"
        )

        return True

    except Exception as e:
        logger.error(f"Error caching methods for {file_path.name}: {e}")
        return False


def invalidate_cache(file_path: Path) -> bool:
    """
    Remove stale cache entry for a file.

    Args:
        file_path: Path to source file

    Returns:
        True if cache entry removed, False if no cache entry existed.

    Example:
        >>> invalidate_cache(Path("MyClass.h"))
        True
    """
    file_path = Path(file_path).resolve()
    cache_file = _get_cache_file_path(file_path)

    if not cache_file.exists():
        return False

    try:
        cache_file.unlink()
        logger.debug(f"Invalidated cache for {file_path.name}")
        return True
    except Exception as e:
        logger.warning(f"Error invalidating cache for {file_path.name}: {e}")
        return False


def clear_all_cache() -> int:
    """
    Wipe entire cache directory.

    Returns:
        Number of cache entries removed.

    Example:
        >>> count = clear_all_cache()
        >>> print(f"Cleared {count} cache entries")
    """
    if not CACHE_DIR.exists():
        return 0

    count = 0
    try:
        for cache_file in CACHE_DIR.glob("*.json"):
            try:
                cache_file.unlink()
                count += 1
            except Exception as e:
                logger.warning(f"Error removing cache file {cache_file}: {e}")

        logger.info(f"Cleared {count} cache entries from {CACHE_DIR}")
        return count

    except Exception as e:
        logger.error(f"Error clearing cache directory: {e}")
        return count


def get_cache_stats() -> Dict:
    """
    Get cache statistics for monitoring.

    Returns:
        Dict with cache statistics including total entries, total size, oldest/newest entry.

    Example:
        >>> stats = get_cache_stats()
        >>> print(f"Cache has {stats['entry_count']} entries, {stats['total_size_mb']:.2f}MB")
    """
    if not CACHE_DIR.exists():
        return {
            'entry_count': 0,
            'total_size_bytes': 0,
            'total_size_mb': 0.0,
            'oldest_entry': None,
            'newest_entry': None
        }

    cache_files = list(CACHE_DIR.glob("*.json"))

    if not cache_files:
        return {
            'entry_count': 0,
            'total_size_bytes': 0,
            'total_size_mb': 0.0,
            'oldest_entry': None,
            'newest_entry': None
        }

    total_size = sum(f.stat().st_size for f in cache_files)

    # Find oldest and newest entries
    oldest = min(cache_files, key=lambda f: f.stat().st_mtime)
    newest = max(cache_files, key=lambda f: f.stat().st_mtime)

    return {
        'entry_count': len(cache_files),
        'total_size_bytes': total_size,
        'total_size_mb': total_size / (1024 * 1024),
        'oldest_entry': {
            'path': str(oldest),
            'mtime': oldest.stat().st_mtime
        },
        'newest_entry': {
            'path': str(newest),
            'mtime': newest.stat().st_mtime
        }
    }


# Private helper functions

def _get_cache_file_path(file_path: Path) -> Path:
    """
    Get cache file path for a source file.

    Uses SHA256 hash of absolute file path to avoid issues with path separators.

    Args:
        file_path: Absolute path to source file

    Returns:
        Path to cache JSON file.
    """
    file_path = Path(file_path).resolve()

    # Hash the file path to create a safe filename
    path_hash = hashlib.sha256(str(file_path).encode('utf-8')).hexdigest()[:16]

    # Include original filename stem for debugging
    filename_stem = file_path.stem[:32]  # Limit to 32 chars

    cache_filename = f"{filename_stem}_{path_hash}.json"
    return CACHE_DIR / cache_filename


def _ensure_cache_dir() -> None:
    """
    Ensure cache directory exists (lazy creation).

    Creates directory with proper permissions if it doesn't exist.
    """
    if not CACHE_DIR.exists():
        try:
            CACHE_DIR.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Created cache directory at {CACHE_DIR}")
        except Exception as e:
            logger.error(f"Failed to create cache directory {CACHE_DIR}: {e}")
            raise


def _validate_cache_entry(cache_entry: Dict) -> bool:
    """
    Validate cache entry structure.

    Args:
        cache_entry: Parsed JSON cache entry

    Returns:
        True if valid, False otherwise.
    """
    try:
        # Check required top-level keys
        if 'metadata' not in cache_entry or 'methods' not in cache_entry:
            return False

        metadata = cache_entry['metadata']

        # Check required metadata fields
        required_fields = ['file_path', 'mtime', 'cached_at', 'method_count']
        if not all(field in metadata for field in required_fields):
            return False

        # Check methods is a list
        if not isinstance(cache_entry['methods'], list):
            return False

        # Verify method count matches
        if len(cache_entry['methods']) != metadata['method_count']:
            return False

        return True

    except Exception:
        return False


if __name__ == "__main__":
    # Configure logging for standalone execution
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Example usage
    import sys

    if len(sys.argv) < 2:
        print("Usage: compilation_db_cache.py <command> [args]")
        print("Commands:")
        print("  check <file_path>     - Check if file has cached results")
        print("  stats                 - Show cache statistics")
        print("  clear                 - Clear all cache entries")
        print("  invalidate <file_path> - Invalidate cache for specific file")
        sys.exit(1)

    command = sys.argv[1]

    if command == "check":
        if len(sys.argv) < 3:
            print("Error: file_path required")
            sys.exit(1)

        file_path = Path(sys.argv[2])
        methods = get_cached_methods(file_path)

        if methods:
            print(f"Cache HIT: {len(methods)} methods cached for {file_path.name}")
            for method in methods:
                print(f"  - {method['class_name']}::{method['name']}")
        else:
            print(f"Cache MISS: No cached results for {file_path.name}")

    elif command == "stats":
        stats = get_cache_stats()
        print(f"Cache Statistics:")
        print(f"  Entries: {stats['entry_count']}")
        print(f"  Total Size: {stats['total_size_mb']:.2f} MB")
        if stats['oldest_entry']:
            print(f"  Oldest: {stats['oldest_entry']['path']}")
        if stats['newest_entry']:
            print(f"  Newest: {stats['newest_entry']['path']}")

    elif command == "clear":
        count = clear_all_cache()
        print(f"Cleared {count} cache entries")

    elif command == "invalidate":
        if len(sys.argv) < 3:
            print("Error: file_path required")
            sys.exit(1)

        file_path = Path(sys.argv[2])
        if invalidate_cache(file_path):
            print(f"Invalidated cache for {file_path.name}")
        else:
            print(f"No cache entry for {file_path.name}")

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
