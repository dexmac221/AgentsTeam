#!/usr/bin/env python3
"""
YOLO Object Detector - Main Entry Point
Run with: python run.py [options]
"""

import argparse
import asyncio
import logging
import sys
import uvicorn
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.config.settings import settings, update_settings
from src.api.main import app


def setup_logging(level: str = "INFO"):
    """Setup logging configuration"""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('yolo_detector.log')
        ]
    )


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="YOLO Object Detector - Real-time detection with tracking and segmentation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Start with default settings
  python run.py
  
  # Start with custom camera URL
  python run.py --camera-url http://192.168.1.62:5002
  
  # Start with specific model and confidence
  python run.py --model yolov8n.pt --confidence 0.3
  
  # Start in CLI mode (no web interface)
  python run.py --cli-mode
  
  # Debug mode with verbose logging
  python run.py --debug --log-level DEBUG
        """
    )
    
    # Server options
    parser.add_argument('--host', default=settings.host, help='Server host')
    parser.add_argument('--port', type=int, default=settings.port, help='Server port')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    
    # Camera options
    parser.add_argument('--camera-url', default=settings.camera_url, help='Camera stream URL')
    parser.add_argument('--camera-timeout', type=int, default=settings.camera_timeout, help='Camera timeout seconds')
    
    # Detection options
    parser.add_argument('--model', default=settings.model_size.value, help='YOLO model size')
    parser.add_argument('--confidence', type=float, default=settings.detection_confidence, help='Detection confidence threshold')
    parser.add_argument('--iou', type=float, default=settings.iou_threshold, help='IoU threshold')
    parser.add_argument('--device', default=settings.device, help='Device (auto, cpu, cuda, mps)')
    
    # Feature toggles
    parser.add_argument('--no-tracking', action='store_true', help='Disable object tracking')
    parser.add_argument('--no-segmentation', action='store_true', help='Disable segmentation')
    parser.add_argument('--cli-mode', action='store_true', help='CLI-only mode (no web interface)')
    
    # Logging
    parser.add_argument('--log-level', default=settings.log_level, 
                       choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'], help='Log level')
    
    # Performance
    parser.add_argument('--workers', type=int, default=settings.max_workers, help='Number of worker threads')
    parser.add_argument('--fps', type=int, default=settings.stream_fps, help='Target FPS')
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.log_level)
    logger = logging.getLogger(__name__)
    
    # Update settings from command line
    config_updates = {
        'host': args.host,
        'port': args.port,
        'debug': args.debug,
        'camera_url': args.camera_url,
        'camera_timeout': args.camera_timeout,
        'model_size': args.model,
        'detection_confidence': args.confidence,
        'iou_threshold': args.iou,
        'device': args.device,
        'enable_tracking': not args.no_tracking,
        'enable_segmentation': not args.no_segmentation,
        'cli_mode': args.cli_mode,
        'log_level': args.log_level,
        'max_workers': args.workers,
        'stream_fps': args.fps
    }
    
    # Apply configuration
    update_settings(**config_updates)
    
    logger.info("=" * 60)
    logger.info("YOLO Object Detector Starting")
    logger.info("=" * 60)
    logger.info(f"Camera URL: {settings.camera_url}")
    logger.info(f"Model: {settings.model_size.value}")
    logger.info(f"Confidence: {settings.detection_confidence}")
    logger.info(f"Device: {settings.device}")
    logger.info(f"Tracking: {settings.enable_tracking}")
    logger.info(f"Segmentation: {settings.enable_segmentation}")
    logger.info(f"CLI Mode: {settings.cli_mode}")
    logger.info("=" * 60)
    
    try:
        if settings.cli_mode:
            # CLI-only mode - start minimal server
            logger.info("Starting in CLI mode...")
            uvicorn.run(
                app,
                host=settings.host,
                port=settings.port,
                log_level=settings.log_level.lower(),
                access_log=False,
                loop="asyncio"
            )
        else:
            # Full web interface mode
            logger.info(f"Starting web server at http://{settings.host}:{settings.port}")
            logger.info("Web interface will be available once server starts")
            
            uvicorn.run(
                app,
                host=settings.host,
                port=settings.port,
                log_level=settings.log_level.lower() if not settings.debug else "debug",
                reload=settings.debug,
                access_log=settings.debug,
                loop="asyncio"
            )
            
    except KeyboardInterrupt:
        logger.info("Shutting down YOLO Object Detector...")
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()