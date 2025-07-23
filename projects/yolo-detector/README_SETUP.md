# YOLO Object Detector - Quick Setup Guide

## 🚀 Quick Start

The AgentsTeam has created a comprehensive YOLO object detection system for you. Here's how to get it running:

### 1. Prerequisites Check

```bash
# Check Python version (requires 3.8+)
python --version

# Check if pip is available
pip --version
```

### 2. Install Dependencies

```bash
cd /media/work1/Working/AgentsTeam/projects/yolo-detector

# Install minimal required packages
pip install opencv-python ultralytics torch torchvision fastapi uvicorn requests

# Or install all packages from requirements.txt
pip install -r requirements.txt
```

### 3. Test Basic Setup

```bash
# Run system tests
python simple_detector.py --test

# Create a test image
python simple_detector.py --create-test

# Test detection on image
python simple_detector.py --image test_image.jpg
```

### 4. Camera Connection

If your camera at `http://192.168.1.62:5002` is available:

```bash
# Test camera connection
curl -I http://192.168.1.62:5002

# Start full YOLO detector with camera
python run.py --camera-url http://192.168.1.62:5002
```

### 5. Alternative: Use Webcam

If the network camera is not available:

```bash
# Use local webcam instead
python simple_detector.py --webcam

# Or modify the camera URL to use webcam
python run.py --camera-url 0  # Uses default webcam
```

## 🎯 What You Get

### Object Detection Features
- ✅ Real-time YOLO detection with bounding boxes
- ✅ Object IDs and confidence scores
- ✅ Multi-object tracking with persistent IDs
- ✅ Segmentation masks (if enabled)
- ✅ Web interface at `http://localhost:8000`
- ✅ CLI agent for automation

### CLI Agent Commands

```bash
# Check system health
python src/cli/agent.py health

# Get detection status
python src/cli/agent.py status --format json

# Run continuous monitoring
python src/cli/agent.py monitor --duration 60 --format json

# Configure detection settings
python src/cli/agent.py configure --confidence 0.7 --tracking
```

### Web Interface
- Live video stream with detection overlays
- Real-time control panel for settings
- Performance monitoring and statistics
- Mobile-responsive design

## 🔧 Configuration Options

### Camera Options
```bash
# Different camera sources
python run.py --camera-url http://192.168.1.62:5002  # Network camera
python run.py --camera-url 0                          # Default webcam
python run.py --camera-url 1                          # Second webcam
python run.py --camera-url /path/to/video.mp4         # Video file
```

### Detection Options
```bash
# Model selection (speed vs accuracy)
python run.py --model yolov8n.pt  # Fastest
python run.py --model yolov8s.pt  # Balanced
python run.py --model yolov8m.pt  # Good accuracy
python run.py --model yolov8l.pt  # High accuracy
python run.py --model yolov8x.pt  # Best accuracy

# Confidence threshold
python run.py --confidence 0.3  # More detections
python run.py --confidence 0.7  # Fewer, more confident detections
```

### Feature Toggles
```bash
# Enable/disable features
python run.py --no-tracking        # Disable object tracking
python run.py --no-segmentation    # Disable segmentation masks
python run.py --cli-mode           # CLI-only, no web interface
```

## 🐛 Troubleshooting

### Common Issues

**1. Dependencies Missing**
```bash
pip install opencv-python ultralytics torch torchvision
```

**2. Camera Connection Failed**
```bash
# Test camera manually
curl -I http://192.168.1.62:5002

# Try alternative camera sources
python run.py --camera-url 0  # Use webcam instead
```

**3. Low Performance**
```bash
# Use smaller model
python run.py --model yolov8n.pt

# Disable features
python run.py --no-segmentation --fps 15
```

**4. CUDA Issues**
```bash
# Force CPU usage
python run.py --device cpu
```

## 📊 Expected Performance

| Model | Speed (FPS) | Accuracy | Use Case |
|-------|-------------|----------|----------|
| YOLOv8n | 45+ FPS | Good | Real-time, mobile |
| YOLOv8s | 35+ FPS | Better | Balanced performance |
| YOLOv8m | 25+ FPS | High | Quality applications |
| YOLOv8l | 20+ FPS | Higher | Professional use |
| YOLOv8x | 15+ FPS | Highest | Research/analysis |

## 🎮 Usage Examples

### Basic Detection
```bash
# Start with defaults
python run.py

# Access web interface: http://localhost:8000
```

### High-Precision Mode
```bash
python run.py \
  --model yolov8m.pt \
  --confidence 0.8 \
  --iou 0.3
```

### Agent Automation
```bash
# Monitor for 5 minutes, save results
python src/cli/agent.py monitor \
  --duration 300 \
  --interval 1.0 \
  --format json > detections.json
```

### Custom Configuration
```bash
# Create .env file with settings
echo "YOLO_CAMERA_URL=http://192.168.1.62:5002" > .env
echo "YOLO_DETECTION_CONFIDENCE=0.6" >> .env
echo "YOLO_MODEL_SIZE=yolov8s.pt" >> .env

# Run with custom config
python run.py
```

## 💡 Next Steps

1. **Test the basic setup** with `python simple_detector.py --test`
2. **Create test images** with `python simple_detector.py --create-test`
3. **Start the full system** with `python run.py`
4. **Access the web interface** at http://localhost:8000
5. **Use CLI agent** for automation

The system is designed to be flexible and work with various camera sources. Start with the simple detector to test your setup, then move to the full system for advanced features.