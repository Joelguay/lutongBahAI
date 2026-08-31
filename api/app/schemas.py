from pydantic import BaseModel, Field


class Box(BaseModel):
    name: str
    conf: float
    xyxy: list[float]


class DetectResponse(BaseModel):
    mode: str
    ingredients: list[str]
    boxes: list[Box]


class HealthResponse(BaseModel):
    ok: bool
    detector: str
    classes: list[str]
    openai_configured: bool


class RecipeItem(BaseModel):
    name: str
    description: str


class RecipesRequest(BaseModel):
    ingredients: list[str] = Field(min_length=1)


class RecipesResponse(BaseModel):
    recipes: list[RecipeItem]


class RecipeStep(BaseModel):
    title: str
    detail: str


class StepsRequest(BaseModel):
    name: str
    ingredients: list[str] = Field(default_factory=list)


class StepsResponse(BaseModel):
    name: str
    servings: str
    allergens: str
    ingredients: list[str]
    steps: list[RecipeStep]
    notes: list[str]
    reference: str = ""
