# Custom/Banavo-Integration Branch Changelog

**Branch:** `custom/banavo-integration`  
**Base:** `origin/main` (v2.3.7)  
**Generated:** 2026-01-21

---

## Feature 1: Andromeda360 Custom Features

> **Commit:** `70b3ea008`  
> **Message:** feat: Add Andromeda360 custom features to Agno fork

### 1.1 Custom Message Logger
**File:** `agno_v2/utils/custom_message_logger.py`

- System message truncation via `AGNO_SYSTEM_MESSAGE_LOG_TRUNCATE_LENGTH` environment variable
- Enhanced message logging with configurable truncation
- Useful for reducing log verbosity in production environments

### 1.2 Model.log_messages Flag
**File:** `agno_v2/models/base.py`

- Added `log_messages` boolean flag to Model class
- Toggle for context message logging
- Allows disabling verbose message logging in production

### 1.3 Selective Agent Content Return
**Files:**
- `agno_v2/tools/function.py`
- `agno_v2/models/base.py`

- Added `agent_ids_to_return_content_for` field on Function class
- Filter which downstream agent outputs to include in tool results
- Enables fine-grained control over agent response propagation

### 1.4 Token Counter Utility
**File:** `agno_v2/utils/token_counter.py`

- tiktoken-based token counting utility
- Replaces dependency on `banavo.utils.token_counter`
- Added `tiktoken` to `pyproject.toml` dependencies

---

## Feature 2: DynamicParallel Workflow

> **Commit:** `2814e6d65`  
> **Message:** feat(workflow): add DynamicParallel to core workflow

### 2.1 DynamicParallel Class
**File:** `agno_v2/workflow/dynamic_parallel.py`

- New workflow construct for dynamic parallel execution
- Allows runtime-determined parallel step execution
- Exported via `agno_v2.workflow.DynamicParallel`

### 2.2 AWS Bedrock Enhancement
**File:** `agno_v2/models/aws/bedrock.py`

- Minor fixes to AWS Bedrock model integration

---

## Feature 3: Package Rename (agno → agno_v2)

> **Commit:** `16824a80a`  
> **Message:** chore: rename agno to agno_v2 for concurrent versioning

### Purpose
Allow concurrent installation of different Agno versions in the same environment.

### Changes
| Category | Change |
|----------|--------|
| Package directory | `libs/agno/agno/` → `libs/agno_v2/agno_v2/` |
| Package name | `name = "agno"` → `name = "agno_v2"` in pyproject.toml |
| All imports | `from agno.*` → `from agno_v2.*` (1000+ files) |
| Environment variables | `AGNO_*` → `AGNO_V2_*` |
| Logger name | `"agno"` → `"agno_v2"` |
| Scripts | Updated all scripts in `scripts/` directory |
| CI/CD | Updated `.github/workflows/` paths |

---

## Merge Conflict Resolutions

| Commit | Description |
|--------|-------------|
| `0160d405a` | Fix NameError: define FilterExpr imports in all files |
| `a2f5999f3` | Fix syntax error in agent.py and double replacement of env vars |
| `63594dbd0` | Merge branch 'main' and resolve all conflicts |
| `6512ae271` | Resolve conflict in pyproject.toml |
| `cf5c9b69a` | Merge branch 'main' into custom/banavo-integration |
| `2aa78f6c2` | Merge branch 'feat/dynamic-parallel' and fix conflicts |

---

## Files Modified (Summary)

```
libs/agno_v2/agno_v2/models/base.py           # log_messages flag, agent content filtering
libs/agno_v2/agno_v2/tools/function.py        # agent_ids_to_return_content_for
libs/agno_v2/agno_v2/utils/custom_message_logger.py  # System message truncation
libs/agno_v2/agno_v2/utils/token_counter.py   # tiktoken-based counter
libs/agno_v2/agno_v2/workflow/dynamic_parallel.py    # DynamicParallel class
libs/agno_v2/pyproject.toml                   # Package rename + tiktoken dep
+ 1000+ files with import updates (agno → agno_v2)
```

---

## Compatibility Notes

- All features are **backward compatible** and **opt-in** via configuration
- Existing code using default settings will continue to work
- The `agno_v2` package can be installed alongside the original `agno` package
