# Railway Single Project Deployment Guide

## Architecture Overview

**One Railway project** containing:
- PostgreSQL database
- Redis cache
- MinIO object storage
- Gateway service
- Upload service
- Processor service (Celery worker)
- Reports service

All services communicate internally via service names (e.g., `postgres:5432`, `redis:6379`, `minio:9000`)

---

## Phase 1: Create the Project

1. Go to https://railway.app/dashboard
2. Click **"+ New Project"**
3. Select **"Deploy from GitHub"**
4. Authorize Railway to access GitHub
5. Select your repository
6. Name the project: `architecture-analyzer`
7. Click **"Deploy"**

---

## Phase 2: Add Services to the Project

Once the initial deployment starts, you'll add services one by one.

### Service 1: PostgreSQL Database

1. In your Railway project, click **"+ New"** (top right)
2. Select **"Database"** → **"PostgreSQL"**
3. Railway creates it automatically with:
   - `DATABASE_URL` available as environment variable
   - All services can access it via `postgres:5432`
4. Wait for it to be **"Running"**

### Service 2: Redis Cache

1. Click **"+ New"** again
2. Select **"Database"** → **"Redis"**
3. Railway creates it with:
   - `REDIS_URL` available as environment variable
   - All services access via `redis:6379`
4. Wait for it to be **"Running"**

### Service 3: MinIO Service

1. Click **"+ New"** → **"GitHub Repo"**
2. Select your repository again
3. Configure:
   - **Name**: `minio`
   - **Dockerfile**: `services/minio/Dockerfile`
   - **Start Command**: Leave empty (use Dockerfile default)
   - **Port**: Leave empty (internal communication only)
4. In **Variables** tab, add:
   ```
   MINIO_ROOT_USER=minioadmin
   MINIO_ROOT_PASSWORD=minioadmin
   ```
5. Deploy

### Service 4: Upload Service

1. Click **"+ New"** → **"GitHub Repo"**
2. Select your repository
3. Configure:
   - **Name**: `upload`
   - **Dockerfile**: `services/upload/Dockerfile`
   - **Start Command**: Leave empty (use Dockerfile default)
   - **Port**: Leave empty (internal communication only)
4. In **Variables** tab, add:
   ```
   MINIO_ENDPOINT=minio:9000
   MINIO_ACCESS_KEY=minioadmin
   MINIO_SECRET_KEY=minioadmin
   ```
   (DATABASE_URL and REDIS_URL are auto-provided by Railway)
5. Deploy

### Service 5: Processor Service (Celery Worker)

1. Click **"+ New"** → **"GitHub Repo"**
2. Select your repository
3. Configure:
   - **Name**: `processor`
   - **Dockerfile**: `services/processor/Dockerfile`
   - **Start Command**: Leave empty (use Dockerfile default)
   - **Port**: Leave empty (background worker, no port needed)
4. In **Variables** tab, add:
   ```
   MINIO_ENDPOINT=minio:9000
   MINIO_ACCESS_KEY=minioadmin
   MINIO_SECRET_KEY=minioadmin
   ANTHROPIC_API_KEY=sk-ant-your-actual-anthropic-api-key
   ```
   (DATABASE_URL and REDIS_URL are auto-provided by Railway)
5. Deploy

### Service 6: Reports Service

1. Click **"+ New"** → **"GitHub Repo"**
2. Select your repository
3. Configure:
   - **Name**: `reports`
   - **Dockerfile**: `services/reports/Dockerfile`
   - **Start Command**: Leave empty (use Dockerfile default)
   - **Port**: Leave empty (internal communication only)
4. No extra variables needed (DATABASE_URL and REDIS_URL are auto-provided by Railway)
5. Deploy

### Service 7: Gateway Service (Entry Point)

1. Click **"+ New"** → **"GitHub Repo"**
2. Select your repository
3. Configure:
   - **Name**: `gateway`
   - **Dockerfile**: `services/gateway/Dockerfile`
   - **Start Command**: Leave empty (use Dockerfile default)
   - **Port**: `8080` with **HTTP** (generates public domain like `gateway-xxx.railway.app`)
4. In **Variables** tab, add:
   ```
   UPLOAD_SERVICE_URL=http://upload:8080
   REPORTS_SERVICE_URL=http://reports:8080
   JWT_SECRET=6eb1c23018e715fc8bc37dcdf22f21dab179bfe6dcf5d5358971e0f532cdd513
   ```
5. Deploy

---

## Phase 3: Verify All Services Are Running

1. Go to your Railway project dashboard
2. You should see **7 service cards**:
   - postgres ✅
   - redis ✅
   - minio ✅
   - upload ✅
   - processor ✅
   - reports ✅
   - gateway ✅

3. Each should show **"Running"** or **"Healthy"**
4. Click each one to check **Logs** for errors

---

## Phase 4: Test the Deployment

### Get the Gateway Public URL

1. Click the **gateway** service card
2. At the top, you'll see a URL like: `https://architecture-analyzer-gateway-xxxxx.railway.app`
3. This is your **public API endpoint**

### Test Health Endpoints

```bash
# Test gateway health
curl https://<GATEWAY_URL>/health

# Should return: {"status":"ok","service":"gateway"}
```

### Test Full Upload Flow

```bash
# 1. Upload a test image
curl -X POST https://<GATEWAY_URL>/api/v1/upload \
  -F "file=@test-image.png"

# Response will include: {"id": "analysis-id-xxx"}

# 2. Wait 10-30 seconds for Celery to process

# 3. Retrieve the report
curl https://<GATEWAY_URL>/api/v1/report/analysis-id-xxx
```

---

## Important: Service Communication

**Internal service URLs** (used by services to talk to each other):
- `postgres:5432` - PostgreSQL
- `redis:6379` - Redis
- `minio:9000` - MinIO (S3)
- `upload:8080` - Upload service
- `reports:8080` - Reports service
- `processor` - Celery worker (no port, background)
- `gateway:8080` - Gateway service

These are already set in the service environment variables.

---

## Troubleshooting

### Service won't start
- Click the service → **Logs** tab
- Look for error messages
- Common issues:
  - Wrong Dockerfile path
  - Missing environment variables
  - Port already in use

### Services can't connect to each other
- Verify service names in environment variables match project service names
- Check that services are actually running (status = "Running")
- Restart service: Click service → **Deployments** → redeploy button

### Database/Redis not connecting
- Should auto-connect via `DATABASE_URL` and `REDIS_URL`
- Check these variables are present in service Variables tab
- If missing, Railway will auto-add them

---

## Environment Variables Summary

**Auto-provided by Railway** (DON'T set these - leave blank):
- `DATABASE_URL` - PostgreSQL connection string
- `REDIS_URL` - Redis connection string

**You MUST set these:**

| Service | Variable | Value |
|---------|----------|-------|
| **minio** | `MINIO_ROOT_USER` | `minioadmin` |
| **minio** | `MINIO_ROOT_PASSWORD` | `minioadmin` |
| **upload** | `MINIO_ENDPOINT` | `minio:9000` |
| **upload** | `MINIO_ACCESS_KEY` | `minioadmin` |
| **upload** | `MINIO_SECRET_KEY` | `minioadmin` |
| **processor** | `MINIO_ENDPOINT` | `minio:9000` |
| **processor** | `MINIO_ACCESS_KEY` | `minioadmin` |
| **processor** | `MINIO_SECRET_KEY` | `minioadmin` |
| **processor** | `ANTHROPIC_API_KEY` | `sk-ant-your-actual-key` |
| **gateway** | `UPLOAD_SERVICE_URL` | `http://upload:8080` |
| **gateway** | `REPORTS_SERVICE_URL` | `http://reports:8080` |
| **gateway** | `JWT_SECRET` | `6eb1c23018e715fc8bc37dcdf22f21dab179bfe6dcf5d5358971e0f532cdd513` |

---

## After Successful Deployment

1. Document the **Gateway public URL** - this is your API endpoint
2. Test the full workflow (upload → process → retrieve)
3. Monitor logs for any issues
4. Scale services if needed (via Railway dashboard)
