from fastapi import APIRouter, HTTPException

from app.ingredients import canonicalize_ingredients
from app.llm import generate_recipes, generate_steps, llm_configured
from app.schemas import RecipesRequest, RecipesResponse, StepsRequest, StepsResponse

router = APIRouter()


@router.post("/recipes", response_model=RecipesResponse)
def recipes(body: RecipesRequest) -> RecipesResponse:
    if not llm_configured():
        raise HTTPException(
            status_code=503,
            detail="GEMINI_API_KEY is not set. Add it to api/.env",
        )
    ingredients = canonicalize_ingredients(body.ingredients)
    try:
        items = generate_recipes(ingredients)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Recipe generation failed: {exc}") from exc
    return RecipesResponse(recipes=items)


@router.post("/recipes/steps", response_model=StepsResponse)
def recipe_steps(body: StepsRequest) -> StepsResponse:
    if not llm_configured():
        raise HTTPException(
            status_code=503,
            detail="GEMINI_API_KEY is not set. Add it to api/.env",
        )
    if not body.name.strip():
        raise HTTPException(status_code=400, detail="Recipe name is required.")
    ingredients = canonicalize_ingredients(body.ingredients) if body.ingredients else []
    try:
        data = generate_steps(body.name.strip(), ingredients)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Recipe steps failed: {exc}") from exc
    return StepsResponse(**data)
