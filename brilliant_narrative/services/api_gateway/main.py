from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import httpx

app = FastAPI()

# Service URLs - these would be configurable in a real deployment
CORE_SERVICE_URL = "http://localhost:8001"
QUERY_SERVICE_URL = "http://localhost:8004"

@app.post("/upload/")
async def route_upload(request: Request):
    """
    Routes upload requests to the core_service.
    """
    async with httpx.AsyncClient() as client:
        try:
            # Recreate the form data to stream the file
            form = await request.form()
            files = {'file': (form['file'].filename, form['file'].file, form['file'].content_type)}
            response = await client.post(f"{CORE_SERVICE_URL}/upload/", files=files)
            response.raise_for_status()
            return JSONResponse(content=response.json(), status_code=response.status_code)
        except httpx.RequestError as exc:
            raise HTTPException(status_code=503, detail=f"Service unavailable: {exc}")
        except httpx.HTTPStatusError as exc:
            raise HTTPException(status_code=exc.response.status_code, detail=exc.response.text)


@app.post("/query/")
async def route_query(request: Request):
    """
    Routes query requests to the query_service.
    """
    async with httpx.AsyncClient() as client:
        try:
            data = await request.json()
            response = await client.post(f"{QUERY_SERVICE_URL}/query/", json=data)
            response.raise_for_status()
            return JSONResponse(content=response.json(), status_code=response.status_code)
        except httpx.RequestError as exc:
            raise HTTPException(status_code=503, detail=f"Service unavailable: {exc}")
        except httpx.HTTPStatusError as exc:
            raise HTTPException(status_code=exc.response.status_code, detail=exc.response.text)

if __name__ == "__main__":
    import uvicorn
    # The gateway will be the main entry point for the application
    uvicorn.run(app, host="0.0.0.0", port=80)
