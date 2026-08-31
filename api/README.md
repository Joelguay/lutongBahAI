# LutongBahAI API

FastAPI service for ingredient detection and Filipino recipe generation.

## Run

```bash
cd api
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
cp .env.example .env        # then add OPENAI_API_KEY
uvicorn app.main:app --reload --port 8000
```

API docs: http://localhost:8000/docs

## Weights

Detection stays in **mock** mode until you add:

```
api/weights/best.pt
```

Mock mode returns no boxes. You can still type ingredients in the web app and generate recipes.

## Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/v1/health` | Detector mode, class list, whether OpenAI is configured |
| GET | `/v1/classes` | Ingredient names the model knows |
| POST | `/v1/detect` | Multipart `file` + `conf` query |
| POST | `/v1/recipes` | `{ "ingredients": ["Garlic"] }` |
| POST | `/v1/recipes/steps` | `{ "name": "Adobo", "ingredients": [...] }` |
