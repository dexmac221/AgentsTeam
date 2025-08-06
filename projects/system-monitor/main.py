import asyncio
import logging
from pathlib import Path

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware

from system_monitor import (
    get_gpu_info,
    get_cpu_info,
    get_memory_info,
    get_disk_info,
    get_network_info,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger("system_monitor_app")

app = FastAPI(title="System Monitor API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).parent
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")

templates = Jinja2Templates(directory=BASE_DIR / "templates")


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """
    Render the main dashboard page.
    """
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/health")
async def health_check():
    """
    Health check endpoint.
    """
    return {"status": "ok"}


@app.get("/metrics")
async def get_metrics():
    """
    Retrieve system metrics as JSON.
    """
    try:
        metrics = {
            "gpu": await get_gpu_info(),
            "cpu": await get_cpu_info(),
            "memory": await get_memory_info(),
            "disk": await get_disk_info(),
            "network": await get_network_info(),
        }
        return metrics
    except Exception as exc:
        logger.exception("Failed to gather metrics")
        raise exc


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time metric updates.
    """
    await websocket.accept()
    try:
        while True:
            metrics = {
                "gpu": await get_gpu_info(),
                "cpu": await get_cpu_info(),
                "memory": await get_memory_info(),
                "disk": await get_disk_info(),
                "network": await get_network_info(),
            }
            await websocket.send_json(metrics)
            await asyncio.sleep(5)  # Update interval
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except Exception as exc:
        logger.exception("Error in WebSocket connection")
        await websocket.close(code=1011)


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """
    Handle unexpected exceptions and return a JSON response.
    """
    logger.exception("Unhandled exception: %s", exc)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error"},
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )