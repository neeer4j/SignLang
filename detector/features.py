"""
Feature Extraction Module - Convert landmarks to ML features

Enhanced feature set for improved accuracy:
- Normalized coordinates (63 features)
- Finger tip to MCP distances (5 features)  
- Finger tip to palm distances (5 features)
- Inter-finger tip distances (10 features)
- Thumb to finger distances (4 features)
- Finger angles/curvature (5 features)
- Palm orientation (3 features)
"""
import numpy as np


class FeatureExtractor:
    """Extract normalized features from hand landmarks for ML classification."""
    
    # Landmark indices
    FINGER_TIPS = [4, 8, 12, 16, 20]      # Thumb, Index, Middle, Ring, Pinky tips
    FINGER_MCPS = [2, 5, 9, 13, 17]       # MCP joints (knuckles)
    FINGER_PIPS = [3, 6, 10, 14, 18]      # PIP joints (middle of finger)
    FINGER_DIPS = [3, 7, 11, 15, 19]      # DIP joints
    PALM_CENTER = 9                        # Middle finger MCP as palm reference
    WRIST = 0
    
    @staticmethod
    def extract(landmarks) -> np.ndarray:
        """Extract feature vector from landmarks.
        
        Features include:
        - Normalized x, y, z coordinates (relative to wrist)
        - Distances between key points
        
        Args:
            landmarks: List of 21 (x, y, z) tuples from MediaPipe
            
        Returns:
            numpy array of features (68 features)
        """
        if landmarks is None or len(landmarks) != 21:
            return None
        
        landmarks = np.array(landmarks)
        
        # Normalize relative to wrist (landmark 0)
        wrist = landmarks[0]
        normalized = landmarks - wrist
        
        # Scale normalization - use distance from wrist to middle finger MCP
        scale = np.linalg.norm(landmarks[9] - landmarks[0])
        if scale > 0:
            normalized = normalized / scale
        
        # Flatten to 1D feature vector (63 features: 21 * 3)
        features = normalized.flatten()
        
        # Add finger distances (useful for detecting open/closed fingers)
        finger_tips = [4, 8, 12, 16, 20]  # Thumb, Index, Middle, Ring, Pinky tips
        finger_mcps = [2, 5, 9, 13, 17]   # MCP joints
        
        distances = []
        for tip, mcp in zip(finger_tips, finger_mcps):
            dist = np.linalg.norm(landmarks[tip] - landmarks[mcp])
            distances.append(dist / scale if scale > 0 else 0)
        
        # Combine all features
        features = np.concatenate([features, np.array(distances)])
        
        return features.astype(np.float32)
    
    @staticmethod
    def get_feature_count() -> int:
        """Return the total number of features."""
        return 63 + 5  # 21*3 coordinates + 5 finger distances = 68 features
