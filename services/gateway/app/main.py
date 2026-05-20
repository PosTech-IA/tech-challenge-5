import httpx
from fastapi import FastAPI, Request
from shared.logging import setup_logging, get_logger, get_correlation_id, set_correlation_id
import uuid

setup_logging('gateway')
logger = get_logger(__name__)

app = FastAPI(title="API Gateway")

# Internal service URLs (all use port 8080 in Railway)
UPLOAD_SERVICE = "http://upload:8080"
REPORTS_SERVICE = "http://reports:8080"

@app.on_event("startup")
async def startup():
    logger.info("Gateway service starting up")

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "gateway"}

@app.post("/api/v1/upload")
async def proxy_upload(request: Request):
    correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4())[:8])
    set_correlation_id(correlation_id)

    logger.info(f"Received upload request for file")

    try:
        # Parse incoming multipart form
        form = await request.form()
        file = form.get("file")

        if not file:
            raise ValueError("No file provided in upload request")

        logger.info(f"Parsed file from request: {file.filename}, Content-Type: {file.content_type}")

        # Read file content
        file_content = await file.read()
        logger.info(f"File size: {len(file_content)} bytes")

        # Prepare multipart data for httpx using files parameter
        # This properly reconstructs the multipart request that upload service expects
        files = {"file": (file.filename, file_content, file.content_type)}

        # Only include correlation ID header when forwarding to upload service
        headers = {"X-Correlation-ID": correlation_id}

        async with httpx.AsyncClient(timeout=30.0) as client:
            logger.info(f"Forwarding to upload service: {UPLOAD_SERVICE}/upload")
            resp = await client.post(
                f"{UPLOAD_SERVICE}/upload",
                files=files,
                headers=headers
            )
            logger.info(f"Upload service responded with status {resp.status_code}")
            return resp.json()
    except Exception as e:
        logger.error(f"Error calling upload service: {str(e)}", exc_info=True)
        raise

@app.get("/api/v1/report/{analysis_id}")
async def proxy_report(analysis_id: str):
    correlation_id = get_correlation_id()
    logger.info(f"Retrieving report for analysis: {analysis_id}")

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            logger.info(f"Forwarding to reports service: {REPORTS_SERVICE}/reports/{analysis_id}")
            resp = await client.get(
                f"{REPORTS_SERVICE}/reports/{analysis_id}",
                headers={"X-Correlation-ID": correlation_id}
            )
            logger.info(f"Reports service responded with status {resp.status_code}")
            return resp.json()
    except Exception as e:
        logger.error(f"Error calling reports service: {str(e)}", exc_info=True)
        raise