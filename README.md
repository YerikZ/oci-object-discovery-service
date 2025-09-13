# OCI Object Discovery Service

Components:
- Controller API (FastAPI)
- Scheduler (APScheduler)
- Scanner Worker (Redis + stubbed OCI client)

## Local (Docker Compose)
```bash
cd deployments
docker-compose up --build
```

## Kubernetes (kubectl)
```bash
kubectl apply -f deployments/k8s/base/namespace.yaml
kubectl apply -f deployments/k8s/base/redis.yaml
kubectl apply -f deployments/k8s/base/configmap-manifest.yaml
kubectl apply -f deployments/k8s/base/controller-api-deploy.yaml
kubectl apply -f deployments/k8s/base/scheduler-deploy.yaml
kubectl apply -f deployments/k8s/base/worker-deploy.yaml
kubectl apply -f deployments/k8s/base/ingress.yaml   # optional
```
