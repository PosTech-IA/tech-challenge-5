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

    # Forward the incoming request body and headers to the upload service
    body = await request.body()
    headers = {k: v for k, v in request.headers.items()}
    headers.pop("host", None)
    headers["X-Correlation-ID"] = correlation_id

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            logger.info(f"Forwarding to upload service: {UPLOAD_SERVICE}/upload")
            resp = await client.post(f"{UPLOAD_SERVICE}/upload", content=body, headers=headers)
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