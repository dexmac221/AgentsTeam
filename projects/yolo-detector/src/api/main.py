"""
FastAPI Main Application for YOLO Object Detector
"""

import asyncio
import json
import time
import logging
from typing import List, Dict, Any, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from ..config.settings import settings, get_cli_config, update_settings, get_model_info
from ..core.detector import YOLODetector, format_detections_for_cli
from ..core.tracker import MultiObjectTracker
from ..core.segmentation import SegmentationProcessor, format_segmentation_for_cli
from ..core.camera import CameraStream, encode_frame_as_jpeg
from .websocket import ConnectionManager, WebSocketHandler

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global components
camera_stream = None
detector = None
tracker = None
segmentation_processor = None
connection_manager = None
websocket_handler = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    # Startup
    logger.info("Starting YOLO Object Detector application")
    
    global camera_stream, detector, tracker, segmentation_processor, connection_manager, websocket_handler
    
    try:
        # Initialize components
        camera_stream = CameraStream(settings.camera_url)
        detector = YOLODetector()
        tracker = MultiObjectTracker()
        segmentation_processor = SegmentationProcessor()
        connection_manager = ConnectionManager()
        websocket_handler = WebSocketHandler(
            camera_stream, detector, tracker, segmentation_processor, connection_manager
        )
        
        # Initialize YOLO models
        await detector.initialize_models()
        
        # Start camera stream
        success = await camera_stream.start_stream()
        if not success:
            logger.warning("Failed to start camera stream, will retry on first request")
        
        logger.info("Application startup complete")
        
        yield
        
    except Exception as e:
        logger.error(f"Startup error: {e}")
        raise
    
    finally:
        # Shutdown
        logger.info("Shutting down application")
        
        if camera_stream:
            camera_stream.stop_stream()
        if detector:
            await detector.shutdown()
        if connection_manager:
            await connection_manager.disconnect_all()
        
        logger.info("Application shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="YOLO Object Detector",
    description="Real-time YOLO object detection with tracking and segmentation",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files and templates
try:
    app.mount("/static", StaticFiles(directory="src/web/static"), name="static")
    templates = Jinja2Templates(directory="src/web/templates")
except Exception as e:
    logger.warning(f"Could not mount static files: {e}")
    templates = None


# Pydantic models
class ConfigUpdate(BaseModel):
    camera_url: Optional[str] = None
    detection_confidence: Optional[float] = None
    iou_threshold: Optional[float] = None
    enable_tracking: Optional[bool] = None
    enable_segmentation: Optional[bool] = None
    model_size: Optional[str] = None
    cli_mode: Optional[bool] = None


class DetectionRequest(BaseModel):
    image_base64: Optional[str] = None
    save_results: bool = False
    return_image: bool = True


# API Routes
@app.get("/")
async def root(request: Request):
    """Main web interface"""
    if templates:
        return templates.TemplateResponse(
            "index.html", 
            {
                "request": request,
                "config": get_cli_config(),
                "model_info": get_model_info()
            }
        )
    else:
        return JSONResponse({
            "message": "YOLO Object Detector API",
            "version": "1.0.0",
            "endpoints": {
                "stream": "/stream",
                "detect": "/detect",
                "config": "/config",
                "stats": "/stats",
                "websocket": "/ws"
            }
        })


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    global camera_stream, detector
    
    status = {
        "status": "healthy",
        "timestamp": time.time(),
        "components": {
            "camera": camera_stream.is_streaming if camera_stream else False,
            "detector": detector.model is not None if detector else False,
            "tracker": tracker is not None,
            "segmentation": segmentation_processor is not None
        }
    }
    
    return status


@app.get("/config")
async def get_config():
    """Get current configuration"""
    config = get_cli_config()
    config["model_info"] = get_model_info()
    return config


@app.post("/config")
async def update_config(config: ConfigUpdate):
    """Update configuration"""
    try:
        # Convert to dict and filter None values
        updates = {k: v for k, v in config.dict().items() if v is not None}
        
        if not updates:
            raise HTTPException(status_code=400, detail="No valid updates provided")
        
        # Apply updates
        update_settings(**updates)
        
        # Handle camera URL change
        if "camera_url" in updates and camera_stream:
            camera_stream.set_stream_url(updates["camera_url"])
        
        logger.info(f"Configuration updated: {updates}")
        
        return {
            "status": "success",
            "updated": updates,
            "new_config": get_cli_config()
        }
        
    except Exception as e:
        logger.error(f"Config update error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/stats")
async def get_stats():
    """Get system statistics"""
    global camera_stream, detector, tracker
    
    stats = {
        "timestamp": time.time(),
        "uptime": time.time() - (camera_stream.stats.get("stream_start_time", time.time()) if camera_stream else time.time()),
        "camera": camera_stream.get_stats() if camera_stream else {},
        "detector": detector.get_stats() if detector else {},
        "tracker": tracker.get_stats() if tracker else {},
        "connections": connection_manager.get_stats() if connection_manager else {}
    }
    
    return stats


@app.get("/models")
async def get_models():
    """Get available models information"""
    return get_model_info()


@app.get("/stream")
async def video_stream():
    """Video stream endpoint"""
    global camera_stream
    
    if not camera_stream or not camera_stream.is_streaming:
        raise HTTPException(status_code=503, detail="Camera stream not available")
    
    async def generate_frames():
        """Generate MJPEG stream"""
        try:
            async for frame in camera_stream.frame_generator():
                if frame is None:
                    continue
                
                # Encode frame as JPEG
                jpeg_bytes = encode_frame_as_jpeg(frame)
                if jpeg_bytes:
                    yield (
                        b'--frame\r\n'
                        b'Content-Type: image/jpeg\r\n\r\n' + jpeg_bytes + b'\r\n'
                    )
                    
                await asyncio.sleep(0.03)  # ~30 FPS
                
        except Exception as e:
            logger.error(f"Stream generation error: {e}")
    
    return StreamingResponse(
        generate_frames(),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )


@app.get("/processed-stream")
async def processed_video_stream():
    """Processed video stream with detections"""
    global camera_stream, detector, tracker, segmentation_processor
    
    if not camera_stream or not camera_stream.is_streaming:
        raise HTTPException(status_code=503, detail="Camera stream not available")
    
    if not detector or not detector.model:
        raise HTTPException(status_code=503, detail="Detector not ready")
    
    async def generate_processed_frames():
        """Generate processed MJPEG stream"""
        try:
            async for frame in camera_stream.frame_generator():
                if frame is None:
                    continue
                
                # Process frame
                result = await detector.detect_frame(frame)
                
                # Apply tracking
                if settings.enable_tracking and tracker:
                    result = tracker.update(result)
                
                # Process segmentation
                if settings.enable_segmentation and segmentation_processor:
                    result = segmentation_processor.process_segmentation_masks(result, frame)
                
                # Draw results on frame
                from ..core.detector import draw_detections
                from ..core.tracker import draw_tracks
                
                processed_frame = draw_detections(frame, result.detections)
                
                if settings.enable_tracking and tracker:
                    active_tracks = tracker.get_active_tracks()
                    trajectories = tracker.get_track_trajectories()
                    processed_frame = draw_tracks(processed_frame, active_tracks, trajectories)
                
                # Apply segmentation overlay
                if settings.enable_segmentation and segmentation_processor:
                    processed_frame = segmentation_processor.apply_masks_to_frame(
                        processed_frame, result.detections
                    )
                
                # Encode frame
                jpeg_bytes = encode_frame_as_jpeg(processed_frame)
                if jpeg_bytes:
                    yield (
                        b'--frame\r\n'
                        b'Content-Type: image/jpeg\r\n\r\n' + jpeg_bytes + b'\r\n'
                    )
                
                await asyncio.sleep(0.03)  # ~30 FPS
                
        except Exception as e:
            logger.error(f"Processed stream generation error: {e}")
    
    return StreamingResponse(
        generate_processed_frames(),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )


@app.post("/detect")
async def detect_objects():
    """Detect objects in current frame"""
    global camera_stream, detector, tracker, segmentation_processor
    
    if not camera_stream or not camera_stream.is_streaming:
        raise HTTPException(status_code=503, detail="Camera stream not available")
    
    if not detector or not detector.model:
        raise HTTPException(status_code=503, detail="Detector not ready")
    
    try:
        # Get current frame
        frame = await camera_stream.get_frame_async()
        if frame is None:
            raise HTTPException(status_code=503, detail="No frame available")
        
        # Process frame
        result = await detector.detect_frame(frame)
        
        # Apply tracking
        if settings.enable_tracking and tracker:
            result = tracker.update(result)
        
        # Process segmentation
        if settings.enable_segmentation and segmentation_processor:
            result = segmentation_processor.process_segmentation_masks(result, frame)
        
        # Format for CLI
        detection_data = format_detections_for_cli(result)
        
        # Add segmentation info
        if settings.enable_segmentation:
            detection_data["segmentation"] = format_segmentation_for_cli(result.detections)
        
        # Add tracking info
        if settings.enable_tracking and tracker:
            detection_data["tracking"] = tracker.get_stats()
        
        return detection_data
        
    except Exception as e:
        logger.error(f"Detection error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Main WebSocket endpoint"""
    global websocket_handler
    
    if websocket_handler:
        await websocket_handler.handle_connection(websocket)
    else:
        await websocket.close(code=1011, reason="WebSocket handler not available")


@app.websocket("/ws/stream")
async def websocket_stream(websocket: WebSocket):
    """WebSocket stream for real-time detection results"""
    await connection_manager.connect(websocket)
    
    try:
        while True:
            # Check if client is still connected
            await websocket.receive_text()  # Ping message
            
    except WebSocketDisconnect:
        connection_manager.disconnect(websocket)


# CLI-specific endpoints
@app.get("/cli/status")
async def cli_status():
    """CLI-optimized status endpoint"""
    global camera_stream, detector, tracker
    
    status = {
        "online": True,
        "camera_connected": camera_stream.is_streaming if camera_stream else False,
        "detector_ready": detector.model is not None if detector else False,
        "current_fps": camera_stream.current_fps if camera_stream else 0.0,
        "detection_count": 0,
        "tracking_enabled": settings.enable_tracking,
        "segmentation_enabled": settings.enable_segmentation
    }
    
    # Get latest detection count
    if detector and camera_stream:
        try:
            frame = await camera_stream.get_frame_async()
            if frame is not None:
                result = await detector.detect_frame(frame)
                status["detection_count"] = len(result.detections)
        except Exception:
            pass
    
    return status


@app.get("/cli/quick-detect")
async def cli_quick_detect():
    """Quick detection for CLI agents"""
    try:
        result = await detect_objects()
        
        # Simplified format for CLI
        return {
            "count": result["detection_count"],
            "objects": [
                {
                    "class": det["class_name"],
                    "confidence": round(det["confidence"], 2),
                    "bbox": [round(x, 1) for x in det["bbox"]],
                    "track_id": det.get("track_id")
                }
                for det in result["detections"][:10]  # Limit to 10 most confident
            ],
            "fps": round(result["fps"], 1),
            "timestamp": result["timestamp"]
        }
        
    except HTTPException:
        return {"count": 0, "objects": [], "fps": 0.0, "error": "Service unavailable"}
    except Exception as e:
        return {"count": 0, "objects": [], "fps": 0.0, "error": str(e)}


if __name__ == "__main__":
    import uvicorn
    
    logger.info(f"Starting YOLO Object Detector on {settings.host}:{settings.port}")
    
    uvicorn.run(
        "src.api.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        access_log=False if settings.log_level == "ERROR" else True
    )