"""
YOLO Object Detector Package
Real-time object detection, tracking, and segmentation with YOLO
"""

__version__ = "1.0.0"
__author__ = "AgentsTeam"
__description__ = "Real-time YOLO object detection with tracking and segmentation"

from .config.settings import settings
from .core.detector import YOLODetector, Detection, DetectionResult
from .core.tracker import MultiObjectTracker, TrackState
from .core.segmentation import SegmentationProcessor, SegmentationMask
from .core.camera import CameraStream

__all__ = [
    'settings',
    'YOLODetector',
    'Detection', 
    'DetectionResult',
    'MultiObjectTracker',
    'TrackState',
    'SegmentationProcessor',
    'SegmentationMask',
    'CameraStream'
]