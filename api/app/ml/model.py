from __future__ import annotations

import logging
from typing import Any

from app.config import DEFAULT_CLASSES, weights_path

logger = logging.getLogger(__name__)

_model: Any = None
_mode = "mock"


def detector_mode() -> str:
    return _mode


def class_names() -> list[str]:
    if _model is not None:
        return [str(name) for name in _model.names.values()]
    return list(DEFAULT_CLASSES)


def init_model() -> None:
    global _model, _mode
    path = weights_path()
    if not path.exists():
        _model = None
        _mode = "mock"
        logger.warning(
            "No weights at %s — detect() will return empty results. "
            "Drop best.pt there when you have it.",
            path,
        )
        return

    from ultralytics import YOLO

    _model = YOLO(str(path))
    _mode = "yolo"
    logger.info("Loaded YOLO weights from %s", path)


def detect_image(image_bytes: bytes, conf: float) -> dict[str, Any]:
    if _model is None:
        return {"mode": "mock", "ingredients": [], "boxes": []}

    import cv2
    import numpy as np

    arr = np.frombuffer(image_bytes, dtype=np.uint8)
    frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if frame is None:
        raise ValueError("Could not decode image")

    height, width = frame.shape[:2]
    results = _model.predict(frame, conf=conf, verbose=False, imgsz=640)
    result = results[0] if isinstance(results, (list, tuple)) else results

    names: set[str] = set()
    boxes: list[dict[str, Any]] = []
    if result is not None and getattr(result, "boxes", None) is not None:
        for box in result.boxes:
            cls_id = int(box.cls[0])
            name = str(_model.names.get(cls_id, cls_id))
            score = float(box.conf[0])
            x1, y1, x2, y2 = [float(v) for v in box.xyxy[0]]
            names.add(name)
            boxes.append(
                {
                    "name": name,
                    "conf": round(score, 3),
                    "xyxy": [
                        round(x1 / width, 4),
                        round(y1 / height, 4),
                        round(x2 / width, 4),
                        round(y2 / height, 4),
                    ],
                }
            )

    return {
        "mode": "yolo",
        "ingredients": sorted(names),
        "boxes": boxes,
    }
