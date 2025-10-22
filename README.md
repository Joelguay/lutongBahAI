<<<<<<< HEAD
## LutongBahAI — YOLOv5 Ingredient Detection + OpenAI Recipes (Windows)

This project has two parts:
- Python backend in `lutongbahAI/` (Flask API, YOLOv5 inference, OpenAI integration)
- React frontend (Vite) in the repo root `src/`

### 1) Prerequisites
- Python 3.10+
- Node.js 18+
- Webcam (optional) or image/video files

### 2) Backend Setup (Python)
```powershell
cd lutongbahAI
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt
# Set your key for this shell
$env:OPENAI_API_KEY="YOUR_OPENAI_API_KEY"
```

Run API server (Flask):
```powershell
python main.py --api
# Server on http://localhost:5000
```

Or run CLI with detection first:
```powershell
python main.py --weights .\train\weights\best.pt
```

Optional build to serve React from Flask (production):
```powershell
cd ..
npm run build
# Flask in `lutongbahAI/api.py` serves `../dist/index.html` and assets
```

### 3) Frontend Setup (Vite)
```powershell
npm install
npm run dev
# Frontend on http://localhost:5173
```

The frontend calls the backend at `http://localhost:5000/api/...`.

### 4) Useful API endpoints
- `GET http://localhost:5000/api/getRecipeByInd?Ind_val=fish,garlic,potatoes`
- `GET http://localhost:5000/api/getRecipeByDish?recipe_val=Adobo`
- `GET http://localhost:5000/api/video_feed` (MJPEG stream if camera enabled)

### 5) Notes
- Weights path default is `lutongbahAI/train/weights/best.pt`.
- Never commit real API keys. Use `$env:OPENAI_API_KEY` per session.
=======
## YOLO Ingredient Detection → OpenAI Recipe Generation

This app integrates your custom YOLOv5 CNN (trained on 23 ingredient classes) with OpenAI to generate Filipino recipes. The flow is: CNN runs first to detect ingredients → results are saved as JSON → JSON and ingredient list are sent to OpenAI to generate recipes → you choose a dish to view detailed steps.

### 🚀 Quick Start

1) Install dependencies (recommended in a virtual environment)

```powershell
cd "C:\Users\guayj\OneDrive\Desktop\Thesis"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r ingredient_Detection\OLLama-LLM\requirements.txt
```

2) Set your OpenAI API key for the session

```powershell
$env:OPENAI_API_KEY="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"
```

3) Run with detection (CNN first, then LLM)

```powershell
python ingredient_Detection\OLLama-LLM\main.py --weights ingredient_Detection\OLLama-LLM\train\weights\best.pt
```

4) Skip detection (uses defaults)

```powershell
python ingredient_Detection\OLLama-LLM\main.py --no-detection
```

### ▶️ CLI Usage

```powershell
# Basic detection with default settings (auto-cleanup)
python ingredient_Detection\OLLama-LLM\main.py

# Custom model weights
python ingredient_Detection\OLLama-LLM\main.py --weights "C:\\path\\to\\your\\model.pt"

# Different camera or file source
python ingredient_Detection\OLLama-LLM\main.py --source "1"              # camera 1
python ingredient_Detection\OLLama-LLM\main.py --source "path\\image.jpg"  # image file

# Adjust confidence threshold
python ingredient_Detection\OLLama-LLM\main.py --conf 0.7

# Skip detection, use default ingredients
python ingredient_Detection\OLLama-LLM\main.py --no-detection

# Keep captured files (don’t auto-clean)
python ingredient_Detection\OLLama-LLM\main.py --keep-captured
```

### 🌐 Run as Web API

```powershell
python ingredient_Detection\OLLama-LLM\main.py --api
```

Then open `http://localhost:5000`.

### 🔧 How It Works

1. YOLO detection runs first (press `P` to capture, `Q` to quit).
2. Detected objects are saved as JSON in `captured/capture_YYYYMMDD_HHMMSS.txt`.
3. The app reads the detected ingredient list and also passes the raw JSON to OpenAI as context.
4. OpenAI returns 5 Filipino household recipes in the format:
   - `Recipe 1: Dish Name` followed by a one-line description, up to `Recipe 5`.
5. You select a recipe number to print detailed step-by-step instructions.
6. Auto-cleanup removes the `captured/` directory unless `--keep-captured` is used.

### 📁 File Structure

```
ingredient_Detection/OLLama-LLM/
├── main.py                    # Entry point / CLI
├── yoloDetect.py              # YOLOv5 detection loop (press P to capture)
├── ingredient_integration.py  # Detection helpers, JSON reading, cleanup
├── llm_utils.py               # OpenAI integration and caching
├── api.py                     # Flask API endpoints
├── templates/
│   └── index.html             # Web UI
├── train/weights/best.pt      # Your model weights (default path)
├── yolov5/                    # Local YOLOv5 repo (used via torch.hub.load)
├── classes.txt                # Your 23 ingredient classes
└── requirements.txt           # Python dependencies
```

### 🧠 Ingredient Classes (example)

If you trained on 23 classes (see `classes.txt`), examples include: Banana, Butter, Carrot, Cheese, Chicken, Egg, Eggplant, Fish, Flour, Garlic, GBellP, Lime, LimeComG, LimeComY, Meat, Mushroom, Onion, Parsley, Potato, RBellP, Sausage, Tomato, YBellP.

### 🔍 Detection Results Format

```json
{
  "Detected Objects": [
    "Chicken",
    "Potato",
    "Carrot"
  ]
}
```

### 🧹 Auto-Cleanup

- CLI: `captured/` is deleted when the session finishes (unless `--keep-captured`).
- API: `captured/` is deleted when the server shuts down.
- Cleanup also runs on exceptions and `Ctrl+C`.

### ⚙️ Configuration Notes

- Default model path: `ingredient_Detection/OLLama-LLM/train/weights/best.pt` (project-relative).
- YOLOv5 is loaded from the local `yolov5/` directory using `torch.hub.load`.
- Python 3.10+ recommended.

### 🐛 Troubleshooting

1) "No detection file found"
   - Press `P` during detection to capture.
   - Ensure `captured/` exists with `capture_*.txt` after capture.

2) "Could not open source"
   - Check `--source` value (`"0"`, `"1"`, path to image/video).

3) OpenAI key error
   - Ensure `$env:OPENAI_API_KEY` is set before running.

4) Missing deps (e.g., cv2/torch)
   - Run `pip install -r ingredient_Detection/OLLama-LLM/requirements.txt`.

5) Model path errors
   - Pass `--weights` pointing to your `.pt` file if default is missing.

### 🔄 API Endpoints

- `GET /` – Web UI.
- `GET /getRecipeByInd?Ind_val=ingredient1,ingredient2` – Generate recipes by ingredients.
- `GET /getRecipeByDish?recipe_val=Dish Name` – Get step-by-step instructions for a dish.
- `GET /getDetectedIngredients` – Latest detected ingredients from `captured/`.

### 📦 Development Tips

- Keep sessions clean by letting auto-cleanup run. Use `--keep-captured` only when you need to inspect files.
- You can alter detection JSON parsing or cleanup strategies in `ingredient_integration.py`.
- For CPU-only environments, Torch may be slower; consider installing a CUDA-enabled build if available.

---

If you need the README to reflect previous Ollama instructions exactly (or want a button in the web UI to trigger a fresh capture), let me know and I’ll add it.


>>>>>>> recovery-branch
