# Architecture Design

## Overview
The platform uses a queue-based architecture with isolated namespaces and strict network policies. The API receives tasks, publishes messages to Kafka, workers process and store results in Valkey, and Prometheus/Grafana provide observability.

## Data Flow
1. Client sends POST /task with JSON payload.
2. API validates JWT and publishes to Kafka.
3. Worker consumes messages, processes, and stores results in Valkey.
4. API /stats reads Valkey key count, queue backlog, and processed count.

## Reliability
- Rolling upgrades for API and worker deployments.
- PDBs to maintain minimum replicas.
- Liveness/readiness probes gate traffic.
- Resource requests/limits to prevent noisy neighbors.

## Security
- Non-root containers and restricted pod security.
- Network policies with default deny.
- Secrets managed via Kubernetes Secrets.
