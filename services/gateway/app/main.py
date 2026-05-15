import httpx
from fastapi import FastAPI, Request

app = FastAPI(title="API Gateway")

UPLOAD_SERVICE = "http://upload:8001"
REPORTS_SERVICE = "http://reports:8002"

@app.post("/api/v1/upload")
async def proxy_upload(request: Request):
    # Forward the incoming request body and headers to the upload service
    body = await request.body()
    headers = {k: v for k, v in request.headers.items()}
    # Ensure host header is not forwarded as-is
    headers.pop("host", None)

    async with httpx.AsyncClient() as client:
        resp = await client.post(f"{UPLOAD_SERVICE}/upload", content=body, headers=headers)
        return resp.json()

@app.get("/api/v1/report/{analysis_id}")
async def proxy_report(analysis_id: str):
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{REPORTS_SERVICE}/reports/{analysis_id}")
        return resp.json()