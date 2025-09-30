import os
import cv2
import torch
import json
import argparse
import warnings
from datetime import datetime

# Suppress noisy warnings from PyTorch/YOLOv5 with newer Torch versions
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings(
    "ignore",
    category=UserWarning,
    message=r"pkg_resources is deprecated as an API.*",
)


# Load YOLOv5 model
def load_model(model_path: str, device: str | None = None):
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model path '{model_path}' does not exist.")
    # Use torch.hub to load YOLOv5 model
    # Resolve local yolov5 directory relative to this file
    repo_path = os.path.join(os.path.dirname(__file__), "yolov5")
    model = torch.hub.load(
        repo_path,
        "custom",
        path=model_path,
        source="local",
        device=device or ("cuda" if torch.cuda.is_available() else "cpu"),
    )
    return model


# Open webcam or video/image file
def open_source(source: str | int):
    # Accept formats: "usb0", "0", 0, video path
    cap = None
    if isinstance(source, int) or (isinstance(source, str) and source.isdigit()):
        cap = cv2.VideoCapture(int(source))
    elif isinstance(source, str) and source.lower().startswith("usb"):
        idx = int(source[3:]) if len(source) > 3 else 0
        cap = cv2.VideoCapture(idx)
    else:
        cap = cv2.VideoCapture(source)

    if not cap.isOpened():
        raise ValueError(f"Could not open source: {source}")
    return cap


# Save image and run detection on it, return detected object names and save as .txt
def GetCaptureObjectAPI(model, image, save_dir: str = "captured"):
    os.makedirs(save_dir, exist_ok=True)

    # Use timestamp for unique naming
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    image_filename = f"capture_{timestamp}.jpg"
    image_path = os.path.join(save_dir, image_filename)

    # Save the image
    cv2.imwrite(image_path, image)

    # Run detection
    results = model(image)
    names = model.names

    detected = set()
    preds = results.xyxy[0].cpu().numpy()
    for *_, conf, cls in preds:
        if conf > 0.5:
            detected.add(names[int(cls)])

    json_data = {"Detected Objects": list(detected)}

    # Save JSON to .txt file
    txt_filename = f"capture_{timestamp}.txt"
    txt_path = os.path.join(save_dir, txt_filename)
    with open(txt_path, "w") as f:
        f.write(json.dumps(json_data, indent=2))

    return json_data


# Main detection loop with 'P' to capture
def detect_and_display(
    model, cap, window_title: str = "YOLOv5 Detection - Press 'P' to capture"
):
    while True:
        ret, frame = cap.read()
        if not ret:
            print("No frame captured, ending detection.")
            break

        results = model(frame)
        # Render returns a list of annotated images (BGR)
        rendered_list = results.render()
        annotated_frame = rendered_list[0] if rendered_list else frame

        cv2.imshow(window_title, annotated_frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):  # press q for exit
            break
        elif key == ord("p"):
            print(" Capturing frame and running object detection...")
            json_result = GetCaptureObjectAPI(model, frame)
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
    args = parser.parse_args()

    model = load_model(args.weights)

    # Set confidence for Ultralytics autoshape models if available
    if hasattr(model, "conf"):
        model.conf = float(args.conf)

    cap = open_source(args.source)
    detect_and_display(model, cap)


if __name__ == "__main__":
    main()
