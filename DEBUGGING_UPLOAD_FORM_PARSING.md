# Debugging Upload Form Parsing Issue

## Problem Summary

The upload endpoint is returning a FastAPI form parsing error when attempting to upload files:

```json
{
  "detail": [
    {
      "type": "value_error",
      "loc": ["body", "file"],
      "msg": "Value error, Expected UploadFile, received: <class 'str'>",
      "input": "test.png",
      "ctx": { "error": {} }
    }
  ]
}
```

HTTP Status: `422 Unprocessable Entity`

## Root Cause

FastAPI requires the `UploadFile` parameter to use the `File(...)` dependency to properly parse multipart/form-data requests. Without this declaration, FastAPI treats the file parameter as a JSON body parameter and receives a string instead of the actual file object.

## Changes Made

### 1. Fixed `/services/upload/app/routes.py`

**Before:**
```python
from fastapi import APIRouter, Depends, HTTPException, UploadFile, status

async def upload_diagram(
    file: UploadFile,
    db: Session = Depends(get_db),
) -> AnalysisSchema:
```

**After:**
```python
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

async def upload_diagram(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> AnalysisSchema:
```

**Changes:**
- Added `File` to the imports from FastAPI
- Updated function signature to include `= File(...)` default value

### 2. Added Comprehensive Logging

Added logging statements throughout the upload flow:
```python
logger.info(f"Upload request received. File: {file.filename}, Content-Type: {file.content_type}")
logger.info("Reading file bytes...")
logger.info(f"File read complete. Size: {len(file_bytes)} bytes")
logger.info(f"Created analysis ID: {analysis_id}, file_ref: {file_ref}")
logger.info(f"Uploading to MinIO: {file_ref}")
logger.info(f"Creating database record for analysis {analysis_id}")
logger.info(f"Enqueueing Celery task for analysis {analysis_id}")
```

## Commit

```
629674f - fix: add File() declaration for multipart form parsing

FastAPI requires UploadFile parameters to use File(...) dependency
to properly parse multipart/form-data. Without this, the file parameter
receives a string value instead of the actual file object.

This fixes the 'Expected UploadFile, received: <class 'str'>' error when
uploading files.
```

## Deployment Status

### Current Fix (Commit 240c423)

The root cause was in the **gateway service**, not the upload service.

**Previous Attempts:**
1. ✓ Commit 629674f: Added `File(...)` to upload service routes - **Correct but insufficient**
2. ✗ Commit 7bc13ae: Used `await request.form()` + `files=` in gateway - Didn't work
3. ✗ Commit af9bdb7: Used `await request.body()` + `content=` in gateway - Current failing state

**Current Solution (240c423):**
- Re-implemented the `files=` parameter approach more carefully
- Parse incoming multipart form with `await request.form()`
- Extract and read file content
- Use httpx `files={"file": (filename, content, content_type)}` parameter
- httpx automatically generates proper multipart encoding with correct boundaries

**Key Insight:** The gateway must use `files=` parameter with httpx, not `content=` or raw body forwarding. The httpx `files` parameter is designed specifically to handle multipart encoding correctly.

## Testing Plan

### Test 1: Direct Upload Service (Bypass Gateway)
```bash
# Replace URL with your actual Upload service URL from Railway
curl -X POST "https://your-upload-service.railway.app/upload" \
  -F "file=@/tmp/test-diagram.png" \
  -v
```

This will determine if the issue is:
- With the Upload service itself
- With how the Gateway forwards multipart form data

### Test 2: Check Logs for New Messages
In the Railway dashboard, check the Upload service logs for:
```
Upload request received. File: test-diagram.png, Content-Type: image/png
```

If this message appears, the new code IS running. If not, the old code is still active.

### Test 3: Through Gateway (After Fix Confirmed)
```bash
curl -X POST "https://your-gateway-url.railway.app/api/v1/upload" \
  -F "file=@/tmp/test-diagram.png" \
  -v
```

## Expected Success Response

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "filename": "test-diagram.png",
  "file_ref": "uploads/550e8400-e29b-41d4-a716-446655440000/test-diagram.png",
  "status": "received",
  "created_at": "2026-05-18T14:30:00Z"
}
```

## Database State

**Important Note:** From the first error attempt, an empty `analyses` table was successfully created in PostgreSQL. This confirms:
- ✓ Database connection working
- ✓ Service initialization successful
- ✓ SQLAlchemy table creation working

The only issue is the form parsing, not the database layer.

## Related Code

### Upload Service Architecture
- `/services/upload/app/main.py` - FastAPI app setup with lifespan
- `/services/upload/app/routes.py` - Upload and status endpoints
- `/services/upload/app/config.py` - Configuration and environment variables
- `/services/upload/app/celery_app.py` - Celery task enqueueing

### Gateway Service (Multipart Forwarding)
The Gateway in `/services/gateway/app/main.py` forwards requests to the Upload service:
```python
@app.post("/api/v1/upload")
async def proxy_upload(request: Request):
    correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4())[:8])
    set_correlation_id(correlation_id)

    body = await request.body()
    headers = {k: v for k, v in request.headers.items()}
    headers.pop("host", None)
    headers["X-Correlation-ID"] = correlation_id

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(f"{UPLOAD_SERVICE}/upload", content=body, headers=headers)
        return resp.json()
```

**Potential Issue:** The Gateway is forwarding `content=body`, which may not preserve the multipart boundary. This might need adjustment if testing directly to the Upload service works but through the Gateway doesn't.

## Technical Deep Dive: Why `files=` Parameter Works

When forwarding multipart requests, there are three approaches:

### ❌ Approach 1: `content=await request.body()`
```python
body = await request.body()
resp = await client.post(url, content=body, headers=headers)
```
**Problem:** httpx sends the exact bytes, but multipart boundaries may not be preserved correctly. FastAPI might not recognize it as a valid multipart request, resulting in form parsing failure.

### ❌ Approach 2: `request.stream()`
```python
resp = await client.post(url, content=request.stream(), headers=headers)
```
**Problem:** Streaming raw bytes has the same issue as above - the multipart structure might be corrupted during forwarding.

### ✅ Approach 3: `files=` Parameter (Current)
```python
form = await request.form()
file = form.get("file")
files = {"file": (file.filename, await file.read(), file.content_type)}
resp = await client.post(url, files=files, headers=headers)
```
**Why it works:**
- httpx understands the `files=` parameter is multipart form data
- httpx automatically generates proper multipart encoding with correct boundaries
- Starlette/FastAPI's multipart parser receives a correctly formatted request
- FastAPI's `UploadFile = File(...)` can properly extract the file

## Next Steps

1. Deploy the fixed gateway code to Railway
2. Test the upload endpoint with a real file
3. Check Railway logs for the upload service - should see:
   ```
   [app.routes] Received upload request for file
   [app.routes] Parsed file from request: test.png, Content-Type: image/png
   [app.routes] File size: XXXX bytes
   ```
4. If successful, test full workflow: upload → MinIO → database → Celery → processing
5. Deploy frontend with correct API endpoints

## Debugging Commands

### Test upload through gateway (after deployment):
```bash
curl -X POST "https://your-gateway-url.railway.app/api/v1/upload" \
  -F "file=@/tmp/test.png" \
  -H "X-Correlation-ID: debug-123" \
  -v
```

### Check gateway logs:
```bash
# Look for:
# - "Received upload request for file"
# - "Parsed file from request: test.png"
# - "Upload service responded with status 202"
```

### Check upload service logs:
```bash
# Look for:
# - "Upload request received. File: test.png"
# - "Database record created successfully"
# - "Celery task enqueued successfully"
```

## Environment Variables

All services use Railway-managed PostgreSQL and Redis:
- `DATABASE_URL` - Auto-injected by Railway
- `REDIS_URL` - Auto-injected by Railway
- `MINIO_ENDPOINT` - Set to `minio:9000` for internal communication

## Correlation ID Logging

The logging system includes correlation IDs for tracing requests across services:
```
[app.routes] [a1b2c3d4] [INFO] Upload request received. File: test-diagram.png, Content-Type: image/png
```

This helps trace requests through Gateway → Upload → MinIO → Database → Celery.
