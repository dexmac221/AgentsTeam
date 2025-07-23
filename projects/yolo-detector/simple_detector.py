#!/usr/bin/env python3
"""
Simple YOLO Object Detector
Works with webcam, image files, or video streams
"""

import cv2
import argparse
import sys
import time
from pathlib import Path

def test_opencv():
    """Test if OpenCV is available"""
    try:
        import cv2
        print(f"✅ OpenCV available: {cv2.__version__}")
        return True
    except ImportError:
        print("❌ OpenCV not found. Install with: pip install opencv-python")
        return False

def test_yolo():
    """Test if YOLO/Ultralytics is available"""
    try:
        from ultralytics import YOLO
        print("✅ Ultralytics YOLO available")
        return True
    except ImportError:
        print("❌ Ultralytics not found. Install with: pip install ultralytics")
        return False

def simple_webcam_detection():
    """Simple webcam detection"""
    print("Starting webcam detection...")
    
    # Try to load YOLO model
    try:
        from ultralytics import YOLO
        model = YOLO('yolov8n.pt')  # Will download if not present
        print("✅ YOLO model loaded")
    except Exception as e:
        print(f"❌ Failed to load YOLO: {e}")
        return
    
    # Open webcam
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("❌ Cannot open webcam")
        return
    
    print("✅ Webcam opened. Press 'q' to quit")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to read frame")
            break
        
        # Run detection
        results = model(frame, verbose=False)
        
        # Draw results
        annotated_frame = results[0].plot()
        
        # Show frame
        cv2.imshow('YOLO Detection', annotated_frame)
        
        # Print detection info
        detections = results[0].boxes
        if detections is not None and len(detections) > 0:
            print(f"Detected {len(detections)} objects", end='\r')
        
        # Break on 'q' key
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()
    print("\nDetection stopped")

def test_image_detection(image_path):
    """Test detection on a single image"""
    print(f"Testing detection on {image_path}")
    
    try:
        from ultralytics import YOLO
        model = YOLO('yolov8n.pt')
        
        # Load image
        img = cv2.imread(image_path)
        if img is None:
            print(f"❌ Could not load image: {image_path}")
            return
        
        # Run detection
        results = model(img, verbose=False)
        
        # Draw results
        annotated_img = results[0].plot()
        
        # Save result
        output_path = f"detected_{Path(image_path).name}"
        cv2.imwrite(output_path, annotated_img)
        
        # Print results
        detections = results[0].boxes
        if detections is not None:
            print(f"✅ Found {len(detections)} objects")
            print(f"   Result saved to: {output_path}")
            
            # Print object details
            for i, box in enumerate(detections):
                conf = box.conf[0].item()
                cls = int(box.cls[0].item())
                class_name = model.names[cls]
                print(f"   Object {i+1}: {class_name} ({conf:.2f})")
        else:
            print("No objects detected")
            
    except Exception as e:
        print(f"❌ Detection failed: {e}")

def create_test_image():
    """Create a test image with simple shapes"""
    import numpy as np
    
    # Create a test image
    img = np.ones((480, 640, 3), dtype=np.uint8) * 255
    
    # Draw some simple shapes
    cv2.rectangle(img, (50, 50), (200, 150), (0, 255, 0), -1)  # Green rectangle
    cv2.circle(img, (400, 100), 50, (255, 0, 0), -1)  # Blue circle
    cv2.rectangle(img, (300, 200), (500, 350), (0, 0, 255), -1)  # Red rectangle
    
    # Save test image
    test_path = "test_image.jpg"
    cv2.imwrite(test_path, img)
    print(f"✅ Created test image: {test_path}")
    return test_path

def main():
    parser = argparse.ArgumentParser(description="Simple YOLO Object Detector")
    parser.add_argument('--test', action='store_true', help='Run system tests')
    parser.add_argument('--webcam', action='store_true', help='Use webcam for detection')
    parser.add_argument('--image', type=str, help='Process single image')
    parser.add_argument('--create-test', action='store_true', help='Create test image')
    
    args = parser.parse_args()
    
    print("🔍 Simple YOLO Object Detector")
    print("=" * 40)
    
    # Run tests
    if args.test:
        print("Running system tests...")
        opencv_ok = test_opencv()
        yolo_ok = test_yolo()
        
        if not opencv_ok or not yolo_ok:
            print("\n❌ Required dependencies missing")
            print("Install with: pip install opencv-python ultralytics")
            return
        
        print("✅ All tests passed!")
        return
    
    # Create test image
    if args.create_test:
        create_test_image()
        return
    
    # Process single image
    if args.image:
        if not Path(args.image).exists():
            print(f"❌ Image not found: {args.image}")
            return
        test_image_detection(args.image)
        return
    
    # Use webcam
    if args.webcam:
        if not test_opencv() or not test_yolo():
            return
        simple_webcam_detection()
        return
    
    # Default: show help
    print("Usage examples:")
    print("  python simple_detector.py --test          # Run system tests")
    print("  python simple_detector.py --create-test   # Create test image")
    print("  python simple_detector.py --image test_image.jpg  # Process image")
    print("  python simple_detector.py --webcam        # Use webcam")

if __name__ == "__main__":
    main()