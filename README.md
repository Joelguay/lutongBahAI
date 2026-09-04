# LutongBahAI

AI-powered Filipino recipe helper: scan ingredients, get lutong bahay suggestions.

## Architecture

```
web/        Next.js (Vercel) — pages + browser camera
api/        FastAPI — YOLO detect + Gemini Flash recipes
training/   How to add classes later
```

The older Vite/Flask files (`index.html`, `src/`, `lutongbahAI/`) are still here for reference. **Run the new app from `web/` and `api/`.**

## Quick start

### API

```bash
cd api
python3 -m venv .venv
source .venv/bin/activate
pip install fastapi "uvicorn[standard]" python-dotenv google-genai python-multipart pydantic
cp .env.example .env   # add GEMINI_API_KEY for recipes
uvicorn app.main:app --reload --port 8000
```

Full `requirements.txt` includes PyTorch/Ultralytics. Install that when you add `api/weights/best.pt`.

Until weights exist, `/v1/detect` runs in **mock** mode (no boxes). Recipe requests still must use detector class names (`GET /v1/classes`).

### Web

```bash
cd web
cp .env.example .env.local
npm install
npm run dev
```

Open http://localhost:3000

| Page | Route |
|------|--------|
| Home | `/` |
| About | `/about` |
| Camera + recipes | `/camera` |
| Manual | `/manual` |
| Support | `/support` |

## Ingredient classes

This version is trained on **33** YOLO classes (live list: `GET /v1/classes`). The API maps Roboflow labels such as `GBellP` to readable names (`Green bell pepper`) in `api/app/ingredients.py` — that is not a retrain. Typed names that are not in that list are rejected with `"…" is not yet available.`

Recipes may still use pantry staples the camera cannot see: rice, water, oil, salt, soy sauce (toyo), vinegar (suka). Do not type those as ingredients.

## Deploy later

- Frontend → Vercel (`NEXT_PUBLIC_API_URL` = your API origin)
- API → Hugging Face Spaces / Fly / a VM (not Vercel)
- `best.pt` → `api/weights/` or Hugging Face Hub (not GitHub)
