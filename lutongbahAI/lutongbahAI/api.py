# ============================================================
# Optimized LutongBahAI API (Full 640×640, Threaded Camera, FP16)
# ============================================================
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
from threading import Thread

# --- Basic Setup ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

dist_folder = os.path.join(os.path.dirname(__file__), '..', 'dist')
app = Flask(__name__, template_folder=dist_folder, static_folder=os.path.join(dist_folder, 'assets'))
CORS(app)

# --- App Setup ---
clear_cache()
atexit.register(cleanup_captured_directory)
logger.info("Registered cleanup function for captured ingredients directory.")

# ============================================================
# Globals
# ============================================================
latest_detected_ingredients = set()
CONFIDENCE_THRESHOLD = 0.7

# ============================================================
# YOLO Model Loading
# ============================================================
try:
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    from ultralytics import YOLO
    yolo_model = YOLO('./train/weights/best.pt')
    yolo_model.to(device)
    logger.info(f"YOLO model loaded on device: {device}")

    # Warm up model once to remove first-frame lag
    dummy = np.zeros((640, 640, 3), dtype=np.uint8)
    yolo_model.predict(dummy, verbose=False)
    logger.info("Model warm-up complete.")
except Exception as e:
    logger.error(f"Error loading YOLO model: {e}")
    yolo_model = None

# ============================================================
# Threaded Camera Class (non-blocking)
# ============================================================
class VideoCamera:
    def __init__(self, src=0):
        self.camera = cv2.VideoCapture(src)
        if not self.camera.isOpened():
            logger.error("Unable to access webcam.")
        self.running = True
        self.grabbed, self.frame = self.camera.read()
        Thread(target=self._update, daemon=True).start()

    def _update(self):
        while self.running:
            self.grabbed, self.frame = self.camera.read()

    def get_frame(self):
        return self.frame

    def stop(self):
        self.running = False
        self.camera.release()

# ============================================================
# Performance Monitoring Decorator
# ============================================================
def monitor_performance(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        start_time = time.time()
        try:
            result = f(*args, **kwargs)
            elapsed = time.time() - start_time
            logger.info(f"{f.__name__} executed in {elapsed:.3f}s")
            return result
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"{f.__name__} failed after {elapsed:.3f}s: {e}")
            return jsonify({'error': f'Internal error in {f.__name__}'}), 500
    return decorated_function

# ============================================================
# --- Video Streaming Function (Optimized) ---
# ============================================================
def generate_frames():
    """Generator function to capture video, run YOLO detection, and yield frames."""
    global latest_detected_ingredients
    if not yolo_model:
        logger.error("YOLO model is not loaded.")
        return

    camera = VideoCamera(0)
    target_fps = 20.0
    frame_interval = 1.0 / target_fps
    last_time = time.time()

    while True:
        now = time.time()
        if now - last_time < frame_interval:
            time.sleep(max(0, frame_interval - (now - last_time)))
        last_time = time.time()

        frame = camera.get_frame()
        if frame is None:
            continue

        try:
            with torch.no_grad():
                results = yolo_model.predict(
                    frame,
                    conf=CONFIDENCE_THRESHOLD,
                    verbose=False,
                    imgsz=640,                       # Full size, no resize
                    half=True if device == 'cuda' else False,
                    device=device
                )

            result = results[0] if isinstance(results, (list, tuple)) else results
            detected_names = set()

            # Load trained classes
            classes_path = os.path.join(os.path.dirname(__file__), 'classes.txt')
            trained_classes = set()
            try:
                with open(classes_path, 'r', encoding='utf-8') as cf:
                    trained_classes = {ln.strip().lower() for ln in cf if ln.strip()}
            except Exception:
                pass

            TRAINED_CLASS_CONF = 0.9
            if result and len(result.boxes) > 0:
                for box in result.boxes:
                    try:
                        cls_id = int(box.cls[0])
                        name = yolo_model.names.get(cls_id, str(cls_id))
                        conf = float(box.conf[0]) if hasattr(box, 'conf') else None
                        if name.strip().lower() in trained_classes and conf and conf >= TRAINED_CLASS_CONF:
                            detected_names.add(name)
                    except Exception:
                        continue

            latest_detected_ingredients = detected_names

            # Render results to frame
            rendered_frame = result.plot() if hasattr(result, "plot") else frame
            ret, buffer = cv2.imencode('.jpg', rendered_frame)
            if not ret:
                continue
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')

        except Exception as e:
            logger.error(f"Frame processing error: {e}")
            continue

# ============================================================
# --- ROUTES ---
# ============================================================
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    return app.send_static_file('index.html')

@app.route('/api/video_feed')
def video_feed():
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

# ============================================================
# --- Recipe Endpoints ---
# ============================================================
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
    logger.info(f"Ingredients used: {ingredients}")

    try:
        recipes_text = generate_recipes(ingredients, use_cache=False, model="gpt-4.1")
        if isinstance(recipes_text, bytes):
            recipes_text = recipes_text.decode('utf-8', errors='replace')

        parsed_recipes, current_recipe = [], None
        for line in recipes_text.splitlines():
            line = line.strip()
            if not line:
                continue
            if line.lower().startswith('recipe') or (line and line[0].isdigit()):
                if current_recipe:
                    parsed_recipes.append(current_recipe)
                recipe_name = line.split(':')[-1].split('.', 1)[-1].split(')', 1)[-1].strip()
                current_recipe = {"name": recipe_name, "description": ""}
            elif current_recipe and not current_recipe["description"]:
                current_recipe["description"] = line
        if current_recipe:
            parsed_recipes.append(current_recipe)

        if not parsed_recipes:
            logger.error("No parsable recipes found.")
            return jsonify({'error': 'No recipes could be parsed.'}), 502
        return jsonify({"recipes": parsed_recipes[:5]})
    except Exception as e:
        logger.error(f"Recipe generation failed: {e}")
        return jsonify({'error': 'Failed to generate recipes'}), 500

# In api.py

@app.route('/api/getRecipeByDish', methods=['GET'])
@monitor_performance
def get_recipe_steps_endpoint():
    recipe_name = request.args.get('recipe_val', '')
    if not recipe_name:
        return jsonify({'error': 'A recipe name is required.'}), 400
    
    try:
        steps = get_recipe_steps(recipe_name, required_ingredients=[], use_cache=False, model="gpt-4.1")
        if isinstance(steps, bytes):
            steps = steps.decode('utf-8', errors='replace')
        return jsonify({'steps': steps})
    except Exception as e:
        logger.error(f"Error getting recipe steps for '{recipe_name}': {e}")
        return jsonify({'error': 'Failed to get recipe steps'}), 500

# ============================================================
# --- Confidence Control ---
# ============================================================
@app.route('/api/setConfidence', methods=['POST'])
@monitor_performance
def set_confidence_endpoint():
    global CONFIDENCE_THRESHOLD
    try:
        data = request.get_json()
        new_conf = float(data.get('confidence', 0))
        if not 0.0 <= new_conf <= 1.0:
            return jsonify({'error': 'Confidence must be 0.0–1.0'}), 400
        CONFIDENCE_THRESHOLD = new_conf
        logger.info(f"Confidence threshold updated: {CONFIDENCE_THRESHOLD}")
        return jsonify({'message': f'Confidence threshold set to {CONFIDENCE_THRESHOLD}'})
    except Exception as e:
        logger.error(f"Error updating confidence: {e}")
        return jsonify({'error': 'Failed to update confidence'}), 500

@app.route('/api/getConfidence', methods=['GET'])
def get_confidence_endpoint():
    return jsonify({'confidence': CONFIDENCE_THRESHOLD})

# ============================================================
# --- Error Handlers ---
# ============================================================
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'API endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal Server Error: {error}")
    return jsonify({'error': 'Internal server error'}), 500

# ============================================================
# --- Run Server ---
# ============================================================
if __name__ == '__main__':
    print("Starting LutongBahAI API server on http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=False)
