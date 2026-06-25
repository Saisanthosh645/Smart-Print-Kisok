# SmartPrintX — Local and Deploy Guide

This repository contains the backend (FastAPI) and frontend (Vite + React) for SmartPrintX.

## Quick start (recommended — Docker Compose)

1. Ensure Docker Desktop is running.
2. From the repo root:
```bash
docker-compose up -d --build
```
3. Frontend: http://localhost:3000, Backend health: http://localhost:8000/health

## Local development (without Docker)

Backend:
```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:DATABASE_URL="postgresql+asyncpg://smartprintx:smartprintx@localhost:5432/smartprintx"
$env:REDIS_URL="redis://localhost:6379/0"
.venv\Scripts\python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Frontend:
```bash
cd frontend
npm install
npm run dev
```

## Environment
Copy `.env.example` to `.env` and fill values for production. Do NOT commit `.env`.

## How to see this "live" (production)

1. Provision a Linux VPS (DigitalOcean, Linode, etc.) with Docker and Docker Compose installed.
2. Copy the repo to the server and create a `.env` with production-ready values.
3. Run:
```bash
docker-compose up -d --build
```
4. Point your DNS to the server IP and configure a reverse proxy / TLS as needed.

## CI/CD (GitHub Actions)

This repo includes a scaffolded workflow to build Docker images and push to Docker Hub (or another registry) and optionally SSH-deploy to a server. You need to set the following repository secrets if you want automated pushes:
- `DOCKERHUB_USERNAME`
- `DOCKERHUB_TOKEN`
- `SSH_HOST`, `SSH_USER`, `SSH_PRIVATE_KEY` (for deployment via SSH)

## Before pushing to GitHub
- Ensure `.env` is not tracked.
- Remove any hard-coded secrets.
- Update `SECRET_KEY` for production.

## Tests
Run backend tests:
```bash
cd backend
pytest
```
# SmartPrintX – Intelligent Campus Printing Ecosystem

A cloud-based campus printing platform where students upload documents, pay online, and collect printouts from kiosks or print centers.

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│  React SPA  │────▶│  FastAPI     │────▶│ PostgreSQL  │
│  (Vite)     │     │  Backend     │     │  (RDS)      │
└─────────────┘     └──────┬───────┘     └─────────────┘
                           │
                    ┌──────┴───────┐
                    │ Redis Queue  │
                    │ (Heap/Priority)│
                    └──────┬───────┘
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
           AWS S3      Razorpay      SMTP Email
```

## Features

### Student Portal
- Signup/Login with JWT authentication
- Email verification & password reset
- Upload PDF, DOCX, PPTX
- Print options: B&W/Color, Single/Double-sided, page range
- AI cost calculator with optimization suggestions
- Razorpay payments (UPI, Cards, Net Banking)
- Live job tracking (Uploaded → Processing → Queued → Printing → Completed)

### Print Center Dashboard
- View incoming orders sorted by priority
- Heap-based priority queue (urgency + premium + submission time)
- Automatic printer assignment
- Failed job recovery with auto-requeue (up to 3 retries)

### Admin Dashboard
- Analytics: daily/monthly revenue, total prints, active users
- User management: ban/unban, premium toggle
- Payment refunds
- Printer management & health monitoring

### Advanced Features
- **AI Document Analysis**: blank pages, duplicates, orientation detection
- **Cost Optimization**: double-sided savings suggestions
- **Recommendation Engine**: cheapest settings, nearby kiosks, fastest collection
- **Real-time Notifications**: email + in-app

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python, FastAPI, SQLAlchemy, PostgreSQL |
| Queue | Redis (sorted set / heap priority queue) |
| Auth | JWT |
| Frontend | React, Vite, Tailwind CSS, Recharts |
| Cloud | AWS EC2, S3, RDS |
| Payments | Razorpay |
| DevOps | Docker, GitHub Actions |

## Quick Start

### With Docker (recommended)

```bash
docker compose up --build
```

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### Local Development

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Start PostgreSQL and Redis (or use docker compose up postgres redis)
uvicorn app.main:app --reload --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173

## Demo Accounts

| Role | Email | Password |
|------|-------|----------|
| Student | student@demo.com | student123 |
| Print Center | operator@smartprintx.com | operator123 |
| Admin | admin@smartprintx.com | admin12345 |

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/register` | Register student |
| POST | `/api/v1/auth/login` | Login |
| POST | `/api/v1/student/documents/upload` | Upload document |
| POST | `/api/v1/student/estimate` | Calculate cost |
| POST | `/api/v1/student/jobs` | Create print job |
| POST | `/api/v1/student/jobs/{id}/pay` | Create payment order |
| GET | `/api/v1/print-center/jobs` | Incoming orders |
| GET | `/api/v1/print-center/queue` | Priority queue |
| GET | `/api/v1/admin/analytics` | Dashboard analytics |

Full API documentation at `/docs` when the server is running.

## System Design Highlights

- **REST APIs** with role-based access control
- **Database**: normalized schema with users, documents, jobs, payments, printers
- **Caching/Queue**: Redis sorted sets implement a min-heap priority queue
- **Authentication**: JWT access + refresh tokens
- **File Storage**: local dev storage or AWS S3 in production
- **Load Balancing**: stateless FastAPI behind nginx/ALB

## Production Deployment (AWS)

1. **EC2**: Run Docker containers for backend + frontend
2. **RDS**: PostgreSQL managed database
3. **S3**: Document storage (set `USE_LOCAL_STORAGE=false`)
4. **ElastiCache**: Redis for queue (optional, or Redis on EC2)
5. Set environment variables for Razorpay, SMTP, and AWS credentials

## License

MIT
