"""
Gesture Sequence - Data structures for temporal gesture representation

This module defines the core data structures used throughout the
sign language processing pipeline to represent gestures over time.
"""
import time
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Tuple
from enum import Enum
import numpy as np


class GestureType(Enum):
    """Types of gestures recognized by the system."""
    STATIC = "static"           # Static hand pose (letters, numbers)
    DYNAMIC = "dynamic"         # Movement-based gesture (J, Z, wave)
    WORD = "word"               # Complete word gesture
    PHRASE = "phrase"           # Multi-word phrase gesture
    TRANSITION = "transition"   # Transitional movement between gestures
    UNKNOWN = "unknown"


class GestureConfidence(Enum):
    """Confidence levels for gesture recognition."""
    HIGH = "high"        # > 0.85
    MEDIUM = "medium"    # 0.65 - 0.85
    LOW = "low"          # 0.45 - 0.65
    UNCERTAIN = "uncertain"  # < 0.45


@dataclass
class GestureFrame:
    """A single frame of gesture data with landmarks and predictions.
    
    Represents a snapshot of hand tracking at a specific moment,
    including raw landmarks, extracted features, and predictions.
    """
    timestamp: float
    frame_id: int
    
    # Raw landmark data (21 points x 3 coords)
    landmarks: Optional[np.ndarray] = None
    
    # Extracted features for ML classification
    features: Optional[np.ndarray] = None
    
    # Prediction results
    predicted_label: Optional[str] = None
    confidence: float = 0.0
    gesture_type: GestureType = GestureType.UNKNOWN
    
    # Hand tracking metadata
    hand_detected: bool = False
    handedness: str = "unknown"  # "left" or "right"
    
    # Additional context
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def confidence_level(self) -> GestureConfidence:
        """Get confidence level category."""
        if self.confidence >= 0.85:
            return GestureConfidence.HIGH
        elif self.confidence >= 0.65:
            return GestureConfidence.MEDIUM
        elif self.confidence >= 0.45:
            return GestureConfidence.LOW
        return GestureConfidence.UNCERTAIN
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'timestamp': self.timestamp,
            'frame_id': self.frame_id,
            'predicted_label': self.predicted_label,
            'confidence': self.confidence,
            'gesture_type': self.gesture_type.value,
            'hand_detected': self.hand_detected,
            'handedness': self.handedness,
            'metadata': self.metadata
        }


@dataclass
class RecognizedGesture:
    """A gesture recognized from temporal analysis of multiple frames.
    
    Represents a stabilized gesture recognition result after
    temporal smoothing and confidence aggregation.
    """
    label: str
    gesture_type: GestureType
    confidence: float
    
    # Temporal information
    start_time: float
    end_time: float
    frame_count: int
    
    # Supporting data
    supporting_frames: List[int] = field(default_factory=list)
    alternative_labels: List[Tuple[str, float]] = field(default_factory=list)
    
    # Semantic information
    semantic_meaning: Optional[str] = None  # What this gesture means
    is_word_level: bool = False  # True if represents complete word
    
    @property
    def duration(self) -> float:
        """Get gesture duration in seconds."""
        return self.end_time - self.start_time
    
    @property
    def confidence_level(self) -> GestureConfidence:
        """Get confidence level category."""
        if self.confidence >= 0.85:
            return GestureConfidence.HIGH
        elif self.confidence >= 0.65:
            return GestureConfidence.MEDIUM
        elif self.confidence >= 0.45:
            return GestureConfidence.LOW
        return GestureConfidence.UNCERTAIN


@dataclass
class GestureSequence:
    """A sequence of recognized gestures forming a translation unit.
    
    Represents multiple gestures that together form a word,
    sentence, or phrase for translation.
    """
    gestures: List[RecognizedGesture] = field(default_factory=list)
    
    # Sequence metadata
    start_time: float = 0.0
    end_time: float = 0.0
    is_complete: bool = False
    
    # Translation result
    translated_text: Optional[str] = None
    translation_confidence: float = 0.0
    
    def add_gesture(self, gesture: RecognizedGesture):
        """Add a recognized gesture to the sequence."""
        self.gestures.append(gesture)
        
        if len(self.gestures) == 1:
            self.start_time = gesture.start_time
        self.end_time = gesture.end_time
    
    def get_labels(self) -> List[str]:
        """Get list of gesture labels in sequence."""
        return [g.label for g in self.gestures]
    
    def get_raw_text(self) -> str:
        """Get raw concatenation of gesture labels."""
        parts = []
        for g in self.gestures:
            if g.is_word_level:
                parts.append(f" {g.semantic_meaning or g.label} ")
            else:
                parts.append(g.label)
        return "".join(parts).strip()
    
    @property
    def duration(self) -> float:
        """Total sequence duration in seconds."""
        return self.end_time - self.start_time
    
    @property
    def average_confidence(self) -> float:
        """Average confidence across all gestures."""
        if not self.gestures:
            return 0.0
        return sum(g.confidence for g in self.gestures) / len(self.gestures)
    
    def clear(self):
        """Clear the sequence."""
        self.gestures.clear()
        self.start_time = 0.0
        self.end_time = 0.0
        self.is_complete = False
        self.translated_text = None
        self.translation_confidence = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'gestures': [
                {
                    'label': g.label,
                    'type': g.gesture_type.value,
                    'confidence': g.confidence,
                    'duration': g.duration,
                    'meaning': g.semantic_meaning
                }
                for g in self.gestures
            ],
            'duration': self.duration,
            'translated_text': self.translated_text,
            'confidence': self.translation_confidence
        }


@dataclass
class TranslationResult:
    """Final translation result from sign language to text.
    
    Contains the translated text along with metadata about
    the translation process and confidence.
    """
    text: str
    confidence: float
    
    # Source information
    source_sequence: Optional[GestureSequence] = None
    gesture_count: int = 0
    
    # Timing
    translation_time: float = 0.0  # Time taken to translate
    capture_duration: float = 0.0  # Duration of captured gestures
    
    # Quality metrics
    word_count: int = 0
    average_gesture_confidence: float = 0.0
    
    # Alternative translations
    alternatives: List[Tuple[str, float]] = field(default_factory=list)
    
    @property
    def is_valid(self) -> bool:
        """Check if translation is valid."""
        return bool(self.text) and self.confidence > 0.0
    
    def __str__(self) -> str:
        return self.text
