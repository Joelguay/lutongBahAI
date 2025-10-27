# LutongBahAI - Filipino Recipe Generator with AI-Powered Ingredient Detection

A complete system that uses YOLO object detection to identify ingredients and OpenAI's GPT to generate authentic Filipino recipes.

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
  - [CLI Mode](#cli-mode)
  - [API/Web Mode](#apiweb-mode)
- [Architecture](#architecture)
- [File Structure](#file-structure)
- [API Endpoints](#api-endpoints)
- [Troubleshooting](#troubleshooting)

## 📖 Overview

LutongBahAI combines computer vision and AI to create Filipino recipes from detected ingredients:

1. **Ingredient Detection**: Uses a custom-trained YOLO model to detect ingredients from webcam or images
2. **Recipe Generation**: Leverages OpenAI's GPT to generate 5 Filipino recipe suggestions
3. **Detailed Instructions**: Provides step-by-step cooking instructions for selected recipes

The system can run in two modes:
- **CLI Mode**: Interactive terminal interface with live webcam detection
- **API Mode**: Flask-based web API with live video streaming and RESTful endpoints

## ✨ Features

- 🎥 Real-time ingredient detection via webcam
- 🤖 AI-powered recipe generation using GPT-4
- 📱 Modern web interface with live video streaming
- 🎯 Custom-trained YOLO model for 33 ingredient classes
- 🔧 Adjustable confidence thresholds
- 💾 Automatic cleanup of temporary files
- 🚀 Caching system for faster response times

## 🔧 Prerequisites

### System Requirements
- **OS**: Windows 10/11 (Linux/Mac supported but not tested)
- **Python**: 3.10 or higher
- **RAM**: 4GB minimum (8GB recommended)
- **Camera**: Working webcam (optional - can use image/video files)

### GPU Support (Optional but Recommended)
- **NVIDIA GPU** with CUDA 11.8+ drivers
- **PyTorch CUDA** build for faster inference

## 📦 Installation

### Step 1: Clone or Download the Repository

If this is on a new machine, ensure the folder structure looks like:
```
lutongbahAI_FinalRepo/
├── lutongbahAI/           # Python backend
│   ├── train/weights/     # Model weights
│   ├── classes.txt        # Ingredient classes
│   └── ...
└── ...
```

### Step 2: Create Virtual Environment

Open PowerShell in the project root and navigate to the backend:

```powershell
cd lutongbahAI
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

You should see `(.venv)` in your prompt.

### Step 3: Install Dependencies

```powershell
pip install --upgrade pip
pip install -r requirements.txt
```

**Note**: If you have an NVIDIA GPU and want CUDA-enabled PyTorch for faster inference:
1. Visit [PyTorch's official site](https://pytorch.org/get-started/locally/)
2. Install the CUDA-enabled PyTorch wheel first
3. Then run `pip install -r requirements.txt`

### Step 4: Verify Model Weights

Ensure your YOLO model weights exist at:
```
lutongbahAI/train/weights/best.pt
```

If your weights are elsewhere, you can specify the path using the `--weights` flag.

### Step 5: Set Up OpenAI API Key

Create a `.env` file in the `lutongbahAI/` directory:

```env
OPENAI_API_KEY=your_openai_api_key_here
```

**Important**: Never commit real API keys to version control!

Alternatively, set the environment variable in PowerShell:
```powershell
$env:OPENAI_API_KEY="your_openai_api_key_here"
```

## ⚙️ Configuration

### Ingredient Classes

The model is trained to detect 33 ingredients defined in `classes.txt`:
- Vegetables: Carrot, Potato, Onion, Tomato, Eggplant, Mushroom, etc.
- Proteins: Chicken, Fish, Meat, Shrimp, Sausage, etc.
- Herbs & Spices: Garlic, Basil, Parsley, Pepper, etc.
- Others: Butter, Cheese, Flour, Milk, etc.

### Confidence Threshold

The default confidence threshold is `0.7` (70% confidence required for detection).

- **CLI Mode**: Pass `--conf 0.5` for more detections (lower threshold)
- **API Mode**: Change threshold via `/api/setConfidence` endpoint or via the UI

## 🚀 Usage

### CLI Mode

Run with live detection (recommended):

```powershell
python main.py --weights .\train\weights\best.pt
```

**Controls**:
- Press **`P`** to capture and detect ingredients from current frame
- Press **`Q`** to quit detection
- After quitting, the app generates recipes and asks you to choose one

#### Advanced CLI Options

```powershell
# Use custom model weights
python main.py --weights "C:\path\to\your\model.pt"

# Different camera or file source
python main.py --source "1"                    # Camera 1
python main.py --source "path\to\image.jpg"    # Image file
python main.py --source "path\to\video.mp4"     # Video file

# Adjust confidence threshold
python main.py --conf 0.5                       # Lower threshold (more detections)
python main.py --conf 0.9                       # Higher threshold (fewer but confident detections)

# Skip detection, use default ingredients
python main.py --no-detection

# Keep captured files (for debugging)
python main.py --keep-captured
```

### API/Web Mode

Start the Flask API server:

```powershell
python main.py --api
```

The server will start on `http://localhost:5000`

#### Using the Web Interface

1. Open your browser and navigate to `http://localhost:5000`
2. You'll see the web UI with live video streaming
3. Adjust the confidence threshold using the slider
4. The system automatically detects ingredients from the video feed
5. Click "Get Recipes" to generate recipe suggestions

#### Stop the Server

Press `Ctrl+C` in the terminal to gracefully shut down the server.

## 🏗️ Architecture

### System Flow

```
┌─────────────────┐
│   User Input    │
│  (Webcam/Image) │
└────────┬────────┘
         │
         ▼
┌─────────────────┐     ┌──────────────┐
│  YOLO Detection  │────▶│ Detected     │
│  (Custom Model)  │     │ Ingredients  │
└────────┬────────┘     └──────┬───────┘
         │                      │
         │                      ▼
         │              ┌─────────────────┐
         │              │ OpenAI GPT-4     │
         │              │ Recipe Generation│
         │              └──────┬────────────┘
         │                     │
         │                     ▼
         │              ┌─────────────────┐
         └─────────────▶│ Recipe Steps    │
                        │ (Detailed)      │
                        └─────────────────┘
```

### Core Components

1. **yoloDetect.py**: YOLO inference and detection loop
2. **ingredient_integration.py**: Detection helpers, JSON reading, cleanup
3. **llm_utils.py**: OpenAI integration and caching
4. **api.py**: Flask API endpoints
5. **main.py**: Entry point with CLI argument parsing

## 📁 File Structure

```
lutongbahAI/
├── main.py                      # Entry point / CLI
├── yoloDetect.py               # YOLO detection loop
├── ingredient_integration.py   # Detection helpers
├── llm_utils.py                # OpenAI integration
├── api.py                      # Flask API server
├── classes.txt                 # 33 ingredient classes
├── requirements.txt             # Python dependencies
├── README.md                   # This file
├── train/
│   └── weights/
│       └── best.pt             # Trained YOLO model
└── captured/                   # Auto-generated, auto-cleaned
    ├── capture_TIMESTAMP.jpg
    └── capture_TIMESTAMP.txt   # JSON detection results
```

### Detection Result Format

The system saves detection results as JSON in `.txt` files:

```json
{
  "Detected Objects": [
    "Chicken",
    "Potato",
    "Carrot",
    "Garlic"
  ]
}
```

## 🌐 API Endpoints

### Recipe Generation

```http
GET /api/getRecipeByInd?Ind_val=ingredient1,ingredient2
```

**Response**:
```json
{
  "recipes": [
    {
      "name": "Chicken Adobo",
      "description": "Classic Filipino dish with soy sauce and vinegar."
    },
    ...
  ]
}
```

### Recipe Steps

```http
GET /api/getRecipeByDish?recipe_val=Chicken Adobo
```

**Response**:
```json
{
  "steps": "Detailed step-by-step instructions..."
}
```

### Confidence Control

```http
POST /api/setConfidence
Content-Type: application/json

{
  "confidence": 0.7
}
```

```http
GET /api/getConfidence
```

### Video Feed

```http
GET /api/video_feed
```

Returns an MJPEG stream for live video with detection overlays.

## 🐛 Troubleshooting

### "No module named 'xxx'"
**Solution**: Activate the virtual environment and install requirements:
```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### "OPENAI_API_KEY is not set"
**Solution**: Create `.env` file or set environment variable:
```powershell
$env:OPENAI_API_KEY="your_key_here"
```

### "Could not open source"
**Solution**: 
- Try a different camera index: `--source "1"` or `--source "2"`
- Ensure image/video path is correct
- Check file permissions

### "No detection file found"
**Solution**: 
- In CLI mode: Press `P` during detection to capture a frame
- Verify `captured/` directory exists after capture
- Check that model is loading correctly

### Slow inference on CPU
**Solution**: 
- Install CUDA-enabled PyTorch if you have an NVIDIA GPU
- Reduce input resolution (edit `yoloDetect.py`)
- Lower the confidence threshold: `--conf 0.5`

### Model path errors
**Solution**: Specify the correct path to your model:
```powershell
python main.py --weights "C:\full\path\to\best.pt"
```

### Camera not detected
**Solution**:
- Try different camera indices (`--source "0"`, `--source "1"`)
- Check device manager for camera driver issues
- Try different backend: `--backend msmf`

## 📝 Development Notes

### Auto-Cleanup Behavior
- CLI: `captured/` is deleted when the session finishes (unless `--keep-captured`)
- API: `captured/` is deleted when the server shuts down
- Cleanup also runs on exceptions and `Ctrl+C`

### Caching System
- Recipe suggestions are cached for 1 hour
- Recipe steps are cached for 2 hours
- Cache can be cleared via API or restarting the server

### YOLO Model Details
- Framework: Ultralytics YOLO (not original YOLOv5)
- Input size: 640x640
- Architecture: YOLOv5mu (custom medium-sized model)
- Training: Custom dataset with 33 ingredient classes

## 📄 License

This project is for educational and research purposes.

## 🤝 Contributing

Contributions are welcome! Please ensure to:
1. Test your changes thoroughly
2. Update this README if needed
3. Never commit API keys or sensitive data

## 📞 Support

For issues or questions:
- Check the Troubleshooting section above
- Review the code comments in each module
- Ensure all dependencies are properly installed

---

**Note**: This system requires an OpenAI API key with credits. Recipe generation will incur API costs based on usage.
