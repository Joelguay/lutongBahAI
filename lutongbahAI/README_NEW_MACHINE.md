## New Machine Setup Guide

This guide helps you run the project on a fresh Windows machine with minimal steps.

### 1) Prerequisites
- Python 3.10+ installed and on PATH
- A working webcam (for live detection) or image/video files
- Optional: NVIDIA GPU + CUDA drivers (for faster Torch)

### 2) Get the Project
- Copy the folder to the new machine, or clone your repo so that the project path looks like:
  `.../ingredient_Detection/OLLama-LLM/`

### 3) Create Virtual Environment and Install Deps
Open PowerShell in the project root (containing `ingredient_Detection/`):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r ingredient_Detection\OLLama-LLM\requirements.txt
```

If you have an NVIDIA GPU and want CUDA-enabled PyTorch, install the wheel from the official site first, then rerun the requirements install.

### 4) Place Model Weights
Ensure your YOLO weights exist at:
`ingredient_Detection/OLLama-LLM/train/weights/best.pt`

If your weights are elsewhere, pass `--weights` with the full path when running.

### 5) Set OpenAI API Key
```powershell
# Replace with your own key. Never commit real keys to the repo.
$env:OPENAI_API_KEY="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"
```

### 6) Run
- Run with detection (CNN first, then LLM):
```powershell
python ingredient_Detection\OLLama-LLM\main.py --weights ingredient_Detection\OLLama-LLM\train\weights\best.pt
```
  - Window opens; press `P` to capture; press `Q` to end detection. The app then generates recipes and asks you to pick a dish for steps.

- Skip detection (use default ingredients):
```powershell
python ingredient_Detection\OLLama-LLM\main.py --no-detection
```

- API mode (web server):
```powershell
python ingredient_Detection\OLLama-LLM\main.py --api
```
Open `http://localhost:5000` in a browser.

### 7) Common CLI Flags
```powershell
--weights PATH   # path to model .pt
--source 0       # webcam index; or path to image/video file
--conf 0.7       # confidence threshold
--no-detection   # skip CNN, use default ingredients
--keep-captured  # keep captured/ files after run
--api            # start Flask API
```

### 8) Troubleshooting
- "No module named 'openai'": Ensure venv is active and `pip install -r .../requirements.txt` ran without errors.
- "OPENAI_API_KEY is not set": Set `$env:OPENAI_API_KEY` in the same shell before running.
- "Could not open source": Change `--source` (e.g., `--source 1`, or provide a file path).
- Slow Torch on CPU: Consider installing a CUDA-enabled PyTorch build if you have an NVIDIA GPU.
- No detection file found: During the detection window, press `P` to capture a frame.

### 9) Files You Need
- Code: `main.py`, `yoloDetect.py`, `ingredient_integration.py`, `llm_utils.py`, `api.py`
- YOLO runtime: `yolov5/` (kept minimal for inference)
- Web UI: `templates/index.html`
- Model weights: `train/weights/best.pt` (and optional `last.pt`)
- Dependencies: `requirements.txt`

You should now be able to run detection and generate Filipino recipes with the same output format as the original app.


