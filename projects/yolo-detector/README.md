# YOLO Object Detector with AgentsTeam

A comprehensive real-time YOLO object detection system with camera streaming, multi-object tracking, segmentation capabilities, and AI agent-optimized CLI interface.

## 🎯 Features

### Core Detection
- **YOLOv8 Integration**: Support for all YOLOv8 models (nano to x-large)
- **Real-time Processing**: High-performance async processing pipeline
- **Multiple Detection Modes**: Detection-only, tracking, segmentation, or full mode
- **Confidence Filtering**: Configurable detection thresholds
- **Class Filtering**: Target specific object classes (COCO dataset)

### Object Tracking
- **Multi-Object Tracking**: Kalman filter-based tracking with Hungarian algorithm
- **Unique ID Assignment**: Persistent object IDs across frames
- **Trajectory Storage**: Complete path history for each tracked object
- **Track Lifecycle Management**: Smart track creation, update, and cleanup

### Segmentation
- **Instance Segmentation**: Pixel-level object masks with YOLOv8-seg models
- **Mask Visualization**: Colored overlay with configurable transparency
- **Segmentation Analytics**: Area calculation, contour detection, statistics
- **Multiple Rendering Modes**: Overlay, mask-only, comparison views

### Streaming & Web Interface
- **Dual Stream Support**: Raw camera feed and processed detection stream
- **WebSocket Real-time Updates**: Live detection results and statistics
- **Interactive Dashboard**: Responsive web interface with controls
- **Fullscreen Mode**: Immersive viewing experience
- **Mobile Responsive**: Works on tablets and smartphones

### AI Agent Integration
- **REST API**: Complete HTTP API for programmatic access
- **CLI Agent Tool**: Rich terminal interface with live monitoring
- **Agent-Optimized Endpoints**: Structured data formats for AI agents
- **Batch Processing**: Support for automated analysis workflows
- **Configuration API**: Dynamic settings updates via API

## 🏗️ Project Structure

```
yolo-detector/
├── src/
│   ├── core/                    # Core processing engines
│   │   ├── detector.py          # YOLO detection engine
│   │   ├── tracker.py           # Multi-object tracking system
│   │   ├── segmentation.py      # Segmentation processing
│   │   └── camera.py            # Camera stream handler
│   ├── api/                     # Web API and services
│   │   ├── main.py              # FastAPI application
│   │   └── websocket.py         # WebSocket handlers
│   ├── web/                     # Frontend interface
│   │   ├── templates/           # HTML templates
│   │   └── static/              # CSS/JS/assets
│   ├── cli/                     # Command-line interface
│   │   └── agent.py             # CLI agent for AI interaction
│   └── config/                  # Configuration management
│       └── settings.py          # Settings and validation
├── requirements.txt             # Python dependencies
├── run.py                       # Main application entry point
└── README.md                    # This file
```

## 🚀 Quick Start

### 1. Installation

```bash
# Clone or navigate to project directory
cd /media/work1/Working/AgentsTeam/projects/yolo-detector

# Install dependencies (recommended: use virtual environment)
pip install -r requirements.txt

# Verify installation
python -c "import ultralytics; print('YOLO ready!')"
```

### 2. Basic Usage

```bash
# Start with default settings (camera at http://192.168.1.62:5002)
python run.py

# Custom camera URL
python run.py --camera-url http://your-camera-ip:port

# Specific model and settings
python run.py --model yolov8n.pt --confidence 0.3 --no-segmentation
```

### 3. Access Interfaces

- **Web Interface**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs  
- **Health Check**: http://localhost:8000/health
- **CLI Agent**: Use the built-in CLI commands (see below)

## 🔧 Configuration Options

### Command Line Arguments

```bash
python run.py --help

Options:
  --host HOST              Server host (default: 0.0.0.0)
  --port PORT              Server port (default: 8000)
  --camera-url URL         Camera stream URL
  --model MODEL            YOLO model (yolov8n.pt to yolov8x.pt)
  --confidence FLOAT       Detection confidence threshold (0.1-1.0)
  --iou FLOAT              IoU threshold for NMS (0.1-1.0)
  --device DEVICE          Device (auto, cpu, cuda, mps)
  --no-tracking            Disable object tracking
  --no-segmentation        Disable segmentation
  --cli-mode               CLI-only mode (no web interface)
  --log-level LEVEL        Logging level (DEBUG, INFO, WARNING, ERROR)
  --workers INT            Number of worker threads
  --fps INT                Target FPS for stream processing
```

### Environment Variables

```bash
# Camera configuration
export YOLO_CAMERA_URL="http://192.168.1.62:5002"
export YOLO_CAMERA_TIMEOUT=10

# Detection settings
export YOLO_DETECTION_CONFIDENCE=0.5
export YOLO_IOU_THRESHOLD=0.45
export YOLO_MODEL_SIZE="yolov8s.pt"

# Feature toggles
export YOLO_ENABLE_TRACKING=true
export YOLO_ENABLE_SEGMENTATION=true

# Performance
export YOLO_DEVICE="auto"
export YOLO_MAX_WORKERS=4
export YOLO_STREAM_FPS=30
```

### Configuration File

Create `.env` file in project root:
```bash
YOLO_CAMERA_URL=http://192.168.1.62:5002
YOLO_DETECTION_CONFIDENCE=0.6
YOLO_MODEL_SIZE=yolov8m.pt
YOLO_ENABLE_TRACKING=true
YOLO_ENABLE_SEGMENTATION=true
```

## 🤖 AI Agent CLI Interface

The CLI agent provides AI-optimized commands for automated interaction:

### Installation
```bash
# Make CLI executable
chmod +x src/cli/agent.py

# Add to PATH (optional)
ln -s $(pwd)/src/cli/agent.py /usr/local/bin/yolo-agent
```

### Commands

```bash
# Check system health
python src/cli/agent.py health

# Get current system status
python src/cli/agent.py status --format json

# Get detection results
python src/cli/agent.py detect
python src/cli/agent.py detect --full  # Full details

# Monitor continuously
python src/cli/agent.py monitor --duration 300 --interval 0.5

# Live dashboard
python src/cli/agent.py live --watch

# Configure settings
python src/cli/agent.py configure --confidence 0.7 --tracking

# Get statistics
python src/cli/agent.py stats --format yaml
```

### Output Formats

- `--format table` (default): Human-readable tables
- `--format json`: Structured JSON for processing
- `--format yaml`: YAML format for configuration

### Example Agent Workflow

```bash
#!/bin/bash
# AI Agent automation script

# Check if system is ready
STATUS=$(python src/cli/agent.py health --format json)
if [[ $(echo $STATUS | jq -r '.status') != "healthy" ]]; then
    echo "System not ready"
    exit 1
fi

# Configure for high-precision detection
python src/cli/agent.py configure \
    --confidence 0.8 \
    --iou 0.3 \
    --tracking \
    --segmentation

# Monitor for 60 seconds and save results
python src/cli/agent.py monitor \
    --duration 60 \
    --interval 1.0 \
    --format json > detection_results.json

# Process results with AI model...
python analyze_detections.py detection_results.json
```

## 📡 API Reference

### Health & Status
- `GET /health` - System health check
- `GET /cli/status` - Detailed system status
- `GET /stats` - Performance statistics

### Detection
- `POST /detect` - Single frame detection
- `GET /cli/quick-detect` - Fast detection results
- `GET /stream` - Raw video stream
- `GET /processed-stream` - Detection overlay stream

### Configuration
- `GET /config` - Get current configuration
- `POST /config` - Update configuration
- `GET /models` - Available model information

### WebSocket
- `WS /ws` - Main WebSocket endpoint
- `WS /ws/stream` - Streaming endpoint

### Example API Usage

```python
import httpx
import asyncio

async def get_detections():
    async with httpx.AsyncClient() as client:
        # Get current detections
        response = await client.get('http://localhost:8000/cli/quick-detect')
        return response.json()

# Run detection
results = asyncio.run(get_detections())
print(f"Found {results['count']} objects")
```

## 🎛️ Web Interface Features

### Main Dashboard
- **Live Video Feed**: Real-time camera stream with detection overlays
- **Detection List**: Scrollable list of recent detections with confidence scores
- **System Status**: Real-time status indicators for all components
- **Performance Metrics**: FPS, processing time, detection counts

### Control Panel
- **Detection Settings**: Confidence and IoU threshold sliders
- **Feature Toggles**: Enable/disable tracking and segmentation
- **Model Selection**: Choose YOLO model size (speed vs accuracy)
- **Camera Configuration**: Update camera URL and test connection

### Advanced Features
- **Fullscreen Mode**: Immersive viewing experience
- **Raw/Processed Toggle**: Switch between original and processed feeds
- **Class Filtering**: Show/hide specific object classes
- **Keyboard Shortcuts**: Ctrl+Space (toggle stream), Ctrl+F (fullscreen)

## 🔬 Technical Details

### Performance Optimization
- **Async Processing**: Non-blocking detection pipeline
- **Frame Queue Management**: Configurable buffer size to prevent memory issues
- **Thread Pool Execution**: CPU-intensive tasks in separate threads
- **GPU Acceleration**: Automatic CUDA/MPS detection and usage
- **Model Caching**: Intelligent model loading and memory management

### Tracking Algorithm
- **Kalman Filtering**: Predict object positions between detections
- **Hungarian Algorithm**: Optimal assignment of detections to tracks
- **Track Lifecycle**: Smart creation, update, and cleanup logic
- **Trajectory Storage**: Complete path history with configurable retention

### Segmentation Pipeline
- **YOLOv8-seg Models**: State-of-the-art instance segmentation
- **Mask Post-processing**: Smoothing, contour detection, area calculation
- **Visualization Options**: Multiple rendering modes and color schemes
- **Performance Tuning**: Configurable mask resolution and quality

## 🐛 Troubleshooting

### Common Issues

#### Camera Connection Failed
```bash
# Test camera URL manually
curl -I http://192.168.1.62:5002

# Check network connectivity
ping 192.168.1.62

# Try different camera URL format
python run.py --camera-url http://192.168.1.62:5002/video
```

#### Low FPS Performance
```bash
# Use smaller model for speed
python run.py --model yolov8n.pt

# Disable segmentation
python run.py --no-segmentation

# Reduce target FPS
python run.py --fps 15

# Use CPU if GPU memory issues
python run.py --device cpu
```

#### Memory Issues
```bash
# Reduce worker threads
python run.py --workers 1

# Lower detection limit
# Edit src/config/settings.py: max_detections = 100

# Reduce frame buffer
# Edit src/config/settings.py: max_frame_buffer = 3
```

### Debug Mode
```bash
# Enable debug logging
python run.py --debug --log-level DEBUG

# Check logs
tail -f yolo_detector.log
```

## 📈 Performance Benchmarks

### Model Performance (RTX 3080)
| Model | Speed (FPS) | Accuracy (mAP) | Memory (GB) |
|-------|-------------|----------------|-------------|
| YOLOv8n | 120+ | 37.3 | 1.2 |
| YOLOv8s | 80+ | 44.9 | 2.1 |
| YOLOv8m | 50+ | 50.2 | 4.2 |
| YOLOv8l | 30+ | 52.9 | 6.8 |
| YOLOv8x | 20+ | 53.9 | 8.7 |

### System Requirements
- **Minimum**: 4GB RAM, CPU-only, YOLOv8n
- **Recommended**: 8GB RAM, GTX 1660+, YOLOv8s
- **Optimal**: 16GB RAM, RTX 3080+, YOLOv8m+

## 🤝 Contributing

This project is part of the AgentsTeam ecosystem. Contributions are welcome!

### Development Setup
```bash
# Install development dependencies
pip install -r requirements.txt pytest black flake8

# Run tests
pytest tests/

# Format code
black src/

# Lint code
flake8 src/
```

## 📄 License

This project is part of the AgentsTeam framework. See the main repository for license information.

## 🆘 Support

For issues and support:
1. Check this README for common solutions
2. Review logs in debug mode
3. Check AgentsTeam documentation
4. Open an issue with detailed information

---

**Built with AgentsTeam** - Real-time AI object detection for the future