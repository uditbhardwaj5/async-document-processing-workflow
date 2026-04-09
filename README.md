# async-document-processing-workflow

A production-style full stack application for asynchronous document processing with live progress tracking.

## Tech Stack
- Frontend: Next.js 14 + TypeScript
- Backend: FastAPI (Python)
- Database: PostgreSQL
- Background Jobs: Celery
- Messaging + Progress Events: Redis Pub/Sub
- Orchestration: Docker Compose

## System Architecture
1. User uploads one or more documents from the frontend.
2. FastAPI stores file metadata and document record in PostgreSQL.
3. FastAPI enqueues a Celery background task for each document.
4. Celery worker executes multi-stage processing and publishes progress events to Redis Pub/Sub.
5. Backend exposes SSE endpoint for progress stream.
6. Frontend dashboard polls document list and detail page subscribes to SSE for live event updates.
7. User reviews/edits structured output, finalizes records, and exports finalized data as JSON or CSV.

## Processing Stages
- job_started
- document_parsing_started
- document_parsing_completed
- field_extraction_started
- field_extraction_completed
- final_result_stored
- job_completed
- job_failed

## Folder Structure
- `backend/` FastAPI, Celery worker, models, services, routes
- `frontend/` Next.js client app
- `sample_files/` sample documents for testing
- `sample_exports/` sample exported outputs

## API Surface
- `POST /api/documents/upload` Upload one or more files
- `GET /api/documents` List documents (search/filter/sort/pagination)
- `GET /api/documents/{document_id}` Get document detail
- `GET /api/documents/{document_id}/progress/stream` SSE progress stream
- `POST /api/documents/{document_id}/retry` Retry failed document
- `PATCH /api/documents/{document_id}/review` Save edited reviewed output
- `POST /api/documents/{document_id}/finalize` Finalize completed document
- `GET /api/documents/export/download?format=json|csv&finalized_only=true` Export finalized records
- `GET /health` Health check

## Local Setup (Docker Compose)
1. Copy environment examples:
   - `cp backend/.env.example backend/.env`
   - `cp frontend/.env.example frontend/.env.local`
2. Start services:
   - `docker compose up --build`
3. Open apps:
   - Frontend: http://localhost:3000
   - Backend docs: http://localhost:8000/docs

## Local Setup (Without Docker)
### Backend
1. `cd backend`
2. `python -m venv .venv && source .venv/bin/activate`
3. `pip install -r requirements.txt`
4. Ensure PostgreSQL + Redis are running and env vars are set
5. Start API: `uvicorn app.main:app --reload --port 8000`
6. Start worker: `celery -A app.workers.celery_app.celery_app worker -l info`

### Frontend
1. `cd frontend`
2. `npm install`
3. `npm run dev`

## Production Setup (Docker Compose + Caddy)
1. Create production env file:
   - `cp .env.prod.example .env.prod`
2. Update required values in `.env.prod`:
   - `DOMAIN`
   - `POSTGRES_PASSWORD`
   - `DATABASE_URL`
   - `CORS_ORIGINS`
   - `ALLOWED_HOSTS`
3. Start production stack:
   - `docker compose -f docker-compose.prod.yml --env-file .env.prod up -d --build`
4. Verify services:
   - `docker compose -f docker-compose.prod.yml --env-file .env.prod ps`
   - `curl -fsS http://localhost/health`

### Production Hardening Included
- Backend `DEBUG` defaults to `false`
- Trusted host validation via `ALLOWED_HOSTS`
- Optional HTTPS redirect via `ENFORCE_HTTPS`
- Response compression via `GZIP_MINIMUM_SIZE`
- CORS supports explicit origins and optional regex
- Container health checks and startup ordering in compose files


## Workflow Demo Script
1. Upload files from `sample_files/`.
2. Observe status transitions in dashboard.
3. Open a document detail page and watch live events.
4. Edit reviewed JSON and save.
5. Finalize completed document.
6. Export finalized records to JSON and CSV.


## Assumptions
- Documents are stored on local filesystem (`UPLOAD_DIR`) for this assignment.
- Text parsing is intentionally simple and mock-friendly.
- Authentication is not enabled in this baseline implementation.

## Trade-offs
- SQLAlchemy tables are auto-created on startup (no Alembic migrations in this version).
- Dashboard uses near-real-time polling for list freshness while detail page uses SSE for live event stream.
- Parsing logic is lightweight and deterministic to focus on async architecture.

## Limitations
- No authentication/authorization.
- No object storage abstraction (S3/GCS) yet.
- No cancellation endpoint.
- No full automated test suite in this submission baseline.

## Bonus Features Included
- Docker Compose multi-service setup
- Retry support for failed jobs
- Structured export (JSON and CSV)


## AI Usage Note
This project was developed with AI-assisted support.
