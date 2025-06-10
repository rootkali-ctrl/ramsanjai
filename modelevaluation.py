from ultralytics import YOLO

# Load the trained model
model = YOLO("runs/obb/train/weights/best.pt")

# Perform validation on the entire dataset (uses data.yaml)
metrics = model.val(data="D:/Resume and Intern Documents/Bipolar Factory/Bike Helmet Detection.v1i.yolov8-obb/data.yaml")

# Print evaluation metrics
print("\n=== Evaluation Metrics ===")
print(f"mAP@0.5       : {metrics.box.map50:.4f}")
print(f"mAP@0.5:0.95  : {metrics.box.map:.4f}")
print(f"Precision     : {metrics.box.mp:.4f}")
print(f"Recall        : {metrics.box.mr:.4f}")
