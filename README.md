# DevOps Test Task - Kubernetes Microservices Platform

## Overview

This project implements a production-ready microservices platform deployed on Kubernetes, demonstrating infrastructure as code, queue-based processing, and multi-cloud deployment strategies across AWS, Hetzner, and OVH.

## Architecture

The system consists of:
- **Microservice**: REST API that accepts requests and publishes to a message queue
- **Message Queue**: Kafka for asynchronous job processing
- **Worker**: Processes jobs from the queue and performs business logic/ML inference
- **Valkey**: Redis-compatible cache and session store
- **PostgreSQL**: Primary database
- **Observability Stack**: Prometheus, Grafana, Jaeger for metrics, logging, and tracing

### Documentation

📖 **[Architecture & Infrastructure Design](ARCHITECTURE.md)** - Comprehensive architecture document covering:
- Microservice → Queue → Worker flow
- Cache/storage strategy
- Deployment approaches (rolling, blue-green, canary)
- Multi-cloud scaling across AWS, Hetzner, and OVH
- Secrets management with Vault
- Network topology and security
- Observability implementation

## Technology Stack

- **Container Orchestration**: Kubernetes (Kind/Minikube for local, EKS/Hetzner K8s/OVH K8s for cloud)
- **Infrastructure as Code**: Terraform, Helm, Kustomize
- **Languages**: Python (FastAPI/Flask)
- **Message Queue**: Kafka
- **Cache**: Valkey (Redis-compatible)
- **Database**: PostgreSQL
- **CI/CD**: GitHub Actions / GitLab CI
- **GitOps**: ArgoCD
- **Monitoring**: Prometheus, Grafana, Jaeger
- **Secrets**: HashiCorp Vault / Sealed Secrets

## Project Structure

```
repo/
├── architecture/               # Architecture documentation
│   ├── design.md              # Main architecture design doc
│   └── diagrams.png           # Architecture diagrams
├── infra/                     # Infrastructure as Code
│   ├── helm/                  # Helm charts
│   │   ├── valkey/           # Valkey (Redis) cache
│   │   ├── queue/            # Message queue (Kafka)
│   │   ├── api/              # API service chart
│   │   └── worker/           # Worker service chart
│   ├── terraform/            # Cloud infrastructure (optional)
│   └── monitoring/           # Monitoring stack (Prometheus/Grafana)
├── services/                 # Application source code
│   ├── api/                  # Microservice API
│   └── worker/               # Worker service
├── ci/                       # CI/CD configuration
│   └── pipeline.yaml         # CI/CD pipeline definition
└── docs/                     # Additional documentation
    ├── how-to-run.md         # Deployment and running instructions
    ├── troubleshooting.md    # Common issues and solutions
    └── decisions.md          # Technical decisions and ADRs
```

## Getting Started

### Prerequisites

- Docker
- kubectl
- Kind/Minikube/K3s
- Helm 3+
- Terraform (optional for cloud deployment)

### Local Development

```bash
# 1. Start local Kubernetes cluster
kind create cluster --name devops-test

# 2. Deploy infrastructure components
kubectl apply -f k8s/base/namespace.yaml
helm install kafka bitnami/kafka -n infrastructure
helm install valkey bitnami/valkey -n infrastructure
helm install postgresql bitnami/postgresql -n infrastructure

# 3. Deploy application
kubectl apply -k k8s/overlays/dev

# 4. Access the API
kubectl port-forward svc/api-service 8080:80
curl http://localhost:8080/health
```

### Cloud Deployment

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed multi-cloud deployment strategies.

## Testing

```bash
# Unit tests
pytest src/tests/

# Integration tests
pytest src/tests/integration/

# Load tests
locust -f tests/load/locustfile.py
```

## Monitoring

- **Grafana Dashboard**: http://localhost:3000
- **Prometheus**: http://localhost:9090
- **Jaeger UI**: http://localhost:16686

## Security

- All secrets managed via HashiCorp Vault or Kubernetes Sealed Secrets
- Network policies enforce least-privilege communication
- Container images scanned with Trivy
- TLS encryption for all external communication

## License

MIT

## Author

DevOps Candidate - CueGrowth Test Task

