# LLT Research Documents

This directory contains research reports and proof-of-concept code for the dante plugin LowLevelTests skills.

## Documents

### clangdb-test-discovery.md
**Date**: 2026-02-17
**Status**: Complete

Comprehensive research on using clang compilation database for LLT test function discovery and coverage mapping.

**Key Findings**:
- ✅ Use clang compilation database as PRIMARY approach (100% accuracy)
- ✅ Full Windows/Mac/Linux support verified
- ✅ Mangled name extraction enables precise coverage mapping
- ✅ Performance optimized with caching (1-3s → 10-30ms per file)

**Recommendation**: Implement clang parsing in llt-find with aggressive caching, fallback to regex on errors.

**Next Steps**:
1. Implement clang parsing in llt-find (Phase 1.1, 2 days)
2. Add caching layer (Phase 1.2, 1 day)
3. Update JSON schema for mangled names (Phase 1.3, 0.5 day)
4. Integrate with llt-coverage for coverage mapping (Phase 2, 3 days)

**Total Effort**: ~11.5 days for full implementation

## Proof-of-Concept Code

### test_clang_parsing.py
**Status**: Working prototype

Demonstrates:
- LibClang Python bindings usage
- Compilation database loading
- AST traversal for test functions
- Mangled name extraction

**Usage**:
```bash
# Test with example compilation database
python3 test_clang_parsing.py

# Parse real test file (requires compile_commands.json)
python3 test_clang_parsing.py path/to/test_file.cpp
```

## Quick Reference

### Generate Compilation Database

```bash
# In ushell
ushell .build misc clangdb FortniteEditor

# Direct UBT
.\Engine\Binaries\DotNET\UnrealBuildTool.exe FortniteEditor Win64 Development \
  -Mode=GenerateClangDatabase \
  -Exclude=".../Intermediate/;.../Platforms/;.../ThirdParty/"
```

### Install LibClang

```bash
pip3 install libclang
```

### Example: Parse Test File

```python
from clang.cindex import Index, CompilationDatabase

# Load compilation database
compdb = CompilationDatabase.fromDirectory("/path/to/FortniteGame")

# Get commands for test file
commands = compdb.getCompileCommands("path/to/Test.cpp")

# Parse with libclang
index = Index.create()
tu = index.parse("path/to/Test.cpp", args=compiler_args)

# Walk AST to find tests
for cursor in tu.cursor.walk_preorder():
    if cursor.kind == CursorKind.FUNCTION_DECL:
        mangled_name = cursor.mangled_name
        # Check for Catch2 test functions
```

## Performance Metrics

| Approach | Per File | 100 Files | Accuracy | Mangled Names |
|----------|----------|-----------|----------|---------------|
| **Regex** | 50-100ms | 5-10s | ~95% | ❌ No |
| **Clang (Cold)** | 1-3s | 100-300s | 100% | ✅ Yes |
| **Clang (Cached)** | 10-30ms | 1-3s | 100% | ✅ Yes |

**Recommendation**: Use clang with caching for best results.

## Related Documentation

- **LLT Skills SDD**: `../docs/design/llt-skills-sdd.md`
- **llt-find Skill**: `../skills/llt-find/`
- **llt-coverage Skill**: `../skills/llt-coverage/`

## Contact

For questions or feedback on this research:
- File issue in dante_plugin repo
- Contact: Claude Code (research author)
