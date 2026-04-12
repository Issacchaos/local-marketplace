#!/usr/bin/env python3
"""
Example usage of metadata_resolver module for generating test stubs.

This example demonstrates the complete workflow:
1. Parse llt-find JSON output
2. Identify untested methods
3. Extract method signatures
4. Generate test stubs with appropriate templates
"""

import json
import sys
from pathlib import Path

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))

from metadata_resolver import (
    parse_llt_find_output,
    identify_untested_methods,
    generate_stubs_for_file
)


def create_sample_llt_find_output(output_path: Path):
    """Create sample llt-find JSON output for demonstration."""
    sample_data = {
        "source_files": [
            {
                "file": "//depot/FortniteLLTs/Source/Runtime/CommChannels/Public/CommChannelNode.h",
                "methods": [
                    "ConnectTo",
                    "IsConnectedTo",
                    "SetChannelValue",
                    "GetChannelValue",
                    "Disconnect"
                ],
                "test_files": [
                    "Tests/CommChannelsTests/Private/CommChannelNodeTests.cpp"
                ],
                "tested_methods": [
                    "ConnectTo",
                    "IsConnectedTo"
                ],
                "untested_methods": [
                    "SetChannelValue",
                    "GetChannelValue",
                    "Disconnect"
                ]
            }
        ]
    }

    output_path.write_text(json.dumps(sample_data, indent=2))
    print(f"✓ Created sample llt-find output: {output_path}")


def main():
    """Run example workflow."""
    print("=" * 80)
    print("Metadata Resolver Example")
    print("=" * 80)

    # Setup paths
    example_dir = Path(__file__).parent
    llt_find_json = example_dir / "sample_llt_find_output.json"
    output_dir = example_dir / "generated_stubs"
    output_dir.mkdir(exist_ok=True)

    # Step 1: Create sample llt-find output
    print("\nStep 1: Creating sample llt-find output...")
    create_sample_llt_find_output(llt_find_json)

    # Step 2: Parse llt-find output
    print("\nStep 2: Parsing llt-find output...")
    llt_find_data = parse_llt_find_output(llt_find_json)
    print(f"✓ Found {len(llt_find_data['source_files'])} source file(s)")

    # Step 3: Identify untested methods
    print("\nStep 3: Identifying untested methods...")
    source_file = Path("CommChannelNode.h")
    untested = identify_untested_methods(source_file, llt_find_data)
    print(f"✓ Identified {len(untested)} untested method(s):")
    for method in untested:
        print(f"  - {method}")

    # Step 4: Generate test stubs
    print("\nStep 4: Generating test stubs...")
    print("Note: This requires actual source files and will use mocked signatures")

    # For demo purposes, we'll show the expected output structure
    # In real usage, this would call generate_stubs_for_file with real paths
    print("\nExpected output structure:")
    print("""
    {
      "source_file": "CommChannelNode.h",
      "untested_methods": ["SetChannelValue", "GetChannelValue", "Disconnect"],
      "generated_stubs": [
        {
          "method_name": "SetChannelValue",
          "stub_code": "TEST_CASE(...) { ... }",
          "line_count": 15,
          "has_params": true,
          "return_type": "void"
        },
        ...
      ],
      "stub_count": 3,
      "template": "basic",
      "dependencies": ["Core", "CoreUObject", "CommChannelsRuntime"],
      "warnings": []
    }
    """)

    # Step 5: Show example stub code
    print("\nExample generated stub:")
    print("""
TEST_CASE("FCommChannelNode::SetChannelValue", "[comm_channels]") {
    // Arrange
    // TODO: Set up test fixture for SetChannelValue
    const FString& ChannelName; // TODO: Initialize ChannelName
    const FVariant& Value; // TODO: Initialize Value

    // Act
    // TODO: Call SetChannelValue with test inputs
    // Example: FCommChannelNode instance;
    // instance.SetChannelValue(ChannelName, Value);

    // Assert
    // TODO: Verify expected behavior
    // REQUIRE(condition);
}
    """)

    print("\n" + "=" * 80)
    print("Example Complete!")
    print("=" * 80)
    print(f"\nSample files created in: {example_dir}")
    print(f"  - {llt_find_json.name}")
    print(f"  - {output_dir.name}/")
    print("\nTo run metadata_resolver with real files:")
    print("  python metadata_resolver.py llt-find-output.json Source.h -o generated/")


if __name__ == '__main__':
    main()
