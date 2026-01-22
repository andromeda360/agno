# Agno Production Deployment Guide for Andromeda360

**Document Version:** 1.0
**Last Updated:** 2025-12-16
**Target Audience:** DevOps Engineers, Platform Teams, Production Deployments

---

## Table of Contents

- [Overview](#overview)
- [Phase 1: Git Tags + Docker (Immediate Production)](#phase-1-git-tags--docker-immediate-production)
- [Phase 2: Private PyPI + Docker (Enterprise Scale)](#phase-2-private-pypi--docker-enterprise-scale)
- [Migration Path](#migration-path)
- [Security Considerations](#security-considerations)
- [Monitoring and Observability](#monitoring-and-observability)
- [Disaster Recovery](#disaster-recovery)
- [Troubleshooting](#troubleshooting)

---

## Overview

This guide provides two production-ready approaches for deploying Agno within Andromeda360:

| Approach | Timeline | Complexity | Cost | Best For |
|----------|----------|------------|------|----------|
| **Phase 1: Git Tags + Docker** | Immediate | Low | Minimal | Small to medium deployments |
| **Phase 2: Private PyPI + Docker** | 1-2 months | Medium | $50-500/month | Enterprise scale |

Both approaches are production-ready. Start with Phase 1 and migrate to Phase 2 as you scale.

---

# Phase 1: Git Tags + Docker (Immediate Production)

## Architecture Overview

```
┌──────────────────────────────────────────────────────────┐
│  GitHub: andromeda360/agno                               │
│  Branch: custom/andromeda360-integration                 │
│  Tags: v1.0.0-andromeda360, v1.0.1-andromeda360, ...    │
└────────────────┬─────────────────────────────────────────┘
                 │
                 │ GitHub Actions Workflow
                 │ (on git tag push)
                 ▼
┌──────────────────────────────────────────────────────────┐
│  Docker Build Process                                    │
│  - Multi-stage build                                     │
│  - Security scanning (Trivy)                             │
│  - Dependency caching                                    │
└────────────────┬─────────────────────────────────────────┘
                 │
                 │ Push
                 ▼
┌──────────────────────────────────────────────────────────┐
│  Container Registry                                      │
│  - AWS ECR (Recommended)                                 │
│  - Google GCR                                            │
│  - Docker Hub (Private)                                  │
└────────────────┬─────────────────────────────────────────┘
                 │
                 │ Pull
                 ▼
┌──────────────────────────────────────────────────────────┐
│  Production Environment                                  │
│  - Kubernetes / ECS / Cloud Run                          │
│  - Multiple replicas                                     │
│  - Auto-scaling enabled                                  │
└──────────────────────────────────────────────────────────┘
```

---

## Step 1: Fork Setup and Version Tagging

### 1.1 Create Production Fork

```bash
# Fork the repository (if not already done)
# GitHub UI: Fork agno-ai/agno to andromeda360/agno

# Clone your fork
git clone git@github.com:andromeda360/agno.git
cd agno

# Create custom branch
git checkout -b custom/andromeda360-integration

# Add upstream for syncing
git remote add upstream https://github.com/agno-ai/agno.git
git fetch upstream
```

### 1.2 Apply Custom Features

Apply your custom features from `agno_custom` (see `MIGRATION_FROM_AGNO_CUSTOM.md`):

```bash
# Example: Add custom features
# - Custom message logger
# - Model.log_messages flag
# - Selective agent content
# - Token counter

git add .
git commit -m "feat: Add Andromeda360 custom features

- Custom message logger with truncation
- Model.log_messages flag for controllable logging
- Selective agent content return in tool calls
- Built-in token counter using tiktoken

Refs: AGNO-001"

git push origin custom/andromeda360-integration
```

### 1.3 Version Tagging Strategy

Use semantic versioning with custom suffix:

**Format:** `v{AGNO_VERSION}-andromeda360.{CUSTOM_RELEASE}`

**Examples:**
- `v2.2.11-andromeda360.1` - First custom release based on Agno 2.2.11
- `v2.2.11-andromeda360.2` - Second custom release (bug fixes, patches)
- `v2.2.12-andromeda360.1` - Updated to upstream Agno 2.2.12

**Create first production tag:**

```bash
# Ensure all tests pass
./scripts/test.sh

# Create annotated tag
git tag -a v2.2.11-andromeda360.1 -m "Production Release v2.2.11-andromeda360.1

Features:
- Based on upstream Agno v2.2.11
- Custom message logger with 200 char truncation
- Model.log_messages flag (default: true)
- Selective agent content in tool calls
- Built-in tiktoken token counter

Tested: ✓ Unit tests, ✓ Integration tests, ✓ Load tests
Security: ✓ Dependency scan, ✓ Container scan
Approved-By: DevOps Team"

# Push tag to trigger CI/CD
git push origin v2.2.11-andromeda360.1
```

---

## Step 2: Docker Configuration

### 2.1 Production Dockerfile

Create `docker/production/Dockerfile`:

```dockerfile
# ============================================
# Stage 1: Builder
# ============================================
FROM python:3.11-slim AS builder

# Build arguments for versioning
ARG AGNO_VERSION=unknown
ARG BUILD_DATE=unknown
ARG VCS_REF=unknown

LABEL org.opencontainers.image.title="Agno Andromeda360"
LABEL org.opencontainers.image.version="${AGNO_VERSION}"
LABEL org.opencontainers.image.created="${BUILD_DATE}"
LABEL org.opencontainers.image.revision="${VCS_REF}"
LABEL org.opencontainers.image.vendor="Andromeda360"

WORKDIR /build

# Install build dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install uv for faster dependency resolution
RUN pip install --no-cache-dir uv

# Copy only dependency files first (layer caching)
COPY libs/agno/pyproject.toml libs/agno/
COPY libs/agno_infra/pyproject.toml libs/agno_infra/

# Copy source code
COPY libs/agno/agno libs/agno/agno
COPY libs/agno_infra/agno libs/agno_infra/agno

# Install Agno with production extras
# Customize extras based on your needs
RUN cd libs/agno && \
    uv pip install --system \
    ".[openai,anthropic,postgres,redis,os,pdf,opentelemetry]" \
    --no-cache

# ============================================
# Stage 2: Runtime
# ============================================
FROM python:3.11-slim

# Runtime arguments
ARG AGNO_VERSION=unknown
ENV AGNO_VERSION=${AGNO_VERSION}

# Security: Create non-root user
RUN groupadd -r agno -g 1000 && \
    useradd -r -u 1000 -g agno -m -s /bin/bash agno

# Install runtime dependencies only
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy Python packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code (if you have custom app code)
# COPY --chown=agno:agno ./your_app /app/your_app

# Create directories for runtime data
RUN mkdir -p /app/storage /app/logs && \
    chown -R agno:agno /app

# Switch to non-root user
USER agno

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PATH="/home/agno/.local/bin:${PATH}"

# Health check for AgentOS
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Expose AgentOS port
EXPOSE 8000

# Default command: Run AgentOS
CMD ["uvicorn", "agno.os.app:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

### 2.2 Docker Compose for Local Testing

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  agno-app:
    build:
      context: .
      dockerfile: docker/production/Dockerfile
      args:
        AGNO_VERSION: "2.2.11-andromeda360.1"
        BUILD_DATE: "2025-12-16T00:00:00Z"
        VCS_REF: "abc123"
    ports:
      - "8000:8000"
    environment:
      # Database configuration
      DATABASE_URL: postgresql://agno:agno@postgres:5432/agno

      # Redis configuration
      REDIS_URL: redis://redis:6379/0

      # API Keys (use secrets in production)
      OPENAI_API_KEY: ${OPENAI_API_KEY}
      ANTHROPIC_API_KEY: ${ANTHROPIC_API_KEY}

      # Agno configuration
      AGNO_ENV: production
      LOG_LEVEL: INFO

    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    volumes:
      - agno-storage:/app/storage
      - agno-logs:/app/logs
    networks:
      - agno-network
    restart: unless-stopped

  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: agno
      POSTGRES_PASSWORD: agno
      POSTGRES_DB: agno
    volumes:
      - postgres-data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U agno"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - agno-network

  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes
    volumes:
      - redis-data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - agno-network

volumes:
  postgres-data:
  redis-data:
  agno-storage:
  agno-logs:

networks:
  agno-network:
    driver: bridge
```

### 2.3 Test Local Build

```bash
# Build image
docker build \
  -f docker/production/Dockerfile \
  -t agno-andromeda360:latest \
  --build-arg AGNO_VERSION=2.2.11-andromeda360.1 \
  --build-arg BUILD_DATE=$(date -u +"%Y-%m-%dT%H:%M:%SZ") \
  --build-arg VCS_REF=$(git rev-parse --short HEAD) \
  .

# Test locally
docker-compose up -d

# Check health
curl http://localhost:8000/health

# View logs
docker-compose logs -f agno-app

# Run smoke tests
docker-compose exec agno-app python -c "from agno.agent import Agent; print('✓ Agno loaded')"

# Cleanup
docker-compose down
```

---

## Step 3: CI/CD Automation with GitHub Actions

### 3.1 Create GitHub Actions Workflow

Create `.github/workflows/production-release.yml`:

```yaml
name: Production Release - Build and Publish Docker Image

on:
  push:
    tags:
      - 'v*-andromeda360.*'

env:
  AWS_REGION: us-east-1
  ECR_REPOSITORY: agno-andromeda360

jobs:
  # ============================================
  # Job 1: Run Tests
  # ============================================
  test:
    name: Run Tests
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'

      - name: Install dependencies
        run: |
          pip install uv
          cd libs/agno
          uv pip install --system ".[dev]"

      - name: Run unit tests
        run: |
          ./scripts/test.sh

      - name: Run security scan
        run: |
          pip install safety pip-audit
          safety check --json || true
          pip-audit --format json || true

  # ============================================
  # Job 2: Build and Push Docker Image
  # ============================================
  build-and-push:
    name: Build and Push Docker Image
    runs-on: ubuntu-latest
    needs: test

    permissions:
      id-token: write  # Required for AWS OIDC
      contents: read

    outputs:
      image-tag: ${{ steps.meta.outputs.tags }}
      image-digest: ${{ steps.build.outputs.digest }}

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Extract version from tag
        id: version
        run: |
          VERSION=${GITHUB_REF#refs/tags/v}
          echo "VERSION=${VERSION}" >> $GITHUB_OUTPUT
          echo "Building version: ${VERSION}"

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::123456789012:role/GitHubActionsECRRole
          aws-region: ${{ env.AWS_REGION }}

      - name: Login to Amazon ECR
        id: login-ecr
        uses: aws-actions/amazon-ecr-login@v2

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Docker metadata
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ${{ steps.login-ecr.outputs.registry }}/${{ env.ECR_REPOSITORY }}
          tags: |
            type=semver,pattern={{version}}
            type=semver,pattern={{major}}.{{minor}}
            type=sha,prefix={{branch}}-
            type=raw,value=latest,enable={{is_default_branch}}

      - name: Build and push Docker image
        id: build
        uses: docker/build-push-action@v5
        with:
          context: .
          file: docker/production/Dockerfile
          push: true
          tags: |
            ${{ steps.login-ecr.outputs.registry }}/${{ env.ECR_REPOSITORY }}:${{ steps.version.outputs.VERSION }}
            ${{ steps.login-ecr.outputs.registry }}/${{ env.ECR_REPOSITORY }}:latest
          build-args: |
            AGNO_VERSION=${{ steps.version.outputs.VERSION }}
            BUILD_DATE=${{ github.event.repository.updated_at }}
            VCS_REF=${{ github.sha }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
          platforms: linux/amd64

      - name: Output image details
        run: |
          echo "Image pushed:"
          echo "${{ steps.login-ecr.outputs.registry }}/${{ env.ECR_REPOSITORY }}:${{ steps.version.outputs.VERSION }}"
          echo "Digest: ${{ steps.build.outputs.digest }}"

  # ============================================
  # Job 3: Security Scan with Trivy
  # ============================================
  security-scan:
    name: Security Scan
    runs-on: ubuntu-latest
    needs: build-and-push

    permissions:
      security-events: write

    steps:
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::123456789012:role/GitHubActionsECRRole
          aws-region: ${{ env.AWS_REGION }}

      - name: Login to Amazon ECR
        id: login-ecr
        uses: aws-actions/amazon-ecr-login@v2

      - name: Extract version from tag
        id: version
        run: echo "VERSION=${GITHUB_REF#refs/tags/v}" >> $GITHUB_OUTPUT

      - name: Run Trivy vulnerability scanner
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: ${{ steps.login-ecr.outputs.registry }}/${{ env.ECR_REPOSITORY }}:${{ steps.version.outputs.VERSION }}
          format: 'sarif'
          output: 'trivy-results.sarif'
          severity: 'CRITICAL,HIGH'

      - name: Upload Trivy results to GitHub Security
        uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: 'trivy-results.sarif'

      - name: Fail on critical vulnerabilities
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: ${{ steps.login-ecr.outputs.registry }}/${{ env.ECR_REPOSITORY }}:${{ steps.version.outputs.VERSION }}
          format: 'table'
          exit-code: '1'
          severity: 'CRITICAL'

  # ============================================
  # Job 4: Create GitHub Release
  # ============================================
  create-release:
    name: Create GitHub Release
    runs-on: ubuntu-latest
    needs: [build-and-push, security-scan]

    permissions:
      contents: write

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Extract version from tag
        id: version
        run: echo "VERSION=${GITHUB_REF#refs/tags/v}" >> $GITHUB_OUTPUT

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
            ${{ needs.build-and-push.outputs.image-tag }}
            ```

            ### Changes
            - Based on upstream Agno v2.2.11
            - Custom Andromeda360 features included

            ### Deployment
            ```bash
            docker pull ${{ needs.build-and-push.outputs.image-tag }}
            ```

            ### Security
            - ✓ Vulnerability scan passed
            - ✓ All tests passed

            ### Digest
            ```
            ${{ needs.build-and-push.outputs.image-digest }}
            ```
          draft: false
          prerelease: false
```

### 3.2 AWS ECR Setup

```bash
# Create ECR repository
aws ecr create-repository \
  --repository-name agno-andromeda360 \
  --region us-east-1 \
  --image-scanning-configuration scanOnPush=true \
  --encryption-configuration encryptionType=AES256

# Set lifecycle policy (keep last 30 images)
aws ecr put-lifecycle-policy \
  --repository-name agno-andromeda360 \
  --lifecycle-policy-text '{
    "rules": [{
      "rulePriority": 1,
      "description": "Keep last 30 images",
      "selection": {
        "tagStatus": "any",
        "countType": "imageCountMoreThan",
        "countNumber": 30
      },
      "action": {
        "type": "expire"
      }
    }]
  }'

# Create IAM role for GitHub Actions (OIDC)
# See: https://docs.github.com/en/actions/deployment/security-hardening-your-deployments/configuring-openid-connect-in-amazon-web-services
```

### 3.3 Trigger First Release

```bash
# Create and push tag (triggers CI/CD)
git tag -a v2.2.11-andromeda360.1 -m "Production release v2.2.11-andromeda360.1"
git push origin v2.2.11-andromeda360.1

# Monitor workflow
# GitHub UI → Actions tab → Watch "Production Release" workflow

# Verify image in ECR
aws ecr describe-images \
  --repository-name agno-andromeda360 \
  --region us-east-1
```

---

## Step 4: Production Deployment

### 4.1 Kubernetes Deployment

Create `k8s/production/deployment.yaml`:

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: agno-production

---
apiVersion: v1
kind: Secret
metadata:
  name: agno-secrets
  namespace: agno-production
type: Opaque
stringData:
  database-url: "postgresql://user:pass@postgres.internal:5432/agno"
  redis-url: "redis://redis.internal:6379/0"
  openai-api-key: "sk-..."
  anthropic-api-key: "sk-ant-..."

---
apiVersion: v1
kind: ConfigMap
metadata:
  name: agno-config
  namespace: agno-production
data:
  AGNO_ENV: "production"
  LOG_LEVEL: "INFO"
  WORKERS: "4"

---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: agno-app
  namespace: agno-production
  labels:
    app: agno
    version: v2.2.11-andromeda360.1
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  selector:
    matchLabels:
      app: agno
  template:
    metadata:
      labels:
        app: agno
        version: v2.2.11-andromeda360.1
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "8000"
        prometheus.io/path: "/metrics"
    spec:
      serviceAccountName: agno-sa

      containers:
      - name: agno
        image: 123456789012.dkr.ecr.us-east-1.amazonaws.com/agno-andromeda360:2.2.11-andromeda360.1
        imagePullPolicy: Always

        ports:
        - name: http
          containerPort: 8000
          protocol: TCP

        env:
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
        - name: ANTHROPIC_API_KEY
          valueFrom:
            secretKeyRef:
              name: agno-secrets
              key: anthropic-api-key

        envFrom:
        - configMapRef:
            name: agno-config

        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "2000m"

        livenessProbe:
          httpGet:
            path: /health
            port: http
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3

        readinessProbe:
          httpGet:
            path: /ready
            port: http
          initialDelaySeconds: 5
          periodSeconds: 5
          timeoutSeconds: 3
          failureThreshold: 2

        volumeMounts:
        - name: storage
          mountPath: /app/storage
        - name: logs
          mountPath: /app/logs

      volumes:
      - name: storage
        persistentVolumeClaim:
          claimName: agno-storage-pvc
      - name: logs
        emptyDir: {}

---
apiVersion: v1
kind: Service
metadata:
  name: agno-service
  namespace: agno-production
  labels:
    app: agno
spec:
  type: ClusterIP
  selector:
    app: agno
  ports:
  - name: http
    port: 80
    targetPort: 8000
    protocol: TCP

---
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
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80

---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: agno-storage-pvc
  namespace: agno-production
spec:
  accessModes:
  - ReadWriteMany
  resources:
    requests:
      storage: 100Gi
  storageClassName: efs-sc
```

Deploy to Kubernetes:

```bash
# Apply manifests
kubectl apply -f k8s/production/

# Verify deployment
kubectl get pods -n agno-production
kubectl get svc -n agno-production

# Check logs
kubectl logs -f deployment/agno-app -n agno-production

# Test endpoint
kubectl port-forward svc/agno-service 8000:80 -n agno-production
curl http://localhost:8000/health
```

### 4.2 AWS ECS Deployment

Create `ecs/task-definition.json`:

```json
{
  "family": "agno-andromeda360",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "executionRoleArn": "arn:aws:iam::123456789012:role/ecsTaskExecutionRole",
  "taskRoleArn": "arn:aws:iam::123456789012:role/agnoTaskRole",
  "containerDefinitions": [
    {
      "name": "agno",
      "image": "123456789012.dkr.ecr.us-east-1.amazonaws.com/agno-andromeda360:2.2.11-andromeda360.1",
      "essential": true,
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "AGNO_ENV",
          "value": "production"
        },
        {
          "name": "LOG_LEVEL",
          "value": "INFO"
        }
      ],
      "secrets": [
        {
          "name": "DATABASE_URL",
          "valueFrom": "arn:aws:secretsmanager:us-east-1:123456789012:secret:agno/database-url"
        },
        {
          "name": "OPENAI_API_KEY",
          "valueFrom": "arn:aws:secretsmanager:us-east-1:123456789012:secret:agno/openai-key"
        }
      ],
      "healthCheck": {
        "command": ["CMD-SHELL", "curl -f http://localhost:8000/health || exit 1"],
        "interval": 30,
        "timeout": 5,
        "retries": 3,
        "startPeriod": 60
      },
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/agno-andromeda360",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

Deploy to ECS:

```bash
# Register task definition
aws ecs register-task-definition \
  --cli-input-json file://ecs/task-definition.json

# Create or update service
aws ecs create-service \
  --cluster production-cluster \
  --service-name agno-service \
  --task-definition agno-andromeda360:1 \
  --desired-count 3 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx,subnet-yyy],securityGroups=[sg-xxx],assignPublicIp=DISABLED}" \
  --load-balancers "targetGroupArn=arn:aws:elasticloadbalancing:us-east-1:123456789012:targetgroup/agno-tg/xxx,containerName=agno,containerPort=8000"

# Monitor deployment
aws ecs describe-services \
  --cluster production-cluster \
  --services agno-service
```

---

## Step 5: Production Operations

### 5.1 Rolling Updates

```bash
# Tag new version
git tag -a v2.2.11-andromeda360.2 -m "Bug fix release"
git push origin v2.2.11-andromeda360.2

# Wait for CI/CD to build and push image

# Kubernetes: Update deployment
kubectl set image deployment/agno-app \
  agno=123456789012.dkr.ecr.us-east-1.amazonaws.com/agno-andromeda360:2.2.11-andromeda360.2 \
  -n agno-production

# Monitor rollout
kubectl rollout status deployment/agno-app -n agno-production

# Rollback if needed
kubectl rollout undo deployment/agno-app -n agno-production
```

### 5.2 Monitoring Setup

Create `monitoring/prometheus-rules.yaml`:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: agno-prometheus-rules
  namespace: agno-production
data:
  agno.rules: |
    groups:
    - name: agno
      interval: 30s
      rules:
      - alert: AgnoHighErrorRate
        expr: rate(agno_errors_total[5m]) > 0.05
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High error rate in Agno"
          description: "Error rate is {{ $value }} errors/sec"

      - alert: AgnoHighLatency
        expr: histogram_quantile(0.95, agno_request_duration_seconds) > 2
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High latency in Agno"
          description: "P95 latency is {{ $value }} seconds"

      - alert: AgnoHighMemoryUsage
        expr: container_memory_usage_bytes{pod=~"agno-app-.*"} / container_spec_memory_limit_bytes > 0.9
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High memory usage"
          description: "Memory usage is {{ $value | humanizePercentage }}"
```

---

# Phase 2: Private PyPI + Docker (Enterprise Scale)

## Architecture Overview

```
┌──────────────────────────────────────────────────────────┐
│  GitHub: andromeda360/agno                               │
│  Branch: custom/andromeda360-integration                 │
└────────────────┬─────────────────────────────────────────┘
                 │
                 │ GitHub Actions
                 │ (on tag push)
                 ▼
        ┌────────┴────────┐
        │                 │
        ▼                 ▼
┌───────────────┐  ┌──────────────┐
│ Build Wheel   │  │ Build Docker │
└───────┬───────┘  └──────┬───────┘
        │                 │
        │ Publish         │ Push
        ▼                 ▼
┌───────────────┐  ┌──────────────┐
│ AWS           │  │ AWS ECR      │
│ CodeArtifact  │  │ (Container   │
│ (PyPI)        │  │  Registry)   │
└───────┬───────┘  └──────┬───────┘
        │                 │
        │ pip install     │ docker pull
        ▼                 ▼
┌───────────────┐  ┌──────────────┐
│ Development   │  │ Production   │
│ Environments  │  │ Deployments  │
└───────────────┘  └──────────────┘
```

---

## Step 1: AWS CodeArtifact Setup

### 1.1 Create CodeArtifact Resources

```bash
# Create domain
aws codeartifact create-domain \
  --domain andromeda360 \
  --region us-east-1

# Create repository for Agno packages
aws codeartifact create-repository \
  --domain andromeda360 \
  --repository agno-packages \
  --description "Andromeda360 Agno fork and internal packages" \
  --region us-east-1

# Create upstream connection to PyPI (for dependencies)
aws codeartifact create-repository \
  --domain andromeda360 \
  --repository pypi-store \
  --description "PyPI upstream mirror" \
  --upstreams repositoryName=pypi-store \
  --region us-east-1

# Associate PyPI upstream with main repository
aws codeartifact associate-external-connection \
  --domain andromeda360 \
  --repository pypi-store \
  --external-connection public:pypi \
  --region us-east-1

aws codeartifact update-repository \
  --domain andromeda360 \
  --repository agno-packages \
  --upstreams repositoryName=pypi-store \
  --region us-east-1
```

### 1.2 Configure Access Policies

Create `codeartifact-policy.json`:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::123456789012:root"
      },
      "Action": [
        "codeartifact:DescribePackageVersion",
        "codeartifact:DescribeRepository",
        "codeartifact:GetPackageVersionReadme",
        "codeartifact:GetRepositoryEndpoint",
        "codeartifact:ListPackages",
        "codeartifact:ListPackageVersions",
        "codeartifact:ReadFromRepository"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::123456789012:role/GitHubActionsPublishRole"
      },
      "Action": [
        "codeartifact:PublishPackageVersion",
        "codeartifact:PutPackageMetadata"
      ],
      "Resource": "*"
    }
  ]
}
```

Apply policy:

```bash
aws codeartifact put-repository-permissions-policy \
  --domain andromeda360 \
  --repository agno-packages \
  --policy-document file://codeartifact-policy.json \
  --region us-east-1
```

---

## Step 2: Enhanced CI/CD for PyPI + Docker

Create `.github/workflows/enterprise-release.yml`:

```yaml
name: Enterprise Release - PyPI + Docker

on:
  push:
    tags:
      - 'v*-andromeda360.*'

env:
  AWS_REGION: us-east-1
  ECR_REPOSITORY: agno-andromeda360
  CODEARTIFACT_DOMAIN: andromeda360
  CODEARTIFACT_REPOSITORY: agno-packages

jobs:
  # ============================================
  # Job 1: Test
  # ============================================
  test:
    name: Run Tests
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install and test
        run: |
          pip install uv
          cd libs/agno
          uv pip install --system ".[dev]"
          cd ../..
          ./scripts/test.sh

  # ============================================
  # Job 2: Build and Publish Python Package
  # ============================================
  publish-pypi:
    name: Publish to CodeArtifact
    runs-on: ubuntu-latest
    needs: test

    permissions:
      id-token: write
      contents: read

    outputs:
      package-version: ${{ steps.version.outputs.VERSION }}

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Extract version
        id: version
        run: echo "VERSION=${GITHUB_REF#refs/tags/v}" >> $GITHUB_OUTPUT

      - name: Install build tools
        run: pip install build twine

      - name: Build package
        run: |
          cd libs/agno
          python -m build
          cd ../agno_infra
          python -m build

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::123456789012:role/GitHubActionsPublishRole
          aws-region: ${{ env.AWS_REGION }}

      - name: Login to CodeArtifact
        run: |
          export CODEARTIFACT_AUTH_TOKEN=$(aws codeartifact get-authorization-token \
            --domain ${{ env.CODEARTIFACT_DOMAIN }} \
            --query authorizationToken \
            --output text)

          export TWINE_USERNAME=aws
          export TWINE_PASSWORD=$CODEARTIFACT_AUTH_TOKEN
          export TWINE_REPOSITORY_URL=$(aws codeartifact get-repository-endpoint \
            --domain ${{ env.CODEARTIFACT_DOMAIN }} \
            --repository ${{ env.CODEARTIFACT_REPOSITORY }} \
            --format pypi \
            --query repositoryEndpoint \
            --output text)

          echo "TWINE_USERNAME=$TWINE_USERNAME" >> $GITHUB_ENV
          echo "TWINE_PASSWORD=$TWINE_PASSWORD" >> $GITHUB_ENV
          echo "TWINE_REPOSITORY_URL=$TWINE_REPOSITORY_URL" >> $GITHUB_ENV

      - name: Publish agno package
        run: |
          cd libs/agno
          twine upload dist/*

      - name: Publish agno-infra package
        run: |
          cd libs/agno_infra
          twine upload dist/*

      - name: Verify publication
        run: |
          aws codeartifact list-package-versions \
            --domain ${{ env.CODEARTIFACT_DOMAIN }} \
            --repository ${{ env.CODEARTIFACT_REPOSITORY }} \
            --format pypi \
            --package agno \
            --status Published

  # ============================================
  # Job 3: Build and Push Docker (uses PyPI)
  # ============================================
  build-docker:
    name: Build Docker from PyPI
    runs-on: ubuntu-latest
    needs: publish-pypi

    permissions:
      id-token: write
      contents: read

    steps:
      - uses: actions/checkout@v4

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::123456789012:role/GitHubActionsECRRole
          aws-region: ${{ env.AWS_REGION }}

      - name: Login to Amazon ECR
        id: login-ecr
        uses: aws-actions/amazon-ecr-login@v2

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Extract version
        id: version
        run: echo "VERSION=${GITHUB_REF#refs/tags/v}" >> $GITHUB_OUTPUT

      - name: Get CodeArtifact endpoint
        id: codeartifact
        run: |
          ENDPOINT=$(aws codeartifact get-repository-endpoint \
            --domain ${{ env.CODEARTIFACT_DOMAIN }} \
            --repository ${{ env.CODEARTIFACT_REPOSITORY }} \
            --format pypi \
            --query repositoryEndpoint \
            --output text | sed 's|https://||')

          TOKEN=$(aws codeartifact get-authorization-token \
            --domain ${{ env.CODEARTIFACT_DOMAIN }} \
            --query authorizationToken \
            --output text)

          echo "ENDPOINT=$ENDPOINT" >> $GITHUB_OUTPUT
          echo "TOKEN=$TOKEN" >> $GITHUB_OUTPUT

      - name: Build and push (using CodeArtifact)
        uses: docker/build-push-action@v5
        with:
          context: .
          file: docker/enterprise/Dockerfile
          push: true
          tags: |
            ${{ steps.login-ecr.outputs.registry }}/${{ env.ECR_REPOSITORY }}:${{ steps.version.outputs.VERSION }}
            ${{ steps.login-ecr.outputs.registry }}/${{ env.ECR_REPOSITORY }}:latest
          build-args: |
            AGNO_VERSION=${{ steps.version.outputs.VERSION }}
            CODEARTIFACT_ENDPOINT=${{ steps.codeartifact.outputs.ENDPOINT }}
            CODEARTIFACT_TOKEN=${{ steps.codeartifact.outputs.TOKEN }}
          cache-from: type=gha
          cache-to: type=gha,mode=max

  # ============================================
  # Job 4: Security Scan
  # ============================================
  security-scan:
    name: Security Scan
    runs-on: ubuntu-latest
    needs: build-docker

    permissions:
      id-token: write
      security-events: write

    steps:
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::123456789012:role/GitHubActionsECRRole
          aws-region: ${{ env.AWS_REGION }}

      - name: Login to Amazon ECR
        id: login-ecr
        uses: aws-actions/amazon-ecr-login@v2

      - name: Extract version
        id: version
        run: echo "VERSION=${GITHUB_REF#refs/tags/v}" >> $GITHUB_OUTPUT

      - name: Run Trivy scanner
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: ${{ steps.login-ecr.outputs.registry }}/${{ env.ECR_REPOSITORY }}:${{ steps.version.outputs.VERSION }}
          format: 'sarif'
          output: 'trivy-results.sarif'

      - name: Upload to GitHub Security
        uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: 'trivy-results.sarif'
```

---

## Step 3: Enterprise Dockerfile (using CodeArtifact)

Create `docker/enterprise/Dockerfile`:

```dockerfile
FROM python:3.11-slim AS builder

ARG AGNO_VERSION
ARG CODEARTIFACT_ENDPOINT
ARG CODEARTIFACT_TOKEN

WORKDIR /build

# Install uv
RUN pip install --no-cache-dir uv

# Configure pip to use CodeArtifact
RUN pip config set global.index-url https://aws:${CODEARTIFACT_TOKEN}@${CODEARTIFACT_ENDPOINT}simple/

# Install Agno from CodeArtifact
RUN uv pip install --system \
    "agno[openai,anthropic,postgres,redis,os,pdf,opentelemetry]==${AGNO_VERSION}" \
    --no-cache

# Runtime stage
FROM python:3.11-slim

RUN groupadd -r agno -g 1000 && \
    useradd -r -u 1000 -g agno -m -s /bin/bash agno

WORKDIR /app

COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

RUN apt-get update && \
    apt-get install -y --no-install-recommends curl ca-certificates && \
    rm -rf /var/lib/apt/lists/*

RUN mkdir -p /app/storage /app/logs && chown -R agno:agno /app

USER agno

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

EXPOSE 8000

CMD ["uvicorn", "agno.os.app:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

---

## Step 4: Developer Workflow with CodeArtifact

### 4.1 Configure Local Development

Create `scripts/setup-codeartifact.sh`:

```bash
#!/bin/bash
set -e

DOMAIN="andromeda360"
REPOSITORY="agno-packages"
REGION="us-east-1"

echo "Configuring pip for AWS CodeArtifact..."

# Get authorization token
TOKEN=$(aws codeartifact get-authorization-token \
  --domain $DOMAIN \
  --query authorizationToken \
  --output text \
  --region $REGION)

# Get repository endpoint
ENDPOINT=$(aws codeartifact get-repository-endpoint \
  --domain $DOMAIN \
  --repository $REPOSITORY \
  --format pypi \
  --query repositoryEndpoint \
  --output text \
  --region $REGION)

# Configure pip
pip config set global.index-url "${ENDPOINT}simple/"
pip config set global.extra-index-url "https://pypi.org/simple"

# Set environment variable for temporary use
export CODEARTIFACT_AUTH_TOKEN=$TOKEN

# Configure pip.conf for longer term
mkdir -p ~/.config/pip
cat > ~/.config/pip/pip.conf <<EOF
[global]
index-url = https://aws:${TOKEN}@${ENDPOINT#https://}simple/
extra-index-url = https://pypi.org/simple
EOF

echo "✓ CodeArtifact configured successfully"
echo ""
echo "Repository: ${ENDPOINT}"
echo "Token expires in: 12 hours"
echo ""
echo "To install Agno:"
echo "  pip install agno[openai,postgres]"
```

Make executable and run:

```bash
chmod +x scripts/setup-codeartifact.sh
./scripts/setup-codeartifact.sh
```

### 4.2 Install from CodeArtifact

```bash
# Setup authentication
./scripts/setup-codeartifact.sh

# Install Agno
pip install "agno[openai,postgres,os]==2.2.11-andromeda360.1"

# Or in pyproject.toml
```

Create `pyproject.toml` for internal projects:

```toml
[project]
name = "my-andromeda360-app"
version = "1.0.0"
dependencies = [
    "agno[openai,anthropic,postgres,os]==2.2.11-andromeda360.1",
    # other dependencies...
]

[tool.uv]
index-url = "https://aws:TOKEN@andromeda360-123456789012.d.codeartifact.us-east-1.amazonaws.com/pypi/agno-packages/simple/"
extra-index-url = ["https://pypi.org/simple"]
```

### 4.3 Automated Token Refresh

Create `~/.bashrc` addition:

```bash
# Auto-refresh CodeArtifact token
codeartifact-refresh() {
  export CODEARTIFACT_AUTH_TOKEN=$(aws codeartifact get-authorization-token \
    --domain andromeda360 \
    --query authorizationToken \
    --output text \
    --region us-east-1)

  ENDPOINT=$(aws codeartifact get-repository-endpoint \
    --domain andromeda360 \
    --repository agno-packages \
    --format pypi \
    --query repositoryEndpoint \
    --output text \
    --region us-east-1)

  pip config set global.index-url "https://aws:${CODEARTIFACT_AUTH_TOKEN}@${ENDPOINT#https://}simple/"
  echo "✓ CodeArtifact token refreshed"
}

# Refresh on shell start
codeartifact-refresh
```

---

## Step 5: Production Deployment (Enterprise)

### 5.1 Kubernetes with CodeArtifact

Update `k8s/production/deployment.yaml`:

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: codeartifact-credentials
  namespace: agno-production
type: Opaque
stringData:
  # Refreshed by external-secrets operator or CronJob
  token: "TOKEN_HERE"
  endpoint: "andromeda360-123456789012.d.codeartifact.us-east-1.amazonaws.com"

---
# CronJob to refresh CodeArtifact token
apiVersion: batch/v1
kind: CronJob
metadata:
  name: refresh-codeartifact-token
  namespace: agno-production
spec:
  schedule: "0 */6 * * *"  # Every 6 hours
  jobTemplate:
    spec:
      template:
        spec:
          serviceAccountName: codeartifact-refresher
          containers:
          - name: token-refresher
            image: amazon/aws-cli:latest
            command:
            - /bin/bash
            - -c
            - |
              TOKEN=$(aws codeartifact get-authorization-token \
                --domain andromeda360 \
                --query authorizationToken \
                --output text \
                --region us-east-1)

              kubectl create secret generic codeartifact-credentials \
                --from-literal=token=$TOKEN \
                --namespace agno-production \
                --dry-run=client -o yaml | kubectl apply -f -
          restartPolicy: OnFailure
```

### 5.2 Cost Optimization

```bash
# Monitor CodeArtifact costs
aws codeartifact list-packages \
  --domain andromeda360 \
  --repository agno-packages \
  --region us-east-1

# Set up lifecycle policies
# Packages are charged per GB stored
# Delete old versions to save costs

aws codeartifact delete-package-versions \
  --domain andromeda360 \
  --repository agno-packages \
  --format pypi \
  --package agno \
  --versions "2.2.10-andromeda360.1" "2.2.10-andromeda360.2"
```

---

# Migration Path

## From Phase 1 to Phase 2

### Week 1: Setup Infrastructure
1. Create AWS CodeArtifact domain and repository
2. Configure IAM roles and policies
3. Test publishing packages manually

### Week 2: Update CI/CD
1. Update GitHub Actions workflow
2. Test automated publishing
3. Verify packages in CodeArtifact

### Week 3: Pilot with Development Team
1. Configure 2-3 developers with CodeArtifact
2. Install Agno from CodeArtifact
3. Gather feedback

### Week 4: Full Migration
1. Update all projects to use CodeArtifact
2. Update documentation
3. Train team on new workflow
4. Keep Docker deployment unchanged

### Week 5: Optimization
1. Setup token refresh automation
2. Configure cost monitoring
3. Optimize caching strategies

---

# Security Considerations

## Container Security

### Image Scanning

```yaml
# Add to CI/CD
- name: Run vulnerability scan
  uses: aquasecurity/trivy-action@master
  with:
    image-ref: ${{ env.IMAGE }}
    severity: 'CRITICAL,HIGH'
    exit-code: '1'
```

### Runtime Security

```yaml
# PodSecurityPolicy (Kubernetes)
apiVersion: policy/v1beta1
kind: PodSecurityPolicy
metadata:
  name: agno-psp
spec:
  privileged: false
  allowPrivilegeEscalation: false
  requiredDropCapabilities:
    - ALL
  volumes:
    - 'configMap'
    - 'emptyDir'
    - 'projected'
    - 'secret'
    - 'persistentVolumeClaim'
  runAsUser:
    rule: 'MustRunAsNonRoot'
  seLinux:
    rule: 'RunAsAny'
  fsGroup:
    rule: 'RunAsAny'
  readOnlyRootFilesystem: true
```

## Secrets Management

### AWS Secrets Manager Integration

```python
# In your application
import boto3
import json

def get_secret(secret_name):
    client = boto3.client('secretsmanager', region_name='us-east-1')
    response = client.get_secret_value(SecretId=secret_name)
    return json.loads(response['SecretString'])

# Usage
secrets = get_secret('agno/production/api-keys')
openai_key = secrets['OPENAI_API_KEY']
```

### External Secrets Operator (Kubernetes)

```yaml
apiVersion: external-secrets.io/v1beta1
kind: SecretStore
metadata:
  name: aws-secrets-manager
  namespace: agno-production
spec:
  provider:
    aws:
      service: SecretsManager
      region: us-east-1
      auth:
        jwt:
          serviceAccountRef:
            name: agno-sa

---
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: agno-external-secret
  namespace: agno-production
spec:
  refreshInterval: 1h
  secretStoreRef:
    name: aws-secrets-manager
    kind: SecretStore
  target:
    name: agno-secrets
  data:
  - secretKey: openai-api-key
    remoteRef:
      key: agno/production/openai-key
  - secretKey: database-url
    remoteRef:
      key: agno/production/database-url
```

---

# Monitoring and Observability

## Metrics Collection

### Prometheus Integration

Add to your Agno application:

```python
from prometheus_client import Counter, Histogram, start_http_server

# Metrics
agent_runs = Counter('agno_agent_runs_total', 'Total agent runs')
agent_errors = Counter('agno_agent_errors_total', 'Total agent errors')
agent_latency = Histogram('agno_agent_latency_seconds', 'Agent run latency')

# In your agent code
@agent_latency.time()
def run_agent(query: str):
    agent_runs.inc()
    try:
        result = agent.run(query)
        return result
    except Exception as e:
        agent_errors.inc()
        raise

# Start metrics server
start_http_server(8001)
```

### Grafana Dashboard

```json
{
  "dashboard": {
    "title": "Agno Production Metrics",
    "panels": [
      {
        "title": "Agent Runs per Minute",
        "targets": [
          {
            "expr": "rate(agno_agent_runs_total[1m])"
          }
        ]
      },
      {
        "title": "Error Rate",
        "targets": [
          {
            "expr": "rate(agno_agent_errors_total[5m])"
          }
        ]
      },
      {
        "title": "P95 Latency",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(agno_agent_latency_seconds_bucket[5m]))"
          }
        ]
      }
    ]
  }
}
```

## Logging

### Structured Logging

```python
import structlog

logger = structlog.get_logger()

logger.info(
    "agent_run_started",
    agent_id=agent.agent_id,
    user_id=user_id,
    session_id=session_id
)
```

### Log Aggregation (ELK Stack)

```yaml
# Filebeat configuration
apiVersion: v1
kind: ConfigMap
metadata:
  name: filebeat-config
  namespace: agno-production
data:
  filebeat.yml: |
    filebeat.inputs:
    - type: container
      paths:
        - /var/log/containers/agno-*.log
      processors:
        - add_kubernetes_metadata:
            host: ${NODE_NAME}
            matchers:
            - logs_path:
                logs_path: "/var/log/containers/"

    output.elasticsearch:
      hosts: ['${ELASTICSEARCH_HOST}:${ELASTICSEARCH_PORT}']
      username: ${ELASTICSEARCH_USERNAME}
      password: ${ELASTICSEARCH_PASSWORD}
```

## Tracing

### OpenTelemetry Integration

```python
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

# Setup tracing
trace.set_tracer_provider(TracerProvider())
tracer = trace.get_tracer(__name__)

otlp_exporter = OTLPSpanExporter(endpoint="http://jaeger:4317")
span_processor = BatchSpanProcessor(otlp_exporter)
trace.get_tracer_provider().add_span_processor(span_processor)

# Use in code
with tracer.start_as_current_span("agent_run"):
    result = agent.run(query)
```

---

# Disaster Recovery

## Backup Strategy

### Database Backups

```bash
# PostgreSQL backup (automated daily)
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
pg_dump $DATABASE_URL | gzip > /backups/agno_${DATE}.sql.gz

# Upload to S3
aws s3 cp /backups/agno_${DATE}.sql.gz s3://andromeda360-backups/agno/

# Retention: 30 days
find /backups -name "agno_*.sql.gz" -mtime +30 -delete
```

### Configuration Backups

```bash
# Backup Kubernetes resources
kubectl get all,configmap,secret -n agno-production -o yaml > k8s-backup.yaml
aws s3 cp k8s-backup.yaml s3://andromeda360-backups/k8s/
```

## Recovery Procedures

### Rollback Deployment

```bash
# Kubernetes
kubectl rollout undo deployment/agno-app -n agno-production

# ECS
aws ecs update-service \
  --cluster production-cluster \
  --service agno-service \
  --task-definition agno-andromeda360:PREVIOUS_VERSION
```

### Database Recovery

```bash
# Download backup
aws s3 cp s3://andromeda360-backups/agno/agno_20251216_120000.sql.gz .

# Restore
gunzip agno_20251216_120000.sql.gz
psql $DATABASE_URL < agno_20251216_120000.sql
```

---

# Troubleshooting

## Common Issues

### Issue: Container fails to start

**Symptoms:** Pod CrashLoopBackOff in Kubernetes

**Debug:**
```bash
# Check logs
kubectl logs -f deployment/agno-app -n agno-production

# Check events
kubectl describe pod <pod-name> -n agno-production

# Common causes:
# - Missing environment variables
# - Database connection failure
# - OOM (increase memory limits)
```

### Issue: High latency

**Symptoms:** P95 latency > 2 seconds

**Debug:**
```bash
# Check CPU/memory
kubectl top pods -n agno-production

# Check database connections
# Check Redis connections
# Enable profiling

# Scale up if needed
kubectl scale deployment/agno-app --replicas=10 -n agno-production
```

### Issue: CodeArtifact authentication failure

**Symptoms:** pip install fails with 401

**Debug:**
```bash
# Refresh token
aws codeartifact get-authorization-token \
  --domain andromeda360 \
  --query authorizationToken \
  --output text

# Check expiration (tokens last 12 hours)
# Verify IAM permissions
```

---

## Appendix

### A. Cost Estimates (Monthly)

#### Phase 1: Git + Docker
- AWS ECR: $0.10/GB stored + $0.09/GB transferred = ~$10-20/month
- Compute (ECS/EKS): $50-500/month (depends on usage)
- **Total: $60-520/month**

#### Phase 2: PyPI + Docker
- AWS CodeArtifact: $0.05/GB stored + $0.05/request (first 100K free) = ~$20-100/month
- AWS ECR: $10-20/month
- Compute (ECS/EKS): $50-500/month
- **Total: $80-620/month**

### B. Performance Benchmarks

| Metric | Git Install | PyPI Install | Docker Pull |
|--------|-------------|--------------|-------------|
| Cold install | ~45s | ~8s | ~15s |
| Cached install | ~30s | ~2s | ~5s |
| Size | N/A | 15MB wheel | 250MB image |

### C. Support Contacts

- **DevOps Team:** devops@andromeda360.com
- **Agno Upstream:** https://docs.agno.com
- **Internal Wiki:** https://wiki.andromeda360.com/agno

---

**End of Document**
