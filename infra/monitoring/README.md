# Monitoring Stack

This folder provides values and manifests to deploy Prometheus Operator, Grafana, and Loki.

## Install (Helm)

1. Add repositories:

```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo add grafana https://grafana.github.io/helm-charts
helm repo update
```

2. Install Prometheus Operator and Grafana:

```bash
helm upgrade --install kube-prometheus-stack prometheus-community/kube-prometheus-stack \
  --namespace monitoring --create-namespace \
  -f infra/monitoring/values-kube-prometheus-stack.yaml
```

3. Install Loki stack:

```bash
helm upgrade --install loki grafana/loki-stack \
  --namespace monitoring \
  -f infra/monitoring/values-loki.yaml
```

4. Apply the dashboard ConfigMap:

```bash
kubectl apply -f infra/monitoring/grafana-dashboard.yaml
```
