# Architecture

## Summary
This repo describes a small production-like Kubernetes setup with namespace isolation, strict network policies, non-root workloads, resource limits, probes, HPA, PDBs, and rolling updates. The system is a simple pipeline: API -> Kafka -> Worker -> Valkey.

## Components
- API (FastAPI): accepts tasks and exposes stats/metrics.
- Kafka: single node KRaft broker with SASL/PLAIN auth.
- Worker (FastAPI): consumes tasks, writes results to Valkey, exposes metrics.
- Valkey: HA with master/replicas, persistence, and exporter.
- Observability: Prometheus/Grafana/Loki (optional in this repo).

## Deployment Notes
- Namespaces: `infrastructure`, `application`, `worker`, `monitoring`.
- Network policies: default deny, allow only required ports.
- Security: non-root containers, restricted pod security labels.
- Upgrades: rolling update strategy on Deployments; PDBs for availability.

## Cloud Considerations
This layout works on any managed Kubernetes (EKS/GKE/AKS/Hetzner). Use a storage class that supports PVCs and a CNI that enforces NetworkPolicy.

## Data Flow
1. API receives `/task` and writes to Kafka.
2. Worker consumes from Kafka, processes, writes to Valkey.
3. API `/stats` reads Valkey for key counts and backlog.
