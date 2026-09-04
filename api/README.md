# LutongBahAI API

FastAPI service for ingredient detection and Filipino recipe generation.

## Run

```bash
cd api
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
cp .env.example .env        # then add GEMINI_API_KEY
uvicorn app.main:app --reload --port 8000
```

API docs: http://localhost:8000/docs

## Weights

Detection stays in **mock** mode until you add:

```
api/weights/best.pt
```

Mock mode returns no boxes. Recipe endpoints still only accept names from `GET /v1/classes`.

## Ingredient allowlist

`POST /v1/recipes` and `POST /v1/recipes/steps` accept detector classes (33 with `best.pt`), including Roboflow names (`GBellP`) and display names (`Green bell pepper`). Unknown strings return 400: `"…" is not yet available.`

Readable names are defined in `app/ingredients.py` (`DISPLAY_NAMES`). They do not change `best.pt`.

Gemini may still use pantry staples (rice, oil, salt, toyo, suka) in the cooked recipe. Those are not typed ingredients.

## Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/v1/health` | Detector mode, class list, whether Gemini is configured |
| GET | `/v1/classes` | Ingredient names the model knows |
| POST | `/v1/detect` | Multipart `file` + `conf` query |
| POST | `/v1/recipes` | `{ "ingredients": ["Garlic"] }` |
| POST | `/v1/recipes/steps` | `{ "name": "Adobo", "ingredients": [...] }` |
