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

## 2. Deploy Valkey

```bash
helm upgrade --install valkey infra/helm/valkey -n infrastructure
```

## 3. Deploy Kafka

```bash
helm upgrade --install kafka infra/helm/queue -n infrastructure
```

## 4. Deploy API and Worker

```bash
helm upgrade --install api infra/helm/api -n application
helm upgrade --install worker infra/helm/worker -n worker
```

## 5. Deploy Monitoring

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

## 6. Smoke test

```bash
kubectl -n application port-forward svc/api-api 8080:80
curl -f http://localhost:8080/health
```

## Secrets
Update the following before production:
- `infra/helm/api/values.yaml` `secrets.kafkaBootstrapServers`, `secrets.kafkaUsername`, `secrets.kafkaPassword`, `secrets.valkeyPassword`, `secrets.jwtSecret`
- `infra/helm/worker/values.yaml` `secrets.kafkaBootstrapServers`, `secrets.kafkaUsername`, `secrets.kafkaPassword`, `secrets.valkeyPassword`
- `infra/helm/queue/values.yaml` `auth.username`, `auth.password`, `auth.clusterId`
