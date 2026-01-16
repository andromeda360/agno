# Agno Deployment Approaches - Comparison

**Version:** 1.0
**Date:** 2025-12-16
**For:** Technical Decision Makers

---

## Overview

Three approaches for deploying Agno within Andromeda360, each suited for different needs:

| Approach | Best For | Complexity | Time to Setup | Monthly Cost |
|----------|----------|------------|---------------|--------------|
| **Development PyPI** | Fast development iteration | Low | 1 day | ~$30-80 |
| **Production Docker** | Production deployments | Medium | 1-2 weeks | ~$300-500 |
| **Enterprise PyPI+Docker** | Large teams + Production | High | 4-6 weeks | ~$350-600 |

---

## Approach 1: Development PyPI (Fast Iteration)

### Purpose
Enable developers to quickly install and test Agno changes without building Docker images.

### Architecture

```
Fork Repository
     ↓
Build Python Wheel
     ↓
AWS CodeArtifact (Private PyPI)
     ↓
Developer: pip install agno
```

### Setup

**1. Create CodeArtifact Repository**
```bash
aws codeartifact create-domain --domain andromeda360
aws codeartifact create-repository \
  --domain andromeda360 \
  --repository agno-packages
```

**2. Build and Publish**
```bash
cd libs/agno
python -m build
twine upload --repository codeartifact dist/*
```

**3. Developer Installation**
```bash
# Configure once
aws codeartifact login --tool pip --domain andromeda360

# Install Agno
pip install agno[openai,postgres]==2.2.11-andromeda360.1

# Or in requirements.txt
agno[openai,postgres]==2.2.11-andromeda360.1
```

### Pros

✅ **Fast installation:** 2-5 seconds (vs 15-30s with Docker)
✅ **Easy iteration:** Change code → build → publish → install
✅ **Standard Python workflow:** Familiar pip/poetry/uv tools
✅ **Package versioning:** Semantic versioning, dependency management
✅ **Multi-project use:** Install in multiple projects easily

### Cons

❌ **Not for production:** No containerization, environment differences
❌ **Infrastructure cost:** $30-80/month for CodeArtifact
❌ **Token management:** 12-hour auth tokens need refresh
❌ **Build step required:** Must rebuild wheel for each change

### Cost

```
AWS CodeArtifact:
- Storage: 5GB × $0.05/GB = $0.25/month
- Requests: 10K × $0.05/10K = $0.50/month
- Data transfer: Free (within AWS)
Total: ~$30-80/month (varies by usage)
```

### When to Use

- Local development and testing
- Multiple developers on team (>5 people)
- Need fast `pip install` workflow
- Building libraries used by multiple projects
- NOT for production deployments (use Approach 2)

---

## Approach 2: Production Docker (Recommended for Production)

### Purpose
Production-ready deployments with containerization, zero-downtime updates, and auto-scaling.

### Architecture

```
Fork Repository
     ↓
Git Tag (v2.2.11-andromeda360.1)
     ↓
GitHub Actions CI/CD
     ↓
Docker Image Build
     ↓
AWS ECR (Container Registry)
     ↓
Production (Kubernetes/ECS)
```

### Setup

**1. Configure CI/CD (GitHub Actions)**
- Automatically triggered on git tag push
- Builds Docker image
- Runs tests and security scans
- Pushes to ECR

**2. Create Production Tag**
```bash
git tag -a v2.2.11-andromeda360.1 -m "Production release"
git push origin v2.2.11-andromeda360.1
# CI/CD runs automatically (~25 minutes)
```

**3. Deploy to Production**
```bash
# Kubernetes
kubectl set image deployment/agno-app \
  agno=123.ecr.../agno:2.2.11-andromeda360.1

# ECS
aws ecs update-service --task-definition agno:v1
```

### Pros

✅ **Production-ready:** Battle-tested deployment pattern
✅ **Reproducible:** Same environment dev/staging/prod
✅ **Zero-downtime:** Rolling updates, health checks
✅ **Auto-scaling:** Handle traffic spikes automatically
✅ **Security:** Automated vulnerability scanning
✅ **Fast rollback:** Revert to previous version in 2 minutes
✅ **Immutable:** Containers can't be modified at runtime

### Cons

❌ **Slower iteration:** Must rebuild Docker image (~12 min first build, ~2 min cached)
❌ **Higher infrastructure cost:** $300-500/month for production setup
❌ **DevOps overhead:** Requires Kubernetes/ECS knowledge
❌ **Build complexity:** Multi-stage Dockerfile, CI/CD pipeline

### Cost

```
AWS Infrastructure (Production):
- ECR (container registry): $0.50/month
- ECS Fargate (3 tasks): $125/month
  OR EKS (Kubernetes): $147/month
- RDS PostgreSQL (Multi-AZ): $132/month
- ElastiCache Redis: $37/month
- Application Load Balancer: $21/month
- CloudWatch/Secrets: $13/month
Total: ~$329-351/month
```

### When to Use

- Production deployments
- Need zero-downtime updates
- Need auto-scaling
- Need security scanning
- Team size: 5-100+ developers
- Application deployments (not library development)

---

## Approach 3: Enterprise (PyPI + Docker)

### Purpose
Best of both worlds: Fast development (PyPI) + Production deployments (Docker).

### Architecture

```
Fork Repository
     ↓
Git Tag Push
     ↓
CI/CD Pipeline
     ↓
    ┌─────────────┬──────────────┐
    ↓             ↓              ↓
Build Wheel   Build Docker    Run Tests
    ↓             ↓
CodeArtifact   AWS ECR
    ↓             ↓
Development  Production
```

### Setup

**1. Dual-Track CI/CD**
- Publishes Python wheel to CodeArtifact
- Builds Docker image from CodeArtifact packages
- Both triggered by same git tag

**2. Development Use**
```bash
# Developers use PyPI
pip install agno[openai,postgres]==2.2.11-andromeda360.1
# Fast: 2 seconds
```

**3. Production Use**
```bash
# Production uses Docker
kubectl set image deployment/agno-app \
  agno=123.ecr.../agno:2.2.11-andromeda360.1
# Docker image built FROM CodeArtifact packages
```

### Pros

✅ **Fast development:** pip install in 2 seconds
✅ **Production-ready:** Docker for deployments
✅ **Package management:** Proper dependency resolution
✅ **Audit trail:** CodeArtifact tracks all downloads
✅ **Compliance-ready:** SBOM generation, scanning
✅ **Flexible:** Choose pip OR Docker per use case

### Cons

❌ **Highest cost:** CodeArtifact + ECR + compute
❌ **Most complex:** Two distribution paths to maintain
❌ **Token management:** CodeArtifact tokens expire every 12 hours
❌ **Longer setup:** 4-6 weeks for full implementation

### Cost

```
AWS Infrastructure (Enterprise):
- CodeArtifact (PyPI): $30-80/month
- ECR (Docker registry): $0.50/month
- ECS/EKS (compute): $125-147/month
- RDS PostgreSQL: $132/month
- ElastiCache Redis: $37/month
- Load Balancer: $21/month
- CloudWatch/Secrets: $13/month
Total: ~$359-431/month
```

### When to Use

- Large teams (50+ developers)
- Need fast development AND production reliability
- Building libraries AND applications
- Need compliance features (audit trail, SBOM)
- Budget allows for both systems

---

## Decision Matrix

### Choose Development PyPI if:

- **Team size:** 5-50 developers
- **Primary use:** Local development, testing
- **Speed priority:** Need fast `pip install`
- **Not deploying:** Using for library development
- **Budget:** Minimal infrastructure spend

### Choose Production Docker if:

- **Deploying to production:** Applications, services, APIs
- **Need:** Zero-downtime, auto-scaling, security scanning
- **Team size:** 5-100+ developers
- **DevOps capacity:** Have or can hire DevOps engineer
- **Budget:** $300-500/month is acceptable

### Choose Enterprise (Both) if:

- **Large team:** 50+ developers
- **Mature organization:** Established DevOps practices
- **Need both:** Fast dev iteration + production deployments
- **Compliance required:** SOC 2, HIPAA, audit trails
- **Budget:** $400-600/month is acceptable

---

## Recommended Path

### For Most Teams (Recommended)

**Phase 1 (Week 1):** Start with Production Docker only
- Production deployments use Docker
- Developers use `pip install git+https://...` (slower but free)
- Cost: ~$300-350/month
- Time to production: 2 weeks

**Phase 2 (Month 3-6):** Add Development PyPI as team grows
- When team reaches 20-30 developers
- Add CodeArtifact for faster development
- Production continues using Docker (no change)
- Cost increases to ~$350-400/month

**Result:** Start cheap and simple, scale infrastructure as team grows.

---

## Quick Comparison Table

| Feature | Development PyPI | Production Docker | Enterprise (Both) |
|---------|------------------|-------------------|-------------------|
| **Install speed** | ⚡ 2s | 🐢 15s (pull image) | ⚡ 2s (dev) / 15s (prod) |
| **Development iteration** | ⚡ Fast | 🐢 Slow | ⚡ Fast |
| **Production-ready** | ❌ No | ✅ Yes | ✅ Yes |
| **Zero-downtime deploy** | ❌ No | ✅ Yes | ✅ Yes |
| **Auto-scaling** | ❌ No | ✅ Yes | ✅ Yes |
| **Security scanning** | ⚠️ Manual | ✅ Automated | ✅ Automated |
| **Audit trail** | ✅ Yes | ⚠️ Basic | ✅ Advanced |
| **Setup time** | 1 day | 1-2 weeks | 4-6 weeks |
| **Monthly cost** | $30-80 | $300-500 | $350-600 |
| **Team size** | 5-50 | 5-100+ | 50-500+ |
| **Complexity** | ⭐ Low | ⭐⭐ Medium | ⭐⭐⭐ High |

---

## Implementation Summary

### Development PyPI Setup

```bash
# 1. Create CodeArtifact (one-time)
aws codeartifact create-domain --domain andromeda360
aws codeartifact create-repository --domain andromeda360 --repository agno-packages

# 2. Build and publish
cd libs/agno
python -m build
twine upload --repository codeartifact dist/*

# 3. Developers install
pip install agno[openai,postgres]==2.2.11-andromeda360.1
```

**Time:** 1 day setup, 5 minutes per release

---

### Production Docker Setup

```bash
# 1. Configure GitHub Actions (one-time, 2 weeks)
# - Add .github/workflows/production-release.yml
# - Configure AWS ECR access
# - Setup Kubernetes/ECS cluster

# 2. Create release
git tag -a v2.2.11-andromeda360.1 -m "Release"
git push origin v2.2.11-andromeda360.1
# CI/CD runs automatically

# 3. Deploy
kubectl set image deployment/agno-app agno=123.ecr.../agno:2.2.11-andromeda360.1
```

**Time:** 2 weeks setup, 25 minutes per release (automated)

---

### Enterprise Setup

```bash
# Combines both approaches above
# 1. Setup CodeArtifact (1 day)
# 2. Setup Docker CI/CD (2 weeks)
# 3. Configure dual-track publishing (1 week)
# 4. Test both paths (1 week)

# Developers use PyPI
pip install agno==2.2.11-andromeda360.1

# Production uses Docker
kubectl set image deployment/agno-app agno=...
```

**Time:** 4-6 weeks setup, 30 minutes per release

---

## Next Steps

### To Implement Development PyPI:

1. Create AWS CodeArtifact domain and repository
2. Configure CI/CD to build wheels
3. Test publishing and installation
4. Document for team

**Estimated effort:** 8 hours

---

### To Implement Production Docker:

1. Review detailed guide: `PHASE_1_DETAILED_EXPLANATION.md`
2. Setup GitHub Actions workflow
3. Configure AWS ECR
4. Setup Kubernetes/ECS cluster
5. Configure database and cache
6. Test end-to-end deployment
7. Document operations

**Estimated effort:** 80 hours (2 weeks, 1 DevOps engineer)

---

### To Implement Enterprise:

1. Complete Production Docker setup first
2. Add CodeArtifact setup
3. Modify CI/CD for dual publishing
4. Test both deployment paths
5. Train team on both workflows

**Estimated effort:** 120 hours (3 weeks, 1 DevOps engineer)

---

## FAQ

**Q: Can we start with Development PyPI only?**
A: Yes, but it's not production-ready. Use for local development, but add Production Docker before deploying.

**Q: Can we add Development PyPI to existing Production Docker?**
A: Yes! They're complementary. Add CodeArtifact anytime to speed up development.

**Q: Which approach is most cost-effective?**
A: Development PyPI is cheapest ($30-80/month) but limited. Production Docker ($300-500/month) is best value for production needs.

**Q: How long to switch from one approach to another?**
A:
- PyPI → Docker: 2 weeks
- Docker → Docker+PyPI: 1 week
- No switching needed - they complement each other

**Q: Can we use free Docker Hub instead of ECR?**
A: For private images, Docker Hub costs $7/month per user. ECR is cheaper and integrates better with AWS.

**Q: What about using just git+https for development?**
A: Works for small teams (<5 developers). Slow (30-45s installs) but free. Upgrade to PyPI when speed matters.

---

**For Full Details:**
- Technical deep dive: `PHASE_1_DETAILED_EXPLANATION.md` (2,235 lines)
- Implementation guide: `PRODUCTION_DEPLOYMENT_GUIDE.md` (2,060 lines)
- Executive summary: `PRODUCTION_DEPLOYMENT_EXECUTIVE_SUMMARY.md` (426 lines)