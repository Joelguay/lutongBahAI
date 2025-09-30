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

# --- YOLOv5 Model Loading ---
try:
    yolo_model = torch.hub.load(
        './yolov5',
        'custom',
        path='./train/weights/best.pt',
        source='local',
        force_reload=True
    )
    yolo_model.conf = 0.5
    logger.info("YOLOv5 model loaded successfully for video streaming.")
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
def generate_frames():
    """Generator function to capture video, run detection, and yield frames."""
    global latest_detected_ingredients # Declare that we are using the global variable
    if not yolo_model:
        logger.error("YOLOv5 model is not loaded. Cannot generate frames.")
        return

    camera = cv2.VideoCapture(0)
    if not camera.isOpened():
        logger.error("Could not open video source.")
        return

    while True:
        success, frame = camera.read()
        if not success:
            break
        else:
            results = yolo_model(frame)
            
            # ======================================================================
            # CHANGE 2: Extract and store the names of detected ingredients
            # ======================================================================
            detected_names = set()
            # Loop through the detection results
            for *box, conf, cls in results.xyxy[0]:
                # Add the detected class name to our temporary set
                detected_names.add(yolo_model.names[int(cls)])
            # Update the global set with the latest detections
            latest_detected_ingredients = detected_names
            
            rendered_frame = results.render()[0]
            ret, buffer = cv2.imencode('.jpg', rendered_frame)
            if not ret:
                continue
            
            frame_bytes = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

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
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

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
        
        return jsonify({"recipes": parsed_recipes[:5]})
    except Exception as e:
        logger.error(f"Error in generate_recipes_endpoint: {str(e)}")
        return jsonify({'error': 'Failed to generate recipes from LLM'}), 500

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