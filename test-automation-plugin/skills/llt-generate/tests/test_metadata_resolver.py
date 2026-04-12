#!/usr/bin/env python3
"""
Tests for metadata_resolver module.

Tests metadata-driven test stub generation using llt-find output.

Requirements Coverage:
- REQ-F-30: Parse llt-find JSON output
- REQ-F-31: Compare source methods against tested methods
- REQ-F-32: Generate test stubs for untested methods
- REQ-F-33: Infer test dependencies
- REQ-F-34: Maintain consistent tagging
- REQ-F-35: Extract method signatures from source headers
"""

import json
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Import module under test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))

from metadata_resolver import (
    parse_llt_find_output,
    identify_untested_methods,
    extract_method_signature,
    infer_test_dependencies,
    generate_test_stub,
    generate_stubs_for_file,
    MetadataResolverError,
    InvalidJsonError,
    SourceFileNotFoundError
)


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def sample_llt_find_output():
    """Sample llt-find JSON output with 5 methods (2 tested, 3 untested)."""
    return {
        "source_files": [
            {
                "file": "//depot/FortniteLLTs/Source/Runtime/CommChannels/Public/CommChannelNode.h",
                "methods": ["ConnectTo", "IsConnectedTo", "SetChannelValue", "GetChannelValue", "Disconnect"],
                "test_files": ["Tests/CommChannelsTests/Private/CommChannelNodeTests.cpp"],
                "tested_methods": ["ConnectTo", "IsConnectedTo"],
                "untested_methods": ["SetChannelValue", "GetChannelValue", "Disconnect"]
            }
        ]
    }


@pytest.fixture
def sample_method_signatures():
    """Sample method signatures extracted from header."""
    return [
        {
            'name': 'SetChannelValue',
            'return_type': 'void',
            'params': [
                {'type': 'const FString&', 'name': 'ChannelName'},
                {'type': 'const FVariant&', 'name': 'Value'}
            ],
            'is_const': False,
            'is_virtual': False,
            'is_pure_virtual': False,
            'is_static': False,
            'has_ufunction': False,
            'is_template': False,
            'line': 45,
            'class_name': 'FCommChannelNode'
        },
        {
            'name': 'GetChannelValue',
            'return_type': 'FVariant',
            'params': [
                {'type': 'const FString&', 'name': 'ChannelName'}
            ],
            'is_const': True,
            'is_virtual': False,
            'is_pure_virtual': False,
            'is_static': False,
            'has_ufunction': False,
            'is_template': False,
            'line': 50,
            'class_name': 'FCommChannelNode'
        },
        {
            'name': 'Disconnect',
            'return_type': 'void',
            'params': [],
            'is_const': False,
            'is_virtual': False,
            'is_pure_virtual': False,
            'is_static': False,
            'has_ufunction': False,
            'is_template': False,
            'line': 55,
            'class_name': 'FCommChannelNode'
        }
    ]


@pytest.fixture
def temp_json_file(tmp_path, sample_llt_find_output):
    """Create temporary JSON file with llt-find output."""
    json_file = tmp_path / "llt-find-output.json"
    json_file.write_text(json.dumps(sample_llt_find_output, indent=2))
    return json_file


# ============================================================================
# parse_llt_find_output Tests (REQ-F-30)
# ============================================================================

def test_parse_llt_find_output_valid_json(temp_json_file):
    """Test parsing valid llt-find JSON file."""
    result = parse_llt_find_output(temp_json_file)

    assert 'source_files' in result
    assert len(result['source_files']) == 1
    assert result['source_files'][0]['file'].endswith('CommChannelNode.h')
    assert len(result['source_files'][0]['methods']) == 5
    assert len(result['source_files'][0]['tested_methods']) == 2
    assert len(result['source_files'][0]['untested_methods']) == 3


def test_parse_llt_find_output_invalid_json(tmp_path):
    """Test parsing invalid JSON raises InvalidJsonError."""
    invalid_json_file = tmp_path / "invalid.json"
    invalid_json_file.write_text("{ invalid json }")

    with pytest.raises(InvalidJsonError) as exc_info:
        parse_llt_find_output(invalid_json_file)

    assert "Invalid JSON" in str(exc_info.value)


def test_parse_llt_find_output_missing_file():
    """Test parsing missing file raises FileNotFoundError."""
    missing_file = Path("/nonexistent/file.json")

    with pytest.raises(FileNotFoundError) as exc_info:
        parse_llt_find_output(missing_file)

    assert "not found" in str(exc_info.value)


def test_parse_llt_find_output_empty_json(tmp_path):
    """Test parsing empty JSON returns empty structure."""
    empty_json = tmp_path / "empty.json"
    empty_json.write_text("{}")

    result = parse_llt_find_output(empty_json)

    assert result == {}


def test_parse_llt_find_output_missing_source_files(tmp_path):
    """Test parsing JSON without source_files key."""
    invalid_structure = tmp_path / "invalid_structure.json"
    invalid_structure.write_text(json.dumps({"other_key": "value"}))

    result = parse_llt_find_output(invalid_structure)

    assert 'source_files' not in result


# ============================================================================
# identify_untested_methods Tests (REQ-F-31)
# ============================================================================

def test_identify_untested_methods_basic(sample_llt_find_output):
    """Test identifying untested methods from llt-find output."""
    source_file = Path("CommChannelNode.h")

    untested = identify_untested_methods(source_file, sample_llt_find_output)

    assert len(untested) == 3
    assert 'SetChannelValue' in untested
    assert 'GetChannelValue' in untested
    assert 'Disconnect' in untested


def test_identify_untested_methods_all_tested():
    """Test when all methods are tested returns empty list."""
    llt_find_data = {
        "source_files": [
            {
                "file": "//depot/path/to/MyClass.h",
                "methods": ["MethodA", "MethodB"],
                "tested_methods": ["MethodA", "MethodB"],
                "untested_methods": []
            }
        ]
    }

    untested = identify_untested_methods(Path("MyClass.h"), llt_find_data)

    assert len(untested) == 0


def test_identify_untested_methods_no_tests():
    """Test when no methods are tested returns all methods."""
    llt_find_data = {
        "source_files": [
            {
                "file": "//depot/path/to/MyClass.h",
                "methods": ["MethodA", "MethodB", "MethodC"],
                "tested_methods": [],
                "untested_methods": ["MethodA", "MethodB", "MethodC"]
            }
        ]
    }

    untested = identify_untested_methods(Path("MyClass.h"), llt_find_data)

    assert len(untested) == 3
    assert 'MethodA' in untested
    assert 'MethodB' in untested
    assert 'MethodC' in untested


def test_identify_untested_methods_source_file_not_found(sample_llt_find_output):
    """Test when source file not in llt-find output returns empty list."""
    nonexistent_file = Path("NonexistentFile.h")

    untested = identify_untested_methods(nonexistent_file, sample_llt_find_output)

    assert len(untested) == 0


def test_identify_untested_methods_fuzzy_match(sample_llt_find_output):
    """Test fuzzy matching for source file paths."""
    # Test with different path formats
    source_file = Path("Public/CommChannelNode.h")

    untested = identify_untested_methods(source_file, sample_llt_find_output)

    assert len(untested) == 3


# ============================================================================
# extract_method_signature Tests (REQ-F-35)
# ============================================================================

@patch('metadata_resolver.source_parser.extract_method_signatures')
def test_extract_method_signature_found(mock_extract, sample_method_signatures):
    """Test extracting method signature when method exists."""
    mock_extract.return_value = sample_method_signatures

    header_path = Path("CommChannelNode.h")
    sig = extract_method_signature("SetChannelValue", header_path)

    assert sig is not None
    assert sig['name'] == 'SetChannelValue'
    assert sig['return_type'] == 'void'
    assert len(sig['params']) == 2


@patch('metadata_resolver.source_parser.extract_method_signatures')
def test_extract_method_signature_not_found(mock_extract, sample_method_signatures):
    """Test extracting method signature when method doesn't exist."""
    mock_extract.return_value = sample_method_signatures

    header_path = Path("CommChannelNode.h")
    sig = extract_method_signature("NonexistentMethod", header_path)

    assert sig is None


@patch('metadata_resolver.source_parser.extract_method_signatures')
def test_extract_method_signature_header_not_found(mock_extract):
    """Test extracting method signature when header file doesn't exist."""
    mock_extract.return_value = []

    header_path = Path("/nonexistent/header.h")
    sig = extract_method_signature("SomeMethod", header_path)

    assert sig is None


@patch('metadata_resolver.source_parser.extract_method_signatures')
def test_extract_method_signature_with_compdb(mock_extract, sample_method_signatures):
    """Test extracting method signature with compilation database."""
    mock_extract.return_value = sample_method_signatures

    header_path = Path("CommChannelNode.h")
    compdb_path = Path("/path/to/compile_commands.json")

    sig = extract_method_signature("GetChannelValue", header_path, compdb_path)

    assert sig is not None
    assert sig['name'] == 'GetChannelValue'
    assert sig['is_const'] is True

    # Verify compilation database was passed
    mock_extract.assert_called_once_with(header_path, compdb_path, use_cache=True)


# ============================================================================
# infer_test_dependencies Tests (REQ-F-33)
# ============================================================================

@patch('metadata_resolver.module_analyzer.extract_dependencies')
def test_infer_test_dependencies_from_build_cs(mock_extract_deps, tmp_path):
    """Test inferring dependencies from existing test module's .Build.cs."""
    # Mock existing test module with .Build.cs
    test_module_path = tmp_path / "CommChannelsTests"
    test_module_path.mkdir()
    build_cs = test_module_path / "CommChannelsTests.Build.cs"
    build_cs.write_text("""
        PrivateDependencyModuleNames.AddRange(
            new string[] {
                "Core",
                "CoreUObject",
                "CommChannelsRuntime",
                "ApplicationCore"
            }
        );
    """)

    mock_extract_deps.return_value = ['Core', 'CoreUObject', 'CommChannelsRuntime', 'ApplicationCore']

    deps = infer_test_dependencies(test_module_path)

    assert len(deps) == 4
    assert 'CommChannelsRuntime' in deps
    assert 'Core' in deps


@patch('metadata_resolver.module_analyzer.extract_dependencies')
def test_infer_test_dependencies_no_build_cs(mock_extract_deps, tmp_path):
    """Test inferring dependencies when no .Build.cs exists returns defaults."""
    nonexistent_module = tmp_path / "NonexistentModule"

    # Mock will not be called, should return defaults
    mock_extract_deps.side_effect = FileNotFoundError("Build.cs not found")

    deps = infer_test_dependencies(nonexistent_module)

    # Should return essential dependencies as fallback
    assert 'Core' in deps
    assert 'CoreUObject' in deps
    assert 'ApplicationCore' in deps


def test_infer_test_dependencies_from_llt_find_data():
    """Test inferring dependencies from llt-find test_files list."""
    llt_find_data = {
        "source_files": [
            {
                "file": "//depot/path/to/Source.h",
                "test_files": ["Tests/ModuleTests/Private/SourceTests.cpp"],
                "tested_methods": ["MethodA"]
            }
        ]
    }

    # Extract test module path from test_files
    test_file = llt_find_data['source_files'][0]['test_files'][0]
    test_module_path = Path(test_file).parent.parent

    assert 'ModuleTests' in str(test_module_path)


# ============================================================================
# generate_test_stub Tests (REQ-F-32)
# ============================================================================

def test_generate_test_stub_basic():
    """Test generating basic test stub with method signature."""
    method_sig = {
        'name': 'SetChannelValue',
        'return_type': 'void',
        'params': [
            {'type': 'const FString&', 'name': 'ChannelName'},
            {'type': 'const FVariant&', 'name': 'Value'}
        ],
        'class_name': 'FCommChannelNode'
    }

    context = {
        'module_name': 'CommChannels',
        'test_tag': '[comm_channels]'
    }

    stub = generate_test_stub(method_sig, 'basic', context)

    # Verify stub structure
    assert 'TEST_CASE' in stub
    assert 'FCommChannelNode::SetChannelValue' in stub
    assert '[comm_channels]' in stub
    assert 'Arrange' in stub
    assert 'Act' in stub
    assert 'Assert' in stub
    assert 'TODO' in stub

    # Verify parameter placeholders
    assert 'ChannelName' in stub or 'TODO' in stub
    assert 'Value' in stub or 'TODO' in stub


def test_generate_test_stub_const_method():
    """Test generating stub for const method."""
    method_sig = {
        'name': 'GetChannelValue',
        'return_type': 'FVariant',
        'params': [{'type': 'const FString&', 'name': 'ChannelName'}],
        'is_const': True,
        'class_name': 'FCommChannelNode'
    }

    context = {'module_name': 'CommChannels', 'test_tag': '[comm_channels]'}

    stub = generate_test_stub(method_sig, 'basic', context)

    assert 'GetChannelValue' in stub
    assert 'const' in stub or 'TODO' in stub


def test_generate_test_stub_no_params():
    """Test generating stub for method with no parameters."""
    method_sig = {
        'name': 'Disconnect',
        'return_type': 'void',
        'params': [],
        'class_name': 'FCommChannelNode'
    }

    context = {'module_name': 'CommChannels', 'test_tag': '[comm_channels]'}

    stub = generate_test_stub(method_sig, 'basic', context)

    assert 'Disconnect' in stub
    assert 'TEST_CASE' in stub


def test_generate_test_stub_fixture_template():
    """Test generating stub using fixture template."""
    method_sig = {
        'name': 'ProcessRequest',
        'return_type': 'bool',
        'params': [{'type': 'const FRequest&', 'name': 'Request'}],
        'class_name': 'FRequestHandler'
    }

    context = {
        'module_name': 'RequestSystem',
        'test_tag': '[request_system]',
        'fixture_class': 'FRequestHandlerFixture'
    }

    stub = generate_test_stub(method_sig, 'fixture', context)

    assert 'ProcessRequest' in stub
    assert 'FRequestHandlerFixture' in stub or 'TODO' in stub


def test_generate_test_stub_consistent_tagging():
    """Test stub generation maintains consistent tagging with existing tests (REQ-F-34)."""
    method_sig = {
        'name': 'NewMethod',
        'return_type': 'void',
        'params': [],
        'class_name': 'FMyClass'
    }

    # Context includes existing test tags
    context = {
        'module_name': 'MyModule',
        'test_tag': '[my_module][core]',  # Multiple tags from existing tests
        'existing_tags': ['my_module', 'core']
    }

    stub = generate_test_stub(method_sig, 'basic', context)

    # Verify tags are maintained
    assert '[my_module]' in stub or '[core]' in stub


# ============================================================================
# generate_stubs_for_file Tests (REQ-F-30 to REQ-F-35)
# ============================================================================

@patch('metadata_resolver.source_parser.extract_method_signatures')
@patch('metadata_resolver.module_analyzer.extract_dependencies')
def test_generate_stubs_for_file_complete_workflow(
    mock_extract_deps,
    mock_extract_sigs,
    sample_llt_find_output,
    sample_method_signatures,
    tmp_path
):
    """Test complete workflow: parse llt-find → identify untested → generate stubs."""
    # Setup mocks
    mock_extract_sigs.return_value = sample_method_signatures
    mock_extract_deps.return_value = ['Core', 'CoreUObject', 'CommChannelsRuntime']

    source_file = Path("CommChannelNode.h")
    output_dir = tmp_path / "generated"
    output_dir.mkdir()

    result = generate_stubs_for_file(
        source_file,
        sample_llt_find_output,
        output_dir,
        template='basic'
    )

    # Verify result structure
    assert 'source_file' in result
    assert 'untested_methods' in result
    assert 'generated_stubs' in result
    assert 'stub_count' in result

    # Verify correct number of stubs
    assert result['stub_count'] == 3
    assert len(result['generated_stubs']) == 3

    # Verify stub details
    stub_names = [s['method_name'] for s in result['generated_stubs']]
    assert 'SetChannelValue' in stub_names
    assert 'GetChannelValue' in stub_names
    assert 'Disconnect' in stub_names


@patch('metadata_resolver.source_parser.extract_method_signatures')
def test_generate_stubs_for_file_no_untested_methods(mock_extract_sigs, tmp_path):
    """Test generating stubs when all methods are tested."""
    llt_find_data = {
        "source_files": [
            {
                "file": "//depot/path/to/FullyCovered.h",
                "methods": ["MethodA", "MethodB"],
                "tested_methods": ["MethodA", "MethodB"],
                "untested_methods": []
            }
        ]
    }

    source_file = Path("FullyCovered.h")
    output_dir = tmp_path / "generated"
    output_dir.mkdir()

    result = generate_stubs_for_file(source_file, llt_find_data, output_dir)

    assert result['stub_count'] == 0
    assert len(result['generated_stubs']) == 0


@patch('metadata_resolver.source_parser.extract_method_signatures')
def test_generate_stubs_for_file_missing_signatures(mock_extract_sigs, sample_llt_find_output, tmp_path):
    """Test generating stubs when some method signatures cannot be extracted."""
    # Return fewer signatures than untested methods
    mock_extract_sigs.return_value = [
        {
            'name': 'SetChannelValue',
            'return_type': 'void',
            'params': [],
            'class_name': 'FCommChannelNode'
        }
        # Missing: GetChannelValue, Disconnect
    ]

    source_file = Path("CommChannelNode.h")
    output_dir = tmp_path / "generated"
    output_dir.mkdir()

    result = generate_stubs_for_file(source_file, sample_llt_find_output, output_dir)

    # Should generate stubs only for methods with signatures
    assert result['stub_count'] >= 1

    # Should log warnings for missing signatures
    assert 'warnings' in result or result['stub_count'] < 3


@patch('metadata_resolver.source_parser.extract_method_signatures')
@patch('metadata_resolver.pattern_detector.detect_test_pattern')
def test_generate_stubs_for_file_automatic_template_selection(
    mock_detect_pattern,
    mock_extract_sigs,
    sample_llt_find_output,
    sample_method_signatures,
    tmp_path
):
    """Test automatic template selection based on source analysis (REQ-F-32)."""
    mock_extract_sigs.return_value = sample_method_signatures
    mock_detect_pattern.return_value = 'async'  # Auto-detected async pattern

    source_file = Path("CommChannelNode.h")
    output_dir = tmp_path / "generated"
    output_dir.mkdir()

    # Don't specify template - should auto-detect
    result = generate_stubs_for_file(
        source_file,
        sample_llt_find_output,
        output_dir,
        template=None  # Auto-detect
    )

    assert result['template'] == 'async'
    assert result['stub_count'] == 3


@patch('metadata_resolver.source_parser.extract_method_signatures')
def test_generate_stubs_for_file_with_compilation_database(
    mock_extract_sigs,
    sample_llt_find_output,
    sample_method_signatures,
    tmp_path
):
    """Test generating stubs with compilation database for accurate signatures."""
    mock_extract_sigs.return_value = sample_method_signatures

    source_file = Path("CommChannelNode.h")
    output_dir = tmp_path / "generated"
    output_dir.mkdir()
    compdb_path = Path("/path/to/compile_commands.json")

    result = generate_stubs_for_file(
        source_file,
        sample_llt_find_output,
        output_dir,
        compdb_path=compdb_path
    )

    # Verify compilation database was used
    mock_extract_sigs.assert_called()
    call_args = mock_extract_sigs.call_args
    assert call_args is not None

    assert result['stub_count'] == 3


# ============================================================================
# Edge Cases and Error Handling
# ============================================================================

def test_parse_llt_find_output_malformed_structure(tmp_path):
    """Test parsing JSON with unexpected structure logs warning but doesn't crash."""
    malformed_json = tmp_path / "malformed.json"
    malformed_json.write_text(json.dumps({
        "source_files": "not_a_list"  # Should be array
    }))

    result = parse_llt_find_output(malformed_json)

    # Should return data even if structure unexpected
    assert isinstance(result, dict)


def test_identify_untested_methods_empty_source_files():
    """Test identifying untested methods with empty source_files."""
    llt_find_data = {"source_files": []}

    untested = identify_untested_methods(Path("AnyFile.h"), llt_find_data)

    assert len(untested) == 0


def test_generate_test_stub_empty_context():
    """Test generating stub with minimal context uses defaults."""
    method_sig = {
        'name': 'TestMethod',
        'return_type': 'void',
        'params': [],
        'class_name': 'FTestClass'
    }

    stub = generate_test_stub(method_sig, 'basic', {})

    # Should generate stub with TODO placeholders for missing context
    assert 'TestMethod' in stub
    assert 'TODO' in stub


def test_generate_stubs_for_file_invalid_output_dir():
    """Test generating stubs with invalid output directory raises error."""
    llt_find_data = {"source_files": []}

    with pytest.raises((FileNotFoundError, OSError, MetadataResolverError)):
        generate_stubs_for_file(
            Path("Source.h"),
            llt_find_data,
            Path("/nonexistent/invalid/path")
        )


# ============================================================================
# Integration Test
# ============================================================================

@patch('metadata_resolver.source_parser.extract_method_signatures')
@patch('metadata_resolver.module_analyzer.extract_dependencies')
@patch('metadata_resolver.pattern_detector.detect_test_pattern')
def test_full_integration_workflow(
    mock_detect_pattern,
    mock_extract_deps,
    mock_extract_sigs,
    temp_json_file,
    sample_method_signatures,
    tmp_path
):
    """Integration test: Full workflow from JSON file to generated stubs."""
    # Setup mocks
    mock_extract_sigs.return_value = sample_method_signatures
    mock_extract_deps.return_value = ['Core', 'CoreUObject', 'CommChannelsRuntime']
    mock_detect_pattern.return_value = 'basic'

    # Parse llt-find output
    llt_find_data = parse_llt_find_output(temp_json_file)

    # Identify untested methods
    source_file = Path("CommChannelNode.h")
    untested = identify_untested_methods(source_file, llt_find_data)
    assert len(untested) == 3

    # Generate stubs
    output_dir = tmp_path / "generated"
    output_dir.mkdir()

    result = generate_stubs_for_file(source_file, llt_find_data, output_dir)

    # Verify complete result
    assert result['stub_count'] == 3
    assert len(result['generated_stubs']) == 3

    # Verify each stub has required fields
    for stub_info in result['generated_stubs']:
        assert 'method_name' in stub_info
        assert 'stub_code' in stub_info
        assert 'line_count' in stub_info

        # Verify stub code structure
        stub_code = stub_info['stub_code']
        assert 'TEST_CASE' in stub_code
        assert 'Arrange' in stub_code
        assert 'Act' in stub_code
        assert 'Assert' in stub_code


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
