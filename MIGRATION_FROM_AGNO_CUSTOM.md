# Migration from agno_custom to Official Agno Fork

## Overview

The `agno_custom/` directory contains a custom parallel implementation of the Agno framework with specific modifications. This document outlines the strategy to migrate from `agno_custom` to using a fork of the official Agno repository.

## Current State Analysis

### agno_custom Structure
```
agno_custom/
├── agent/agent.py        (7,897 lines - custom agent implementation)
├── team/team.py          (7,720 lines - custom team implementation)
├── models/
│   ├── base.py          (1,686 lines - custom model base)
│   ├── openai/chat.py   (custom OpenAI implementation)
│   ├── aws/claude.py    (custom AWS Bedrock implementation)
│   └── anthropic/claude.py (custom Anthropic implementation)
├── tools/
│   ├── function.py      (custom function implementation)
│   └── toolkit.py       (custom toolkit implementation)
├── memory/memory.py     (custom memory implementation)
└── utils/
    ├── custom_message_logger.py  (custom logging)
    └── functions.py              (custom function utilities)
```

### Official Agno Structure (for comparison)
```
libs/agno/agno/
├── agent/agent.py        (10,390 lines - official)
├── team/team.py          (8,766 lines - official)
├── models/base.py        (2,175 lines - official)
└── [rest of framework]
```

## Key Customizations in agno_custom

### 1. Custom Message Logger with Truncation
**File:** `agno_custom/utils/custom_message_logger.py`

**Feature:** Truncates system messages in logs for improved readability
```python
def log_message(
    message: Message,
    system_message_truncate_length: int = None,
    metrics: bool = True,
    level: Optional[str] = None
):
    # Truncates system message content if specified
    if message.role == "system" and system_message_truncate_length:
        content = (
            "<truncated system message>\n"
            + content[:system_message_truncate_length]
            + "\n</truncated system message>"
        )
```

**Usage in models/base.py:**
```python
from agno_custom.utils.custom_message_logger import log_message
from banavo.config.settings import SETTINGS

def _log_messages(messages: List[Message]) -> None:
    for m in messages:
        log_message(
            m,
            system_message_truncate_length=SETTINGS.AGNO_SYSTEM_MESSAGE_LOG_TRUNCATE_LENGTH,
            metrics=False
        )
```

### 2. Banavo Integration
**External Dependencies:**
- `banavo.config.settings.SETTINGS` - Configuration management
- `banavo.utils.token_counter.count_tokens` - Token counting utilities

**Files with Banavo dependencies:**
- `agno_custom/models/base.py:36` - SETTINGS import
- `agno_custom/memory/memory.py:23` - count_tokens import
- `agno_custom/team/team.py:89` - count_tokens import

### 3. Model.log_messages Flag
**File:** `agno_custom/models/base.py:264`

**Feature:** Controllable logging of context messages
```python
@dataclass
class Model(ABC):
    # Flag to enable/disable logging of all in-context messages
    log_messages: bool = True

    def response(self, messages, ...):
        if self.log_messages:
            _log_messages(messages)
```

### 4. Selective Agent Content Return
**File:** `agno_custom/models/base.py:1576-1580`

**Feature:** Filter which downstream agent outputs to include in tool call results
```python
# In arun_function_calls async method
agent_id = getattr(item, "agent_id", None) or getattr(item, "team_id", None)
if (
    fc.function.agent_ids_to_return_content_for is None
    or agent_id in fc.function.agent_ids_to_return_content_for
):
    function_call_output += item.content or ""
```

## Migration Strategy

### Phase 1: Fork Official Agno Repository

1. **Create Fork**
   ```bash
   # Fork https://github.com/agno-agi/agno to your organization
   git clone https://github.com/YOUR_ORG/agno.git agno-fork
   cd agno-fork

   # Create a custom branch for your modifications
   git checkout -b custom/banavo-integration
   ```

2. **Set Up Upstream**
   ```bash
   git remote add upstream https://github.com/agno-agi/agno.git
   git fetch upstream
   ```

### Phase 2: Apply Custom Features to Fork

#### 2.1 Add Custom Message Logger

Create `libs/agno/agno/utils/custom_message_logger.py`:
```python
# Copy from agno_custom/utils/custom_message_logger.py
# Remove banavo dependencies, use environment variables instead
```

Modify `libs/agno/agno/models/base.py`:
```python
# Add import
from agno.utils.custom_message_logger import log_message

# Add configuration (replace SETTINGS.AGNO_SYSTEM_MESSAGE_LOG_TRUNCATE_LENGTH)
import os
SYSTEM_MESSAGE_TRUNCATE_LENGTH = int(os.getenv("AGNO_SYSTEM_MESSAGE_LOG_TRUNCATE_LENGTH", "0"))

# Update _log_messages function
def _log_messages(messages: List[Message]) -> None:
    for m in messages:
        if SYSTEM_MESSAGE_TRUNCATE_LENGTH > 0:
            log_message(m, system_message_truncate_length=SYSTEM_MESSAGE_TRUNCATE_LENGTH, metrics=False)
        else:
            m.log(metrics=False)
```

#### 2.2 Add log_messages Flag to Model

Modify `libs/agno/agno/models/base.py`:
```python
@dataclass
class Model(ABC):
    # ... existing fields ...

    # Flag to enable/disable the logging of all in context messages
    log_messages: bool = True
```

Update all `response()` and `aresponse()` methods to respect this flag.

#### 2.3 Add Selective Agent Content Return

Modify `libs/agno/agno/models/base.py` in the `arun_function_calls` method:
```python
# Around line 1574 in the async for loop handling AsyncIterator results
agent_id = getattr(item, "agent_id", None) or getattr(item, "team_id", None)
if (
    fc.function.agent_ids_to_return_content_for is None
    or agent_id in fc.function.agent_ids_to_return_content_for
):
    function_call_output += item.content or ""
```

Also add the field to `libs/agno/agno/tools/function.py`:
```python
@dataclass
class Function:
    # ... existing fields ...

    # Filter which downstream agent outputs to include
    agent_ids_to_return_content_for: Optional[List[str]] = None
```

#### 2.4 Replace Banavo Token Counter

Create `libs/agno/agno/utils/token_counter.py`:
```python
# Implement token counting using tiktoken or similar
from typing import Union, List
import tiktoken

def count_tokens(
    messages: Union[str, List],
    model: str = "gpt-4"
) -> int:
    """Count tokens in messages using tiktoken."""
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        encoding = tiktoken.get_encoding("cl100k_base")

    if isinstance(messages, str):
        return len(encoding.encode(messages))

    # Handle message list format
    num_tokens = 0
    for message in messages:
        if isinstance(message, dict):
            for key, value in message.items():
                num_tokens += len(encoding.encode(str(value)))
        else:
            num_tokens += len(encoding.encode(str(message)))

    return num_tokens
```

Update `libs/agno/pyproject.toml`:
```toml
dependencies = [
    # ... existing dependencies ...
    "tiktoken",
]
```

Then replace imports in:
- `libs/agno/agno/memory/` files
- `libs/agno/agno/team/team.py`

Change from:
```python
from banavo.utils.token_counter import count_tokens
```

To:
```python
from agno.utils.token_counter import count_tokens
```

### Phase 3: Update Project Configuration

#### 3.1 Update pyproject.toml or requirements.txt

**Option A: Use Local Development Install**
```bash
# In your main project directory
pip uninstall agno  # Remove official version if installed

# Install from local fork
cd agno-fork
pip install -e libs/agno
```

**Option B: Use Git Dependency**

In your project's `pyproject.toml`:
```toml
[project]
dependencies = [
    "agno @ git+https://github.com/YOUR_ORG/agno.git@custom/banavo-integration#subdirectory=libs/agno",
]
```

Or in `requirements.txt`:
```
agno @ git+https://github.com/YOUR_ORG/agno.git@custom/banavo-integration#subdirectory=libs/agno
```

#### 3.2 Set Environment Variables

Replace `SETTINGS.AGNO_SYSTEM_MESSAGE_LOG_TRUNCATE_LENGTH` with environment variable:

```bash
# In .env file
AGNO_SYSTEM_MESSAGE_LOG_TRUNCATE_LENGTH=500
```

Or in code:
```python
import os
os.environ["AGNO_SYSTEM_MESSAGE_LOG_TRUNCATE_LENGTH"] = "500"
```

### Phase 4: Migrate Code from agno_custom to Official Agno

#### 4.1 Update Import Statements

**Before:**
```python
from agno_custom.agent import Agent
from agno_custom.team import Team
from agno_custom.models.openai import OpenAIChat
from agno_custom.tools import Toolkit, Function
```

**After:**
```python
from agno.agent import Agent
from agno.team import Team
from agno.models.openai import OpenAIChat
from agno.tools import Toolkit, Function
```

#### 4.2 Search and Replace

Run these commands in your project:

```bash
# Find all files using agno_custom
find . -name "*.py" -type f -exec grep -l "agno_custom" {} \;

# Replace imports (review carefully before running)
find . -name "*.py" -type f -exec sed -i 's/from agno_custom/from agno/g' {} \;
find . -name "*.py" -type f -exec sed -i 's/import agno_custom/import agno/g' {} \;
```

#### 4.3 Remove agno_custom Directory

After verifying everything works:
```bash
# Backup first
cp -r agno_custom agno_custom.backup

# Add to .gitignore
echo "agno_custom/" >> .gitignore
echo "agno_custom.backup/" >> .gitignore

# Remove from repository
git rm -r agno_custom/
```

### Phase 5: Testing and Validation

#### 5.1 Unit Tests
```bash
# Test that imports work
python -c "from agno.agent import Agent; print('✓ Agent import works')"
python -c "from agno.team import Team; print('✓ Team import works')"
python -c "from agno.models.openai import OpenAIChat; print('✓ Model import works')"
```

#### 5.2 Integration Tests
```bash
# Run your existing test suite
pytest tests/

# Run Agno's test suite in your fork
cd agno-fork
./scripts/test.sh
```

#### 5.3 Feature Verification Checklist

- [ ] Message truncation works with environment variable
- [ ] Token counting works without banavo dependency
- [ ] `log_messages` flag controls logging properly
- [ ] Selective agent content return works in tool calls
- [ ] All model providers (OpenAI, Anthropic, AWS) work correctly
- [ ] Agent, Team, and Workflow functionality preserved
- [ ] All existing tools and toolkits work

### Phase 6: Maintain Fork

#### 6.1 Sync with Upstream

```bash
# Regularly pull updates from official Agno
cd agno-fork
git checkout main
git fetch upstream
git merge upstream/main

# Rebase your custom branch
git checkout custom/banavo-integration
git rebase main

# Resolve any conflicts
# Test thoroughly after rebasing
./scripts/test.sh
```

#### 6.2 Document Custom Changes

Create `CUSTOM_CHANGES.md` in your fork:
```markdown
# Custom Changes to Agno Fork

## Added Features

1. **Custom Message Logger** (libs/agno/agno/utils/custom_message_logger.py)
   - System message truncation for logs
   - Configurable via AGNO_SYSTEM_MESSAGE_LOG_TRUNCATE_LENGTH env var

2. **Model.log_messages Flag** (libs/agno/agno/models/base.py)
   - Control whether context messages are logged
   - Default: True

3. **Selective Agent Content Return** (libs/agno/agno/models/base.py, libs/agno/agno/tools/function.py)
   - Function.agent_ids_to_return_content_for
   - Filter downstream agent outputs in tool results

4. **Built-in Token Counter** (libs/agno/agno/utils/token_counter.py)
   - Uses tiktoken for accurate token counting
   - Replaces external banavo dependency

## Maintenance

Branch: `custom/banavo-integration`
Last synced with upstream: [date]
Upstream commit: [commit hash]
```

## Migration Checklist

- [ ] **Phase 1: Fork Setup**
  - [ ] Fork agno-agi/agno repository
  - [ ] Clone fork locally
  - [ ] Set up upstream remote
  - [ ] Create custom branch

- [ ] **Phase 2: Apply Custom Features**
  - [ ] Add custom message logger
  - [ ] Add log_messages flag to Model
  - [ ] Add selective agent content return
  - [ ] Implement token counter replacement
  - [ ] Update dependencies in pyproject.toml
  - [ ] Test all custom features

- [ ] **Phase 3: Project Configuration**
  - [ ] Update project dependencies to use fork
  - [ ] Set environment variables
  - [ ] Verify fork installs correctly

- [ ] **Phase 4: Code Migration**
  - [ ] Find all agno_custom usages
  - [ ] Update import statements
  - [ ] Remove agno_custom directory
  - [ ] Update .gitignore

- [ ] **Phase 5: Testing**
  - [ ] Run unit tests
  - [ ] Run integration tests
  - [ ] Verify all custom features
  - [ ] Test in development environment
  - [ ] Test in staging environment

- [ ] **Phase 6: Maintenance Setup**
  - [ ] Document custom changes
  - [ ] Create sync schedule with upstream
  - [ ] Set up CI/CD for fork
  - [ ] Update CLAUDE.md with fork information

## Benefits of Migration

1. **Official Framework Features**: Access to all Agno framework features (100+ tools, 20+ vector DBs, etc.)
2. **Better Performance**: Benefit from official performance optimizations (3μs agent instantiation)
3. **Community Updates**: Easy to sync with upstream improvements and bug fixes
4. **Reduced Maintenance**: Only maintain small diff instead of entire parallel implementation
5. **Better Documentation**: Use official docs at docs.agno.com
6. **AgentOS Support**: Access to production runtime and control plane

## Rollback Plan

If issues arise during migration:

1. **Keep agno_custom.backup**
   ```bash
   mv agno_custom.backup agno_custom
   ```

2. **Revert dependencies**
   ```bash
   # Reinstall official agno or revert to agno_custom
   pip uninstall agno
   # Use agno_custom imports again
   ```

3. **Restore git state**
   ```bash
   git checkout <commit-before-migration>
   ```

## Support and Questions

- Official Agno Discord: https://discord.gg/4MtYHHrgA8
- Agno Documentation: https://docs.agno.com
- Community Forum: https://community.agno.com

## Timeline Estimate

- **Phase 1**: 1-2 hours (fork setup)
- **Phase 2**: 4-8 hours (apply custom features)
- **Phase 3**: 1-2 hours (project configuration)
- **Phase 4**: 2-4 hours (code migration)
- **Phase 5**: 4-8 hours (testing)
- **Phase 6**: 1-2 hours (documentation)

**Total**: 2-4 days for complete migration
