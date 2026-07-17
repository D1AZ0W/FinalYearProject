from pathlib import Path

from ultralytics import YOLO
import os

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

DATA_PATH = str(PROJECT_ROOT / "config" / "coco128.yaml")
BASE_MODEL = str(PROJECT_ROOT / "weights" / "base" / "yolov8l.pt")
PROJECT_NAME = str(PROJECT_ROOT / "outputs" / "runs" / "helmet_train")
EPOCHS_PER_PHASE = 150
BATCH_SIZE = 8
IMAGE_SIZE = 640
INITIAL_LR = 0.001
LR_DECAY = 0.5
PHASES = 1
FREEZE_LAYERS = 5
PATIENCE = 0

model = YOLO(BASE_MODEL)
best_model_path = None
prev_best_f1 = 0.0
current_lr = INITIAL_LR

for phase in range(1, PHASES + 1):
    print(f"\n========== Phase {phase} Training ==========")
    run_name = f"phase{phase}_lr{current_lr:.4f}"
    freeze_layers = FREEZE_LAYERS if phase == 1 else 0

    results = model.train(
        data=DATA_PATH,
        epochs=EPOCHS_PER_PHASE,
        imgsz=IMAGE_SIZE,
        batch=BATCH_SIZE,
        lr0=current_lr,
        lrf=current_lr * 0.1,
        optimizer="AdamW",
        warmup_epochs=3,
        freeze=freeze_layers,
        project=PROJECT_NAME,
        name=run_name,
        patience=PATIENCE,
        verbose=True,
        pretrained=best_model_path or BASE_MODEL,
    )

    metrics = model.val(data=DATA_PATH)
    current_f1 = metrics.results_dict.get("metrics/precision(B)", 0.0)
    current_map = metrics.results_dict.get("metrics/mAP50(B)", 0.0)
    print(f"\n Phase {phase} Results:")
    print(f"  F1-score: {current_f1:.4f}")
    print(f"  mAP@0.5:  {current_map:.4f}")

    phase_best = os.path.join(PROJECT_NAME, run_name, "weights", "best.pt")
    if current_f1 > prev_best_f1:
        print(f"Improvement detected (ΔF1={current_f1 - prev_best_f1:.4f})")
        best_model_path = phase_best
        prev_best_f1 = current_f1
    else:
        current_lr *= LR_DECAY
        print(f"No improvement. Reducing LR to {current_lr:.6f}")

    if current_lr < 1e-5:
        print("Learning rate too low, stopping training.")
        break

print("\nTraining complete.")
print(f"Best model: {best_model_path}")
print(f"Best F1-score achieved: {prev_best_f1:.4f}")
