from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
import base64
from io import BytesIO
from PIL import Image
import numpy as np

app = FastAPI()

# Enable CORS for React app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Simple mock detection function (replace with actual model)
def detect_objects_simple(image_array):
    """
    Mock detection function - replace this with your actual model
    For now, it returns random detections for demo purposes
    """
    import random
    
    # Mock detections
    mock_objects = ['person', 'car', 'dog', 'cat', 'bicycle', 'bottle', 'phone']
    
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
    return {"message": "Object Detection API is running! (Simple version without OpenCV)"}

@app.post("/api/detect-base64")
async def detect_objects_base64(data: dict):
    try:
        # Decode base64 image
        image_data = base64.b64decode(data["image"].split(",")[1])
        image = Image.open(BytesIO(image_data))
        image_array = np.array(image)
        
        # Simple detection (replace with actual model)
        result = detect_objects_simple(image_array)
        return result
        
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/status")
async def get_status():
    return {
        "status": "running",
        "model": "simple_mock_detector",
        "message": "Install opencv-python for full YOLO support"
    }

if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)