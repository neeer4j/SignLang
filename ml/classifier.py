"""
Gesture Classifier - Real-time prediction with temporal smoothing
"""
import pickle
import numpy as np
import os
from collections import deque
from config import MODEL_PATH, LABELS_PATH


class Classifier:
    """Load trained model and make predictions with temporal smoothing."""
    
    def __init__(self, smoothing_window: int = 12):
        """Initialize classifier.
        
        Args:
            smoothing_window: Number of frames to average predictions over
        """
        self.model = None
        self.label_encoder = None
        self.is_loaded = False
        
        # Temporal smoothing buffer
        self.smoothing_window = smoothing_window
        self.prediction_buffer = deque(maxlen=smoothing_window)
        self.confidence_buffer = deque(maxlen=smoothing_window)
    
    def load(self, model_path: str = None, labels_path: str = None) -> bool:
        """Load trained model and label encoder.
        
        Returns:
            True if loaded successfully
        """
        model_path = model_path or MODEL_PATH
        labels_path = labels_path or LABELS_PATH
        
        if not os.path.exists(model_path) or not os.path.exists(labels_path):
            return False
        
        try:
            with open(model_path, 'rb') as f:
                self.model = pickle.load(f)
            
            with open(labels_path, 'rb') as f:
                self.label_encoder = pickle.load(f)
            
            self.is_loaded = True
            self.clear_buffer()  # Reset buffer on new model load
            return True
        except Exception as e:
            print(f"Error loading model: {e}")
            return False
    
    def clear_buffer(self):
        """Clear the prediction smoothing buffer."""
        self.prediction_buffer.clear()
        self.confidence_buffer.clear()
    
    def predict(self, features: np.ndarray, use_smoothing: bool = True) -> tuple:
        """Make prediction for given features with optional temporal smoothing.
        
        Args:
            features: Feature vector from FeatureExtractor
            use_smoothing: Whether to apply temporal smoothing
            
        Returns:
            tuple: (predicted_label, confidence_score)
        """
        if not self.is_loaded or features is None:
            return None, 0.0
        
        # Reshape for single prediction
        features = features.reshape(1, -1)
        
        # Get raw prediction and probabilities
        prediction = self.model.predict(features)[0]
        probabilities = self.model.predict_proba(features)[0]
        
        # Get raw label and confidence
        raw_label = self.label_encoder.inverse_transform([prediction])[0]
        raw_confidence = probabilities[prediction]
        
        if not use_smoothing:
            return raw_label, float(raw_confidence)
        
        # Add to smoothing buffer
        self.prediction_buffer.append(raw_label)
        self.confidence_buffer.append(raw_confidence)
        
        # Get smoothed prediction using majority voting
        if len(self.prediction_buffer) >= 2:
            # Count occurrences of each label
            label_counts = {}
            label_confidences = {}
            
            for label, conf in zip(self.prediction_buffer, self.confidence_buffer):
                if label not in label_counts:
                    label_counts[label] = 0
                    label_confidences[label] = []
                label_counts[label] += 1
                label_confidences[label].append(conf)
            
            # Find the most common label
            best_label = max(label_counts, key=label_counts.get)
            
            # Average confidence for that label
            avg_confidence = np.mean(label_confidences[best_label])
            
            # Consistency: fraction of buffer that matches best_label
            consistency = label_counts[best_label] / len(self.prediction_buffer)
            
            # REJECT if consistency is too low (e.g. < 50% of frames agree)
            if consistency < 0.5:
                return None, 0.0
            
            # Boost confidence if consistent predictions
            # If 100% consistent, confidence boosted by 1.2x.
            adjusted_confidence = avg_confidence * (0.8 + 0.5 * consistency)
            
            return best_label, float(min(adjusted_confidence, 1.0))
        
        return raw_label, float(raw_confidence)
    
    def predict_top_n(self, features: np.ndarray, n: int = 3) -> list:
        """Get top N predictions with confidence scores.
        
        Args:
            features: Feature vector
            n: Number of top predictions to return
            
        Returns:
            list of (label, confidence) tuples
        """
        if not self.is_loaded or features is None:
            return []
        
        features = features.reshape(1, -1)
        probabilities = self.model.predict_proba(features)[0]
        
        # Get top N indices
        top_indices = np.argsort(probabilities)[-n:][::-1]
        
        results = []
        for idx in top_indices:
            label = self.label_encoder.inverse_transform([idx])[0]
            confidence = probabilities[idx]
            results.append((label, float(confidence)))
        
        return results
    
    def get_classes(self) -> list:
        """Get list of available classes."""
        if self.label_encoder is None:
            return []
        return self.label_encoder.classes_.tolist()
    
    def model_exists(self) -> bool:
        """Check if model file exists."""
        return os.path.exists(MODEL_PATH) and os.path.exists(LABELS_PATH)
