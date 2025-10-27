# LutongBahAI - AI-Powered Filipino Recipe Generator

A complete web application that uses computer vision (YOLO) and artificial intelligence (OpenAI GPT) to detect ingredients and generate authentic Filipino recipes.

## 🚀 Quick Start

### Prerequisites
- **Python 3.10+** installed and on PATH
- **Node.js 18+** for frontend development
- **OpenAI API Key** (get one at [platform.openai.com](https://platform.openai.com))
- **Webcam** (optional - can use image/video files)

### Installation

#### 1. Backend Setup
```powershell
cd lutongbahAI
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

#### 2. Configure API Key
Create a `.env` file in `lutongbahAI/` directory:
```env
OPENAI_API_KEY=your_openai_api_key_here
```

#### 3. Run Backend Server
```powershell
cd lutongbahAI
.\.venv\Scripts\Activate.ps1
python main.py --api
```
Server runs on **http://localhost:5000**

#### 4. Frontend Development (Optional)
```powershell
npm install
npm run dev
```
Runs on **http://localhost:5173**

## 📖 Complete Documentation

For detailed setup, troubleshooting, API endpoints, architecture diagrams, and advanced usage:
👉 **[Full Documentation](lutongbahAI/README.md)**

## 🎯 Features

- 🎥 **Real-time ingredient detection** from webcam or images
- 🤖 **AI-powered recipe generation** using OpenAI GPT-4
- 📱 **Modern web interface** with live video streaming
- 🎯 **Custom YOLO model** trained on 33 ingredient classes
- 🔧 **Adjustable detection confidence** thresholds
- 💾 **Automatic cleanup** of temporary files
- 🚀 **Caching system** for faster responses

## 🏗️ Architecture

### Backend (`lutongbahAI/`)
- Python Flask API server
- YOLO object detection for ingredients
- OpenAI integration for recipe generation
- Live video streaming

### Frontend (`src/`)
- React.js with Vite
- Real-time video display
- Recipe browsing and detailed steps
- Modern UI/UX

## 🎮 Quick Usage

### API Mode
```powershell
cd lutongbahAI
.\.venv\Scripts\Activate.ps1
python main.py --api
```
Open `http://localhost:5000` in your browser.

### CLI Mode
```powershell
python main.py --weights .\train\weights\best.pt
```
- Press **P** to capture ingredients
- Press **Q** to quit and generate recipes

## 🔌 API Endpoints

- `GET /api/getRecipeByInd?Ind_val=ingredient1,ingredient2` - Generate recipes
- `GET /api/getRecipeByDish?recipe_val=Dish Name` - Get recipe steps
- `GET /api/video_feed` - Live video stream
- `POST /api/setConfidence` - Adjust detection confidence

## 🐛 Common Issues

**"OPENAI_API_KEY is not set"**
- Create `.env` file in `lutongbahAI/` with your API key

**Camera not working**
- Try different camera indices: `--source "1"`

**No module found**
- Ensure venv is activated: `.\.venv\Scripts\Activate.ps1`

👉 See [Full Documentation](lutongbahAI/README.md) for complete troubleshooting.

## 📄 License

Educational and research purposes.

---

**Note**: This system requires an OpenAI API key with credits. Usage will incur API costs.
