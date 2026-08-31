from fastapi import APIRouter, File, HTTPException, Query, UploadFile

from app.ml.model import class_names, detect_image, detector_mode
from app.schemas import DetectResponse

router = APIRouter()


@router.get("/classes")
def get_classes() -> dict[str, list[str]]:
    return {"classes": class_names()}


@router.post("/detect", response_model=DetectResponse)
async def detect(
    file: UploadFile = File(...),
    conf: float = Query(0.5, ge=0.0, le=1.0),
) -> DetectResponse:
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Upload an image file.")

    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Empty image.")

    try:
        result = detect_image(data, conf)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Detection failed: {exc}") from exc

    if detector_mode() == "mock":
        result["mode"] = "mock"
    return DetectResponse(**result)
