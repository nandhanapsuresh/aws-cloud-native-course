# AWS Cloud-Native Course Management API

> Academic project demonstrating a cloud-native REST API built with Flask, containerised with Docker, and deployed on Amazon EKS using a fully automated CI/CD pipeline.

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [API Endpoints](#api-endpoints)
- [Local Development](#local-development)
- [Docker](#docker)
- [AWS Infrastructure](#aws-infrastructure)
- [CI/CD Pipeline](#cicd-pipeline)
- [Kubernetes Deployment](#kubernetes-deployment)
- [Environment Variables](#environment-variables)
- [Author](#author)

---

## Overview

This project implements a **Course Management REST API** that allows students to create, retrieve, and list courses. It is designed as a cloud-native application following modern DevOps practices:

- Stateless Flask microservice backed by **Amazon DynamoDB**
- Containerised with a multi-stage **Docker** build for minimal image size
- Stored in **Amazon ECR** and deployed on **Amazon EKS**
- Exposed via an **AWS Application Load Balancer (ALB)** Ingress
- Automated build and push via **AWS CodeBuild** (`buildspec.yaml`)
- Observability via **AWS X-Ray SDK**

---

## Architecture

```
                        ┌─────────────────────────────────────┐
                        │           Amazon EKS Cluster         │
  Browser / Client      │  Namespace: cloudstudents            │
       │                │                                      │
       │  HTTP          │  ┌──────────┐    ┌───────────────┐  │
       └──────────────► │  │  ALB     │──► │  Flask App    │  │
                        │  │ Ingress  │    │  (Gunicorn)   │  │
                        │  └──────────┘    │  Port 3001    │  │
                        │                  └──────┬────────┘  │
                        └─────────────────────────┼───────────┘
                                                   │
                        ┌──────────────────────────▼───────────┐
                        │          Amazon DynamoDB              │
                        │       Table: nandhana-course          │
                        └──────────────────────────────────────┘

  GitHub ──► AWS CodeBuild ──► Amazon ECR ──► EKS (rolling deploy)
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.12 |
| Framework | Flask 3.0 + Gunicorn |
| Database | Amazon DynamoDB |
| Container | Docker (multi-stage, slim image) |
| Registry | Amazon ECR |
| Orchestration | Amazon EKS (Kubernetes) |
| Ingress | AWS ALB Ingress Controller |
| CI/CD | AWS CodeBuild |
| Observability | AWS X-Ray SDK |
| CORS | flask-cors |

---

## Project Structure

```
aws-cloud-native-course/
├── app.py                  # Flask application & API routes
├── requirements.txt        # Python dependencies
├── Dockerfile              # Multi-stage Docker build
├── .dockerignore           # Files excluded from Docker context
├── buildspec.yaml          # AWS CodeBuild CI/CD spec
└── nandhana-course.yaml    # Kubernetes manifests (Deployment, Service, Ingress)
```

---

## API Endpoints

All endpoints are served under the `/nandhana-student` path prefix.

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/nandhana-student` | Home / liveness check |
| `GET` | `/nandhana-student/health` | Health check (used by ALB) |
| `POST` | `/nandhana-student/courses` | Create a new course |
| `GET` | `/nandhana-student/courses` | List all courses (max 50) |
| `GET` | `/nandhana-student/courses/<course_code>` | Get a course by ID |

### Example: Create a Course

```bash
curl -X POST https://<ALB_HOST>/nandhana-student/courses \
  -H "Content-Type: application/json" \
  -d '{"id": "CS101", "name": "Cloud Computing", "credits": 3}'
```

### Example: Get a Course

```bash
curl https://<ALB_HOST>/nandhana-student/courses/CS101
```

---

## Local Development

### Prerequisites

- Python 3.12+
- AWS credentials configured (`aws configure`)
- DynamoDB table `nandhana-course` created in `ap-south-2`

### Setup

```bash
# Clone the repository
git clone https://github.com/nandhanapsuresh/aws-cloud-native-course.git
cd aws-cloud-native-course

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate        # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the application
python app.py
```

The server will start on `http://localhost:3001`.

---

## Docker

### Build

```bash
docker build -t nandhana-course-app:latest .
```

### Run Locally

```bash
docker run -p 3001:3001 \
  -e AWS_REGION=ap-south-2 \
  -e AWS_ACCESS_KEY_ID=<your_key> \
  -e AWS_SECRET_ACCESS_KEY=<your_secret> \
  nandhana-course-app:latest
```

The Dockerfile uses a **multi-stage build**:
- **Builder stage** — installs dependencies into an isolated `/install` prefix
- **Runtime stage** — copies only the installed packages and `app.py`, runs as a non-root user (`appuser`) for security

A `HEALTHCHECK` is built into the image, polling `/health` every 15 seconds.

---

## AWS Infrastructure

### DynamoDB

| Property | Value |
|---|---|
| Table Name | `nandhana-course` |
| Partition Key | `id` (String) |
| Region | `ap-south-2` |

### Amazon ECR

```
991524241826.dkr.ecr.ap-south-2.amazonaws.com/nandhana-course-app
```

### S3 Static Frontend (CORS Origin)

```
http://nandhana-course-public.s3-website.ap-south-2.amazonaws.com
```

---

## CI/CD Pipeline

The `buildspec.yaml` file defines an **AWS CodeBuild** pipeline with three phases:

| Phase | Actions |
|---|---|
| `pre_build` | Authenticate Docker with ECR |
| `build` | Build and tag the Docker image |
| `post_build` | Push image to ECR; generate `imagedefinitions.json` |

The `imagedefinitions.json` artifact is consumed by downstream ECS/EKS deployment stages to roll out the new image.

---

## Kubernetes Deployment

The `nandhana-course.yaml` file contains three Kubernetes resources deployed to the `cloudstudents` namespace:

### Deployment

- 1 replica of the Flask app
- Image pulled from ECR (`imagePullPolicy: Always`)
- Container port: `3001`

### Service

- Type: `NodePort`
- Forwards traffic on port `3001` to the container

### Ingress

- Uses the **AWS ALB Ingress Controller**
- Scheme: `internet-facing`
- Target type: `ip`
- Ingress group: `students-app` (shared ALB)
- Path: `/nandhana-student` (prefix match)
- Health check path: `/health`

### Apply the Manifests

```bash
# Configure kubectl for your EKS cluster
aws eks update-kubeconfig --region ap-south-2 --name <your-cluster-name>

# Deploy
kubectl apply -f nandhana-course.yaml

# Verify
kubectl get pods -n cloudstudents
kubectl get ingress -n cloudstudents
```

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `AWS_REGION` | `ap-south-2` | AWS region for DynamoDB and other services |

AWS credentials are expected to be provided via IAM roles (EC2/EKS instance role) in production, or via environment variables / `~/.aws/credentials` locally.

---

## Author

**Nandhana P Suresh**
Academic project — AWS Cloud Native Course

---

*Built with Flask · Deployed on AWS EKS · Automated with AWS CodeBuild*
