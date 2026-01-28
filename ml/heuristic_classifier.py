"""
Heuristic Gesture Classifier - Rule-based gesture detection

Uses geometric analysis of hand landmarks for reliable gesture detection
without relying on ML models trained on synthetic data.
"""
import numpy as np
from typing import Optional, Tuple, List


class HeuristicClassifier:
    """Rule-based gesture classifier using hand landmark geometry."""
    
    def __init__(self):
        """Initialize classifier."""
        self.last_prediction = None
        self.prediction_count = 0
        self.FINGER_TIPS = [4, 8, 12, 16, 20]  # Thumb, Index, Middle, Ring, Pinky
        self.FINGER_PIPS = [3, 6, 10, 14, 18]  # PIP joints
        self.FINGER_MCPS = [2, 5, 9, 13, 17]   # MCP joints
    
    def predict(self, landmarks: List[Tuple[float, float, float]]) -> Tuple[Optional[str], float]:
        """Predict gesture from landmarks using geometric heuristics.
        
        Args:
            landmarks: List of 21 (x, y, z) tuples from MediaPipe
            
        Returns:
            (gesture_label, confidence) or (None, 0.0) if no match
        """
        if landmarks is None or len(landmarks) != 21:
            return None, 0.0
        
        # Convert to numpy for easier math
        lm = np.array(landmarks)
        
        # Calculate finger states
        fingers_extended = self._get_fingers_extended(lm)
        thumb_extended = self._is_thumb_extended(lm)
        
        # Count extended fingers
        extended_count = sum(fingers_extended) + (1 if thumb_extended else 0)
        
        # Classify based on finger patterns
        gesture, confidence = self._classify_gesture(
            fingers_extended, thumb_extended, extended_count, lm
        )
        
        # Temporal smoothing - require 2 consistent predictions
        if gesture == self.last_prediction:
            self.prediction_count += 1
        else:
            self.last_prediction = gesture
            self.prediction_count = 1
        
        if self.prediction_count >= 2:
            return gesture, confidence
        
        return None, 0.0
    
    def _get_fingers_extended(self, lm: np.ndarray) -> List[bool]:
        """Check which fingers are extended (not thumb).
        
        A finger is extended if tip is above (lower y) PIP joint.
        """
        extended = []
        for tip, pip in zip(self.FINGER_TIPS[1:], self.FINGER_PIPS[1:]):  # Skip thumb
            # Finger extended if tip.y < pip.y (higher on screen)
            extended.append(lm[tip][1] < lm[pip][1])
        return extended
    
    def _is_thumb_extended(self, lm: np.ndarray) -> bool:
        """Check if thumb is extended."""
        # Thumb extended if tip.x is far from index MCP
        thumb_tip = lm[4]
        index_mcp = lm[5]
        wrist = lm[0]
        
        # Check horizontal distance (works for both hands)
        thumb_dist = abs(thumb_tip[0] - index_mcp[0])
        hand_width = abs(lm[17][0] - lm[5][0])  # Pinky MCP to Index MCP
        
        return thumb_dist > hand_width * 0.5
    
    def _classify_gesture(self, fingers: List[bool], thumb: bool, 
                          count: int, lm: np.ndarray) -> Tuple[Optional[str], float]:
        """Classify gesture based on finger states."""
        idx, mid, ring, pinky = fingers
        
        # === NUMBERS / SIMPLE GESTURES ===
        
        # Fist / A / S - no fingers extended
        if count == 0 or (not any(fingers) and not thumb):
            return "A", 0.75  # Fist-like, could be A or S
        
        # L - thumb and index only, perpendicular
        if thumb and idx and not mid and not ring and not pinky:
            return "L", 0.85
        
        # V or 2 - index and middle only
        if idx and mid and not ring and not pinky and not thumb:
            return "V", 0.85
        
        # W or 3 - index, middle, ring
        if idx and mid and ring and not pinky and not thumb:
            return "W", 0.85
        
        # 4 - all fingers but not thumb
        if idx and mid and ring and pinky and not thumb:
            return "B", 0.80  # Open hand without thumb
        
        # 5 / Open - all extended
        if all(fingers) and thumb:
            return "5", 0.85  # Open hand
        
        # Y - thumb and pinky only
        if thumb and pinky and not idx and not mid and not ring:
            return "Y", 0.85
        
        # I - pinky only
        if pinky and not idx and not mid and not ring and not thumb:
            return "I", 0.85
        
        # Pointing - index only
        if idx and not mid and not ring and not pinky:
            if thumb:
                return "G", 0.75  # Index + thumb = G or pointing
            else:
                return "D", 0.75  # Just index = D
        
        # U - index and middle together
        if idx and mid and not ring and not pinky:
            # Check if fingers are close together
            index_tip = lm[8]
            middle_tip = lm[12]
            finger_dist = np.linalg.norm(index_tip[:2] - middle_tip[:2])
            hand_width = abs(lm[17][0] - lm[5][0])
            
            if finger_dist < hand_width * 0.3:
                return "U", 0.80
            return "V", 0.75  # Spread = V
        
        # C - curved, moderate opening
        if thumb and idx and mid:
            # Check curvature - tips should form arc
            return "C", 0.65  # Approximation
        
        # O - closed loop
        thumb_tip = lm[4]
        index_tip = lm[8]
        tip_dist = np.linalg.norm(thumb_tip - index_tip)
        if tip_dist < 0.08:  # Tips touching
            return "O", 0.75
        
        # F - similar to O but other fingers extended
        if tip_dist < 0.1 and mid and ring and pinky:
            return "F", 0.75
        
        # Default - return most common based on count
        if count == 1:
            return "D", 0.5
        elif count == 2:
            return "V", 0.5
        elif count == 3:
            return "W", 0.5
        elif count == 4:
            return "B", 0.5
        else:
            return "5", 0.5
    
    def clear(self):
        """Reset prediction state."""
        self.last_prediction = None
        self.prediction_count = 0
