from asyncio.log import logger
import os
import cv2
import torch
import json
import argparse
import warnings
from datetime import datetime
import numpy as np

# Suppress noisy warnings from PyTorch/YOLOv5 with newer Torch versions
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings(
    "ignore",
    category=UserWarning,
    message=r"pkg_resources is deprecated as an API.*",
)


# # Load YOLOv5 model
# def load_model(model_path: str, device: str | None = None):
#     if not os.path.exists(model_path):
#         raise FileNotFoundError(f"Model path '{model_path}' does not exist.")
#     # Use torch.hub to load YOLOv5 model
#     # Resolve local yolov5 directory relative to this file
#     repo_path = os.path.join(os.path.dirname(__file__), "yolov5")
#     model = torch.hub.load(
#         repo_path,
#         "custom",
#         path=model_path,
#         source="local",
#         device=device or ("cuda" if torch.cuda.is_available() else "cpu"),
#     )
#     return model

# --- YOLO Model Loading ---
try:
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    
    # Load Ultralytics YOLO model (since the weights contain ultralytics.nn.tasks.DetectionModel)
    from ultralytics import YOLO
    yolo_model = YOLO('./train/weights/best.pt')
    yolo_model.to(device)
    logger.info(f"Ultralytics YOLO model loaded successfully on device: {device}.")
        
except Exception as e:
    logger.error(f"Error loading YOLO model: {e}")
    yolo_model = None

# Open webcam or video/image file
def open_source(source: str | int, backend: str | None = None, width: int | None = 640, height: int | None = 480):
    # Accept formats: "usb0", "0", 0, video path
    cap = None
    api = None
    b = (backend or "").strip().lower()
    if b == "dshow":
        api = cv2.CAP_DSHOW
    elif b == "msmf":
        api = cv2.CAP_MSMF

    if isinstance(source, int) or (isinstance(source, str) and source.isdigit()):
        idx = int(source)
        cap = cv2.VideoCapture(idx, api) if api is not None else cv2.VideoCapture(idx)
    elif isinstance(source, str) and source.lower().startswith("usb"):
        idx = int(source[3:]) if len(source) > 3 else 0
        cap = cv2.VideoCapture(idx, api) if api is not None else cv2.VideoCapture(idx)
    else:
        cap = cv2.VideoCapture(source)

    if not cap.isOpened():
        raise ValueError(f"Could not open source: {source}")
    try:
        if width:
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, int(width))
        if height:
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, int(height))
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    except Exception:
        pass
    return cap


# Save image and run detection on it, return detected object names and save as .txt
def GetCaptureObjectAPI(model, image, save_dir: str = "captured", conf_threshold: float = 0.7):
    os.makedirs(save_dir, exist_ok=True)

    # Use timestamp for unique naming
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    image_filename = f"capture_{timestamp}.jpg"
    image_path = os.path.join(save_dir, image_filename)

    # Save the image
    cv2.imwrite(image_path, image)

    # Load trained classes from classes.txt
    trained_class_ids = None
    classes_path = os.path.join(os.path.dirname(__file__), 'classes.txt')
    try:
        with open(classes_path, 'r', encoding='utf-8') as cf:
            trained_class_names = {ln.strip().lower() for ln in cf if ln.strip()}
        
        # Map class names to IDs
        names = getattr(model, 'names', {})
        model_names_lower = {name.lower(): cls_id for cls_id, name in names.items()}
        trained_class_ids = [model_names_lower[name] for name in trained_class_names if name in model_names_lower]
        
        if trained_class_ids:
            print(f"Filtering to {len(trained_class_ids)} trained classes")
    except Exception as e:
        print(f"Could not load classes.txt: {e}")
        trained_class_ids = None

    # Run detection with class filtering. Ultralytics model(...) may return a Results object or a list of Results.
    if trained_class_ids:
        raw_results = model(image, classes=trained_class_ids, conf=conf_threshold)
    else:
        raw_results = model(image, conf=conf_threshold)
    
    # Normalize to a single Results-like object
    results = raw_results[0] if isinstance(raw_results, (list, tuple)) and raw_results else raw_results
    names = getattr(model, 'names', {})


    # Use model.conf if available; fallback to 0.5
    try:
        threshold = float(getattr(model, "conf", 0.5))
    except Exception:
        threshold = 0.5

    # Filter detections below threshold BEFORE counting and rendering
    try:
        det = results.xyxy[0]
        if hasattr(det, 'cpu'):
            mask = det[:, 4] >= threshold
            results.xyxy[0] = det[mask]
            filtered = results.xyxy[0].cpu().numpy()
        else:
            import numpy as _np
            mask = det[:, 4] >= threshold
            results.xyxy[0] = det[mask]
            filtered = results.xyxy[0]
    except Exception:
        filtered = results.xyxy[0].cpu().numpy()

    detected = set()
    try:
        # Prefer structured access (xyxy) when available
        preds = getattr(results, 'xyxy', None)
        if preds is None:
            # Some versions expose .boxes with numpy conversion
            preds = getattr(results, 'boxes', None)
            if preds is not None and hasattr(preds, 'xyxy'):
                preds = preds.xyxy

        # preds expected to be indexable like preds[0]
        if preds is not None:
            arr = preds[0].cpu().numpy() if hasattr(preds[0], 'cpu') else preds[0]
            for *_, conf, cls in arr:
                try:
                    cls = int(cls)
                    label = names.get(cls, str(cls)).strip()
                    # Since we already filtered during prediction, just add all detections
                    if float(conf) >= conf_threshold:
                        detected.add(label)
                except Exception:
                    continue
    except Exception:
        # If anything goes wrong, fall back to empty detection set
        detected = set()

    json_data = {"Detected Objects": list(detected)}

    # Save JSON to .txt file
    txt_filename = f"capture_{timestamp}.txt"
    txt_path = os.path.join(save_dir, txt_filename)
    with open(txt_path, "w") as f:
        f.write(json.dumps(json_data, indent=2))

    return json_data


# Main detection loop with 'P' to capture
def detect_and_display(
    model, cap, window_title: str = "YOLOv5 Detection - Press 'P' to capture", conf_threshold: float = 0.7
):
    # Load trained classes for filtering during display
    trained_class_ids = None
    classes_path = os.path.join(os.path.dirname(__file__), 'classes.txt')
    try:
        with open(classes_path, 'r', encoding='utf-8') as cf:
            trained_class_names = {ln.strip().lower() for ln in cf if ln.strip()}
        names = getattr(model, 'names', {})
        model_names_lower = {name.lower(): cls_id for cls_id, name in names.items()}
        trained_class_ids = [model_names_lower[name] for name in trained_class_names if name in model_names_lower]
    except Exception:
        trained_class_ids = None

    while True:
        ret, frame = cap.read()
        if not ret:
            print("No frame captured, ending detection.")
            break

        # Run detection with class filtering if classes are specified
        if trained_class_ids:
            raw_results = model(frame, classes=trained_class_ids, conf=conf_threshold, verbose=False)
        else:
            raw_results = model(frame, conf=conf_threshold, verbose=False)
        # Normalize the results to a single Results-like object
        results = raw_results[0] if isinstance(raw_results, (list, tuple)) and raw_results else raw_results

        # Render may be available on Results (older yolov5 API) or Results.render() may return a list
        annotated_frame = frame
        try:
            if hasattr(results, 'render'):
                rendered_list = results.render()
                annotated_frame = rendered_list[0] if rendered_list else frame
            elif hasattr(results, 'plot'):
                # Ultralytics Results.plot() returns an image
                annotated_frame = results.plot()
        except Exception:
            annotated_frame = frame

        cv2.imshow(window_title, annotated_frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):  # press q for exit
            break
        elif key == ord("p"):
            print(f" Capturing frame and running object detection with confidence threshold: {conf_threshold}...")
            json_result = GetCaptureObjectAPI(model, frame, conf_threshold=conf_threshold)
            print(" Detection Result Saved:\n", json.dumps(json_result, indent=2))

    cap.release()
    cv2.destroyAllWindows()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--weights",
        default=os.path.join(os.path.dirname(__file__), "train", "weights", "best.pt"),
        help="Path to model weights (.pt)",
    )
    parser.add_argument(
        "--source",
        default="0",
        help="Source: webcam index (e.g., '0' or 'usb0') or path to image/video",
    )
    parser.add_argument(
        "--conf",
        type=float,
        default=0.5,
        help="Confidence threshold for display and capture filtering",
    )
    parser.add_argument(
        "--backend",
        choices=["dshow", "msmf", "default"],
        default="dshow",
        help="Camera backend to use on Windows",
    )
    parser.add_argument(
        "--width",
        type=int,
        default=640,
        help="Capture width",
    )
    parser.add_argument(
        "--height",
        type=int,
        default=480,
        help="Capture height",
    )
    args = parser.parse_args()

    # Prevent accidentally using the weights path as the inference source.
    # If we preloaded a model instance at module import (yolo_model), use it.
    # Otherwise create a new YOLO instance from the provided weights path.
    if yolo_model is not None:
        model = yolo_model
    else:
        from ultralytics import YOLO as _YOLO
        model = _YOLO(args.weights)

    # Set confidence for Ultralytics autoshape models if available
    if hasattr(model, "conf"):
        try:
            model.conf = float(args.conf)
        except Exception:
            pass

    print(f"Using confidence threshold: {args.conf}")
    cap = open_source(args.source)
    detect_and_display(model, cap, conf_threshold=float(args.conf))


if __name__ == "__main__":
    main()
