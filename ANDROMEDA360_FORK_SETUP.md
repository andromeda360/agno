# Agno Fork Setup for Andromeda360 Organization

This guide provides step-by-step instructions for packaging and using an Agno fork within the Andromeda360 organization repository.

## Table of Contents

- [Overview](#overview)
- [Option 1: Git Dependency (Recommended)](#option-1-git-dependency-recommended)
- [Option 2: Renamed Package Distribution](#option-2-renamed-package-distribution)
- [Option 3: Local Development Install](#option-3-local-development-install)
- [Applying Custom Features](#applying-custom-features)
- [Maintenance and Updates](#maintenance-and-updates)
- [Troubleshooting](#troubleshooting)

## Overview

There are three main approaches to using an Agno fork in your organization:

| Approach | Best For | Pros | Cons |
|----------|----------|------|------|
| **Git Dependency** | Most teams | Simple, version-controlled, no publishing needed | Requires git access |
| **Renamed Package** | Public distribution | Clear namespace, can publish to PyPI | More complex setup |
| **Local Install** | Active development | Fast iteration | Manual updates needed |

## Option 1: Git Dependency (Recommended)

This is the simplest approach - use the fork directly via git without renaming.

### Step 1: Fork the Repository

1. **On GitHub:** Fork `agno-agi/agno` to `andromeda360/agno`

2. **Clone your fork:**
   ```bash
   git clone https://github.com/andromeda360/agno.git
   cd agno
   ```

3. **Create a custom branch:**
   ```bash
   git checkout -b custom/andromeda360-integration
   ```

4. **Set up upstream for syncing:**
   ```bash
   git remote add upstream https://github.com/agno-agi/agno.git
   git fetch upstream
   ```

### Step 2: Configure Your Project

**Using pyproject.toml:**

```toml
[project]
name = "your-andromeda360-project"
dependencies = [
    "agno @ git+https://github.com/andromeda360/agno.git@custom/andromeda360-integration#subdirectory=libs/agno",
]
```

**Using requirements.txt:**

```txt
agno @ git+https://github.com/andromeda360/agno.git@custom/andromeda360-integration#subdirectory=libs/agno
```

### Step 3: Install

```bash
# If using pyproject.toml
pip install -e .

# If using requirements.txt
pip install -r requirements.txt

# Or install directly
pip install "agno @ git+https://github.com/andromeda360/agno.git@custom/andromeda360-integration#subdirectory=libs/agno"
```

### Step 4: Verify Installation

```bash
python -c "from agno.agent import Agent; print('✓ Agno fork installed successfully')"
```

### Step 5: Version with Tags (Recommended)

For production stability, use git tags instead of branches:

```bash
# In your agno fork
git tag -a v1.0.0-andromeda360 -m "Andromeda360 custom release v1.0.0"
git push origin v1.0.0-andromeda360

# In your project's pyproject.toml
[project]
dependencies = [
    "agno @ git+https://github.com/andromeda360/agno.git@v1.0.0-andromeda360#subdirectory=libs/agno",
]
```

### Advantages

- ✅ No package renaming needed
- ✅ Version controlled via branches/tags
- ✅ Easy to sync with upstream
- ✅ Private to organization (if repo is private)
- ✅ No publishing infrastructure required
- ✅ Code imports stay as `from agno...`

## Option 2: Renamed Package Distribution

Use this if you want to distribute a custom-named package (e.g., `agno-andromeda360`).

### Step 1: Fork and Clone

Follow Option 1, Step 1 to fork and clone the repository.

### Step 2: Rename the Package

Edit `libs/agno/pyproject.toml`:

```toml
[project]
name = "agno-andromeda360"  # Changed from "agno"
version = "2.2.11-andromeda360.1"  # Add custom version suffix
description = "Agno fork for Andromeda360 - Multi-Agent Systems framework"
requires-python = ">=3.7,<4"
readme = "README.md"
license-files = ["LICENSE"]
authors = [
  {name = "Andromeda360", email = "dev@andromeda360.com"}  # Updated
]

# Add original attribution
[project.urls]
homepage = "https://andromeda360.com"
documentation = "https://docs.agno.com"
repository = "https://github.com/andromeda360/agno"
upstream = "https://github.com/agno-agi/agno"
```

**Important:** The Python package directory name (`agno/`) remains unchanged. Imports still use:
```python
from agno.agent import Agent  # NOT from agno_andromeda360
```

### Step 3: Build the Package

```bash
cd libs/agno

# Install build tools
pip install build twine

# Build distribution files
python -m build
```

This creates:
- `dist/agno_andromeda360-2.2.11_andromeda360.1-py3-none-any.whl`
- `dist/agno-andromeda360-2.2.11-andromeda360.1.tar.gz`

### Step 4: Publish the Package

**Option A: PyPI (Public)**

```bash
# Test on TestPyPI first
twine upload --repository testpypi dist/*

# Then publish to PyPI
twine upload dist/*
```

**Option B: GitHub Packages (Private)**

1. Create a Personal Access Token with `write:packages` permission

2. Configure `.pypirc`:
   ```ini
   [distutils]
   index-servers =
       github

   [github]
   repository = https://upload.pypi.org/legacy/
   username = __token__
   password = ghp_YOUR_TOKEN_HERE
   ```

3. Upload:
   ```bash
   twine upload --repository github dist/*
   ```

**Option C: Private PyPI Server**

```bash
twine upload --repository-url https://pypi.andromeda360.com/legacy/ dist/*
```

**Option D: Distribute Wheel Files Directly**

Share the `.whl` file from `libs/agno/dist/` with your team:

```bash
# Team members install from file
pip install agno_andromeda360-2.2.11_andromeda360.1-py3-none-any.whl

# Or from URL
pip install https://internal-storage.andromeda360.com/packages/agno_andromeda360-2.2.11-py3-none-any.whl
```

### Step 5: Install in Projects

**From PyPI:**
```toml
[project]
dependencies = [
    "agno-andromeda360==2.2.11-andromeda360.1",
]
```

**From GitHub Packages:**
```bash
pip install agno-andromeda360 --index-url https://pypi.andromeda360.com/simple/
```

**From wheel file:**
```bash
pip install /path/to/agno_andromeda360-2.2.11-py3-none-any.whl
```

### Advantages

- ✅ Clear namespace separation
- ✅ Can publish to public/private registries
- ✅ Standard pip installation
- ✅ Version management via package versions

### Disadvantages

- ❌ More complex setup
- ❌ Publishing infrastructure needed
- ❌ Manual rebuild for updates

## Option 3: Local Development Install

For active development and testing.

### Step 1: Clone the Fork

```bash
git clone https://github.com/andromeda360/agno.git /path/to/andromeda360-agno
cd /path/to/andromeda360-agno
git checkout custom/andromeda360-integration
```

### Step 2: Install in Editable Mode

```bash
# Remove official agno if installed
pip uninstall agno

# Install fork in editable mode
pip install -e libs/agno
```

### Step 3: Verify

```bash
python -c "import agno; print(agno.__file__)"
# Should output: /path/to/andromeda360-agno/libs/agno/agno/__init__.py
```

### Step 4: Use in Your Project

Your code imports work normally:
```python
from agno.agent import Agent
from agno.team import Team
```

Changes in the fork are immediately reflected without reinstalling.

### Advantages

- ✅ Fast iteration during development
- ✅ Immediate reflection of changes
- ✅ Easy debugging

### Disadvantages

- ❌ Manual setup on each machine
- ❌ Not suitable for production deployment
- ❌ Path-dependent

## Applying Custom Features

After setting up the fork, apply your custom features from `agno_custom`. See `MIGRATION_FROM_AGNO_CUSTOM.md` for detailed instructions.

### Quick Summary

1. **Custom Message Logger:** Add `libs/agno/agno/utils/custom_message_logger.py`
2. **Model.log_messages Flag:** Modify `libs/agno/agno/models/base.py`
3. **Selective Agent Content:** Modify tool execution in `libs/agno/agno/models/base.py`
4. **Token Counter:** Add `libs/agno/agno/utils/token_counter.py` with tiktoken

### Commit Custom Changes

```bash
cd /path/to/andromeda360-agno
git add .
git commit -m "feat: Add Andromeda360 custom features

- Custom message logger with truncation
- Model.log_messages flag for controllable logging
- Selective agent content return in tool calls
- Built-in token counter using tiktoken"
git push origin custom/andromeda360-integration
```

## Maintenance and Updates

### Syncing with Upstream Agno

```bash
cd /path/to/andromeda360-agno

# Fetch upstream changes
git fetch upstream

# Option 1: Merge upstream into main
git checkout main
git merge upstream/main
git push origin main

# Option 2: Rebase your custom branch
git checkout custom/andromeda360-integration
git rebase main

# Resolve conflicts if any
# Test thoroughly
./scripts/test.sh

# Push updates
git push origin custom/andromeda360-integration --force-with-lease
```

### Update Schedule

- **Weekly:** Check for security updates
- **Monthly:** Sync with upstream main
- **Quarterly:** Major version updates

### Testing After Updates

```bash
# Run Agno tests
./scripts/test.sh

# Test custom features
pytest tests/custom/

# Test in your project
cd /path/to/your-andromeda360-project
pytest
```

### Versioning Strategy

Use semantic versioning with custom suffix:

- `2.2.11-andromeda360.1` - First custom release based on Agno 2.2.11
- `2.2.11-andromeda360.2` - Second custom release (bug fixes)
- `2.2.12-andromeda360.1` - Updated to upstream 2.2.12

Tag each release:
```bash
git tag -a v2.2.11-andromeda360.1 -m "Release v2.2.11-andromeda360.1"
git push origin v2.2.11-andromeda360.1
```

## Troubleshooting

### Issue: Import Error "No module named 'agno'"

**Solution:**
```bash
# Verify installation
pip show agno

# Reinstall
pip uninstall agno
pip install "agno @ git+https://github.com/andromeda360/agno.git@custom/andromeda360-integration#subdirectory=libs/agno"
```

### Issue: Wrong Version Installed

**Solution:**
```bash
# Force reinstall
pip install --force-reinstall --no-cache-dir "agno @ git+https://github.com/andromeda360/agno.git@custom/andromeda360-integration#subdirectory=libs/agno"
```

### Issue: Git Authentication Failed

**Solution:**
```bash
# Use SSH instead of HTTPS
pip install "agno @ git+ssh://git@github.com/andromeda360/agno.git@custom/andromeda360-integration#subdirectory=libs/agno"

# Or use personal access token
pip install "agno @ git+https://YOUR_TOKEN@github.com/andromeda360/agno.git@custom/andromeda360-integration#subdirectory=libs/agno"
```

### Issue: Editable Install Not Reflecting Changes

**Solution:**
```bash
# Reinstall in editable mode
pip uninstall agno
pip install -e /path/to/andromeda360-agno/libs/agno

# Check Python is using correct path
python -c "import agno; print(agno.__file__)"
```

### Issue: Dependency Conflicts

**Solution:**
```bash
# Use dependency resolver
pip install --use-feature=fast-deps "agno @ git+https://github.com/andromeda360/agno.git@custom/andromeda360-integration#subdirectory=libs/agno"

# Or create clean environment
python -m venv .venv-clean
source .venv-clean/bin/activate
pip install "agno @ git+https://github.com/andromeda360/agno.git@custom/andromeda360-integration#subdirectory=libs/agno"
```

## Best Practices

### 1. Use Virtual Environments

```bash
# Create dedicated environment
python -m venv .venv-andromeda360
source .venv-andromeda360/bin/activate  # Unix
.venv-andromeda360\Scripts\activate     # Windows
```

### 2. Pin Versions in Production

```toml
# Development - use branch
dependencies = [
    "agno @ git+https://github.com/andromeda360/agno.git@custom/andromeda360-integration#subdirectory=libs/agno"
]

# Production - use tag
dependencies = [
    "agno @ git+https://github.com/andromeda360/agno.git@v1.0.0-andromeda360#subdirectory=libs/agno"
]
```

### 3. Document Custom Changes

Create `CUSTOM_CHANGES.md` in your fork:

```markdown
# Andromeda360 Custom Features

## Changes from Upstream

1. Custom message logger with truncation
2. Model.log_messages flag
3. Selective agent content return
4. Built-in token counter

## Files Modified

- libs/agno/agno/models/base.py
- libs/agno/agno/tools/function.py
- libs/agno/agno/utils/custom_message_logger.py (new)
- libs/agno/agno/utils/token_counter.py (new)
```

### 4. CI/CD Integration

Add to `.github/workflows/test.yml`:

```yaml
name: Test Andromeda360 Fork

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install -e libs/agno[dev]
      - name: Run tests
        run: |
          ./scripts/test.sh
      - name: Test custom features
        run: |
          pytest tests/custom/
```

### 5. Security Scanning

```bash
# Scan for vulnerabilities
pip install safety
safety check

# Scan dependencies
pip install pip-audit
pip-audit
```

## Recommended Setup for Andromeda360

Based on the analysis of your `agno_custom` implementation, we recommend:

**Choice:** Option 1 (Git Dependency)

**Reasoning:**
- ✅ Simple to set up and maintain
- ✅ Version controlled via git tags
- ✅ No publishing infrastructure needed
- ✅ Easy to sync with upstream
- ✅ Private to organization
- ✅ Standard imports (`from agno...`)

**Implementation:**

```toml
# In andromeda360 projects
[project]
name = "your-project"
dependencies = [
    "agno @ git+https://github.com/andromeda360/agno.git@v1.0.0-andromeda360#subdirectory=libs/agno",
    # other dependencies...
]
```

**Next Steps:**

1. Complete migration from `agno_custom` (see `MIGRATION_FROM_AGNO_CUSTOM.md`)
2. Apply custom features to fork
3. Test thoroughly
4. Tag first release: `v1.0.0-andromeda360`
5. Update all andromeda360 projects to use fork
6. Remove `agno_custom` directory

## Support

- **Upstream Agno:** https://docs.agno.com
- **Issues:** https://github.com/andromeda360/agno/issues
- **Agno Discord:** https://discord.gg/4MtYHHrgA8
- **Agno Community:** https://community.agno.com

## License

This fork maintains the Mozilla Public License 2.0 (MPL 2.0) from the upstream Agno project. See LICENSE file for details.
