"""
Face Detector Module - MediaPipe Tasks API for Emotion Detection

Detects facial expressions/emotions to add context to sign language translation.
Uses facial landmark analysis to classify emotions.
"""
import cv2
import numpy as np
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import os
from typing import Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from urllib.request import urlretrieve

from config import MODELS_DIR


class Emotion(Enum):
    """Detected emotion categories."""
    NEUTRAL = "neutral"
    HAPPY = "happy"
    SAD = "sad"
    SURPRISED = "surprised"
    ANGRY = "angry"


@dataclass
class EmotionResult:
    """Result of emotion detection."""
    emotion: Emotion
    confidence: float
    landmarks_detected: bool


class FaceDetector:
    """MediaPipe FaceLandmarker wrapper for emotion detection.
    
    Uses facial landmark positions to estimate emotional state
    based on eyebrow position, mouth shape, and eye openness.
    """
    
    # Face landmark model URL
    MODEL_URL = "https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task"
    MODEL_NAME = "face_landmarker.task"
    
    def __init__(self):
        """Initialize face detector with MediaPipe FaceLandmarker."""
        self.model_path = os.path.join(MODELS_DIR, self.MODEL_NAME)
        
        # Download model if not exists
        if not os.path.exists(self.model_path):
            print(f"Downloading face landmarker model...")
            try:
                urlretrieve(self.MODEL_URL, self.model_path)
                print(f"Downloaded to: {self.model_path}")
            except Exception as e:
                print(f"Warning: Could not download face model: {e}")
                self.detector = None
                self.results = None
                return
        
        # Create face landmarker
        try:
            base_options = python.BaseOptions(model_asset_path=self.model_path)
            options = vision.FaceLandmarkerOptions(
                base_options=base_options,
                running_mode=vision.RunningMode.IMAGE,
                num_faces=1,
                min_face_detection_confidence=0.5,
                min_tracking_confidence=0.5,
                output_face_blendshapes=True  # Enable blendshapes for emotion
            )
            self.detector = vision.FaceLandmarker.create_from_options(options)
        except Exception as e:
            print(f"Warning: Could not create face detector: {e}")
            self.detector = None
        
        self.results = None
        self._frame_height = 480
        self._frame_width = 640
        
        # Landmark indices for emotion detection (478 landmarks)
        self.LEFT_EYE_INDICES = [33, 160, 158, 133, 153, 144]
        self.RIGHT_EYE_INDICES = [362, 385, 387, 263, 373, 380]
        self.LEFT_EYEBROW_INDICES = [70, 63, 105, 66, 107]
        self.RIGHT_EYEBROW_INDICES = [336, 296, 334, 293, 300]
        self.NOSE_TIP = 1
    
    def process(self, frame_rgb: np.ndarray) -> Optional[EmotionResult]:
        """Process RGB frame to detect face and emotion.
        
        Args:
            frame_rgb: RGB image frame (numpy array)
            
        Returns:
            EmotionResult with detected emotion, or None if no face
        """
        if self.detector is None:
            return EmotionResult(Emotion.NEUTRAL, 0.0, False)
        
        self._frame_height, self._frame_width = frame_rgb.shape[:2]
        
        # Convert to MediaPipe Image
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_rgb)
        
        # Detect face
        try:
            self.results = self.detector.detect(mp_image)
        except Exception as e:
            return EmotionResult(Emotion.NEUTRAL, 0.0, False)
        
        if not self.results.face_landmarks:
            return EmotionResult(Emotion.NEUTRAL, 0.0, False)
        
        # Analyze emotion from landmarks and blendshapes
        emotion, confidence = self._analyze_emotion()
        
        return EmotionResult(emotion, confidence, True)
    
    def _analyze_emotion(self) -> Tuple[Emotion, float]:
        """Analyze facial landmarks and blendshapes to determine emotion."""
        if not self.results or not self.results.face_landmarks:
            return Emotion.NEUTRAL, 0.0
        
        # Use blendshapes if available (more accurate)
        if self.results.face_blendshapes and len(self.results.face_blendshapes) > 0:
            return self._analyze_blendshapes(self.results.face_blendshapes[0])
        
        # Fallback to landmark analysis
        return self._analyze_landmarks(self.results.face_landmarks[0])
    
    def _analyze_blendshapes(self, blendshapes) -> Tuple[Emotion, float]:
        """Analyze face blendshapes for emotion detection."""
        # Convert blendshapes to dict for easier access
        bs_dict = {bs.category_name: bs.score for bs in blendshapes}
        
        scores = {
            Emotion.NEUTRAL: 0.5,
            Emotion.HAPPY: 0.0,
            Emotion.SAD: 0.0,
            Emotion.SURPRISED: 0.0,
            Emotion.ANGRY: 0.0
        }
        
        # Happy: mouth smile + cheek squint
        mouth_smile_left = bs_dict.get('mouthSmileLeft', 0)
        mouth_smile_right = bs_dict.get('mouthSmileRight', 0)
        smile_score = (mouth_smile_left + mouth_smile_right) / 2
        if smile_score > 0.3:
            scores[Emotion.HAPPY] += smile_score
        
        # Surprised: eyebrows raised + jaw open
        brow_inner_up = bs_dict.get('browInnerUp', 0)
        jaw_open = bs_dict.get('jawOpen', 0)
        if brow_inner_up > 0.3 and jaw_open > 0.2:
            scores[Emotion.SURPRISED] += (brow_inner_up + jaw_open) / 2
        
        # Sad: mouth frown + brow down
        mouth_frown_left = bs_dict.get('mouthFrownLeft', 0)
        mouth_frown_right = bs_dict.get('mouthFrownRight', 0)
        frown_score = (mouth_frown_left + mouth_frown_right) / 2
        if frown_score > 0.2:
            scores[Emotion.SAD] += frown_score
        
        # Angry: brow down + eye squint
        brow_down_left = bs_dict.get('browDownLeft', 0)
        brow_down_right = bs_dict.get('browDownRight', 0)
        brow_down = (brow_down_left + brow_down_right) / 2
        if brow_down > 0.3:
            scores[Emotion.ANGRY] += brow_down
        
        # Get highest scoring emotion
        best_emotion = max(scores, key=scores.get)
        confidence = min(1.0, scores[best_emotion])
        
        return best_emotion, confidence
    
    def _analyze_landmarks(self, landmarks) -> Tuple[Emotion, float]:
        """Fallback: Analyze landmarks for emotion (less accurate)."""
        # Simple heuristics based on landmark positions
        # Get mouth and eye metrics
        try:
            # Mouth height
            top_lip = landmarks[13]
            bottom_lip = landmarks[14]
            mouth_height = abs(top_lip.y - bottom_lip.y)
            
            # Mouth corners
            left_corner = landmarks[61]
            right_corner = landmarks[291]
            center_bottom = landmarks[17]
            
            corner_avg_y = (left_corner.y + right_corner.y) / 2
            mouth_curve = center_bottom.y - corner_avg_y
            
            # Simple classification
            if mouth_curve > 0.02:
                return Emotion.HAPPY, 0.7
            elif mouth_height > 0.05:
                return Emotion.SURPRISED, 0.6
            elif mouth_curve < -0.02:
                return Emotion.SAD, 0.6
            else:
                return Emotion.NEUTRAL, 0.5
        except:
            return Emotion.NEUTRAL, 0.5
    
    def draw_landmarks(self, frame_bgr: np.ndarray, 
                       show_mesh: bool = False,
                       show_emotion: bool = True,
                       emotion_result: Optional[EmotionResult] = None) -> np.ndarray:
        """Draw face landmarks and emotion on frame."""
        if self.results is None or not self.results.face_landmarks:
            return frame_bgr
        
        h, w = frame_bgr.shape[:2]
        
        # Draw face landmarks (simplified - just contour)
        for face_landmarks in self.results.face_landmarks:
            # Draw face oval
            face_oval_indices = [10, 338, 297, 332, 284, 251, 389, 356, 454, 323, 361, 288, 
                                397, 365, 379, 378, 400, 377, 152, 148, 176, 149, 150, 136,
                                172, 58, 132, 93, 234, 127, 162, 21, 54, 103, 67, 109]
            
            points = []
            for idx in face_oval_indices:
                if idx < len(face_landmarks):
                    lm = face_landmarks[idx]
                    px = int(lm.x * w)
                    py = int(lm.y * h)
                    points.append((px, py))
            
            # Draw oval
            if len(points) > 2:
                for i in range(len(points) - 1):
                    cv2.line(frame_bgr, points[i], points[i+1], (0, 255, 255), 1)
                cv2.line(frame_bgr, points[-1], points[0], (0, 255, 255), 1)
        
        # Draw emotion text
        if show_emotion and emotion_result and emotion_result.landmarks_detected:
            emotion_text = f"{emotion_result.emotion.value.capitalize()}"
            confidence_text = f"{emotion_result.confidence:.0%}"
            
            # Emotion colors
            emotion_colors = {
                Emotion.NEUTRAL: (200, 200, 200),
                Emotion.HAPPY: (0, 255, 100),
                Emotion.SAD: (255, 100, 100),
                Emotion.SURPRISED: (0, 200, 255),
                Emotion.ANGRY: (0, 0, 255)
            }
            color = emotion_colors.get(emotion_result.emotion, (255, 255, 255))
            
            # Draw background box
            cv2.rectangle(frame_bgr, (10, 10), (180, 60), (0, 0, 0), -1)
            cv2.rectangle(frame_bgr, (10, 10), (180, 60), color, 2)
            
            # Draw text
            cv2.putText(frame_bgr, f"{emotion_text}", (20, 35),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
            cv2.putText(frame_bgr, confidence_text, (20, 52),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, (150, 150, 150), 1)
        
        return frame_bgr
    
    def has_face(self) -> bool:
        """Check if a face was detected in the last frame."""
        return (self.results is not None and 
                self.results.face_landmarks is not None and
                len(self.results.face_landmarks) > 0)
    
    def release(self):
        """Release resources."""
        if self.detector:
            self.detector.close()
