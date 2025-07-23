"""
Advanced Segmentation Processing for YOLO Detector
"""

import cv2
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import logging
from scipy import ndimage
import matplotlib.pyplot as plt
from matplotlib.colors import hsv_to_rgb

from ..config.settings import settings
from .detector import Detection, DetectionResult

logger = logging.getLogger(__name__)


@dataclass
class SegmentationMask:
    """Enhanced segmentation mask with additional properties"""
    mask: np.ndarray
    contours: List[np.ndarray]
    area: float
    perimeter: float
    centroid: Tuple[float, float]
    bounding_rect: Tuple[int, int, int, int]
    color: Tuple[int, int, int]
    alpha: float = 0.3


class SegmentationProcessor:
    """Advanced segmentation processing and visualization"""
    
    def __init__(self):
        self.color_palette = self._generate_color_palette()
        self.mask_cache = {}  # Cache processed masks
        
    def _generate_color_palette(self) -> List[Tuple[int, int, int]]:
        """Generate diverse color palette for different classes"""
        colors = []
        
        # Use HSV color space for better color distribution
        num_colors = 80  # COCO has 80 classes
        for i in range(num_colors):
            hue = i / num_colors
            saturation = 0.7 + 0.3 * (i % 3) / 2  # Vary saturation
            value = 0.8 + 0.2 * (i % 2)  # Vary brightness
            
            rgb = hsv_to_rgb([hue, saturation, value])
            # Convert to BGR for OpenCV
            bgr = (int(rgb[2] * 255), int(rgb[1] * 255), int(rgb[0] * 255))
            colors.append(bgr)
        
        return colors
    
    def process_segmentation_masks(self, detection_result: DetectionResult, 
                                   frame: np.ndarray) -> DetectionResult:
        """Process and enhance segmentation masks"""
        if not settings.enable_segmentation:
            return detection_result
        
        enhanced_detections = []
        
        for detection in detection_result.detections:
            if detection.mask is not None:
                # Process the mask
                enhanced_mask = self._process_single_mask(
                    detection.mask, detection.class_id, frame.shape[:2]
                )
                
                # Create enhanced detection with processed mask
                detection.mask = enhanced_mask.mask
                enhanced_detections.append(detection)
            else:
                enhanced_detections.append(detection)
        
        detection_result.detections = enhanced_detections
        return detection_result
    
    def _process_single_mask(self, mask: np.ndarray, class_id: int, 
                           frame_shape: Tuple[int, int]) -> SegmentationMask:
        """Process a single segmentation mask"""
        # Resize mask to frame dimensions
        if mask.shape != frame_shape:
            mask_resized = cv2.resize(mask, (frame_shape[1], frame_shape[0]))
        else:
            mask_resized = mask.copy()
        
        # Threshold mask
        binary_mask = (mask_resized > 0.5).astype(np.uint8)
        
        # Find contours
        contours, _ = cv2.findContours(
            binary_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )
        
        if not contours:
            # Create empty mask if no contours found
            return SegmentationMask(
                mask=binary_mask,
                contours=[],
                area=0.0,
                perimeter=0.0,
                centroid=(0.0, 0.0),
                bounding_rect=(0, 0, 0, 0),
                color=self.color_palette[class_id % len(self.color_palette)]
            )
        
        # Use largest contour
        largest_contour = max(contours, key=cv2.contourArea)
        
        # Calculate properties
        area = cv2.contourArea(largest_contour)
        perimeter = cv2.arcLength(largest_contour, True)
        
        # Calculate centroid
        moments = cv2.moments(largest_contour)
        if moments['m00'] != 0:
            cx = moments['m10'] / moments['m00']
            cy = moments['m01'] / moments['m00']
            centroid = (cx, cy)
        else:
            centroid = (0.0, 0.0)
        
        # Bounding rectangle
        bounding_rect = cv2.boundingRect(largest_contour)
        
        # Smooth mask using morphological operations
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        binary_mask = cv2.morphologyEx(binary_mask, cv2.MORPH_CLOSE, kernel)
        binary_mask = cv2.morphologyEx(binary_mask, cv2.MORPH_OPEN, kernel)
        
        return SegmentationMask(
            mask=binary_mask,
            contours=[largest_contour],
            area=area,
            perimeter=perimeter,
            centroid=centroid,
            bounding_rect=bounding_rect,
            color=self.color_palette[class_id % len(self.color_palette)],
            alpha=settings.mask_alpha
        )
    
    def apply_masks_to_frame(self, frame: np.ndarray, 
                           detections: List[Detection]) -> np.ndarray:
        """Apply segmentation masks to frame with advanced blending"""
        if not settings.enable_segmentation:
            return frame
        
        result_frame = frame.copy()
        mask_overlay = np.zeros_like(frame)
        
        for detection in detections:
            if detection.mask is None:
                continue
            
            # Get color for this class
            color = self.color_palette[detection.class_id % len(self.color_palette)]
            
            # Create colored mask
            colored_mask = np.zeros_like(frame)
            mask_bool = detection.mask > 0.5
            colored_mask[mask_bool] = color
            
            # Add to overlay
            mask_overlay = cv2.addWeighted(mask_overlay, 1.0, colored_mask, 1.0, 0)
        
        # Blend overlay with original frame
        result_frame = cv2.addWeighted(
            result_frame, 1.0 - settings.mask_alpha, 
            mask_overlay, settings.mask_alpha, 0
        )
        
        return result_frame
    
    def create_mask_only_image(self, frame_shape: Tuple[int, int, int], 
                              detections: List[Detection]) -> np.ndarray:
        """Create image with only segmentation masks"""
        mask_image = np.zeros(frame_shape, dtype=np.uint8)
        
        for detection in detections:
            if detection.mask is None:
                continue
            
            color = self.color_palette[detection.class_id % len(self.color_palette)]
            mask_bool = detection.mask > 0.5
            mask_image[mask_bool] = color
        
        return mask_image
    
    def get_mask_statistics(self, detections: List[Detection]) -> Dict[str, Any]:
        """Get detailed statistics about segmentation masks"""
        stats = {
            "total_masks": 0,
            "total_area": 0.0,
            "average_area": 0.0,
            "masks_by_class": {},
            "area_by_class": {},
            "largest_mask": None,
            "smallest_mask": None
        }
        
        areas = []
        class_counts = {}
        class_areas = {}
        
        for detection in detections:
            if detection.mask is None:
                continue
            
            stats["total_masks"] += 1
            
            # Calculate mask area
            area = np.sum(detection.mask > 0.5)
            areas.append(area)
            stats["total_area"] += area
            
            # Track by class
            class_name = detection.class_name
            if class_name not in class_counts:
                class_counts[class_name] = 0
                class_areas[class_name] = 0.0
            
            class_counts[class_name] += 1
            class_areas[class_name] += area
            
            # Track largest and smallest
            if stats["largest_mask"] is None or area > stats["largest_mask"]["area"]:
                stats["largest_mask"] = {
                    "class": class_name,
                    "area": area,
                    "bbox": detection.bbox
                }
            
            if stats["smallest_mask"] is None or area < stats["smallest_mask"]["area"]:
                stats["smallest_mask"] = {
                    "class": class_name,
                    "area": area,
                    "bbox": detection.bbox
                }
        
        # Calculate averages
        if areas:
            stats["average_area"] = stats["total_area"] / len(areas)
        
        stats["masks_by_class"] = class_counts
        stats["area_by_class"] = class_areas
        
        return stats
    
    def create_segmentation_heatmap(self, frame_shape: Tuple[int, int, int], 
                                   detections: List[Detection]) -> np.ndarray:
        """Create density heatmap from segmentation masks"""
        heatmap = np.zeros(frame_shape[:2], dtype=np.float32)
        
        for detection in detections:
            if detection.mask is None:
                continue
            
            # Add mask to heatmap with confidence weighting
            mask_float = detection.mask.astype(np.float32)
            heatmap += mask_float * detection.confidence
        
        # Normalize heatmap
        if heatmap.max() > 0:
            heatmap = heatmap / heatmap.max()
        
        # Convert to color image
        heatmap_colored = cv2.applyColorMap(
            (heatmap * 255).astype(np.uint8), cv2.COLORMAP_JET
        )
        
        return heatmap_colored
    
    def extract_object_regions(self, frame: np.ndarray, 
                              detections: List[Detection]) -> List[Dict[str, Any]]:
        """Extract individual object regions based on segmentation masks"""
        object_regions = []
        
        for i, detection in enumerate(detections):
            if detection.mask is None:
                continue
            
            # Create mask for this object
            mask_bool = detection.mask > 0.5
            
            # Extract object region
            object_frame = frame.copy()
            object_frame[~mask_bool] = 0  # Zero out background
            
            # Find bounding rectangle of mask
            y_indices, x_indices = np.where(mask_bool)
            if len(y_indices) == 0 or len(x_indices) == 0:
                continue
            
            x_min, x_max = x_indices.min(), x_indices.max()
            y_min, y_max = y_indices.min(), y_indices.max()
            
            # Crop to bounding rectangle
            cropped_object = object_frame[y_min:y_max+1, x_min:x_max+1]
            cropped_mask = detection.mask[y_min:y_max+1, x_min:x_max+1]
            
            object_regions.append({
                "detection_index": i,
                "class_name": detection.class_name,
                "confidence": detection.confidence,
                "object_image": cropped_object,
                "mask": cropped_mask,
                "bbox_in_frame": (x_min, y_min, x_max, y_max),
                "area": np.sum(mask_bool)
            })
        
        return object_regions
    
    def create_segmentation_comparison(self, frame: np.ndarray, 
                                     detections: List[Detection]) -> np.ndarray:
        """Create side-by-side comparison of original and segmented image"""
        height, width = frame.shape[:2]
        
        # Create comparison image
        comparison = np.zeros((height, width * 2, 3), dtype=np.uint8)
        
        # Left side: original frame
        comparison[:, :width] = frame
        
        # Right side: segmentation overlay
        segmented = self.apply_masks_to_frame(frame, detections)
        comparison[:, width:] = segmented
        
        # Add dividing line
        cv2.line(comparison, (width, 0), (width, height), (255, 255, 255), 2)
        
        # Add labels
        cv2.putText(comparison, "Original", (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        cv2.putText(comparison, "Segmented", (width + 10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        
        return comparison
    
    def get_segmentation_summary(self, detections: List[Detection]) -> str:
        """Get human-readable summary of segmentation results"""
        if not detections:
            return "No objects detected"
        
        mask_count = sum(1 for d in detections if d.mask is not None)
        if mask_count == 0:
            return f"Detected {len(detections)} objects but no segmentation masks available"
        
        stats = self.get_mask_statistics(detections)
        
        summary_parts = [
            f"Segmented {mask_count} out of {len(detections)} detected objects",
            f"Total mask area: {stats['total_area']:.0f} pixels",
            f"Average mask area: {stats['average_area']:.0f} pixels"
        ]
        
        if stats['masks_by_class']:
            class_summary = ", ".join([
                f"{count} {class_name}" 
                for class_name, count in stats['masks_by_class'].items()
            ])
            summary_parts.append(f"Classes: {class_summary}")
        
        return "; ".join(summary_parts)


# Utility functions for CLI/agent interaction
def format_segmentation_for_cli(detections: List[Detection]) -> Dict[str, Any]:
    """Format segmentation results for CLI/agent consumption"""
    processor = SegmentationProcessor()
    stats = processor.get_mask_statistics(detections)
    
    return {
        "segmentation_enabled": settings.enable_segmentation,
        "total_masks": stats["total_masks"],
        "total_area": stats["total_area"],
        "average_area": stats["average_area"],
        "masks_by_class": stats["masks_by_class"],
        "area_by_class": stats["area_by_class"],
        "largest_mask": stats["largest_mask"],
        "smallest_mask": stats["smallest_mask"],
        "mask_alpha": settings.mask_alpha,
        "summary": processor.get_segmentation_summary(detections)
    }


def create_segmentation_config_cli() -> Dict[str, Any]:
    """Create CLI-friendly segmentation configuration"""
    return {
        "enabled": settings.enable_segmentation,
        "model": settings.segmentation_model.value,
        "alpha": settings.mask_alpha,
        "colors": settings.mask_colors,
        "available_models": [model.value for model in settings.ModelSize if "seg" in model.value]
    }