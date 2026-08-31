from fastapi import APIRouter, HTTPException

from app.llm import generate_recipes, generate_steps, openai_configured
from app.schemas import RecipesRequest, RecipesResponse, StepsRequest, StepsResponse

router = APIRouter()


@router.post("/recipes", response_model=RecipesResponse)
def recipes(body: RecipesRequest) -> RecipesResponse:
    if not openai_configured():
        raise HTTPException(
            status_code=503,
            detail="OPENAI_API_KEY is not set. Add it to api/.env",
        )
    try:
        items = generate_recipes(body.ingredients)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Recipe generation failed: {exc}") from exc
    return RecipesResponse(recipes=items)


@router.post("/recipes/steps", response_model=StepsResponse)
def recipe_steps(body: StepsRequest) -> StepsResponse:
    if not openai_configured():
        raise HTTPException(
            status_code=503,
            detail="OPENAI_API_KEY is not set. Add it to api/.env",
        )
    if not body.name.strip():
        raise HTTPException(status_code=400, detail="Recipe name is required.")
    try:
        data = generate_steps(body.name.strip(), body.ingredients)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Recipe steps failed: {exc}") from exc
    return StepsResponse(**data)
