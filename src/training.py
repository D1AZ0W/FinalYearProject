from ultralytics import YOLO
import os 
# --- Paths ---
images_dir = "../data/train/images"        # folder with good images
txt_dir = "../data/train/labels"         # folder where all txt files are

# Get all image 
image_files = {os.path.splitext(f)[0] for f in os.listdir(images_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png'))}

# Loop through all txt files
for txt_file in os.listdir(txt_dir):
    if txt_file.lower().endswith('.txt'):
        txt_name = os.path.splitext(txt_file)[0]
        if txt_name not in image_files:
            file_path = os.path.join(txt_dir, txt_file)
            os.remove(file_path)
            print(f"Deleted: {txt_file}")

print("Cleanup complete! Only .txt files with corresponding images remain.")

# yolo model creation
model = YOLO("../weights/base/yolov8l.pt")
model.train(data="../config/coco128.yaml", imgsz=320, batch=4, epochs=20, workers=0, lr0 =0.001, lrf = 0.0001, optimizer = "AdamW")
model.save("../weights/trained/Train2nd.pt")

