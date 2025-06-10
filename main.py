from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import base64
from io import BytesIO
from PIL import Image
import numpy as np
import cv2
import os
import tempfile
from ultralytics import YOLO
import supervision as sv

app = FastAPI()

# Enable CORS for React app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load YOLO model (update path as needed)
try:
    model = YOLO('runs/obb/train/weights/best.pt')
    CLASS_NAMES = ["With Helmet", "Without Helmet"]
    model_loaded = True
    print("YOLO model loaded successfully!")
except Exception as e:
    print(f"Error loading YOLO model: {e}")
    model_loaded = False
    model = None

def detect_objects_yolo(image_array):
    """
    YOLO detection function using the trained model
    """
    if not model_loaded:
        return {"error": "YOLO model not loaded"}
    
    try:
        # Convert numpy array to PIL Image if needed
        if isinstance(image_array, np.ndarray):
            # Convert RGB to BGR for OpenCV
            if len(image_array.shape) == 3 and image_array.shape[2] == 3:
                image_bgr = cv2.cvtColor(image_array, cv2.COLOR_RGB2BGR)
            else:
                image_bgr = image_array
        else:
            image_bgr = image_array
        
        # Run detection
        results = model(image_bgr)
        
        # Process detections
        detections = sv.Detections.from_ultralytics(results[0])
        
        # Convert detections to the format expected by frontend
        detection_list = []
        
        if len(detections) > 0:
            for i in range(len(detections)):
                # Get bounding box coordinates
                x1, y1, x2, y2 = detections.xyxy[i]
                
                # Get class ID and confidence
                class_id = int(detections.class_id[i])
                confidence = float(detections.confidence[i])
                
                # Get label
                label = CLASS_NAMES[class_id] if class_id < len(CLASS_NAMES) else f"Class_{class_id}"
                
                detection_list.append({
                    "label": label,
                    "confidence": confidence,
                    "box": {
                        "x": int(x1),
                        "y": int(y1),
                        "width": int(x2 - x1),
                        "height": int(y2 - y1)
                    }
                })
        
        return {"detections": detection_list}
        
    except Exception as e:
        return {"error": f"Detection failed: {str(e)}"}

def detect_objects_simple(image_array):
    """
    Fallback mock detection function when YOLO model is not available
    """
    import random
    
    # Mock detections
    mock_objects = ['With Helmet', 'Without Helmet']
    
    detections = []
    num_detections = random.randint(0, 3)
    
    for i in range(num_detections):
        detections.append({
            "label": random.choice(mock_objects),
            "confidence": round(random.uniform(0.5, 0.95), 2),
            "box": {
                "x": random.randint(50, 200),
                "y": random.randint(50, 150),
                "width": random.randint(80, 150),
                "height": random.randint(80, 150)
            }
        })
    
    return {"detections": detections}

@app.get("/")
async def root():
    status = "YOLO model loaded" if model_loaded else "Using mock detection (YOLO model not found)"
    return {"message": f"Object Detection API is running! Status: {status}"}

@app.post("/api/detect-base64")
async def detect_objects_base64(data: dict):
    """
    Detect objects from base64 encoded image (for camera input)
    """
    try:
        # Decode base64 image
        image_data = base64.b64decode(data["image"].split(",")[1])
        image = Image.open(BytesIO(image_data))
        image_array = np.array(image)
        
        # Use YOLO detection if available, otherwise fallback to simple detection
        if model_loaded:
            result = detect_objects_yolo(image_array)
        else:
            result = detect_objects_simple(image_array)
            
        return result
        
    except Exception as e:
        return {"error": str(e)}

@app.post("/api/detect-upload")
async def detect_objects_upload(file: UploadFile = File(...)):
    """
    Detect objects from uploaded image file
    """
    try:
        # Validate file type
        if not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Read uploaded file
        contents = await file.read()
        
        # Convert to PIL Image
        image = Image.open(BytesIO(contents))
        
        # Convert to numpy array
        image_array = np.array(image)
        
        # Use YOLO detection if available, otherwise fallback to simple detection
        if model_loaded:
            result = detect_objects_yolo(image_array)
        else:
            result = detect_objects_simple(image_array)
        
        # Add image dimensions to result
        result["image_info"] = {
            "width": image.width,
            "height": image.height,
            "filename": file.filename
        }
        
        return result
        
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/status")
async def get_status():
    return {
        "status": "running",
        "model": "YOLO OBB" if model_loaded else "mock_detector",
        "model_loaded": model_loaded,
        "classes": CLASS_NAMES if model_loaded else ["Mock classes"],
        "message": "YOLO model active" if model_loaded else "YOLO model not found - using mock detection"
    }

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "model_status": "loaded" if model_loaded else "not_loaded"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)