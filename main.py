from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import base64
from io import BytesIO
from PIL import Image
import numpy as np
import os

app = FastAPI()

# Enable CORS for React app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for deployment
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Simple mock detection function
def detect_objects_simple(image_array):
    import random
    
    mock_objects = ['person', 'car', 'dog', 'cat', 'bicycle', 'bottle', 'phone', 'laptop', 'book', 'chair']
    
    detections = []
    num_detections = random.randint(1, 4)  # Always detect at least 1 object
    
    for i in range(num_detections):
        detections.append({
            "label": random.choice(mock_objects),
            "confidence": round(random.uniform(0.6, 0.95), 2),
            "box": {
                "x": random.randint(50, 300),
                "y": random.randint(50, 200),
                "width": random.randint(80, 200),
                "height": random.randint(80, 200)
            }
        })
    
    return {"detections": detections}

# API routes
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
        return {"error": str(e), "detections": []}

@app.get("/api/status")
async def get_status():
    return {
        "status": "running",
        "model": "simple_mock_detector",
        "message": "Mock detector is working!"
    }

@app.get("/api")
async def api_root():
    return {"message": "Object Detection API is running!"}

# Serve React static files
if os.path.exists("build"):
    app.mount("/static", StaticFiles(directory="build/static"), name="static")
    
    # Handle all other routes (for React Router)
    @app.get("/{catchall:path}")
    async def serve_react_app(catchall: str):
        # Don't serve React for API routes
        if catchall.startswith("api"):
            return {"error": "API route not found"}
        
        # Check if it's a static file
        file_path = f"build/{catchall}"
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return FileResponse(file_path)
        
        # Otherwise serve React app
        return FileResponse("build/index.html")

# Serve React app at root
@app.get("/")
async def serve_react_root():
    if os.path.exists("build/index.html"):
        return FileResponse("build/index.html")
    return {"message": "React build not found. API is running at /api"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
    
