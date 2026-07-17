import os
from pathlib import Path

import cv2
import numpy as np
from sklearn.metrics import f1_score, precision_score, recall_score
from ultralytics import YOLO

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

model_path = PROJECT_ROOT / "outputs" / "runs" / "helmet_train" / "phase1_lr0.00104" / "weights" / "best.pt"
test_images_dir = PROJECT_ROOT / "data" / "train" / "images"
test_labels_dir = PROJECT_ROOT / "data" / "train" / "labels"
output_dir = PROJECT_ROOT / "outputs" / "predictions" / "test_results"

os.makedirs(output_dir, exist_ok=True)

model = YOLO(str(model_path))


def read_yolo_labels(label_path, img_width=640, img_height=640):
    boxes = []
    if os.path.exists(label_path):
        with open(label_path, "r") as f:
            for line in f:
                data = line.strip().split()
                if len(data) == 5:
                    class_id = int(data[0])
                    x_center = float(data[1]) * img_width
                    y_center = float(data[2]) * img_height
                    width = float(data[3]) * img_width
                    height = float(data[4]) * img_height

                    x1 = x_center - width / 2
                    y1 = y_center - height / 2
                    x2 = x_center + width / 2
                    y2 = y_center + height / 2

                    boxes.append({"class_id": class_id, "bbox": [x1, y1, x2, y2]})
    return boxes


def calculate_iou(box1, box2):
    x1_1, y1_1, x2_1, y2_1 = box1
    x1_2, y1_2, x2_2, y2_2 = box2

    xi1 = max(x1_1, x1_2)
    yi1 = max(y1_1, y1_2)
    xi2 = min(x2_1, x2_2)
    yi2 = min(y2_1, y2_2)

    inter_area = max(0, xi2 - xi1) * max(0, yi2 - yi1)

    box1_area = (x2_1 - x1_1) * (y2_1 - y1_1)
    box2_area = (x2_2 - x1_2) * (y2_2 - y1_2)
    union_area = box1_area + box2_area - inter_area

    return inter_area / union_area if union_area > 0 else 0


all_true_classes = []
all_pred_classes = []
class_names = ["with helmet", "without helmet", "rider", "number plate"]

for img_file in os.listdir(test_images_dir):
    if img_file.lower().endswith((".jpg", ".jpeg", ".png")):
        img_path = test_images_dir / img_file

        img = cv2.imread(str(img_path))
        if img is None:
            continue

        img_height, img_width = img.shape[:2]

        results_pred = model.predict(str(img_path), conf=0.25, iou=0.5)

        txt_file = test_labels_dir / f"{os.path.splitext(img_file)[0]}.txt"
        gt_boxes = read_yolo_labels(txt_file, img_width, img_height)

        pred_boxes = []
        if len(results_pred[0].boxes) > 0:
            for box in results_pred[0].boxes:
                pred_boxes.append({
                    "class_id": int(box.cls),
                    "bbox": box.xyxy[0].tolist(),
                    "conf": float(box.conf),
                })

        matched_gt = set()
        matched_pred = set()

        for i, gt_box in enumerate(gt_boxes):
            for j, pred_box in enumerate(pred_boxes):
                if j in matched_pred:
                    continue

                iou = calculate_iou(gt_box["bbox"], pred_box["bbox"])
                if iou > 0.5:
                    all_true_classes.append(gt_box["class_id"])
                    all_pred_classes.append(pred_box["class_id"])
                    matched_gt.add(i)
                    matched_pred.add(j)
                    break

        for j, pred_box in enumerate(pred_boxes):
            if j not in matched_pred:
                all_true_classes.append(-1)
                all_pred_classes.append(pred_box["class_id"])

        for i, gt_box in enumerate(gt_boxes):
            if i not in matched_gt:
                all_true_classes.append(gt_box["class_id"])
                all_pred_classes.append(-1)

        save_path = output_dir / img_file
        img_with_boxes = results_pred[0].plot()
        cv2.imwrite(str(save_path), img_with_boxes)

        print(f"Processed: {img_file} | GT: {len(gt_boxes)} | Pred: {len(pred_boxes)}")

valid_mask = (np.array(all_true_classes) != -1) & (np.array(all_pred_classes) != -1)
valid_true = np.array(all_true_classes)[valid_mask]
valid_pred = np.array(all_pred_classes)[valid_mask]

if len(valid_true) > 0:
    print("\n" + "=" * 50)
    print("PERFORMANCE METRICS")
    print("=" * 50)

    for class_id, class_name in enumerate(class_names):
        class_true = valid_true == class_id
        class_pred = valid_pred == class_id

        if np.any(class_true) or np.any(class_pred):
            precision = precision_score(class_true, class_pred, zero_division=0)
            recall = recall_score(class_true, class_pred, zero_division=0)
            f1 = f1_score(class_true, class_pred, zero_division=0)

            print(f"{class_name:15} | Precision: {precision:.3f} | Recall: {recall:.3f} | F1: {f1:.3f}")

    macro_precision = precision_score(valid_true, valid_pred, average="macro", zero_division=0)
    macro_recall = recall_score(valid_true, valid_pred, average="macro", zero_division=0)
    macro_f1 = f1_score(valid_true, valid_pred, average="macro", zero_division=0)

    print("-" * 50)
    print(f"{'OVERALL':15} | Precision: {macro_precision:.3f} | Recall: {macro_recall:.3f} | F1: {macro_f1:.3f}")

    true_positives = sum(1 for t, p in zip(all_true_classes, all_pred_classes) if t != -1 and p != -1 and t == p)
    false_positives = sum(1 for p in all_pred_classes if p != -1) - true_positives
    false_negatives = sum(1 for t in all_true_classes if t != -1) - true_positives

    print("\nDETECTION STATISTICS:")
    print(f"True Positives: {true_positives}")
    print(f"False Positives: {false_positives}")
    print(f"False Negatives: {false_negatives}")
else:
    print("No valid matches found!")

print(f"\nResults saved to: {output_dir}")
