# Railway Deployment Guide

This guide explains how to deploy the async-document-processing-workflow on Railway.

## Services Setup

You need to set up the following services on Railway:

### 1. **PostgreSQL Database**
- Add a new PostgreSQL service
- Railway will automatically set `DATABASE_URL` environment variable
- No additional setup needed

### 2. **Redis Cache**
- Add a new Redis service  
- Railway will automatically set connection credentials
- Used for: celery broker, result backend, and progress tracking

### 3. **Backend Service** (Web)
- Build: Dockerfile at `./backend/Dockerfile`
- Port: Automatically assigned by Railway (uses `$PORT` env var)
- Environment variables needed:
  - `DATABASE_URL` (auto-set by Railway if you link PostgreSQL service)
  - `REDIS_URL` (auto-set by Railway if you link Redis service)
  - `CELERY_BROKER_URL` (auto-set by Railway if you link Redis service)
  - `CELERY_RESULT_BACKEND` (auto-set by Railway if you link Redis service)
  - Standard config variables (see below)

- Optional config variables:
  ```
  DEBUG=false
  API_PREFIX=/api
  ENFORCE_HTTPS=true
  CORS_ORIGINS=["https://yourdomain.com"]
  ALLOWED_HOSTS=["yourdomain.com"]
  ```

### 4. **Celery Worker Service**
- Build: Dockerfile at `./backend/Dockerfile`  
- Start Command: `celery -A app.workers.celery_app.celery_app worker -l info`
- This is a background worker service (not exposed to web)
- Use same environment variables as Backend service

### 5. **Frontend Service** (Optional)
- Build: Dockerfile at `./frontend/Dockerfile`
- Port: Exposed to internet
- Build command: `npm run build`
- Start command: `npm start`

## Key Configuration Steps

1. **Link Services**: When adding environment variables in Railway, you can "Link" services to automatically get their connection URLs
2. **Database Initialization**: The backend will automatically create database tables on startup
3. **CORS Configuration**: Update `CORS_ORIGINS` to include your frontend domain
4. **Health Checks**: Railway will check `/health` endpoint to verify the backend is running

## Troubleshooting

If the backend service keeps crashing:

1. Check logs for database connection errors
2. Make sure PostgreSQL and Redis services are linked
3. Verify environment variables are set correctly
4. Check that PORT environment variable is being used (should be auto-set by Railway)

## Local Testing

To test locally before deploying:

```bash
docker-compose up
```

This uses the local Docker Compose setup that mimics Railway's multi-service environment.
