"""
Camera Stream Handler for YOLO Object Detector
"""

import cv2
import asyncio
import time
import logging
from typing import Optional, Callable, AsyncGenerator
import numpy as np
import httpx
from concurrent.futures import ThreadPoolExecutor
import threading
from collections import deque
import io

from ..config.settings import settings

logger = logging.getLogger(__name__)


class CameraStream:
    """Asynchronous camera stream handler"""
    
    def __init__(self, stream_url: str = None):
        self.stream_url = stream_url or settings.camera_url
        self.cap = None
        self.is_streaming = False
        self.frame_queue = deque(maxlen=settings.max_frame_buffer)
        self.current_frame = None
        self.frame_lock = threading.Lock()
        self.executor = ThreadPoolExecutor(max_workers=2)
        self.stream_thread = None
        self.fps_counter = 0
        self.last_fps_time = time.time()
        self.current_fps = 0.0
        
        # Stream statistics
        self.stats = {
            "total_frames": 0,
            "dropped_frames": 0,
            "connection_attempts": 0,
            "last_frame_time": None,
            "stream_start_time": None,
            "errors": []
        }
    
    async def start_stream(self) -> bool:
        """Start camera stream"""
        if self.is_streaming:
            logger.warning("Stream is already running")
            return True
        
        try:
            logger.info(f"Starting camera stream from {self.stream_url}")
            self.stats["connection_attempts"] += 1
            self.stats["stream_start_time"] = time.time()
            
            # Try to connect to stream
            success = await self._initialize_stream()
            if not success:
                return False
            
            self.is_streaming = True
            
            # Start streaming thread
            self.stream_thread = threading.Thread(target=self._stream_loop, daemon=True)
            self.stream_thread.start()
            
            logger.info("Camera stream started successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start camera stream: {e}")
            self.stats["errors"].append(f"Start stream error: {e}")
            return False
    
    async def _initialize_stream(self) -> bool:
        """Initialize camera stream connection"""
        loop = asyncio.get_event_loop()
        
        try:
            # Try to initialize capture in thread pool
            self.cap = await loop.run_in_executor(
                self.executor, self._create_capture
            )
            
            if self.cap is None or not self.cap.isOpened():
                logger.error("Failed to open camera stream")
                return False
            
            # Set camera properties for better performance
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Reduce buffer size
            self.cap.set(cv2.CAP_PROP_FPS, settings.stream_fps)
            
            # Test read
            ret, frame = self.cap.read()
            if not ret or frame is None:
                logger.error("Failed to read from camera stream")
                return False
            
            logger.info(f"Camera initialized: {frame.shape}")
            return True
            
        except Exception as e:
            logger.error(f"Stream initialization error: {e}")
            self.stats["errors"].append(f"Init error: {e}")
            return False
    
    def _create_capture(self) -> Optional[cv2.VideoCapture]:
        """Create camera capture object (runs in thread pool)"""
        try:
            if self.stream_url.startswith('http'):
                # For HTTP streams
                return cv2.VideoCapture(self.stream_url)
            else:
                # For local cameras or other protocols
                camera_id = int(self.stream_url) if self.stream_url.isdigit() else self.stream_url
                return cv2.VideoCapture(camera_id)
        except Exception as e:
            logger.error(f"Failed to create capture: {e}")
            return None
    
    def _stream_loop(self):
        """Main streaming loop (runs in separate thread)"""
        logger.info("Stream loop started")
        frame_interval = 1.0 / settings.stream_fps
        last_frame_time = 0
        
        while self.is_streaming:
            try:
                current_time = time.time()
                
                # Rate limiting
                if current_time - last_frame_time < frame_interval:
                    time.sleep(0.001)  # Small sleep to prevent busy waiting
                    continue
                
                if self.cap is None or not self.cap.isOpened():
                    logger.warning("Camera disconnected, attempting reconnection...")
                    if not self._reconnect():
                        time.sleep(1.0)  # Wait before retry
                        continue
                
                # Read frame
                ret, frame = self.cap.read()
                if not ret or frame is None:
                    self.stats["dropped_frames"] += 1
                    if self.stats["dropped_frames"] % 100 == 0:
                        logger.warning(f"Dropped frames: {self.stats['dropped_frames']}")
                    continue
                
                # Update frame
                with self.frame_lock:
                    self.current_frame = frame.copy()
                    self.frame_queue.append((current_time, frame))
                    self.stats["total_frames"] += 1
                    self.stats["last_frame_time"] = current_time
                
                # Update FPS
                self._update_fps()
                last_frame_time = current_time
                
            except Exception as e:
                logger.error(f"Stream loop error: {e}")
                self.stats["errors"].append(f"Stream loop error: {e}")
                time.sleep(0.1)  # Brief pause on error
    
    def _reconnect(self) -> bool:
        """Attempt to reconnect to camera stream"""
        try:
            if self.cap:
                self.cap.release()
            
            self.cap = self._create_capture()
            if self.cap and self.cap.isOpened():
                logger.info("Camera reconnected successfully")
                self.stats["connection_attempts"] += 1
                return True
            else:
                logger.error("Failed to reconnect to camera")
                return False
                
        except Exception as e:
            logger.error(f"Reconnection error: {e}")
            self.stats["errors"].append(f"Reconnection error: {e}")
            return False
    
    def _update_fps(self):
        """Update FPS counter"""
        self.fps_counter += 1
        current_time = time.time()
        
        if current_time - self.last_fps_time >= 1.0:
            self.current_fps = self.fps_counter / (current_time - self.last_fps_time)
            self.fps_counter = 0
            self.last_fps_time = current_time
    
    def get_current_frame(self) -> Optional[np.ndarray]:
        """Get the most recent frame"""
        with self.frame_lock:
            return self.current_frame.copy() if self.current_frame is not None else None
    
    def get_frame_with_timestamp(self) -> Optional[tuple]:
        """Get frame with timestamp"""
        with self.frame_lock:
            if self.frame_queue:
                return self.frame_queue[-1]  # Most recent frame
            return None
    
    async def get_frame_async(self) -> Optional[np.ndarray]:
        """Get frame asynchronously"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.executor, self.get_current_frame)
    
    async def frame_generator(self) -> AsyncGenerator[np.ndarray, None]:
        """Async generator for continuous frame stream"""
        last_frame_time = 0
        frame_interval = 1.0 / settings.stream_fps
        
        while self.is_streaming:
            try:
                current_time = time.time()
                
                # Rate limiting
                if current_time - last_frame_time < frame_interval:
                    await asyncio.sleep(0.001)
                    continue
                
                frame = await self.get_frame_async()
                if frame is not None:
                    yield frame
                    last_frame_time = current_time
                else:
                    await asyncio.sleep(0.01)  # Wait if no frame available
                    
            except Exception as e:
                logger.error(f"Frame generator error: {e}")
                await asyncio.sleep(0.1)
    
    def stop_stream(self):
        """Stop camera stream"""
        logger.info("Stopping camera stream")
        self.is_streaming = False
        
        if self.stream_thread and self.stream_thread.is_alive():
            self.stream_thread.join(timeout=2.0)
        
        if self.cap:
            self.cap.release()
            self.cap = None
        
        self.executor.shutdown(wait=False)
        logger.info("Camera stream stopped")
    
    def get_stats(self) -> dict:
        """Get stream statistics"""
        current_time = time.time()
        uptime = current_time - self.stats["stream_start_time"] if self.stats["stream_start_time"] else 0
        
        stats = self.stats.copy()
        stats.update({
            "is_streaming": self.is_streaming,
            "current_fps": self.current_fps,
            "target_fps": settings.stream_fps,
            "uptime_seconds": uptime,
            "frame_queue_size": len(self.frame_queue),
            "has_current_frame": self.current_frame is not None,
            "stream_url": self.stream_url,
            "recent_errors": self.stats["errors"][-5:] if self.stats["errors"] else []
        })
        
        return stats
    
    def set_stream_url(self, url: str):
        """Update stream URL"""
        if url != self.stream_url:
            logger.info(f"Changing stream URL from {self.stream_url} to {url}")
            self.stream_url = url
            
            # Restart stream with new URL
            if self.is_streaming:
                self.stop_stream()
                asyncio.create_task(self.start_stream())


class HTTPStreamReader:
    """HTTP-based stream reader for web cameras"""
    
    def __init__(self, stream_url: str):
        self.stream_url = stream_url
        self.client = None
        self.is_reading = False
    
    async def start(self) -> bool:
        """Start HTTP stream reading"""
        try:
            self.client = httpx.AsyncClient(timeout=settings.camera_timeout)
            
            # Test connection
            response = await self.client.get(self.stream_url)
            if response.status_code == 200:
                logger.info(f"HTTP stream connected: {self.stream_url}")
                self.is_reading = True
                return True
            else:
                logger.error(f"HTTP stream failed: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"HTTP stream start error: {e}")
            return False
    
    async def read_frame(self) -> Optional[np.ndarray]:
        """Read single frame from HTTP stream"""
        if not self.is_reading or not self.client:
            return None
        
        try:
            response = await self.client.get(self.stream_url)
            if response.status_code == 200:
                # Convert response to numpy array
                img_array = np.asarray(bytearray(response.content), dtype=np.uint8)
                frame = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
                return frame
            else:
                logger.warning(f"HTTP frame read failed: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"HTTP frame read error: {e}")
            return None
    
    async def stop(self):
        """Stop HTTP stream reading"""
        self.is_reading = False
        if self.client:
            await self.client.aclose()


# Utility functions
def encode_frame_as_jpeg(frame: np.ndarray, quality: int = 85) -> bytes:
    """Encode frame as JPEG bytes"""
    encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), quality]
    result, encoded_img = cv2.imencode('.jpg', frame, encode_param)
    if result:
        return encoded_img.tobytes()
    else:
        return b''


def create_frame_info(frame: np.ndarray) -> dict:
    """Create frame information dictionary"""
    return {
        "shape": frame.shape,
        "dtype": str(frame.dtype),
        "size_mb": frame.nbytes / (1024 * 1024),
        "channels": frame.shape[2] if len(frame.shape) == 3 else 1,
        "resolution": f"{frame.shape[1]}x{frame.shape[0]}",
        "timestamp": time.time()
    }