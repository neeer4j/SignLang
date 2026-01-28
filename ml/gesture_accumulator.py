"""
Gesture Accumulator - Temporal gesture aggregation for sentence-level translation

Accumulates detected gestures over time and converts them into meaningful
words, sentences, or short paragraphs with confidence-based filtering
and temporal smoothing.
"""
import time
from collections import deque
from typing import Optional, List, Tuple, Dict
from dataclasses import dataclass, field


@dataclass
class GestureEvent:
    """Represents a single gesture detection event."""
    label: str
    confidence: float
    timestamp: float
    gesture_type: str = "static"  # "static" or "dynamic"


class GestureAccumulator:
    """Accumulates gestures over time for sentence-level translation.
    
    Features:
    - Configurable time window for auto-translation
    - Confidence threshold filtering
    - Temporal smoothing (removes rapid duplicates)
    - Word-level gesture mapping
    - Manual and automatic translation triggers
    """
    
    # Predefined word gestures (gesture label -> full word/phrase)
    WORD_GESTURES = {
        "hello": "Hello",
        "wave": "Hello",
        "goodbye": "Goodbye",
        "thank_you": "Thank you",
        "thumbs_up": "👍",
        "thumbs_down": "👎",
        "yes": "Yes",
        "no": "No",
        "please": "Please",
        "sorry": "Sorry",
        "love": "Love",
        "i_love_you": "I love you",
        "help": "Help",
        "stop": "Stop",
    }
    
    def __init__(
        self,
        time_window: float = 3.0,
        confidence_threshold: float = 0.75,
        debounce_time: float = 0.8,
        max_buffer_size: int = 100
    ):
        """Initialize the gesture accumulator.
        
        Args:
            time_window: Seconds of inactivity before auto-translate (0 to disable)
            confidence_threshold: Minimum confidence to accept a gesture
            debounce_time: Minimum time between same consecutive gestures
            max_buffer_size: Maximum number of gestures to buffer
        """
        self.time_window = time_window
        self.confidence_threshold = confidence_threshold
        self.debounce_time = debounce_time
        self.max_buffer_size = max_buffer_size
        
        # Gesture buffer
        self._buffer: deque[GestureEvent] = deque(maxlen=max_buffer_size)
        
        # Tracking
        self._last_gesture: Optional[str] = None
        self._last_gesture_time: float = 0.0
        self._last_activity_time: float = time.time()
        
        # Translation state
        self._is_accumulating: bool = False
        self._pending_translation: bool = False
    
    def start_accumulating(self):
        """Start accumulating gestures for sentence mode."""
        self._is_accumulating = True
        self._last_activity_time = time.time()
    
    def stop_accumulating(self):
        """Stop accumulating (switch to instant mode)."""
        self._is_accumulating = False
    
    def add_gesture(
        self,
        label: str,
        confidence: float,
        gesture_type: str = "static"
    ) -> Optional[str]:
        """Add a detected gesture to the buffer.
        
        Args:
            label: Gesture label (letter, number, or word gesture)
            confidence: Detection confidence (0-1)
            gesture_type: "static" or "dynamic"
            
        Returns:
            The label if accepted and in instant mode, None otherwise
        """
        current_time = time.time()
        
        # Confidence filter
        if confidence < self.confidence_threshold:
            return None
        
        # Debounce filter (same gesture within debounce time)
        if (label == self._last_gesture and 
            current_time - self._last_gesture_time < self.debounce_time):
            return None
        
        # Create gesture event
        event = GestureEvent(
            label=label,
            confidence=confidence,
            timestamp=current_time,
            gesture_type=gesture_type
        )
        
        # Update tracking
        self._last_gesture = label
        self._last_gesture_time = current_time
        self._last_activity_time = current_time
        
        # Add to buffer
        self._buffer.append(event)
        
        # In instant mode, return the label immediately
        if not self._is_accumulating:
            return label
        
        return None
    
    def check_auto_translate(self) -> bool:
        """Check if auto-translation should trigger based on time window.
        
        Returns:
            True if time window has elapsed since last gesture
        """
        if not self._is_accumulating or self.time_window <= 0:
            return False
        
        if len(self._buffer) == 0:
            return False
        
        elapsed = time.time() - self._last_activity_time
        return elapsed >= self.time_window
    
    def translate(self) -> str:
        """Convert accumulated gestures to translated text.
        
        Applies:
        - Consecutive duplicate removal
        - Word gesture mapping
        - Space handling for dynamic gestures
        
        Returns:
            Translated text string
        """
        if len(self._buffer) == 0:
            return ""
        
        result_parts = []
        prev_label = None
        
        for event in self._buffer:
            label = event.label
            
            # Skip consecutive duplicates (already debounced, but double-check)
            if label == prev_label:
                continue
            
            # Check if it's a word gesture
            label_lower = label.lower()
            if label_lower in self.WORD_GESTURES:
                # Add space before word if we have previous content
                if result_parts:
                    result_parts.append(" ")
                result_parts.append(self.WORD_GESTURES[label_lower])
                result_parts.append(" ")
            elif event.gesture_type == "dynamic":
                # Dynamic gestures that represent spaces/separators
                if label_lower in ["wave", "space"]:
                    result_parts.append(" ")
                else:
                    result_parts.append(label)
            else:
                # Regular letter/number
                result_parts.append(label)
            
            prev_label = label
        
        # Join and clean up extra spaces
        text = "".join(result_parts)
        text = " ".join(text.split())  # Normalize spaces
        
        return text
    
    def get_buffer_preview(self) -> str:
        """Get a preview of currently accumulated gestures.
        
        Returns:
            String showing accumulated gestures
        """
        if len(self._buffer) == 0:
            return ""
        
        # Show last N gestures
        preview_limit = 20
        recent = list(self._buffer)[-preview_limit:]
        
        parts = []
        for event in recent:
            if event.gesture_type == "dynamic":
                parts.append(f"[{event.label}]")
            else:
                parts.append(event.label)
        
        return " ".join(parts)
    
    def get_buffer_count(self) -> int:
        """Get number of gestures in buffer."""
        return len(self._buffer)
    
    def get_buffer_events(self) -> List[GestureEvent]:
        """Get all gesture events in buffer."""
        return list(self._buffer)
    
    def get_time_since_last_gesture(self) -> float:
        """Get seconds elapsed since last gesture."""
        return time.time() - self._last_activity_time
    
    def clear(self):
        """Clear the gesture buffer."""
        self._buffer.clear()
        self._last_gesture = None
        self._last_gesture_time = 0.0
        self._last_activity_time = time.time()
    
    def translate_and_clear(self) -> str:
        """Translate accumulated gestures and clear buffer.
        
        Returns:
            Translated text
        """
        text = self.translate()
        self.clear()
        return text
    
    def is_accumulating(self) -> bool:
        """Check if currently in accumulation mode."""
        return self._is_accumulating
    
    def set_confidence_threshold(self, threshold: float):
        """Update confidence threshold."""
        self.confidence_threshold = max(0.0, min(1.0, threshold))
    
    def set_time_window(self, seconds: float):
        """Update auto-translate time window."""
        self.time_window = max(0.0, seconds)
    
    def set_debounce_time(self, seconds: float):
        """Update debounce time."""
        self.debounce_time = max(0.0, seconds)
    
    def add_word_gesture(self, gesture_label: str, word: str):
        """Add custom word gesture mapping.
        
        Args:
            gesture_label: The gesture identifier
            word: The word/phrase it represents
        """
        self.WORD_GESTURES[gesture_label.lower()] = word
