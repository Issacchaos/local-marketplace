# Installation Guide: Automated Testing Plugin for Claude Code

---

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [GitHub SSH Setup](#github-ssh-setup)
4. [Claude Code CLI Plugin Directory](#claude-code-cli-plugin-directory)
5. [Installation Methods](#installation-methods)
6. [Verification](#verification)
7. [First Test](#first-test)
8. [Troubleshooting](#troubleshooting)

---

## Overview

This guide walks you through installing the Automated Testing Plugin for Claude Code. The plugin adds four powerful testing commands to Claude Code:

- `/test-analyze` - Analyze code and identify testing targets
- `/test-generate` - Fully automated test generation with auto-heal
- `/test-loop` - Interactive testing workflow with approval gates
- `/test-resume` - Resume interrupted workflows

**Supported Languages**: Python, JavaScript, TypeScript, Java, C#, Go, C++ (7 languages fully supported)

**Installation time**: 5-10 minutes (first time), 2 minutes (if SSH already configured)

---

## Quick Installation (TL;DR)

**If you already have Claude Code CLI and SSH configured**:

```bash
# 1. Navigate to plugins directory
cd ~/.claude/plugins  # macOS/Linux
cd $env:USERPROFILE\.claude\plugins  # Windows PowerShell

# 2. Clone the repository
git clone git@github.example.com:my-org/my-plugin.git automated-testing-plugin

# 3. Restart Claude Code
# Close and reopen Claude Code

# 4. Verify installation
# In Claude Code, type: /test<Tab>
# Should show: /test-analyze, /test-generate, /test-loop, /test-resume
```

Done! ✅

**If you need to set up SSH or Claude Code CLI first**, continue reading below.

---

## Prerequisites

### Required

1. **Claude Code CLI** (Latest version)
   - Install from: https://docs.claude.com/claude-code
   - Verify installation: `claude --version`
   - **Important**: Claude Code CLI must be installed and working before installing plugins

2. **Git** (for cloning the repository)
   - Download from: https://git-scm.com/downloads
   - Verify installation: `git --version`

3. **GitHub SSH Access** (for cloning from GitHub Enterprise)
   - See [GitHub SSH Setup](#github-ssh-setup) below for detailed instructions
   - Required for Method 2 (Clone Repository)

4. **Language-specific requirements** (depending on your project)
   - **Python 3.8+**: pytest (`pip install pytest`)
   - **JavaScript/TypeScript**: Jest, Vitest, or Mocha (`npm install jest`)
   - **Java**: JUnit 4/5 or TestNG (Maven or Gradle)
   - **C#**: xUnit, NUnit, or MSTest (.NET CLI)
   - **Go**: Built-in testing package (no installation needed)
   - **C++**: Google Test or Catch2 (CMake)

### Optional but Recommended

- **pytest-cov** (for coverage reporting): `pip install pytest-cov`
- **pytest-mock** (for mocking support): `pip install pytest-mock`

---

## GitHub SSH Setup

Before you can clone the plugin repository from GitHub Enterprise, you need to set up SSH authentication.

### Step 1: Check for Existing SSH Keys

```bash
# Windows (PowerShell), macOS, or Linux
ls ~/.ssh/

# Look for files like:
# - id_rsa.pub (public key)
# - id_rsa (private key)
# - id_ed25519.pub (newer format public key)
# - id_ed25519 (newer format private key)
```

If you see these files, you already have SSH keys. Skip to [Step 3: Add SSH Key to GitHub](#step-3-add-ssh-key-to-github).

### Step 2: Generate New SSH Key

If you don't have SSH keys, generate them:

```bash
# Generate SSH key (replace with your email)
ssh-keygen -t ed25519 -C "your.name@example.com"

# When prompted:
# - "Enter file in which to save the key": Press Enter (default location)
# - "Enter passphrase": Enter a passphrase or press Enter for none
# - "Enter same passphrase again": Re-enter passphrase or press Enter

# Start SSH agent
# Windows (PowerShell)
Start-Service ssh-agent

# macOS/Linux
eval "$(ssh-agent -s)"

# Add your SSH key to the agent
ssh-add ~/.ssh/id_ed25519
```

### Step 3: Add SSH Key to GitHub

1. **Copy your public SSH key**:
   ```bash
   # Windows (PowerShell)
   Get-Content ~/.ssh/id_ed25519.pub | Set-Clipboard

   # macOS
   pbcopy < ~/.ssh/id_ed25519.pub

   # Linux
   cat ~/.ssh/id_ed25519.pub
   # Then manually copy the output
   ```

2. **Add key to GitHub**:
   - Go to: https://github.example.com/settings/keys
   - Click **"New SSH key"** or **"Add SSH key"**
   - Title: "My Laptop" or descriptive name
   - Key type: **Authentication Key**
   - Paste your public key into the "Key" field
   - Click **"Add SSH key"**

3. **Verify SSH connection**:
   ```bash
   ssh -T git@github.example.com

   # Expected output:
   # Hi username! You've successfully authenticated, but GitHub does not provide shell access.
   ```

If you see the success message, SSH is configured correctly! ✅

### Troubleshooting SSH

**Issue**: "Permission denied (publickey)"
- **Solution**: Your SSH key isn't added to GitHub. Follow Step 3 above.

**Issue**: "Could not resolve hostname github.example.com"
- **Solution**: Check your internet connection and Epic VPN if required.

**Issue**: SSH agent not running (Windows)
- **Solution**: Run PowerShell as Administrator:
  ```powershell
  Set-Service ssh-agent -StartupType Automatic
  Start-Service ssh-agent
  ```

---

## Claude Code CLI Plugin Directory

Before installing, you need to know where Claude Code stores plugins.

### Finding the Plugin Directory

**Default Locations**:
- **Windows**: `%USERPROFILE%\.claude\plugins\`
  - Example: `C:\Users\YourName\.claude\plugins\`
- **macOS**: `~/.claude/plugins/`
  - Example: `/Users/YourName/.claude/plugins/`
- **Linux**: `~/.claude/plugins/`
  - Example: `/home/yourname/.claude/plugins/`

### Creating the Plugin Directory

If the directory doesn't exist, create it:

```bash
# Windows (PowerShell)
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.claude\plugins"

# macOS/Linux
mkdir -p ~/.claude/plugins
```

### Verifying Claude Code Installation

Before installing plugins, verify Claude Code CLI is installed and configured:

```bash
# Check Claude Code version
claude --version

# Check Claude Code can run
claude --help

# If these commands fail, Claude Code CLI is not installed correctly
# Install from: https://docs.claude.com/claude-code
```

---

## Installation Methods

Choose the method that works best for you:

### Method 1: Claude Code Marketplace (Recommended)

Best for: Quick installation, automatic updates, one-click setup

**Note**: This method requires access to the internal Claude Code marketplace.

```bash
# 1. Open Claude Code CLI
claude

# 2. In Claude Code, type:
/plugins search automated-testing-plugin

# 3. Install the plugin
/plugins install automated-testing-plugin

# 4. Restart Claude Code
# Close and reopen Claude Code
```

**Or via Claude Code GUI** (if available):
1. Open Claude Code
2. Go to **Extensions** or **Plugins** marketplace
3. Search for "Automated Testing Plugin"
4. Click **Install**
5. Restart Claude Code

**Verification**:
```bash
# After restart, verify commands are available
# Type: /test<Tab>
# Should show: /test-analyze, /test-generate, /test-loop, /test-resume
```

### Method 2: Clone Repository via SSH (Recommended for Development)

Best for: Development, staying updated, contributing back, trying latest features

**Prerequisites**:
- ✅ Git installed
- ✅ GitHub SSH key configured (see [GitHub SSH Setup](#github-ssh-setup) above)
- ✅ Claude Code CLI installed and plugins directory exists

**Step-by-Step Installation**:

```bash
# Step 1: Verify SSH access to GitHub (optional but recommended)
ssh -T git@github.example.com
# Expected: "Hi username! You've successfully authenticated..."

# Step 2: Navigate to your Claude Code plugins directory
# Windows (PowerShell)
cd $env:USERPROFILE\.claude\plugins

# macOS/Linux
cd ~/.claude/plugins

# Step 3: Clone the plugin repository using SSH
git clone git@github.example.com:my-org/my-plugin.git automated-testing-plugin

# Alternative: Clone using HTTPS (if SSH not configured)
# git clone https://github.example.com/my-org/my-plugin.git automated-testing-plugin

# Step 4: Navigate into the plugin directory
cd automated-testing-plugin

# Step 5: Verify the plugin structure
# Windows (PowerShell)
dir .claude-plugin

# macOS/Linux
ls .claude-plugin/

# Should see: README.md, agents/, commands/, skills/, subagents/, templates/

# Step 6: Restart Claude Code
# Close all Claude Code instances and restart
```

**Verification**:
```bash
# After restarting Claude Code, open it and type:
# /test<Tab>

# Should autocomplete to show:
# - /test-analyze
# - /test-generate
# - /test-loop
# - /test-resume
```

If you see these commands, installation successful! ✅

**Keeping Updated**:
```bash
# Navigate to plugin directory
cd ~/.claude/plugins/automated-testing-plugin  # macOS/Linux
cd $env:USERPROFILE\.claude\plugins\automated-testing-plugin  # Windows

# Pull latest changes
git pull origin main

# Restart Claude Code to load updates
```

### Method 3: Download and Copy

Best for: Quick setup, no Git required

**Step 1: Download the plugin**

Option A - Download ZIP:
```bash
# Download from GitHub
# https://github.example.com/my-org/my-plugin/archive/refs/heads/feature/phase1-python-pytest-mvp.zip

# Extract to a temporary location
unzip dante_plugin-feature-phase1-python-pytest-mvp.zip
```

Option B - Manual download:
- Go to: https://github.example.com/my-org/my-plugin
- Click "Code" → "Download ZIP"
- Extract to a folder

**Step 2: Copy to Claude Code plugins directory**

```bash
# Windows
xcopy /E /I dante_plugin %USERPROFILE%\.claude\plugins\automated-testing-plugin

# macOS/Linux
cp -r dante_plugin ~/.claude/plugins/automated-testing-plugin
```

**Step 3: Verify**

```bash
# Windows
dir %USERPROFILE%\.claude\plugins\automated-testing-plugin\.claude-plugin\

# macOS/Linux
ls ~/.claude/plugins/automated-testing-plugin/.claude-plugin/
```

### Method 4: Symlink (For Advanced Development)

Best for: Plugin development, testing changes

```bash
# 1. Clone repository to your development location
git clone https://github.example.com/my-org/my-plugin.git ~/dev/dante_plugin

# 2. Create symlink in Claude Code plugins directory
# Windows (Run as Administrator)
mklink /D %USERPROFILE%\.claude\plugins\automated-testing-plugin %USERPROFILE%\dev\dante_plugin

# macOS/Linux
ln -s ~/dev/dante_plugin ~/.claude/plugins/automated-testing-plugin

# 3. Verify symlink
# Windows
dir %USERPROFILE%\.claude\plugins\automated-testing-plugin

# macOS/Linux
ls -la ~/.claude/plugins/automated-testing-plugin
```

---

## Verification

### Step 1: Verify Plugin Structure

```bash
# Navigate to plugin directory
cd ~/.claude/plugins/automated-testing-plugin  # macOS/Linux
cd %USERPROFILE%\.claude\plugins\automated-testing-plugin  # Windows

# Check directory structure
ls -R .claude-plugin/  # macOS/Linux
dir /S .claude-plugin\  # Windows
```

**Expected structure**:
```
.claude-plugin/
├── README.md
├── agents/
│   ├── analyze-agent.md
│   ├── execute-agent.md
│   ├── validate-agent.md
│   └── write-agent.md
├── commands/
│   ├── test-analyze.md
│   ├── test-generate.md
│   ├── test-loop.md
│   └── test-resume.md
├── skills/
│   ├── framework-detection.md
│   ├── test-generation.md
│   ├── result-parsing.md
│   └── code-analysis.md
├── subagents/
│   └── test-loop-orchestrator.md
└── templates/
    └── pytest-template.md
```

### Step 2: Restart Claude Code

```bash
# Close all Claude Code instances
# Then restart Claude Code
claude
```

### Step 3: Verify Commands Are Available

Open Claude Code and type `/test` then press Tab to see autocomplete suggestions.

**Expected commands to appear**:
- `/test-analyze`
- `/test-generate`
- `/test-loop`
- `/test-resume`

If commands appear, installation is successful! ✅

---

## First Test

Let's verify the plugin works by testing the included example project.

### Quick Test (2 Minutes)

```bash
# 1. Navigate to the example Python calculator
cd ~/.claude/plugins/automated-testing-plugin/examples/python-calculator

# Windows
cd %USERPROFILE%\.claude\plugins\automated-testing-plugin\examples\python-calculator

# 2. Install dependencies
pip install -r requirements.txt

# 3. Open Claude Code in this directory
claude

# 4. Run your first command
/test-analyze src/calculator.py
```

**Expected output**:
```
🔍 Analysis Complete

Language: Python
Framework: pytest

Test Targets (4):
  1. add(a, b) - Priority: High
  2. subtract(a, b) - Priority: High
  3. multiply(a, b) - Priority: High
  4. divide(a, b) - Priority: High (Has error handling)

Recommendations:
  - Start with divide() (includes error handling)
  - All functions are good candidates for unit tests
  - pytest detected and configured
```

If you see this output, the plugin is working! ✅

### Full Test (5 Minutes)

```bash
# Generate and run tests automatically
/test-generate src/calculator.py
```

**Expected behavior**:
1. Analyzes calculator.py ✅
2. Generates test plan ✅
3. Generates test code ✅
4. Executes tests ✅
5. Shows results ✅

**Expected results**:
- Test file created: `.claude-tests/test_calculator.py`
- Tests generated: 8-16 tests
- All tests pass (or mostly pass)

---

## Troubleshooting

### Issue 1: Commands Not Appearing

**Symptom**: `/test-analyze` shows "Unknown command"

**Solutions**:

1. **Verify plugin directory location**:
   ```bash
   # Should be in this exact location
   ls ~/.claude/plugins/automated-testing-plugin/.claude-plugin/  # macOS/Linux
   dir %USERPROFILE%\.claude\plugins\automated-testing-plugin\.claude-plugin\  # Windows
   ```

2. **Check directory name**: Plugin directory must be named correctly
   - ✅ Good: `automated-testing-plugin/`
   - ❌ Bad: `dante_plugin/`, `testing-plugin/`

3. **Restart Claude Code**: Close all instances and restart

4. **Check Claude Code version**: Ensure you have the latest version
   ```bash
   claude --version
   ```

5. **Check plugin configuration**: Verify `.claude-plugin/` directory exists at the root

### Issue 2: Plugin Directory Not Found

**Symptom**: `~/.claude/plugins/` doesn't exist

**Solution**: Create the directory manually
```bash
# macOS/Linux
mkdir -p ~/.claude/plugins/

# Windows
mkdir %USERPROFILE%\.claude\plugins\
```

Then retry installation.

### Issue 3: Permission Denied (Windows)

**Symptom**: Cannot create symlink on Windows

**Solution**: Run Command Prompt or PowerShell as Administrator
```powershell
# Right-click Command Prompt → "Run as Administrator"
mklink /D %USERPROFILE%\.claude\plugins\automated-testing-plugin C:\path\to\dante_plugin
```

### Issue 4: Framework Not Found

**Symptom**: Plugin says "Framework not detected" or framework not found

**Solution**: Install the testing framework for your language
```bash
# Python
pip install pytest

# JavaScript/TypeScript
npm install jest  # or: npm install vitest, npm install mocha

# Java - ensure pom.xml or build.gradle has JUnit dependency

# C# - ensure .csproj has xUnit/NUnit/MSTest package

# Go - built-in, no installation needed

# C++ - ensure CMakeLists.txt has Google Test or Catch2

# Verify installation
pytest --version  # Python
npx jest --version  # JavaScript/TypeScript
mvn test  # Java (Maven)
dotnet test  # C#
go test  # Go
ctest  # C++
```

### Issue 5: Python Version Mismatch

**Symptom**: Plugin fails with Python version errors

**Solution**: Ensure Python 3.8+
```bash
python --version
# Should show: Python 3.8.x or higher

# If using multiple Python versions
python3 --version
python3.8 --version
```

### Issue 6: Corrupted Installation

**Symptom**: Plugin loads but commands fail with errors

**Solution**: Clean reinstall
```bash
# 1. Remove plugin directory
rm -rf ~/.claude/plugins/automated-testing-plugin  # macOS/Linux
rmdir /S %USERPROFILE%\.claude\plugins\automated-testing-plugin  # Windows

# 2. Restart Claude Code
# 3. Reinstall using Method 1 or 2
```

### Issue 7: Command Files Not Loading

**Symptom**: Commands appear but fail to execute

**Solution**: Verify markdown files are valid
```bash
# Check command files exist
ls ~/.claude/plugins/automated-testing-plugin/.claude-plugin/commands/

# Should show:
# test-analyze.md
# test-generate.md
# test-loop.md
# test-resume.md

# Verify files are not empty
cat ~/.claude/plugins/automated-testing-plugin/.claude-plugin/commands/test-analyze.md
```

---

## Verifying Installation (Checklist)

Use this checklist to confirm successful installation:

### Pre-Installation
- [ ] Claude Code installed and working
- [ ] Python 3.8+ installed
- [ ] pytest installed in project

### Post-Installation
- [ ] Plugin directory created: `~/.claude/plugins/automated-testing-plugin/`
- [ ] `.claude-plugin/` directory exists
- [ ] All command files present: `test-analyze.md`, `test-generate.md`, `test-loop.md`, `test-resume.md`
- [ ] All agent files present (4 agents in `agents/`)
- [ ] Claude Code restarted
- [ ] Commands appear in autocomplete (type `/test` + Tab)
- [ ] `/test-analyze` command executes without errors
- [ ] Example project tests successfully: `/test-generate src/calculator.py`

---

## Next Steps

### 1. Test the Example Project
```bash
cd examples/python-calculator/
/test-generate src/calculator.py
```

### 2. Use on Your Own Project
```bash
cd /path/to/your/python/project
/test-analyze src/
/test-generate src/your_module.py
```

### 3. Read the User Guide
See `USER_GUIDE.md` for comprehensive usage instructions for external projects.

### 4. Explore Interactive Mode
```bash
/test-loop src/your_module.py
```

---

## Updating the Plugin

### If Installed via Marketplace (Method 1)

```bash
# Open Claude Code
claude

# Update the plugin
/plugins update automated-testing-plugin

# Or update all plugins
/plugins update

# Restart Claude Code
```

### If Installed via Git (Method 2)

```bash
cd ~/.claude/plugins/automated-testing-plugin
git pull origin main
# Restart Claude Code
```

### If Installed via Copy (Method 3)

1. Download the latest version
2. Delete old plugin directory
3. Copy new version to plugins directory
4. Restart Claude Code

---

## Uninstalling

### If Installed via Marketplace (Method 1)

```bash
# Open Claude Code
claude

# Uninstall the plugin
/plugins uninstall automated-testing-plugin

# Restart Claude Code
```

### If Installed via Git or Copy (Methods 2-4)

```bash
# macOS/Linux
rm -rf ~/.claude/plugins/automated-testing-plugin

# Windows
rmdir /S %USERPROFILE%\.claude\plugins\automated-testing-plugin

# Restart Claude Code
```

---

## Getting Help

- **Issues**: https://github.example.com/my-org/my-plugin/issues
- **Documentation**: See `.sdd/` directory in plugin
- **Examples**: See `examples/` directory

---

## Summary

**Quick installation** (most common):

**Via Marketplace** (Recommended):
```bash
# 1. Open Claude Code
claude

# 2. Install plugin
/plugins install automated-testing-plugin

# 3. Restart Claude Code

# 4. Test it works
cd /path/to/automated-testing-plugin/examples/python-calculator/
/test-analyze src/calculator.py
```

**Via Git** (For development):
```bash
# 1. Navigate to plugins directory
cd ~/.claude/plugins/

# 2. Clone repository
git clone https://github.example.com/my-org/my-plugin.git automated-testing-plugin

# 3. Restart Claude Code

# 4. Test it works
cd automated-testing-plugin/examples/python-calculator/
/test-analyze src/calculator.py
```

**That's it!** You're ready to use the Automated Testing Plugin.

---

**Installation Complete?** → Read [USER_GUIDE.md](USER_GUIDE.md) to learn how to use the plugin on your own projects.
