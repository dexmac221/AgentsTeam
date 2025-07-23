"""
WebSocket Handler for Real-time Communication
"""

import asyncio
import json
import time
import logging
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass
import base64

from fastapi import WebSocket, WebSocketDisconnect

from ..config.settings import settings
from ..core.detector import YOLODetector, format_detections_for_cli
from ..core.tracker import MultiObjectTracker
from ..core.segmentation import SegmentationProcessor, format_segmentation_for_cli
from ..core.camera import CameraStream, encode_frame_as_jpeg

logger = logging.getLogger(__name__)


@dataclass
class ClientState:
    """Track individual client state"""
    websocket: WebSocket
    client_id: str
    connected_at: float
    last_ping: float
    subscriptions: Set[str]  # stream, detections, stats
    filters: Dict[str, Any]  # class filters, confidence threshold, etc.
    frame_rate: int = 10  # FPS for this client


class ConnectionManager:
    """Manage WebSocket connections"""
    
    def __init__(self):
        self.clients: Dict[str, ClientState] = {}
        self.next_client_id = 1
        self.stats = {
            "total_connections": 0,
            "current_connections": 0,
            "messages_sent": 0,
            "errors": 0
        }
    
    async def connect(self, websocket: WebSocket) -> str:
        """Accept new WebSocket connection"""
        client_id = f"client_{self.next_client_id}"
        self.next_client_id += 1
        
        await websocket.accept()
        
        client_state = ClientState(
            websocket=websocket,
            client_id=client_id,
            connected_at=time.time(),
            last_ping=time.time(),
            subscriptions={"detections"},  # Default subscription
            filters={}
        )
        
        self.clients[client_id] = client_state
        self.stats["total_connections"] += 1
        self.stats["current_connections"] += 1
        
        logger.info(f"Client {client_id} connected")
        
        # Send welcome message
        await self.send_to_client(client_id, {
            "type": "welcome",
            "client_id": client_id,
            "server_time": time.time(),
            "available_subscriptions": ["stream", "detections", "stats", "config"],
            "default_subscriptions": list(client_state.subscriptions)
        })
        
        return client_id
    
    def disconnect(self, websocket: WebSocket):
        """Handle client disconnection"""
        client_id = None
        for cid, client in self.clients.items():
            if client.websocket == websocket:
                client_id = cid
                break
        
        if client_id:
            del self.clients[client_id]
            self.stats["current_connections"] -= 1
            logger.info(f"Client {client_id} disconnected")
    
    async def send_to_client(self, client_id: str, message: Dict[str, Any]) -> bool:
        """Send message to specific client"""
        if client_id not in self.clients:
            return False
        
        try:
            client = self.clients[client_id]
            await client.websocket.send_text(json.dumps(message))
            self.stats["messages_sent"] += 1
            return True
            
        except Exception as e:
            logger.error(f"Error sending to client {client_id}: {e}")
            self.stats["errors"] += 1
            # Remove disconnected client
            if client_id in self.clients:
                del self.clients[client_id]
                self.stats["current_connections"] -= 1
            return False
    
    async def broadcast(self, message: Dict[str, Any], subscription_filter: str = None):
        """Broadcast message to all or filtered clients"""
        if not self.clients:
            return
        
        disconnect_list = []
        
        for client_id, client in self.clients.items():
            # Check subscription filter
            if subscription_filter and subscription_filter not in client.subscriptions:
                continue
            
            try:
                await client.websocket.send_text(json.dumps(message))
                self.stats["messages_sent"] += 1
                
            except Exception as e:
                logger.error(f"Broadcast error to client {client_id}: {e}")
                disconnect_list.append(client_id)
                self.stats["errors"] += 1
        
        # Clean up disconnected clients
        for client_id in disconnect_list:
            if client_id in self.clients:
                del self.clients[client_id]
                self.stats["current_connections"] -= 1
    
    async def handle_client_message(self, client_id: str, message: str):
        """Handle incoming message from client"""
        try:
            data = json.loads(message)
            message_type = data.get("type")
            
            if message_type == "ping":
                await self._handle_ping(client_id, data)
            elif message_type == "subscribe":
                await self._handle_subscribe(client_id, data)
            elif message_type == "unsubscribe":
                await self._handle_unsubscribe(client_id, data)
            elif message_type == "set_filters":
                await self._handle_set_filters(client_id, data)
            elif message_type == "get_stats":
                await self._handle_get_stats(client_id)
            else:
                await self.send_to_client(client_id, {
                    "type": "error",
                    "message": f"Unknown message type: {message_type}"
                })
                
        except json.JSONDecodeError:
            await self.send_to_client(client_id, {
                "type": "error",
                "message": "Invalid JSON message"
            })
        except Exception as e:
            logger.error(f"Message handling error for client {client_id}: {e}")
            await self.send_to_client(client_id, {
                "type": "error",
                "message": str(e)
            })
    
    async def _handle_ping(self, client_id: str, data: Dict):
        """Handle ping message"""
        if client_id in self.clients:
            self.clients[client_id].last_ping = time.time()
            await self.send_to_client(client_id, {
                "type": "pong",
                "timestamp": time.time()
            })
    
    async def _handle_subscribe(self, client_id: str, data: Dict):
        """Handle subscription request"""
        if client_id not in self.clients:
            return
        
        subscription = data.get("subscription")
        if subscription in ["stream", "detections", "stats", "config"]:
            self.clients[client_id].subscriptions.add(subscription)
            await self.send_to_client(client_id, {
                "type": "subscribed",
                "subscription": subscription
            })
        else:
            await self.send_to_client(client_id, {
                "type": "error",
                "message": f"Invalid subscription: {subscription}"
            })
    
    async def _handle_unsubscribe(self, client_id: str, data: Dict):
        """Handle unsubscription request"""
        if client_id not in self.clients:
            return
        
        subscription = data.get("subscription")
        self.clients[client_id].subscriptions.discard(subscription)
        await self.send_to_client(client_id, {
            "type": "unsubscribed",
            "subscription": subscription
        })
    
    async def _handle_set_filters(self, client_id: str, data: Dict):
        """Handle filter configuration"""
        if client_id not in self.clients:
            return
        
        filters = data.get("filters", {})
        self.clients[client_id].filters = filters
        await self.send_to_client(client_id, {
            "type": "filters_set",
            "filters": filters
        })
    
    async def _handle_get_stats(self, client_id: str):
        """Handle stats request"""
        await self.send_to_client(client_id, {
            "type": "stats",
            "connection_stats": self.get_stats(),
            "timestamp": time.time()
        })
    
    def get_stats(self) -> Dict[str, Any]:
        """Get connection manager statistics"""
        return {
            **self.stats,
            "active_clients": len(self.clients),
            "client_subscriptions": {
                cid: list(client.subscriptions) 
                for cid, client in self.clients.items()
            }
        }
    
    async def disconnect_all(self):
        """Disconnect all clients"""
        disconnect_tasks = []
        for client_id, client in self.clients.items():
            try:
                disconnect_tasks.append(client.websocket.close())
            except Exception:
                pass
        
        if disconnect_tasks:
            await asyncio.gather(*disconnect_tasks, return_exceptions=True)
        
        self.clients.clear()
        self.stats["current_connections"] = 0


class WebSocketHandler:
    """Main WebSocket message handler"""
    
    def __init__(self, camera_stream: CameraStream, detector: YOLODetector,
                 tracker: MultiObjectTracker, segmentation_processor: SegmentationProcessor,
                 connection_manager: ConnectionManager):
        self.camera_stream = camera_stream
        self.detector = detector
        self.tracker = tracker
        self.segmentation_processor = segmentation_processor
        self.connection_manager = connection_manager
        
        # Background tasks
        self.detection_task = None
        self.stats_task = None
        self.is_running = False
    
    async def handle_connection(self, websocket: WebSocket):
        """Handle new WebSocket connection"""
        client_id = await self.connection_manager.connect(websocket)
        
        # Start background tasks if this is the first client
        if not self.is_running:
            self.is_running = True
            self.detection_task = asyncio.create_task(self._detection_loop())
            self.stats_task = asyncio.create_task(self._stats_loop())
        
        try:
            while True:
                # Wait for client messages
                message = await websocket.receive_text()
                await self.connection_manager.handle_client_message(client_id, message)
                
        except WebSocketDisconnect:
            self.connection_manager.disconnect(websocket)
            
            # Stop background tasks if no clients left
            if not self.connection_manager.clients:
                self.is_running = False
                if self.detection_task:
                    self.detection_task.cancel()
                if self.stats_task:
                    self.stats_task.cancel()
    
    async def _detection_loop(self):
        """Background detection loop for WebSocket clients"""
        logger.info("Starting WebSocket detection loop")
        
        while self.is_running and self.connection_manager.clients:
            try:
                if not self.camera_stream or not self.camera_stream.is_streaming:
                    await asyncio.sleep(1.0)
                    continue
                
                # Get current frame
                frame = await self.camera_stream.get_frame_async()
                if frame is None:
                    await asyncio.sleep(0.1)
                    continue
                
                # Run detection
                result = await self.detector.detect_frame(frame)
                
                # Apply tracking if enabled
                if settings.enable_tracking and self.tracker:
                    result = self.tracker.update(result)
                
                # Process segmentation if enabled
                if settings.enable_segmentation and self.segmentation_processor:
                    result = self.segmentation_processor.process_segmentation_masks(result, frame)
                
                # Format results
                detection_data = format_detections_for_cli(result)
                
                # Add additional info
                if settings.enable_segmentation:
                    detection_data["segmentation"] = format_segmentation_for_cli(result.detections)
                
                if settings.enable_tracking and self.tracker:
                    detection_data["tracking"] = self.tracker.get_stats()
                
                # Send to subscribed clients
                await self.connection_manager.broadcast({
                    "type": "detections",
                    "data": detection_data
                }, "detections")
                
                # Send processed frame to stream subscribers
                if any("stream" in client.subscriptions for client in self.connection_manager.clients.values()):
                    # Apply visualizations
                    from ..core.detector import draw_detections
                    from ..core.tracker import draw_tracks
                    
                    processed_frame = draw_detections(frame, result.detections)
                    
                    if settings.enable_tracking and self.tracker:
                        active_tracks = self.tracker.get_active_tracks()
                        trajectories = self.tracker.get_track_trajectories()
                        processed_frame = draw_tracks(processed_frame, active_tracks, trajectories)
                    
                    if settings.enable_segmentation and self.segmentation_processor:
                        processed_frame = self.segmentation_processor.apply_masks_to_frame(
                            processed_frame, result.detections
                        )
                    
                    # Encode as base64
                    jpeg_bytes = encode_frame_as_jpeg(processed_frame)
                    if jpeg_bytes:
                        frame_b64 = base64.b64encode(jpeg_bytes).decode('utf-8')
                        
                        await self.connection_manager.broadcast({
                            "type": "frame",
                            "image": f"data:image/jpeg;base64,{frame_b64}",
                            "timestamp": result.timestamp,
                            "frame_id": result.frame_id
                        }, "stream")
                
                # Rate limiting
                await asyncio.sleep(1.0 / 10)  # 10 FPS for WebSocket
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Detection loop error: {e}")
                await asyncio.sleep(1.0)
        
        logger.info("WebSocket detection loop stopped")
    
    async def _stats_loop(self):
        """Background statistics broadcasting"""
        logger.info("Starting WebSocket stats loop")
        
        while self.is_running and self.connection_manager.clients:
            try:
                # Collect stats
                stats = {
                    "timestamp": time.time(),
                    "camera": self.camera_stream.get_stats() if self.camera_stream else {},
                    "detector": self.detector.get_stats() if self.detector else {},
                    "tracker": self.tracker.get_stats() if self.tracker else {},
                    "connections": self.connection_manager.get_stats(),
                    "settings": {
                        "detection_confidence": settings.detection_confidence,
                        "iou_threshold": settings.iou_threshold,
                        "tracking_enabled": settings.enable_tracking,
                        "segmentation_enabled": settings.enable_segmentation,
                        "mode": settings.mode.value
                    }
                }
                
                # Send to subscribed clients
                await self.connection_manager.broadcast({
                    "type": "stats",
                    "data": stats
                }, "stats")
                
                await asyncio.sleep(5.0)  # Every 5 seconds
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Stats loop error: {e}")
                await asyncio.sleep(5.0)
        
        logger.info("WebSocket stats loop stopped")


# Utility functions for CLI agents
async def send_cli_command(websocket: WebSocket, command: str, **kwargs) -> Dict[str, Any]:
    """Send command through WebSocket and wait for response"""
    message = {
        "type": "cli_command",
        "command": command,
        "params": kwargs,
        "timestamp": time.time()
    }
    
    await websocket.send_text(json.dumps(message))
    response = await websocket.receive_text()
    
    return json.loads(response)


def filter_detections_for_client(detections: List[Dict], client_filters: Dict) -> List[Dict]:
    """Filter detections based on client preferences"""
    if not client_filters:
        return detections
    
    filtered = []
    
    for detection in detections:
        # Class filter
        if "classes" in client_filters:
            if detection["class_name"] not in client_filters["classes"]:
                continue
        
        # Confidence filter
        if "min_confidence" in client_filters:
            if detection["confidence"] < client_filters["min_confidence"]:
                continue
        
        # Area filter
        if "min_area" in client_filters and detection.get("area"):
            if detection["area"] < client_filters["min_area"]:
                continue
        
        filtered.append(detection)
    
    return filtered