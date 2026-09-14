\# LoanTrack Evidence



This document records the commands and verification performed for the Docker Compose and Kubernetes implementations.



\## 1. Docker Compose



\### 1.1 Start all services



Command:



```powershell

docker compose up -d

docker compose ps



Expected verification:



PostgreSQL is healthy.

Backend is running.

Frontend is running.

Backend waits for PostgreSQL health before starting.

1.2 Backend health and readiness



Commands:



curl.exe http://localhost:8000/healthz

curl.exe http://localhost:8000/readyz



Observed:



/healthz -> {"status":"ok"}

/readyz -> {"status":"ready"}



This confirms that the backend health endpoint works and readiness confirms database availability.



1.3 UI -> Backend -> PostgreSQL



A loan was submitted through the frontend UI.



The corresponding database row was then verified directly through PostgreSQL:



id | borrower\_name | amount  | status

\---+---------------+---------+--------

8  | evidence      | 15000.00| Pending



This demonstrates the application flow:



Frontend -> Backend API -> PostgreSQL



The frontend does not connect directly to PostgreSQL.



1.4 Database persistence



The PostgreSQL named volume was tested with:



docker compose down

docker compose up -d



The previously created loan remained in the database after the containers were recreated.



This verifies persistence through the named PostgreSQL volume.



1.5 Volume reset



The following command was also tested:



docker compose down -v

docker compose up -d



Removing the volume deleted the previous database state.



After a fresh startup, the migration initialized the database with the five seed rows.



1.6 Database startup retry



PostgreSQL was stopped and the backend was restarted:



docker compose stop postgres

docker compose restart backend

docker compose logs backend



The backend logs showed repeated database connection attempts and retry/backoff behavior while PostgreSQL was unavailable.



After PostgreSQL was started again:



docker compose start postgres

docker compose restart backend

docker compose ps



the backend recovered and became healthy.



1.7 Health vs readiness when database is unavailable



With PostgreSQL stopped:



curl.exe http://localhost:8000/healthz

curl.exe http://localhost:8000/readyz



Observed:



/healthz -> {"status":"ok"}

/readyz -> database unavailable



This demonstrates that liveness/health remains independent of database availability while readiness reports that the application cannot currently serve database-dependent traffic.



1.8 Backend image size



Command:



docker images loantrack-backend



Observed:



loantrack-backend:dev

DISK USAGE 270MB

CONTENT SIZE 64.2MB



loantrack-backend:latest

DISK USAGE 270MB

CONTENT SIZE 64.2MB



The backend image is below the required 300 MB limit.



2\. Kubernetes

2.1 Namespace isolation



LoanTrack resources were moved into the dedicated namespace:



kubectl get all -n loantrack



The application resources are deployed in:



loantrack



The default namespace was checked and LoanTrack application resources were removed from it.



The remaining resources in default are unrelated to LoanTrack.



2.2 Kubernetes application status



Command:



kubectl get all -n loantrack



Observed application components:



backend       Deployment

frontend      Deployment

postgres      Deployment

backend       ClusterIP Service

frontend      NodePort Service

postgres      ClusterIP Service



The PostgreSQL PVC was also bound successfully.



2.3 Resource requests and limits



Command:



kubectl get deployment -n loantrack \\

&#x20; -o custom-columns=NAME:.metadata.name,REQUESTS\_CPU:.spec.template.spec.containers\[0].resources.requests.cpu,REQUESTS\_MEMORY:.spec.template.spec.containers\[0].resources.requests.memory,LIMITS\_CPU:.spec.template.spec.containers\[0].resources.limits.cpu,LIMITS\_MEMORY:.spec.template.spec.containers\[0].resources.limits.memory



Observed:



backend    100m  128Mi  500m  512Mi

frontend    50m   64Mi  200m  128Mi

postgres   100m  128Mi  500m  512Mi



Every application container has CPU and memory requests and limits.



2.4 Backend health probes



Command:



kubectl describe deployment backend -n loantrack



The backend deployment contains:



Startup probe:   /healthz

Liveness probe:  /healthz

Readiness probe: /readyz



These correspond to the application's health and readiness endpoints tested in the Docker section.



2.5 Frontend probes



The frontend deployment contains HTTP probes against:



/



The frontend container serves the application through Nginx on port 8080.



2.6 Kubernetes Secret



The PostgreSQL credentials are stored in:



postgres-secret



The backend deployment consumes the credentials through secretKeyRef.



The PostgreSQL deployment also references the Secret rather than containing a literal database password.



A dummy example is committed as:



k8s/secret.example.yaml



Real credentials are supplied locally during deployment and are not committed to Git.



2.7 Kubernetes ConfigMap



The PostgreSQL migration is stored in the non-sensitive ConfigMap:



postgres-migration



The migration is mounted into PostgreSQL during deployment.



2.8 PostgreSQL DNS



From the backend environment, PostgreSQL was resolved using the Kubernetes service DNS name:



postgres.loantrack.svc.cluster.local



The service resolved successfully to the PostgreSQL ClusterIP.



This verifies Kubernetes service-name DNS rather than hard-coded pod IP addressing.



2.9 Kubernetes health and readiness



The backend endpoints were verified inside Kubernetes:



/healthz -> {"status":"ok"}

/readyz -> {"status":"ready"}

2.10 Backend scaling



The backend was scaled to three replicas:



kubectl scale deployment/backend --replicas=3 -n loantrack

kubectl get pods -n loantrack

kubectl get endpoints backend -n loantrack



Three backend pods were running and the backend service exposed endpoints for all three pods.



The configured HPA has:



min replicas: 1

max replicas: 3

target CPU:   70%

2.11 Rolling update and rollback



A second backend image was built:



loantrack-backend:v2



The deployment was updated using:



kubectl set image deployment/backend backend=loantrack-backend:v2 -n loantrack

kubectl rollout status deployment/backend -n loantrack



The rollout completed successfully.



Rollback was then tested:



kubectl rollout undo deployment/backend -n loantrack

kubectl rollout status deployment/backend -n loantrack



The deployment successfully returned to:



loantrack-backend:v1.0.0

2.12 Backend pod replacement



A backend pod was manually deleted:



kubectl delete pod <backend-pod-name> -n loantrack

kubectl get pods -n loantrack



Kubernetes created a replacement pod automatically and the Deployment returned to the desired replica count.



2.13 PostgreSQL pod replacement and persistence



The PostgreSQL pod was deleted:



kubectl delete pod <postgres-pod-name> -n loantrack



A replacement PostgreSQL pod was created by the Deployment.



The database row count before and after the PostgreSQL pod replacement remained:



5 rows



This verifies that database data survives PostgreSQL pod replacement because the database uses the persistent volume.



2.14 Final Kubernetes resource inventory



Command:



kubectl get all,pvc,configmap,secret,ingress -n loantrack



The final deployment contains:



Backend Deployment and Service

Frontend Deployment and NodePort Service

PostgreSQL Deployment and ClusterIP Service

PostgreSQL PVC

PostgreSQL migration ConfigMap

PostgreSQL Secret

LoanTrack Ingress

Backend HPA

2.15 Kubernetes deployment automation



The project includes:



scripts/deploy.sh



The script:



Loads local environment variables.

Builds the backend image in Minikube.

Builds the frontend image in Minikube.

Creates the LoanTrack namespace.

Creates/updates the PostgreSQL Secret.

Applies the migration ConfigMap.

Deploys PostgreSQL.

Waits for PostgreSQL rollout.

Deploys the backend and HPA.

Waits for backend rollout.

Deploys the frontend.

Waits for frontend rollout.

Applies the Ingress.

Prints the frontend service URL.



The script was executed successfully against the Minikube cluster and completed all rollout checks.



3\. Required UI Evidence



Screenshots should be stored under:



evidence/



Recommended screenshots:



# Screenshot Evidence

## Docker

### Docker Compose Health

![Docker Compose Healthy](evidence/Docker%20Compse%20Healty.png)

### Docker Health and Readiness

![Docker Health Ready](evidence/Docker%20Health%20Ready.png)

### Add New Loan

![Add New Loan](evidence/Add%20new%20loan.png)

### Docker UI

![Docker UI](evidence/Docker%20UI%202.png)

### Docker Persistence

![Docker Persistence](evidence/Docker%20Persistence.png)

### Docker Image Size

![Docker Image Size](evidence/Docker%20Image%20size.png)

## Kubernetes

### Kubernetes Resources

![Kubernetes Resources](evidence/K8%20resources.png)

### Kubernetes Resource Limits

![Kubernetes Resource Limits](evidence/K8s%20Resource%20limit.png)

### Backend Probes

![Kubernetes Backend Probes](evidence/K8s%20backend%20probes.png)

### Kubernetes DNS

![Kubernetes DNS](evidence/K8s%20dns.png)

### Kubernetes Secret

![Kubernetes Secret](evidence/K8s%20Secret.png)

### Kubernetes Rollout

![Kubernetes Rollout](evidence/K8s%20Rollout.png)


The screenshots are supplementary evidence; the commands and outputs above document the technical verification.



4\. Verification Summary

Requirement	Verified

Docker Compose starts all tiers Yes

Backend /healthz	  	Yes

Backend /readyz			Yes

DB startup retry		Yes

Health independent of DB	Yes

Readiness depends on DB		Yes

UI -> Backend -> DB		Yes

Docker volume persistence	Yes

down -v resets DB		Yes

Backend image < 300 MB		Yes

Kubernetes namespace isolation	Yes

Kubernetes probes		Yes

Resource requests/limits	Yes

Secret-based DB credentials	Yes

ConfigMap migration		Yes

Kubernetes service DNS		Yes

Backend scaling to 3		Yes

Rolling update			Yes

Rollback			Yes

Backend pod replacement		Yes

PostgreSQL pod replacement	Yes

PostgreSQL data persistence	Yes

Automated Kubernetes deployment	Yes

