---
name: project-detection
description: Detect project root directory from any path within a project, with validation to prevent writing to incorrect locations. Use when resolving the correct project root for test file placement and build system interaction.
user-invocable: false
---

# Project Root Detection Skill

**Version**: 1.0.0
**Category**: Infrastructure
**Languages**: Python, JavaScript, TypeScript, Java, C#, Go, C++
**Purpose**: Detect project root directory from any path within a project, with validation to prevent writing to incorrect locations

---

## Overview

The Project Root Detection Skill identifies the root directory of a project by walking up the directory tree and finding language-specific project marker files. This is critical for:
1. Placing test files in correct locations relative to project root
2. Saving state files in project's `.claude/` directory (not plugin directory)
3. Validating paths are within project boundaries
4. Supporting cross-language workflows

**Key Principle**: Never guess the project root. Either find a definitive marker or return an error with actionable guidance.

---

## Detection Algorithm

### Step 1: Normalize Input Path

```python
def normalize_path(target_path: str) -> str:
    """
    Normalize path to absolute form with security validation.

    Args:
        target_path: File or directory path (may be relative)

    Returns:
        Absolute path

    Raises:
        ValueError: If path contains invalid or suspicious patterns
    """
    # Input validation: Reject obviously malicious patterns
    if not target_path or not isinstance(target_path, str):
        raise ValueError("Invalid path: must be a non-empty string")

    # Reject null bytes (path traversal attack vector)
    if '\x00' in target_path:
        raise ValueError("Invalid path: contains null bytes")

    # Convert to absolute path (resolves relative paths safely)
    abs_path = os.path.abspath(target_path)

    # If it's a file, use its directory
    if os.path.isfile(abs_path):
        abs_path = os.path.dirname(abs_path)

    # Normalize path separators (Windows compatibility)
    abs_path = os.path.normpath(abs_path)

    # Resolve any remaining symlinks to get real path
    # This prevents symlink-based path traversal
    try:
        abs_path = os.path.realpath(abs_path)
    except (OSError, ValueError) as e:
        raise ValueError(f"Invalid path: cannot resolve to real path: {e}")

    return abs_path
```

---

### Step 2: Define Project Markers (Cross-Language)

Project markers are files/directories that definitively indicate a project root:

```python
PROJECT_MARKERS = {
    # Python
    'python': {
        'markers': [
            'pyproject.toml',     # Modern Python (PEP 518)
            'setup.py',           # Traditional Python packaging
            'setup.cfg',          # setuptools config
            'requirements.txt',   # pip dependencies
            'Pipfile',            # pipenv
            'poetry.lock',        # poetry
            'pytest.ini',         # pytest config
            'tox.ini',            # tox testing
        ],
        'priority': 10  # Highest priority if multiple markers found
    },

    # JavaScript/TypeScript
    'javascript': {
        'markers': [
            'package.json',       # npm/yarn package
            'package-lock.json',  # npm lock
            'yarn.lock',          # yarn lock
            'pnpm-lock.yaml',     # pnpm lock
        ],
        'priority': 10
    },

    'typescript': {
        'markers': [
            'tsconfig.json',      # TypeScript config
            'package.json',       # npm package (TS projects have this too)
        ],
        'priority': 10
    },

    # Java
    'java': {
        'markers': [
            'pom.xml',            # Maven project
            'build.gradle',       # Gradle project
            'build.gradle.kts',   # Gradle Kotlin DSL
            'settings.gradle',    # Gradle settings
            'gradlew',            # Gradle wrapper
        ],
        'priority': 10
    },

    # C#
    'csharp': {
        'markers': [
            '*.sln',              # Visual Studio solution
            '*.csproj',           # C# project file
            'Directory.Build.props',  # MSBuild directory props
            'global.json',        # .NET global config
        ],
        'priority': 10
    },

    # Go
    'go': {
        'markers': [
            'go.work',            # Go workspace (Go 1.18+, multi-module)
            'go.mod',             # Go modules (Go 1.11+)
            'go.sum',             # Go dependencies checksum
        ],
        'priority': 10
    },

    # C++
    'cpp': {
        'markers': [
            'CMakeLists.txt',     # CMake build
            'Makefile',           # Make build
            'conanfile.txt',      # Conan package manager
            'conanfile.py',       # Conan package manager (Python)
            'vcpkg.json',         # vcpkg manifest
            'meson.build',        # Meson build
        ],
        'priority': 8  # Lower priority (Makefile can be anywhere)
    },

    # Version Control (Fallback)
    'vcs': {
        'markers': [
            '.git',               # Git repository
            '.hg',                # Mercurial
            '.svn',               # Subversion
        ],
        'priority': 5  # Lower priority - use as fallback
    }
}

# Flattened list for detection (all markers across all languages)
ALL_MARKERS = []
for lang_markers in PROJECT_MARKERS.values():
    ALL_MARKERS.extend(lang_markers['markers'])
```

---

### Step 3: Walk Up Directory Tree

```python
def find_project_root(target_path: str, plugin_repo_path: str = None) -> dict:
    """
    Walk up directory tree to find project root.

    Args:
        target_path: Starting path (file or directory)
        plugin_repo_path: Path to plugin repository (for validation)

    Returns:
        dict with:
        {
            'project_root': str | None,       # Absolute path to project root
            'marker_file': str | None,        # Which marker file was found
            'marker_language': str | None,    # Language associated with marker
            'confidence': str,                # 'high', 'medium', 'low'
            'error': str | None,              # Error message if detection failed
            'suggestion': str | None          # Actionable suggestion for user
        }
    """
    # Normalize starting path
    current = normalize_path(target_path)

    # Track what we've seen
    found_markers = []

    # Walk up directory tree (max 10 levels to prevent infinite loops)
    MAX_DEPTH = 10
    for depth in range(MAX_DEPTH):
        # Check for project markers in current directory
        for marker in ALL_MARKERS:
            if marker.startswith('*'):
                # Wildcard pattern (e.g., *.csproj)
                pattern = os.path.join(current, marker)
                matches = glob.glob(pattern)
                if matches:
                    marker_file = matches[0]  # Use first match
                    marker_name = os.path.basename(marker_file)
                    found_markers.append({
                        'root': current,
                        'marker': marker_name,
                        'full_path': marker_file
                    })
            else:
                # Exact file/directory match
                marker_path = os.path.join(current, marker)
                if os.path.exists(marker_path):
                    found_markers.append({
                        'root': current,
                        'marker': marker,
                        'full_path': marker_path
                    })

        # If we found markers at this level, evaluate them
        if found_markers:
            # Select best marker based on priority
            best_marker = select_best_marker(found_markers)

            # Validate the project root
            validation = validate_project_root(
                best_marker['root'],
                plugin_repo_path
            )

            if validation['valid']:
                return {
                    'project_root': best_marker['root'],
                    'marker_file': best_marker['marker'],
                    'marker_language': detect_language_from_marker(best_marker['marker']),
                    'confidence': 'high',
                    'error': None,
                    'suggestion': None
                }
            else:
                # Found marker but validation failed
                return {
                    'project_root': None,
                    'marker_file': best_marker['marker'],
                    'marker_language': detect_language_from_marker(best_marker['marker']),
                    'confidence': 'low',
                    'error': validation['error'],
                    'suggestion': validation['suggestion']
                }

        # Move up one directory
        parent = os.path.dirname(current)

        # Check if we've reached filesystem root
        if parent == current:
            # Can't go further up
            break

        current = parent

    # No project root found after walking up MAX_DEPTH levels
    return {
        'project_root': None,
        'marker_file': None,
        'marker_language': None,
        'confidence': 'none',
        'error': f"Cannot determine project root from path: {target_path}",
        'suggestion': (
            "Make sure you're inside a project directory with one of these files:\\n"
            "  Python: pyproject.toml, setup.py, requirements.txt\\n"
            "  JavaScript/TypeScript: package.json, tsconfig.json\\n"
            "  Java: pom.xml, build.gradle\\n"
            "  C#: *.sln, *.csproj\\n"
            "  Go: go.mod\\n"
            "  C++: CMakeLists.txt, Makefile\\n"
            "  Or: Initialize a git repository (.git directory)"
        )
    }


def select_best_marker(found_markers: list) -> dict:
    """
    Select the most appropriate project marker from candidates.

    Priority:
    1. Language-specific config (highest priority)
    2. Version control markers (lowest priority)

    Args:
        found_markers: List of {root, marker, full_path} dicts

    Returns:
        Best marker dict
    """
    # If only one marker, return it
    if len(found_markers) == 1:
        return found_markers[0]

    # Score each marker
    scored = []
    for marker_info in found_markers:
        marker_name = marker_info['marker']
        priority = get_marker_priority(marker_name)
        scored.append((priority, marker_info))

    # Sort by priority (highest first)
    scored.sort(key=lambda x: x[0], reverse=True)

    return scored[0][1]


def get_marker_priority(marker_name: str) -> int:
    """Get priority score for a marker file."""
    for lang, lang_info in PROJECT_MARKERS.items():
        if marker_name in lang_info['markers'] or any(
            marker_name.endswith(m[1:]) for m in lang_info['markers'] if m.startswith('*')
        ):
            return lang_info['priority']
    return 0


def detect_language_from_marker(marker_name: str) -> str | None:
    """Detect language from marker file name."""
    marker_to_lang = {
        'pyproject.toml': 'python',
        'setup.py': 'python',
        'requirements.txt': 'python',
        'package.json': 'javascript',  # Could be TS too
        'tsconfig.json': 'typescript',
        'pom.xml': 'java',
        'build.gradle': 'java',
        'go.mod': 'go',
        'CMakeLists.txt': 'cpp',
        'Makefile': 'cpp',
    }

    # Check exact match
    if marker_name in marker_to_lang:
        return marker_to_lang[marker_name]

    # Check extensions for wildcards
    if marker_name.endswith('.sln') or marker_name.endswith('.csproj'):
        return 'csharp'

    return None
```

---

### Step 4: Validate Project Root

**Critical**: Prevent writing to incorrect locations (especially plugin repository).

```python
def validate_project_root(
    project_root: str,
    plugin_repo_path: str = None
) -> dict:
    """
    Validate that detected project root is safe to use.

    Validation Rules:
    1. Project root must exist and be a directory
    2. Project root must be writable
    3. Project root must NOT be the plugin repository
    4. Project root must NOT be a parent directory of plugin repository
    5. Project root must NOT be system-critical directories

    Args:
        project_root: Detected project root path
        plugin_repo_path: Path to dante_plugin repository

    Returns:
        dict with:
        {
            'valid': bool,
            'error': str | None,
            'suggestion': str | None
        }
    """
    # Normalize and resolve the path securely
    try:
        project_root_abs = os.path.realpath(os.path.abspath(project_root))
    except (OSError, ValueError) as e:
        return {
            'valid': False,
            'error': f"Invalid project root path: {e}",
            'suggestion': "Ensure the path is valid and accessible."
        }

    # Rule 0: Prevent writes to system-critical directories (security check)
    # These directories should never be treated as project roots
    FORBIDDEN_ROOTS = [
        '/', '/bin', '/boot', '/dev', '/etc', '/lib', '/lib64',
        '/proc', '/root', '/sbin', '/sys', '/usr', '/var',
        'C:\\', 'C:\\Windows', 'C:\\Program Files', 'C:\\Program Files (x86)',
        '/System', '/Library', '/Applications'  # macOS
    ]

    for forbidden in FORBIDDEN_ROOTS:
        forbidden_abs = os.path.abspath(forbidden)
        if project_root_abs == forbidden_abs or project_root_abs.startswith(forbidden_abs + os.sep):
            return {
                'valid': False,
                'error': f"Cannot use system directory as project root: {project_root_abs}",
                'suggestion': (
                    "Project root cannot be a system directory for security reasons.\n"
                    "Navigate to your project directory (e.g., ~/projects/myapp) and try again."
                )
            }

    # Rule 1: Must exist and be a directory
    if not os.path.exists(project_root_abs):
        return {
            'valid': False,
            'error': f"Project root does not exist: {project_root_abs}",
            'suggestion': "Check the path and try again."
        }

    if not os.path.isdir(project_root_abs):
        return {
            'valid': False,
            'error': f"Project root is not a directory: {project_root_abs}",
            'suggestion': "Specify a directory path, not a file."
        }

    # Rule 2: Must be writable (we need to create tests/ and .claude/)
    if not os.access(project_root_abs, os.W_OK):
        return {
            'valid': False,
            'error': f"Project root is not writable: {project_root_abs}",
            'suggestion': "Check directory permissions."
        }

    # Rule 3 & 4: Must NOT be plugin repository
    if plugin_repo_path:
        plugin_repo_abs = os.path.abspath(plugin_repo_path)

        # Check if project root IS the plugin repo
        if project_root_abs == plugin_repo_abs:
            return {
                'valid': False,
                'error': (
                    "Cannot use plugin repository as target project.\\n"
                    f"Plugin repo: {plugin_repo_abs}\\n"
                    f"Detected project root: {project_root_abs}"
                ),
                'suggestion': (
                    "Navigate to your actual project directory and run the command again.\\n"
                    "Example: cd /path/to/your/project && /test-loop src/"
                )
            }

        # Check if project root is inside plugin repo
        if project_root_abs.startswith(plugin_repo_abs + os.sep):
            return {
                'valid': False,
                'error': (
                    "Detected project root is inside plugin repository.\\n"
                    f"Plugin repo: {plugin_repo_abs}\\n"
                    f"Detected project root: {project_root_abs}"
                ),
                'suggestion': (
                    "You may be running the command from inside the plugin directory.\\n"
                    "Navigate to your actual project directory first."
                )
            }

    # All validations passed
    return {
        'valid': True,
        'error': None,
        'suggestion': None
    }
```

---

## Usage Examples

### Example 1: Python Project

```python
# User runs: /test-loop src/calculator.py
# Current directory: /home/user/myproject/src/

result = find_project_root("/home/user/myproject/src/calculator.py")

# Result:
{
    'project_root': '/home/user/myproject',
    'marker_file': 'pyproject.toml',
    'marker_language': 'python',
    'confidence': 'high',
    'error': None,
    'suggestion': None
}
```

### Example 2: JavaScript/TypeScript Project

```python
# User runs: /test-loop src/index.ts
# Current directory: /home/user/webapp/src/

result = find_project_root("/home/user/webapp/src/index.ts")

# Result:
{
    'project_root': '/home/user/webapp',
    'marker_file': 'package.json',
    'marker_language': 'javascript',  # or 'typescript' if tsconfig.json found
    'confidence': 'high',
    'error': None,
    'suggestion': None
}
```

### Example 3: Java Maven Project

```python
# User runs: /test-loop src/main/java/Calculator.java

result = find_project_root("/home/user/javaproject/src/main/java/Calculator.java")

# Result:
{
    'project_root': '/home/user/javaproject',
    'marker_file': 'pom.xml',
    'marker_language': 'java',
    'confidence': 'high',
    'error': None,
    'suggestion': None
}
```

### Example 4: Go Project

```python
# User runs: /test-loop calculator.go
# Go projects have flat structure

result = find_project_root("/home/user/go-calc/calculator.go")

# Result:
{
    'project_root': '/home/user/go-calc',
    'marker_file': 'go.mod',
    'marker_language': 'go',
    'confidence': 'high',
    'error': None,
    'suggestion': None
}

# Note: For Go workspace (multi-module) projects:
# If go.work is found, it points to one or more go.mod files
# This can speed up module resolution in monorepos
# Example structure:
#   /workspace/
#     go.work          # Workspace file
#     module-a/
#       go.mod         # Module A
#     module-b/
#       go.mod         # Module B
```

### Example 5: C# Project

```python
# User runs: /test-loop src/Calculator.cs

result = find_project_root("/home/user/MyApp/src/Calculator.cs")

# Result:
{
    'project_root': '/home/user/MyApp',
    'marker_file': 'MyApp.sln',
    'marker_language': 'csharp',
    'confidence': 'high',
    'error': None,
    'suggestion': None
}
```

### Example 6: Error Case - No Project Marker

```python
# User runs: /test-loop script.py
# But script.py is in home directory with no project files

result = find_project_root("/home/user/script.py")

# Result:
{
    'project_root': None,
    'marker_file': None,
    'marker_language': None,
    'confidence': 'none',
    'error': "Cannot determine project root from path: /home/user/script.py",
    'suggestion': "Make sure you're inside a project directory with one of these files:\\n..."
}
```

### Example 7: Error Case - Plugin Repository Detection

```python
# User accidentally runs from plugin directory

result = find_project_root(
    "/home/user/.claude/plugins/dante_plugin/examples/test.py",
    plugin_repo_path="/home/user/.claude/plugins/dante_plugin"
)

# Result:
{
    'project_root': None,
    'marker_file': 'pyproject.toml',  # Plugin has its own pyproject.toml
    'marker_language': 'python',
    'confidence': 'low',
    'error': "Cannot use plugin repository as target project...",
    'suggestion': "Navigate to your actual project directory and run the command again..."
}
```

---

## Edge Cases

### Nested Projects (Monorepos)

**Scenario**: Multiple projects in subdirectories, each with own project markers.

```
/monorepo/
├── package.json (root)
├── project-a/
│   └── package.json
└── project-b/
    └── package.json
```

**Behavior**: Walking up from `/monorepo/project-a/src/index.js` will find `/monorepo/project-a/package.json` first (closest marker).

**Solution**: Use closest marker (most specific project).

### Symlinks

**Scenario**: Source files accessed via symlink.

**Behavior**: `os.path.abspath()` resolves symlinks. Project root detection follows real paths.

**Solution**: No special handling needed - standard path normalization works.

### Case Sensitivity (Windows vs Unix)

**Scenario**: `pyproject.toml` vs `Pyproject.toml` vs `PYPROJECT.TOML`

**Behavior**:
- Unix: Case-sensitive (only exact match works)
- Windows: Case-insensitive (any case works)

**Solution**: Use `os.path.exists()` which handles platform differences automatically.

### Network Paths / UNC Paths (Windows)

**Scenario**: `\\\\server\\share\\project\\src\\file.py`

**Behavior**: `os.path` functions handle UNC paths correctly.

**Solution**: No special handling needed.

---

## Integration with Other Skills

### Used By:

1. **Test Loop Orchestrator** (Phase 1: Analysis)
   - Calls this skill to find project root before test generation

2. **Write Agent** (Step 3: Generate Test Structure)
   - Uses project root to determine test file locations

3. **State Management Skill**
   - Uses project root to place `.claude/.test-loop-state.md`

4. **Test Location Resolution Skill**
   - Uses project root as base for test directory resolution

### Provides:

- `project_root`: Base directory for all project-relative paths
- `marker_language`: Hint for language-specific logic
- `validation`: Safety checks passed

---

## Testing Checklist

For TASK-001 acceptance:

- [ ] Detects Python projects (pyproject.toml, setup.py, requirements.txt)
- [ ] Detects JavaScript projects (package.json)
- [ ] Detects TypeScript projects (tsconfig.json, package.json)
- [ ] Detects Java projects (pom.xml, build.gradle)
- [ ] Detects C# projects (*.sln, *.csproj)
- [ ] Detects Go projects (go.mod)
- [ ] Detects C++ projects (CMakeLists.txt, Makefile)
- [ ] Walks up from subdirectories correctly
- [ ] Prioritizes language-specific markers over VCS markers
- [ ] Returns error when no marker found
- [ ] Returns error when project root is plugin repository
- [ ] Handles Windows paths correctly (backslashes)
- [ ] Handles Unix paths correctly (forward slashes)
- [ ] Handles UNC paths (Windows network paths)
- [ ] Handles symlinks correctly
- [ ] Max depth limit prevents infinite loops
- [ ] Clear error messages with actionable suggestions

---

## Configuration

**Plugin Repository Path Detection**:

The orchestrator must provide the plugin repository path for validation. This can be detected via:

```python
# In orchestrator or agent
PLUGIN_REPO_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Assuming agent is in dante_plugin/agents/
```

Or from environment variable:
```python
PLUGIN_REPO_PATH = os.getenv('CLAUDE_PLUGIN_PATH', '/default/path')
```

---

## Enhanced Error Messages (v1.1.0)

This section provides comprehensive, actionable error messages for all failure scenarios.

### Error 1: No Project Marker Found

**Scenario**: Walking up directory tree finds no project markers within 10 levels.

**Error Message**:
```
❌ Cannot Determine Project Root

I searched up to 10 directory levels from your target path but couldn't find any project marker files.

Target path: {target_path}
Searched up to: {highest_directory_searched}

What are project marker files?
Project markers are files that indicate the root of a project, such as:
  • Python: pyproject.toml, setup.py, requirements.txt, pytest.ini
  • JavaScript/TypeScript: package.json, tsconfig.json
  • Java: pom.xml, build.gradle
  • C#: *.sln, *.csproj, global.json
  • Go: go.mod
  • C++: CMakeLists.txt, Makefile
  • Version Control: .git/ directory

How to fix this:
1. Navigate to your project root directory:
   cd /path/to/your/project

2. Verify a marker file exists:
   ls -la | grep -E "pyproject.toml|package.json|pom.xml|go.mod|CMakeLists.txt|\.git"

3. If no marker exists, create one for your language:
   Python:     touch requirements.txt (or pyproject.toml for modern Python)
   JavaScript: npm init -y
   TypeScript: npm init -y && npx tsc --init
   Java:       Create pom.xml (Maven) or build.gradle (Gradle)
   Go:         go mod init <module-name>
   C++:        Create CMakeLists.txt or Makefile

4. Then run the test command again from within your project.

Need help? Check if you're in the right directory:
  pwd                    # Show current directory
  ls -la                 # List all files including hidden ones
  find . -name "*.py"    # Find Python files (adjust for your language)
```

**Implementation**:
```python
def generate_no_marker_error(target_path: str, max_depth_reached: str) -> dict:
    return {
        'project_root': None,
        'marker_file': None,
        'marker_language': None,
        'confidence': 'none',
        'error': f"Cannot determine project root from path: {target_path}",
        'suggestion': (
            f"Target path: {target_path}\n"
            f"Searched up to: {max_depth_reached}\n\n"
            "Make sure you're inside a project directory with one of these marker files:\n\n"
            "Python Projects:\n"
            "  • pyproject.toml (modern Python with build config)\n"
            "  • setup.py (traditional Python packaging)\n"
            "  • requirements.txt (pip dependencies)\n"
            "  • pytest.ini (pytest configuration)\n\n"
            "JavaScript/TypeScript Projects:\n"
            "  • package.json (npm/yarn package file)\n"
            "  • tsconfig.json (TypeScript configuration)\n\n"
            "Java Projects:\n"
            "  • pom.xml (Maven project)\n"
            "  • build.gradle (Gradle project)\n\n"
            "C# Projects:\n"
            "  • *.sln (Visual Studio solution)\n"
            "  • *.csproj (C# project file)\n"
            "  • global.json (.NET global config)\n\n"
            "Go Projects:\n"
            "  • go.mod (Go modules file)\n\n"
            "C++ Projects:\n"
            "  • CMakeLists.txt (CMake build file)\n"
            "  • Makefile (Make build file)\n\n"
            "Or initialize a git repository:\n"
            "  git init\n\n"
            "To fix:\n"
            "1. cd to your project root directory\n"
            "2. Verify marker file exists: ls -la\n"
            "3. If missing, create one (see examples above)\n"
            "4. Run the test command again"
        )
    }
```

---

### Error 2: Plugin Repository Detected as Project Root

**Scenario**: Project root detection finds the plugin repository itself.

**Error Message**:
```
❌ Cannot Use Plugin Repository as Target Project

The detected project root is the plugin repository itself, not your actual project.

Plugin repository: {plugin_repo_path}
Detected project root: {project_root}

This usually happens when:
  • You ran the command from inside the plugin directory
  • The plugin directory has a project marker file (pyproject.toml, etc.)

How to fix:
1. Navigate to your actual project directory:
   cd /path/to/your/actual/project

2. Verify you're in the right place:
   pwd                    # Should show YOUR project path
   ls                     # Should show YOUR project files

3. Run the test command again:
   /test-loop src/your_file.py

Example:
  # ❌ Wrong - inside plugin directory
  cd ~/.claude/plugins/dante_plugin
  /test-loop examples/calculator.py

  # ✅ Correct - in your actual project
  cd ~/projects/my-app
  /test-loop src/calculator.py

The plugin should analyze YOUR code, not its own code!
```

**Implementation**:
```python
def generate_plugin_repo_error(project_root: str, plugin_repo_path: str) -> dict:
    return {
        'valid': False,
        'error': (
            "❌ Cannot Use Plugin Repository as Target Project\n\n"
            f"Plugin repository: {plugin_repo_path}\n"
            f"Detected project root: {project_root}\n\n"
            "The plugin detected its own directory as the project root, but it should be analyzing YOUR code, not the plugin's code."
        ),
        'suggestion': (
            "How to fix:\n\n"
            "1. Navigate to your actual project directory:\n"
            f"   cd /path/to/your/project\n\n"
            "2. Verify you're in the correct directory:\n"
            "   pwd        # Should NOT show the plugin path\n"
            "   ls         # Should show YOUR project files\n\n"
            "3. Run the test command again:\n"
            "   /test-loop src/\n\n"
            "Example:\n"
            "  ❌ Wrong:\n"
            "    cd ~/.claude/plugins/dante_plugin\n"
            "    /test-loop examples/test.py\n\n"
            "  ✅ Correct:\n"
            "    cd ~/projects/my-app\n"
            "    /test-loop src/calculator.py"
        )
    }
```

---

### Error 3: Project Root Not Writable

**Scenario**: Project root found but lacks write permissions.

**Error Message** (Platform-specific):
```python
import platform
import os

def generate_not_writable_error(project_root: str) -> str:
    """Generate platform-specific error message for unwritable project root."""
    current_user = os.getuser()
    is_windows = platform.system() == 'Windows'

    if is_windows:
        # Windows-specific instructions
        return f"""❌ Project Root is Not Writable

Project root: {project_root}
Current user: {current_user}

I cannot create test files or state directories because the project root lacks write permissions.

How to fix:

1. Check current permissions:
   icacls "{project_root}"
   # Look for your username with (W) write permission

2. Fix permissions if you own the directory:
   # Run PowerShell as Administrator, then:
   icacls "{project_root}" /grant {current_user}:(OI)(CI)F /T
   # Or using File Explorer: Right-click folder > Properties > Security > Edit

3. If you don't own the directory:
   # Option A: Change ownership (requires Administrator)
   takeown /F "{project_root}" /R /D Y
   icacls "{project_root}" /grant {current_user}:(OI)(CI)F /T

   # Option B: Copy project to writable location
   xcopy "{project_root}" "%USERPROFILE%\\my-projects\\project-copy" /E /I
   cd %USERPROFILE%\\my-projects\\project-copy

4. Verify write access:
   echo test > "{project_root}\\test-write.txt" && del "{project_root}\\test-write.txt"
   # Should succeed without errors

5. Run the test command again

Common causes:
  • Project in system directory (C:\\Windows, C:\\Program Files)
  • Network drive with restricted permissions
  • OneDrive/cloud folder with sync issues
  • Wrong user (project owned by different user)
"""
    else:
        # Unix/Linux/macOS-specific instructions
        return f"""❌ Project Root is Not Writable

Project root: {project_root}
Current user: {current_user}

I cannot create test files or state directories because the project root lacks write permissions.

How to fix:

1. Check current permissions:
   ls -ld {project_root}
   # Should show: drwxr-xr-x  (owner has write permission)

2. Fix permissions if you own the directory:
   chmod u+w {project_root}

3. If you don't own the directory:
   # Option A: Change ownership (requires sudo)
   sudo chown -R {current_user} {project_root}

   # Option B: Copy project to writable location
   cp -r {project_root} ~/my-projects/project-copy
   cd ~/my-projects/project-copy

4. Verify write access:
   touch {project_root}/test-write && rm {project_root}/test-write
   # Should succeed without errors

5. Run the test command again

Common causes:
  • Project in system directory (/usr/local, /opt, /etc)
  • Project in read-only mount
  • Docker container with read-only volumes
  • Wrong user (project owned by different user)
  • NFS mount with no_root_squash issue
"""
```

**Implementation**:
```python
import getpass

def generate_not_writable_error(project_root: str) -> dict:
    current_user = getpass.getuser()
    return {
        'valid': False,
        'error': f"Project root is not writable: {project_root}",
        'suggestion': (
            f"❌ Project Root is Not Writable\n\n"
            f"Project root: {project_root}\n"
            f"Current user: {current_user}\n\n"
            "Cannot create test files or state directories due to insufficient permissions.\n\n"
            "How to fix:\n\n"
            "1. Check permissions:\n"
            f"   ls -ld {project_root}\n\n"
            "2. Fix permissions:\n"
            f"   chmod u+w {project_root}    # Add write permission\n\n"
            "3. Or change ownership:\n"
            f"   sudo chown -R {current_user} {project_root}\n\n"
            "4. Or copy to writable location:\n"
            f"   cp -r {project_root} ~/my-projects/\n\n"
            "5. Verify write access:\n"
            f"   touch {project_root}/test && rm {project_root}/test"
        )
    }
```

---

### Error 4: Project Root is Inside Plugin Repository

**Scenario**: Project root detected inside the plugin repository (subdirectory).

**Error Message**:
```
❌ Detected Project Root is Inside Plugin Repository

Plugin repository: {plugin_repo_path}
Detected project root: {project_root}

This indicates you may be working on example code or tests inside the plugin directory itself.

How to fix:

1. If this is your actual project (not plugin examples):
   # Move your project outside the plugin directory
   mv {project_root} ~/projects/
   cd ~/projects/{project_name}
   /test-loop src/

2. If you want to test the plugin examples:
   # Don't use the test loop for plugin development
   # Instead, run tests directly:
   cd {plugin_repo_path}
   pytest tests/

3. If you're developing a new project:
   # Create it outside the plugin directory
   cd ~/projects
   mkdir my-new-project
   cd my-new-project
   # Initialize your project (pip init, npm init, etc.)
   /test-loop src/

The plugin directory is for plugin code only. Your projects should live elsewhere!
```

---

### Error 5: Project Root Does Not Exist

**Scenario**: Validation finds project root doesn't exist (edge case).

**Error Message**:
```
❌ Project Root Does Not Exist

Project root: {project_root}

This is unusual - the path was detected but doesn't exist. This might indicate:
  • Path was deleted after detection
  • Symlink is broken
  • Race condition (file system changed during detection)

How to fix:

1. Verify the path:
   ls -la {project_root}

2. Check for symlinks:
   ls -la {os.path.dirname(project_root)}

3. If path should exist, recreate it:
   mkdir -p {project_root}
   cd {project_root}
   # Initialize your project

4. Try from a different directory:
   cd /path/to/working/directory
   /test-loop src/

5. If problem persists, report a bug with these details:
   - Command run: {command}
   - Current directory: {os.getcwd()}
   - Detected root: {project_root}
```

---

### Error Template Helpers

```python
def format_error_with_context(
    error_type: str,
    project_root: str = None,
    plugin_repo_path: str = None,
    target_path: str = None,
    additional_context: dict = None
) -> str:
    """
    Format error message with full context for debugging.

    Args:
        error_type: Type of error (no_marker, plugin_repo, not_writable, etc.)
        project_root: Detected project root (if any)
        plugin_repo_path: Plugin repository path
        target_path: Original target path
        additional_context: Additional key-value pairs for context

    Returns:
        Formatted error string with context
    """
    context_lines = [
        "=== Debug Context ===",
        f"Error Type: {error_type}",
    ]

    if target_path:
        context_lines.append(f"Target Path: {target_path}")

    if project_root:
        context_lines.append(f"Detected Project Root: {project_root}")

    if plugin_repo_path:
        context_lines.append(f"Plugin Repository: {plugin_repo_path}")

    context_lines.append(f"Current Directory: {os.getcwd()}")
    context_lines.append(f"User: {getpass.getuser()}")

    if additional_context:
        for key, value in additional_context.items():
            context_lines.append(f"{key}: {value}")

    context_lines.append("=" * 20)

    return "\n".join(context_lines)
```

---

## Version History

- **1.1.0** (2025-12-12): Enhanced error messages with actionable guidance
- **1.0.0** (2025-12-11): Initial version with cross-language support for 7 languages
