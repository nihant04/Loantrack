#!/usr/bin/env bash
set -e

if [ -f .env ]; then
  set -a
  . ./.env
  set +a
fi

: "${POSTGRES_DB:?POSTGRES_DB is not set. Copy .env.example to .env first.}"
: "${POSTGRES_USER:?POSTGRES_USER is not set. Copy .env.example to .env first.}"
: "${POSTGRES_PASSWORD:?POSTGRES_PASSWORD is not set. Copy .env.example to .env first.}"

echo "Building backend image..."
minikube image build -t loantrack-backend:v1.0.0 ./backend

echo "Building frontend image..."
minikube image build -t loantrack-frontend:v1.0.0 ./frontend

echo "Creating namespace..."
kubectl apply -f k8s/namespace.yaml

echo "Creating PostgreSQL Secret..."
kubectl create secret generic postgres-secret \
  --namespace loantrack \
  --from-literal=POSTGRES_DB="${POSTGRES_DB}" \
  --from-literal=POSTGRES_USER="${POSTGRES_USER}" \
  --from-literal=POSTGRES_PASSWORD="${POSTGRES_PASSWORD}" \
  --dry-run=client -o yaml | kubectl apply -f -

echo "Applying PostgreSQL migration..."
kubectl apply -n loantrack -f k8s/postgres-migration.yaml

echo "Applying PostgreSQL..."
kubectl apply -n loantrack -f k8s/postgres.yaml

echo "Waiting for PostgreSQL..."
kubectl rollout status deployment/postgres -n loantrack --timeout=120s

echo "Applying backend..."
kubectl apply -n loantrack -f k8s/backend.yaml
kubectl apply -n loantrack -f k8s/backend-hpa.yaml

echo "Waiting for backend..."
kubectl rollout status deployment/backend -n loantrack --timeout=120s

echo "Applying frontend..."
kubectl apply -n loantrack -f k8s/frontend.yaml

echo "Waiting for frontend..."
kubectl rollout status deployment/frontend -n loantrack --timeout=120s

echo "Applying Ingress..."
kubectl apply -n loantrack -f k8s/ingress.yaml

echo ""
echo "LoanTrack deployment complete."
echo "Frontend URL:"
minikube service frontend -n loantrack --url