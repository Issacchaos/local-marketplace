#!/usr/bin/env python3
"""
Unit tests for compilation_db_cache.py

Tests cache hit/miss scenarios, freshness validation, performance benchmarks,
and auto-invalidation on file modification.
"""

import json
import sys
import tempfile
import time
import unittest
from pathlib import Path

# Add scripts directory to path for direct imports
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import compilation_db_cache


class TestCacheBasics(unittest.TestCase):
    """Test basic cache operations."""

    def setUp(self):
        """Set up test fixtures."""
        # Use a temporary cache directory for tests
        self.original_cache_dir = compilation_db_cache.CACHE_DIR
        self.test_cache_dir = Path(tempfile.mkdtemp()) / "test_cache"
        compilation_db_cache.CACHE_DIR = self.test_cache_dir

    def tearDown(self):
        """Clean up test fixtures."""
        # Restore original cache directory
        compilation_db_cache.CACHE_DIR = self.original_cache_dir

        # Clean up test cache
        if self.test_cache_dir.exists():
            for f in self.test_cache_dir.glob("*"):
                f.unlink()
            self.test_cache_dir.rmdir()

    def test_cache_miss_no_entry(self):
        """Test cache miss when no cache entry exists."""
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.h', delete=False, encoding='utf-8'
        ) as f:
            f.write("class MyClass { public: int GetValue(); };")
            header_path = Path(f.name)

        try:
            methods = compilation_db_cache.get_cached_methods(header_path)
            self.assertIsNone(methods)
        finally:
            header_path.unlink()

    def test_cache_hit(self):
        """Test cache hit returns cached methods."""
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.h', delete=False, encoding='utf-8'
        ) as f:
            f.write("class MyClass { public: int GetValue(); };")
            header_path = Path(f.name)

        try:
            # Create test methods
            test_methods = [
                {
                    'name': 'GetValue',
                    'return_type': 'int',
                    'params': [],
                    'is_const': False,
                    'class_name': 'MyClass'
                }
            ]

            # Cache the methods
            success = compilation_db_cache.cache_methods(header_path, test_methods)
            self.assertTrue(success)

            # Retrieve from cache
            cached_methods = compilation_db_cache.get_cached_methods(header_path)
            self.assertIsNotNone(cached_methods)
            self.assertEqual(len(cached_methods), 1)
            self.assertEqual(cached_methods[0]['name'], 'GetValue')
            self.assertEqual(cached_methods[0]['return_type'], 'int')
        finally:
            header_path.unlink()

    def test_cache_invalidation_on_file_modification(self):
        """Test cache auto-invalidation when source file modified."""
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.h', delete=False, encoding='utf-8'
        ) as f:
            f.write("class MyClass { public: int GetValue(); };")
            header_path = Path(f.name)

        try:
            # Cache initial methods
            test_methods = [{'name': 'GetValue', 'return_type': 'int', 'params': []}]
            compilation_db_cache.cache_methods(header_path, test_methods)

            # Verify cache hit
            cached = compilation_db_cache.get_cached_methods(header_path)
            self.assertIsNotNone(cached)

            # Modify file (change mtime)
            time.sleep(0.1)  # Ensure mtime changes
            with open(header_path, 'a', encoding='utf-8') as f:
                f.write("\n// Modified")

            # Cache should be stale
            cached_after_modification = compilation_db_cache.get_cached_methods(header_path)
            self.assertIsNone(cached_after_modification)
        finally:
            header_path.unlink()

    def test_manual_invalidation(self):
        """Test manual cache invalidation."""
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.h', delete=False, encoding='utf-8'
        ) as f:
            f.write("class MyClass {};")
            header_path = Path(f.name)

        try:
            # Cache methods
            test_methods = [{'name': 'Test', 'return_type': 'void', 'params': []}]
            compilation_db_cache.cache_methods(header_path, test_methods)

            # Verify cache exists
            self.assertIsNotNone(compilation_db_cache.get_cached_methods(header_path))

            # Invalidate cache
            result = compilation_db_cache.invalidate_cache(header_path)
            self.assertTrue(result)

            # Verify cache removed
            self.assertIsNone(compilation_db_cache.get_cached_methods(header_path))
        finally:
            header_path.unlink()

    def test_clear_all_cache(self):
        """Test clearing all cache entries."""
        # Create multiple cache entries
        files = []
        try:
            for i in range(3):
                with tempfile.NamedTemporaryFile(
                    mode='w', suffix='.h', delete=False, encoding='utf-8'
                ) as f:
                    f.write(f"class MyClass{i} {{}};")
                    header_path = Path(f.name)
                    files.append(header_path)

            # Cache all files
            for i, header_path in enumerate(files):
                test_methods = [{'name': f'Method{i}', 'return_type': 'void', 'params': []}]
                compilation_db_cache.cache_methods(header_path, test_methods)

            # Verify all cached
            for header_path in files:
                self.assertIsNotNone(compilation_db_cache.get_cached_methods(header_path))

            # Clear all cache
            count = compilation_db_cache.clear_all_cache()
            self.assertEqual(count, 3)

            # Verify all removed
            for header_path in files:
                self.assertIsNone(compilation_db_cache.get_cached_methods(header_path))
        finally:
            for header_path in files:
                if header_path.exists():
                    header_path.unlink()


class TestCachePerformance(unittest.TestCase):
    """Test cache performance requirements."""

    def setUp(self):
        """Set up test fixtures."""
        self.original_cache_dir = compilation_db_cache.CACHE_DIR
        self.test_cache_dir = Path(tempfile.mkdtemp()) / "test_cache"
        compilation_db_cache.CACHE_DIR = self.test_cache_dir

    def tearDown(self):
        """Clean up test fixtures."""
        compilation_db_cache.CACHE_DIR = self.original_cache_dir
        if self.test_cache_dir.exists():
            for f in self.test_cache_dir.glob("*"):
                f.unlink()
            self.test_cache_dir.rmdir()

    def test_cache_hit_performance_under_30ms(self):
        """Test cache hit meets <30ms performance target (REQ-F-39)."""
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.h', delete=False, encoding='utf-8'
        ) as f:
            f.write("class MyClass { public: int GetValue(); };")
            header_path = Path(f.name)

        try:
            # Create and cache methods
            test_methods = [
                {'name': f'Method{i}', 'return_type': 'int', 'params': []}
                for i in range(10)
            ]
            compilation_db_cache.cache_methods(header_path, test_methods)

            # Measure cache hit performance (warm up)
            compilation_db_cache.get_cached_methods(header_path)

            # Measure performance multiple times for accuracy
            times = []
            for _ in range(10):
                start = time.perf_counter()
                cached = compilation_db_cache.get_cached_methods(header_path)
                elapsed_ms = (time.perf_counter() - start) * 1000
                times.append(elapsed_ms)

                self.assertIsNotNone(cached)
                self.assertEqual(len(cached), 10)

            # Check average time
            avg_time = sum(times) / len(times)
            max_time = max(times)

            # REQ-F-39: Cache hit should be <30ms
            self.assertLess(
                avg_time, 30.0,
                f"Average cache hit time {avg_time:.1f}ms exceeds 30ms target"
            )
            self.assertLess(
                max_time, 50.0,
                f"Max cache hit time {max_time:.1f}ms significantly exceeds target"
            )

            print(
                f"\nCache hit performance: avg={avg_time:.1f}ms, max={max_time:.1f}ms "
                f"(target: <30ms) ✓"
            )
        finally:
            header_path.unlink()

    def test_cache_with_large_method_list(self):
        """Test cache performance with large method lists."""
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.h', delete=False, encoding='utf-8'
        ) as f:
            f.write("class LargeClass {};")
            header_path = Path(f.name)

        try:
            # Create a large list of methods (100 methods)
            test_methods = [
                {
                    'name': f'Method{i}',
                    'return_type': 'int',
                    'params': [
                        {'type': 'int', 'name': f'param{j}'}
                        for j in range(3)
                    ],
                    'is_const': i % 2 == 0,
                    'is_virtual': i % 3 == 0,
                    'class_name': 'LargeClass',
                    'line': i + 10,
                    'mangled_name': f'_ZN10LargeClass7Method{i}Eiii'
                }
                for i in range(100)
            ]

            # Cache the large method list
            success = compilation_db_cache.cache_methods(header_path, test_methods)
            self.assertTrue(success)

            # Measure cache hit performance
            start = time.perf_counter()
            cached = compilation_db_cache.get_cached_methods(header_path)
            elapsed_ms = (time.perf_counter() - start) * 1000

            self.assertIsNotNone(cached)
            self.assertEqual(len(cached), 100)

            # Should still be under 30ms even with 100 methods
            self.assertLess(
                elapsed_ms, 30.0,
                f"Cache hit time {elapsed_ms:.1f}ms exceeds 30ms target with 100 methods"
            )

            print(
                f"\nLarge method list (100 methods) cache hit: {elapsed_ms:.1f}ms "
                f"(target: <30ms) ✓"
            )
        finally:
            header_path.unlink()


class TestCacheValidation(unittest.TestCase):
    """Test cache entry validation."""

    def setUp(self):
        """Set up test fixtures."""
        self.original_cache_dir = compilation_db_cache.CACHE_DIR
        self.test_cache_dir = Path(tempfile.mkdtemp()) / "test_cache"
        compilation_db_cache.CACHE_DIR = self.test_cache_dir

    def tearDown(self):
        """Clean up test fixtures."""
        compilation_db_cache.CACHE_DIR = self.original_cache_dir
        if self.test_cache_dir.exists():
            for f in self.test_cache_dir.glob("*"):
                f.unlink()
            self.test_cache_dir.rmdir()

    def test_invalid_cache_entry_structure(self):
        """Test handling of invalid cache entry structure."""
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.h', delete=False, encoding='utf-8'
        ) as f:
            f.write("class MyClass {};")
            header_path = Path(f.name)

        try:
            # Create an invalid cache entry
            cache_file = compilation_db_cache._get_cache_file_path(header_path)
            compilation_db_cache._ensure_cache_dir()

            invalid_entry = {
                'invalid': 'structure'
                # Missing metadata and methods
            }

            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(invalid_entry, f)

            # Should return None and invalidate
            cached = compilation_db_cache.get_cached_methods(header_path)
            self.assertIsNone(cached)

            # Cache file should be removed
            self.assertFalse(cache_file.exists())
        finally:
            header_path.unlink()

    def test_corrupted_cache_file(self):
        """Test handling of corrupted JSON cache file."""
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.h', delete=False, encoding='utf-8'
        ) as f:
            f.write("class MyClass {};")
            header_path = Path(f.name)

        try:
            # Create a corrupted cache file
            cache_file = compilation_db_cache._get_cache_file_path(header_path)
            compilation_db_cache._ensure_cache_dir()

            with open(cache_file, 'w', encoding='utf-8') as f:
                f.write("{ invalid json {")

            # Should return None gracefully
            cached = compilation_db_cache.get_cached_methods(header_path)
            self.assertIsNone(cached)
        finally:
            header_path.unlink()

    def test_method_count_mismatch(self):
        """Test detection of method count mismatch in cache entry."""
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.h', delete=False, encoding='utf-8'
        ) as f:
            f.write("class MyClass {};")
            header_path = Path(f.name)

        try:
            # Create cache entry with mismatched method count
            cache_file = compilation_db_cache._get_cache_file_path(header_path)
            compilation_db_cache._ensure_cache_dir()

            invalid_entry = {
                'metadata': {
                    'file_path': str(header_path),
                    'mtime': header_path.stat().st_mtime,
                    'cached_at': time.time(),
                    'method_count': 5  # Wrong count
                },
                'methods': [
                    {'name': 'Method1', 'return_type': 'int', 'params': []},
                    {'name': 'Method2', 'return_type': 'void', 'params': []}
                    # Only 2 methods, but metadata says 5
                ]
            }

            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(invalid_entry, f)

            # Should return None and invalidate
            cached = compilation_db_cache.get_cached_methods(header_path)
            self.assertIsNone(cached)
        finally:
            header_path.unlink()


class TestCacheStats(unittest.TestCase):
    """Test cache statistics functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.original_cache_dir = compilation_db_cache.CACHE_DIR
        self.test_cache_dir = Path(tempfile.mkdtemp()) / "test_cache"
        compilation_db_cache.CACHE_DIR = self.test_cache_dir

    def tearDown(self):
        """Clean up test fixtures."""
        compilation_db_cache.CACHE_DIR = self.original_cache_dir
        if self.test_cache_dir.exists():
            for f in self.test_cache_dir.glob("*"):
                f.unlink()
            self.test_cache_dir.rmdir()

    def test_cache_stats_empty(self):
        """Test cache stats with empty cache."""
        stats = compilation_db_cache.get_cache_stats()

        self.assertEqual(stats['entry_count'], 0)
        self.assertEqual(stats['total_size_bytes'], 0)
        self.assertIsNone(stats['oldest_entry'])
        self.assertIsNone(stats['newest_entry'])

    def test_cache_stats_with_entries(self):
        """Test cache stats with multiple entries."""
        files = []
        for i in range(3):
            with tempfile.NamedTemporaryFile(
                mode='w', suffix='.h', delete=False, encoding='utf-8'
            ) as f:
                f.write(f"class MyClass{i} {{}};")
                header_path = Path(f.name)
                files.append(header_path)

                test_methods = [{'name': f'Method{i}', 'return_type': 'void', 'params': []}]
                compilation_db_cache.cache_methods(header_path, test_methods)

            time.sleep(0.01)  # Ensure different mtimes

        try:
            stats = compilation_db_cache.get_cache_stats()

            self.assertEqual(stats['entry_count'], 3)
            self.assertGreater(stats['total_size_bytes'], 0)
            self.assertIsNotNone(stats['oldest_entry'])
            self.assertIsNotNone(stats['newest_entry'])
            self.assertLess(
                stats['oldest_entry']['mtime'],
                stats['newest_entry']['mtime']
            )

            print(
                f"\nCache stats: {stats['entry_count']} entries, "
                f"{stats['total_size_mb']:.3f} MB"
            )
        finally:
            for header_path in files:
                header_path.unlink()


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)
