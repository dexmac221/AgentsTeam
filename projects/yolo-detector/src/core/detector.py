"""
YOLO Object Detection Core Engine
"""

import cv2
import numpy as np
import asyncio
import time
from typing import Dict, List, Optional, Tuple, Any
from ultralytics import YOLO
from dataclasses import dataclass
import logging
from concurrent.futures import ThreadPoolExecutor
import torch

from ..config.settings import settings, DetectionMode, ModelSize

logger = logging.getLogger(__name__)


@dataclass
class Detection:
    """Single object detection result"""
    bbox: Tuple[float, float, float, float]  # x1, y1, x2, y2
    confidence: float
    class_id: int
    class_name: str
    track_id: Optional[int] = None
    mask: Optional[np.ndarray] = None
    center: Optional[Tuple[float, float]] = None
    area: Optional[float] = None


@dataclass
class DetectionResult:
    """Complete detection result for a frame"""
    frame_id: int
    timestamp: float
    detections: List[Detection]
    frame_shape: Tuple[int, int, int]  # H, W, C
    processing_time: float
    fps: float


class YOLODetector:
    """YOLO detection engine with async support"""
    
    def __init__(self):
        self.model = None
        self.seg_model = None
        self.device = self._get_device()
        self.executor = ThreadPoolExecutor(max_workers=settings.max_workers)
        self.frame_count = 0
        self.fps_tracker = []
        
        # Initialize models
        asyncio.create_task(self.initialize_models())
    
    def _get_device(self) -> str:
        """Determine the best device for inference"""
        if settings.device == "auto":
            if torch.cuda.is_available():
                return "cuda"
            elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
                return "mps"
            else:
                return "cpu"
        return settings.device
    
    async def initialize_models(self):
        """Initialize YOLO models asynchronously"""
        try:
            logger.info(f"Initializing YOLO models on device: {self.device}")
            
            # Load detection model
            loop = asyncio.get_event_loop()
            self.model = await loop.run_in_executor(
                self.executor, 
                self._load_model, 
                settings.model_size.value
            )
            
            # Load segmentation model if needed
            if settings.mode in [DetectionMode.SEGMENTATION, DetectionMode.FULL]:
                self.seg_model = await loop.run_in_executor(
                    self.executor,
                    self._load_model,
                    settings.segmentation_model.value
                )
            
            logger.info("YOLO models initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize YOLO models: {e}")
            raise
    
    def _load_model(self, model_path: str) -> YOLO:
        """Load YOLO model (runs in thread pool)"""
        model = YOLO(model_path)
        model.to(self.device)
        if settings.half_precision and self.device != "cpu":
            model.model.half()
        return model
    
    async def detect_frame(self, frame: np.ndarray) -> DetectionResult:
        """Detect objects in a single frame"""
        start_time = time.time()
        self.frame_count += 1
        
        try:
            # Run detection in thread pool
            loop = asyncio.get_event_loop()
            detections = await loop.run_in_executor(
                self.executor,
                self._process_frame,
                frame
            )
            
            processing_time = time.time() - start_time
            fps = self._calculate_fps(processing_time)
            
            return DetectionResult(
                frame_id=self.frame_count,
                timestamp=time.time(),
                detections=detections,
                frame_shape=frame.shape,
                processing_time=processing_time,
                fps=fps
            )
            
        except Exception as e:
            logger.error(f"Detection failed for frame {self.frame_count}: {e}")
            return DetectionResult(
                frame_id=self.frame_count,
                timestamp=time.time(),
                detections=[],
                frame_shape=frame.shape,
                processing_time=time.time() - start_time,
                fps=0.0
            )
    
    def _process_frame(self, frame: np.ndarray) -> List[Detection]:
        """Process frame for detection (runs in thread pool)"""
        detections = []
        
        if self.model is None:
            logger.warning("YOLO model not initialized")
            return detections
        
        # Run inference
        results = self.model(
            frame,
            conf=settings.detection_confidence,
            iou=settings.iou_threshold,
            max_det=settings.max_detections,
            classes=settings.target_classes if settings.target_classes else None,
            verbose=False
        )
        
        # Process results
        for result in results:
            boxes = result.boxes
            if boxes is None:
                continue
                
            # Process each detection
            for i, box in enumerate(boxes):
                # Extract box coordinates
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                confidence = float(box.conf[0])
                class_id = int(box.cls[0])
                
                # Calculate center and area
                center = ((x1 + x2) / 2, (y1 + y2) / 2)
                area = (x2 - x1) * (y2 - y1)
                
                # Get class name
                class_name = settings.class_names.get(class_id, f"class_{class_id}")
                
                # Get mask if segmentation is enabled
                mask = None
                if (settings.mode in [DetectionMode.SEGMENTATION, DetectionMode.FULL] 
                    and hasattr(result, 'masks') and result.masks is not None):
                    if i < len(result.masks.data):
                        mask = result.masks.data[i].cpu().numpy()
                
                detection = Detection(
                    bbox=(float(x1), float(y1), float(x2), float(y2)),
                    confidence=confidence,
                    class_id=class_id,
                    class_name=class_name,
                    mask=mask,
                    center=center,
                    area=area
                )
                
                detections.append(detection)
        
        return detections
    
    def _calculate_fps(self, processing_time: float) -> float:
        """Calculate current FPS"""
        self.fps_tracker.append(processing_time)
        
        # Keep only last 30 measurements
        if len(self.fps_tracker) > 30:
            self.fps_tracker.pop(0)
        
        # Calculate average FPS
        avg_time = sum(self.fps_tracker) / len(self.fps_tracker)
        return 1.0 / avg_time if avg_time > 0 else 0.0
    
    async def detect_batch(self, frames: List[np.ndarray]) -> List[DetectionResult]:
        """Detect objects in multiple frames"""
        tasks = []
        for frame in frames:
            task = asyncio.create_task(self.detect_frame(frame))
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions
        valid_results = []
        for result in results:
            if isinstance(result, DetectionResult):
                valid_results.append(result)
            else:
                logger.error(f"Batch detection error: {result}")
        
        return valid_results
    
    def get_stats(self) -> Dict[str, Any]:
        """Get detector statistics"""
        return {
            "frame_count": self.frame_count,
            "device": self.device,
            "model": settings.model_size.value,
            "segmentation_model": settings.segmentation_model.value if self.seg_model else None,
            "mode": settings.mode.value,
            "confidence_threshold": settings.detection_confidence,
            "iou_threshold": settings.iou_threshold,
            "current_fps": self.fps_tracker[-1] if self.fps_tracker else 0.0,
            "average_fps": self._calculate_fps(0) if self.fps_tracker else 0.0
        }
    
    async def shutdown(self):
        """Cleanup resources"""
        logger.info("Shutting down YOLO detector")
        self.executor.shutdown(wait=True)
        if self.model:
            del self.model
        if self.seg_model:
            del self.seg_model
        torch.cuda.empty_cache() if torch.cuda.is_available() else None


# Utility functions for visualization
def draw_detections(frame: np.ndarray, detections: List[Detection]) -> np.ndarray:
    """Draw detection results on frame"""
    frame_copy = frame.copy()
    
    for detection in detections:
        x1, y1, x2, y2 = map(int, detection.bbox)
        
        # Draw bounding box
        color = (0, 255, 0)  # Green
        cv2.rectangle(frame_copy, (x1, y1), (x2, y2), color, settings.bbox_thickness)
        
        # Prepare label text
        label_parts = []
        if settings.show_class_names:
            label_parts.append(detection.class_name)
        if settings.show_confidence:
            label_parts.append(f"{detection.confidence:.2f}")
        if settings.show_tracking_id and detection.track_id is not None:
            label_parts.append(f"ID:{detection.track_id}")
        
        label = " | ".join(label_parts)
        
        # Draw label background
        if label:
            (text_width, text_height), _ = cv2.getTextSize(
                label, cv2.FONT_HERSHEY_SIMPLEX, settings.text_size, settings.text_thickness
            )
            
            cv2.rectangle(
                frame_copy,
                (x1, y1 - text_height - 10),
                (x1 + text_width, y1),
                color,
                -1
            )
            
            # Draw label text
            cv2.putText(
                frame_copy,
                label,
                (x1, y1 - 5),
                cv2.FONT_HERSHEY_SIMPLEX,
                settings.text_size,
                (255, 255, 255),
                settings.text_thickness
            )
        
        # Draw mask if available
        if detection.mask is not None and settings.enable_segmentation:
            mask_colored = np.zeros_like(frame_copy)
            mask_resized = cv2.resize(detection.mask, (frame.shape[1], frame.shape[0]))
            mask_bool = mask_resized > 0.5
            
            # Apply color to mask
            mask_colored[mask_bool] = color
            
            # Blend with original frame
            frame_copy = cv2.addWeighted(
                frame_copy, 1.0, mask_colored, settings.mask_alpha, 0
            )
    
    return frame_copy


def format_detections_for_cli(result: DetectionResult) -> Dict[str, Any]:
    """Format detection results for CLI/agent consumption"""
    return {
        "frame_id": result.frame_id,
        "timestamp": result.timestamp,
        "processing_time": result.processing_time,
        "fps": result.fps,
        "detection_count": len(result.detections),
        "detections": [
            {
                "bbox": detection.bbox,
                "confidence": detection.confidence,
                "class_id": detection.class_id,
                "class_name": detection.class_name,
                "track_id": detection.track_id,
                "center": detection.center,
                "area": detection.area
            }
            for detection in result.detections
        ]
    }