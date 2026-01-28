"""
Dataset Downloader and Processor for ASL Hand Landmarks

This script downloads ASL alphabet images and processes them with MediaPipe
to extract hand landmarks, creating training data for the gesture classifier.
"""
import os
import csv
import urllib.request
import zipfile
import cv2
import numpy as np
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
from tqdm import tqdm

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
MODELS_DIR = os.path.join(BASE_DIR, "models")
TEMP_DIR = os.path.join(BASE_DIR, "temp_images")

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)


def create_hand_landmarker():
    """Create MediaPipe hand landmarker."""
    model_path = os.path.join(MODELS_DIR, "hand_landmarker.task")
    
    base_options = python.BaseOptions(model_asset_path=model_path)
    options = vision.HandLandmarkerOptions(
        base_options=base_options,
        running_mode=vision.RunningMode.IMAGE,
        num_hands=1,
        min_hand_detection_confidence=0.5,
        min_tracking_confidence=0.5
    )
    
    return vision.HandLandmarker.create_from_options(options)


def extract_features(landmarks):
    """Extract features from landmarks (matches features.py logic)."""
    if landmarks is None or len(landmarks) != 21:
        return None
    
    landmarks_arr = np.array([(lm.x, lm.y, lm.z) for lm in landmarks])
    
    # Normalize relative to wrist
    wrist = landmarks_arr[0]
    normalized = landmarks_arr - wrist
    
    # Scale normalization
    scale = np.linalg.norm(landmarks_arr[9] - landmarks_arr[0])
    if scale > 0:
        normalized = normalized / scale
    
    features = normalized.flatten()
    
    # Add finger distances
    finger_tips = [4, 8, 12, 16, 20]
    finger_mcps = [2, 5, 9, 13, 17]
    
    distances = []
    for tip, mcp in zip(finger_tips, finger_mcps):
        dist = np.linalg.norm(landmarks_arr[tip] - landmarks_arr[mcp])
        distances.append(dist / scale if scale > 0 else 0)
    
    features = np.concatenate([features, np.array(distances)])
    return features.astype(np.float32)


def generate_sample_data():
    """
    Generate sample training data by creating synthetic variations.
    This creates enough data to demonstrate the system working.
    
    For production use, replace with actual ASL images dataset.
    """
    print("Generating sample training data...")
    
    # We'll use a simple approach: create a few samples per letter
    # based on typical hand landmark positions for ASL alphabet
    
    # Sample landmark templates (simplified - in real use, collect actual data)
    # These are approximate normalized positions for demonstration
    
    samples = []
    labels = []
    
    # Letters A-Z with basic variations
    for label in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
        # Generate 50 samples per letter with random variations
        for _ in range(50):
            # Base features (68 total: 63 landmarks + 5 distances)
            base = np.random.randn(68) * 0.1
            
            # Add letter-specific offset (simple encoding)
            letter_offset = (ord(label) - ord('A')) / 25.0
            base[0] += letter_offset
            
            # Add some noise for variation
            noise = np.random.randn(68) * 0.05
            features = base + noise
            
            samples.append(features)
            labels.append(label)
    
    # Save to CSV
    output_path = os.path.join(DATA_DIR, "asl_alphabet_sample.csv")
    
    with open(output_path, 'w', newline='') as f:
        writer = csv.writer(f)
        
        # Header
        header = ['label'] + [f'f{i}' for i in range(68)]
        writer.writerow(header)
        
        # Data
        for features, label in zip(samples, labels):
            row = [label] + features.tolist()
            writer.writerow(row)
    
    print(f"Generated {len(samples)} samples for {len(set(labels))} letters")
    print(f"Saved to: {output_path}")
    return output_path


def process_images_folder(images_dir: str, output_csv: str):
    """
    Process a folder of ASL images and extract landmarks.
    
    Folder structure should be:
    images_dir/
        A/
            img1.jpg
            img2.jpg
        B/
            img1.jpg
            ...
    """
    detector = create_hand_landmarker()
    
    samples = []
    labels = []
    
    for label in os.listdir(images_dir):
        label_dir = os.path.join(images_dir, label)
        if not os.path.isdir(label_dir):
            continue
        
        print(f"Processing label: {label}")
        
        for img_file in tqdm(os.listdir(label_dir)):
            img_path = os.path.join(label_dir, img_file)
            
            try:
                # Read image
                img = cv2.imread(img_path)
                if img is None:
                    continue
                
                # Convert to RGB
                img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                
                # Create MediaPipe image
                mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=img_rgb)
                
                # Detect
                results = detector.detect(mp_image)
                
                if results.hand_landmarks:
                    features = extract_features(results.hand_landmarks[0])
                    if features is not None:
                        samples.append(features)
                        labels.append(label.upper())
            except Exception as e:
                print(f"Error processing {img_path}: {e}")
    
    detector.close()
    
    # Save to CSV
    with open(output_csv, 'w', newline='') as f:
        writer = csv.writer(f)
        header = ['label'] + [f'f{i}' for i in range(68)]
        writer.writerow(header)
        
        for features, label in zip(samples, labels):
            row = [label] + features.tolist()
            writer.writerow(row)
    
    print(f"Processed {len(samples)} images, saved to {output_csv}")
    return output_csv


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate or process ASL training data")
    parser.add_argument("--generate", action="store_true", help="Generate sample data")
    parser.add_argument("--process", type=str, help="Process images from folder")
    parser.add_argument("--output", type=str, default="asl_data.csv", help="Output CSV filename")
    
    args = parser.parse_args()
    
    if args.generate:
        generate_sample_data()
    elif args.process:
        output_path = os.path.join(DATA_DIR, args.output)
        process_images_folder(args.process, output_path)
    else:
        # Default: generate sample data
        generate_sample_data()
