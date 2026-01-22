# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Agno is a multi-agent framework, runtime and control plane built for speed, privacy, and scale. It provides tools for building Agents, Multi-Agent Teams, and Step-based Workflows, along with AgentOS - a production-ready FastAPI runtime.

## Important: agno_custom Directory

**NOTE**: The `agno_custom/` directory is a legacy custom implementation and should NOT be used for new development. It contains a parallel implementation of Agno with specific customizations for the Banavo project.

**For migration from agno_custom to official Agno framework, see:** `MIGRATION_FROM_AGNO_CUSTOM.md`

This migration guide provides:
- Analysis of custom features in agno_custom
- Step-by-step instructions to create an Agno fork with custom features
- Code migration strategy from agno_custom to official framework
- Testing and validation procedures

## Development Commands

### Setup
```bash
# Clone repository and setup development environment
./scripts/dev_setup.sh  # Unix
# or
.\scripts\dev_setup.bat  # Windows

# Activate virtual environment
source .venv/bin/activate  # Unix
.venv\Scripts\activate     # Windows
```

### Testing
```bash
# Run all tests with coverage
./scripts/test.sh

# Run specific test file
pytest ./libs/agno/tests/unit/utils/test_string.py

# Run specific test case
pytest ./libs/agno/tests/unit/utils/test_string.py::test_function_name
```

### Code Quality
```bash
# Format code (uses ruff)
./scripts/format.sh

# Validate code (uses mypy for type checking)
./scripts/validate.sh
```

### Running Examples
```bash
# Setup cookbook environment
./scripts/cookbook_setup.sh
source .venvs/cookbookenv/bin/activate

# Run any cookbook example
python cookbook/agents/basic_agent.py
```

## Architecture Overview

Agno uses a hierarchical composition model with three core execution abstractions:

### 1. Agent (Execution Layer)
The fundamental execution unit in `libs/agno/agno/agent/agent.py`. Each Agent combines:
- **Model**: LLM for reasoning (supports 40+ providers)
- **Tools**: Functions/Toolkits for actions (100+ built-in)
- **Knowledge**: RAG with 20+ vector databases
- **Memory**: User memory across sessions via MemoryManager
- **Culture**: Collective knowledge via CultureManager
- **Database**: Persistence for sessions, history, metrics

### 2. Team (Coordination Layer)
Found in `libs/agno/agno/team/team.py`. Coordinates multiple Agents/Teams with:
- **Team Leader**: Designated Agent that delegates and coordinates
- **Members**: List of Agents or Teams (recursive composition)
- **Coordination Modes**: delegate_task_to_all_members, determine_input_for_members, respond_directly, share_member_interactions
- **Shared State**: Session state and context propagation across members

### 3. Workflow (Orchestration Layer)
Located in `libs/agno/agno/workflow/`. Provides deterministic execution with:
- **Steps**: Sequential, parallel, conditional, loops, routing
- **Executors**: Steps can be Agents, Teams, or Python functions
- **State Management**: Session state flows through steps
- **Error Handling**: Retry policies, skip-on-failure, timeouts

### Composition Pattern
Workflows compose Teams → Teams compose Agents. All three are independently runnable and can be nested.

## Critical Performance Rules

**NEVER create agents in loops** - Agents should be instantiated once and reused:
```python
# WRONG - Massive performance hit
for query in queries:
    agent = Agent(...)  # DON'T DO THIS
    agent.run(query)

# CORRECT - Create once, reuse
agent = Agent(...)
for query in queries:
    agent.run(query)
```

This is critical because Agno Agents are optimized for ~3μs instantiation and ~6.6KiB memory footprint, but creating them repeatedly negates these benefits.

## Database and Persistence

### Database Strategy
Abstract `BaseDb` interface with 10+ implementations in `libs/agno/agno/db/`:
- **SQL**: PostgreSQL (production), SQLite (dev only), MySQL, SingleStore
- **NoSQL**: MongoDB, DynamoDB, Firestore, SurrealDB
- **In-Memory**: InMemoryDb, JSON files

### Storage Schemas
The database stores:
- Sessions (agent_id, team_id, workflow_id, user_id)
- Messages (conversation history)
- User Memories (semantic user knowledge)
- Cultural Knowledge (team-wide patterns)
- Metrics (performance tracking)
- Knowledge Content Metadata

**Production Rule**: Always use PostgreSQL in production, SQLite for development only.

## AgentOS Runtime Architecture

Located in `libs/agno/agno/os/`. AgentOS is a FastAPI-based production runtime:

### Key Components
- **AgentOS** (`app.py`): Assembles multi-agent systems, configures FastAPI routers
- **Router** (`router.py`): Dispatches to agents/teams/workflows, handles SSE streaming
- **WebSocket Manager**: Real-time streaming for workflow execution
- **Modular Routers** (`routers/`): Separate endpoints for agents, teams, workflows, knowledge, memory, metrics, sessions

### Design Principles
- **Stateless**: AgentOS instances hold no state; database is source of truth
- **Horizontally Scalable**: Multiple instances can run in parallel
- **SSE Streaming**: Server-Sent Events for real-time updates without WebSocket overhead
- **Async-First**: All operations prefer async for non-blocking I/O

### Configuration
Uses `AgentOSConfig` in `libs/agno/agno/os/config.py` with support for:
- YAML configuration files
- Python code overrides
- Database mapping for sessions, metrics, memory, knowledge

## Model Integration

Models are in `libs/agno/agno/models/` with 40+ provider implementations.

### Adding New Model Providers
- If OpenAI-compatible: Inherit from `OpenAILike` in `models/openai/like.py`
- If custom API: Implement `Model` base class from `models/base.py`
- Add to `models/utils.py` in the `get_model()` function to enable string syntax like `model="provider:model-name"`

### Model Capabilities
All models support unified interface for:
- Tool calling (native format conversion)
- Streaming (async generators)
- Structured output (response schema validation)
- Vision (image/video input)
- Reasoning (extended thinking for compatible models)

## Tool Execution Framework

Tools are in `libs/agno/agno/tools/`.

### Tool Structure
- **Function**: Pydantic model with name, description, parameters, entrypoint
- **Toolkit**: Groups related functions with filtering, confirmation, caching
- **Hooks**: pre_hook and post_hook for middleware around execution

### Tool Resolution Flow
1. Agent collects tools from self.tools list
2. Model receives tool definitions in system message
3. Model calls tools by name with parameters
4. Runtime executes via Function.entrypoint()
5. Hooks process pre/post execution

## Knowledge and RAG

Knowledge system is in `libs/agno/agno/knowledge/`.

### Knowledge Pipeline
- **Content Sources**: Paths, URLs, text, topics, remote (S3/GCS)
- **Readers**: Document parsers for PDF, DOCX, PPTX, CSV, Markdown
- **Chunking**: Text splitting strategies
- **Embeddings**: Document embedding generation
- **VectorDB**: Storage in 20+ vector databases
- **Search**: Hybrid search with optional reranking

### Vector Database Integration
Abstract `VectorDb` base class in `libs/agno/agno/vectordb/base.py` with implementations for:
Qdrant, Pinecone, Weaviate, Chroma, PGVector, Redis, Milvus, LanceDB, and more.

All implement: create(), delete(), upsert(), search() with async variants.

### RAG at Runtime
Enable with `search_knowledge=True` on Agent. At runtime:
1. Agent.run() triggers knowledge.search()
2. Optional reranking of results
3. Results injected into context automatically

## Memory Systems

### Three Memory Levels

**Session Memory** (via Database)
- Conversation history per session
- Indexed by session_id, user_id, agent_id
- Enable with `add_history_to_context=True` on Agent

**User Memory** (via MemoryManager in `libs/agno/agno/memory/`)
- Semantic user knowledge across sessions
- Methods: add_memories(), search_memories(), update_memories(), delete_memories()
- Scoped to user_id for multi-tenancy

**Culture** (via CultureManager in `libs/agno/agno/culture/`)
- Collective team-wide knowledge
- Patterns and behaviors that evolve over time
- Methods: add_knowledge(), update_knowledge(), delete_knowledge()

## Advanced Features

### Structured Output
Use `output_schema` parameter with Pydantic BaseModel for type-safe responses:
```python
class Result(BaseModel):
    summary: str
    findings: list[str]

agent = Agent(model=model, output_schema=Result)
result: Result = agent.run(query).content
```

### Guardrails
Located in `libs/agno/agno/guardrails/`. Implement `BaseGuardrail` for:
- Prompt injection protection
- Output validation
- Cost limits
- Custom validation logic

Can be used directly as pre_hooks.

### Hooks System
Multiple levels of hooks for cross-cutting concerns:
- **Agent.pre_hooks**: Validation before execution
- **Agent.post_hooks**: Output transformation
- **Agent.tool_hooks**: Middleware around all tool calls
- **Tool.pre_hook**: Setup before specific tool
- **Tool.post_hook**: Processing after specific tool

### Model Context Protocol (MCP)
First-class MCP support in `libs/agno/agno/tools/mcp/`:
- Tool server lifecycle management
- Dynamic tool discovery
- Connection management in AgentOS lifespan

### Reasoning Models
Support for extended thinking in `libs/agno/agno/reasoning/`:
- ReasoningStep model captures step-by-step thinking
- Included in RunOutput.reasoning_steps
- Streamed via reasoning_step events
- Supports models like DeepSeek R1

## Request/Response Flow

### RunContext (libs/agno/agno/run/context.py)
All executions flow through RunContext:
- run_id, session_id, user_id
- dependencies: Injected variables for dynamic context
- knowledge_filters: RAG filtering parameters
- session_state: Persistent cross-run state
- metadata: Telemetry and tracking

### RunOutput (libs/agno/agno/run/output.py)
Unified response structure:
- messages: Full conversation history
- media: Images, videos, audio, files
- reasoning_steps: Step-by-step thinking
- metrics: Latency, tokens, costs
- citations: Knowledge references
- session_summary: Auto-generated abstracts

### Streaming Events
Event-driven architecture with RunOutputEvent types:
- run_started, run_continued, run_completed
- tool_call_started, tool_call_completed
- reasoning_step (for reasoning models)
- parser_model_response_started
- Custom events via CustomEvent

## Code Organization

```
libs/agno/agno/
├── agent/          - Agent class (core execution unit)
├── team/           - Team class (multi-agent coordination)
├── workflow/       - Workflow orchestration + step types
├── models/         - 40+ LLM provider implementations
├── tools/          - 100+ built-in tools + framework
├── knowledge/      - RAG pipeline (chunking, embedding, search)
├── vectordb/       - 20+ vector database implementations
├── db/             - 10+ database backends + schemas
├── memory/         - MemoryManager (semantic user memory)
├── culture/        - CultureManager (collective knowledge)
├── session/        - Session objects for Agent/Team/Workflow
├── run/            - RunContext, RunOutput, RunEvents
├── os/             - AgentOS runtime, routers, WebSocket
├── guardrails/     - Safety and validation framework
├── reasoning/      - Reasoning step models
└── media/          - Image, Video, Audio, File abstractions

cookbook/           - Hundreds of usage examples
libs/agno_infra/    - Infrastructure utilities (Docker, AWS)
```

## Contributing Guidelines

From `CONTRIBUTING.md`:

### Pull Request Format
- Title must start with type tag: `[feat]`, `[fix]`, `[docs]`, `[test]`, `[refactor]`, `[build]`, `[ci]`, `[chore]`, `[perf]`, `[style]`, `[revert]`
- Description should reference issue: `fixes #42`, `closes #42`, `resolves #42`

### Adding New Components

**New Vector Database:**
1. Create class in `libs/agno/agno/vectordb/<db_name>/<db_name>.py`
2. Implement `VectorDb` interface from `vectordb/base.py`
3. Add recipe in `cookbook/knowledge/vector_db/<db_name>/`

**New Model Provider:**
1. If OpenAI-compatible: inherit from `OpenAILike`
2. If custom: implement `Model` base class
3. Add to `models/utils.py` get_model() function
4. Add recipe in `cookbook/models/<provider>/`

**New Tool:**
1. Create class inheriting `Toolkit` from `tools/toolkit.py`
2. Register all functions via flags
3. Add recipe in `cookbook/tools/<tool>/`

### Code Quality Standards
- Use `uv pip install` for package management (uv must be installed)
- Run `./scripts/format.sh` before commits (uses ruff)
- Run `./scripts/validate.sh` for type checking (uses mypy)
- Add test coverage for new features
- Line length: 120 characters (configured in pyproject.toml)

## Pattern Selection Guide

From `.cursorrules`:

**Use Single Agent** (90% of use cases):
- One clear task or domain
- Solvable with tools + instructions
- Example: Search, analyze, generate content

**Use Team** (autonomous coordination):
- Multiple specialized agents with different expertise
- Agents decide coordination via LLM
- Complex tasks requiring multiple perspectives
- Example: Research + Analysis + Writing

**Use Workflow** (programmatic control):
- Sequential steps with clear flow
- Need conditional logic or branching
- Full control over execution order
- Example: Extract → Transform → Load pipelines

## Documentation Resources

- Docs: https://docs.agno.com
- LLM-optimized docs: https://docs.agno.com/llms-full.txt
- Community: https://community.agno.com
- Discord: https://discord.gg/4MtYHHrgA8
- Examples: cookbook/ directory (hundreds of examples)

## Key Design Principles

1. **Stateless by Design**: AgentOS is stateless; database is source of truth
2. **Composition Over Inheritance**: Agent/Team/Workflow are independent, composable dataclasses
3. **Plugin Architecture**: Everything is pluggable (databases, models, tools, vector stores)
4. **Async-First**: All operations prefer async with sync compatibility
5. **Context Injection**: Dependencies and state flow through RunContext, not global state
6. **Performance Optimized**: 3μs instantiation, 6.6KiB memory per Agent
7. **Multi-Tenant**: user_id throughout for isolation
8. **Event-Driven**: SSE streaming for real-time updates
