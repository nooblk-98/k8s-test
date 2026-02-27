# Decisions

## Queue Choice
Kafka was selected for its durability and scalable consumer group model. Metrics are exposed via kafka-exporter.

## Valkey
Valkey is deployed in replication mode with Sentinel enabled for automatic failover. Persistence uses AOF with PVCs.

## Security
- NetworkPolicies default deny and allow only required ports between namespaces.
- Pods run as non-root with `RuntimeDefault` seccomp profiles.
- JWT validation is enforced on API endpoints.

## Optional: Zero-Downtime Schema Migration
Goal: add `schema_version` and `processed_at` fields to stored results without breaking older workers.

Strategy:
1. Update API to accept/forward both old and new payloads (no schema change required).
2. Deploy worker v2 that writes `schema_version` and `processed_at` while still reading old messages.
3. Keep read paths tolerant to missing fields (default values).
4. After v2 is stable, deprecate legacy fields in a later release.

Deployment order:
1. Deploy worker v2 (backward compatible).
2. Monitor processing success and metrics.
3. Deploy API changes if needed.
4. Only then remove legacy support.
