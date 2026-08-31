# How to add more ingredient classes later

Do not dump new photos into a random folder and overwrite `best.pt`.

1. Decide the class name (e.g. `Ginger`). Prefer visible raw items, not sauces.
2. Collect 100+ photos in real kitchens (cut, whole, in a bowl, with a hand).
3. Label them in Roboflow (or CVAT) **on top of the existing dataset**.
4. Generate a **frozen dataset version** (train/val/test split).
5. Train Ultralytics YOLO from the previous weights or a nano/small checkpoint.
6. Copy the new file to `api/weights/best.pt` (or upload to Hugging Face and we can wire download later).
7. Restart the API. `GET /v1/classes` and the camera chips update from the model.

The website does not need a code change when classes are added.
