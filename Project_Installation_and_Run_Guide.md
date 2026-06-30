This Project contains:

* FastAPI Backend
* React Frontend (Vite)
* PostgreSQL
* Redis
* ChromaDB
* Celery Worker
* Docker Compose
* Environment file (.env)

---

# Wireless Communication Industry Knowledge Assistance

## Installation & Setup Guide (For a New PC)

---

# System Requirements

### Operating System

Any one of the following:

* Windows 10/11 (Recommended)
* Ubuntu 22.04+
* macOS

---

# Software Required

Install the following software before running the project.

## 1. Git

Download and install:

[https://git-scm.com/downloads](https://git-scm.com/downloads)

Verify

```bash
git --version
```

---

## 2. Docker Desktop

Download

[https://www.docker.com/products/docker-desktop/](https://www.docker.com/products/docker-desktop/)

After installation verify

```bash
docker --version

docker compose version
```

If both commands work, Docker is installed correctly.

---

## 3. VS Code
Download

[https://code.visualstudio.com/](https://code.visualstudio.com/)

Recommended Extensions

* Docker
* Python
* ESLint
* Prettier

---


# Optional (Only if AI APIs are Required)

If you want live AI responses:

Create accounts and obtain API keys:

* OpenAI API Key
* Tavily API Key (Optional)

---

# Project Setup

## Step 1

Clone the repository

```bash
git clone <repository-url>
```

or extract the ZIP file.

---

## Step 2

Open terminal

Go inside the project

```bash
cd wireless-communication-industry-knowledge-assistance
```

---

## Step 3

Create Environment File

Copy

```bash
cp .env.example .env
```

 For Windows PowerShell

```powershell
copy .env.example .env
```

---

## Step 4

Open `.env`

Update these values.

Example

```env
OPENAI_API_KEY=your_openai_api_key

TAVILY_API_KEY=your_tavily_api_key

JWT_SECRET=your_secret

ADMIN_USERNAME=admin

ADMIN_PASSWORD=admin123

POSTGRES_PASSWORD=password
```

---

# Running the Project

## Start Everything

```bash
docker compose up --build
```

The first run may take **5–15 minutes** because Docker downloads all required images and builds the containers.

---

## Run in Background

```bash
docker compose up -d --build
```

---

# Verify Containers

```bash
docker compose ps
```

You should see services similar to:

* frontend
* backend
* postgres
* redis
* chromadb
* worker

All should show **Up** or **Running**.

---

# Access the Application

## Frontend

```
http://localhost:5173
```

---

## Backend API

```
http://localhost:18000
```

---

## Swagger API Docs

```
http://localhost:18000/docs
```

---

## ChromaDB

```
http://localhost:18001
```

---

# Health Check

Backend

```bash
curl http://localhost:18000/health
```

Expected

```json
{
  "status":"healthy"
}
```

---

Ready Check

```bash
curl http://localhost:18000/ready
```

---

# View Logs

Backend

```bash
docker compose logs -f backend
```

Frontend

```bash
docker compose logs -f frontend
```

Worker

```bash
docker compose logs -f worker
```

All Services

```bash
docker compose logs -f
```

---

# Stop the Project

```bash
docker compose down
```

---

# Restart

```bash
docker compose up -d
```

---

# Rebuild After Code Changes

```bash
docker compose up --build
```

---

# Common Commands

## Check Running Containers

```bash
docker ps
```

---

## Check Images

```bash
docker images
```

---

## Remove Containers

```bash
docker compose down
```

---

## Remove Everything (Containers + Volumes)

```bash
docker compose down -v
```

---

## Rebuild from Scratch

```bash
docker compose down -v

docker compose up --build
```

---

# Project Architecture

```
                User
                  │
                  ▼
        React Frontend (Vite)
                  │
                  ▼
          FastAPI Backend
        ┌─────────┼──────────┐
        │         │          │
        ▼         ▼          ▼
   PostgreSQL   Redis    ChromaDB
                             │
                             ▼
                     Vector Database

                  │
                  ▼
             Celery Worker

                  │
                  ▼
        OpenAI / Tavily APIs
```

---

# Troubleshooting

### Docker is not running

Start Docker Desktop and wait until it shows **Docker Engine Running**.

---

### Port Already in Use

If ports 5173, 18000, or 18001 are occupied, stop the conflicting application or update the ports in the `.env` file if your project supports custom host ports.

---

### Environment Variables Missing

Ensure the `.env` file exists and contains valid values for required variables such as API keys and passwords.

---

### Containers Exit Immediately

Inspect logs:

```bash
docker compose logs
```

or

```bash
docker compose logs -f backend
```

---

This guide is simple enough to follow on a fresh machine without needing to install Python, Node.js, PostgreSQL, or Redis manually, since Docker Compose handles those dependencies.
