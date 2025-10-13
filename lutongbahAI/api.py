# MERGE NOTE: Combined imports from both files.
# Added render_template for the new index route.
# Added ingredient_integration and atexit for the new features.
from flask import Flask, jsonify, make_response, request, render_template, Response
from flask_cors import CORS
from llm_utils import generate_recipes, get_recipe_steps, clear_cache, get_cache_stats
from ingredient_integration import read_detected_ingredients, cleanup_captured_directory
import time
import logging
from functools import wraps
import sys
import atexit
import os
import cv2
import torch
import numpy as np
from typing import Optional, List, Dict

# Helper: load class names from classes.txt and map to indices
def load_class_names(txt_path: str):
    try:
        with open(txt_path, "r", encoding="utf-8") as f:
            names = [line.strip() for line in f if line.strip()]
        return {i: name for i, name in enumerate(names)}
    except Exception:
        return {}

# --- Basic Setup (From your API) ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Point Flask to the 'dist' folder for a unified server
dist_folder = os.path.join(os.path.dirname(__file__), '..', 'dist')
app = Flask(__name__, template_folder=dist_folder, static_folder=os.path.join(dist_folder, 'assets'))
CORS(app)

# --- App Setup ---
clear_cache()
atexit.register(cleanup_captured_directory)
logger.info("Registered cleanup function for captured ingredients directory.")

# ======================================================================
# CHANGE 1: Create a shared set to store detected ingredients
# A 'set' is used to automatically store only unique ingredient names.
# ======================================================================
latest_detected_ingredients = set()

# --- Video source opener (robust across Windows backends) ---
def _make_cap(idx: int, api: Optional[int]):
    try:
        if api is None:
            return cv2.VideoCapture(idx)
        return cv2.VideoCapture(idx, api)
    except Exception:
        return None

def open_video_capture(source: Optional[str] = None, backend: Optional[str] = None,
                       width: Optional[int] = 640, height: Optional[int] = 480):
    """Try to open a video capture device robustly on Windows.

    Tries DirectShow first (more reliable on some Windows setups), then MSMF, then default.
    Accepts numeric indices as strings (e.g., "0", "1").
    """
    candidates = []
    # Normalize source to int index when possible
    idx: Optional[int] = None
    if source is None:
        idx = 0
    else:
        try:
            idx = int(source)
        except Exception:
            idx = 0

    # Map backend string to OpenCV API flag
    api_order: List[Optional[int]]
    if backend:
        b = backend.strip().lower()
        if b == 'dshow':
            api_order = [cv2.CAP_DSHOW]
        elif b == 'msmf':
            api_order = [cv2.CAP_MSMF]
        elif b == 'any' or b == 'default':
            api_order = [None]
        else:
            api_order = [cv2.CAP_DSHOW, cv2.CAP_MSMF, None]
    else:
        api_order = [cv2.CAP_DSHOW, cv2.CAP_MSMF, None]

    for api in api_order:
        cap = _make_cap(idx, api)
        if cap is not None:
            candidates.append(cap)

    for cap in candidates:
        try:
            if cap is not None and cap.isOpened():
                # Basic tuning: resolution and buffer
                try:
                    if width:
                        cap.set(cv2.CAP_PROP_FRAME_WIDTH, int(width))
                    if height:
                        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, int(height))
                    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                except Exception:
                    pass
                return cap
            elif cap is not None:
                cap.release()
        except Exception:
            try:
                cap.release()
            except Exception:
                pass
    return None

# --- YOLOv5 Model Loading ---
try:
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    yolo_model = torch.hub.load(
        './yolov5',
        'custom',
        path='./train/weights/best.pt',
        source='local',
        force_reload=False
    )
    # Move to device and prefer half precision on CUDA
    yolo_model.to(device)
    if device == 'cuda':
        try:
            yolo_model.half()
        except Exception:
            pass
    # Enable backend optimizations
    try:
        if torch.backends.cudnn.is_available():
            torch.backends.cudnn.benchmark = True
    except Exception:
        pass

    # Default threshold; can be updated dynamically if needed
    yolo_model.conf = 0.5
    # Override class names from classes.txt if available
    try:
        classes_path = os.path.join(os.path.dirname(__file__), "classes.txt")
        custom_names = load_class_names(classes_path)
        if custom_names:
            yolo_model.names = custom_names
    except Exception:
        pass
    # Model warm-up to reduce first-frame latency
    try:
        with torch.no_grad():
            dummy = np.zeros((320, 320, 3), dtype=np.uint8)
            _ = yolo_model(dummy)
    except Exception:
        pass

    logger.info(f"YOLOv5 model loaded successfully on device: {device}.")
except Exception as e:
    logger.error(f"Error loading YOLOv5 model: {e}")
    yolo_model = None

# --- Performance monitoring decorator ---
def monitor_performance(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        start_time = time.time()
        try:
            result = f(*args, **kwargs)
            execution_time = time.time() - start_time
            logger.info(f"{f.__name__} executed in {execution_time:.3f} seconds")
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"{f.__name__} failed after {execution_time:.3f} seconds: {str(e)}")
            return jsonify({'error': f'An internal error occurred in {f.__name__}'}), 500
    return decorated_function

# --- Video Streaming Function ---
def generate_frames(source: Optional[str] = None, backend: Optional[str] = None,
                   width: Optional[int] = 640, height: Optional[int] = 480):
    """Generator function to capture video, run detection, and yield frames."""
    global latest_detected_ingredients # Declare that we are using the global variable
    if not yolo_model:
        logger.error("YOLOv5 model is not loaded. Cannot generate frames.")
        return

    camera = open_video_capture(source, backend=backend, width=width, height=height)
    if not camera or not camera.isOpened():
        logger.error("Could not open video source.")
        return

    # Throttle to ~10 FPS to reduce CPU/GPU load
    target_fps = 10.0
    frame_interval = 1.0 / target_fps
    last_time = time.time()

    # Prime the camera by grabbing a few frames (discarded)
    try:
        for _ in range(3):
            camera.read()
    except Exception:
        pass

    consecutive_failures = 0
    try:
        while True:
            # Simple FPS throttle
            now = time.time()
            if now - last_time < frame_interval:
                time.sleep(max(0, frame_interval - (now - last_time)))
            last_time = time.time()

            success, frame = camera.read()
            if not success:
                consecutive_failures += 1
                if consecutive_failures >= 3:
                    # Attempt to re-open the camera once
                    try:
                        camera.release()
                    except Exception:
                        pass
                    camera = open_video_capture(source, backend=backend, width=width, height=height)
                    if not camera or not camera.isOpened():
                        logger.error("Failed to re-open video source. Stopping stream.")
                        break
                    consecutive_failures = 0
                continue
            else:
                consecutive_failures = 0
                # Resize to a known resolution for consistent performance
                try:
                    target_w = int(width) if width else 640
                    target_h = int(height) if height else 480
                    frame = cv2.resize(frame, (target_w, target_h), interpolation=cv2.INTER_LINEAR)
                except Exception:
                    pass

                # Inference with no gradients
                try:
                    with torch.no_grad():
                        results = yolo_model(frame)
                except Exception as e:
                    logger.error(f"Inference error: {e}")
                    continue
                
                # Extract and store detected ingredient names above threshold
                detected_names = set()
                try:
                    # Determine threshold from model.conf (float) or default 0.5
                    try:
                        threshold = float(getattr(yolo_model, 'conf', 0.5))
                    except Exception:
                        threshold = 0.5

                    # Filter detections below threshold BEFORE rendering
                    try:
                        det = results.xyxy[0]
                        if hasattr(det, 'cpu'):
                            mask = det[:, 4] >= threshold
                            results.xyxy[0] = det[mask]
                            filtered_iter = results.xyxy[0]
                        else:
                            mask = det[:, 4] >= threshold
                            results.xyxy[0] = det[mask]
                            filtered_iter = results.xyxy[0]
                    except Exception:
                        filtered_iter = results.xyxy[0]

                    for *box, conf, cls in filtered_iter:
                        try:
                            if float(conf) >= threshold:
                                detected_names.add(yolo_model.names[int(cls)])
                        except Exception:
                            continue
                except Exception:
                    detected_names = set()
                # Update the global set with the latest detections
                latest_detected_ingredients = detected_names
                
                try:
                    rendered_frame = results.render()[0]
                    ret, buffer = cv2.imencode('.jpg', rendered_frame)
                    if not ret:
                        continue
                    frame_bytes = buffer.tobytes()
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
                except (BrokenPipeError, ConnectionResetError, GeneratorExit):
                    # Client disconnected; stop streaming
                    break
                except Exception:
                    continue
    finally:
        try:
            camera.release()
        except Exception:
            pass

# --- Main Web Page Endpoint ---
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    # This route serves the built React app
    return app.send_static_file('index.html')


# --- API Endpoints ---
@app.route('/api/video_feed')
def video_feed():
    """Video streaming route."""
    # Optional: allow setting conf via query string when starting stream
    try:
        conf_q = request.args.get('conf')
        if conf_q is not None and yolo_model is not None:
            val = float(conf_q)
            if 0.0 <= val <= 1.0:
                yolo_model.conf = val
    except Exception:
        pass

    # Allow selecting camera source via query e.g., /api/video_feed?source=1
    source = request.args.get('source')
    backend = request.args.get('backend')  # 'dshow' | 'msmf' | 'default'
    width = request.args.get('width', type=int)
    height = request.args.get('height', type=int)

    return Response(generate_frames(source, backend=backend, width=width, height=height),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/api/video_devices', methods=['GET'])
def list_video_devices():
    """Probe indices 0..5 across backends and report which open successfully."""
    results: List[Dict[str, object]] = []
    for idx in range(0, 6):
        for name, api in [('dshow', cv2.CAP_DSHOW), ('msmf', cv2.CAP_MSMF), ('default', None)]:
            cap = _make_cap(idx, api)
            ok = False
            if cap is not None:
                ok = cap.isOpened()
                try:
                    cap.release()
                except Exception:
                    pass
            results.append({'index': idx, 'backend': name, 'opened': bool(ok)})
    return jsonify({'devices': results})

@app.route('/api/getRecipeByInd', methods=['GET'])
@monitor_performance
def generate_recipes_endpoint():
    """Generates a list of recipes based on ingredients from a query parameter."""
    global latest_detected_ingredients # Declare that we are using the global variable
    ingredients = []
    
    # ======================================================================
    # CHANGE 3: Use the globally stored ingredients first
    # ======================================================================
    if latest_detected_ingredients:
        ingredients = list(latest_detected_ingredients)
        logger.info(f"Using LIVE detected ingredients: {ingredients}")
    else:
        # Fallback to query parameter or default if no live ingredients are found
        ind_val = request.args.get('Ind_val', 'fish,garlic,potatoes')
        ingredients = [i.strip() for i in ind_val.split(',') if i.strip()]
        logger.info(f"Using fallback/default ingredients: {ingredients}")

    if not ingredients:
        return jsonify({'error': 'No valid ingredients provided.'}), 400

    try:
        recipes_text = generate_recipes(ingredients, use_cache=False, model="gpt-4.1")
        if isinstance(recipes_text, bytes):
            recipes_text = recipes_text.decode('utf-8', errors='replace')
        
        parsed_recipes = []
        lines = recipes_text.split('\n')
        current_recipe = None
        for line in lines:
            line = line.strip()
            if not line: continue
            if line.lower().startswith('recipe') and ':' in line or (line and line[0].isdigit() and ('.' in line or ')' in line)):
                if current_recipe:
                    parsed_recipes.append(current_recipe)
                recipe_name = line.split(':', 1)[-1].split('.', 1)[-1].split(')', 1)[-1].strip()
                current_recipe = {"name": recipe_name, "description": ""}
            elif current_recipe and not current_recipe["description"]:
                current_recipe["description"] = line

        if current_recipe:
            parsed_recipes.append(current_recipe)

        # If nothing parsed, surface a clear error for the frontend
        if not parsed_recipes:
            logger.error("LLM returned no parsable recipes. Raw text: %s", recipes_text[:500])
            return jsonify({'error': 'No recipes could be parsed from LLM response. Check OPENAI_API_KEY, network, and model access.'}), 502

        return jsonify({"recipes": parsed_recipes[:5]})
    except Exception as e:
        logger.error(f"Error in generate_recipes_endpoint: {str(e)}")
        return jsonify({'error': 'Failed to generate recipes from LLM'}), 500


@app.route('/api/set_conf', methods=['POST', 'GET'])
def set_conf_endpoint():
    """Set the YOLO confidence threshold globally (0.0 - 1.0)."""
    if yolo_model is None:
        return jsonify({'error': 'Model not loaded'}), 503
    # accept JSON {"conf": 0.7}, form or query ?value=0.7 / ?conf=0.7
    val = None
    try:
        if request.is_json:
            body = request.get_json(silent=True) or {}
            val = body.get('conf', body.get('value'))
        if val is None:
            val = request.values.get('conf', request.values.get('value'))
        if val is None:
            return jsonify({'error': 'Missing conf value'}), 400
        valf = float(val)
        if not (0.0 <= valf <= 1.0):
            return jsonify({'error': 'conf must be between 0.0 and 1.0'}), 400
        yolo_model.conf = valf
        return jsonify({'conf': yolo_model.conf})
    except Exception as e:
        return jsonify({'error': f'invalid conf value: {e}'}), 400

@app.route('/api/getRecipeByDish', methods=['GET'])
@monitor_performance
def get_recipe_steps_endpoint():
    """Gets the detailed steps for a specific recipe name from a query parameter."""
    recipe_name = request.args.get('recipe_val', '')
    if not recipe_name:
        return jsonify({'error': 'A recipe name is required.'}), 400
    
    try:
        steps = get_recipe_steps(recipe_name, required_ingredients=[], use_cache=False, model="gpt-4.1")
        if isinstance(steps, bytes):
            steps = steps.decode('utf-8', errors='replace')
        return jsonify({'steps': steps})
    except Exception as e:
        logger.error(f"Error getting recipe steps for '{recipe_name}': {str(e)}")
        return jsonify({'error': 'Failed to get recipe steps from LLM'}), 500


# --- Error Handlers ---
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'API endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal Server Error: {error}")
    return jsonify({'error': 'Internal server error'}), 500


# --- Main Execution ---
if __name__ == '__main__':
    print("Starting LutongBahAI API server...")
    print("\nStarting server on http://localhost:5000") # Ensure your port is correct
    app.run(host='0.0.0.0', port=5000, debug=False) # Set debug=False for stability with streaming