# Phase 1: Git Tags + Docker - Detailed Explanation

**Document Version:** 1.0
**Last Updated:** 2025-12-16
**Target Audience:** Technical teams implementing Phase 1 deployment strategy

---

## Table of Contents

- [Core Concept](#core-concept)
- [The Complete Workflow](#the-complete-workflow)
- [Source Control Foundation](#1-source-control-foundation)
- [Git Tags as Version Control](#2-the-git-tag-as-version-control)
- [Automated CI/CD Pipeline](#3-automated-cicd-pipeline-github-actions)
- [Docker Image as Deployment Unit](#4-the-docker-image-as-the-deployment-unit)
- [Production Deployment](#5-production-deployment-kubernetes-example)
- [Day-to-Day Operations](#6-day-to-day-operations)
- [Why This is Production-Ready](#7-why-this-approach-is-production-ready)
- [Resource Requirements](#8-resource-requirements)
- [What You're NOT Doing](#9-comparison-what-youre-not-doing)
- [Success Stories](#10-success-stories)
- [Summary](#summary-why-phase-1-works)

---

## Core Concept

### What Phase 1 Is

A production deployment strategy that uses **Git version control** for source management and **Docker containers** for runtime distribution. Instead of publishing Python packages to PyPI, you version the code with Git tags and distribute the entire application as pre-built Docker images.

### Why It Works

Combines the immutability and reproducibility of containers with the version control of Git, creating a deployment pipeline that's both simple and production-grade.

**Key Principle:** The Git tag represents your source code version, and the Docker image is the compiled artifact ready for deployment.

---

## The Complete Workflow

### Overview Diagram

```
┌─────────────────────────────────────────────────────────────┐
│  Step 1: Source Control                                     │
│  Developer commits to fork, creates Git tag                 │
│  Repository: github.com/andromeda360/agno                   │
└────────────────────────┬────────────────────────────────────┘
                         │ git push origin v2.2.11-andromeda360.1
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  Step 2: Automated Testing                                  │
│  GitHub Actions triggered by tag                            │
│  - Run unit tests                                           │
│  - Run integration tests                                    │
│  - Security scan dependencies                               │
└────────────────────────┬────────────────────────────────────┘
                         │ Tests pass ✓
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  Step 3: Docker Image Build                                 │
│  Multi-stage Dockerfile compilation                         │
│  - Install dependencies                                     │
│  - Build minimal runtime image                              │
│  - Tag: agno-andromeda360:2.2.11-andromeda360.1            │
└────────────────────────┬────────────────────────────────────┘
                         │ Build complete
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  Step 4: Push to Registry                                   │
│  Upload to AWS ECR                                          │
│  Image: 123.dkr.ecr.../agno:2.2.11-andromeda360.1          │
└────────────────────────┬────────────────────────────────────┘
                         │ Upload complete
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  Step 5: Security Scanning                                  │
│  Trivy scans for vulnerabilities                            │
│  - OS packages                                              │
│  - Python dependencies                                      │
│  - Known CVEs                                               │
└────────────────────────┬────────────────────────────────────┘
                         │ Scan pass ✓
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  Step 6: GitHub Release                                     │
│  Create release with metadata                               │
│  - Changelog                                                │
│  - Image digest                                             │
│  - Security report                                          │
└────────────────────────┬────────────────────────────────────┘
                         │ Ready for deployment
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  Step 7: Production Deployment                              │
│  Deploy to Kubernetes/ECS                                   │
│  - Pull image from ECR                                      │
│  - Rolling update (zero downtime)                           │
│  - Health checks                                            │
└─────────────────────────────────────────────────────────────┘
```

---

## 1. Source Control Foundation

### Your Fork Setup

```
github.com/andromeda360/agno (your organization's fork)
│
├── Branch: main (synced with upstream)
│   └── Tracks official agno-ai/agno repository
│
├── Branch: custom/andromeda360-integration
│   └── Your custom features:
│       ├── Custom message logger with truncation
│       ├── Model.log_messages flag
│       ├── Selective agent content return
│       └── Built-in token counter
│
└── Tags: Production releases
    ├── v2.2.11-andromeda360.1 (Initial release)
    ├── v2.2.11-andromeda360.2 (Bug fix)
    ├── v2.2.11-andromeda360.3 (Feature addition)
    └── v2.2.12-andromeda360.1 (Upstream sync)
```

### Why a Fork?

**You need custom features:**
- Your organization has specific requirements (message logger, token counter, etc.)
- These features are proprietary or Andromeda360-specific
- Can't be merged into upstream Agno

**You want to sync with upstream Agno updates:**
```bash
# Add upstream remote
git remote add upstream https://github.com/agno-ai/agno.git

# Sync with upstream (monthly or quarterly)
git fetch upstream
git checkout main
git merge upstream/main
git push origin main

# Rebase your custom branch
git checkout custom/andromeda360-integration
git rebase main
# Resolve conflicts, test
git push origin custom/andromeda360-integration --force-with-lease
```

**You maintain control over what goes to production:**
- Main branch tracks upstream (for reference)
- Custom branch is what you actually deploy
- Tags mark production-ready snapshots

**Clear separation:**
```
Upstream changes → main branch → reviewed → merged into custom branch → tagged → deployed
```

### Version Tagging Strategy

**Format:** `v{UPSTREAM_VERSION}-andromeda360.{CUSTOM_RELEASE}`

**Breakdown:**
- `v` - Version prefix (Git convention)
- `2.2.11` - Based on official Agno version 2.2.11
- `andromeda360` - Your organization identifier
- `.1` - First release of your custom features for this Agno version

**Example Progression:**

| Tag | Meaning |
|-----|---------|
| `v2.2.11-andromeda360.1` | Initial custom release based on Agno 2.2.11 |
| `v2.2.11-andromeda360.2` | Bug fix - same Agno version, second custom release |
| `v2.2.11-andromeda360.3` | Another patch - third custom release |
| `v2.2.12-andromeda360.1` | Upgraded to Agno 2.2.12 + your custom features |
| `v2.2.12-andromeda360.2` | Bug fix on the 2.2.12 base |

**Why this format?**
- Clear upstream dependency tracking
- Semantic versioning compatibility
- Easy to sort chronologically
- Grep-friendly for automation

---

## 2. The Git Tag as Version Control

### Creating a Production Tag

```bash
# You've made changes to your fork
git checkout custom/andromeda360-integration
git add libs/agno/agno/utils/custom_message_logger.py
git commit -m "feat: Add custom message truncation

- Truncate messages to 200 chars for cleaner logs
- Configurable via AGNO_MESSAGE_MAX_LENGTH env var
- Preserves full messages in database"

# Run tests locally (IMPORTANT!)
./scripts/test.sh
# ✓ All 1,247 tests passed
# ✓ Coverage: 87%

# Create annotated tag (not lightweight tag)
git tag -a v2.2.11-andromeda360.1 -m "Production Release v2.2.11-andromeda360.1

Features:
- Custom message logger with 200 char truncation
- Model.log_messages flag (default: true)
- Selective agent content in tool calls
- Built-in tiktoken token counter

Based on: Agno v2.2.11
Tested: ✓ Unit tests (1,247 passed), ✓ Integration tests (89 passed)
Security: ✓ Dependency scan clean
Approved-By: Jane Doe <jane@andromeda360.com>
JIRA: AGNO-123, AGNO-124"

# Push tag to trigger CI/CD
git push origin v2.2.11-andromeda360.1
```

### Annotated vs Lightweight Tags

**Lightweight tag (DON'T use for production):**
```bash
git tag v2.2.11-andromeda360.1  # No message, no metadata
```

**Annotated tag (USE for production):**
```bash
git tag -a v2.2.11-andromeda360.1 -m "Message"
```

**Why annotated?**
- Stores tagger name, email, timestamp
- Can include detailed release notes
- Can be GPG-signed for verification
- Shows up in `git describe` output
- Required by most CD tools

### Tag Best Practices

**DO:**
- ✅ Test thoroughly before tagging
- ✅ Include descriptive release notes
- ✅ Reference JIRA tickets or issues
- ✅ List breaking changes explicitly
- ✅ Tag from a clean working tree

**DON'T:**
- ❌ Tag untested code
- ❌ Move or delete production tags
- ❌ Tag from feature branches (use custom branch)
- ❌ Use vague messages like "new release"

### Why Tags Instead of Branches?

| Aspect | Branch | Tag |
|--------|--------|-----|
| **Mutability** | Can change | Immutable |
| **Purpose** | Ongoing development | Snapshot in time |
| **Deployment** | Unstable reference | Stable reference |
| **Semantics** | "Latest code" | "Release v1.0" |
| **CI/CD** | Triggers on every push | Triggers on tag only |

**Example Problem with Branches:**

```bash
# Using branch for deployment (BAD)
kubectl set image deployment/agno \
  agno=...agno@custom/andromeda360-integration  # Which commit?

# Problem: custom/andromeda360-integration moves forward
# What you deployed yesterday ≠ what deploys today

# Using tag for deployment (GOOD)
kubectl set image deployment/agno \
  agno=...agno:2.2.11-andromeda360.1  # Exact version

# This always refers to the same code
```

---

## 3. Automated CI/CD Pipeline (GitHub Actions)

### Pipeline Overview

When you push a tag, GitHub Actions executes a 6-stage pipeline (total time: ~25-35 minutes):

```
Tag Push → Test → Build → Push → Scan → Release → Ready to Deploy
  (0s)     (8m)    (12m)   (3m)    (5m)    (1m)      (Total: 29m)
```

### Stage 1: Test (5-10 minutes)

**What happens:**

```yaml
# .github/workflows/production-release.yml
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code at tag
        uses: actions/checkout@v4
        # Checks out the exact commit the tag points to

      - name: Setup Python 3.11
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'  # Cache dependencies for speed

      - name: Install dependencies
        run: |
          pip install uv
          cd libs/agno
          uv pip install --system ".[dev]"
          # Installs Agno with dev dependencies (pytest, mypy, ruff)

      - name: Run test suite
        run: |
          ./scripts/test.sh
          # Runs all unit and integration tests

      - name: Run security scan
        run: |
          pip install safety pip-audit
          safety check  # Check for known vulnerabilities
          pip-audit     # Audit dependencies
```

**Why this matters:**

- **No broken code reaches production:** If tests fail, pipeline stops
- **Automated quality gates:** Can't forget to run tests
- **Fast feedback:** Know within 10 minutes if tag is good
- **Security first:** Vulnerabilities caught before building image

**Example failure:**

```bash
# Test fails
FAILED libs/agno/tests/unit/test_logger.py::test_message_truncation
AssertionError: Expected 200 chars, got 250

# Pipeline stops here, no Docker build
# Developer fixes bug, creates new tag v2.2.11-andromeda360.2
```

### Stage 2: Build Docker Image (10-15 minutes)

**Multi-Stage Dockerfile Deep Dive:**

#### **Stage 1: Builder**

```dockerfile
# ============================================
# STAGE 1: Builder - Compiles the application
# ============================================
FROM python:3.11-slim AS builder

# Build arguments (passed from CI/CD)
ARG AGNO_VERSION=unknown
ARG BUILD_DATE=unknown
ARG VCS_REF=unknown

# Metadata labels (OCI standard)
LABEL org.opencontainers.image.title="Agno Andromeda360"
LABEL org.opencontainers.image.version="${AGNO_VERSION}"
LABEL org.opencontainers.image.created="${BUILD_DATE}"
LABEL org.opencontainers.image.revision="${VCS_REF}"
LABEL org.opencontainers.image.vendor="Andromeda360"

WORKDIR /build

# Install build dependencies
# These are only needed during build, not runtime
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    git \              # Some pip packages need git to install
    build-essential \  # gcc, g++, make for compiling C extensions
    && rm -rf /var/lib/apt/lists/*  # Clean up to reduce image size

# Install uv (faster pip alternative from Astral)
# 10-100x faster dependency resolution
RUN pip install --no-cache-dir uv

# Copy ONLY dependency files first
# Docker layer caching: if dependencies don't change, reuse this layer
COPY libs/agno/pyproject.toml libs/agno/
COPY libs/agno_infra/pyproject.toml libs/agno_infra/

# Copy source code
COPY libs/agno/agno libs/agno/agno
COPY libs/agno_infra/agno libs/agno_infra/agno

# Install Agno with production dependencies
# Choose exactly which integrations you need
RUN cd libs/agno && \
    uv pip install --system \
    ".[openai,anthropic,postgres,redis,os,pdf,opentelemetry]" \
    --no-cache

# Why --no-cache?
# Don't store pip download cache in image (saves ~100MB)
```

**What's being installed:**

| Extra | Purpose | Dependencies Added |
|-------|---------|-------------------|
| `openai` | OpenAI/Azure models | openai SDK (~5MB) |
| `anthropic` | Claude models | anthropic SDK (~3MB) |
| `postgres` | PostgreSQL database | psycopg-binary, psycopg (~15MB) |
| `redis` | Redis caching | redis-py, redisvl (~8MB) |
| `os` | AgentOS runtime | FastAPI, uvicorn, PyJWT (~20MB) |
| `pdf` | PDF processing | pypdf, rapidocr (~25MB) |
| `opentelemetry` | Observability | OTEL SDK, exporters (~10MB) |

**Total dependencies:** ~100-150 packages, ~200MB installed

#### **Stage 2: Runtime**

```dockerfile
# ============================================
# STAGE 2: Runtime - Minimal production image
# ============================================
FROM python:3.11-slim

# Runtime arguments
ARG AGNO_VERSION=unknown
ENV AGNO_VERSION=${AGNO_VERSION}

# Security: Create non-root user
# UID 1000 is standard for first non-system user
RUN groupadd -r agno -g 1000 && \
    useradd -r -u 1000 -g agno -m -s /bin/bash agno

# Install ONLY runtime dependencies
# No build-essential, no git - just what's needed to run
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl \              # For health checks
    ca-certificates \   # For HTTPS requests
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy ONLY the installed packages from builder
# NOT the source code, NOT the build tools
# This is why multi-stage builds are powerful
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Create directories for runtime data
RUN mkdir -p /app/storage /app/logs && \
    chown -R agno:agno /app

# Switch to non-root user
# Any code runs as UID 1000, not root
USER agno

# Environment variables
ENV PYTHONUNBUFFERED=1          # Don't buffer stdout (see logs immediately)
ENV PYTHONDONTWRITEBYTECODE=1   # Don't create .pyc files
ENV PATH="/home/agno/.local/bin:${PATH}"

# Health check
# Kubernetes/ECS uses this to know if container is healthy
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Default command
# 4 workers for concurrent request handling
CMD ["uvicorn", "agno.os.app:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

**Image Size Comparison:**

| Approach | Size | Breakdown |
|----------|------|-----------|
| **Single-stage (bad)** | ~850MB | python:3.11-slim (150MB) + build tools (200MB) + packages (200MB) + source (300MB) |
| **Multi-stage (good)** | ~250MB | python:3.11-slim (150MB) + packages (100MB) |
| **Savings** | **600MB** | 71% reduction! |

**Why this matters:**
- Faster downloads from registry
- Less storage cost in ECR
- Faster container startup
- Smaller attack surface (no build tools in production)

### Docker Layer Caching

**How it works:**

```dockerfile
# Layer 1: Base image (rarely changes)
FROM python:3.11-slim
# Cached: Yes (unless Python version changes)

# Layer 2: System packages (rarely changes)
RUN apt-get update && apt-get install -y curl
# Cached: Yes

# Layer 3: Dependency files (changes occasionally)
COPY libs/agno/pyproject.toml libs/agno/
# Cached: Yes if pyproject.toml unchanged

# Layer 4: Install dependencies (changes occasionally)
RUN uv pip install --system ".[openai,postgres]"
# Cached: Yes if Layer 3 was cached
# This is the SLOW layer (2-5 minutes)

# Layer 5: Source code (changes frequently)
COPY libs/agno/agno libs/agno/agno
# Cached: No (you just changed code)
# But this is FAST (just copy files)
```

**Result:**
- First build: 12 minutes
- Rebuild after code change: 2 minutes (90% faster!)
- Rebuild after dependency change: 8 minutes

### Stage 3: Push to Registry (2-5 minutes)

```yaml
- name: Login to Amazon ECR
  id: login-ecr
  uses: aws-actions/amazon-ecr-login@v2

- name: Build and push Docker image
  uses: docker/build-push-action@v5
  with:
    context: .
    file: docker/production/Dockerfile
    push: true
    tags: |
      ${{ steps.login-ecr.outputs.registry }}/agno-andromeda360:${{ steps.version.outputs.VERSION }}
      ${{ steps.login-ecr.outputs.registry }}/agno-andromeda360:latest
    build-args: |
      AGNO_VERSION=${{ steps.version.outputs.VERSION }}
      BUILD_DATE=${{ github.event.repository.updated_at }}
      VCS_REF=${{ github.sha }}
    cache-from: type=gha     # Use GitHub Actions cache
    cache-to: type=gha,mode=max
    platforms: linux/amd64   # Build for x86_64 (most common)
```

**What gets pushed:**

```
123456789012.dkr.ecr.us-east-1.amazonaws.com/agno-andromeda360:2.2.11-andromeda360.1
├── Manifest (JSON describing layers)
├── Config (Image metadata, labels, env vars)
└── Layers:
    ├── Layer 1: python:3.11-slim base (150MB) [shared with other images]
    ├── Layer 2: System packages (5MB)
    ├── Layer 3: Python packages (95MB)
    └── Total: ~250MB
```

**Two tags created:**
- `2.2.11-andromeda360.1` - Specific version (use in production)
- `latest` - Latest build (use for development)

### Why ECR (vs Docker Hub, GCR, etc.)?

| Feature | AWS ECR | Docker Hub | Google GCR |
|---------|---------|------------|------------|
| **Integration with ECS/EKS** | Native | Via credentials | Via credentials |
| **Vulnerability scanning** | Built-in (Clair) | Paid tier only | Built-in |
| **IAM integration** | Yes | No | GCP IAM |
| **Cross-region replication** | Yes | No | Yes |
| **Lifecycle policies** | Yes | Paid tier | Yes |
| **Private by default** | Yes | Paid tier | Yes |
| **Cost** | $0.10/GB stored | $0.25/GB (paid) | $0.05/GB |

**For AWS-based deployments:** ECR is the clear choice

### Stage 4: Security Scanning (5 minutes)

```yaml
- name: Run Trivy vulnerability scanner
  uses: aquasecurity/trivy-action@master
  with:
    image-ref: ${{ steps.login-ecr.outputs.registry }}/agno-andromeda360:${{ steps.version.outputs.VERSION }}
    format: 'sarif'               # Security Alert Report Interchange Format
    output: 'trivy-results.sarif'
    severity: 'CRITICAL,HIGH'     # Focus on serious issues

- name: Upload Trivy results to GitHub Security
  uses: github/codeql-action/upload-sarif@v3
  with:
    sarif_file: 'trivy-results.sarif'
    # Results visible in GitHub Security tab

- name: Fail on critical vulnerabilities
  uses: aquasecurity/trivy-action@master
  with:
    image-ref: ${{ steps.login-ecr.outputs.registry }}/agno-andromeda360:${{ steps.version.outputs.VERSION }}
    format: 'table'
    exit-code: '1'        # Fail pipeline if CRITICAL found
    severity: 'CRITICAL'
```

**What Trivy scans:**

1. **OS Packages:**
   ```
   Debian packages in python:3.11-slim base image
   Example findings:
   - curl 7.88.0 → CVE-2023-xxxxx (HIGH)
   - openssl 1.1.1 → CVE-2023-yyyyy (CRITICAL)
   ```

2. **Python Packages:**
   ```
   PyPI packages installed via pip
   Example findings:
   - requests 2.28.0 → GHSA-xxxx (MEDIUM)
   - cryptography 40.0.0 → CVE-2023-zzzzz (HIGH)
   ```

3. **Secrets:**
   ```
   Hardcoded secrets (API keys, passwords)
   Example findings:
   - AWS_SECRET_ACCESS_KEY found in layer 5 (CRITICAL)
   ```

**Example scan result:**

```
Total: 15 vulnerabilities found
├── CRITICAL: 0
├── HIGH: 2
├── MEDIUM: 8
└── LOW: 5

HIGH vulnerabilities:
1. CVE-2023-12345 in openssl (1.1.1)
   Severity: HIGH
   Fix: Upgrade to 1.1.1w or later

2. CVE-2023-67890 in requests (2.28.0)
   Severity: HIGH
   Fix: Upgrade to 2.31.0 or later
```

**If CRITICAL found:**
- Pipeline fails ❌
- Image NOT deployed to production
- Developer notified via GitHub/Slack
- Must fix vulnerability and create new tag

### Stage 5: Create GitHub Release (1 minute)

```yaml
- name: Create Release
  uses: actions/create-release@v1
  env:
    GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
  with:
    tag_name: ${{ github.ref }}
    release_name: Agno Andromeda360 v${{ steps.version.outputs.VERSION }}
    body: |
      ## Production Release v${{ steps.version.outputs.VERSION }}

      ### Docker Image
      ```
      123456789012.dkr.ecr.us-east-1.amazonaws.com/agno-andromeda360:${{ steps.version.outputs.VERSION }}
      ```

      ### Changes
      See commits: https://github.com/andromeda360/agno/compare/v2.2.11-andromeda360.0...v${{ steps.version.outputs.VERSION }}

      ### Deployment
      ```bash
      kubectl set image deployment/agno-app \
        agno=123456789012.dkr.ecr.us-east-1.amazonaws.com/agno-andromeda360:${{ steps.version.outputs.VERSION }}
      ```

      ### Security
      - ✓ Vulnerability scan passed (0 CRITICAL, 2 HIGH)
      - ✓ All tests passed (1,247/1,247)

      ### Image Digest
      ```
      sha256:${{ steps.build.outputs.digest }}
      ```
    draft: false
    prerelease: false
```

**What appears on GitHub:**

```
Releases → v2.2.11-andromeda360.1

Published by github-actions 25 minutes ago

Docker Image: 123.ecr.../agno:2.2.11-andromeda360.1
Digest: sha256:abc123...
Tests: ✓ Passed
Security: ✓ 0 Critical vulnerabilities

[Download Source (zip)]  [Download Source (tar.gz)]
```

---

## 4. The Docker Image as the Deployment Unit

### What's Inside the Image?

```
agno-andromeda360:2.2.11-andromeda360.1 (250MB total)
│
├── Operating System Layer (150MB)
│   ├── Debian 12 (Bookworm) base
│   ├── Python 3.11.7 runtime
│   ├── Standard libraries (ssl, sqlite, etc.)
│   └── System utilities (curl, ca-certificates)
│
├── Python Packages Layer (95MB)
│   ├── Agno framework (your custom fork)
│   ├── OpenAI SDK (4MB)
│   ├── Anthropic SDK (3MB)
│   ├── PostgreSQL drivers (15MB)
│   ├── Redis client (8MB)
│   ├── FastAPI + Uvicorn (20MB)
│   ├── PDF processing (25MB)
│   ├── OpenTelemetry (10MB)
│   └── ~100 more dependencies (10MB)
│
├── Configuration Layer (5MB)
│   ├── Non-root user (agno:1000)
│   ├── Working directory (/app)
│   ├── Storage directory (/app/storage)
│   ├── Logs directory (/app/logs)
│   └── Environment variables
│
└── Metadata
    ├── Labels (version, build date, git SHA)
    ├── Health check configuration
    ├── Exposed port (8000)
    └── Default command (uvicorn)
```

### Image Manifest

```json
{
  "schemaVersion": 2,
  "mediaType": "application/vnd.docker.distribution.manifest.v2+json",
  "config": {
    "mediaType": "application/vnd.docker.container.image.v1+json",
    "size": 7234,
    "digest": "sha256:abc123..."
  },
  "layers": [
    {
      "mediaType": "application/vnd.docker.image.rootfs.diff.tar.gzip",
      "size": 157234567,
      "digest": "sha256:def456..."
    },
    {
      "mediaType": "application/vnd.docker.image.rootfs.diff.tar.gzip",
      "size": 5123456,
      "digest": "sha256:ghi789..."
    },
    {
      "mediaType": "application/vnd.docker.image.rootfs.diff.tar.gzip",
      "size": 99876543,
      "digest": "sha256:jkl012..."
    }
  ]
}
```

### Immutability Guarantee

**Once built, the image NEVER changes:**

```bash
# Pull image today
docker pull 123.ecr.../agno:2.2.11-andromeda360.1
# sha256:abc123def456...

# Pull same image in 1 year
docker pull 123.ecr.../agno:2.2.11-andromeda360.1
# sha256:abc123def456... (identical!)

# If content changes, digest changes
# If digest matches, content is byte-for-byte identical
```

**What this means:**

| Environment | Image | Behavior |
|-------------|-------|----------|
| Developer laptop | `agno:2.2.11-andromeda360.1` | ✓ Identical |
| CI/CD testing | `agno:2.2.11-andromeda360.1` | ✓ Identical |
| Staging | `agno:2.2.11-andromeda360.1` | ✓ Identical |
| Production | `agno:2.2.11-andromeda360.1` | ✓ Identical |

**No more:**
- "Works on my machine"
- "Different Python version in prod"
- "Missing dependency in production"
- "Config mismatch between envs"

### Image Verification

```bash
# Verify image integrity
docker inspect 123.ecr.../agno:2.2.11-andromeda360.1 | grep RepoDigests
# "RepoDigests": [
#   "123.ecr.../agno@sha256:abc123def456..."
# ]

# Compare with CI/CD build artifact
# If hashes match → authentic image
# If hashes differ → tampered or wrong image

# View image labels
docker inspect 123.ecr.../agno:2.2.11-andromeda360.1 --format '{{json .Config.Labels}}'
# {
#   "org.opencontainers.image.version": "2.2.11-andromeda360.1",
#   "org.opencontainers.image.created": "2025-12-16T10:30:00Z",
#   "org.opencontainers.image.revision": "a1b2c3d4e5f6",
#   "org.opencontainers.image.vendor": "Andromeda360"
# }
```

### Running the Image Locally

```bash
# Basic run
docker run -p 8000:8000 123.ecr.../agno:2.2.11-andromeda360.1

# With environment variables
docker run -p 8000:8000 \
  -e DATABASE_URL=postgresql://localhost/agno \
  -e OPENAI_API_KEY=sk-... \
  -e LOG_LEVEL=DEBUG \
  123.ecr.../agno:2.2.11-andromeda360.1

# With volume mounts
docker run -p 8000:8000 \
  -v $(pwd)/storage:/app/storage \
  -v $(pwd)/logs:/app/logs \
  123.ecr.../agno:2.2.11-andromeda360.1

# Interactive shell (debugging)
docker run -it --entrypoint /bin/bash \
  123.ecr.../agno:2.2.11-andromeda360.1

# Inside container:
agno@container:/app$ python
>>> from agno.agent import Agent
>>> print("Agno loaded successfully!")
```

---

## 5. Production Deployment (Kubernetes Example)

### Kubernetes Deployment Manifest

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: agno-app
  namespace: agno-production
  labels:
    app: agno
    version: v2.2.11-andromeda360.1
spec:
  # High Availability: 3 replicas
  replicas: 3

  # Deployment Strategy: Zero-downtime rolling updates
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1         # Add 1 extra pod during update
      maxUnavailable: 0   # Never drop below 3 pods
      # This ensures always 3+ pods serving traffic

  # Pod selector
  selector:
    matchLabels:
      app: agno

  # Pod template
  template:
    metadata:
      labels:
        app: agno
        version: v2.2.11-andromeda360.1
      annotations:
        # Prometheus scraping
        prometheus.io/scrape: "true"
        prometheus.io/port: "8000"
        prometheus.io/path: "/metrics"

    spec:
      # Service account for AWS IAM
      serviceAccountName: agno-sa

      # Pod containers
      containers:
      - name: agno
        # Exact image version (never use :latest in production)
        image: 123456789012.dkr.ecr.us-east-1.amazonaws.com/agno-andromeda360:2.2.11-andromeda360.1
        imagePullPolicy: Always  # Always check for updates

        # Exposed ports
        ports:
        - name: http
          containerPort: 8000
          protocol: TCP

        # Environment variables (configuration)
        env:
        # Secrets (from Kubernetes Secrets)
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: agno-secrets
              key: database-url

        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: agno-secrets
              key: redis-url

        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: agno-secrets
              key: openai-api-key

        # ConfigMaps (non-sensitive config)
        - name: AGNO_ENV
          value: "production"
        - name: LOG_LEVEL
          value: "INFO"
        - name: WORKERS
          value: "4"

        # Resource allocation
        resources:
          requests:
            memory: "512Mi"   # Guaranteed memory
            cpu: "500m"       # Guaranteed CPU (0.5 cores)
          limits:
            memory: "2Gi"     # Maximum memory before OOM kill
            cpu: "2000m"      # Maximum CPU (2 cores)

        # Liveness probe (is container alive?)
        livenessProbe:
          httpGet:
            path: /health
            port: http
          initialDelaySeconds: 30  # Wait 30s after startup
          periodSeconds: 10        # Check every 10s
          timeoutSeconds: 5        # 5s timeout for response
          failureThreshold: 3      # Restart after 3 failures
        # If /health fails 3 times → Kubernetes restarts pod

        # Readiness probe (is container ready for traffic?)
        readinessProbe:
          httpGet:
            path: /ready
            port: http
          initialDelaySeconds: 5   # Check soon after startup
          periodSeconds: 5         # Check every 5s
          timeoutSeconds: 3        # 3s timeout
          failureThreshold: 2      # Remove from LB after 2 failures
        # If /ready fails → Kubernetes removes from load balancer

        # Volume mounts
        volumeMounts:
        - name: storage
          mountPath: /app/storage
        - name: logs
          mountPath: /app/logs

      # Volumes
      volumes:
      - name: storage
        persistentVolumeClaim:
          claimName: agno-storage-pvc
      - name: logs
        emptyDir: {}  # Temporary, cleared on pod restart
```

### Deployment Process (Step-by-Step)

**Initial state: 3 pods running v1**

```
┌─────────────────────────────────────────┐
│         Load Balancer                   │
│  Distributes traffic evenly             │
└──────┬──────────┬──────────┬────────────┘
       │          │          │
       ▼          ▼          ▼
    [v1-pod1] [v1-pod2] [v1-pod3]
    Ready ✓   Ready ✓   Ready ✓
    100 req/s 100 req/s 100 req/s
```

**Step 1: Deploy new version**

```bash
kubectl set image deployment/agno-app \
  agno=123.ecr.../agno:2.2.11-andromeda360.2
```

**Step 2: Create one new pod (maxSurge: 1)**

```
┌─────────────────────────────────────────┐
│         Load Balancer                   │
└──────┬──────────┬──────────┬────────────┘
       │          │          │
       ▼          ▼          ▼
    [v1-pod1] [v1-pod2] [v1-pod3] [v2-pod4]
    Ready ✓   Ready ✓   Ready ✓   Starting...
    100 req/s 100 req/s 100 req/s  0 req/s

v2-pod4 logs:
  Downloading image... ████████████ 100%
  Starting uvicorn...
  Uvicorn running on 0.0.0.0:8000
  Running health check... /health → 200 OK
  Pod is ready!
```

**Step 3: Wait for readiness probe (5-10 seconds)**

```
┌─────────────────────────────────────────┐
│         Load Balancer                   │
└──────┬──────────┬──────────┬────────┬───┘
       │          │          │        │
       ▼          ▼          ▼        ▼
    [v1-pod1] [v1-pod2] [v1-pod3] [v2-pod4]
    Ready ✓   Ready ✓   Ready ✓   Ready ✓
    75 req/s  75 req/s  75 req/s  75 req/s
    (traffic now balanced across 4 pods)
```

**Step 4: Terminate one v1 pod (maxUnavailable: 0)**

```
┌─────────────────────────────────────────┐
│         Load Balancer                   │
└──────┬──────────┬──────────┬────────────┘
       │          │          │
       ▼          ▼          ▼
    [v1-pod2] [v1-pod3] [v2-pod4]
    Ready ✓   Ready ✓   Ready ✓
    100 req/s 100 req/s 100 req/s
```

**Step 5: Repeat until all v2**

```
After ~2-3 minutes:

┌─────────────────────────────────────────┐
│         Load Balancer                   │
└──────┬──────────┬──────────┬────────────┘
       │          │          │
       ▼          ▼          ▼
    [v2-pod4] [v2-pod5] [v2-pod6]
    Ready ✓   Ready ✓   Ready ✓
    100 req/s 100 req/s 100 req/s

Deployment complete ✓
All traffic on v2
Zero downtime achieved
```

### Health Check Endpoints

**Implement in your app:**

```python
# libs/agno/agno/os/app.py (or your FastAPI app)

from fastapi import FastAPI, Response, status

app = FastAPI()

@app.get("/health")
async def health_check():
    """
    Liveness probe endpoint
    Returns 200 if process is alive
    Kubernetes restarts pod if this fails
    """
    return {"status": "healthy", "version": "2.2.11-andromeda360.1"}

@app.get("/ready")
async def readiness_check():
    """
    Readiness probe endpoint
    Returns 200 if ready to serve traffic
    Kubernetes removes from LB if this fails
    """
    # Check dependencies
    try:
        # Check database connection
        await db.execute("SELECT 1")

        # Check Redis connection
        await redis.ping()

        # All good
        return {
            "status": "ready",
            "database": "connected",
            "redis": "connected"
        }
    except Exception as e:
        # Not ready, return 503
        return Response(
            content={"status": "not_ready", "error": str(e)},
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE
        )
```

### Rollback Procedure

**Scenario: v2 has a bug, need to rollback**

```bash
# View deployment history
kubectl rollout history deployment/agno-app -n agno-production
# REVISION  CHANGE-CAUSE
# 1         Initial deployment (v2.2.11-andromeda360.1)
# 2         Update to v2.2.11-andromeda360.2 (current)

# Rollback to previous version
kubectl rollout undo deployment/agno-app -n agno-production

# Kubernetes automatically:
# 1. Creates pods with v1 image
# 2. Waits for readiness
# 3. Terminates v2 pods
# 4. Restores to previous state

# Rollback time: ~2-3 minutes
# Zero downtime: Yes
```

**Or rollback to specific version:**

```bash
# Rollback to exact version
kubectl set image deployment/agno-app \
  agno=123.ecr.../agno:2.2.11-andromeda360.1 \
  -n agno-production
```

---

## 6. Day-to-Day Operations

### Making a Code Change (End-to-End)

**Day 1: Developer workflow**

```bash
# 1. Create feature branch
git checkout custom/andromeda360-integration
git pull origin custom/andromeda360-integration
git checkout -b feature/AGNO-125-improve-logging

# 2. Make changes
vim libs/agno/agno/utils/custom_message_logger.py
# Add new feature: log rotation

# 3. Test locally
./scripts/test.sh
# ✓ All 1,247 tests passed

# Run specific tests
pytest libs/agno/tests/unit/utils/test_custom_message_logger.py -v
# ✓ test_message_truncation PASSED
# ✓ test_log_rotation PASSED
# ✓ test_max_file_size PASSED

# 4. Format code
./scripts/format.sh
# Formatted 1 file

# 5. Type check
./scripts/validate.sh
# Success: no issues found

# 6. Commit
git add libs/agno/agno/utils/custom_message_logger.py
git add libs/agno/tests/unit/utils/test_custom_message_logger.py
git commit -m "feat: Add log rotation to custom message logger

- Rotate logs at 10MB
- Keep 5 rotated files
- Configurable via AGNO_LOG_MAX_SIZE env var

Closes AGNO-125"

# 7. Push and create PR
git push origin feature/AGNO-125-improve-logging
gh pr create --title "Add log rotation to custom message logger" \
  --body "Implements AGNO-125. See commit message for details."
```

**Day 2: Code review**

```bash
# Reviewer comments:
# "Please add tests for edge cases"

# Developer addresses feedback
git commit -m "test: Add edge case tests for log rotation"
git push origin feature/AGNO-125-improve-logging

# Approval received
gh pr merge --squash
# Pull request #42 merged into custom/andromeda360-integration
```

**Day 3: Create production release**

```bash
# DevOps engineer prepares release
git checkout custom/andromeda360-integration
git pull origin custom/andromeda360-integration

# Review changes since last tag
git log v2.2.11-andromeda360.2..HEAD --oneline
# a1b2c3d feat: Add log rotation to custom message logger
# d4e5f6g fix: Handle edge case in token counter
# g7h8i9j docs: Update README with new env vars

# Run full test suite
./scripts/test.sh
# ✓ All 1,250 tests passed (3 new tests added)

# Create release tag
git tag -a v2.2.11-andromeda360.3 -m "Production Release v2.2.11-andromeda360.3

Features:
- Log rotation for custom message logger (AGNO-125)
- Edge case fix in token counter (AGNO-126)

Based on: Agno v2.2.11
Tests: ✓ 1,250 passed
Security: ✓ No new vulnerabilities
Approved-By: DevOps Team
Release-Date: 2025-12-20"

# Push tag (triggers CI/CD)
git push origin v2.2.11-andromeda360.3

# Monitor CI/CD
# GitHub → Actions → "Production Release" workflow
# Status: Running... (25 minutes estimated)
```

**Day 3 (30 minutes later): CI/CD complete**

```
GitHub Actions Summary:
✓ Test (8 minutes)
✓ Build Docker (12 minutes)
✓ Push to ECR (3 minutes)
✓ Security Scan (5 minutes)
  - 0 CRITICAL vulnerabilities
  - 2 HIGH vulnerabilities (existing, not blocking)
✓ Create Release (1 minute)

Release created: https://github.com/andromeda360/agno/releases/tag/v2.2.11-andromeda360.3

Docker image available:
123456789012.dkr.ecr.us-east-1.amazonaws.com/agno-andromeda360:2.2.11-andromeda360.3
```

**Day 3: Deploy to staging**

```bash
# Deploy to staging first
kubectl set image deployment/agno-app \
  agno=123.ecr.../agno:2.2.11-andromeda360.3 \
  -n agno-staging

# Monitor rollout
kubectl rollout status deployment/agno-app -n agno-staging
# Waiting for deployment "agno-app" rollout to finish: 1 out of 3 new replicas have been updated...
# Waiting for deployment "agno-app" rollout to finish: 2 out of 3 new replicas have been updated...
# Waiting for deployment "agno-app" rollout to finish: 3 out of 3 new replicas have been updated...
# deployment "agno-app" successfully rolled out

# Verify new version
kubectl get pods -n agno-staging -o wide
# NAME                        READY   STATUS    VERSION
# agno-app-7d9f8b6c5-abc123   1/1     Running   2.2.11-andromeda360.3
# agno-app-7d9f8b6c5-def456   1/1     Running   2.2.11-andromeda360.3
# agno-app-7d9f8b6c5-ghi789   1/1     Running   2.2.11-andromeda360.3

# Test in staging
curl https://staging.agno.andromeda360.com/health
# {"status":"healthy","version":"2.2.11-andromeda360.3"}

# Run smoke tests
./scripts/smoke-tests.sh staging
# ✓ Health check passed
# ✓ Agent creation passed
# ✓ Tool execution passed
# ✓ Database connection passed
# ✓ All smoke tests passed
```

**Day 4: Deploy to production (with approval gate)**

```bash
# Request approval (manual step)
# Slack: @devops-team Ready to deploy v2.2.11-andromeda360.3 to production
# Response: ✅ Approved by Jane Doe

# Deploy to production
kubectl set image deployment/agno-app \
  agno=123.ecr.../agno:2.2.11-andromeda360.3 \
  -n agno-production

# Monitor rollout
kubectl rollout status deployment/agno-app -n agno-production --timeout=5m
# deployment "agno-app" successfully rolled out

# Verify
kubectl get deployment agno-app -n agno-production -o yaml | grep image:
# image: 123.ecr.../agno:2.2.11-andromeda360.3

# Check all pods
kubectl get pods -n agno-production
# All 3 pods running new version

# Monitor metrics
# Grafana dashboard → Agno Production
# - Request rate: Normal
# - Error rate: 0%
# - P95 latency: 250ms (within SLA)
# - Memory usage: 45% (healthy)

# Post-deployment announcement
# Slack: ✅ v2.2.11-andromeda360.3 deployed to production successfully
```

**Total time: Code change to production = 3 days**
- Day 1: Development + testing
- Day 2: Code review
- Day 3: CI/CD + staging deployment
- Day 4: Production deployment

**With hotfix urgency: Can be < 4 hours**

### Monitoring What's Running

```bash
# Which version is in production?
kubectl get deployment agno-app -n agno-production -o jsonpath='{.spec.template.spec.containers[0].image}'
# 123.ecr.../agno:2.2.11-andromeda360.3

# View deployment history
kubectl rollout history deployment/agno-app -n agno-production
# REVISION  CHANGE-CAUSE
# 1         v2.2.11-andromeda360.1 (2025-01-15)
# 2         v2.2.11-andromeda360.2 (2025-01-20)
# 3         v2.2.11-andromeda360.3 (2025-01-25)

# View available versions in ECR
aws ecr describe-images \
  --repository-name agno-andromeda360 \
  --region us-east-1 \
  --query 'sort_by(imageDetails,&imagePushedAt)[*].[imageTags[0],imagePushedAt]' \
  --output table

# +-------------------------+------------------------+
# |                         |                        |
# +-------------------------+------------------------+
# |  2.2.11-andromeda360.1  |  2025-01-15T10:30:00Z |
# |  2.2.11-andromeda360.2  |  2025-01-20T14:15:00Z |
# |  2.2.11-andromeda360.3  |  2025-01-25T09:45:00Z |
# +-------------------------+------------------------+

# Check pod logs
kubectl logs -f deployment/agno-app -n agno-production
# [2025-12-16 10:30:00] INFO: Starting AgentOS v2.2.11-andromeda360.3
# [2025-12-16 10:30:01] INFO: Database connected
# [2025-12-16 10:30:01] INFO: Redis connected
# [2025-12-16 10:30:02] INFO: Uvicorn running on 0.0.0.0:8000

# Execute command in pod
kubectl exec -it deployment/agno-app -n agno-production -- python -c "from agno import __version__; print(__version__)"
# 2.2.11-andromeda360.3
```

### Scaling Operations

```bash
# Manual scaling
kubectl scale deployment/agno-app --replicas=10 -n agno-production
# deployment.apps/agno-app scaled

# Verify
kubectl get pods -n agno-production
# NAME                        READY   STATUS
# agno-app-7d9f8b6c5-pod1    1/1     Running
# agno-app-7d9f8b6c5-pod2    1/1     Running
# ...
# agno-app-7d9f8b6c5-pod10   1/1     Running

# Scale down
kubectl scale deployment/agno-app --replicas=3 -n agno-production
```

**Auto-scaling:**

```yaml
# Already configured in deployment
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: agno-hpa
  namespace: agno-production
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: agno-app
  minReplicas: 3
  maxReplicas: 50
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  # If average CPU > 70% across pods → scale up
  # If average CPU < 70% → scale down (to min 3)
```

**Monitoring auto-scale:**

```bash
# View HPA status
kubectl get hpa agno-hpa -n agno-production
# NAME        REFERENCE             TARGETS   MINPODS   MAXPODS   REPLICAS
# agno-hpa    Deployment/agno-app   45%/70%   3         50        3

# During traffic spike:
kubectl get hpa agno-hpa -n agno-production
# NAME        REFERENCE             TARGETS   MINPODS   MAXPODS   REPLICAS
# agno-hpa    Deployment/agno-app   85%/70%   3         50        8
# Scaled up to 8 replicas due to high CPU
```

---

## 7. Why This Approach is Production-Ready

### Reproducibility

**Problem:** "It works on my machine but not in production"

**Solution:** Every environment runs the exact same Docker image

```
Developer Laptop:
  docker run 123.ecr.../agno:2.2.11-andromeda360.1
  → Python 3.11.7, Agno 2.2.11-andromeda360.1, OpenAI SDK 1.10.0

CI/CD Testing:
  docker run 123.ecr.../agno:2.2.11-andromeda360.1
  → Python 3.11.7, Agno 2.2.11-andromeda360.1, OpenAI SDK 1.10.0

Staging Environment:
  kubectl ... image: 123.ecr.../agno:2.2.11-andromeda360.1
  → Python 3.11.7, Agno 2.2.11-andromeda360.1, OpenAI SDK 1.10.0

Production:
  kubectl ... image: 123.ecr.../agno:2.2.11-andromeda360.1
  → Python 3.11.7, Agno 2.2.11-andromeda360.1, OpenAI SDK 1.10.0
```

**Result:** Same Python version, same dependencies, same behavior everywhere

### Auditability

**Who deployed what, when?**

```bash
# Kubernetes deployment history
kubectl rollout history deployment/agno-app -n agno-production
# Shows: revision number, timestamp, change cause

# Git tag history
git tag -l "v*-andromeda360*" --format="%(refname:short) - %(creatordate:short) - %(subject)"
# v2.2.11-andromeda360.1 - 2025-01-15 - Initial production release
# v2.2.11-andromeda360.2 - 2025-01-20 - Bug fixes
# v2.2.11-andromeda360.3 - 2025-01-25 - Log rotation feature

# GitHub Release notes
# Each release shows:
# - What changed (commits)
# - Who approved it
# - Test results
# - Security scan results
# - Docker image digest

# ECR image history
aws ecr describe-images --repository-name agno-andromeda360
# Shows: push timestamp, image tags, scan results
```

**Compliance questions answered:**
- "What version is in production?" → Check Kubernetes deployment
- "When was v2 deployed?" → Check deployment history
- "Who created this release?" → Check Git tag author
- "What changed in v3?" → Check GitHub release notes
- "Does v2 have vulnerabilities?" → Check Trivy scan results

### Security

**1. Vulnerability Scanning:**
```
Every image scanned before production
CRITICAL vulnerabilities → Pipeline fails
HIGH vulnerabilities → Documented and tracked
Results uploaded to GitHub Security tab
```

**2. Non-root Containers:**
```dockerfile
USER agno  # UID 1000, not root

# Even if attacker exploits app:
# - Can't modify system files
# - Can't install packages
# - Can't access other containers
# - Limited damage potential
```

**3. Immutable Infrastructure:**
```
Containers are read-only (except mounted volumes)
Can't modify running container
To make changes → build new image, deploy new version
No "SSH into prod and edit files"
```

**4. Secrets Management:**
```yaml
# No hardcoded secrets
env:
- name: OPENAI_API_KEY
  valueFrom:
    secretKeyRef:
      name: agno-secrets
      key: openai-api-key

# Secrets stored in:
# - Kubernetes Secrets (encrypted at rest)
# - AWS Secrets Manager (centralized)
# - Never in Git, never in Docker image
```

**5. Network Isolation:**
```yaml
# Kubernetes NetworkPolicy
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: agno-network-policy
spec:
  podSelector:
    matchLabels:
      app: agno
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: load-balancer
  egress:
  - to:
    - podSelector:
        matchLabels:
          app: postgres
    - podSelector:
        matchLabels:
          app: redis

# Result:
# - Agno pods can only receive traffic from load balancer
# - Agno pods can only send traffic to postgres and redis
# - All other traffic blocked
```

### Scalability

**Horizontal Scaling (Add more pods):**

```bash
# Traffic: 100 req/s → 3 pods handle it
# Traffic: 500 req/s → Auto-scale to 15 pods
# Traffic: 1000 req/s → Auto-scale to 30 pods

# Each pod:
# - Independent
# - Stateless (state in database/redis)
# - Can be added/removed instantly
```

**Real-world scenario:**

```
Normal Load:
  3 pods × 33 req/s each = 100 req/s total
  Cost: $75/month

Black Friday Sale:
  30 pods × 33 req/s each = 1000 req/s total
  Duration: 6 hours
  Cost: $75 + $15 (6 hours of extra capacity) = $90/month

After Sale:
  Auto-scales back to 3 pods
  Cost returns to $75/month
```

**Vertical Scaling (Bigger pods):**

```yaml
# If you need more memory per pod:
resources:
  requests:
    memory: "2Gi"   # Was 512Mi
    cpu: "1000m"    # Was 500m
  limits:
    memory: "4Gi"   # Was 2Gi
    cpu: "4000m"    # Was 2000m

# Deploy update
kubectl apply -f deployment.yaml
# Kubernetes rolling updates to new resource allocation
```

### Disaster Recovery

**Scenario 1: Someone deleted production cluster!**

```bash
# Total recovery time: ~45 minutes

# 1. Create new Kubernetes cluster (10 minutes)
eksctl create cluster --name production-cluster-v2

# 2. Apply manifests from Git (2 minutes)
git clone https://github.com/andromeda360/agno.git
kubectl apply -f agno/k8s/production/

# 3. Images pull from ECR automatically (5 minutes)
# Kubernetes automatically pulls: 123.ecr.../agno:2.2.11-andromeda360.3

# 4. Restore database from backup (30 minutes)
aws rds restore-db-instance-to-point-in-time \
  --source-db-instance-identifier agno-prod \
  --target-db-instance-identifier agno-prod-restored \
  --restore-time 2025-12-16T10:00:00Z

# 5. Update DNS (2 minutes)
# Point agno.andromeda360.com to new load balancer

# Total downtime: ~45 minutes
```

**Scenario 2: v3 has a critical bug!**

```bash
# Total rollback time: ~2 minutes

# 1. Rollback to v2 (2 minutes)
kubectl rollout undo deployment/agno-app -n agno-production
# Kubernetes automatically restores previous version

# 2. Verify (30 seconds)
kubectl get pods -n agno-production
# All pods running v2.2.11-andromeda360.2

# Total downtime: ~2 minutes
```

**Scenario 3: ECR region outage**

```bash
# With cross-region replication:
aws ecr put-replication-configuration \
  --replication-configuration '{
    "rules": [{
      "destinations": [{
        "region": "us-west-2",
        "registryId": "123456789012"
      }]
    }]
  }'

# During outage:
# 1. Update cluster to pull from us-west-2 ECR (5 minutes)
# 2. Deploy continues normally
# Total impact: 5 minutes to switch regions
```

---

## 8. Resource Requirements

### AWS Resources Needed

**1. ECR Repository**
```bash
# One-time setup
aws ecr create-repository \
  --repository-name agno-andromeda360 \
  --region us-east-1 \
  --image-scanning-configuration scanOnPush=true

# Storage: ~5GB (stores 20-30 images with lifecycle policy)
# Cost: $0.10/GB/month = $0.50/month
```

**2. Compute Options**

**Option A: ECS Fargate (Serverless)**
```bash
# 3 tasks (1 vCPU, 2GB RAM each)
# $0.04048/hour per vCPU = $29/month per vCPU
# $0.004445/hour per GB = $6.40/month per GB

Cost calculation:
  3 tasks × 1 vCPU × $29/month = $87/month (CPU)
  3 tasks × 2 GB × $6.40/month = $38.40/month (memory)
  Total: ~$125/month

Pros:
  - No server management
  - Auto-scaling built-in
  - Pay only for running tasks

Cons:
  - Slightly more expensive than EC2
  - Less control over infrastructure
```

**Option B: EKS (Kubernetes)**
```bash
# EKS managed cluster: $0.10/hour = $72/month
# 3 × t3.medium nodes (2 vCPU, 4GB RAM): $0.0416/hour = $25/month each
# Total: $72 + (3 × $25) = $147/month

Pros:
  - More control
  - Better for complex deployments
  - Cheaper at scale (>10 pods)

Cons:
  - More management overhead
  - Higher minimum cost
```

**3. Database: RDS PostgreSQL**
```bash
# db.t3.medium (2 vCPU, 4GB RAM)
# Multi-AZ for high availability
# $0.082/hour × 730 hours = ~$60/month (single-AZ)
# $0.164/hour × 730 hours = ~$120/month (Multi-AZ)

# Storage: 100GB GP3 SSD
# $0.115/GB/month = $11.50/month

# Backups: 100GB (same as allocated storage, free)

Total: ~$132/month (Multi-AZ + storage)
```

**4. Cache: ElastiCache Redis**
```bash
# cache.t3.small (1.5GB memory)
# $0.051/hour × 730 hours = ~$37/month

# Or cache.t3.medium (3.2GB)
# $0.102/hour × 730 hours = ~$75/month
```

**5. Load Balancer**
```bash
# Application Load Balancer
# $0.0225/hour + $0.008/LCU-hour
# ~$16/month (base) + $5/month (LCUs) = ~$21/month
```

**6. Other Services**
```bash
# CloudWatch Logs: 10GB/month
# $0.50/GB = $5/month

# Data Transfer: 50GB/month outbound
# $0.09/GB (first 10TB) = $4.50/month

# Secrets Manager: 10 secrets
# $0.40/secret/month = $4/month
```

**Total Monthly Cost (ECS Fargate):**
```
ECR:               $0.50
ECS Fargate:       $125.00
RDS PostgreSQL:    $132.00
ElastiCache Redis: $37.00
Load Balancer:     $21.00
CloudWatch:        $5.00
Data Transfer:     $4.50
Secrets Manager:   $4.00
─────────────────────────
Total:             ~$329/month
```

**Total Monthly Cost (EKS):**
```
ECR:               $0.50
EKS Cluster:       $72.00
EC2 Nodes (3×):    $75.00
RDS PostgreSQL:    $132.00
ElastiCache Redis: $37.00
Load Balancer:     $21.00
CloudWatch:        $5.00
Data Transfer:     $4.50
Secrets Manager:   $4.00
─────────────────────────
Total:             ~$351/month
```

### Team Resources

**Initial Setup (One-time):**
```
Role: DevOps Engineer
Time: 2 weeks (80 hours)

Week 1:
  - Day 1-2: Fork setup, branch strategy (16 hours)
  - Day 3-4: CI/CD pipeline (GitHub Actions) (16 hours)
  - Day 5: Testing, iteration (8 hours)

Week 2:
  - Day 1-2: Kubernetes/ECS configuration (16 hours)
  - Day 3: RDS, ElastiCache setup (8 hours)
  - Day 4: Secrets management, IAM roles (8 hours)
  - Day 5: Testing, documentation (8 hours)

Deliverables:
  ✓ GitHub fork configured
  ✓ CI/CD pipeline automated
  ✓ Kubernetes cluster deployed
  ✓ Database and cache provisioned
  ✓ Secrets management configured
  ✓ Documentation written
```

**Ongoing Maintenance:**
```
Role: DevOps Engineer
Time: 2-4 hours/week

Weekly tasks:
  - Monitor CI/CD pipeline (30 min)
  - Review security scans (30 min)
  - Update dependencies (1 hour)
  - Respond to incidents (variable)
  - Plan capacity scaling (1 hour/month)

Monthly tasks:
  - Sync with upstream Agno (4 hours)
  - Review and optimize costs (2 hours)
  - Update Kubernetes cluster (2 hours)
  - Disaster recovery testing (4 hours)
```

---

## 9. Comparison: What You're NOT Doing

### Not Using: Direct pip install

**What you would do:**
```bash
pip install git+https://github.com/andromeda360/agno.git@custom/andromeda360-integration#subdirectory=libs/agno
```

**Problems:**

| Issue | Impact |
|-------|--------|
| **Slow** | Every install rebuilds from source (~30-45 seconds) |
| **Unreliable** | If branch changes, different machines get different versions |
| **No security** | No vulnerability scanning |
| **Manual deployment** | No automation, prone to errors |
| **Requires git** | Production servers need git access to GitHub |
| **No versioning** | Can't easily rollback |

**Example failure:**

```bash
# Developer laptop (Monday morning)
pip install git+https://...@custom/andromeda360-integration
# Gets commit abc123 (has bug)

# Production server (Monday afternoon)
pip install git+https://...@custom/andromeda360-integration
# Gets commit def456 (different code! bug might be gone or worse)

# Problem: Can't reproduce issues
# "It works on my laptop" → Yes, because you have different code!
```

### Not Using: Public PyPI

**What you would want:**
```bash
pip install agno-andromeda360
```

**Why you can't:**

| Reason | Explanation |
|--------|-------------|
| **Proprietary code** | Your custom features are not open source |
| **Namespace conflict** | Can't upload to PyPI without ownership |
| **No access control** | Anyone could install your internal version |
| **Compliance** | Exposing internal code violates policy |

### Not Using: Manual Deployments

**What you would do:**
```bash
# SSH into production
ssh production-server

# Pull latest code
cd /opt/agno
git pull origin custom/andromeda360-integration

# Install
pip install -e libs/agno

# Restart service
sudo systemctl restart agno

# Hope it works 🤞
```

**Problems:**

| Issue | Impact | With Phase 1 |
|-------|--------|--------------|
| **Downtime** | Service offline during deploy | ✓ Zero downtime (rolling update) |
| **Human error** | Forgot to restart, wrong branch, etc. | ✓ Fully automated |
| **No rollback** | Hard to undo | ✓ One command rollback |
| **No testing** | Deployed code might not work | ✓ CI/CD tests everything |
| **No versioning** | Don't know what's deployed | ✓ Exact version tracking |
| **Security** | SSH access to production | ✓ No SSH needed |

---

## 10. Success Stories

### Example 1: Rapid Iteration

**Timeline:**

```
Day 1: Initial deployment
  - v2.2.11-andromeda360.1 deployed
  - Serving 100 req/s
  - All green ✓

Day 3: Bug discovered
  - Token counter off by one error
  - Fix takes 1 hour
  - v2.2.11-andromeda360.2 deployed
  - CI/CD: 25 minutes
  - Deploy: 5 minutes
  - Total fix time: 1.5 hours

Day 5: Feature request
  - Add message export to PDF
  - Development: 4 hours
  - v2.2.11-andromeda360.3 deployed
  - CI/CD: 28 minutes
  - Deploy: 5 minutes
  - Feature live same day

Day 10: Upstream sync
  - Agno releases v2.2.12 with security fix
  - Sync and test: 2 hours
  - v2.2.12-andromeda360.1 deployed
  - CI/CD: 27 minutes
  - Deploy: 5 minutes
  - Security patch live within 3 hours
```

**Result:** 4 production deployments in 10 days, zero incidents

### Example 2: Traffic Spike Handling

**Scenario:** Marketing campaign launches

```
Before campaign:
  - 3 pods
  - 100 req/s
  - Cost: $125/month (Fargate)

Campaign launches (9 AM):
  - Traffic: 100 → 500 req/s
  - HPA detects high CPU
  - Auto-scales: 3 → 12 pods (2 minutes)
  - All requests handled ✓

Peak (11 AM):
  - Traffic: 500 → 1000 req/s
  - Auto-scales: 12 → 25 pods (1 minute)
  - P95 latency: 280ms (within SLA)
  - Error rate: 0%

Campaign ends (6 PM):
  - Traffic: 1000 → 200 req/s
  - Auto-scales: 25 → 6 pods (10 minutes)

Next day:
  - Traffic: 200 → 100 req/s (normal)
  - Auto-scales: 6 → 3 pods
  - Cost for day: $125 + $18 = $143
  - Extra cost: $18 for 9 hours of high traffic
```

**Result:** Handled 10x traffic spike with zero manual intervention, $18 extra cost

### Example 3: Security Incident Response

**Scenario:** Critical vulnerability in OpenAI SDK

```
10:00 AM: GitHub Security Alert
  - OpenAI SDK 1.10.0 has CVE-2024-xxxxx (CRITICAL)
  - Affected: Remote code execution
  - Fix: Upgrade to 1.10.5

10:05 AM: Team notified
  - Slack alert: Critical vulnerability detected
  - Incident declared

10:15 AM: Fix started
  - Update libs/agno/pyproject.toml
  - Change: openai>=1.10.0 → openai>=1.10.5
  - git commit -m "security: Upgrade OpenAI SDK to 1.10.5 (CVE-2024-xxxxx)"

10:20 AM: Create hotfix tag
  - git tag -a v2.2.11-andromeda360.4 -m "Security hotfix: CVE-2024-xxxxx"
  - git push origin v2.2.11-andromeda360.4

10:20-10:48 AM: CI/CD runs
  - Tests pass ✓
  - Docker image built with OpenAI 1.10.5
  - Security scan: PASS (vulnerability gone)
  - Image pushed to ECR

10:50 AM: Deploy to staging
  - Verify fix
  - Run security scan again
  - All clear ✓

11:00 AM: Deploy to production
  - kubectl set image...
  - Rolling update (5 minutes)
  - All pods on fixed version

11:05 AM: Incident resolved
  - Total time: 1 hour 5 minutes (alert → fixed in prod)
  - No downtime
  - No customer impact
```

**Result:** Critical security fix deployed in 65 minutes with zero downtime

---

## Summary: Why Phase 1 Works

### The 5 Pillars

**1. Git Tags → Version Control**
- Immutable snapshots of code
- Clear audit trail
- Easy rollbacks
- Semantic versioning

**2. Docker Images → Reproducibility**
- Same environment everywhere
- No "works on my machine"
- Tested artifact deployed to production
- Lightweight and portable

**3. CI/CD Automation → Speed and Reliability**
- Automated testing (can't forget)
- Automated security scanning
- Automated build and deploy
- Fast feedback (25 minutes)

**4. Kubernetes/ECS → Scalability and Zero-Downtime**
- Horizontal scaling (add more pods)
- Zero-downtime deployments (rolling updates)
- Auto-healing (restart failed pods)
- Auto-scaling (handle traffic spikes)

**5. Security Scanning → Confidence**
- Vulnerability detection before production
- Non-root containers
- Secrets management
- Network isolation

### Cost-Benefit Analysis

**Costs:**
- AWS infrastructure: ~$329-351/month
- DevOps time: 80 hours setup + 2-4 hours/week ongoing
- Total first month: ~$6,000 (labor) + $329 (AWS) = ~$6,329
- Ongoing monthly: ~$400 (labor) + $329 (AWS) = ~$729/month

**Benefits:**
- **Faster deployments:** 25 minutes (vs hours manually)
- **Zero downtime:** No service interruptions
- **Security:** Vulnerabilities caught automatically
- **Scalability:** Handle 10x traffic with no code changes
- **Reliability:** Automated testing prevents regressions
- **Developer productivity:** Confidence to deploy frequently
- **Compliance:** Full audit trail for SOC 2, ISO 27001

**ROI:**
- Break-even: ~3 months
- After 3 months: Saves time, reduces risk, enables growth
- Enables features impossible with manual deployment (auto-scaling, zero-downtime)

### When to Choose Phase 1

**Choose Phase 1 if you:**
- Need production deployment soon (1-2 weeks)
- Have 5-50 developers
- Are budget-conscious (minimize infrastructure)
- Deploy applications (not libraries)
- Want industry-standard DevOps practices
- Value simplicity over advanced features

**Don't choose Phase 1 if you:**
- Need sub-second `pip install` times (choose Phase 2)
- Have 100+ developers (choose Phase 2)
- Need package-level audit trails (choose Phase 2)
- Are distributing libraries to other teams (choose Phase 2)

### Migration Path

**Start with Phase 1 now, migrate to Phase 2 later:**

Phase 1 doesn't prevent Phase 2. You can:
1. Deploy with Phase 1 (week 1-2)
2. Run production for 6-12 months
3. Add Phase 2 (AWS CodeArtifact) when team grows
4. Keep Docker deployments, add PyPI for development

**Best of both worlds:** Phase 1 for production stability, Phase 2 for development speed.

---

**End of Document**

**Next Steps:**
1. Review this document with team
2. Get stakeholder approval
3. Assign DevOps engineer
4. Create AWS account resources
5. Follow the implementation guide
6. Deploy to staging
7. Test thoroughly
8. Deploy to production
9. Monitor and iterate

**Questions?** See [PRODUCTION_DEPLOYMENT_GUIDE.md](PRODUCTION_DEPLOYMENT_GUIDE.md) for full implementation details.
