"""
Stage 1: Face Detection & Encoding
Detects a face in an input image and generates a face embedding using deepface.
Saves the embedding to output/face_encoding.json.
"""

import os
import json
import sys
from pathlib import Path
from typing import Any, cast

try:
    import cv2
except ImportError as e:
    raise ImportError(
        "OpenCV is not installed correctly. Install it with: pip install opencv-python"
    ) from e

try:
    from deepface import DeepFace
except ImportError:
    print("ERROR: deepface not installed. Run: pip install deepface")
    sys.exit(1)


def detect_and_encode_face(image_path: str, output_dir: str = "output") -> dict:
    """
    Detects a face in the image and generates an embedding.
    
    Args:
        image_path: Path to the input image file
        output_dir: Directory to save the encoding JSON
        
    Returns:
        dict: Contains face bounding box and encoding vector
        
    Raises:
        FileNotFoundError: If image file doesn't exist
        Exception: If no face is detected or processing fails
    """
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Validate input file
    if not os.path.isfile(image_path):
        raise FileNotFoundError(f"Image file not found: {image_path}")
    
    print(f"[Stage 1] Processing image: {image_path}")

    cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"  # type: ignore[attr-defined]
    face_cascade = cv2.CascadeClassifier(cascade_path)
    if face_cascade.empty():
        raise RuntimeError(
            "Failed to load Haar Cascade classifier. "
            f"OpenCV cascade path is invalid: {cascade_path}"
        )

    image = cv2.imread(image_path)
    if image is None:
        raise ValueError(
            f"Image unable to load: cv2.imread() returned None for '{image_path}'. "
            "Check that the path is correct and the file is a supported image format."
        )

    grayscale_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    detected_faces = face_cascade.detectMultiScale(
        grayscale_image,
        scaleFactor=1.1,
        minNeighbors=5,
        minSize=(80, 80),
    )
    if len(detected_faces) == 0:
        raise ValueError(
            "No face detected by OpenCV Haar Cascade. Use a clear, front-facing, "
            "well-lit human face image."
        )

    x, y, width, height = max(
        detected_faces, key=lambda detected_face: detected_face[2] * detected_face[3]
    )
    face_crop = image[y:y + height, x:x + width]
    if face_crop.size == 0:
        raise ValueError("Face detected, but the detected image region could not be read")
    
    try:
        # Use deepface to extract face embeddings
        # model_name options: 'VGG-Face', 'Facenet', 'Facenet512', 'OpenFace', 'DeepFace', 'DeepID', 'ArcFace', 'Dlib', 'SFace'
        embeddings = DeepFace.represent(
            img_path=face_crop,
            model_name="Facenet512",  # Reliable, widely-used model
            detector_backend="skip",
            enforce_detection=True  # Raise error if no face detected
        )
        
        if not embeddings:
            raise ValueError("No face embedding generated")
        
        # deepface returns a list; take the first (most confident) face
        face_data = cast(dict[str, Any], embeddings[0])
        
        # Extract bounding box if available
        result = {
            "image_file": image_path,
            "model": "Facenet512",
            "embedding": face_data.get("embedding", []),
            "distance_metric": face_data.get("distance_metric", "cosine"),
        }
        
        # Optional: If facial_area is in the result (older deepface versions), include bounding box
        if "facial_area" in face_data:
            bbox = face_data["facial_area"]
            result["bounding_box"] = {
                "x": bbox.get("x", 0),
                "y": bbox.get("y", 0),
                "w": bbox.get("w", 0),
                "h": bbox.get("h", 0),
            }
            print(f"  → Face detected at bounding box: ({bbox.get('x', 0)}, {bbox.get('y', 0)}) size {bbox.get('w', 0)}x{bbox.get('h', 0)}")
        else:
            result["bounding_box"] = {
                "x": int(x),
                "y": int(y),
                "w": int(width),
                "h": int(height),
            }
            print(f"  → Face detected at bounding box: ({x}, {y}) size {width}x{height}")
        
        # Save encoding to output file
        output_file = os.path.join(output_dir, "face_encoding.json")
        with open(output_file, "w") as f:
            json.dump(result, f, indent=2)
        
        print(f"  ✓ Face encoding saved to: {output_file}")
        print(f"  ✓ Embedding vector dimension: {len(result['embedding'])}")
        
        return result
    
    except ValueError as e:
        print(f"ERROR: No face detected or no embedding generated: {e}")
        raise
    except Exception as e:
        print(f"ERROR: Face detection failed: {e}")
        raise


def main(image_path: str):
    """Main entry point for stage 1"""
    try:
        result = detect_and_encode_face(image_path)
        print("\n[Stage 1] ✓ SUCCESS: Face detected and encoded\n")
        return result
    except FileNotFoundError as e:
        print(f"\n[Stage 1] ✗ FAILED: {e}\n")
        return None
    except Exception as e:
        print(f"\n[Stage 1] ✗ FAILED: {e}\n")
        return None


if __name__ == "__main__":
    if len(sys.argv) > 1:
        image_path = sys.argv[1]
    else:
        image_path = "input_face.jpg"
    
    main(image_path)
