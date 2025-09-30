import os
import json
import glob
import shutil
from typing import List, Optional
from datetime import datetime

def get_latest_detection_file(captured_dir: str = "captured") -> Optional[str]:
    """
    Find the most recent detection result file in the captured directory.
    
    Args:
        captured_dir: Directory containing captured detection results
        
    Returns:
        Path to the most recent JSON file, or None if none found
    """
    if not os.path.exists(captured_dir):
        print(f"Warning: Captured directory '{captured_dir}' not found.")
        return None
    
    # Look for .txt files (yoloDetect.py saves JSON as .txt files)
    txt_files = glob.glob(os.path.join(captured_dir, "capture_*.txt"))
    
    if not txt_files:
        print(f"No detection files found in '{captured_dir}' directory.")
        return None
    
    # Sort by modification time (newest first)
    txt_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
    return txt_files[0]

def read_detected_ingredients(file_path: Optional[str] = None) -> List[str]:
    """
    Read detected ingredients from a detection result file.
    
    Args:
        file_path: Path to the detection file. If None, finds the latest one.
        
    Returns:
        List of detected ingredient names
    """
    if file_path is None:
        file_path = get_latest_detection_file()
    
    if file_path is None:
        print("No detection file found. Using default ingredients.")
        return ["chicken", "banana", "potato"]
    
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        # Extract ingredient names from the JSON structure
        if "Detected Objects" in data and isinstance(data["Detected Objects"], list):
            ingredients = [obj.strip() for obj in data["Detected Objects"] if obj.strip()]
            if ingredients:
                print(f"Detected ingredients from {os.path.basename(file_path)}: {', '.join(ingredients)}")
                return ingredients
            else:
                print("Warning: No ingredients detected in the file. Using default ingredients.")
                return ["chicken", "banana", "potato"]
        else:
            print("Warning: Invalid JSON format in detection file. Using default ingredients.")
            return ["chicken", "banana", "potato"]
            
    except (json.JSONDecodeError, KeyError, IOError) as e:
        print(f"Error reading detection file '{file_path}': {e}. Using default ingredients.")
        return ["chicken", "banana", "potato"]

def cleanup_captured_directory(captured_dir: str = "captured"):
    """
    Clean up the captured directory and all its contents.
    
    Args:
        captured_dir: Directory to clean up
    """
    try:
        if os.path.exists(captured_dir):
            shutil.rmtree(captured_dir)
            print(f"✓ Cleaned up captured directory: {captured_dir}")
        else:
            print(f"Captured directory '{captured_dir}' doesn't exist.")
    except Exception as e:
        print(f"Warning: Could not clean up captured directory: {e}")

def run_yolo_detection(weights_path: str = None, source: str = "0", conf: float = 0.5):
    """
    Run YOLO detection using the yoloDetect.py module.
    
    Args:
        weights_path: Path to model weights (.pt file)
        source: Source for detection (webcam index, image path, etc.)
        conf: Confidence threshold
    """
    print("Starting YOLO detection...")
    print("Press 'P' to capture and detect ingredients")
    print("Press 'Q' to quit detection")
    
    # Import and run yoloDetect
    try:
        from yoloDetect import main as yolo_main
        import sys
        
        # Temporarily modify sys.argv to pass arguments to yoloDetect
        original_argv = sys.argv.copy()
        # Default to project-relative weights if not provided
        default_weights = os.path.join(os.path.dirname(__file__), 'train', 'weights', 'best.pt')
        sys.argv = [
            'yoloDetect.py',
            '--weights', weights_path or default_weights,
            '--source', source,
            '--conf', str(conf)
        ]
        
        # Run YOLO detection
        yolo_main()
        
        # Restore original argv
        sys.argv = original_argv
        
        print("YOLO detection completed.")
        
    except ImportError as e:
        print(f"Error importing yoloDetect: {e}")
        print("Make sure yoloDetect.py is in the same directory.")
    except Exception as e:
        print(f"Error running YOLO detection: {e}")

def get_ingredients_with_detection(use_detection: bool = True, 
                                 weights_path: str = None,
                                 source: str = "0",
                                 conf: float = 0.5) -> List[str]:
    """
    Get ingredients either from YOLO detection or use defaults.
    
    Args:
        use_detection: Whether to run YOLO detection first
        weights_path: Path to YOLO model weights
        source: Source for detection
        conf: Confidence threshold
        
    Returns:
        List of ingredient names
    """
    if use_detection:
        # Run YOLO detection first (do NOT clean up here)
        run_yolo_detection(weights_path, source, conf)
        
        # Wait a moment for files to be written
        import time
        time.sleep(2)
        
        # Read the detected ingredients
        return read_detected_ingredients()
    else:
        # Use default ingredients
        return ["chicken", "banana", "potato"]
