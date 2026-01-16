# agno_custom to Agno Fork - Quick Summary

## What is agno_custom?

`agno_custom/` is a **parallel custom implementation** of the Agno framework (17,303 lines) that mirrors the official framework but with specific modifications. It is NOT part of the official Agno framework.

## Key Custom Features

1. **Custom Message Logger** - Truncates system messages in logs for readability
   - Controlled by `SETTINGS.AGNO_SYSTEM_MESSAGE_LOG_TRUNCATE_LENGTH`

2. **Banavo Integration** - External dependencies:
   - `banavo.config.settings` - Configuration
   - `banavo.utils.token_counter` - Token counting

3. **Model.log_messages Flag** - Toggle context message logging

4. **Selective Agent Content** - Filter downstream agent outputs in tool calls
   - `Function.agent_ids_to_return_content_for`

## Why Migrate?

### Current Problems with agno_custom
- ❌ Parallel implementation requires double maintenance
- ❌ Missing official Agno features (100+ tools, 20+ vector DBs)
- ❌ No access to AgentOS production runtime
- ❌ Harder to sync with upstream improvements
- ❌ Can't use official documentation

### Benefits of Fork Approach
- ✅ Access to full Agno framework
- ✅ Keep custom features as small patches
- ✅ Easy to sync with upstream updates
- ✅ Use official docs + tools + ecosystem
- ✅ AgentOS support out of the box

## Migration Strategy (High-Level)

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Fork Official Agno                                       │
│    github.com/agno-agi/agno → YOUR_ORG/agno                 │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. Apply 4 Custom Features to Fork                         │
│    - Add custom_message_logger.py                          │
│    - Add log_messages flag to Model                        │
│    - Add agent_ids_to_return_content_for                   │
│    - Replace banavo token counter with tiktoken            │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│ 3. Update Project Dependencies                             │
│    pip install agno @ git+https://YOUR_ORG/agno.git        │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│ 4. Replace Imports                                          │
│    from agno_custom.agent → from agno.agent                │
│    from agno_custom.team  → from agno.team                 │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│ 5. Remove agno_custom/                                      │
│    git rm -r agno_custom/                                   │
└─────────────────────────────────────────────────────────────┘
```

## Files Changed in Migration

### In Your Fork (agno-fork/libs/agno/agno/)

| File | Change |
|------|--------|
| `utils/custom_message_logger.py` | **NEW** - Add custom logger |
| `utils/token_counter.py` | **NEW** - Add tiktoken-based counter |
| `models/base.py` | **MODIFY** - Add `log_messages` flag, use custom logger |
| `tools/function.py` | **MODIFY** - Add `agent_ids_to_return_content_for` |
| `pyproject.toml` | **MODIFY** - Add tiktoken dependency |

### In Your Project

| Action | Files |
|--------|-------|
| **Update imports** | All files using `from agno_custom` |
| **Remove directory** | `agno_custom/` (entire directory) |
| **Update config** | `pyproject.toml` or `requirements.txt` |
| **Add env var** | `AGNO_SYSTEM_MESSAGE_LOG_TRUNCATE_LENGTH=500` |

## Code Changes Required

### Before (agno_custom)
```python
from agno_custom.agent import Agent
from agno_custom.team import Team
from agno_custom.models.openai import OpenAIChat
from agno_custom.tools import Toolkit

agent = Agent(
    model=OpenAIChat(id="gpt-4"),
    tools=[Toolkit(...)],
)
```

### After (Agno fork)
```python
from agno.agent import Agent
from agno.team import Team
from agno.models.openai import OpenAIChat
from agno.tools import Toolkit

# Set environment variable for message truncation
import os
os.environ["AGNO_SYSTEM_MESSAGE_LOG_TRUNCATE_LENGTH"] = "500"

agent = Agent(
    model=OpenAIChat(id="gpt-4", log_messages=True),  # Now a standard feature
    tools=[Toolkit(...)],
)
```

## Estimated Effort

- **Fork setup**: 1-2 hours
- **Apply custom features**: 4-8 hours
- **Code migration**: 2-4 hours
- **Testing**: 4-8 hours
- **Total**: 2-4 days

## Quick Start Commands

```bash
# 1. Fork and clone
git clone https://github.com/YOUR_ORG/agno.git agno-fork
cd agno-fork
git checkout -b custom/banavo-integration

# 2. Apply patches (see detailed guide in MIGRATION_FROM_AGNO_CUSTOM.md)

# 3. Install your fork
cd agno-fork
pip install -e libs/agno

# 4. Update your project imports
cd /path/to/your/project
find . -name "*.py" -exec sed -i 's/from agno_custom/from agno/g' {} \;

# 5. Remove agno_custom
git rm -r agno_custom/

# 6. Test
pytest tests/
```

## Rollback Plan

If migration fails:
```bash
# Restore agno_custom
mv agno_custom.backup agno_custom

# Revert git
git checkout <commit-before-migration>

# Reinstall dependencies
pip uninstall agno
```

## Next Steps

1. **Read full guide**: `MIGRATION_FROM_AGNO_CUSTOM.md`
2. **Test in dev environment first**
3. **Create fork branch**: `custom/banavo-integration`
4. **Apply one feature at a time**
5. **Test thoroughly before removing agno_custom/**

## Questions?

- Full migration guide: `MIGRATION_FROM_AGNO_CUSTOM.md`
- Agno documentation: https://docs.agno.com
- Discord: https://discord.gg/4MtYHHrgA8
