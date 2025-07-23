"""
Multi-Object Tracking System with Trajectory Storage
"""

import numpy as np
import time
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from collections import defaultdict, deque
import logging
from filterpy.kalman import KalmanFilter
from scipy.optimize import linear_sum_assignment
import cv2

from ..config.settings import settings
from .detector import Detection, DetectionResult

logger = logging.getLogger(__name__)


@dataclass
class TrackState:
    """Object tracking state information"""
    track_id: int
    bbox: Tuple[float, float, float, float]
    center: Tuple[float, float]
    velocity: Tuple[float, float]
    confidence: float
    class_id: int
    class_name: str
    age: int  # frames since last detection
    hits: int  # total detection count
    time_since_update: int
    trajectory: deque = field(default_factory=lambda: deque(maxlen=100))
    last_seen: float = field(default_factory=time.time)
    first_seen: float = field(default_factory=time.time)


class KalmanTracker:
    """Kalman filter tracker for single object"""
    
    def __init__(self, bbox: Tuple[float, float, float, float], track_id: int):
        self.track_id = track_id
        self.kf = KalmanFilter(dim_x=8, dim_z=4)
        
        # State vector: [x, y, s, r, dx, dy, ds, dr]
        # where (x,y) is center, s is scale, r is aspect ratio
        # and d* are velocities
        self.kf.F = np.array([
            [1, 0, 0, 0, 1, 0, 0, 0],
            [0, 1, 0, 0, 0, 1, 0, 0],
            [0, 0, 1, 0, 0, 0, 1, 0],
            [0, 0, 0, 1, 0, 0, 0, 1],
            [0, 0, 0, 0, 1, 0, 0, 0],
            [0, 0, 0, 0, 0, 1, 0, 0],
            [0, 0, 0, 0, 0, 0, 1, 0],
            [0, 0, 0, 0, 0, 0, 0, 1]
        ])
        
        self.kf.H = np.array([
            [1, 0, 0, 0, 0, 0, 0, 0],
            [0, 1, 0, 0, 0, 0, 0, 0],
            [0, 0, 1, 0, 0, 0, 0, 0],
            [0, 0, 0, 1, 0, 0, 0, 0]
        ])
        
        # Measurement and process noise
        self.kf.R[2:, 2:] *= 10.0  # measurement noise
        self.kf.P[4:, 4:] *= 1000.0  # initial velocity uncertainty
        self.kf.P *= 10.0  # initial uncertainty
        self.kf.Q[-1, -1] *= 0.01  # process noise
        self.kf.Q[4:, 4:] *= 0.01
        
        # Initialize state
        self.kf.x[:4] = self._bbox_to_state(bbox)
        self.time_since_update = 0
        self.history = []
        
    def _bbox_to_state(self, bbox: Tuple[float, float, float, float]) -> np.ndarray:
        """Convert bounding box to state vector"""
        x1, y1, x2, y2 = bbox
        cx = (x1 + x2) / 2.0
        cy = (y1 + y2) / 2.0
        s = (x2 - x1) * (y2 - y1)  # scale
        r = (x2 - x1) / (y2 - y1)  # aspect ratio
        return np.array([cx, cy, s, r])
    
    def _state_to_bbox(self, state: np.ndarray) -> Tuple[float, float, float, float]:
        """Convert state vector to bounding box"""
        cx, cy, s, r = state
        w = np.sqrt(s * r)
        h = s / w
        x1 = cx - w / 2
        y1 = cy - h / 2
        x2 = cx + w / 2
        y2 = cy + h / 2
        return (float(x1), float(y1), float(x2), float(y2))
    
    def predict(self) -> Tuple[float, float, float, float]:
        """Predict next state and return bounding box"""
        if self.kf.x[2] + self.kf.x[6] <= 0:
            self.kf.x[6] *= 0.0
        self.kf.predict()
        self.time_since_update += 1
        return self._state_to_bbox(self.kf.x[:4])
    
    def update(self, bbox: Tuple[float, float, float, float]):
        """Update tracker with detection"""
        self.time_since_update = 0
        self.history = []
        self.kf.update(self._bbox_to_state(bbox))
    
    def get_state(self) -> Tuple[float, float, float, float]:
        """Get current bounding box estimate"""
        return self._state_to_bbox(self.kf.x[:4])


class MultiObjectTracker:
    """Multi-object tracker using Hungarian algorithm and Kalman filters"""
    
    def __init__(self):
        self.tracks: Dict[int, TrackState] = {}
        self.kalman_trackers: Dict[int, KalmanTracker] = {}
        self.next_id = 1
        self.frame_count = 0
        self.track_history: Dict[int, List] = defaultdict(list)
        
    def update(self, detection_result: DetectionResult) -> DetectionResult:
        """Update tracker with new detections"""
        self.frame_count += 1
        current_time = time.time()
        
        if not detection_result.detections:
            # No detections, just predict existing tracks
            self._predict_existing_tracks()
            self._cleanup_tracks()
            return detection_result
        
        # Predict existing tracks
        predicted_tracks = self._predict_existing_tracks()
        
        # Associate detections with tracks
        matches, unmatched_detections, unmatched_tracks = self._associate(
            detection_result.detections, predicted_tracks
        )
        
        # Update matched tracks
        for match in matches:
            det_idx, track_id = match
            detection = detection_result.detections[det_idx]
            self._update_track(track_id, detection, current_time)
        
        # Create new tracks for unmatched detections
        for det_idx in unmatched_detections:
            detection = detection_result.detections[det_idx]
            self._create_track(detection, current_time)
        
        # Handle unmatched tracks
        for track_id in unmatched_tracks:
            if track_id in self.tracks:
                self.tracks[track_id].time_since_update += 1
                self.tracks[track_id].age += 1
        
        # Clean up old tracks
        self._cleanup_tracks()
        
        # Update detection results with track IDs
        updated_detections = []
        for detection in detection_result.detections:
            # Find track ID for this detection
            track_id = self._find_track_for_detection(detection)
            if track_id:
                detection.track_id = track_id
            updated_detections.append(detection)
        
        detection_result.detections = updated_detections
        return detection_result
    
    def _predict_existing_tracks(self) -> Dict[int, Tuple[float, float, float, float]]:
        """Predict all existing tracks"""
        predictions = {}
        for track_id, kalman_tracker in self.kalman_trackers.items():
            if track_id in self.tracks:
                bbox = kalman_tracker.predict()
                predictions[track_id] = bbox
                
                # Update track position
                track = self.tracks[track_id]
                track.bbox = bbox
                track.center = ((bbox[0] + bbox[2]) / 2, (bbox[1] + bbox[3]) / 2)
                
                # Calculate velocity
                if len(track.trajectory) > 1:
                    prev_center = track.trajectory[-1][1:3]
                    track.velocity = (
                        track.center[0] - prev_center[0],
                        track.center[1] - prev_center[1]
                    )
                
        return predictions
    
    def _associate(self, detections: List[Detection], 
                   predictions: Dict[int, Tuple[float, float, float, float]]) -> Tuple[List, List, List]:
        """Associate detections with tracks using Hungarian algorithm"""
        if not detections or not predictions:
            return [], list(range(len(detections))), list(predictions.keys())
        
        # Calculate IoU matrix
        iou_matrix = np.zeros((len(detections), len(predictions)), dtype=np.float32)
        track_ids = list(predictions.keys())
        
        for d, detection in enumerate(detections):
            for t, track_id in enumerate(track_ids):
                predicted_bbox = predictions[track_id]
                iou = self._calculate_iou(detection.bbox, predicted_bbox)
                iou_matrix[d, t] = iou
        
        # Use Hungarian algorithm for assignment
        matched_indices = linear_sum_assignment(-iou_matrix)
        matches = []
        
        for d, t in zip(matched_indices[0], matched_indices[1]):
            if iou_matrix[d, t] >= settings.iou_threshold_tracking:
                matches.append((d, track_ids[t]))
        
        # Find unmatched detections and tracks
        unmatched_detections = []
        for d in range(len(detections)):
            if d not in matched_indices[0] or not any(
                iou_matrix[d, t] >= settings.iou_threshold_tracking 
                for t in matched_indices[1][matched_indices[0] == d]
            ):
                unmatched_detections.append(d)
        
        unmatched_tracks = []
        for t, track_id in enumerate(track_ids):
            if t not in matched_indices[1] or not any(
                iou_matrix[d, t] >= settings.iou_threshold_tracking 
                for d in matched_indices[0][matched_indices[1] == t]
            ):
                unmatched_tracks.append(track_id)
        
        return matches, unmatched_detections, unmatched_tracks
    
    def _calculate_iou(self, bbox1: Tuple[float, float, float, float], 
                       bbox2: Tuple[float, float, float, float]) -> float:
        """Calculate Intersection over Union"""
        x1_1, y1_1, x2_1, y2_1 = bbox1
        x1_2, y1_2, x2_2, y2_2 = bbox2
        
        # Calculate intersection
        x1_i = max(x1_1, x1_2)
        y1_i = max(y1_1, y1_2)
        x2_i = min(x2_1, x2_2)
        y2_i = min(y2_1, y2_2)
        
        if x2_i <= x1_i or y2_i <= y1_i:
            return 0.0
        
        intersection = (x2_i - x1_i) * (y2_i - y1_i)
        
        # Calculate union
        area1 = (x2_1 - x1_1) * (y2_1 - y1_1)
        area2 = (x2_2 - x1_2) * (y2_2 - y1_2)
        union = area1 + area2 - intersection
        
        return intersection / union if union > 0 else 0.0
    
    def _update_track(self, track_id: int, detection: Detection, current_time: float):
        """Update existing track with new detection"""
        if track_id not in self.tracks:
            return
        
        track = self.tracks[track_id]
        kalman_tracker = self.kalman_trackers[track_id]
        
        # Update Kalman filter
        kalman_tracker.update(detection.bbox)
        
        # Update track state
        track.bbox = detection.bbox
        track.center = detection.center
        track.confidence = detection.confidence
        track.class_id = detection.class_id
        track.class_name = detection.class_name
        track.hits += 1
        track.time_since_update = 0
        track.last_seen = current_time
        
        # Add to trajectory
        track.trajectory.append((current_time, detection.center[0], detection.center[1]))
        
        # Store in history
        self.track_history[track_id].append({
            "frame": self.frame_count,
            "timestamp": current_time,
            "bbox": detection.bbox,
            "center": detection.center,
            "confidence": detection.confidence,
            "class_name": detection.class_name
        })
    
    def _create_track(self, detection: Detection, current_time: float):
        """Create new track from detection"""
        track_id = self.next_id
        self.next_id += 1
        
        # Create track state
        track = TrackState(
            track_id=track_id,
            bbox=detection.bbox,
            center=detection.center,
            velocity=(0.0, 0.0),
            confidence=detection.confidence,
            class_id=detection.class_id,
            class_name=detection.class_name,
            age=1,
            hits=1,
            time_since_update=0,
            first_seen=current_time,
            last_seen=current_time
        )
        
        track.trajectory.append((current_time, detection.center[0], detection.center[1]))
        self.tracks[track_id] = track
        
        # Create Kalman tracker
        self.kalman_trackers[track_id] = KalmanTracker(detection.bbox, track_id)
        
        logger.debug(f"Created new track {track_id} for {detection.class_name}")
    
    def _find_track_for_detection(self, detection: Detection) -> Optional[int]:
        """Find the track ID that best matches this detection"""
        best_iou = 0.0
        best_track_id = None
        
        for track_id, track in self.tracks.items():
            if (track.time_since_update == 0 and  # Recently updated
                track.class_id == detection.class_id):  # Same class
                iou = self._calculate_iou(detection.bbox, track.bbox)
                if iou > best_iou and iou >= settings.iou_threshold_tracking:
                    best_iou = iou
                    best_track_id = track_id
        
        return best_track_id
    
    def _cleanup_tracks(self):
        """Remove old or invalid tracks"""
        tracks_to_remove = []
        
        for track_id, track in self.tracks.items():
            # Remove tracks that haven't been seen for too long
            if track.time_since_update >= settings.max_age:
                tracks_to_remove.append(track_id)
            # Remove tracks with too few hits initially
            elif track.age < settings.min_hits and track.time_since_update > 1:
                tracks_to_remove.append(track_id)
        
        for track_id in tracks_to_remove:
            if track_id in self.tracks:
                logger.debug(f"Removing track {track_id}")
                del self.tracks[track_id]
            if track_id in self.kalman_trackers:
                del self.kalman_trackers[track_id]
    
    def get_active_tracks(self) -> Dict[int, TrackState]:
        """Get all currently active tracks"""
        return {
            track_id: track for track_id, track in self.tracks.items()
            if track.time_since_update < 3  # Recently seen
        }
    
    def get_track_trajectories(self) -> Dict[int, List[Tuple[float, float, float]]]:
        """Get trajectories for all tracks"""
        trajectories = {}
        for track_id, track in self.tracks.items():
            if len(track.trajectory) > 1:
                trajectories[track_id] = list(track.trajectory)
        return trajectories
    
    def get_stats(self) -> Dict[str, Any]:
        """Get tracking statistics"""
        active_tracks = self.get_active_tracks()
        return {
            "total_tracks": len(self.tracks),
            "active_tracks": len(active_tracks),
            "next_id": self.next_id,
            "frame_count": self.frame_count,
            "tracks_by_class": self._get_tracks_by_class(active_tracks),
            "average_track_age": np.mean([track.age for track in active_tracks.values()]) if active_tracks else 0,
            "longest_trajectory": max([len(track.trajectory) for track in self.tracks.values()]) if self.tracks else 0
        }
    
    def _get_tracks_by_class(self, tracks: Dict[int, TrackState]) -> Dict[str, int]:
        """Count tracks by class"""
        class_counts = defaultdict(int)
        for track in tracks.values():
            class_counts[track.class_name] += 1
        return dict(class_counts)


def draw_tracks(frame: np.ndarray, tracks: Dict[int, TrackState], 
                trajectories: Dict[int, List[Tuple[float, float, float]]] = None) -> np.ndarray:
    """Draw tracking results on frame"""
    frame_copy = frame.copy()
    
    # Colors for different tracks
    colors = [
        (255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), (255, 0, 255),
        (0, 255, 255), (128, 0, 128), (255, 165, 0), (255, 192, 203), (165, 42, 42)
    ]
    
    for track_id, track in tracks.items():
        color = colors[track_id % len(colors)]
        x1, y1, x2, y2 = map(int, track.bbox)
        
        # Draw bounding box
        cv2.rectangle(frame_copy, (x1, y1), (x2, y2), color, 2)
        
        # Draw center point
        center = tuple(map(int, track.center))
        cv2.circle(frame_copy, center, 3, color, -1)
        
        # Draw track ID
        label = f"ID:{track_id}"
        cv2.putText(frame_copy, label, (x1, y1 - 10), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
        
        # Draw trajectory
        if trajectories and track_id in trajectories:
            trajectory = trajectories[track_id]
            if len(trajectory) > 1:
                points = [(int(x), int(y)) for _, x, y in trajectory]
                for i in range(1, len(points)):
                    cv2.line(frame_copy, points[i-1], points[i], color, 2)
    
    return frame_copy