import logging
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import frontend_origins
from app.ingredients import display_class_names
from app.llm import llm_configured
from app.ml.model import detector_mode, init_model
from app.routers import detect, recipes
from app.schemas import HealthResponse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

init_model()

app = FastAPI(title="LutongBahAI API", version="2.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=frontend_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(detect.router, prefix="/v1")
app.include_router(recipes.router, prefix="/v1")


@app.get("/v1/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(
        ok=True,
        detector=detector_mode(),
        classes=display_class_names(),
        llm_configured=llm_configured(),
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "8000")),
        reload=True,
    )
