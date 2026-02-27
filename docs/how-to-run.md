# How to Run

## Prerequisites
- Docker
- kubectl
- Helm 3+
- A Kubernetes cluster (kind/minikube/k3s)

## 1. Create namespaces and policies

```bash
kubectl apply -f infra/base/namespaces.yaml
kubectl apply -f infra/base/network-policies.yaml
```

## 2. Deploy Monitoring (required for ServiceMonitor/PrometheusRule)

```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo add grafana https://grafana.github.io/helm-charts
helm repo update

helm upgrade --install kube-prometheus-stack prometheus-community/kube-prometheus-stack \
  --namespace monitoring --create-namespace \
  -f infra/monitoring/values-kube-prometheus-stack.yaml

helm upgrade --install loki grafana/loki-stack \
  --namespace monitoring \
  -f infra/monitoring/values-loki.yaml

kubectl apply -f infra/monitoring/grafana-dashboard.yaml
```

## 3. Deploy Valkey

```bash
helm upgrade --install valkey infra/helm/valkey -n infrastructure
```

## 4. Deploy Kafka

```bash
helm upgrade --install kafka infra/helm/queue -n infrastructure
```

## 5. Deploy API and Worker

```bash
helm upgrade --install api infra/helm/api -n application
helm upgrade --install worker infra/helm/worker -n worker
```

## 6. Wait for pods to be ready

```bash
kubectl -n application rollout status deploy/api-api
kubectl -n worker rollout status deploy/worker-worker
```

If a pod is stuck in Pending, check events:

```bash
kubectl -n application get pods -o wide
kubectl -n application describe pod -l app.kubernetes.io/instance=api
```

## 7. Smoke test

```bash
kubectl -n application port-forward svc/api-api 8080:80
curl -f http://localhost:8080/health
```

## Secrets
Update the following before production:
- `infra/helm/api/values.yaml` `secrets.kafkaBootstrapServers`, `secrets.kafkaUsername`, `secrets.kafkaPassword`, `secrets.valkeyPassword`, `secrets.jwtSecret`
- `infra/helm/worker/values.yaml` `secrets.kafkaBootstrapServers`, `secrets.kafkaUsername`, `secrets.kafkaPassword`, `secrets.valkeyPassword`
- `infra/helm/queue/values.yaml` `auth.username`, `auth.password`, `auth.clusterId`
