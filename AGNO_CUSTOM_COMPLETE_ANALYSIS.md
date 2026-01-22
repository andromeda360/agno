# agno_custom - Complete Custom Implementations Analysis

## Overview

The `agno_custom` directory contains **17,303 lines** of custom code that parallels the official Agno framework. This document lists **ALL** custom implementations identified.

## Complete List of Custom Implementations

### 1. Custom Message Logging
**Files:** `agno_custom/utils/custom_message_logger.py`, `agno_custom/models/base.py`

**What:** Custom message logger with system message truncation capability

**Details:**
```python
# Function signature
def log_message(
    message: Message,
    system_message_truncate_length: int = None,  # NEW PARAMETER
    metrics: bool = True,
    level: Optional[str] = None
)

# Truncation logic
if message.role == "system" and system_message_truncate_length:
    content = (
        "<truncated system message>\n"
        + content[:system_message_truncate_length]
        + "\n</truncated system message>"
    )
```

**Used in:** `agno_custom/models/base.py:65`
- Controlled by: `SETTINGS.AGNO_SYSTEM_MESSAGE_LOG_TRUNCATE_LENGTH`

---

### 2. Model.log_messages Flag
**File:** `agno_custom/models/base.py:264`

**What:** Toggle to control whether context messages are logged

**Details:**
```python
@dataclass
class Model(ABC):
    # Flag to enable/disable the logging of all in context messaged
    # before beginning model execution loop
    log_messages: bool = True
```

**Used in:**
- `response()` method: line 336
- `aresponse()` method: line 440
- `response_stream()` method: line 761
- `aresponse_stream()` method: line 897

---

### 3. Banavo External Dependencies
**Files:** Multiple

**What:** Integration with external Banavo package

**Dependencies:**
1. **Settings Integration:**
   - File: `agno_custom/models/base.py:36`
   - Import: `from banavo.config.settings import SETTINGS`
   - Usage: `SETTINGS.AGNO_SYSTEM_MESSAGE_LOG_TRUNCATE_LENGTH`

2. **Token Counter Integration:**
   - Files:
     - `agno_custom/memory/memory.py:23`
     - `agno_custom/team/team.py:89`
   - Import: `from banavo.utils.token_counter import count_tokens`
   - Usage: Token counting for history management

---

### 4. Selective Agent Content Return (Function.agent_ids_to_return_content_for)
**Files:** `agno_custom/tools/function.py:119`, `agno_custom/models/base.py:1576-1580`

**What:** Allow tool functions to specify which downstream agent outputs to include

**Details:**
```python
# In Function class
class Function(BaseModel):
    # NOTE: New feature - allow tool function to specify which downstream
    # agent outputs to include in the function call output,
    # if not set, all are included.
    agent_ids_to_return_content_for: Optional[str] = None
```

**Used in:** `agno_custom/models/base.py` in `arun_function_calls()` method:
```python
# Line 1576-1580
agent_id = getattr(item, "agent_id", None) or getattr(item, "team_id", None)
if (
    fc.function.agent_ids_to_return_content_for is None
    or agent_id in fc.function.agent_ids_to_return_content_for
):
    function_call_output += item.content or ""
```

---

### 5. Token-Based History Management (max_tokens_from_history)
**Files:** `agno_custom/agent/agent.py:147`, `agno_custom/memory/memory.py:752-849`

**What:** Get most recent runs' messages that fit within a token budget

**Details:**

**In Agent:**
```python
# Line 145-147
# NOTE: New Feature
# This parameter is used to get the most recent runs' messages
# that fit within a token budget.
max_tokens_from_history: Optional[int] = None
```

**In Memory:**
```python
# Line 752-849
# NOTE: New Feature
# This method is used to get the most recent runs' messages that
# fit within a token budget.
def get_max_messages_from_history(
    self,
    session_id: str,
    max_tokens: int,  # NEW PARAMETER
    agent_id: Optional[str] = None,
    team_id: Optional[str] = None,
    skip_role: Optional[str] = None,
    skip_history_messages: bool = True,
    model_encoding: str = "cl100k_base",
) -> List[Message]:
    """Fetch the most recent runs' messages that fit within a token budget.

    Iterates from most recent run backward, computing token usage per run
    and accumulates runs until adding next run would exceed max_tokens.
    """
    # Implementation uses count_tokens() from banavo
```

**Usage:** Enables token-aware history retrieval instead of just run count

---

### 6. Session State in Response (include_session_state_in_response)
**File:** `agno_custom/agent/agent.py:549-550, 1272-1275`

**What:** Return public agent state in the run response

**Details:**
```python
# Line 549-550
# NOTE: New Feature - added ability to return the public agent state
# in the run response
self.include_session_state_in_response = include_session_state_in_response

# Line 1272-1275
# NOTE: New Feature - adds the public agent state to the run response
# if <self.include_session_state_in_response> is set
if self.include_session_state_in_response:
    log_debug("Adding agent session state to run response")
    # ... adds session state to response
```

---

### 7. Session State Reset Bugfix
**File:** `agno_custom/agent/agent.py:611-614`

**What:** Prevent inappropriate session state reset

**Details:**
```python
# Line 611-614
# NOTE: bugfix - agno resets the session state if session id is provided,
# even if storage is not enabled - this results in the team state which
# was written by the parent to be reset here inappropriately
# Do not reset session states, let team handle it on transfer
# self.session_state = None  # COMMENTED OUT
# self.team_session_state = None  # COMMENTED OUT
```

---

### 8. TeamMemberInteraction from Teams Bugfix
**File:** `agno_custom/memory/memory.py:50-54`

**What:** Support creating TeamMemberInteractions from Teams (TeamRunResponse)

**Details:**
```python
# Line 50-54
# NOTE: bugfix - added missing support to create TeamMemberInteractions
# from Teams (TeamRunResponse):
if "team_id" in member_response:
    return cls(
        member_name=data["member_name"],
        task=data["task"],
        response=TeamRunResponse.from_dict(member_response)
    )
```

---

### 9. Limited Team Member Interactions Sharing (max_interactions_to_share)
**File:** `agno_custom/memory/memory.py:1141-1174`

**What:** Limit how many recent team interactions to share for context management

**Details:**
```python
# Line 1141-1142
# NOTE: Custom feature: added ability to specify how many of the most recent
# interactions to share via <max_interactions_to_share> to manage context size
def get_team_member_interactions_str(
    self,
    session_id: str,
    max_interactions_to_share: int = None  # NEW PARAMETER
) -> str:
    # ... implementation that limits interactions
    if max_interactions_to_share and interactions_added >= max_interactions_to_share:
        break
```

---

### 10. Enhanced Memory Instructions
**File:** `agno_custom/agent/agent.py:4421-4422, 4446-4447`

**What:** Additional instructions for memory context prioritization

**Details:**
```python
# Lines 4421-4422 and 4446-4447
system_message_content += (
    "Note: this information is from previous interactions and may be "
    "updated in this conversation. You should always prefer information "
    "from this conversation over the past memories.\n\n"
)
```

**Purpose:** Clarifies to model that current conversation supersedes past memories

---

## Summary Table

| # | Feature | Files Modified | Lines | Priority | Complexity |
|---|---------|---------------|-------|----------|------------|
| 1 | Custom Message Logger | utils/custom_message_logger.py, models/base.py | ~130 | HIGH | Low |
| 2 | log_messages Flag | models/base.py | ~5 | MEDIUM | Low |
| 3 | Banavo Integration | models/base.py, memory/memory.py, team/team.py | ~10 | HIGH | Medium |
| 4 | Selective Agent Content | tools/function.py, models/base.py | ~10 | MEDIUM | Low |
| 5 | Token-Based History | agent/agent.py, memory/memory.py | ~100 | HIGH | Medium |
| 6 | Session State in Response | agent/agent.py | ~10 | LOW | Low |
| 7 | Session State Reset Fix | agent/agent.py | ~5 | MEDIUM | Low |
| 8 | TeamMemberInteraction Fix | memory/memory.py | ~5 | LOW | Low |
| 9 | Limited Team Interactions | memory/memory.py | ~35 | MEDIUM | Low |
| 10 | Memory Instructions | agent/agent.py | ~5 | LOW | Low |

## What Needs to be Added to Official Agno

To migrate from `agno_custom` to official Agno, the following additions are required:

### Critical Additions (Must Have)

#### 1. Custom Message Logger with Truncation
**Add to:** `libs/agno/agno/utils/custom_message_logger.py` (NEW FILE)

**Code:**
```python
import json
from typing import Optional
from agno.models.message import Message, MessageMetrics
from agno.utils.log import log_debug, log_error, log_info, log_warning

def log_message(
    message: Message,
    system_message_truncate_length: int = None,
    metrics: bool = True,
    level: Optional[str] = None
):
    """Log message with optional system message truncation"""
    _logger = log_debug
    if level == "info":
        _logger = log_info
    elif level == "warning":
        _logger = log_warning
    elif level == "error":
        _logger = log_error

    # ... implementation from agno_custom/utils/custom_message_logger.py
    # See lines 26-116
```

**Modify:** `libs/agno/agno/models/base.py`
```python
# Add import
from agno.utils.custom_message_logger import log_message
import os

# Add configuration
SYSTEM_MESSAGE_TRUNCATE_LENGTH = int(
    os.getenv("AGNO_SYSTEM_MESSAGE_LOG_TRUNCATE_LENGTH", "0")
)

# Update _log_messages function
def _log_messages(messages: List[Message]) -> None:
    for m in messages:
        if SYSTEM_MESSAGE_TRUNCATE_LENGTH > 0:
            log_message(
                m,
                system_message_truncate_length=SYSTEM_MESSAGE_TRUNCATE_LENGTH,
                metrics=False
            )
        else:
            m.log(metrics=False)
```

---

#### 2. Token Counter Replacement
**Add to:** `libs/agno/agno/utils/token_counter.py` (NEW FILE)

**Code:**
```python
from typing import Union, List
import tiktoken

def count_tokens(
    messages: Union[str, List],
    model_encoding: str = "cl100k_base"
) -> int:
    """Count tokens using tiktoken"""
    try:
        encoding = tiktoken.get_encoding(model_encoding)
    except KeyError:
        encoding = tiktoken.get_encoding("cl100k_base")

    if isinstance(messages, str):
        return len(encoding.encode(messages))

    # Handle message list
    num_tokens = 0
    for message in messages:
        if isinstance(message, dict):
            for key, value in message.items():
                num_tokens += len(encoding.encode(str(value)))
        elif hasattr(message, 'to_dict'):
            for key, value in message.to_dict().items():
                num_tokens += len(encoding.encode(str(value)))
        else:
            num_tokens += len(encoding.encode(str(message)))

    return num_tokens
```

**Update:** `libs/agno/pyproject.toml`
```toml
dependencies = [
    # ... existing dependencies ...
    "tiktoken",
]
```

**Replace imports in:**
- `libs/agno/agno/memory/` files
- `libs/agno/agno/team/team.py`

From: `from banavo.utils.token_counter import count_tokens`
To: `from agno.utils.token_counter import count_tokens`

---

#### 3. Token-Based History Management
**Add to:** `libs/agno/agno/agent/agent.py`

**Code:**
```python
# Add parameter around line 145
# This parameter is used to get the most recent runs' messages
# that fit within a token budget
max_tokens_from_history: Optional[int] = None
```

**Add to:** `libs/agno/agno/memory/memory.py`

**Code:**
```python
# Add method around line 752
def get_max_messages_from_history(
    self,
    session_id: str,
    max_tokens: int,
    agent_id: Optional[str] = None,
    team_id: Optional[str] = None,
    skip_role: Optional[str] = None,
    skip_history_messages: bool = True,
    model_encoding: str = "cl100k_base",
) -> List[Message]:
    """Fetch the most recent runs' messages that fit within a token budget.

    # ... full implementation from agno_custom/memory/memory.py:754-849
    """
```

**Update Agent to use it:**
```python
# In agent/agent.py where history is loaded
if self.max_tokens_from_history:
    messages_from_history = self.memory.get_max_messages_from_history(
        session_id=session_id,
        max_tokens=self.max_tokens_from_history,
        agent_id=self.agent_id,
        # ... other params
    )
else:
    messages_from_history = self.memory.get_messages_from_last_n_runs(
        session_id=session_id,
        last_n=self.num_history_runs,
        agent_id=self.agent_id,
        # ... other params
    )
```

---

### Important Additions (Should Have)

#### 4. Model.log_messages Flag
**Modify:** `libs/agno/agno/models/base.py`

**Code:**
```python
@dataclass
class Model(ABC):
    # ... existing fields ...

    # Flag to enable/disable the logging of all in context messages
    # before beginning model execution loop
    log_messages: bool = True
```

**Update all response methods:**
```python
def response(self, messages, ...):
    if self.log_messages:  # ADD THIS CHECK
        _log_messages(messages)
    # ... rest of method

async def aresponse(self, messages, ...):
    if self.log_messages:  # ADD THIS CHECK
        _log_messages(messages)
    # ... rest of method

def response_stream(self, messages, ...):
    if self.log_messages:  # ADD THIS CHECK
        _log_messages(messages)
    # ... rest of method

async def aresponse_stream(self, messages, ...):
    if self.log_messages:  # ADD THIS CHECK
        _log_messages(messages)
    # ... rest of method
```

---

#### 5. Selective Agent Content Return
**Add to:** `libs/agno/agno/tools/function.py`

**Code:**
```python
class Function(BaseModel):
    # ... existing fields ...

    # Allow tool function to specify which downstream agent outputs
    # to include in the function call output. If not set, all are included.
    agent_ids_to_return_content_for: Optional[List[str]] = None
```

**Modify:** `libs/agno/agno/models/base.py` in `arun_function_calls()` method

**Code:**
```python
# Around line 1574 in async for loop handling AsyncIterator results
elif isinstance(fc.result, (AsyncGeneratorType, collections.abc.AsyncIterator)):
    async for item in fc.result:
        if isinstance(item, tuple(get_args(RunResponseEvent))) or isinstance(
            item, tuple(get_args(TeamRunResponseEvent))
        ):
            if isinstance(item, RunResponseContentEvent) or isinstance(
                item, TeamRunResponseContentEvent
            ):
                # ADD THIS FILTER:
                agent_id = getattr(item, "agent_id", None) or getattr(item, "team_id", None)
                if (
                    fc.function.agent_ids_to_return_content_for is None
                    or agent_id in fc.function.agent_ids_to_return_content_for
                ):
                    function_call_output += item.content or ""

                if fc.function.show_result:
                    yield ModelResponse(content=item.content)

                yield item
```

---

#### 6. Limited Team Member Interactions
**Add to:** `libs/agno/agno/memory/memory.py`

**Code:**
```python
# Modify method signature around line 1142
def get_team_member_interactions_str(
    self,
    session_id: str,
    max_interactions_to_share: int = None  # ADD THIS PARAMETER
) -> str:
    if not self.team_context:
        return ""

    # ... existing code ...

    # ADD THIS LOGIC:
    interactions_added = 0
    for interaction in reversed(session_team_context.member_interactions):
        # ... build interaction_str ...

        team_member_interactions_str = interaction_str + team_member_interactions_str
        interactions_added += 1
        if max_interactions_to_share and interactions_added >= max_interactions_to_share:
            break
```

---

### Optional Additions (Nice to Have)

#### 7. Session State in Response
**Add to:** `libs/agno/agno/agent/agent.py`

**Code:**
```python
# Add parameter in __init__
self.include_session_state_in_response = include_session_state_in_response

# Add logic in response methods around line 1272
if self.include_session_state_in_response:
    log_debug("Adding agent session state to run response")
    # Add session_state to response
```

---

#### 8. Enhanced Memory Instructions
**Modify:** `libs/agno/agno/agent/agent.py` around lines 4421-4422

**Code:**
```python
system_message_content += "\n</memories_from_previous_interactions>\n\n"
system_message_content += (
    "Note: this information is from previous interactions and may be "
    "updated in this conversation. You should always prefer information "
    "from this conversation over the past memories.\n\n"
)
```

---

### Bugfixes to Include

#### 9. Session State Reset Fix
**Modify:** `libs/agno/agno/agent/agent.py` around line 611

**Code:**
```python
def reset_session_state(self) -> None:
    self.session_name = None
    # NOTE: Do not reset session states if being used by team
    # Let team handle state management on transfer
    # self.session_state = None
    # self.team_session_state = None
```

**Note:** This may need team context to determine when to skip reset

---

#### 10. TeamMemberInteraction from Teams Support
**Modify:** `libs/agno/agno/memory/memory.py` around line 50

**Code:**
```python
@classmethod
def from_dict(cls, data: Dict[str, Any]) -> "TeamMemberInteraction":
    member_response = data["response"]
    # Support creating from Teams (TeamRunResponse)
    if "team_id" in member_response:
        return cls(
            member_name=data["member_name"],
            task=data["task"],
            response=TeamRunResponse.from_dict(member_response)
        )
    return cls(
        member_name=data["member_name"],
        task=data["task"],
        response=RunResponse.from_dict(member_response)
    )
```

---

## Migration Checklist for Fork

### Critical (Must Implement)
- [ ] 1. Add `custom_message_logger.py` with truncation support
- [ ] 2. Add `token_counter.py` using tiktoken
- [ ] 3. Add token-based history management (`get_max_messages_from_history`)
- [ ] 4. Update all banavo imports to use new token_counter
- [ ] 5. Add environment variable support for `AGNO_SYSTEM_MESSAGE_LOG_TRUNCATE_LENGTH`

### Important (Should Implement)
- [ ] 6. Add `Model.log_messages` flag
- [ ] 7. Add `Function.agent_ids_to_return_content_for`
- [ ] 8. Add `max_interactions_to_share` parameter
- [ ] 9. Update `arun_function_calls` with selective content filter

### Optional (Nice to Have)
- [ ] 10. Add `include_session_state_in_response`
- [ ] 11. Add enhanced memory instructions

### Bugfixes
- [ ] 12. Fix session state reset issue
- [ ] 13. Fix TeamMemberInteraction from_dict for Teams

## Effort Estimate

| Category | Files to Modify | New Files | Lines of Code | Estimated Time |
|----------|----------------|-----------|---------------|----------------|
| **Critical** | 4 | 2 | ~250 | 6-8 hours |
| **Important** | 3 | 0 | ~50 | 2-3 hours |
| **Optional** | 2 | 0 | ~20 | 1 hour |
| **Bugfixes** | 2 | 0 | ~10 | 30 min |
| **Testing** | - | - | - | 4-6 hours |
| **TOTAL** | 11 files | 2 files | ~330 lines | **14-19 hours** |

## Configuration Required After Migration

### Environment Variables
```bash
# Set in .env file or environment
AGNO_SYSTEM_MESSAGE_LOG_TRUNCATE_LENGTH=500  # Or any desired length, 0 to disable
```

### Agent Configuration Examples

**Before (agno_custom):**
```python
from agno_custom.agent import Agent
from banavo.config.settings import SETTINGS

agent = Agent(
    max_tokens_from_history=4000,  # Custom feature
    # ... other params
)
```

**After (Agno fork):**
```python
from agno.agent import Agent
import os

# Set truncation via env var
os.environ["AGNO_SYSTEM_MESSAGE_LOG_TRUNCATE_LENGTH"] = "500"

agent = Agent(
    max_tokens_from_history=4000,  # Now supported in fork
    model=OpenAIChat(id="gpt-4", log_messages=True),  # Now supported
    # ... other params
)
```

## Conclusion

**Total Custom Code:**  ~330 lines to add to official Agno

**Original Custom Code:** 17,303 lines

**Reduction:** 98% reduction in custom code maintenance

**Migration Effort:** 2-3 days

**Ongoing Maintenance:** Minimal (just sync with upstream)
