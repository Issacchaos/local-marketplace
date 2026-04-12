#!/usr/bin/env python3
"""
Proof of concept: Using libclang to parse TEST_CASE macros from C++ files.

This demonstrates:
1. Loading a compilation database
2. Parsing C++ files with correct compiler flags
3. Finding TEST_CASE macro invocations
4. Extracting mangled names for coverage mapping
"""

import sys
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import json

try:
    import clang.cindex
    from clang.cindex import Index, CursorKind, CompilationDatabase, TranslationUnit
except ImportError:
    print("Error: libclang not installed. Run: pip3 install libclang")
    sys.exit(1)


class TestCaseInfo:
    """Information about a discovered test case."""
    def __init__(self, name: str, file_path: str, line: int,
                 mangled_name: Optional[str] = None,
                 tags: Optional[List[str]] = None,
                 macro_type: str = "TEST_CASE"):
        self.name = name
        self.file_path = file_path
        self.line = line
        self.mangled_name = mangled_name
        self.tags = tags or []
        self.macro_type = macro_type

    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "file": self.file_path,
            "line": self.line,
            "mangled_name": self.mangled_name,
            "tags": self.tags,
            "macro_type": self.macro_type
        }

    def __repr__(self):
        return f"TestCase({self.name} @ {self.file_path}:{self.line})"


def extract_string_literal(cursor) -> Optional[str]:
    """Extract string literal from cursor."""
    for token in cursor.get_tokens():
        if token.kind == clang.cindex.TokenKind.LITERAL:
            # Remove quotes from string literal
            return token.spelling.strip('"')
    return None


def find_test_cases_in_ast(cursor, test_cases: List[TestCaseInfo]):
    """
    Walk the AST to find TEST_CASE macro invocations.

    TEST_CASE structure in Catch2:
    TEST_CASE("test name", "[tag1][tag2]") { ... }

    This expands to a function definition with mangled name.
    """
    # Look for macro expansions that could be TEST_CASE
    if cursor.kind == CursorKind.MACRO_INSTANTIATION or cursor.kind == CursorKind.MACRO_DEFINITION:
        spelling = cursor.spelling
        if spelling in ['TEST_CASE', 'TEST_CASE_METHOD', 'ONLINE_TEST_CASE']:
            # Try to extract test name and tags from the macro arguments
            # This is approximate - exact parsing requires preprocessing
            location = cursor.location
            test_info = TestCaseInfo(
                name=f"Test at {location.file.name}:{location.line}",
                file_path=str(location.file.name),
                line=location.line,
                macro_type=spelling
            )
            test_cases.append(test_info)

    # Look for function definitions (what TEST_CASE expands to)
    if cursor.kind == CursorKind.FUNCTION_DECL:
        # Check if this function has a mangled name (C++ linkage)
        mangled = cursor.mangled_name
        display_name = cursor.displayname

        # Check if this looks like a Catch2 test function
        # Catch2 generates functions with specific patterns
        if mangled and ("____C_A_T_C_H____" in mangled or "____CATCH____" in mangled):
            location = cursor.location
            test_info = TestCaseInfo(
                name=display_name or cursor.spelling,
                file_path=str(location.file.name) if location.file else "unknown",
                line=location.line,
                mangled_name=mangled,
                macro_type="FUNCTION_DECL"
            )
            test_cases.append(test_info)

    # Recursively visit children
    for child in cursor.get_children():
        find_test_cases_in_ast(child, test_cases)


def parse_file_with_compilation_db(file_path: Path, compdb_path: Path) -> List[TestCaseInfo]:
    """
    Parse a C++ file using compilation database for correct flags.

    Args:
        file_path: Path to the C++ file to parse
        compdb_path: Path to the directory containing compile_commands.json

    Returns:
        List of discovered test cases
    """
    test_cases = []

    try:
        # Load compilation database
        compdb = CompilationDatabase.fromDirectory(str(compdb_path))

        # Get compile commands for this file
        commands = compdb.getCompileCommands(str(file_path))
        if not commands:
            print(f"Warning: No compile commands found for {file_path}")
            # Try without compilation database
            return parse_file_without_compilation_db(file_path)

        # Extract compiler arguments from first command
        # Skip the compiler executable itself (first arg)
        args = []
        for command in commands:
            for arg in command.arguments:
                args.append(arg)
            break  # Use first command

        # Remove compiler path, source file, and output file arguments
        filtered_args = []
        skip_next = False
        for arg in args[1:]:  # Skip compiler executable
            if skip_next:
                skip_next = False
                continue
            if arg in ['-o', '-c']:
                skip_next = True
                continue
            if arg == str(file_path):
                continue
            filtered_args.append(arg)

        # Parse the translation unit
        index = Index.create()
        tu = index.parse(
            str(file_path),
            args=filtered_args,
            options=TranslationUnit.PARSE_DETAILED_PROCESSING_RECORD
        )

        # Check for parse errors
        if not tu:
            print(f"Error: Failed to parse {file_path}")
            return test_cases

        # Walk the AST to find test cases
        find_test_cases_in_ast(tu.cursor, test_cases)

    except Exception as e:
        print(f"Error parsing {file_path}: {e}")
        import traceback
        traceback.print_exc()

    return test_cases


def parse_file_without_compilation_db(file_path: Path) -> List[TestCaseInfo]:
    """
    Parse a C++ file without compilation database (basic flags).
    This is a fallback when compilation database is not available.
    """
    test_cases = []

    try:
        index = Index.create()

        # Basic C++ flags (won't work for complex UE code)
        args = [
            '-x', 'c++',
            '-std=c++17',
            '-I/usr/include',
            '-I/usr/local/include'
        ]

        tu = index.parse(
            str(file_path),
            args=args,
            options=TranslationUnit.PARSE_DETAILED_PROCESSING_RECORD
        )

        if not tu:
            print(f"Error: Failed to parse {file_path}")
            return test_cases

        find_test_cases_in_ast(tu.cursor, test_cases)

    except Exception as e:
        print(f"Error parsing {file_path} without compilation database: {e}")

    return test_cases


def demo_with_example_compdb():
    """
    Demonstrate using the example compilation database from UE source.
    """
    compdb_dir = Path("/Users/stephen.ma/Fornite_Main/Engine/Source/ThirdParty/ShaderConductor/ShaderConductor/External/DirectXShaderCompiler/tools/clang/bindings/python/tests/cindex/INPUTS")

    if not compdb_dir.exists():
        print(f"Example compilation database not found at {compdb_dir}")
        return

    try:
        compdb = CompilationDatabase.fromDirectory(str(compdb_dir))
        all_commands = compdb.getAllCompileCommands()

        print(f"Found {len(all_commands)} compile commands in example database:")
        for cmd in all_commands:
            print(f"  - {cmd.filename}")
            print(f"    Directory: {cmd.directory}")
            print(f"    Command: {' '.join(arg for arg in cmd.arguments)}")
            print()

    except Exception as e:
        print(f"Error loading example compilation database: {e}")


def main():
    print("Clang Compilation Database Test Parser")
    print("=" * 60)
    print()

    # Check if libclang is working
    print("Testing libclang installation...")
    try:
        index = Index.create()
        print("✓ libclang is installed and working")
    except Exception as e:
        print(f"✗ libclang error: {e}")
        return 1

    print()

    # Demo with example compilation database
    print("Testing with example compilation database:")
    print("-" * 60)
    demo_with_example_compdb()

    print()
    print("=" * 60)
    print("Usage:")
    print("  To use with a real test file:")
    print("  1. Generate compilation database: ushell .build misc clangdb FortniteEditor")
    print("  2. Parse test file:")
    print("     python3 test_clang_parsing.py <path_to_test_file.cpp>")
    print()
    print("Example:")
    print("  python3 test_clang_parsing.py \\")
    print("    Plugins/CosmeticsFramework/CosmeticsFrameworkFlowgraph/Source/CosmeticsFrameworkFlowgraphTests/Private/CosmeticsFrameworkFlowgraphTests.cpp")

    return 0


if __name__ == "__main__":
    sys.exit(main())
