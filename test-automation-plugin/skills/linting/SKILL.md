---
name: linting
description: Detect and execute linters/formatters configured in projects for all supported languages. Use when ensuring generated test code complies with project code quality standards by running configured linters and formatters with auto-fix.
user-invocable: false
---

# Linting Skill

**Version**: 1.0.0
**Category**: Code Quality
**Languages**: Python, JavaScript, TypeScript, Java, C#, Go, C++
**Purpose**: Detect and execute linters/formatters configured in projects for all 7 supported languages

## Overview

The Linting Skill provides comprehensive linter and formatter detection and execution capabilities for automated testing workflows. It identifies project-configured linters/formatters by analyzing config files, package scripts, and CI/CD configurations, then executes them with auto-fix enabled to ensure generated tests comply with project code quality standards.

## Skill Interface

### Input

```yaml
project_root: Absolute path to the project root directory
language: Programming language (python, javascript, typescript, java, csharp, go, cpp)
test_files: List of absolute paths to generated test files
```

### Output

```yaml
linters_detected: List of detected linters with configuration
  - tool: black
    config_path: /project/pyproject.toml
    detection_method: config_file
    command: black .
    auto_fix_command: black .
    supports_auto_fix: true
lint_results:
  success: true
  formatters_run: [black, isort]
  linters_run: [ruff]
  formatted_files: 3
  fixed_issues: 5
  errors: []
```

## Detection Strategy

Linter detection uses a **priority-based approach** with multiple detection methods:

### Detection Priority (High to Low)

1. **Config Files** (weight: 10) - Highest confidence
   - Language-specific config files (pyproject.toml, .prettierrc, etc.)
   - Explicit configuration = strong signal of intent

2. **Package Scripts** (weight: 8) - High confidence
   - package.json scripts, Makefile targets, build.gradle tasks
   - Scripts indicate active usage

3. **CI/CD Configs** (weight: 6) - Medium confidence
   - .github/workflows/*.yml, .gitlab-ci.yml, azure-pipelines.yml
   - CI/CD usage indicates project-wide standards

4. **Defaults** (weight: 0) - Fallback only
   - Language-specific defaults if nothing else found
   - No error if no linters detected (graceful fallback)

### Detection Algorithm

```python
def detect_linters(project_root: str, language: str) -> list:
    """
    Detect linters for given language in project.

    Returns list of dicts:
    [{
        "tool": "black",
        "config_path": "/path/to/pyproject.toml",
        "detection_method": "config_file",
        "command": "black {files}",
        "auto_fix_command": "black {files}",
        "supports_auto_fix": true,
        "file_extensions": [".py"]
    }]

    Returns empty list if no linters detected (not an error).
    """
    detected = []

    # 1. Check config files (highest priority)
    for config_file in CONFIG_FILES[language]:
        if exists(os.path.join(project_root, config_file)):
            tools = parse_config(config_file, language)
            detected.extend(tools)

    # 2. Check package scripts
    if language in ['javascript', 'typescript']:
        package_json = os.path.join(project_root, 'package.json')
        if exists(package_json):
            scripts = parse_package_json_scripts(package_json)
            detected.extend(extract_lint_tools(scripts))

    elif language == 'java':
        # Check Maven pom.xml for plugins
        pom_xml = os.path.join(project_root, 'pom.xml')
        if exists(pom_xml):
            plugins = parse_maven_plugins(pom_xml)
            detected.extend(extract_lint_plugins(plugins))

        # Check Gradle build files
        for gradle_file in ['build.gradle', 'build.gradle.kts']:
            gradle_path = os.path.join(project_root, gradle_file)
            if exists(gradle_path):
                plugins = parse_gradle_plugins(gradle_path)
                detected.extend(extract_lint_plugins(plugins))

    # 3. Check CI/CD configs
    ci_tools = detect_from_ci_configs(project_root, language)
    detected.extend(ci_tools)

    # 4. Deduplicate by tool name (keep first occurrence = highest priority)
    detected = deduplicate_by_tool_name(detected)

    return detected
```

## Language-Specific Detection

### Python

**Formatters**:
- **black**: Python code formatter (PEP 8 compliant)
  - Config: `pyproject.toml:[tool.black]`, `.black.toml`
  - Command: `black {files}`
  - Auto-fix: Yes
  - Detection: Check for `[tool.black]` section or black in dependencies

- **isort**: Import statement sorter
  - Config: `pyproject.toml:[tool.isort]`, `.isort.cfg`, `setup.cfg`
  - Command: `isort {files}`
  - Auto-fix: Yes
  - Detection: Check for `[tool.isort]` section or isort in dependencies

- **autopep8**: PEP 8 auto-formatter
  - Config: `setup.cfg`, `.pep8`, `pyproject.toml`
  - Command: `autopep8 --in-place {files}`
  - Auto-fix: Yes
  - Detection: Check for autopep8 in dependencies

**Linters**:
- **ruff**: Fast Python linter (combines multiple linters)
  - Config: `pyproject.toml:[tool.ruff]`, `ruff.toml`, `.ruff.toml`
  - Command: `ruff check {files}`
  - Auto-fix: `ruff check --fix {files}`
  - Detection: Check for `[tool.ruff]` section or ruff in dependencies

- **pylint**: Comprehensive Python linter
  - Config: `.pylintrc`, `pyproject.toml:[tool.pylint]`, `setup.cfg`
  - Command: `pylint {files}`
  - Auto-fix: Limited (some fixes available)
  - Detection: Check for .pylintrc or pylint in dependencies

- **flake8**: Style guide enforcement
  - Config: `.flake8`, `setup.cfg`, `tox.ini`
  - Command: `flake8 {files}`
  - Auto-fix: No (use with autopep8)
  - Detection: Check for .flake8 or flake8 in dependencies

- **mypy**: Static type checker
  - Config: `mypy.ini`, `pyproject.toml:[tool.mypy]`, `setup.cfg`
  - Command: `mypy {files}`
  - Auto-fix: No
  - Detection: Check for mypy.ini or mypy in dependencies

**Config File Detection**:
```python
PYTHON_CONFIG_FILES = [
    'pyproject.toml',      # Poetry, modern Python projects
    'setup.cfg',           # setuptools configuration
    '.black.toml',         # black-specific config
    '.isort.cfg',          # isort-specific config
    'ruff.toml',           # ruff-specific config
    '.ruff.toml',
    '.pylintrc',           # pylint-specific config
    '.flake8',             # flake8-specific config
    'mypy.ini',            # mypy-specific config
]

def parse_python_config(config_file: str, project_root: str) -> list:
    """Parse Python config files to detect linters."""
    detected = []
    config_path = os.path.join(project_root, config_file)

    if config_file == 'pyproject.toml':
        import tomli
        with open(config_path, 'rb') as f:
            config = tomli.load(f)

        # Check for black
        if 'tool' in config and 'black' in config['tool']:
            detected.append({
                'tool': 'black',
                'config_path': config_path,
                'detection_method': 'config_file',
                'command': 'black {files}',
                'auto_fix_command': 'black {files}',
                'supports_auto_fix': True,
                'file_extensions': ['.py']
            })

        # Check for isort
        if 'tool' in config and 'isort' in config['tool']:
            detected.append({
                'tool': 'isort',
                'config_path': config_path,
                'detection_method': 'config_file',
                'command': 'isort {files}',
                'auto_fix_command': 'isort {files}',
                'supports_auto_fix': True,
                'file_extensions': ['.py']
            })

        # Check for ruff
        if 'tool' in config and 'ruff' in config['tool']:
            detected.append({
                'tool': 'ruff',
                'config_path': config_path,
                'detection_method': 'config_file',
                'command': 'ruff check {files}',
                'auto_fix_command': 'ruff check --fix {files}',
                'supports_auto_fix': True,
                'file_extensions': ['.py']
            })

        # Check for pylint
        if 'tool' in config and 'pylint' in config['tool']:
            detected.append({
                'tool': 'pylint',
                'config_path': config_path,
                'detection_method': 'config_file',
                'command': 'pylint {files}',
                'auto_fix_command': None,
                'supports_auto_fix': False,
                'file_extensions': ['.py']
            })

        # Check for mypy
        if 'tool' in config and 'mypy' in config['tool']:
            detected.append({
                'tool': 'mypy',
                'config_path': config_path,
                'detection_method': 'config_file',
                'command': 'mypy {files}',
                'auto_fix_command': None,
                'supports_auto_fix': False,
                'file_extensions': ['.py']
            })

    elif config_file == '.pylintrc':
        detected.append({
            'tool': 'pylint',
            'config_path': config_path,
            'detection_method': 'config_file',
            'command': 'pylint {files}',
            'auto_fix_command': None,
            'supports_auto_fix': False,
            'file_extensions': ['.py']
        })

    # Similar logic for other config files...

    return detected
```

**Package Manager Detection**:
```python
def detect_python_from_dependencies(project_root: str) -> list:
    """Detect Python linters from requirements.txt or pyproject.toml dependencies."""
    detected = []

    # Check requirements.txt
    req_file = os.path.join(project_root, 'requirements.txt')
    if os.path.exists(req_file):
        with open(req_file, 'r') as f:
            requirements = f.read()

        if 'black' in requirements:
            detected.append({'tool': 'black', 'detection_method': 'dependencies'})
        if 'isort' in requirements:
            detected.append({'tool': 'isort', 'detection_method': 'dependencies'})
        if 'ruff' in requirements:
            detected.append({'tool': 'ruff', 'detection_method': 'dependencies'})
        if 'pylint' in requirements:
            detected.append({'tool': 'pylint', 'detection_method': 'dependencies'})
        if 'flake8' in requirements:
            detected.append({'tool': 'flake8', 'detection_method': 'dependencies'})
        if 'mypy' in requirements:
            detected.append({'tool': 'mypy', 'detection_method': 'dependencies'})

    return detected
```

### JavaScript/TypeScript

**Formatters**:
- **prettier**: Opinionated code formatter
  - Config: `.prettierrc`, `.prettierrc.json`, `.prettierrc.js`, `prettier.config.js`, `package.json:prettier`
  - Command: `npx prettier --write {files}`
  - Auto-fix: Yes
  - Detection: Check for prettier config or in package.json dependencies

**Linters**:
- **eslint**: Pluggable JavaScript linter
  - Config: `.eslintrc`, `.eslintrc.json`, `.eslintrc.js`, `eslint.config.js`, `package.json:eslintConfig`
  - Command: `npx eslint {files}`
  - Auto-fix: `npx eslint --fix {files}`
  - Detection: Check for eslint config or in package.json dependencies

- **tslint** (deprecated, but still used): TypeScript linter
  - Config: `tslint.json`
  - Command: `npx tslint --fix {files}`
  - Auto-fix: Yes
  - Detection: Check for tslint.json

**Config File Detection**:
```python
JS_TS_CONFIG_FILES = [
    '.prettierrc',
    '.prettierrc.json',
    '.prettierrc.js',
    'prettier.config.js',
    '.eslintrc',
    '.eslintrc.json',
    '.eslintrc.js',
    'eslint.config.js',
    'tslint.json',
    'package.json',  # Check for prettier/eslintConfig sections
]

def parse_js_ts_config(config_file: str, project_root: str) -> list:
    """Parse JS/TS config files to detect linters."""
    detected = []
    config_path = os.path.join(project_root, config_file)

    if config_file == 'package.json':
        import json
        with open(config_path, 'r') as f:
            package = json.load(f)

        # Check for prettier in config or dependencies
        if 'prettier' in package or 'prettier' in package.get('devDependencies', {}):
            detected.append({
                'tool': 'prettier',
                'config_path': config_path,
                'detection_method': 'config_file',
                'command': 'npx prettier --write {files}',
                'auto_fix_command': 'npx prettier --write {files}',
                'supports_auto_fix': True,
                'file_extensions': ['.js', '.jsx', '.ts', '.tsx', '.json', '.css']
            })

        # Check for eslint in config or dependencies
        if 'eslintConfig' in package or 'eslint' in package.get('devDependencies', {}):
            detected.append({
                'tool': 'eslint',
                'config_path': config_path,
                'detection_method': 'config_file',
                'command': 'npx eslint {files}',
                'auto_fix_command': 'npx eslint --fix {files}',
                'supports_auto_fix': True,
                'file_extensions': ['.js', '.jsx', '.ts', '.tsx']
            })

    elif config_file.startswith('.prettierrc') or config_file == 'prettier.config.js':
        detected.append({
            'tool': 'prettier',
            'config_path': config_path,
            'detection_method': 'config_file',
            'command': 'npx prettier --write {files}',
            'auto_fix_command': 'npx prettier --write {files}',
            'supports_auto_fix': True,
            'file_extensions': ['.js', '.jsx', '.ts', '.tsx', '.json', '.css']
        })

    elif config_file.startswith('.eslintrc') or config_file == 'eslint.config.js':
        detected.append({
            'tool': 'eslint',
            'config_path': config_path,
            'detection_method': 'config_file',
            'command': 'npx eslint {files}',
            'auto_fix_command': 'npx eslint --fix {files}',
            'supports_auto_fix': True,
            'file_extensions': ['.js', '.jsx', '.ts', '.tsx']
        })

    elif config_file == 'tslint.json':
        detected.append({
            'tool': 'tslint',
            'config_path': config_path,
            'detection_method': 'config_file',
            'command': 'npx tslint --fix {files}',
            'auto_fix_command': 'npx tslint --fix {files}',
            'supports_auto_fix': True,
            'file_extensions': ['.ts', '.tsx']
        })

    return detected
```

**Package Scripts Detection**:
```python
def detect_js_ts_from_scripts(project_root: str) -> list:
    """Detect JS/TS linters from package.json scripts."""
    detected = []
    package_json = os.path.join(project_root, 'package.json')

    if os.path.exists(package_json):
        import json
        with open(package_json, 'r') as f:
            package = json.load(f)

        scripts = package.get('scripts', {})

        # Check for lint/format scripts
        for script_name, script_command in scripts.items():
            if 'prettier' in script_command:
                detected.append({'tool': 'prettier', 'detection_method': 'package_script'})
            if 'eslint' in script_command:
                detected.append({'tool': 'eslint', 'detection_method': 'package_script'})
            if 'tslint' in script_command:
                detected.append({'tool': 'tslint', 'detection_method': 'package_script'})

    return detected
```

### Java

**Formatters**:
- **spotless**: Universal code formatter with google-java-format
  - Config: `pom.xml:<plugin>com.diffplug.spotless</plugin>` (Maven), `build.gradle:spotless{}` (Gradle)
  - Command: `mvn spotless:apply` (Maven), `./gradlew spotlessApply` (Gradle)
  - Auto-fix: Yes
  - Detection: Check for spotless plugin in pom.xml or build.gradle

- **google-java-format**: Google's Java formatter
  - Config: Standalone or part of spotless
  - Command: `google-java-format --replace {files}`
  - Auto-fix: Yes
  - Detection: Check for google-java-format in dependencies or spotless config

**Linters**:
- **checkstyle**: Java style checker
  - Config: `checkstyle.xml`, `pom.xml:<plugin>checkstyle</plugin>`
  - Command: `mvn checkstyle:check` (Maven), `./gradlew checkstyleMain` (Gradle)
  - Auto-fix: Limited
  - Detection: Check for checkstyle.xml or checkstyle plugin

**Config File Detection**:
```python
JAVA_CONFIG_FILES = [
    'pom.xml',
    'build.gradle',
    'build.gradle.kts',
    'checkstyle.xml',
]

def parse_java_config(config_file: str, project_root: str) -> list:
    """Parse Java config files to detect linters."""
    detected = []
    config_path = os.path.join(project_root, config_file)

    if config_file == 'pom.xml':
        # Parse Maven pom.xml for plugins
        with open(config_path, 'r') as f:
            content = f.read()

        # Check for spotless plugin
        if 'com.diffplug.spotless' in content:
            detected.append({
                'tool': 'spotless',
                'config_path': config_path,
                'detection_method': 'config_file',
                'command': 'mvn spotless:apply',
                'auto_fix_command': 'mvn spotless:apply',
                'supports_auto_fix': True,
                'file_extensions': ['.java']
            })

        # Check for checkstyle plugin
        if 'maven-checkstyle-plugin' in content:
            detected.append({
                'tool': 'checkstyle',
                'config_path': config_path,
                'detection_method': 'config_file',
                'command': 'mvn checkstyle:check',
                'auto_fix_command': None,
                'supports_auto_fix': False,
                'file_extensions': ['.java']
            })

    elif config_file.startswith('build.gradle'):
        # Parse Gradle build file for plugins
        with open(config_path, 'r') as f:
            content = f.read()

        # Check for spotless plugin
        if 'com.diffplug.spotless' in content or "id 'com.diffplug.spotless'" in content:
            detected.append({
                'tool': 'spotless',
                'config_path': config_path,
                'detection_method': 'config_file',
                'command': './gradlew spotlessApply',
                'auto_fix_command': './gradlew spotlessApply',
                'supports_auto_fix': True,
                'file_extensions': ['.java']
            })

        # Check for checkstyle plugin
        if 'checkstyle' in content:
            detected.append({
                'tool': 'checkstyle',
                'config_path': config_path,
                'detection_method': 'config_file',
                'command': './gradlew checkstyleMain',
                'auto_fix_command': None,
                'supports_auto_fix': False,
                'file_extensions': ['.java']
            })

    elif config_file == 'checkstyle.xml':
        detected.append({
            'tool': 'checkstyle',
            'config_path': config_path,
            'detection_method': 'config_file',
            'command': 'mvn checkstyle:check',
            'auto_fix_command': None,
            'supports_auto_fix': False,
            'file_extensions': ['.java']
        })

    return detected
```

### C#

**Formatters**:
- **dotnet format**: Official .NET code formatter
  - Config: `.editorconfig`, `Directory.Build.props`, `*.csproj`
  - Command: `dotnet format {solution_or_project}`
  - Auto-fix: Yes
  - Detection: Check for .editorconfig or dotnet format usage

**Config File Detection**:
```python
CSHARP_CONFIG_FILES = [
    '.editorconfig',
    'Directory.Build.props',
]

def parse_csharp_config(config_file: str, project_root: str) -> list:
    """Parse C# config files to detect linters."""
    detected = []
    config_path = os.path.join(project_root, config_file)

    if config_file == '.editorconfig' or config_file == 'Directory.Build.props':
        # If .editorconfig exists, dotnet format can use it
        detected.append({
            'tool': 'dotnet format',
            'config_path': config_path,
            'detection_method': 'config_file',
            'command': 'dotnet format',
            'auto_fix_command': 'dotnet format',
            'supports_auto_fix': True,
            'file_extensions': ['.cs']
        })

    return detected
```

### Go

**Formatters**:
- **gofmt**: Official Go formatter (always available)
  - Config: None (standard tool)
  - Command: `gofmt -w {files}`
  - Auto-fix: Yes
  - Detection: Always available with Go installation

- **goimports**: Go formatter with import management
  - Config: None
  - Command: `goimports -w {files}`
  - Auto-fix: Yes
  - Detection: Check if goimports is installed

**Linters**:
- **golangci-lint**: Fast Go linters runner (aggregates multiple linters)
  - Config: `.golangci.yml`, `.golangci.yaml`
  - Command: `golangci-lint run {files}`
  - Auto-fix: `golangci-lint run --fix {files}`
  - Detection: Check for .golangci.yml or golangci-lint installation

- **go vet**: Go's built-in static analysis tool
  - Config: None (standard tool)
  - Command: `go vet {files}`
  - Auto-fix: No
  - Detection: Always available with Go installation

**Config File Detection**:
```python
GO_CONFIG_FILES = [
    '.golangci.yml',
    '.golangci.yaml',
]

def parse_go_config(config_file: str, project_root: str) -> list:
    """Parse Go config files to detect linters."""
    detected = []
    config_path = os.path.join(project_root, config_file)

    # gofmt is always available
    detected.append({
        'tool': 'gofmt',
        'config_path': None,
        'detection_method': 'default',
        'command': 'gofmt -w {files}',
        'auto_fix_command': 'gofmt -w {files}',
        'supports_auto_fix': True,
        'file_extensions': ['.go']
    })

    # Check for goimports
    if shutil.which('goimports'):
        detected.append({
            'tool': 'goimports',
            'config_path': None,
            'detection_method': 'default',
            'command': 'goimports -w {files}',
            'auto_fix_command': 'goimports -w {files}',
            'supports_auto_fix': True,
            'file_extensions': ['.go']
        })

    # Check for golangci-lint config
    if os.path.exists(config_path):
        detected.append({
            'tool': 'golangci-lint',
            'config_path': config_path,
            'detection_method': 'config_file',
            'command': 'golangci-lint run',
            'auto_fix_command': 'golangci-lint run --fix',
            'supports_auto_fix': True,
            'file_extensions': ['.go']
        })

    return detected
```

### C++

**Formatters**:
- **clang-format**: LLVM code formatter
  - Config: `.clang-format`
  - Command: `clang-format -i {files}`
  - Auto-fix: Yes
  - Detection: Check for .clang-format file

**Linters**:
- **clang-tidy**: LLVM C++ linter
  - Config: `.clang-tidy`
  - Command: `clang-tidy {files} -- -std=c++17`
  - Auto-fix: `clang-tidy --fix {files} -- -std=c++17`
  - Detection: Check for .clang-tidy file

**Config File Detection**:
```python
CPP_CONFIG_FILES = [
    '.clang-format',
    '.clang-tidy',
]

def parse_cpp_config(config_file: str, project_root: str) -> list:
    """Parse C++ config files to detect linters."""
    detected = []
    config_path = os.path.join(project_root, config_file)

    if config_file == '.clang-format':
        detected.append({
            'tool': 'clang-format',
            'config_path': config_path,
            'detection_method': 'config_file',
            'command': 'clang-format -i {files}',
            'auto_fix_command': 'clang-format -i {files}',
            'supports_auto_fix': True,
            'file_extensions': ['.cpp', '.hpp', '.cc', '.h', '.cxx']
        })

    elif config_file == '.clang-tidy':
        detected.append({
            'tool': 'clang-tidy',
            'config_path': config_path,
            'detection_method': 'config_file',
            'command': 'clang-tidy {files} --',
            'auto_fix_command': 'clang-tidy --fix {files} --',
            'supports_auto_fix': True,
            'file_extensions': ['.cpp', '.hpp', '.cc', '.h', '.cxx']
        })

    return detected
```

## CI/CD Detection

Detect linters from CI/CD configuration files:

```python
def detect_from_ci_configs(project_root: str, language: str) -> list:
    """Detect linters from CI/CD configurations."""
    detected = []

    # GitHub Actions
    github_workflows_dir = os.path.join(project_root, '.github', 'workflows')
    if os.path.exists(github_workflows_dir):
        for workflow_file in os.listdir(github_workflows_dir):
            if workflow_file.endswith(('.yml', '.yaml')):
                workflow_path = os.path.join(github_workflows_dir, workflow_file)
                with open(workflow_path, 'r') as f:
                    content = f.read()

                # Check for language-specific linters in workflow
                if language == 'python':
                    if 'black' in content:
                        detected.append({'tool': 'black', 'detection_method': 'ci_cd'})
                    if 'ruff' in content:
                        detected.append({'tool': 'ruff', 'detection_method': 'ci_cd'})
                    if 'pylint' in content:
                        detected.append({'tool': 'pylint', 'detection_method': 'ci_cd'})

                elif language in ['javascript', 'typescript']:
                    if 'prettier' in content:
                        detected.append({'tool': 'prettier', 'detection_method': 'ci_cd'})
                    if 'eslint' in content:
                        detected.append({'tool': 'eslint', 'detection_method': 'ci_cd'})

                elif language == 'go':
                    if 'golangci-lint' in content:
                        detected.append({'tool': 'golangci-lint', 'detection_method': 'ci_cd'})

                # Similar checks for other languages...

    # GitLab CI
    gitlab_ci = os.path.join(project_root, '.gitlab-ci.yml')
    if os.path.exists(gitlab_ci):
        with open(gitlab_ci, 'r') as f:
            content = f.read()
        # Similar linter detection logic...

    # Azure Pipelines
    azure_pipelines = os.path.join(project_root, 'azure-pipelines.yml')
    if os.path.exists(azure_pipelines):
        with open(azure_pipelines, 'r') as f:
            content = f.read()
        # Similar linter detection logic...

    return detected
```

## Linter Execution

### Execution Order

**Critical**: Run formatters before linters to avoid conflicts.

1. **Formatters First**: prettier, black, gofmt, clang-format, etc.
   - These modify code structure (whitespace, line breaks)
   - Must run before linters to avoid false positives

2. **Linters Second**: eslint --fix, ruff --fix, golangci-lint --fix, etc.
   - These fix style issues and code quality problems
   - Run after formatters to avoid conflicts

### Execution Logic

**Test Injection Pattern**: The `run_linters()` and `run_tool()` functions support optional dependency injection via the `run_tool_func` parameter. This allows unit tests to mock tool execution without requiring actual linter installations. In production, omit this parameter to use the default `run_tool()` implementation.

```python
def run_linters(test_files: list, linters: list, project_root: str, run_tool_func: callable = None) -> dict:
    """
    Run detected linters on test files.

    Order of operations:
    1. Run formatters (black, prettier, gofmt, clang-format)
    2. Run linters with auto-fix (eslint --fix, ruff --fix)
    3. Run linters without auto-fix (pylint, mypy)
    4. Collect and report results

    Args:
        test_files: List of absolute paths to test files
        linters: List of detected linter dicts
        project_root: Absolute path to project root
        run_tool_func: Optional callable for test injection (defaults to run_tool)
                       Used by unit tests to mock tool execution

    Returns:
        dict with success status, results, and errors
    """
    results = {
        'success': True,
        'formatters_run': [],
        'linters_run': [],
        'formatted_files': 0,
        'fixed_issues': 0,
        'errors': []
    }

    # Use injected function for testing, otherwise use default
    tool_runner = run_tool_func if run_tool_func else run_tool

    # Separate formatters and linters
    formatters = [l for l in linters if l['tool'] in FORMATTER_TOOLS]
    linters_only = [l for l in linters if l['tool'] not in FORMATTER_TOOLS]

    # 1. Run formatters first
    for formatter in formatters:
        result = tool_runner(formatter, test_files, project_root)
        if result['success']:
            results['formatters_run'].append(formatter['tool'])
            results['formatted_files'] += result['files_modified']
        else:
            results['errors'].append(result['error'])
            results['success'] = False

    # 2. Run linters with auto-fix
    for linter in linters_only:
        if linter['supports_auto_fix']:
            result = tool_runner(linter, test_files, project_root, use_auto_fix=True)
            if result['success']:
                results['linters_run'].append(linter['tool'])
                results['fixed_issues'] += result['issues_fixed']
            else:
                results['errors'].append(result['error'])
                # Don't fail workflow for linting errors (just report)

    # 3. Run linters without auto-fix (check only)
    for linter in linters_only:
        if not linter['supports_auto_fix']:
            result = tool_runner(linter, test_files, project_root, use_auto_fix=False)
            if result['success']:
                results['linters_run'].append(linter['tool'])
                if result['issues_found'] > 0:
                    results['errors'].append(f"{linter['tool']} found {result['issues_found']} issues (manual fix required)")

    return results

FORMATTER_TOOLS = ['black', 'isort', 'autopep8', 'prettier', 'gofmt', 'goimports', 'clang-format', 'dotnet format', 'spotless', 'google-java-format']

def run_tool(linter: dict, test_files: list, project_root: str, use_auto_fix: bool = True) -> dict:
    """
    Execute a single linter/formatter tool.

    Args:
        linter: Linter dict with tool, command, config_path
        test_files: List of test file paths
        project_root: Project root directory
        use_auto_fix: Whether to use auto-fix command (if available)

    Returns:
        dict with success, files_modified, issues_fixed, issues_found
    """
    import subprocess

    # Determine command to run
    if use_auto_fix and linter['supports_auto_fix']:
        command_template = linter['auto_fix_command']
    else:
        command_template = linter['command']

    # Replace {files} placeholder with actual file paths
    file_args = ' '.join(shlex.quote(f) for f in test_files)
    command = command_template.replace('{files}', file_args)

    try:
        # Run command from project root
        result = subprocess.run(
            command,
            shell=True,
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=60
        )

        # Parse output to determine success and metrics
        # (Tool-specific parsing logic)

        return {
            'success': result.returncode == 0,
            'files_modified': len(test_files) if result.returncode == 0 else 0,
            'issues_fixed': parse_issues_fixed(result.stdout, linter['tool']),
            'issues_found': parse_issues_found(result.stdout, linter['tool']),
            'stdout': result.stdout,
            'stderr': result.stderr
        }

    except subprocess.TimeoutExpired:
        return {
            'success': False,
            'error': f"{linter['tool']} timed out after 60 seconds"
        }

    except Exception as e:
        return {
            'success': False,
            'error': f"{linter['tool']} failed: {str(e)}"
        }
```

### Conflict Handling

If multiple formatters detected (e.g., prettier + eslint, black + autopep8):

1. **Use first in priority order** (config file detection wins)
2. **Skip duplicate formatters** (e.g., if both prettier and eslint format, only use prettier)
3. **Log conflict warning** but don't fail workflow

```python
def deduplicate_by_tool_name(linters: list) -> list:
    """
    Deduplicate linters by tool name, keeping first occurrence.

    This ensures highest priority detection method wins.
    """
    seen = set()
    deduplicated = []

    for linter in linters:
        if linter['tool'] not in seen:
            seen.add(linter['tool'])
            deduplicated.append(linter)

    return deduplicated
```

## Error Handling

### No Linters Detected

**Behavior**: Return empty list, no error.

```python
if not detected_linters:
    return {
        'linters_detected': [],
        'lint_results': {
            'success': True,
            'formatters_run': [],
            'linters_run': [],
            'message': 'No linters detected. Tests will not be formatted.'
        }
    }
```

**Rationale**: Linting is optional. If project has no linters, that's OK.

### Tool Not Installed

**Behavior**: Log warning, skip tool, continue with other tools.

```python
def run_tool(linter: dict, test_files: list, project_root: str) -> dict:
    # Check if tool is installed
    if not shutil.which(linter['tool'].split()[0]):
        return {
            'success': False,
            'error': f"⚠️  {linter['tool']} not installed (detected from config but not in PATH). Skipping."
        }

    # Continue with execution...
```

**Rationale**: Tool might be configured but not installed (e.g., in development environment but not CI). Don't block workflow.

### Linting Fails with Errors

**Behavior**: Report errors but don't block workflow completion.

```python
# After running all linters
if results['errors']:
    print(f"⚠️  Linting Issues:\n")
    for error in results['errors']:
        print(f"  - {error}")
    print("\nTests generated successfully, but some linting issues require manual review.")
else:
    print(f"✅ All linters passed! Tests are formatted and compliant.")
```

**Rationale**: Linting errors shouldn't prevent test generation workflow from completing. User can fix linting issues afterward.

### Config File Invalid

**Behavior**: Log warning, skip that config file, continue detection.

```python
try:
    config = parse_config(config_file, language)
except Exception as e:
    logger.warning(f"Failed to parse {config_file}: {e}. Skipping.")
    continue
```

## Usage in Orchestrator

### Integration Point: Phase 7 (Completion)

After fix iterations complete and tests pass:

```python
# Phase 7: Completion and Linting
def phase_7_completion(state: dict, project_root: str):
    """
    Complete workflow with linting and cleanup.

    Steps:
    1. Run linters on generated test files
    2. Display lint results
    3. Run unused code cleanup
    4. Display final summary
    5. Archive state
    """
    print("\n🧹 Phase 7: Code Quality Check\n")

    # Step 1: Detect linters
    language = state['language']
    linters = detect_linters(project_root, language)

    if not linters:
        print("ℹ️  No linters detected. Skipping code quality check.\n")
    else:
        print(f"Detected {len(linters)} linter(s):")
        for linter in linters:
            print(f"  - {linter['tool']} ({linter['detection_method']})")
        print()

        # Step 2: Run linters
        test_files = state['generated_test_files']
        lint_results = run_linters(test_files, linters, project_root)

        # Step 3: Display results
        if lint_results['success']:
            print("✅ Code Quality Check Passed\n")
            print(f"Formatters run: {', '.join(lint_results['formatters_run'])}")
            print(f"Linters run: {', '.join(lint_results['linters_run'])}")
            print(f"Files formatted: {lint_results['formatted_files']}")
            print(f"Issues fixed: {lint_results['fixed_issues']}\n")
        else:
            print("⚠️  Code Quality Check Completed with Issues\n")
            for error in lint_results['errors']:
                print(f"  - {error}")
            print()

    # Continue with unused code cleanup (TASK-011)...
```

## Testing Strategy

### Unit Tests

Test linter detection for each language:

```python
def test_python_linter_detection():
    """Test Python linter detection from pyproject.toml."""
    project_root = create_test_project_with_pyproject_toml()

    linters = detect_linters(project_root, 'python')

    assert len(linters) == 3
    assert any(l['tool'] == 'black' for l in linters)
    assert any(l['tool'] == 'isort' for l in linters)
    assert any(l['tool'] == 'ruff' for l in linters)

def test_javascript_linter_detection():
    """Test JS linter detection from package.json."""
    project_root = create_test_project_with_package_json()

    linters = detect_linters(project_root, 'javascript')

    assert len(linters) == 2
    assert any(l['tool'] == 'prettier' for l in linters)
    assert any(l['tool'] == 'eslint' for l in linters)

def test_no_linters_graceful_fallback():
    """Test graceful handling when no linters detected."""
    project_root = create_empty_test_project()

    linters = detect_linters(project_root, 'python')

    assert linters == []  # Empty list, no error

def test_execution_order_formatters_before_linters():
    """Test that formatters run before linters (TASK-009)."""
    project_root = create_test_project_with_pyproject_toml()
    test_file = os.path.join(project_root, 'tests', 'test_example.py')

    # Create test file with both formatting and linting issues
    with open(test_file, 'w') as f:
        f.write('import sys\nx=1+2\n')  # No space around operator (needs black and ruff)

    # Mock linters: black (formatter) and ruff (linter)
    linters = [
        {'tool': 'black', 'supports_auto_fix': True, 'auto_fix_command': 'black {files}'},
        {'tool': 'ruff', 'supports_auto_fix': True, 'auto_fix_command': 'ruff check --fix {files}'}
    ]

    # Track execution order
    execution_order = []

    def mock_run_tool(linter, files, root, use_auto_fix=True):
        execution_order.append(linter['tool'])
        return {'success': True, 'files_modified': 1, 'issues_fixed': 0}

    # Run linters with mocked execution
    results = run_linters([test_file], linters, project_root, run_tool_func=mock_run_tool)

    # Verify formatters ran before linters
    assert execution_order == ['black', 'ruff'], f"Expected ['black', 'ruff'], got {execution_order}"
    assert execution_order.index('black') < execution_order.index('ruff'), "Formatter must run before linter"

def test_conflict_handling_multiple_formatters():
    """Test conflict handling when multiple formatters detected (TASK-009)."""
    # Test deduplication directly with conflicting formatters
    linters_with_duplicates = [
        {'tool': 'black', 'detection_method': 'config_file', 'supports_auto_fix': True},
        {'tool': 'autopep8', 'detection_method': 'package_script', 'supports_auto_fix': True},
        {'tool': 'black', 'detection_method': 'ci_cd', 'supports_auto_fix': True},  # duplicate
        {'tool': 'isort', 'detection_method': 'config_file', 'supports_auto_fix': True}  # not conflicting
    ]

    # Apply deduplication (simulates behavior in detect_linters)
    deduplicated = deduplicate_by_tool_name(linters_with_duplicates)

    # Expected behavior: deduplication keeps first occurrence (highest priority)
    assert len(deduplicated) == 3, f"Expected 3 unique tools, got {len(deduplicated)}"

    # Verify black kept (first occurrence)
    black_linters = [l for l in deduplicated if l['tool'] == 'black']
    assert len(black_linters) == 1, "Should have exactly one black formatter"
    assert black_linters[0]['detection_method'] == 'config_file', "First detection (config_file) should win"

    # Verify autopep8 kept (not duplicate of black, different tool)
    autopep8_linters = [l for l in deduplicated if l['tool'] == 'autopep8']
    assert len(autopep8_linters) == 1, "Should have exactly one autopep8 formatter"

    # Verify isort kept (import sorter, not conflicting with code formatters)
    isort_linters = [l for l in deduplicated if l['tool'] == 'isort']
    assert len(isort_linters) == 1, "Should have exactly one isort formatter"

    # Verify no duplicate black entries
    assert len([l for l in deduplicated if l['tool'] == 'black']) == 1, "Duplicate black should be removed"

def test_auto_fix_flags_applied():
    """Test that auto-fix flags are correctly applied (TASK-009)."""
    project_root = create_test_project_with_pyproject_toml()
    test_file = os.path.join(project_root, 'tests', 'test_example.py')

    # Create linters with auto-fix support
    linters = [
        {
            'tool': 'ruff',
            'supports_auto_fix': True,
            'command': 'ruff check {files}',
            'auto_fix_command': 'ruff check --fix {files}'
        },
        {
            'tool': 'pylint',
            'supports_auto_fix': False,
            'command': 'pylint {files}',
            'auto_fix_command': None
        }
    ]

    # Track which commands were executed
    executed_commands = []

    def mock_run_tool(linter, files, root, use_auto_fix=True):
        if use_auto_fix and linter['supports_auto_fix']:
            executed_commands.append(linter['auto_fix_command'])
        else:
            executed_commands.append(linter['command'])
        return {'success': True, 'files_modified': 1, 'issues_fixed': 2, 'issues_found': 0}

    # Run linters
    results = run_linters([test_file], linters, project_root, run_tool_func=mock_run_tool)

    # Verify auto-fix command used for ruff (supports_auto_fix=True)
    assert 'ruff check --fix {files}' in executed_commands, "Auto-fix flag should be used for ruff"

    # Verify regular command used for pylint (supports_auto_fix=False)
    assert 'pylint {files}' in executed_commands, "Regular command should be used for pylint"
    assert 'pylint --fix {files}' not in executed_commands, "Auto-fix should not be used for pylint"
```

### Integration Tests

Test full linting workflow:

```python
def test_linting_workflow_python():
    """Test full linting workflow for Python project."""
    # Setup: Create project with pyproject.toml
    project_root = create_test_project_with_pyproject_toml()

    # Create test files with formatting issues
    test_file = os.path.join(project_root, 'tests', 'test_example.py')
    with open(test_file, 'w') as f:
        f.write('import sys\nimport os\n\ndef test_example( ):\n    assert 1==1')  # Bad formatting

    # Detect linters
    linters = detect_linters(project_root, 'python')

    # Run linters
    results = run_linters([test_file], linters, project_root)

    # Verify results
    assert results['success'] == True
    assert 'black' in results['formatters_run']
    assert 'isort' in results['formatters_run']
    assert results['formatted_files'] > 0

    # Verify file was formatted
    with open(test_file, 'r') as f:
        content = f.read()

    assert 'def test_example():' in content  # Proper spacing
    assert 'assert 1 == 1' in content  # Proper spacing
```

## Unused Code Cleanup (Phase 6.5a - TASK-011)

### Overview

After fix iterations complete, automatically detect and remove unused imports and variables from generated test files. This cleanup ensures test files are clean and maintainable, removing debugging artifacts left by the Fix Agent.

### Safety

**Critical**: Only clean test files written in the current session.

```python
def cleanup_unused_code(test_files: list, language: str, project_root: str, generated_test_files: list) -> dict:
    """
    Detect and remove unused code from test files.

    Safety: Only clean files in generated_test_files list from state.

    Args:
        test_files: List of test file paths to clean
        language: Programming language
        project_root: Project root directory
        generated_test_files: List of files generated this session (from state)

    Returns:
        dict with cleanup results
    """
    # Safety check: Only clean generated files
    safe_files = [f for f in test_files if f in generated_test_files]

    if len(safe_files) < len(test_files):
        skipped_count = len(test_files) - len(safe_files)
        print(f"⚠️  Skipped {skipped_count} file(s) not in generated_test_files (safety check)")

    if not safe_files:
        return {
            'success': True,
            'files_cleaned': 0,
            'imports_removed': 0,
            'variables_removed': 0,
            'message': 'No generated test files to clean'
        }

    # Proceed with cleanup on safe files
    return cleanup_unused_code_internal(safe_files, language, project_root)
```

### Detection Patterns by Language

#### Python

**Tools**: pyflakes, ruff F401/F841, autoflake

**Detection**:
```python
def detect_unused_code_python(test_files: list, project_root: str) -> dict:
    """
    Detect unused imports and variables in Python test files.

    Uses:
    - ruff check --select F401,F841 (unused imports and variables)
    - pyflakes (fallback if ruff not available)
    - autoflake (for automatic removal)
    """
    detected = {
        'unused_imports': [],
        'unused_variables': []
    }

    # Try ruff first (fastest and most accurate)
    try:
        import subprocess
        result = subprocess.run(
            ['ruff', 'check', '--select', 'F401,F841', '--output-format', 'json'] + test_files,
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode == 0 or result.stdout:
            import json
            issues = json.loads(result.stdout)

            for issue in issues:
                if issue['code'] == 'F401':  # Unused import
                    detected['unused_imports'].append({
                        'file': issue['filename'],
                        'line': issue['location']['row'],
                        'name': issue['message'].split("'")[1]
                    })
                elif issue['code'] == 'F841':  # Unused variable
                    detected['unused_variables'].append({
                        'file': issue['filename'],
                        'line': issue['location']['row'],
                        'name': issue['message'].split("'")[1]
                    })

    except (FileNotFoundError, subprocess.TimeoutExpired, Exception):
        # Fallback to pyflakes if ruff unavailable
        try:
            import subprocess
            for test_file in test_files:
                result = subprocess.run(
                    ['pyflakes', test_file],
                    capture_output=True,
                    text=True,
                    timeout=10
                )

                # Parse pyflakes output
                for line in result.stdout.splitlines():
                    if 'imported but unused' in line:
                        detected['unused_imports'].append(parse_pyflakes_line(line))
                    elif 'assigned to but never used' in line:
                        detected['unused_variables'].append(parse_pyflakes_line(line))

        except (FileNotFoundError, Exception):
            # Both tools unavailable - skip detection
            pass

    return detected
```

**Removal**:
```python
def remove_unused_code_python(test_files: list, detected: dict, project_root: str) -> dict:
    """
    Remove unused imports and variables from Python files.

    Uses autoflake for automatic removal with safety checks.
    """
    results = {
        'files_cleaned': 0,
        'imports_removed': 0,
        'variables_removed': 0
    }

    # Try autoflake for safe automatic removal
    try:
        import subprocess
        result = subprocess.run(
            [
                'autoflake',
                '--in-place',
                '--remove-all-unused-imports',
                '--remove-unused-variables'
            ] + test_files,
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode == 0:
            results['files_cleaned'] = len(test_files)
            results['imports_removed'] = len(detected['unused_imports'])
            results['variables_removed'] = len(detected['unused_variables'])

    except (FileNotFoundError, subprocess.TimeoutExpired, Exception) as e:
        # If autoflake not available, try ruff --fix
        try:
            subprocess.run(
                ['ruff', 'check', '--select', 'F401,F841', '--fix'] + test_files,
                cwd=project_root,
                capture_output=True,
                timeout=30
            )
            results['files_cleaned'] = len(test_files)
            results['imports_removed'] = len(detected['unused_imports'])
            results['variables_removed'] = len(detected['unused_variables'])

        except Exception:
            # Both tools unavailable - return without cleanup
            pass

    return results
```

#### JavaScript/TypeScript

**Tools**: eslint no-unused-vars

**Detection**:
```python
def detect_unused_code_js_ts(test_files: list, project_root: str) -> dict:
    """
    Detect unused imports and variables in JS/TS test files.

    Uses eslint with no-unused-vars rule.
    """
    detected = {
        'unused_imports': [],
        'unused_variables': []
    }

    try:
        import subprocess
        result = subprocess.run(
            ['npx', 'eslint', '--format', 'json', '--rule', 'no-unused-vars:error'] + test_files,
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=30
        )

        import json
        results = json.loads(result.stdout)

        for file_result in results:
            for message in file_result.get('messages', []):
                if message['ruleId'] == 'no-unused-vars':
                    # Distinguish imports vs variables
                    if 'import' in message.get('message', '').lower():
                        detected['unused_imports'].append({
                            'file': file_result['filePath'],
                            'line': message['line'],
                            'name': message.get('message', '').split("'")[1]
                        })
                    else:
                        detected['unused_variables'].append({
                            'file': file_result['filePath'],
                            'line': message['line'],
                            'name': message.get('message', '').split("'")[1]
                        })

    except (FileNotFoundError, Exception):
        pass

    return detected
```

**Removal**:
```python
def remove_unused_code_js_ts(test_files: list, project_root: str) -> dict:
    """
    Remove unused code from JS/TS files using eslint --fix.
    """
    try:
        import subprocess
        subprocess.run(
            ['npx', 'eslint', '--fix', '--rule', 'no-unused-vars:error'] + test_files,
            cwd=project_root,
            capture_output=True,
            timeout=30
        )

        return {'files_cleaned': len(test_files)}

    except Exception:
        return {'files_cleaned': 0}
```

#### Java

**Tools**: javac unused import warnings

**Detection**:
```python
def detect_unused_code_java(test_files: list, project_root: str) -> dict:
    """
    Detect unused imports in Java test files.

    Uses javac compiler warnings or IDE analyzers.
    Note: Java unused variable warnings are limited (only local variables).
    """
    detected = {
        'unused_imports': [],
        'unused_variables': []
    }

    # Try compiling with Xlint:all to get unused import warnings
    try:
        import subprocess
        result = subprocess.run(
            ['javac', '-Xlint:all'] + test_files,
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=30
        )

        # Parse compiler warnings
        for line in result.stderr.splitlines():
            if 'is never used' in line and 'import' in line:
                detected['unused_imports'].append(parse_javac_warning(line))

    except (FileNotFoundError, Exception):
        pass

    return detected
```

**Removal**:
```python
def remove_unused_code_java(test_files: list, project_root: str) -> dict:
    """
    Remove unused imports from Java files.

    Uses IDE formatter or manual AST manipulation.
    Note: This is limited - recommend using IDE's "Optimize Imports" feature.
    """
    # Java unused import removal is best done by IDE tools
    # For automated cleanup, we'd need to parse and rewrite files
    # Return graceful no-op
    return {
        'files_cleaned': 0,
        'message': 'Java unused import removal requires IDE tooling (use "Optimize Imports" in IDE)'
    }
```

#### C#

**Tools**: Roslyn analyzers CS0105 (unused using), CS0168/CS0219 (unused variable)

**Detection**:
```python
def detect_unused_code_csharp(test_files: list, project_root: str) -> dict:
    """
    Detect unused code in C# test files.

    Uses Roslyn analyzers via dotnet build diagnostics.
    """
    detected = {
        'unused_imports': [],
        'unused_variables': []
    }

    try:
        import subprocess
        # Build with diagnostics to detect unused code
        result = subprocess.run(
            ['dotnet', 'build', '/p:TreatWarningsAsErrors=false'],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=60
        )

        # Parse diagnostics
        for line in result.stdout.splitlines():
            if 'CS0105' in line:  # Unused using directive
                detected['unused_imports'].append(parse_csharp_diagnostic(line))
            elif 'CS0168' in line or 'CS0219' in line:  # Unused variable
                detected['unused_variables'].append(parse_csharp_diagnostic(line))

    except (FileNotFoundError, Exception):
        pass

    return detected
```

**Removal**:
```python
def remove_unused_code_csharp(test_files: list, project_root: str) -> dict:
    """
    Remove unused code from C# files using dotnet format.
    """
    try:
        import subprocess
        subprocess.run(
            ['dotnet', 'format', '--include'] + test_files,
            cwd=project_root,
            capture_output=True,
            timeout=30
        )

        return {'files_cleaned': len(test_files)}

    except Exception:
        return {'files_cleaned': 0}
```

#### Go

**Tools**: goimports (auto-removes unused imports), go compiler (unused variable detection)

**Detection & Removal**:
```python
def detect_and_remove_unused_code_go(test_files: list, project_root: str) -> dict:
    """
    Detect and remove unused code in Go test files.

    Go is special: goimports automatically removes unused imports.
    Unused variables are compilation errors, so they must be removed to compile.
    """
    results = {
        'files_cleaned': 0,
        'imports_removed': 0,
        'variables_removed': 0
    }

    # Run goimports -w to remove unused imports automatically
    try:
        import subprocess
        result = subprocess.run(
            ['goimports', '-w'] + test_files,
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode == 0:
            results['files_cleaned'] = len(test_files)
            # goimports output doesn't tell us how many imports removed
            # Just report success

    except FileNotFoundError:
        # goimports not available, fallback to gofmt
        try:
            subprocess.run(
                ['gofmt', '-w'] + test_files,
                cwd=project_root,
                capture_output=True,
                timeout=30
            )
            results['files_cleaned'] = len(test_files)
        except Exception:
            pass

    except Exception:
        pass

    return results
```

**Note**: Go unused variables are compilation errors, not warnings. If tests compile, there are no unused variables. goimports handles unused imports automatically.

#### C++

**Tools**: clang-tidy misc-unused-*, readability-redundant-declaration

**Detection**:
```python
def detect_unused_code_cpp(test_files: list, project_root: str) -> dict:
    """
    Detect unused code in C++ test files.

    Uses clang-tidy with unused checks.
    Note: C++ unused header detection requires complex dependency analysis.
    """
    detected = {
        'unused_imports': [],  # C++ uses #include, not imports
        'unused_variables': []
    }

    try:
        import subprocess
        result = subprocess.run(
            [
                'clang-tidy',
                '--checks=misc-unused-*,readability-redundant-declaration',
                '--format-style=file'
            ] + test_files + ['--'],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=60
        )

        # Parse clang-tidy output
        for line in result.stdout.splitlines():
            if 'misc-unused-' in line:
                detected['unused_variables'].append(parse_clang_tidy_line(line))
            elif 'readability-redundant-declaration' in line:
                detected['unused_imports'].append(parse_clang_tidy_line(line))

    except (FileNotFoundError, Exception):
        pass

    return detected
```

**Removal**:
```python
def remove_unused_code_cpp(test_files: list, project_root: str) -> dict:
    """
    Remove unused code from C++ files using clang-tidy --fix.

    Note: Header analysis is conservative to avoid breaking compilation.
    """
    try:
        import subprocess
        subprocess.run(
            [
                'clang-tidy',
                '--checks=misc-unused-*,readability-redundant-declaration',
                '--fix'
            ] + test_files + ['--'],
            cwd=project_root,
            capture_output=True,
            timeout=60
        )

        return {'files_cleaned': len(test_files)}

    except Exception:
        return {'files_cleaned': 0}
```

**Important**: C++ unused `#include` detection requires header dependency analysis. If uncertain, preserve includes to avoid compilation errors.

### Unified Cleanup Interface

```python
def cleanup_unused_code(test_files: list, language: str, project_root: str, generated_test_files: list) -> dict:
    """
    Unified interface for unused code cleanup across all languages.

    Safety: Only cleans files in generated_test_files list.

    Returns:
        {
            'success': True/False,
            'files_cleaned': int,
            'imports_removed': int,
            'variables_removed': int,
            'errors': [str]
        }
    """
    # Safety check
    safe_files = [f for f in test_files if f in generated_test_files]

    if not safe_files:
        return {
            'success': True,
            'files_cleaned': 0,
            'imports_removed': 0,
            'variables_removed': 0,
            'message': 'No generated test files to clean'
        }

    try:
        if language == 'python':
            detected = detect_unused_code_python(safe_files, project_root)
            results = remove_unused_code_python(safe_files, detected, project_root)

        elif language in ['javascript', 'typescript']:
            detected = detect_unused_code_js_ts(safe_files, project_root)
            results = remove_unused_code_js_ts(safe_files, project_root)
            # Add counts from detection
            results['imports_removed'] = len(detected['unused_imports'])
            results['variables_removed'] = len(detected['unused_variables'])

        elif language == 'java':
            detected = detect_unused_code_java(safe_files, project_root)
            results = remove_unused_code_java(safe_files, project_root)
            results['imports_removed'] = len(detected['unused_imports'])

        elif language == 'csharp':
            detected = detect_unused_code_csharp(safe_files, project_root)
            results = remove_unused_code_csharp(safe_files, project_root)
            results['imports_removed'] = len(detected['unused_imports'])
            results['variables_removed'] = len(detected['unused_variables'])

        elif language == 'go':
            results = detect_and_remove_unused_code_go(safe_files, project_root)

        elif language == 'cpp':
            detected = detect_unused_code_cpp(safe_files, project_root)
            results = remove_unused_code_cpp(safe_files, project_root)
            results['imports_removed'] = len(detected['unused_imports'])
            results['variables_removed'] = len(detected['unused_variables'])

        else:
            return {
                'success': False,
                'errors': [f'Unsupported language for cleanup: {language}']
            }

        results['success'] = True
        return results

    except Exception as e:
        return {
            'success': False,
            'files_cleaned': 0,
            'errors': [f'Cleanup failed: {str(e)}']
        }
```

### Integration with Phase 7

Unused code cleanup runs in Phase 7, **after linting** and **before final summary**:

```python
# Phase 7, Step 2: Unused Code Cleanup (after Step 1: Linting)

# Display cleanup phase start
print("\n🧹 Cleaning up unused code...")

# Get generated test files from state (safety check)
generated_test_files = state.get('generated_test_files', [])

if not generated_test_files:
    print("ℹ️  No generated test files tracked in state. Skipping cleanup.")
else:
    # Run cleanup
    cleanup_results = cleanup_unused_code(
        test_files=generated_test_files,
        language=state['language'],
        project_root=state['project_root'],
        generated_test_files=generated_test_files  # Safety list
    )

    # Display results
    if cleanup_results['success']:
        if cleanup_results['files_cleaned'] > 0:
            print(f"✅ Unused Code Cleanup Complete")
            print(f"   Files Cleaned: {cleanup_results['files_cleaned']}")
            if cleanup_results.get('imports_removed', 0) > 0:
                print(f"   Imports Removed: {cleanup_results['imports_removed']}")
            if cleanup_results.get('variables_removed', 0) > 0:
                print(f"   Variables Removed: {cleanup_results['variables_removed']}")
        else:
            print("ℹ️  No unused code detected.")
    else:
        # Non-blocking: Log errors but continue workflow
        print(f"⚠️  Cleanup encountered issues (non-blocking):")
        for error in cleanup_results.get('errors', []):
            print(f"     - {error}")

    # Save cleanup results to state
    state['cleanup_results'] = cleanup_results
    save_state(state, state['project_root'])
```

### Error Handling

1. **Tool not available**: Graceful fallback, log warning, continue workflow
2. **Cleanup fails**: Log error, continue workflow (non-blocking)
3. **No generated files**: Skip cleanup, log informational message
4. **Safety check fails**: Only clean files in generated_test_files list

### Testing Strategy

```python
def test_cleanup_python():
    """Test Python unused code cleanup."""
    # Create test file with unused imports and variables
    test_file = create_test_file_with_unused_code_python()

    # Run cleanup
    results = cleanup_unused_code(
        test_files=[test_file],
        language='python',
        project_root=project_root,
        generated_test_files=[test_file]
    )

    # Verify cleanup
    assert results['success'] == True
    assert results['files_cleaned'] == 1
    assert results['imports_removed'] > 0

    # Verify file is clean
    with open(test_file, 'r') as f:
        content = f.read()
    assert 'import unused_module' not in content

def test_cleanup_safety():
    """Test that cleanup only affects generated test files."""
    generated_file = create_test_file('generated.py')
    existing_file = create_test_file('existing.py')

    # Run cleanup with only generated file in safe list
    results = cleanup_unused_code(
        test_files=[generated_file, existing_file],
        language='python',
        project_root=project_root,
        generated_test_files=[generated_file]  # Only generated file
    )

    # Verify only generated file was cleaned
    assert results['files_cleaned'] <= 1
```

## Future Enhancements

- **Custom linter configurations**: Allow user to override detected linters via config file
- **Linter version detection**: Detect and report linter versions
- **Parallel execution**: Run multiple linters in parallel for faster execution
- **Incremental linting**: Only lint modified files (not entire test suite)
- **Custom lint rules**: Support project-specific custom lint rules
- **Lint result caching**: Cache lint results to avoid re-running on unchanged files
- **Unused code detection improvements**: Better detection for all languages, especially Java and C++
- **Dead code elimination**: Detect and remove unreachable code blocks

## References

- Dante's linting implementation (if exists): `dante/src/dante/linting/`
- Language linter documentation:
  - Python: black, isort, ruff, pylint, flake8, mypy, autoflake, pyflakes
  - JavaScript/TypeScript: prettier, eslint, tslint
  - Java: spotless, google-java-format, checkstyle
  - C#: dotnet format, Roslyn analyzers
  - Go: gofmt, goimports, golangci-lint
  - C++: clang-format, clang-tidy

---

**Last Updated**: 2026-01-13
**Status**: Phase 6.5a - TASK-008, TASK-009, TASK-011 Complete
**Integration**: Ready for TASK-010 (Orchestrator Integration) - Linting and Unused Code Cleanup
