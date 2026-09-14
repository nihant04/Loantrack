\# LoanTrack



LoanTrack is a three-tier loan management application consisting of a frontend, FastAPI backend, and PostgreSQL database. The same application can be run locally with Docker Compose or deployed to Kubernetes using Minikube.



\## Architecture



```text

&#x20;                        +----------------------+

&#x20;                        |      Browser         |

&#x20;                        +----------+-----------+

&#x20;                                   |

&#x20;                        HTTP :8081 / NodePort

&#x20;                                   |

&#x20;                                   v

&#x20;                        +----------------------+

&#x20;                        |     Frontend         |

&#x20;                        |   Nginx :8080        |

&#x20;                        +----------+-----------+

&#x20;                                   |

&#x20;                             HTTP API

&#x20;                                   |

&#x20;                                   v

&#x20;                        +----------------------+

&#x20;                        |      Backend         |

&#x20;                        | FastAPI :8000        |

&#x20;                        | /loans               |

&#x20;                        | /healthz             |

&#x20;                        | /readyz              |

&#x20;                        +----------+-----------+

&#x20;                                   |

&#x20;                             PostgreSQL

&#x20;                                   |

&#x20;                                   v

&#x20;                        +----------------------+

&#x20;                        |     PostgreSQL       |

&#x20;                        |       :5432          |

&#x20;                        +----------------------+



The frontend communicates with the backend over HTTP. The frontend never connects directly to PostgreSQL.



Technology Stack

Frontend: HTML/CSS/JavaScript served by Nginx

Backend: Python 3.12, FastAPI, Uvicorn, psycopg connection pool

Database: PostgreSQL 16

Containerization: Docker, Docker Compose

Kubernetes: Minikube, kubectl

Kubernetes ingress: Nginx Ingress

Database storage: Docker named volume / Kubernetes PVC

Required Versions



The development environment used for the assignment includes:



Minikube: 1.38.1

kubectl client: 1.36.0

Docker: Docker Desktop

PostgreSQL image: 16

Python: 3.12.x



Check the installed versions on a machine with:



minikube version

kubectl version --client

docker --version

python --version

Application API

GET /loans



Returns all loans.



POST /loans



Creates a new loan.



GET /healthz



Returns application health without requiring database availability.



Expected response:



{"status":"ok"}

GET /readyz



Checks whether the backend can reach PostgreSQL.



Expected response when the database is available:



{"status":"ready"}



When PostgreSQL is unavailable, readiness fails while /healthz remains available.



Database



The database contains a loans table with seeded records.



The migration is versioned:



db/migrations/001\_create\_loans.sql



The application uses a PostgreSQL connection pool.



On startup, the backend retries database connection attempts with retry/backoff behavior instead of immediately terminating.



Docker Compose

Configuration



Create the local environment file:



cp .env.example .env



Edit .env if required.



.env is intentionally ignored by Git. Real credentials must never be committed.



Start the application

docker compose up -d



Check the services:



docker compose ps



Expected services:



postgres

backend

frontend

Open the frontend

http://localhost:8081

Test the backend

curl http://localhost:8000/healthz

curl http://localhost:8000/readyz

curl http://localhost:8000/loans

Stop the application

docker compose down



The PostgreSQL named volume is retained by default, so database data survives a normal down followed by up.



To intentionally delete the database volume:



docker compose down -v



A subsequent docker compose up -d creates a fresh database and reruns the initial migration/seed data.



\## Docker Security and Optimization



The backend image uses a multi-stage Docker build with a pinned Python base image.



The runtime container runs as a non-root user.



The backend image contains a Docker `HEALTHCHECK` for `/healthz`.



The Dockerfile installs Python dependencies before copying the application source. This creates the main cache boundary: dependency layers remain reusable when only application source files change.



The backend image was verified to remain below the required 300 MB image-size limit.



The frontend runtime is served by an unprivileged Nginx configuration on port 8080. The frontend is a static runtime image and does not require a separate build-dependency stage.



Kubernetes



All LoanTrack resources are deployed into:



loantrack



The default namespace is not used for LoanTrack workloads.



Kubernetes resources



The deployment includes:



Backend Deployment

Backend ClusterIP Service

Backend HPA

Frontend Deployment

Frontend NodePort Service

PostgreSQL Deployment

PostgreSQL ClusterIP Service

PostgreSQL PVC

PostgreSQL migration ConfigMap

PostgreSQL Secret

Nginx Ingress

loantrack Namespace

Create the cluster



Start Minikube:



minikube start --driver=docker



Enable the ingress addon if required:



minikube addons enable ingress

One-command deployment



The repository provides:



./scripts/deploy.sh



The deployment script:



Loads local .env values.

Builds the backend image.

Builds the frontend image.

Creates the loantrack namespace.

Creates/updates the PostgreSQL Secret without exposing its values in Kubernetes manifests.

Applies the migration ConfigMap.

Deploys PostgreSQL.

Waits for PostgreSQL rollout.

Deploys the backend.

Applies the backend HPA.

Waits for backend rollout.

Deploys the frontend.

Waits for frontend rollout.

Applies the Ingress.

Prints the frontend service URL.



The script uses declarative/idempotent kubectl apply operations where appropriate, so it can be rerun safely.



Kubernetes status

kubectl get all -n loantrack



Check storage, configuration and ingress:



kubectl get pvc,configmap,secret,ingress -n loantrack

Frontend



The frontend is exposed using a NodePort Service.



The deployment script prints the URL using:



minikube service frontend -n loantrack --url



On Windows with the Docker driver, keep the terminal open while using the temporary Minikube service URL.



Backend health



Backend probes use:



Startup probe:   /healthz

Liveness probe:  /healthz

Readiness probe: /readyz



The frontend has HTTP liveness/readiness probes against /.



Resource management



CPU and memory requests/limits are defined for every application container.



The current values are:



Workload	CPU Request	Memory Request	CPU Limit	Memory Limit

Backend	100m	128Mi	500m	512Mi

Frontend	50m	64Mi	200m	128Mi

PostgreSQL	100m	128Mi	500m	512Mi

Backend HPA



The backend HPA is configured for:



Minimum replicas: 1

Maximum replicas: 3

CPU target: 70%



Check it with:



kubectl get hpa -n loantrack

Database storage



PostgreSQL uses a PersistentVolumeClaim:



postgres-pvc



The database Service is a ClusterIP Service and is therefore not directly exposed outside the Kubernetes cluster.



Kubernetes Secret



Database credentials are stored in:



postgres-secret



The backend consumes the values using secretKeyRef.



A dummy template is committed as:



k8s/secret.example.yaml



Real credentials must not be committed to Git.



The deployment script creates/updates the actual Secret from the local ignored .env file.



Useful Kubernetes Operations



Check pods:



kubectl get pods -n loantrack



Check services:



kubectl get svc -n loantrack



Check deployments:



kubectl get deployments -n loantrack



Scale the backend:



kubectl scale deployment backend --replicas=3 -n loantrack



Check rollout:



kubectl rollout status deployment/backend -n loantrack



Update the backend image:



kubectl set image deployment/backend backend=loantrack-backend:v2 -n loantrack



Undo a rollout:



kubectl rollout undo deployment/backend -n loantrack



Check rollout history:



kubectl rollout history deployment/backend -n loantrack



Delete a backend pod and observe Kubernetes replace it:



kubectl delete pod <backend-pod-name> -n loantrack



Check database rows:



kubectl exec -n loantrack deploy/postgres -- \\

&#x20; psql -U loantrack -d loantrack \\

&#x20; -c "SELECT id, borrower\_name, amount, status FROM loans ORDER BY id;"



Check backend-to-PostgreSQL DNS:



kubectl exec -n loantrack deploy/backend -- \\

&#x20; python -c "import socket; print(socket.gethostbyname\_ex('postgres'))"



The expected Kubernetes DNS name is:



postgres.loantrack.svc.cluster.local

Design Decisions

PostgreSQL Deployment + PVC



PostgreSQL is deployed with a PersistentVolumeClaim so that the database data is independent of an individual PostgreSQL pod. For this assignment, a Deployment with one replica and a PVC is sufficient for demonstrating persistence. A production high-availability database would normally use a managed PostgreSQL service or an appropriate PostgreSQL operator/StatefulSet architecture.



Health vs Readiness



/healthz intentionally does not require PostgreSQL. It answers whether the backend process is alive.



/readyz checks database availability and therefore becomes unavailable when PostgreSQL cannot be reached.



This prevents a temporary database problem from being confused with a crashed backend process.



Secrets



Kubernetes Secret values are consumed using secretKeyRef. The repository does not contain real credentials.



Kubernetes Secret values are encoded rather than encrypted by the manifest representation itself, so production environments should use appropriate secret-management/encryption-at-rest controls such as an external secret manager or encrypted Kubernetes secret storage.



Requests and Limits



Requests provide Kubernetes scheduling guarantees for the expected baseline resource usage. Limits prevent a container from consuming unlimited CPU or memory and provide predictable resource boundaries.



Evidence



Detailed command outputs and testing evidence are maintained in:



EVIDENCE.md



The evidence includes Docker Compose health/readiness behavior, database persistence, Kubernetes resources, probes, scaling, rollout operations, pod replacement, DNS resolution, and database persistence.



AI Usage



AI assistance used during development is documented separately in:



AI\_USAGE.md

Git Workflow



The repository uses:



main — stable/deployable branch

develop — integration branch

feature/\* — feature implementation branches



Branching details are documented in:



BRANCHING.md



Annotated release tags:



v1.0.0 — Docker/Compose working

v1.1.0 — Kubernetes working



No real credentials or .env files are committed to the repository.



