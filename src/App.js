import React, { useState, useRef, useEffect } from 'react';

function App() {
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const fileInputRef = useRef(null);
  const uploadCanvasRef = useRef(null);
  
  const [detections, setDetections] = useState([]);
  const [uploadDetections, setUploadDetections] = useState([]);
  const [isDetecting, setIsDetecting] = useState(false);
  const [isUploadDetecting, setIsUploadDetecting] = useState(false);
  const [cameraActive, setCameraActive] = useState(false);
  const [error, setError] = useState('');
  const [uploadedImage, setUploadedImage] = useState(null);
  const [activeTab, setActiveTab] = useState('camera'); // 'camera' or 'upload'

  // Start camera
  const startCamera = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ 
        video: { width: 640, height: 480 } 
      });
      videoRef.current.srcObject = stream;
      setCameraActive(true);
      setError('');
    } catch (err) {
      setError('Error accessing camera: ' + err.message);
    }
  };

  // Stop camera
  const stopCamera = () => {
    if (videoRef.current && videoRef.current.srcObject) {
      const tracks = videoRef.current.srcObject.getTracks();
      tracks.forEach(track => track.stop());
      videoRef.current.srcObject = null;
    }
    setCameraActive(false);
  };

  // Capture frame and detect objects (Camera)
  const detectObjects = async () => {
    if (!videoRef.current || !canvasRef.current) return;

    setIsDetecting(true);
    
    const canvas = canvasRef.current;
    const context = canvas.getContext('2d');
    
    // Set canvas size to match video
    canvas.width = videoRef.current.videoWidth;
    canvas.height = videoRef.current.videoHeight;
    
    // Draw current video frame to canvas
    context.drawImage(videoRef.current, 0, 0, canvas.width, canvas.height);
    
    // Convert canvas to base64
    const imageData = canvas.toDataURL('image/jpeg');
    
    try {
      const response = await fetch('http://localhost:8000/api/detect-base64', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ image: imageData }),
      });
      
      const result = await response.json();
      
      if (result.error) {
        setError(result.error);
      } else {
        setDetections(result.detections || []);
        setError('');
      }
    } catch (err) {
      setError('Error detecting objects: ' + err.message);
    }
    
    setIsDetecting(false);
  };

  // Handle file upload
  const handleFileUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    // Validate file type
    if (!file.type.startsWith('image/')) {
      setError('Please select an image file');
      return;
    }

    setIsUploadDetecting(true);
    setError('');

    try {
      // Create FormData for file upload
      const formData = new FormData();
      formData.append('file', file);

      // Send to backend
      const response = await fetch('http://localhost:8000/api/detect-upload', {
        method: 'POST',
        body: formData,
      });

      const result = await response.json();

      if (result.error) {
        setError(result.error);
      } else {
        setUploadDetections(result.detections || []);
        
        // Display uploaded image
        const reader = new FileReader();
        reader.onload = (e) => {
          setUploadedImage({
            src: e.target.result,
            width: result.image_info?.width || 0,
            height: result.image_info?.height || 0,
            filename: result.image_info?.filename || file.name
          });
        };
        reader.readAsDataURL(file);
        
        setError('');
      }
    } catch (err) {
      setError('Error uploading and detecting: ' + err.message);
    }

    setIsUploadDetecting(false);
  };

  // Draw bounding boxes on camera canvas
  const drawBoundingBoxes = () => {
    if (!canvasRef.current || detections.length === 0) return;

    const canvas = canvasRef.current;
    const context = canvas.getContext('2d');
    
    // Clear previous drawings
    context.clearRect(0, 0, canvas.width, canvas.height);
    
    // Draw current video frame
    context.drawImage(videoRef.current, 0, 0, canvas.width, canvas.height);
    
    // Draw bounding boxes
    detections.forEach((detection, index) => {
      const { box, label, confidence } = detection;
      
      // Set box style
      context.strokeStyle = '#00ff00';
      context.lineWidth = 2;
      context.fillStyle = '#00ff00';
      context.font = '16px Arial';
      
      // Draw rectangle
      context.strokeRect(box.x, box.y, box.width, box.height);
      
      // Draw label background
      const text = `${label} (${(confidence * 100).toFixed(1)}%)`;
      const textWidth = context.measureText(text).width;
      context.fillRect(box.x, box.y - 25, textWidth + 10, 20);
      
      // Draw label text
      context.fillStyle = '#000000';
      context.fillText(text, box.x + 5, box.y - 10);
    });
  };

  // Draw bounding boxes on uploaded image canvas
  const drawUploadBoundingBoxes = () => {
    if (!uploadCanvasRef.current || !uploadedImage || uploadDetections.length === 0) return;

    const canvas = uploadCanvasRef.current;
    const context = canvas.getContext('2d');
    const img = new Image();
    
    img.onload = () => {
      // Set canvas size to match image
      canvas.width = img.width;
      canvas.height = img.height;
      
      // Draw image
      context.drawImage(img, 0, 0);
      
      // Draw bounding boxes
      uploadDetections.forEach((detection, index) => {
        const { box, label, confidence } = detection;
        
        // Set box style
        context.strokeStyle = '#ff0000';
        context.lineWidth = 3;
        context.fillStyle = '#ff0000';
        context.font = '16px Arial';
        
        // Draw rectangle
        context.strokeRect(box.x, box.y, box.width, box.height);
        
        // Draw label background
        const text = `${label} (${(confidence * 100).toFixed(1)}%)`;
        const textWidth = context.measureText(text).width;
        context.fillRect(box.x, box.y - 25, textWidth + 10, 20);
        
        // Draw label text
        context.fillStyle = '#ffffff';
        context.fillText(text, box.x + 5, box.y - 10);
      });
    };
    
    img.src = uploadedImage.src;
  };

  // Update canvas with bounding boxes when detections change
  useEffect(() => {
    if (cameraActive && detections.length > 0) {
      drawBoundingBoxes();
    }
  }, [detections, cameraActive]);

  // Update upload canvas when upload detections change
  useEffect(() => {
    if (uploadedImage && uploadDetections.length > 0) {
      drawUploadBoundingBoxes();
    }
  }, [uploadDetections, uploadedImage]);

  // Auto-detect objects every 2 seconds when camera is active
  useEffect(() => {
    let interval;
    if (cameraActive && activeTab === 'camera') {
      interval = setInterval(() => {
        if (!isDetecting) {
          detectObjects();
        }
      }, 2000);
    }
    return () => clearInterval(interval);
  }, [cameraActive, isDetecting, activeTab]);

  const tabStyle = (isActive) => ({
    padding: '10px 20px',
    backgroundColor: isActive ? '#007bff' : '#6c757d',
    color: 'white',
    border: 'none',
    borderRadius: '4px 4px 0 0',
    marginRight: '5px',
    cursor: 'pointer'
  });

  return (
    <div style={{ padding: '20px', fontFamily: 'Arial, sans-serif' }}>
      <h1>Helmet Detection System</h1>
      
      {error && (
        <div style={{ 
          color: 'red', 
          backgroundColor: '#ffe6e6', 
          padding: '10px', 
          borderRadius: '4px',
          margin: '10px 0'
        }}>
          {error}
        </div>
      )}

      {/* Tab Navigation */}
      <div style={{ marginBottom: '20px' }}>
        <button 
          onClick={() => setActiveTab('camera')}
          style={tabStyle(activeTab === 'camera')}
        >
          Camera Detection
        </button>
        <button 
          onClick={() => setActiveTab('upload')}
          style={tabStyle(activeTab === 'upload')}
        >
          Image Upload
        </button>
      </div>

      {/* Camera Tab */}
      {activeTab === 'camera' && (
        <div>
          <div style={{ marginBottom: '20px' }}>
            {!cameraActive ? (
              <button 
                onClick={startCamera}
                style={{ 
                  padding: '10px 20px', 
                  backgroundColor: '#28a745', 
                  color: 'white', 
                  border: 'none', 
                  borderRadius: '4px',
                  marginRight: '10px'
                }}
              >
                Start Camera
              </button>
            ) : (
              <button 
                onClick={stopCamera}
                style={{ 
                  padding: '10px 20px', 
                  backgroundColor: '#dc3545', 
                  color: 'white', 
                  border: 'none', 
                  borderRadius: '4px',
                  marginRight: '10px'
                }}
              >
                Stop Camera
              </button>
            )}
            
            <button 
              onClick={detectObjects}
              disabled={!cameraActive || isDetecting}
              style={{ 
                padding: '10px 20px', 
                backgroundColor: isDetecting ? '#6c757d' : '#007bff', 
                color: 'white', 
                border: 'none', 
                borderRadius: '4px'
              }}
            >
              {isDetecting ? 'Detecting...' : 'Detect Objects'}
            </button>
          </div>
          
          <div style={{ position: 'relative', display: 'inline-block' }}>
            <video 
              ref={videoRef}
              autoPlay
              playsInline
              style={{ 
                maxWidth: '640px', 
                width: '100%',
                border: '2px solid #ccc',
                borderRadius: '8px'
              }}
            />
            <canvas 
              ref={canvasRef}
              style={{ 
                position: 'absolute', 
                top: 0, 
                left: 0,
                maxWidth: '640px', 
                width: '100%',
                pointerEvents: 'none'
              }}
            />
          </div>
          
          {detections.length > 0 && (
            <div style={{ marginTop: '20px' }}>
              <h3>Detected Objects (Camera):</h3>
              <ul>
                {detections.map((detection, index) => (
                  <li key={index} style={{ marginBottom: '5px' }}>
                    <strong>{detection.label}</strong> - 
                    Confidence: {(detection.confidence * 100).toFixed(1)}%
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {/* Upload Tab */}
      {activeTab === 'upload' && (
        <div>
          <div style={{ marginBottom: '20px' }}>
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleFileUpload}
              accept="image/*"
              style={{ display: 'none' }}
            />
            <button 
              onClick={() => fileInputRef.current.click()}
              disabled={isUploadDetecting}
              style={{ 
                padding: '10px 20px', 
                backgroundColor: isUploadDetecting ? '#6c757d' : '#28a745', 
                color: 'white', 
                border: 'none', 
                borderRadius: '4px'
              }}
            >
              {isUploadDetecting ? 'Processing...' : 'Upload Image'}
            </button>
          </div>

          {uploadedImage && (
            <div>
              <h3>Uploaded Image: {uploadedImage.filename}</h3>
              <div style={{ position: 'relative', display: 'inline-block', marginBottom: '20px' }}>
                <canvas 
                  ref={uploadCanvasRef}
                  style={{ 
                    maxWidth: '800px', 
                    width: '100%',
                    border: '2px solid #ccc',
                    borderRadius: '8px'
                  }}
                />
              </div>
            </div>
          )}

          {uploadDetections.length > 0 && (
            <div style={{ marginTop: '20px' }}>
              <h3>Detected Objects (Upload):</h3>
              <ul>
                {uploadDetections.map((detection, index) => (
                  <li key={index} style={{ marginBottom: '5px' }}>
                    <strong>{detection.label}</strong> - 
                    Confidence: {(detection.confidence * 100).toFixed(1)}%
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default App;