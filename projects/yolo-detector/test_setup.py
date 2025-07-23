#!/usr/bin/env python3
"""
Simple test script to verify YOLO detector setup
"""

import sys
import subprocess
import requests
from pathlib import Path

def test_imports():
    """Test basic Python imports"""
    print("Testing imports...")
    try:
        import cv2
        print("✅ OpenCV available")
    except ImportError:
        print("❌ OpenCV not available")
        
    try:
        import torch
        print(f"✅ PyTorch available (version: {torch.__version__})")
        if torch.cuda.is_available():
            print(f"✅ CUDA available: {torch.cuda.get_device_name(0)}")
        else:
            print("⚠️  CUDA not available, will use CPU")
    except ImportError:
        print("❌ PyTorch not available")
        
    try:
        import ultralytics
        print(f"✅ Ultralytics available (version: {ultralytics.__version__})")
    except ImportError:
        print("❌ Ultralytics not available")

def test_camera_connection():
    """Test camera connection"""
    print("\nTesting camera connection...")
    camera_url = "http://192.168.1.62:5002"
    
    try:
        response = requests.get(camera_url, timeout=5, stream=True)
        if response.status_code == 200:
            print(f"✅ Camera accessible at {camera_url}")
            print(f"   Content-Type: {response.headers.get('content-type', 'unknown')}")
            print(f"   Content-Length: {response.headers.get('content-length', 'unknown')}")
        else:
            print(f"⚠️  Camera returned status {response.status_code}")
    except requests.exceptions.ConnectionError:
        print(f"❌ Cannot connect to camera at {camera_url}")
    except requests.exceptions.Timeout:
        print(f"⚠️  Camera connection timed out")
    except Exception as e:
        print(f"❌ Camera test failed: {e}")

def test_yolo_basic():
    """Test basic YOLO functionality"""
    print("\nTesting YOLO basic functionality...")
    try:
        from ultralytics import YOLO
        
        # Try to load a small model
        model = YOLO('yolov8n.pt')  # This will download if not present
        print("✅ YOLO model loaded successfully")
        
        # Try a simple prediction on a test image
        import numpy as np
        test_image = np.random.randint(0, 255, (640, 640, 3), dtype=np.uint8)
        results = model(test_image, verbose=False)
        print("✅ YOLO prediction test passed")
        
    except Exception as e:
        print(f"❌ YOLO test failed: {e}")

def install_minimal_requirements():
    """Install minimal requirements"""
    print("\nInstalling minimal requirements...")
    minimal_reqs = [
        "opencv-python",
        "ultralytics", 
        "torch",
        "torchvision",
        "requests",
        "fastapi",
        "uvicorn",
    ]
    
    for req in minimal_reqs:
        try:
            print(f"Installing {req}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", req], 
                                stdout=subprocess.DEVNULL, 
                                stderr=subprocess.DEVNULL)
            print(f"✅ {req} installed")
        except subprocess.CalledProcessError:
            print(f"❌ Failed to install {req}")

def main():
    print("🚀 YOLO Object Detector Setup Test")
    print("=" * 50)
    
    # Test current setup
    test_imports()
    test_camera_connection()
    
    # Ask to install requirements if needed
    if "--install" in sys.argv:
        install_minimal_requirements()
        print("\nRetesting after installation...")
        test_imports()
        test_yolo_basic()
    
    print("\n" + "=" * 50)
    print("Setup test complete!")
    print("Run with --install to install minimal requirements")

if __name__ == "__main__":
    main()