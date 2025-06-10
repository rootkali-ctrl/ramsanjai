from ultralytics import YOLO
import os
import random
import supervision as sv
import cv2

# Load YOLO model
model = YOLO('runs/obb/train/weights/best.pt')

# Get input from user
user_input = input("Enter full path to an image or type 'random' to pick a random training image: ").strip()

# Handle image selection
if user_input.lower() == "random":
    image_dir = r"/train/images"
    image_list = os.listdir(image_dir)
    
    if not image_list:
        raise FileNotFoundError("No images found in the specified directory.")
    
    random_file = random.choice(image_list)
    file_name = os.path.join(image_dir, random_file)
    print(f"Randomly selected image: {file_name}")
else:
    if not os.path.exists(user_input):
        raise FileNotFoundError(f"The specified file does not exist: {user_input}")
    file_name = user_input

# Run detection
results = model(file_name)

# Process detections
detections = sv.Detections.from_ultralytics(results[0])
CLASS_NAMES = ["With Helmet", "Without Helmet"]
labels = [CLASS_NAMES[class_id] for class_id in detections.class_id]
print("Detected labels:", labels)

# Annotate image
ObjectboundAnnotator = sv.OrientedBoxAnnotator()
label_annotator = sv.LabelAnnotator()
image = cv2.imread(file_name)

annotated_frame = ObjectboundAnnotator.annotate(scene=image, detections=detections)
annotated_frame = label_annotator.annotate(scene=annotated_frame, detections=detections, labels=labels)

# Show image
sv.plot_image(image=annotated_frame, size=(16, 16))
