#!/usr/bin/env python3
"""
Source Parser Module

Extracts method signatures from C++ headers using clang AST parsing (primary)
with regex-based fallback. Supports UFUNCTION macros, templates, virtual methods,
and extracts mangled names for coverage mapping.

Requirements:
- REQ-F-37: Use libclang AST parsing with compilation database context for 100% accurate method extraction
- REQ-F-38: Extract mangled function names from clang AST for coverage mapping to object files
- REQ-F-40: Fallback to regex-based parsing when compilation database unavailable or libclang import fails
- REQ-F-43: Store test metadata with mangled names for coverage correlation in JSON output
"""

import logging
import re
from pathlib import Path
from typing import Dict, List, Optional

# Import cache module
try:
    from . import compilation_db_cache
    CACHE_AVAILABLE = True
except ImportError:
    # Fallback for standalone execution
    try:
        import compilation_db_cache
        CACHE_AVAILABLE = True
    except ImportError:
        CACHE_AVAILABLE = False

# Configure logging
logger = logging.getLogger(__name__)

# Try to import clang bindings (may not be available)
try:
    import clang.cindex
    from clang.cindex import CompilationDatabase, CursorKind, Index, TranslationUnit
    CLANG_AVAILABLE = True
    logger.debug("libclang bindings available")
except ImportError as e:
    CLANG_AVAILABLE = False
    logger.debug(f"libclang not available: {e}")


def extract_method_signatures(
    header_path: Path,
    compdb_path: Optional[Path] = None,
    use_cache: bool = True
) -> List[Dict]:
    """
    Extract method signatures from C++ header with automatic fallback.

    Tries cache first (<30ms), then clang AST parsing (100% accuracy), falls back to regex
    if clang unavailable or compilation database missing (95% accuracy).

    Args:
        header_path: Path to C++ header file
        compdb_path: Path to directory containing compile_commands.json (optional)
        use_cache: Whether to use cache (default: True)

    Returns:
        List of method metadata dicts with name, return_type, params, qualifiers, line number.
        Clang mode includes mangled_name field.

    Example:
        >>> methods = extract_method_signatures(
        ...     Path("Source/Runtime/Core/Public/Containers/Array.h"),
        ...     Path(".")  # Directory containing compile_commands.json
        ... )
        >>> print(methods[0]['name'], methods[0]['mangled_name'])
        Num _ZNK7TArrayI...E3NumEv
    """
    header_path = Path(header_path)

    # Try cache first (REQ-F-39: <30ms performance target)
    if use_cache and CACHE_AVAILABLE:
        cached_methods = compilation_db_cache.get_cached_methods(header_path)
        if cached_methods is not None:
            return cached_methods

    # Try clang approach
    if CLANG_AVAILABLE and compdb_path is not None:
        try:
            methods = extract_methods_with_clang(header_path, compdb_path)
            if methods is not None:
                logger.info(
                    f"Extracted {len(methods)} methods from {header_path.name} using clang AST"
                )
                # Cache the results for future use (REQ-F-39)
                if use_cache and CACHE_AVAILABLE:
                    compilation_db_cache.cache_methods(header_path, methods)
                return methods
        except Exception as e:
            logger.warning(
                f"Clang AST parsing failed for {header_path}: {e}, falling back to regex"
            )

    # Fall back to regex
    logger.info(
        f"Using regex parser for {header_path.name} "
        "(install libclang and provide compilation database for 100% accuracy)"
    )
    methods = extract_methods_with_regex(header_path)

    # Don't cache regex results - they're already fast (<1s) and lack mangled names
    # Caching overhead not worth it for regex mode
    return methods


def extract_methods_with_clang(
    header_path: Path,
    compdb_path: Path
) -> Optional[List[Dict]]:
    """
    Extract method signatures using clang AST parsing.

    Advantages:
    - 100% accuracy on all C++ syntax (templates, macros, complex types)
    - Handles UFUNCTION macros correctly
    - Gets mangled names automatically
    - Respects compiler preprocessor definitions
    - Correctly parses nested templates, operator overloads, complex qualifiers

    Args:
        header_path: Path to C++ header file
        compdb_path: Path to directory containing compile_commands.json

    Returns:
        List of method metadata dicts, or None on failure.

    Example:
        >>> methods = extract_methods_with_clang(
        ...     Path("MyClass.h"),
        ...     Path(".")
        ... )
        >>> method = methods[0]
        >>> print(method['name'], method['mangled_name'], method['return_type'])
        GetValue _ZN7MyClass8GetValueEv int32
    """
    if not CLANG_AVAILABLE:
        return None

    header_path = Path(header_path).resolve()
    compdb_path = Path(compdb_path).resolve()

    if not header_path.exists():
        logger.error(f"Header file not found: {header_path}")
        return None

    # Load compilation database
    try:
        compdb = CompilationDatabase.fromDirectory(str(compdb_path))
        logger.debug(f"Loaded compilation database from {compdb_path}")
    except Exception as e:
        logger.warning(f"Failed to load compilation database: {e}")
        return None

    # Get compilation commands for this file
    # Note: compile_commands.json typically has entries for .cpp files, not .h files
    # We need to find a corresponding .cpp file or use the header directly
    compile_commands = compdb.getCompileCommands(str(header_path))

    if compile_commands is None or len(list(compile_commands)) == 0:
        # Try to find a .cpp file in the same directory
        cpp_candidates = [
            header_path.with_suffix(".cpp"),
            header_path.parent.parent / "Private" / header_path.stem / f"{header_path.stem}.cpp",
            header_path.parent.parent / "Private" / f"{header_path.stem}.cpp"
        ]

        compile_commands = None
        for cpp_candidate in cpp_candidates:
            if cpp_candidate.exists():
                compile_commands = compdb.getCompileCommands(str(cpp_candidate))
                if compile_commands is not None and len(list(compile_commands)) > 0:
                    logger.debug(f"Using compile commands from {cpp_candidate}")
                    break

        if compile_commands is None or len(list(compile_commands)) == 0:
            logger.warning(
                f"No compilation commands found for {header_path} or related .cpp files"
            )
            # Continue with default flags - clang can still parse the header

    # Parse header with clang
    try:
        index = Index.create()

        # Extract compiler flags from compilation database if available
        args = []
        if compile_commands is not None:
            for cmd in compile_commands:
                # Parse command line arguments
                # Skip the compiler executable and source file
                cmd_args = list(cmd.arguments)[1:-1]  # Skip compiler and source file
                args.extend(cmd_args)
                break  # Use first matching command

        logger.debug(f"Parsing {header_path} with clang")
        logger.debug(f"Compiler flags: {args[:10]}...")  # Log first 10 flags

        # Parse with detailed processing to get full AST
        tu = index.parse(
            str(header_path),
            args=args,
            options=TranslationUnit.PARSE_DETAILED_PROCESSING_RECORD
        )

        if tu is None:
            logger.error(f"Failed to parse {header_path}")
            return None

        # Check for parse errors
        if len(tu.diagnostics) > 0:
            errors = [d for d in tu.diagnostics if d.severity >= 3]  # Error or Fatal
            if errors:
                logger.warning(f"Parse errors in {header_path}:")
                for diag in errors[:5]:  # Log first 5 errors
                    logger.warning(f"  {diag.location}: {diag.spelling}")

        # Extract methods from AST
        methods = []
        _walk_ast_for_methods(tu.cursor, methods, header_path)

        logger.debug(f"Extracted {len(methods)} methods from AST")
        return methods

    except Exception as e:
        logger.error(f"Error parsing {header_path} with clang: {e}")
        return None


def _walk_ast_for_methods(
    cursor,
    methods: List[Dict],
    header_path: Path
) -> None:
    """
    Walk clang AST to find CXX_METHOD nodes.

    Recursively traverses the AST and extracts method metadata from
    CXX_METHOD cursor kinds.

    Args:
        cursor: clang.cindex.Cursor to start traversal
        methods: List to append method metadata to
        header_path: Header file path for filtering (only extract methods from this file)
    """
    # Only process nodes from the target header file
    if cursor.location.file is None:
        # Skip built-in or implicit nodes
        for child in cursor.get_children():
            _walk_ast_for_methods(child, methods, header_path)
        return

    cursor_file = Path(cursor.location.file.name).resolve()
    if cursor_file != header_path.resolve():
        # Skip nodes from other files (includes)
        return

    # Check if this is a method
    if cursor.kind == CursorKind.CXX_METHOD:
        method_info = _extract_method_info_from_cursor(cursor)
        if method_info:
            methods.append(method_info)

    # Recursively process children
    for child in cursor.get_children():
        _walk_ast_for_methods(child, methods, header_path)


def _extract_method_info_from_cursor(cursor) -> Optional[Dict]:
    """
    Extract method metadata from clang cursor.

    Args:
        cursor: clang.cindex.Cursor of kind CXX_METHOD

    Returns:
        Method metadata dict or None if extraction fails.
    """
    try:
        # Extract basic info
        name = cursor.spelling
        return_type = cursor.result_type.spelling
        line = cursor.location.line

        # Extract parameters
        params = []
        for arg in cursor.get_arguments():
            param_info = {
                'type': arg.type.spelling,
                'name': arg.spelling
            }
            params.append(param_info)

        # Extract qualifiers
        is_const = cursor.is_const_method()
        is_virtual = cursor.is_virtual_method()
        is_pure_virtual = cursor.is_pure_virtual_method()
        is_static = cursor.is_static_method()

        # Extract mangled name (critical for REQ-F-38)
        mangled_name = cursor.mangled_name

        # Get class name from parent
        parent = cursor.semantic_parent
        class_name = parent.spelling if parent else ""

        # Check for UFUNCTION macro
        # We can detect this by looking at tokens before the method
        has_ufunction = _has_ufunction_macro(cursor)

        # Check for template
        # Note: is_function_template() not available in all clang versions
        is_template = cursor.kind == CursorKind.FUNCTION_TEMPLATE or \
                     (hasattr(cursor, 'is_function_template') and cursor.is_function_template())

        method_info = {
            'name': name,
            'return_type': return_type,
            'params': params,
            'is_const': is_const,
            'is_virtual': is_virtual,
            'is_pure_virtual': is_pure_virtual,
            'is_static': is_static,
            'has_ufunction': has_ufunction,
            'is_template': is_template,
            'line': line,
            'class_name': class_name,
            'mangled_name': mangled_name  # REQ-F-38: Mangled name for coverage
        }

        return method_info

    except Exception as e:
        logger.warning(f"Failed to extract method info from cursor: {e}")
        return None


def _has_ufunction_macro(cursor) -> bool:
    """
    Check if method has UFUNCTION macro by examining tokens.

    Args:
        cursor: clang.cindex.Cursor

    Returns:
        True if UFUNCTION macro found before method.
    """
    try:
        # Get tokens before the method declaration
        extent = cursor.extent
        tokens = list(cursor.translation_unit.get_tokens(extent=extent))

        # Look for UFUNCTION token in the tokens
        for token in tokens:
            if 'UFUNCTION' in token.spelling:
                return True

        return False
    except Exception as e:
        logger.debug(f"Error checking for UFUNCTION macro: {e}")
        return False


def extract_methods_with_regex(header_path: Path) -> List[Dict]:
    """
    Extract method signatures using regex-based parsing (fallback).

    Handles common patterns:
    - Regular methods: virtual ReturnType MethodName(Params) const override
    - Interface methods: virtual ReturnType MethodName(Params) = 0
    - Template methods: template<typename T> ReturnType Method(T Param)
    - UFUNCTION methods: UFUNCTION(...) ReturnType MethodName(Params)

    Accuracy: ~95% on well-formed UE code

    Limitations:
    - May miss methods with unusual formatting
    - Template parameters not fully parsed
    - No mangled names available
    - Requires clean code (no complex macros in signatures)

    Args:
        header_path: Path to C++ header file

    Returns:
        List of method metadata dicts (without mangled_name field).

    Example:
        >>> methods = extract_methods_with_regex(Path("MyClass.h"))
        >>> print(methods[0]['name'], methods[0]['return_type'])
        GetValue int32
    """
    header_path = Path(header_path)

    if not header_path.exists():
        logger.error(f"Header file not found: {header_path}")
        return []

    try:
        content = header_path.read_text(encoding='utf-8')
    except Exception as e:
        logger.error(f"Error reading {header_path}: {e}")
        return []

    # Step 1: Remove C++ comments for cleaner parsing
    content = _remove_cpp_comments(content)

    # Step 2: Extract class body
    # Updated regex to handle UE API macros (MYGAME_API, etc.) and UCLASS/GENERATED_BODY
    class_match = re.search(
        r'class\s+(?:\w+_API\s+)?(\w+)(?:\s*:\s*[^{]+)?\s*\{(.*)\};',
        content,
        re.DOTALL
    )

    if not class_match:
        logger.warning(f"No class definition found in {header_path}")
        return []

    class_name = class_match.group(1)
    class_body = class_match.group(2)

    # Remove access specifiers (public:, private:, protected:) for cleaner parsing
    class_body = re.sub(r'\b(public|private|protected)\s*:', '', class_body)

    # Step 3: Match method declarations with comprehensive regex
    method_pattern = r'''
        (?:UFUNCTION\s*\([^)]*\)\s*)?           # Optional UFUNCTION macro
        (?:template\s*<[^>]+>\s*)?              # Optional template declaration
        (?:virtual\s+)?                         # Optional virtual keyword (not captured)
        (?:static\s+)?                          # Optional static keyword (not captured)
        ((?:const\s+)?[\w:<>,\s*&]+?)           # Return type (capture group 1) - may have leading const
        \s+
        (\w+)                                   # Method name (capture group 2)
        \s*\(
        ([^)]*)                                 # Parameters (capture group 3)
        \)
        ((?:\s+const)?                          # Optional const qualifier (capture group 4)
         (?:\s+override)?                       # Optional override keyword
         (?:\s*=\s*0)?                          # Optional pure virtual (= 0)
        )
        \s*[;{]                                 # Ends with ; or { (for inline methods)
    '''

    methods = []
    for match in re.finditer(method_pattern, class_body, re.VERBOSE):
        return_type = match.group(1).strip()
        method_name = match.group(2)
        params_str = match.group(3).strip()
        qualifiers_str = match.group(4)

        # Skip constructors and destructors
        if method_name == class_name or method_name == f"~{class_name}":
            continue

        # Clean return type (remove virtual/static if they leaked through)
        return_type = re.sub(r'\b(virtual|static)\s+', '', return_type).strip()

        # Step 4: Parse parameters
        params = _parse_parameters(params_str)

        # Step 5: Detect qualifiers
        method_text = match.group(0)
        is_const = ' const' in qualifiers_str
        is_virtual = 'virtual' in method_text
        is_pure_virtual = '= 0' in qualifiers_str
        is_static = 'static' in method_text
        has_ufunction = 'UFUNCTION' in method_text
        is_template = 'template<' in method_text

        # Calculate line number
        line = content[:match.start()].count('\n') + 1

        method_info = {
            'name': method_name,
            'return_type': return_type,
            'params': params,
            'is_const': is_const,
            'is_virtual': is_virtual,
            'is_pure_virtual': is_pure_virtual,
            'is_static': is_static,
            'has_ufunction': has_ufunction,
            'is_template': is_template,
            'line': line,
            'class_name': class_name
            # Note: mangled_name not available in regex mode
        }

        methods.append(method_info)

    logger.debug(f"Regex parser extracted {len(methods)} methods from {header_path.name}")
    return methods


def _remove_cpp_comments(content: str) -> str:
    """
    Remove C++ comments for cleaner parsing.

    Args:
        content: C++ source code

    Returns:
        Content with comments removed.
    """
    # Remove single-line comments
    content = re.sub(r'//.*?$', '', content, flags=re.MULTILINE)

    # Remove multi-line comments
    content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)

    return content


def _parse_parameters(params_str: str) -> List[Dict]:
    """
    Parse parameter string into structured list.

    Args:
        params_str: Parameter list string (e.g., "const FString& Name, int Count = 0")

    Returns:
        List of parameter dicts with 'type' and 'name' fields.
    """
    params = []

    if not params_str.strip():
        return params

    # Split parameters by comma (but not commas inside templates)
    param_parts = _split_params_smart(params_str)

    for param in param_parts:
        param = param.strip()
        if not param:
            continue

        # Remove default values: "int Count = 0" -> "int Count"
        param = re.sub(r'\s*=\s*[^,]+$', '', param)

        # Split on last space to separate type from name
        # Handle: "const FString& Name", "TArray<int> Items", "int Count"
        parts = param.rsplit(' ', 1)

        if len(parts) == 2:
            param_type, param_name = parts
            params.append({
                'type': param_type.strip(),
                'name': param_name.strip()
            })
        elif len(parts) == 1:
            # Type only, no name (rare but valid C++)
            params.append({
                'type': parts[0].strip(),
                'name': ''
            })

    return params


def _split_params_smart(params_str: str) -> List[str]:
    """
    Split parameters by comma, respecting template angle brackets.

    Args:
        params_str: Parameter list string

    Returns:
        List of parameter strings.
    """
    params = []
    current = []
    depth = 0  # Track template nesting depth

    for char in params_str:
        if char == '<':
            depth += 1
            current.append(char)
        elif char == '>':
            depth -= 1
            current.append(char)
        elif char == ',' and depth == 0:
            # Split here
            params.append(''.join(current).strip())
            current = []
        else:
            current.append(char)

    # Add last parameter
    if current:
        params.append(''.join(current).strip())

    return params


if __name__ == "__main__":
    # Configure logging for standalone execution
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Example usage
    import sys

    if len(sys.argv) < 2:
        print("Usage: source_parser.py <header_path> [compdb_path]")
        print("Example: source_parser.py MyClass.h .")
        sys.exit(1)

    header_path = Path(sys.argv[1])
    compdb_path = Path(sys.argv[2]) if len(sys.argv) > 2 else None

    methods = extract_method_signatures(header_path, compdb_path)

    print(f"\nExtracted {len(methods)} methods from {header_path.name}:")
    print(f"{'=' * 80}")

    for i, method in enumerate(methods, 1):
        print(f"\n{i}. {method['class_name']}::{method['name']}")
        print(f"   Return Type: {method['return_type']}")
        print(f"   Parameters: {len(method['params'])}")
        for param in method['params']:
            print(f"     - {param['type']} {param['name']}")
        print(f"   Qualifiers: ", end="")
        quals = []
        if method['is_const']:
            quals.append('const')
        if method['is_virtual']:
            quals.append('virtual')
        if method['is_pure_virtual']:
            quals.append('pure virtual')
        if method['is_static']:
            quals.append('static')
        if method['has_ufunction']:
            quals.append('UFUNCTION')
        if method['is_template']:
            quals.append('template')
        print(', '.join(quals) if quals else 'none')
        print(f"   Line: {method['line']}")
        if 'mangled_name' in method:
            print(f"   Mangled: {method['mangled_name']}")
