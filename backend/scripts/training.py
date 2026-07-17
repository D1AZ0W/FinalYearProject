import os
from pathlib import Path

from ultralytics import YOLO

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

images_dir = PROJECT_ROOT / "data" / "train" / "images"
txt_dir = PROJECT_ROOT / "data" / "train" / "labels"

image_files = {
    os.path.splitext(f)[0]
    for f in os.listdir(images_dir)
    if f.lower().endswith((".jpg", ".jpeg", ".png"))
}

for txt_file in os.listdir(txt_dir):
    if txt_file.lower().endswith(".txt"):
        txt_name = os.path.splitext(txt_file)[0]
        if txt_name not in image_files:
            file_path = txt_dir / txt_file
            os.remove(file_path)
            print(f"Deleted: {txt_file}")

print("Cleanup complete! Only .txt files with corresponding images remain.")

model = YOLO(str(PROJECT_ROOT / "weights" / "base" / "yolov8l.pt"))
model.train(
    data=str(PROJECT_ROOT / "config" / "coco128.yaml"),
    imgsz=320,
    batch=4,
    epochs=20,
    workers=0,
    lr0=0.001,
    lrf=0.0001,
    optimizer="AdamW",
)
model.save(str(PROJECT_ROOT / "weights" / "trained" / "Train2nd.pt"))
