#!/usr/bin/env python3
"""
Metadata Resolver - CLI for Method Signature Extraction

This script provides a CLI command for extracting method signatures from C++ header files.
It delegates to source_parser.py which uses libclang for accurate AST-based parsing.

Requirements:
- REQ-F-35: Extract method signatures via source_parser delegation

Usage:
    # Extract method signature
    python3 metadata_resolver.py extract-signature --method SetChannelValue --header CommChannelNode.h

    # With compilation database
    python3 metadata_resolver.py extract-signature --method Foo --header Bar.h --compdb .

Note: Extract-dependencies functionality has been removed. The algorithm is now in SKILL.md
(lines 710-754) for agents to execute directly using Grep/Read tools.
"""

import json
import sys
from pathlib import Path

# Import existing infrastructure
try:
    from . import source_parser
except ImportError:
    # Fallback for standalone execution
    import source_parser


# ============================================================================
# CLI Command: extract-signature
# ============================================================================

def cmd_extract_signature(args):
    """
    Extract method signature from header file.

    Delegates to source_parser.extract_method_signatures() with caching enabled.
    Returns method signature as JSON or error if method not found.

    Args:
        args: Namespace with method, header, compdb attributes

    Returns:
        Exit code (0 = success, 1 = error)
    """
    method_name = args.method
    header_path = Path(args.header)
    compdb_path = Path(args.compdb) if args.compdb else None

    # Validate header exists
    if not header_path.exists():
        result = {
            'status': 'error',
            'error': f'Header file not found: {header_path}',
            'method': method_name,
            'header': str(header_path)
        }
        print(json.dumps(result, indent=2))
        return 1

    try:
        # Extract all methods from header using source_parser
        methods = source_parser.extract_method_signatures(
            header_path,
            compdb_path,
            use_cache=True
        )

        # Find matching method
        for method in methods:
            if method['name'] == method_name:
                result = {
                    'status': 'success',
                    'method': method_name,
                    'header': str(header_path),
                    'signature': method
                }
                print(json.dumps(result, indent=2))
                return 0

        # Method not found
        result = {
            'status': 'error',
            'error': f'Method {method_name} not found in {header_path.name}',
            'method': method_name,
            'header': str(header_path),
            'available_methods': [m['name'] for m in methods[:10]]  # First 10 for context
        }
        print(json.dumps(result, indent=2))
        return 1

    except Exception as e:
        result = {
            'status': 'error',
            'error': str(e),
            'method': method_name,
            'header': str(header_path)
        }
        print(json.dumps(result, indent=2))
        return 1


# ============================================================================
# CLI Argument Parsing
# ============================================================================

def main():
    """CLI interface for method signature extraction."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Metadata resolver CLI for method signature extraction',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Extract method signature
  python metadata_resolver.py extract-signature --method SetChannelValue --header CommChannelNode.h

  # With compilation database
  python metadata_resolver.py extract-signature --method Foo --header Bar.h --compdb .
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Subcommand: extract-signature
    sig_parser = subparsers.add_parser(
        'extract-signature',
        help='Extract method signature from header file'
    )
    sig_parser.add_argument('--method', required=True,
                           help='Method name to extract')
    sig_parser.add_argument('--header', required=True, type=Path,
                           help='Path to C++ header file')
    sig_parser.add_argument('--compdb', type=Path,
                           help='Optional path to compilation database directory')

    args = parser.parse_args()

    # Dispatch to command handler
    if args.command == 'extract-signature':
        return cmd_extract_signature(args)
    else:
        parser.print_help()
        return 1


if __name__ == '__main__':
    sys.exit(main())
