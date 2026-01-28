"""
Enhanced ASL Training Data Generator

Creates training data for ASL letters A-Z with distinctive hand configurations
that more closely match actual ASL fingerspelling patterns.
"""
import os
import sys
import csv
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
os.makedirs(DATA_DIR, exist_ok=True)


def generate_hand_template():
    """Generate base hand landmark positions (21 landmarks)."""
    # MediaPipe hand landmarks layout:
    # 0: Wrist
    # 1-4: Thumb (CMC, MCP, IP, TIP)
    # 5-8: Index (MCP, PIP, DIP, TIP)
    # 9-12: Middle (MCP, PIP, DIP, TIP)
    # 13-16: Ring (MCP, PIP, DIP, TIP)
    # 17-20: Pinky (MCP, PIP, DIP, TIP)
    
    landmarks = np.zeros((21, 3), dtype=np.float32)
    
    # Wrist
    landmarks[0] = [0.5, 0.8, 0]
    
    # Palm base positions (MCPs)
    landmarks[1] = [0.35, 0.7, 0]   # Thumb CMC
    landmarks[5] = [0.35, 0.55, 0]  # Index MCP
    landmarks[9] = [0.45, 0.5, 0]   # Middle MCP
    landmarks[13] = [0.55, 0.55, 0] # Ring MCP
    landmarks[17] = [0.65, 0.62, 0] # Pinky MCP
    
    return landmarks


def set_finger_state(landmarks, finger_idx, state, variation=0.03):
    """
    Set finger state: 'extended', 'bent', 'curved', 'folded'
    
    finger_idx: 0=thumb, 1=index, 2=middle, 3=ring, 4=pinky
    """
    # Finger joint indices
    if finger_idx == 0:  # Thumb
        mcp, pip, dip, tip = 1, 2, 3, 4
        direction = np.array([-0.1, -0.15, 0])
    else:
        base = 5 + (finger_idx - 1) * 4
        mcp, pip, dip, tip = base - 4 + finger_idx * 4, base - 4 + finger_idx * 4 + 1, base - 4 + finger_idx * 4 + 2, base - 4 + finger_idx * 4 + 3
        mcp = 1 + finger_idx * 4
        pip = mcp + 1
        dip = mcp + 2
        tip = mcp + 3
        direction = np.array([0, -0.15, 0])
    
    # Add variation
    noise = np.random.randn(3) * variation
    
    if state == 'extended':
        landmarks[pip] = landmarks[mcp] + direction + noise
        landmarks[dip] = landmarks[pip] + direction * 0.8 + noise * 0.5
        landmarks[tip] = landmarks[dip] + direction * 0.6 + noise * 0.3
    elif state == 'bent':
        # Finger bent at 90 degrees
        landmarks[pip] = landmarks[mcp] + direction * 0.5 + noise
        bend_dir = np.array([0.1, 0.05, 0.05])
        landmarks[dip] = landmarks[pip] + bend_dir + noise * 0.5
        landmarks[tip] = landmarks[dip] + bend_dir * 0.7 + noise * 0.3
    elif state == 'curved':
        # Gentle curve
        landmarks[pip] = landmarks[mcp] + direction * 0.6 + noise
        landmarks[dip] = landmarks[pip] + direction * 0.4 + np.array([0.03, 0.02, 0]) + noise * 0.5
        landmarks[tip] = landmarks[dip] + direction * 0.2 + np.array([0.05, 0.03, 0]) + noise * 0.3
    elif state == 'folded':
        # Fully folded into palm
        fold_dir = np.array([0.05, 0.1, 0.02])
        landmarks[pip] = landmarks[mcp] + direction * 0.2 + noise
        landmarks[dip] = landmarks[pip] + fold_dir + noise * 0.5
        landmarks[tip] = landmarks[dip] + fold_dir * 0.5 + noise * 0.3
    
    return landmarks


def create_asl_letter(letter, variation=0.03):
    """Create hand landmarks for a specific ASL letter."""
    landmarks = generate_hand_template()
    
    # ASL letter configurations
    configs = {
        'A': {'thumb': 'extended', 'index': 'folded', 'middle': 'folded', 'ring': 'folded', 'pinky': 'folded'},
        'B': {'thumb': 'folded', 'index': 'extended', 'middle': 'extended', 'ring': 'extended', 'pinky': 'extended'},
        'C': {'thumb': 'curved', 'index': 'curved', 'middle': 'curved', 'ring': 'curved', 'pinky': 'curved'},
        'D': {'thumb': 'bent', 'index': 'extended', 'middle': 'folded', 'ring': 'folded', 'pinky': 'folded'},
        'E': {'thumb': 'bent', 'index': 'bent', 'middle': 'bent', 'ring': 'bent', 'pinky': 'bent'},
        'F': {'thumb': 'bent', 'index': 'bent', 'middle': 'extended', 'ring': 'extended', 'pinky': 'extended'},
        'G': {'thumb': 'extended', 'index': 'extended', 'middle': 'folded', 'ring': 'folded', 'pinky': 'folded'},
        'H': {'thumb': 'folded', 'index': 'extended', 'middle': 'extended', 'ring': 'folded', 'pinky': 'folded'},
        'I': {'thumb': 'folded', 'index': 'folded', 'middle': 'folded', 'ring': 'folded', 'pinky': 'extended'},
        'J': {'thumb': 'folded', 'index': 'folded', 'middle': 'folded', 'ring': 'folded', 'pinky': 'curved'},
        'K': {'thumb': 'extended', 'index': 'extended', 'middle': 'extended', 'ring': 'folded', 'pinky': 'folded'},
        'L': {'thumb': 'extended', 'index': 'extended', 'middle': 'folded', 'ring': 'folded', 'pinky': 'folded'},
        'M': {'thumb': 'bent', 'index': 'folded', 'middle': 'folded', 'ring': 'folded', 'pinky': 'folded'},
        'N': {'thumb': 'bent', 'index': 'bent', 'middle': 'folded', 'ring': 'folded', 'pinky': 'folded'},
        'O': {'thumb': 'curved', 'index': 'curved', 'middle': 'curved', 'ring': 'curved', 'pinky': 'curved'},
        'P': {'thumb': 'extended', 'index': 'extended', 'middle': 'bent', 'ring': 'folded', 'pinky': 'folded'},
        'Q': {'thumb': 'extended', 'index': 'bent', 'middle': 'folded', 'ring': 'folded', 'pinky': 'folded'},
        'R': {'thumb': 'folded', 'index': 'extended', 'middle': 'extended', 'ring': 'folded', 'pinky': 'folded'},
        'S': {'thumb': 'bent', 'index': 'folded', 'middle': 'folded', 'ring': 'folded', 'pinky': 'folded'},
        'T': {'thumb': 'extended', 'index': 'folded', 'middle': 'folded', 'ring': 'folded', 'pinky': 'folded'},
        'U': {'thumb': 'folded', 'index': 'extended', 'middle': 'extended', 'ring': 'folded', 'pinky': 'folded'},
        'V': {'thumb': 'folded', 'index': 'extended', 'middle': 'extended', 'ring': 'folded', 'pinky': 'folded'},
        'W': {'thumb': 'folded', 'index': 'extended', 'middle': 'extended', 'ring': 'extended', 'pinky': 'folded'},
        'X': {'thumb': 'folded', 'index': 'bent', 'middle': 'folded', 'ring': 'folded', 'pinky': 'folded'},
        'Y': {'thumb': 'extended', 'index': 'folded', 'middle': 'folded', 'ring': 'folded', 'pinky': 'extended'},
        'Z': {'thumb': 'folded', 'index': 'extended', 'middle': 'folded', 'ring': 'folded', 'pinky': 'folded'},
    }
    
    config = configs.get(letter, {})
    finger_names = ['thumb', 'index', 'middle', 'ring', 'pinky']
    
    for i, name in enumerate(finger_names):
        state = config.get(name, 'extended')
        landmarks = set_finger_state(landmarks, i, state, variation)
    
    return landmarks


def extract_features(landmarks):
    """Extract features matching features.py logic."""
    # Normalize relative to wrist
    wrist = landmarks[0]
    normalized = landmarks - wrist
    
    # Scale by middle finger base distance
    scale = np.linalg.norm(landmarks[9] - landmarks[0])
    if scale > 0:
        normalized = normalized / scale
    
    features = normalized.flatten()
    
    # Add finger distances (fingertip to MCP)
    finger_tips = [4, 8, 12, 16, 20]
    finger_mcps = [2, 5, 9, 13, 17]
    
    distances = []
    for tip, mcp in zip(finger_tips, finger_mcps):
        dist = np.linalg.norm(landmarks[tip] - landmarks[mcp])
        distances.append(dist / scale if scale > 0 else 0)
    
    features = np.concatenate([features, np.array(distances)])
    return features.astype(np.float32)


def generate_enhanced_dataset(samples_per_letter=200):
    """Generate enhanced ASL dataset with distinctive patterns."""
    print(f"Generating enhanced ASL dataset ({samples_per_letter} samples per letter)...")
    
    samples = []
    labels = []
    
    np.random.seed(42)
    
    for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
        for i in range(samples_per_letter):
            # Vary the noise level for diversity
            variation = 0.02 + np.random.rand() * 0.03
            
            landmarks = create_asl_letter(letter, variation)
            features = extract_features(landmarks)
            
            samples.append(features)
            labels.append(letter)
    
    # Save to CSV
    output_path = os.path.join(DATA_DIR, "asl_enhanced_data.csv")
    
    with open(output_path, 'w', newline='') as f:
        writer = csv.writer(f)
        
        # Header
        header = ['label'] + [f'f{i}' for i in range(len(samples[0]))]
        writer.writerow(header)
        
        # Data
        for features, label in zip(samples, labels):
            row = [label] + features.tolist()
            writer.writerow(row)
    
    print(f"Generated {len(samples)} samples for {len(set(labels))} letters")
    print(f"Saved to: {output_path}")
    
    return output_path


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate enhanced ASL training data")
    parser.add_argument("--samples", type=int, default=200, help="Samples per letter")
    
    args = parser.parse_args()
    
    generate_enhanced_dataset(args.samples)
    
    print("\nTo train the model, run:")
    print("  python train_model.py")
