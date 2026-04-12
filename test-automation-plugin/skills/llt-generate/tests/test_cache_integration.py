#!/usr/bin/env python3
"""
Integration tests for cache integration with source_parser.

Tests that the cache layer correctly integrates with clang and regex parsing,
and achieves the <30ms performance target.
"""

import sys
import tempfile
import time
import unittest
from pathlib import Path

# Add scripts directory to path for direct imports
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import compilation_db_cache
import source_parser


class TestCacheIntegration(unittest.TestCase):
    """Test cache integration with source parser."""

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

    def test_cache_integration_regex_mode(self):
        """Test cache integration with regex parsing (no compilation database)."""
        header_content = """
        class MyClass {
        public:
            int GetValue() const;
            void SetValue(int Value);
            virtual void Execute() = 0;
        };
        """

        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.h', delete=False, encoding='utf-8'
        ) as f:
            f.write(header_content)
            header_path = Path(f.name)

        try:
            # First parse - cold (regex mode, no cache)
            start = time.perf_counter()
            methods1 = source_parser.extract_method_signatures(header_path, use_cache=True)
            cold_time = (time.perf_counter() - start) * 1000

            self.assertEqual(len(methods1), 3)
            print(f"\nCold parse (regex): {cold_time:.1f}ms")

            # Note: Regex results are NOT cached (by design - already fast)
            # So second parse should also use regex
            start = time.perf_counter()
            methods2 = source_parser.extract_method_signatures(header_path, use_cache=True)
            second_time = (time.perf_counter() - start) * 1000

            self.assertEqual(len(methods2), 3)
            print(f"Second parse (regex): {second_time:.1f}ms")

            # Verify results are identical
            self.assertEqual(methods1[0]['name'], methods2[0]['name'])

        finally:
            header_path.unlink()

    def test_cache_integration_with_manual_caching(self):
        """Test manual cache integration."""
        header_content = """
        class MyClass {
        public:
            int GetValue() const;
            void SetValue(int Value);
        };
        """

        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.h', delete=False, encoding='utf-8'
        ) as f:
            f.write(header_content)
            header_path = Path(f.name)

        try:
            # Parse and manually cache
            methods = source_parser.extract_method_signatures(header_path, use_cache=False)
            self.assertEqual(len(methods), 2)

            # Manually cache the results
            compilation_db_cache.cache_methods(header_path, methods)

            # Now retrieve from cache
            start = time.perf_counter()
            cached_methods = source_parser.extract_method_signatures(header_path, use_cache=True)
            cache_time = (time.perf_counter() - start) * 1000

            self.assertEqual(len(cached_methods), 2)
            self.assertEqual(cached_methods[0]['name'], methods[0]['name'])

            # Should be <30ms
            self.assertLess(cache_time, 30.0)
            print(f"\nCache hit via source_parser: {cache_time:.1f}ms (target: <30ms) ✓")

        finally:
            header_path.unlink()

    def test_cache_disabled(self):
        """Test that cache can be disabled."""
        header_content = """
        class MyClass {
        public:
            int GetValue() const;
        };
        """

        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.h', delete=False, encoding='utf-8'
        ) as f:
            f.write(header_content)
            header_path = Path(f.name)

        try:
            # Manually create cache entry first
            test_methods = [
                {
                    'name': 'GetValue',
                    'return_type': 'int',
                    'params': [],
                    'is_const': True,
                    'class_name': 'MyClass'
                }
            ]
            compilation_db_cache.cache_methods(header_path, test_methods)

            # Verify cache entry exists
            cached = compilation_db_cache.get_cached_methods(header_path)
            self.assertIsNotNone(cached)

            # Parse with cache enabled (should use cache)
            start = time.perf_counter()
            methods1 = source_parser.extract_method_signatures(header_path, use_cache=True)
            cached_time = (time.perf_counter() - start) * 1000
            self.assertEqual(len(methods1), 1)
            print(f"\nWith cache enabled: {cached_time:.1f}ms")

            # Parse with cache disabled (should bypass cache)
            start = time.perf_counter()
            methods2 = source_parser.extract_method_signatures(header_path, use_cache=False)
            nocache_time = (time.perf_counter() - start) * 1000
            self.assertEqual(len(methods2), 1)
            print(f"With cache disabled: {nocache_time:.1f}ms")

            # Results should be identical
            self.assertEqual(methods1[0]['name'], methods2[0]['name'])

        finally:
            header_path.unlink()

    def test_cache_invalidation_on_modification(self):
        """Test that cache invalidates when source file modified."""
        header_content = """
        class MyClass {
        public:
            int GetValue() const;
        };
        """

        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.h', delete=False, encoding='utf-8'
        ) as f:
            f.write(header_content)
            header_path = Path(f.name)

        try:
            # Parse and manually cache
            methods1 = source_parser.extract_method_signatures(header_path, use_cache=False)
            self.assertEqual(len(methods1), 1)
            compilation_db_cache.cache_methods(header_path, methods1)

            # Verify cached
            cached = compilation_db_cache.get_cached_methods(header_path)
            self.assertIsNotNone(cached)

            # Modify file
            time.sleep(0.1)  # Ensure mtime changes
            with open(header_path, 'w', encoding='utf-8') as f:
                f.write("""
                class MyClass {
                public:
                    int GetValue() const;
                    void SetValue(int Value);  // New method
                };
                """)

            # Cache should be stale now
            cached_after_mod = compilation_db_cache.get_cached_methods(header_path)
            self.assertIsNone(cached_after_mod)

            # Parse again - should bypass stale cache and re-parse
            methods2 = source_parser.extract_method_signatures(header_path, use_cache=True)
            self.assertEqual(len(methods2), 2)  # Now has 2 methods

            # Verify new methods were parsed (not from stale cache)
            method_names = [m['name'] for m in methods2]
            self.assertIn('GetValue', method_names)
            self.assertIn('SetValue', method_names)

        finally:
            header_path.unlink()

    def test_performance_comparison_cold_vs_cached(self):
        """Test performance comparison between cold parse and cached parse."""
        # Create a more complex header for realistic comparison
        header_content = """
        class ComplexClass {
        public:
            int GetValue() const;
            void SetValue(int Value);
            virtual void Execute() = 0;
            template<typename T>
            T Transform(const T& Input);
            static ComplexClass* Create();

        private:
            void InternalMethod();
            int PrivateValue;
        };
        """

        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.h', delete=False, encoding='utf-8'
        ) as f:
            f.write(header_content)
            header_path = Path(f.name)

        try:
            # Cold parse (no cache)
            start = time.perf_counter()
            methods1 = source_parser.extract_method_signatures(header_path, use_cache=False)
            cold_time = (time.perf_counter() - start) * 1000

            self.assertEqual(len(methods1), 6)

            # Manually cache
            compilation_db_cache.cache_methods(header_path, methods1)

            # Cached parse
            start = time.perf_counter()
            methods2 = source_parser.extract_method_signatures(header_path, use_cache=True)
            cached_time = (time.perf_counter() - start) * 1000

            self.assertEqual(len(methods2), 6)

            # Cache should be significantly faster
            speedup = cold_time / cached_time
            print(f"\nPerformance comparison:")
            print(f"  Cold parse:   {cold_time:.1f}ms")
            print(f"  Cached parse: {cached_time:.1f}ms")
            print(f"  Speedup:      {speedup:.1f}x")

            # Cache should meet <30ms target
            self.assertLess(cached_time, 30.0)

            # Cache should be at least faster than cold parse
            self.assertLess(cached_time, cold_time)

        finally:
            header_path.unlink()


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)
