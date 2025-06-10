from ultralytics import YOLO

model = YOLO('runs/obb/train/weights/best.pt')

import os
import random

random_file = random.choice(os.listdir("train/images"))
file_name = os.path.join("train/images", random_file)

results = model(file_name)

import supervision as sv
import cv2

detections = sv.Detections.from_ultralytics(results[0])
CLASS_NAMES = [
    "With Helmet", "Without Helmet"
]
labels = [CLASS_NAMES[class_id] for class_id in detections.class_id]
print(labels)
ObjectboundAnnotator = sv.OrientedBoxAnnotator()
label_annotator = sv.LabelAnnotator()

image = cv2.imread(file_name)

annotated_frame = ObjectboundAnnotator.annotate(
    scene=image,
    detections=detections
)
# Draw labels on top of oriented boxes
annotated_frame = label_annotator.annotate(
    scene=annotated_frame,
    detections=detections,
    labels=labels
)


sv.plot_image(image=annotated_frame, size=(16, 16))