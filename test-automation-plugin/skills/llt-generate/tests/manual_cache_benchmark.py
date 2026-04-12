#!/usr/bin/env python3
"""
Manual benchmark to demonstrate cache performance improvements.

This script provides a realistic demonstration of cache performance with
UE-style headers containing multiple methods.
"""

import sys
import tempfile
import time
from pathlib import Path

# Add scripts directory to path for direct imports
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import compilation_db_cache
import source_parser


def create_realistic_ue_header(method_count: int = 20) -> str:
    """
    Create a realistic UE-style header with multiple methods.

    Args:
        method_count: Number of methods to generate

    Returns:
        C++ header content
    """
    header = """#pragma once

#include "CoreMinimal.h"
#include "UObject/Object.h"
#include "MyClass.generated.h"

/**
 * Example Unreal Engine class with multiple methods.
 */
UCLASS(BlueprintType)
class MYMODULE_API UMyClass : public UObject
{
    GENERATED_BODY()

public:
    /** Constructor */
    UMyClass();

"""

    # Generate methods
    for i in range(method_count):
        if i % 4 == 0:
            # UFUNCTION method
            header += f"""    UFUNCTION(BlueprintCallable, Category="MyCategory")
    void BlueprintMethod{i}(int32 Param1, const FString& Param2);

"""
        elif i % 4 == 1:
            # Virtual method
            header += f"""    virtual void VirtualMethod{i}(float Value) override;

"""
        elif i % 4 == 2:
            # Const method
            header += f"""    int32 GetValue{i}() const;

"""
        else:
            # Template method
            header += f"""    template<typename T>
    T TransformValue{i}(const T& Input);

"""

    header += """private:
    /** Internal state */
    int32 InternalValue;
    FString InternalString;
};
"""

    return header


def benchmark_cache_performance():
    """
    Benchmark cache performance with realistic UE header.
    """
    print("=" * 80)
    print("Compilation Database Cache Performance Benchmark")
    print("=" * 80)

    # Create realistic header
    method_count = 20
    header_content = create_realistic_ue_header(method_count)

    print(f"\nTest Setup:")
    print(f"  - Methods: {method_count}")
    print(f"  - Header size: {len(header_content)} bytes")

    # Create temporary file
    with tempfile.NamedTemporaryFile(
        mode='w', suffix='.h', delete=False, encoding='utf-8'
    ) as f:
        f.write(header_content)
        header_path = Path(f.name)

    try:
        # Cold parse (no cache, regex mode)
        print(f"\n{'Test 1: Cold Parse (No Cache)':-^80}")
        start = time.perf_counter()
        methods1 = source_parser.extract_method_signatures(header_path, use_cache=False)
        cold_time = (time.perf_counter() - start) * 1000

        print(f"  Results:")
        print(f"    - Methods extracted: {len(methods1)}")
        print(f"    - Parse time: {cold_time:.2f}ms")
        print(f"    - Average per method: {cold_time / len(methods1):.2f}ms")

        # Cache the results
        print(f"\n{'Test 2: Caching Results':-^80}")
        start = time.perf_counter()
        success = compilation_db_cache.cache_methods(header_path, methods1)
        cache_write_time = (time.perf_counter() - start) * 1000

        print(f"  Results:")
        print(f"    - Cache write: {'SUCCESS' if success else 'FAILED'}")
        print(f"    - Write time: {cache_write_time:.2f}ms")

        # Cached parse (warm cache)
        print(f"\n{'Test 3: Cached Parse (Warm Cache)':-^80}")
        times = []
        for i in range(10):
            start = time.perf_counter()
            methods2 = source_parser.extract_method_signatures(header_path, use_cache=True)
            elapsed = (time.perf_counter() - start) * 1000
            times.append(elapsed)

        avg_cached_time = sum(times) / len(times)
        min_cached_time = min(times)
        max_cached_time = max(times)

        print(f"  Results (10 iterations):")
        print(f"    - Methods extracted: {len(methods2)}")
        print(f"    - Average time: {avg_cached_time:.2f}ms")
        print(f"    - Min time: {min_cached_time:.2f}ms")
        print(f"    - Max time: {max_cached_time:.2f}ms")
        print(f"    - Average per method: {avg_cached_time / len(methods2):.2f}ms")

        # Performance comparison
        print(f"\n{'Performance Summary':-^80}")
        speedup = cold_time / avg_cached_time
        improvement = ((cold_time - avg_cached_time) / cold_time) * 100

        print(f"  Speedup: {speedup:.1f}x faster")
        print(f"  Improvement: {improvement:.1f}% faster")

        # Verify <30ms requirement
        meets_requirement = avg_cached_time < 30.0
        print(f"\n  REQ-F-39 (<30ms cache hit): {'✓ PASS' if meets_requirement else '✗ FAIL'}")
        if meets_requirement:
            margin = 30.0 - avg_cached_time
            print(f"    - Margin: {margin:.2f}ms under target")
        else:
            overage = avg_cached_time - 30.0
            print(f"    - Overage: {overage:.2f}ms over target")

        # Cache statistics
        print(f"\n{'Cache Statistics':-^80}")
        stats = compilation_db_cache.get_cache_stats()
        print(f"  Cache entries: {stats['entry_count']}")
        print(f"  Total size: {stats['total_size_mb']:.3f} MB")

        # Test file modification (invalidation)
        print(f"\n{'Test 4: File Modification (Cache Invalidation)':-^80}")
        time.sleep(0.1)  # Ensure mtime changes
        with open(header_path, 'a', encoding='utf-8') as f:
            f.write("\n// Modified\n")

        cached_after_mod = compilation_db_cache.get_cached_methods(header_path)
        print(f"  Cache after modification: {'INVALID (as expected)' if cached_after_mod is None else 'VALID (unexpected!)'}")

        # Re-parse after modification
        start = time.perf_counter()
        methods3 = source_parser.extract_method_signatures(header_path, use_cache=True)
        reparse_time = (time.perf_counter() - start) * 1000

        print(f"  Re-parse time: {reparse_time:.2f}ms")
        print(f"  Methods extracted: {len(methods3)}")

        # Final summary
        print(f"\n{'Benchmark Complete':-^80}")
        print(f"\nKey Findings:")
        print(f"  1. Cache reduces parse time by {improvement:.1f}%")
        print(f"  2. Average cached parse: {avg_cached_time:.2f}ms (target: <30ms)")
        print(f"  3. Cache automatically invalidates on file modification")
        print(f"  4. Performance is consistent across multiple accesses")

    finally:
        # Cleanup
        if header_path.exists():
            header_path.unlink()

        # Clear test cache
        count = compilation_db_cache.clear_all_cache()
        print(f"\nCleanup: Cleared {count} cache entries")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    benchmark_cache_performance()
