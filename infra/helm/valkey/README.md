# Valkey Helm Chart

A production-ready Helm chart for deploying Valkey (Redis-compatible) with High Availability, security hardening, and observability.

## Features

✅ **High Availability**
- Master-Replica replication architecture
- Sentinel-based automatic failover
- Multiple replicas for read scalability

✅ **Security**
- Non-root container execution
- Pod Security Context with seccomp profiles
- Read-only root filesystem
- Network policies for traffic restriction
- Password authentication
- Secrets management

✅ **Production-Ready**
- Resource requests and limits
- Liveness and readiness probes
- Horizontal Pod Autoscaling (HPA)
- Pod Disruption Budgets (PDB)
- Rolling update strategy
- Persistent storage with PVCs

✅ **Observability**
- Prometheus metrics exporter
- ServiceMonitor for Prometheus Operator
- Pre-configured alerting rules
- Structured logging

## Architecture

```
┌─────────────────────────────────────────────────┐
│                   Valkey Cluster                 │
│                                                  │
│  ┌──────────────┐         ┌──────────────┐     │
│  │   Master     │────────▶│  Replica 1   │     │
│  │ (Read/Write) │         │  (Read-only) │     │
│  └──────┬───────┘         └──────────────┘     │
│         │                       │               │
│         │                 ┌──────────────┐     │
│         └────────────────▶│  Replica 2   │     │
│                           │  (Read-only) │     │
│                           └──────────────┘     │
│                                                  │
│  ┌─────────────────────────────────────────┐   │
│  │         Sentinel Quorum (3 nodes)       │   │
│  │  Monitors health & handles failover     │   │
│  └─────────────────────────────────────────┘   │
└─────────────────────────────────────────────────┘
```

## Prerequisites

- Kubernetes 1.21+
- Helm 3.8+
- PV provisioner support in the underlying infrastructure
- (Optional) Prometheus Operator for ServiceMonitor

## Installation

### Quick Start

```bash
# Add the repository (if published) or use local chart
cd infra/helm/valkey

# Install with default values
helm install valkey . -n infrastructure --create-namespace

# Get the Valkey password
export VALKEY_PASSWORD=$(kubectl get secret --namespace infrastructure valkey -o jsonpath="{.data.password}" | base64 -d)

# Connect to Valkey master
kubectl run --namespace infrastructure valkey-client --rm --tty -i --restart='Never' \
  --image docker.io/valkey/valkey:7.2.4-alpine -- valkey-cli -h valkey-master -a $VALKEY_PASSWORD
```

### Custom Installation

```bash
# Create custom values file
cat > custom-values.yaml <<EOF
global:
  storageClass: "gp3"  # Your storage class

auth:
  password: "MySecurePassword123!"

master:
  resources:
    requests:
      cpu: 500m
      memory: 1Gi
    limits:
      cpu: 2000m
      memory: 2Gi

replica:
  replicaCount: 3
  autoscaling:
    enabled: true
    minReplicas: 3
    maxReplicas: 10
    targetCPU: 75

metrics:
  enabled: true
  serviceMonitor:
    enabled: true
EOF

# Install with custom values
helm install valkey . -n infrastructure -f custom-values.yaml
```

## Configuration

### Key Configuration Options

| Parameter | Description | Default |
|-----------|-------------|---------|
| `architecture` | Deployment mode: `standalone` or `replication` | `replication` |
| `auth.enabled` | Enable password authentication | `true` |
| `auth.password` | Valkey password (auto-generated if empty) | `""` |
| `master.replicaCount` | Number of master nodes | `1` |
| `replica.replicaCount` | Number of replica nodes | `2` |
| `replica.autoscaling.enabled` | Enable HPA for replicas | `true` |
| `replica.autoscaling.minReplicas` | Minimum replicas | `2` |
| `replica.autoscaling.maxReplicas` | Maximum replicas | `5` |
| `sentinel.enabled` | Enable Sentinel for failover | `true` |
| `sentinel.quorum` | Minimum Sentinels for failover | `2` |
| `persistence.enabled` | Enable persistent storage | `true` |
| `persistence.size` | PVC size | `8Gi` |
| `metrics.enabled` | Enable metrics exporter | `true` |
| `networkPolicy.enabled` | Enable network policies | `true` |

See [values.yaml](values.yaml) for all configuration options.

### Security Settings

All pods run with the following security context:

```yaml
podSecurityContext:
  fsGroup: 1001
  runAsUser: 1001
  runAsNonRoot: true
  seccompProfile:
    type: RuntimeDefault

containerSecurityContext:
  runAsUser: 1001
  runAsNonRoot: true
  allowPrivilegeEscalation: false
  readOnlyRootFilesystem: true
  capabilities:
    drop:
      - ALL
```

### Resource Allocation

Default resource requests and limits:

**Master/Replica:**
- Requests: 250m CPU, 512Mi Memory
- Limits: 1000m CPU, 1Gi Memory

**Sentinel:**
- Requests: 100m CPU, 128Mi Memory
- Limits: 500m CPU, 256Mi Memory

**Metrics Exporter:**
- Requests: 50m CPU, 64Mi Memory
- Limits: 200m CPU, 128Mi Memory

## High Availability

### Sentinel Configuration

Sentinel provides automatic failover:
- Monitors master health
- Promotes replica to master on failure
- Reconfigures clients to new master
- Minimum quorum of 2 sentinels required

### Pod Disruption Budgets

PDBs ensure minimum availability during:
- Node maintenance
- Cluster upgrades
- Voluntary evictions

```yaml
master:
  pdb:
    minAvailable: 1

replica:
  pdb:
    minAvailable: 1

sentinel:
  pdb:
    minAvailable: 2
```

## Scaling

### Horizontal Pod Autoscaling

Replicas automatically scale based on:
- CPU utilization (default: 70%)
- Memory utilization (default: 80%)

```bash
# Watch HPA status
kubectl get hpa -n infrastructure -w

# Manually scale replicas
kubectl scale statefulset valkey-replica -n infrastructure --replicas=5
```

## Monitoring

### Metrics

Prometheus metrics exposed on port 9121:
- `valkey_up` - Instance availability
- `valkey_connected_slaves` - Number of connected replicas
- `valkey_memory_used_bytes` - Memory usage
- `valkey_commands_processed_total` - Commands processed
- And many more...

### Alerts

Pre-configured alerts:
- **ValkeyDown**: Instance is unreachable
- **ValkeyHighMemoryUsage**: Memory usage > 90%
- **ValkeyReplicationBroken**: Master has no replicas

### Grafana Dashboard

Import dashboard ID `763` for Redis metrics visualization.

## Backup and Restore

### Backup

Valkey uses two persistence mechanisms:
1. **RDB (Redis Database)**: Point-in-time snapshots
2. **AOF (Append-Only File)**: Transaction log

```bash
# Trigger manual save
kubectl exec -n infrastructure valkey-master-0 -- valkey-cli -a $VALKEY_PASSWORD BGSAVE

# Check save status
kubectl exec -n infrastructure valkey-master-0 -- valkey-cli -a $VALKEY_PASSWORD LASTSAVE
```

### Restore

```bash
# Copy backup to pod
kubectl cp backup.rdb infrastructure/valkey-master-0:/data/dump.rdb

# Restart pod to load backup
kubectl delete pod -n infrastructure valkey-master-0
```

## Troubleshooting

### Check Pod Status

```bash
kubectl get pods -n infrastructure -l app.kubernetes.io/name=valkey
```

### View Logs

```bash
# Master logs
kubectl logs -n infrastructure valkey-master-0 -c valkey

# Replica logs
kubectl logs -n infrastructure valkey-replica-0 -c valkey

# Sentinel logs
kubectl logs -n infrastructure -l app.kubernetes.io/component=sentinel
```

### Connect to Valkey CLI

```bash
# Master
kubectl exec -it -n infrastructure valkey-master-0 -- valkey-cli -a $VALKEY_PASSWORD

# Replica
kubectl exec -it -n infrastructure valkey-replica-0 -- valkey-cli -a $VALKEY_PASSWORD

# Check replication status
kubectl exec -n infrastructure valkey-master-0 -- valkey-cli -a $VALKEY_PASSWORD INFO replication
```

### Common Issues

**Issue: Pods in CrashLoopBackOff**
```bash
# Check events
kubectl describe pod -n infrastructure valkey-master-0

# Common causes:
# 1. Insufficient resources
# 2. Storage provisioning failure
# 3. Security context restrictions
```

**Issue: Replication not working**
```bash
# Check master-replica connectivity
kubectl exec -n infrastructure valkey-replica-0 -- ping valkey-master

# Verify credentials
kubectl get secret -n infrastructure valkey -o yaml
```

## Uninstallation

```bash
# Uninstall the chart
helm uninstall valkey -n infrastructure

# Delete PVCs (if needed)
kubectl delete pvc -n infrastructure -l app.kubernetes.io/name=valkey
```

## Upgrading

```bash
# Update values or chart version
helm upgrade valkey . -n infrastructure -f custom-values.yaml

# Rollback if needed
helm rollback valkey -n infrastructure
```

## Security Considerations

1. **Change default password** in production
2. **Use external secrets management** (Vault, AWS Secrets Manager)
3. **Enable TLS** for client connections (requires cert-manager)
4. **Restrict network policies** to only required sources
5. **Regular security scanning** of container images
6. **Implement RBAC** for Kubernetes access

## Performance Tuning

### For High Throughput

```yaml
configmap:
  extraConfig: |
    tcp-backlog 2048
    maxclients 20000
    timeout 300
    tcp-keepalive 60
```

### For Low Latency

```yaml
replica:
  resources:
    requests:
      cpu: 2000m
      memory: 4Gi

configmap:
  extraConfig: |
    appendfsync no  # Sacrifice durability for speed
    save ""  # Disable snapshotting
```

## License

MIT

## Support

For issues and questions:
- GitHub Issues: [your-repo/issues]
- Documentation: [ARCHITECTURE.md](../../../ARCHITECTURE.md)
