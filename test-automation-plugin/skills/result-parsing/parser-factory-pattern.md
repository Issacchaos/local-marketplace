# Parser Factory Pattern

**Version**: 1.0.0
**Category**: Design Pattern
**Purpose**: Registry and selection mechanism for test framework parsers

## Overview

The Parser Factory Pattern provides a centralized registry of test framework parsers and intelligent selection logic to choose the appropriate parser based on framework name or output analysis. This allows the Execute Agent to parse test results without knowing which specific parser to use.

## Factory Architecture

```
TestParserFactory (Singleton)
├── Parser Registry: List[Type[BaseTestParser]]
├── Framework Hints: Dict[str, List[str]]  # Aliases
├── register_parser(parser_class) → None
├── get_parser(framework, output) → BaseTestParser
├── auto_detect_framework(command, output) → str
└── list_registered_parsers() → List[str]
```

## Factory Implementation

### Singleton Pattern

```python
# Global factory instance
_global_factory: Optional[TestParserFactory] = None

def get_parser_factory() -> TestParserFactory:
    """Get the global parser factory instance (singleton)."""
    global _global_factory

    if _global_factory is None:
        _global_factory = TestParserFactory()
        _auto_register_parsers(_global_factory)

    return _global_factory
```

**Why Singleton?**
- Single registry shared across all agents
- Parsers register once, available everywhere
- Avoids duplicate registrations
- Consistent parser selection

### Auto-Registration

```python
def _auto_register_parsers(factory: TestParserFactory) -> None:
    """Auto-import and register all available parsers."""
    import importlib
    import pkgutil
    from pathlib import Path

    # Get the parsers package directory
    parsers_dir = Path(__file__).parent

    # Find all parser modules (*_parser.py)
    for module_info in pkgutil.iter_modules([str(parsers_dir)]):
        module_name = module_info.name

        # Skip non-parser modules
        if module_name in ["__init__", "base_parser", "parser_factory"]:
            continue

        if module_name.endswith("_parser"):
            # Import the module
            module = importlib.import_module(f".{module_name}", package="parsers")

            # Find parser classes in the module
            for attr_name in dir(module):
                attr = getattr(module, attr_name)

                # Check if it's a parser class
                if (
                    isinstance(attr, type)
                    and attr.__name__.endswith('Parser')
                    and attr.__name__ != 'BaseTestParser'
                    and hasattr(attr, 'parse')
                    and hasattr(attr, 'can_parse')
                ):
                    # Verify it inherits from BaseTestParser
                    if 'BaseTestParser' in [base.__name__ for base in attr.__mro__]:
                        factory.register_parser(attr)
```

**Benefits**:
- No manual registration needed
- New parsers automatically available
- Follows convention-over-configuration
- Reduces boilerplate code

## Parser Selection Logic

### get_parser(framework, output)

Multi-stage selection process:

```
1. Exact Framework Match
   ├─ framework="pytest" → Try PytestParser.can_parse()
   └─ Match? Return parser

2. Framework Hint Match (Aliases)
   ├─ framework="py.test" → Hint maps to "pytest"
   └─ Try PytestParser.can_parse()

3. Output Pattern Analysis
   ├─ For each registered parser:
   │   └─ Call parser.can_parse("", output)
   │       └─ Returns True? Use that parser
   └─ First match wins

4. Generic Parser Fallback
   └─ No parser matched? Return GenericParser
```

**Implementation**:

```python
def get_parser(
    self, framework: Optional[str] = None, output: Optional[str] = None
) -> BaseTestParser:
    """Get appropriate parser for the given framework/output."""

    # Normalize framework name
    if framework:
        framework = framework.lower().strip()

    # Try each registered parser
    for parser_class in self._parsers:
        try:
            parser = parser_class()

            # Check if parser can handle this framework/output
            if parser.can_parse(framework or "", output or ""):
                logger.info(f"Selected parser: {parser_class.__name__}")
                return parser

        except Exception as e:
            logger.warning(f"Error checking parser {parser_class.__name__}: {e}")
            continue

    # Fallback to generic parser
    for parser_class in self._parsers:
        if "generic" in parser_class.__name__.lower():
            logger.warning(f"No specific parser found, using GenericParser")
            return parser_class()

    # Last resort: raise error
    raise ValueError(
        f"No parser available for framework='{framework}'. "
        f"Registered parsers: {[p.__name__ for p in self._parsers]}"
    )
```

## Framework Hints (Aliases)

Map alternative framework names to canonical names:

```python
self._framework_hints = {
    "pytest": ["pytest", "py.test"],                    # pytest aliases
    "jest": ["jest", "vitest"],                          # Jest-like frameworks
    "junit": ["junit", "maven", "gradle"],               # Java testing
    "gtest": ["gtest", "googletest"],                    # C++ testing
    "go": ["go test"],                                   # Go testing
    "cargo": ["cargo test", "cargo"],                    # Rust testing
    "dotnet": ["dotnet test", "xunit", "nunit", "mstest"], # .NET testing
    "rspec": ["rspec", "ruby"],                          # Ruby testing
    "unity": ["unity test", "unity"],                    # C testing
    "generic": ["generic"],                              # Fallback
}
```

**Usage**:
```python
# User types "py.test" → Factory maps to "pytest" → Selects PytestParser
parser = factory.get_parser(framework="py.test")
```

## Auto-Detection

### auto_detect_framework(command, output)

Detect framework from test command and output:

```python
def auto_detect_framework(self, command: str, output: str) -> Optional[str]:
    """Auto-detect framework from command and output."""
    command_lower = command.lower()
    output_lower = output.lower()

    # Step 1: Check command for framework keywords
    for framework, hints in self._framework_hints.items():
        for hint in hints:
            if hint in command_lower:
                return framework

    # Step 2: Check output for framework signatures
    framework_signatures = {
        "pytest": [
            r"=+\s*test session starts",
            r"pytest",
            r"\.py::\w+",
        ],
        "jest": [
            r"PASS\s+.*\.test\.(js|ts)",
            r"Test Suites:",
        ],
        "junit": [
            r'<testsuite.*?>',
            r"\[junit\]",
        ],
        "gtest": [
            r"\[={10}\].*Running.*tests",
            r"\[\s*RUN\s*\]",
        ],
        # ... (more frameworks)
    }

    for framework, patterns in framework_signatures.items():
        for pattern in patterns:
            if re.search(pattern, output_lower, re.MULTILINE):
                return framework

    return None  # Unable to detect
```

**Detection Strategy**:
1. **Command Analysis** (fastest): Look for framework keywords in command
   - `pytest tests/` → "pytest"
   - `npm test` → Check package.json or output
   - `dotnet test` → "dotnet"

2. **Output Signature** (reliable): Match framework-specific patterns
   - `===== test session starts =====` → "pytest"
   - `PASS tests/foo.test.js` → "jest"
   - `[==========] Running 10 tests` → "gtest"

3. **Confidence Scoring** (optional): Score multiple matches and select highest
   - Useful when multiple frameworks produce similar output

## Output Signatures

Framework-specific patterns for detection:

### pytest
```python
pytest_signatures = [
    r"=+\s*test session starts",     # Session header
    r"pytest",                         # Framework name
    r"\.py::\w+",                      # Test path format (tests/test_foo.py::test_name)
    r"collected \d+ items?",           # Collection message
]
```

### Jest/Vitest
```python
jest_signatures = [
    r"PASS\s+.*\.test\.(js|ts)",      # Pass marker
    r"FAIL\s+.*\.test\.(js|ts)",      # Fail marker
    r"Test Suites:",                   # Summary section
    r"Tests:\s+\d+",                   # Test count
]
```

### JUnit
```python
junit_signatures = [
    r'<testsuite.*?>',                 # XML format
    r'<testcase.*?>',                  # XML test case
    r"\[junit\]",                      # ANT output
    r"Tests run: \d+",                 # Summary line
]
```

### GTest (C++)
```python
gtest_signatures = [
    r"\[={10}\].*Running.*tests",     # Test run header
    r"\[\s*RUN\s*\]",                  # Individual test start
    r"\[\s*(PASSED|FAILED)\s*\]",     # Test result
]
```

### Go
```python
go_signatures = [
    r"===\s*RUN",                      # Test start
    r"---\s*(PASS|FAIL):",             # Test result
    r"FAIL\s+\S+\s+[\d.]+s",          # Package fail summary
]
```

### Cargo (Rust)
```python
cargo_signatures = [
    r"running \d+ tests?",             # Test run start
    r"test.*?\.\.\..*?(ok|FAILED|ignored)", # Test result
    r"test result:",                   # Summary section
]
```

## Usage Examples

### Basic Usage

```python
# Get factory singleton
factory = get_parser_factory()

# Get parser by framework name
parser = factory.get_parser(framework="pytest")
result = parser.parse(execution_result)

# Get parser by output analysis
parser = factory.get_parser(output="===== test session starts =====")
result = parser.parse(execution_result)
```

### With Auto-Detection

```python
factory = get_parser_factory()

# Auto-detect framework
framework = factory.auto_detect_framework(
    command="pytest tests/",
    output=test_output
)

# Get appropriate parser
parser = factory.get_parser(framework=framework, output=test_output)
result = parser.parse(execution_result)
```

### Register Custom Parser

```python
class MyCustomParser(BaseTestParser):
    def parse(self, result):
        # Custom parsing logic
        pass

    def extract_failures(self, output):
        pass

    def extract_coverage(self, output):
        pass

    def can_parse(self, framework, output):
        return framework == "mycustom"

# Register with factory
factory = get_parser_factory()
factory.register_parser(MyCustomParser)

# Now available for use
parser = factory.get_parser(framework="mycustom")
```

## Error Handling

### No Parser Found

```python
try:
    parser = factory.get_parser(framework="unknown", output="")
except ValueError as e:
    # No parser available
    logger.error(f"No parser found: {e}")
    # Use GenericParser as fallback
```

### Parser Registration Error

```python
try:
    factory.register_parser(NotAParser)
except TypeError as e:
    # Must inherit from BaseTestParser
    logger.error(f"Invalid parser: {e}")
```

### Parser Selection Error

```python
try:
    parser = factory.get_parser(framework=None, output=None)
except ValueError:
    # No framework or output provided
    # Use default parser
    parser = factory.get_parser(framework="generic")
```

## Extension Points

### Adding New Framework Support

1. **Create Parser Class**:
   ```python
   # parsers/myframework_parser.py
   class MyFrameworkParser(BaseTestParser):
       def can_parse(self, framework, output):
           return framework == "myframework" or "MyFramework" in output

       def parse(self, result):
           # Parse logic
           pass
   ```

2. **Auto-Registration**:
   - Place file in `parsers/` directory
   - Name file `*_parser.py`
   - Factory auto-discovers and registers

3. **Add Framework Hints** (optional):
   ```python
   factory._framework_hints["myframework"] = ["myframework", "mf", "my-framework"]
   ```

4. **Add Output Signatures** (optional):
   ```python
   # In auto_detect_framework()
   framework_signatures["myframework"] = [
       r"MyFramework Test Runner",
       r"MF>",
   ]
   ```

### Custom Selection Logic

Override `get_parser()` for custom logic:

```python
class CustomParserFactory(TestParserFactory):
    def get_parser(self, framework, output):
        # Custom selection logic
        if self.is_ci_environment():
            return CIOptimizedParser()
        else:
            return super().get_parser(framework, output)
```

## Performance Considerations

### Parser Registration

- **Lazy Loading**: Parsers imported only when first requested
- **One-Time Cost**: Registration happens once at startup
- **Memory**: All parsers kept in memory (negligible overhead)

### Parser Selection

- **Fast Path**: Framework name match is O(1)
- **Slow Path**: Output analysis is O(n×m) where n=parsers, m=patterns
- **Caching**: Consider caching parser selection for repeated calls

### Optimization Tips

```python
# Cache parser selection
_parser_cache = {}

def get_cached_parser(framework, output_sample):
    cache_key = (framework, output_sample[:100])  # Use first 100 chars
    if cache_key not in _parser_cache:
        _parser_cache[cache_key] = factory.get_parser(framework, output_sample)
    return _parser_cache[cache_key]
```

## Testing

### Test Auto-Registration

```python
def test_auto_registration():
    factory = get_parser_factory()
    parsers = factory.list_registered_parsers()

    assert "PytestParser" in parsers
    assert "JestParser" in parsers
    assert "GenericParser" in parsers
```

### Test Parser Selection

```python
def test_get_parser_by_framework():
    factory = get_parser_factory()
    parser = factory.get_parser(framework="pytest")
    assert isinstance(parser, PytestParser)

def test_get_parser_by_output():
    factory = get_parser_factory()
    output = "===== test session starts ====="
    parser = factory.get_parser(output=output)
    assert isinstance(parser, PytestParser)
```

### Test Auto-Detection

```python
def test_auto_detect_from_command():
    factory = get_parser_factory()
    framework = factory.auto_detect_framework("pytest tests/", "")
    assert framework == "pytest"

def test_auto_detect_from_output():
    factory = get_parser_factory()
    output = "PASS tests/foo.test.js"
    framework = factory.auto_detect_framework("npm test", output)
    assert framework == "jest"
```

## References

- Dante's ParserFactory: `dante/src/dante/runner/test_execution/parsers/parser_factory.py`
- Factory Pattern: https://refactoring.guru/design-patterns/factory-method
- Singleton Pattern: https://refactoring.guru/design-patterns/singleton
- Plugin Architecture: https://packaging.python.org/guides/creating-and-discovering-plugins/

---

**Last Updated**: 2025-12-05
**Status**: Factory pattern documented
**Usage**: Centralized parser registry and selection
