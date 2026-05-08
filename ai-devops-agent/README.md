# AI DevOps Agent

Production-ready, **fully on-premise** AI DevOps Agent for incident triage, diagnosis, and automated remediation. No external APIs; all infrastructure runs inside your network.

## Architecture Overview

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   ServiceNow     │────▶│  AI DevOps Agent │────▶│  Ollama (LLM)   │
│   (Incidents)    │     │  (LangGraph)     │     │  llama3.1:70b    │
└─────────────────┘     └────────┬─────────┘     └─────────────────┘
                                 │
         ┌───────────────────────┼───────────────────────┐
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐
│  Milvus (RAG)   │   │  EFK (Logs)     │   │  Prometheus     │
│  Runbooks/KB    │   │  Elasticsearch  │   │  Metrics/Alerts │
└─────────────────┘   └─────────────────┘   └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 ▼
                    ┌─────────────────────────┐
                    │  K8s API / SSH / Ansible │
                    │  (Remediation actions)   │
                    └─────────────────────────┘
```

- **Orchestration**: LangGraph state machine (fetch incident → RAG → logs/metrics/K8s → diagnose → fix or escalate → verify → close).
- **LLM**: Ollama (llama3.1:70b) and nomic-embed-text for embeddings, all in-cluster.
- **RAG**: Milvus stores runbooks, playbooks, and past incident resolutions.
- **Observability**: Prometheus metrics, EFK logs, audit log for every SSH command.
- **Security**: SSH allowlist, RBAC, NetworkPolicy (no internet egress), secrets via K8s/Vault.

## Setup

### Prerequisites

- Python 3.11+
- Poetry
- Docker (for local dev)
- Kubernetes cluster (for production); see **[Deploy with Helm](#deploy-with-helm)** for deployment steps
- Ollama, Milvus, Prometheus, Elasticsearch deployed (see `k8s/` and `scripts/deploy.sh`)

### Local development

```bash
# Install dependencies
poetry install
# or
make install

# Copy and edit environment
cp .env.example .env
# Edit .env with your SNOW, Prometheus, ELK, Ollama URLs — see docs/CONFIG.md

# Run RAG ingestion (after Ollama + Milvus are up)
make rag-ingest

# Run agent
python main.py
# or with uvicorn reload: uvicorn api.server:app --reload --host 0.0.0.0 --port 8080
```

### Production (Kubernetes)

See **[Deploy with Helm](#deploy-with-helm)** below for full steps and what to change before deploying.

---

## Deploy with Helm

This section describes how to deploy the AI DevOps Agent to a Kubernetes cluster using Helm, and **what to change before you deploy**.

### Prerequisites

- **kubectl** configured for your cluster
- **Helm 3** installed
- **Docker** (to build the agent image)
- **Container registry** your cluster can pull from (e.g. registry.internal, GitLab Container Registry)
- Cluster has (or you will deploy):
  - **Ollama** (LLM) — e.g. from `k8s/manifests/ollama-deployment.yaml`
  - **Milvus** (vector DB for RAG) — or use Milvus Lite via env (see config)
  - **Prometheus** and **Elasticsearch** if the agent will query metrics and logs

### Steps to change before deploy

Do these **before** running `helm upgrade --install` or `./scripts/deploy.sh`:

| Step | What to change | Where |
|------|----------------|-------|
| **1. Image** | Set your registry and image tag so the cluster can pull the agent image. | **`k8s/helm/values.yaml`** → `image.repository` and `image.tag`. Example: `repository: registry.internal/ai-devops-agent`, `tag: v1.0.0` or `latest`. |
| **2. Environment (non-secret)** | Override URLs and settings for your cluster (Ollama, Milvus, Prometheus, Elasticsearch URLs, namespace, etc.). | **`k8s/helm/values.yaml`** → `env` map. Values here override the chart’s default ConfigMap. Example: `OLLAMA_BASE_URL: "http://ollama.ai-agent.svc.cluster.local:11434"`. |
| **3. Secrets** | Provide ServiceNow URL/password, Elasticsearch password, internal API token. Never put these in values.yaml; use a Secret. | Create a Kubernetes Secret (e.g. `ai-devops-agent-secrets`) with keys: `SNOW_BASE_URL`, `SNOW_USERNAME`, `SNOW_PASSWORD`, `ELASTICSEARCH_PASSWORD`, `INTERNAL_API_TOKEN`. Or use **External Secrets** / Vault and point the chart at the secret name. See **`k8s/helm/templates/secrets.yaml`** for the expected secret name (`<release>-secrets`). |
| **4. SSH key and certs (optional)** | If the agent will run SSH or use TLS for SNOW/ELK, provide the SSH private key and CA certs. | Create secrets `ai-devops-agent-ssh-key` and (optional) `ai-devops-agent-certs` in the same namespace. The deployment mounts them at `/secrets` and `/certs`. |
| **5. Namespace** | Deploy into a specific namespace (default is `ai-agent`). | Use `-n <namespace>` with Helm, or change **`k8s/namespace.yaml`** and apply it first. Update Ollama/Milvus URLs in `env` if they run in another namespace. |
| **6. Ingress (optional)** | Expose the API outside the cluster. | **`k8s/helm/values.yaml`** → set `ingress.enabled: true` and configure ingress host/tls. |

**Build and push the image** (required before deploy):

```bash
# From project root (devops/ai-devops-agent)
docker build -t <your-registry>/ai-devops-agent:<tag> .
docker push <your-registry>/ai-devops-agent:<tag>
# Then set image.repository and image.tag in k8s/helm/values.yaml to match.
```

Or use the Makefile: `make build`, then `make push REGISTRY=<your-registry>` (and set `image.tag` in values).

### Helm deploy commands

**Option A — Helm only (you already have namespace and secrets):**

```bash
# From project root
cd devops/ai-devops-agent

# Create namespace if not exists
kubectl apply -f k8s/namespace.yaml

# Install or upgrade the agent release
helm upgrade --install ai-devops-agent ./k8s/helm -n ai-agent -f k8s/helm/values.yaml --wait
```

**Option B — Full script (namespace + secrets + Ollama + Milvus + agent):**

```bash
# Set secrets in the environment, then run the deploy script
export SNOW_BASE_URL="https://your-instance.service-now.com"
export SNOW_PASSWORD="your-snow-password"
export ELASTICSEARCH_PASSWORD="your-elk-password"
export INTERNAL_API_TOKEN="your-internal-token"

./scripts/deploy.sh
```

The script creates the namespace, a generic secret from env vars, deploys Ollama and (optionally) Milvus, then runs `helm upgrade --install` for the agent.

**Option C — Staging vs production (Makefile):**

```bash
# Staging (namespace ai-agent)
make deploy-staging

# Production (namespace production) — use a dedicated values file
make deploy-prod
# Or: helm upgrade --install ai-devops-agent ./k8s/helm -n production -f k8s/helm/values-prod.yaml
```

### After deploy

- **Check pods:** `kubectl get pods -n ai-agent`
- **Check logs:** `kubectl logs -f deployment/ai-devops-agent -n ai-agent`
- **Port-forward to test API:** `kubectl port-forward deployment/ai-devops-agent 8080:8080 -n ai-agent` then `curl http://localhost:8080/health` and `curl http://localhost:8080/ready`
- **Smoke test:** `BASE_URL=http://localhost:8080 ./scripts/smoke_test.sh` (with port-forward active)

See **`k8s/README.md`** for details on each Helm template and manifest.

---

## How to Run

- **API server**: Listens on port 8080. Endpoints: `GET /health`, `GET /ready`, `POST /incidents/{id}/trigger`, etc.
- **SNOW poller**: Background thread polls ServiceNow every `SNOW_POLL_INTERVAL_SECONDS` and triggers the agent for new incidents (P2/P3 by default).
- **Manual trigger**: `POST /incidents/INC0010001/trigger` to process a specific incident.

## Project layout

Each folder has its own **README.md** that explains what the folder is, why it exists, what each file does, and how to add or change things. No AI background needed—the docs and code comments explain everything.

| Folder / File | Purpose | See |
|----------------|---------|-----|
| **agent/** | AI agent workflow (LangGraph): state, graph, nodes, edges, prompts, LLM, runner | [agent/README.md](agent/README.md) |
| **api/** | HTTP API (FastAPI): health, ready, trigger incident, stats, RAG ingest, audit log | [api/README.md](api/README.md) |
| **config/** | Configuration: all URLs and credentials (Ollama, SNOW, Prometheus, ELK, Milvus, etc.) | [config/README.md](config/README.md) |
| **tools/** | Integrations: ServiceNow, Elasticsearch, Prometheus, K8s, SSH, Ansible, RAG search | [tools/README.md](tools/README.md) |
| **rag/** | RAG: ingest runbooks into Milvus, CLI for ingestion, sample documents | [rag/README.md](rag/README.md) |
| **watcher/** | ServiceNow poller: background thread that triggers the agent for new incidents | [watcher/README.md](watcher/README.md) |
| **k8s/** | Kubernetes: namespace, Helm chart, manifests for Ollama/Milvus | [k8s/README.md](k8s/README.md) |
| **scripts/** | Shell scripts: local setup, deploy, RAG ingest, smoke test | [scripts/README.md](scripts/README.md) |
| **tests/** | Automated tests (pytest), mocks for SNOW/ELK/Ollama/Milvus | [tests/README.md](tests/README.md) |
| **docs/** | Extra docs: CONFIG (all env vars), PUSH_TO_GITLAB, operations | [docs/README.md](docs/README.md) |
| **main.py** | Entry point: starts SNOW poller in a background thread and the FastAPI server on port 8080 | — |
| **pyproject.toml** | Python dependencies and project metadata (Poetry) | — |
| **.env** | Your local config (URLs, passwords); copy from .env.example. Never commit. | [docs/CONFIG.md](docs/CONFIG.md) |

## Constraints

- **No external APIs**: All LLM, embeddings, and data stay on-premise.
- **SSH**: Only whitelisted commands; every execution is audit-logged.
- **P1 incidents**: Always escalated to humans; no auto-close.
- **Secrets**: Kubernetes Secrets or HashiCorp Vault only; no secrets in code.

## License

Internal use only.
