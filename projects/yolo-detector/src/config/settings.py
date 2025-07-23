"""
Configuration settings for YOLO Object Detector
"""

import os
from typing import Dict, List, Optional
from pydantic import BaseSettings, validator
from enum import Enum


class ModelSize(str, Enum):
    """Available YOLO model sizes"""
    NANO = "yolov8n.pt"
    SMALL = "yolov8s.pt" 
    MEDIUM = "yolov8m.pt"
    LARGE = "yolov8l.pt"
    XLARGE = "yolov8x.pt"
    # Segmentation models
    NANO_SEG = "yolov8n-seg.pt"
    SMALL_SEG = "yolov8s-seg.pt"
    MEDIUM_SEG = "yolov8m-seg.pt"
    LARGE_SEG = "yolov8l-seg.pt"
    XLARGE_SEG = "yolov8x-seg.pt"


class DetectionMode(str, Enum):
    """Detection processing modes"""
    DETECTION_ONLY = "detection"
    DETECTION_TRACKING = "tracking"
    SEGMENTATION = "segmentation"
    FULL = "full"  # Detection + Tracking + Segmentation


class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # Camera and Streaming
    camera_url: str = "http://192.168.1.62:5002"
    camera_timeout: int = 10
    stream_fps: int = 30
    max_frame_buffer: int = 10
    
    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False
    
    # YOLO Model Configuration
    model_size: ModelSize = ModelSize.SMALL
    segmentation_model: ModelSize = ModelSize.SMALL_SEG
    detection_confidence: float = 0.5
    iou_threshold: float = 0.45
    max_detections: int = 1000
    
    # Detection Mode
    mode: DetectionMode = DetectionMode.FULL
    
    # Object Tracking
    enable_tracking: bool = True
    tracker_type: str = "bytetrack"  # bytetrack, botsort
    max_age: int = 30
    min_hits: int = 3
    iou_threshold_tracking: float = 0.3
    
    # Segmentation
    enable_segmentation: bool = True
    mask_alpha: float = 0.3
    mask_colors: List[str] = [
        "#FF0000", "#00FF00", "#0000FF", "#FFFF00", "#FF00FF", 
        "#00FFFF", "#800080", "#FFA500", "#FFC0CB", "#A52A2A"
    ]
    
    # Visualization
    bbox_thickness: int = 2
    text_size: float = 0.6
    text_thickness: int = 2
    show_confidence: bool = True
    show_class_names: bool = True
    show_tracking_id: bool = True
    
    # Performance
    device: str = "auto"  # auto, cpu, cuda, mps
    half_precision: bool = False
    batch_size: int = 1
    max_workers: int = 4
    
    # Class Filtering (COCO classes by default, empty means all classes)
    target_classes: List[int] = []  # [0, 1, 2, 3, 5, 7]  # person, bicycle, car, motorcycle, bus, truck
    class_names: Dict[int, str] = {
        0: "person", 1: "bicycle", 2: "car", 3: "motorcycle", 4: "airplane",
        5: "bus", 6: "train", 7: "truck", 8: "boat", 9: "traffic light",
        10: "fire hydrant", 11: "stop sign", 12: "parking meter", 13: "bench",
        14: "bird", 15: "cat", 16: "dog", 17: "horse", 18: "sheep", 19: "cow"
    }
    
    # Agent CLI Configuration
    cli_mode: bool = False
    output_format: str = "json"  # json, yaml, text
    log_level: str = "INFO"
    save_detections: bool = False
    save_images: bool = False
    output_dir: str = "outputs"
    
    # WebSocket Configuration
    max_connections: int = 10
    ping_interval: int = 10
    ping_timeout: int = 5
    
    @validator("detection_confidence")
    def validate_confidence(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError("Detection confidence must be between 0.0 and 1.0")
        return v
    
    @validator("iou_threshold")
    def validate_iou(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError("IoU threshold must be between 0.0 and 1.0")
        return v
    
    @validator("mask_alpha")
    def validate_alpha(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError("Mask alpha must be between 0.0 and 1.0")
        return v
    
    @validator("device")
    def validate_device(cls, v):
        if v not in ["auto", "cpu", "cuda", "mps"]:
            raise ValueError("Device must be one of: auto, cpu, cuda, mps")
        return v
    
    class Config:
        env_file = ".env"
        env_prefix = "YOLO_"


# Global settings instance
settings = Settings()


# Utility functions for CLI agents
def get_cli_config() -> Dict:
    """Get configuration optimized for CLI/agent interaction"""
    return {
        "camera": {
            "url": settings.camera_url,
            "timeout": settings.camera_timeout,
            "fps": settings.stream_fps
        },
        "detection": {
            "model": settings.model_size.value,
            "confidence": settings.detection_confidence,
            "iou_threshold": settings.iou_threshold,
            "mode": settings.mode.value
        },
        "tracking": {
            "enabled": settings.enable_tracking,
            "type": settings.tracker_type,
            "max_age": settings.max_age
        },
        "segmentation": {
            "enabled": settings.enable_segmentation,
            "model": settings.segmentation_model.value,
            "alpha": settings.mask_alpha
        },
        "output": {
            "format": settings.output_format,
            "save_detections": settings.save_detections,
            "save_images": settings.save_images,
            "directory": settings.output_dir
        }
    }


def update_settings(**kwargs) -> None:
    """Update settings dynamically for CLI/agent configuration"""
    global settings
    for key, value in kwargs.items():
        if hasattr(settings, key):
            setattr(settings, key, value)
        else:
            print(f"Warning: Unknown setting '{key}' ignored")


def get_model_info() -> Dict:
    """Get information about available models"""
    return {
        "detection_models": {
            "nano": {"model": ModelSize.NANO, "speed": "fastest", "accuracy": "lowest"},
            "small": {"model": ModelSize.SMALL, "speed": "fast", "accuracy": "good"},
            "medium": {"model": ModelSize.MEDIUM, "speed": "medium", "accuracy": "better"},
            "large": {"model": ModelSize.LARGE, "speed": "slow", "accuracy": "high"},
            "xlarge": {"model": ModelSize.XLARGE, "speed": "slowest", "accuracy": "highest"}
        },
        "segmentation_models": {
            "nano": {"model": ModelSize.NANO_SEG, "speed": "fastest", "accuracy": "lowest"},
            "small": {"model": ModelSize.SMALL_SEG, "speed": "fast", "accuracy": "good"},
            "medium": {"model": ModelSize.MEDIUM_SEG, "speed": "medium", "accuracy": "better"},
            "large": {"model": ModelSize.LARGE_SEG, "speed": "slow", "accuracy": "high"},
            "xlarge": {"model": ModelSize.XLARGE_SEG, "speed": "slowest", "accuracy": "highest"}
        }
    }