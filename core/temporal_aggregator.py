"""
Temporal Aggregator - Multi-frame gesture aggregation with temporal context

This module handles temporal analysis of gesture sequences:
- Smoothing predictions across frames
- Detecting gesture boundaries (start/end)
- Aggregating consecutive frames into stable gesture recognitions
- Handling transitions between gestures
"""
import time
import numpy as np
from collections import deque
from typing import Optional, List, Tuple, Dict, Callable
from dataclasses import dataclass, field
from enum import Enum

from .gesture_sequence import (
    GestureFrame, RecognizedGesture, GestureType, 
    GestureConfidence
)


class AggregationState(Enum):
    """States for the temporal aggregation FSM."""
    IDLE = "idle"                    # No hand detected
    TRACKING = "tracking"            # Hand detected, building gesture
    STABLE = "stable"                # Gesture is stable
    TRANSITIONING = "transitioning"  # Transitioning between gestures


@dataclass
class GestureCandidate:
    """A candidate gesture being tracked during aggregation."""
    label: str
    gesture_type: GestureType
    
    # Frame tracking
    start_frame: int
    end_frame: int
    frame_ids: List[int] = field(default_factory=list)
    
    # Confidence tracking
    confidences: List[float] = field(default_factory=list)
    peak_confidence: float = 0.0
    
    # Timing
    start_time: float = 0.0
    last_seen_time: float = 0.0
    
    @property
    def duration_frames(self) -> int:
        return self.end_frame - self.start_frame + 1
    
    @property
    def average_confidence(self) -> float:
        if not self.confidences:
            return 0.0
        return sum(self.confidences) / len(self.confidences)
    
    @property
    def consistency(self) -> float:
        """How consistent this gesture has been (0-1)."""
        if len(self.confidences) < 2:
            return 1.0
        # Lower variance = higher consistency
        variance = np.var(self.confidences)
        return max(0.0, 1.0 - variance)


class TemporalAggregator:
    """Aggregates gesture predictions across time for stable recognition.
    
    Uses a sliding window approach with majority voting and confidence
    weighting to produce stable gesture recognitions from noisy
    frame-by-frame predictions.
    
    Key features:
    - Temporal smoothing with configurable window
    - Gesture boundary detection
    - Confidence-weighted voting
    - Transition handling between gestures
    - Support for both static and dynamic gestures
    """
    
    def __init__(
        self,
        window_size: int = 15,
        stability_threshold: int = 5,
        min_confidence: float = 0.5,
        transition_frames: int = 3,
        fps: int = 30
    ):
        """Initialize the temporal aggregator.
        
        Args:
            window_size: Number of frames to consider for voting
            stability_threshold: Minimum consecutive frames for stable gesture
            min_confidence: Minimum confidence to consider a prediction
            transition_frames: Frames of tolerance for gesture transitions
            fps: Expected frame rate (for timing calculations)
        """
        self.window_size = window_size
        self.stability_threshold = stability_threshold
        self.min_confidence = min_confidence
        self.transition_frames = transition_frames
        self.fps = fps
        
        # Frame buffer
        self._frame_buffer: deque[GestureFrame] = deque(maxlen=window_size)
        
        # Prediction history for voting
        self._prediction_history: deque[Tuple[str, float]] = deque(maxlen=window_size)
        
        # Current state
        self._state = AggregationState.IDLE
        self._current_candidate: Optional[GestureCandidate] = None
        self._last_stable_gesture: Optional[RecognizedGesture] = None
        
        # Frame counter
        self._frame_count = 0
        self._no_hand_count = 0
        
        # Callbacks
        self._on_gesture_recognized: Optional[Callable] = None
        self._on_state_change: Optional[Callable] = None
        
        # Statistics
        self._total_gestures_recognized = 0
        self._recognition_times: List[float] = []
    
    def set_on_gesture_recognized(self, callback: Callable[[RecognizedGesture], None]):
        """Set callback for when a gesture is recognized."""
        self._on_gesture_recognized = callback
    
    def set_on_state_change(self, callback: Callable[[AggregationState], None]):
        """Set callback for state changes."""
        self._on_state_change = callback
    
    def process_frame(self, frame: GestureFrame) -> Optional[RecognizedGesture]:
        """Process a new frame and return recognized gesture if stable.
        
        Args:
            frame: The gesture frame to process
            
        Returns:
            RecognizedGesture if a stable gesture is recognized, None otherwise
        """
        self._frame_count += 1
        frame.frame_id = self._frame_count
        
        # Add to buffer
        self._frame_buffer.append(frame)
        
        # Handle no hand detection
        if not frame.hand_detected:
            self._no_hand_count += 1
            
            # If we were tracking a gesture, check if we should finalize it
            if self._state == AggregationState.TRACKING and self._current_candidate:
                if self._no_hand_count > self.transition_frames:
                    return self._finalize_gesture()
            
            if self._no_hand_count > self.window_size // 2:
                self._change_state(AggregationState.IDLE)
            
            return None
        
        # Reset no-hand counter
        self._no_hand_count = 0
        
        # Add prediction to history if valid
        if frame.predicted_label and frame.confidence >= self.min_confidence:
            self._prediction_history.append((frame.predicted_label, frame.confidence))
        
        # Perform temporal voting
        voted_label, voted_confidence = self._perform_voting()
        
        if voted_label is None:
            return None
        
        # Update state machine
        return self._update_state(voted_label, voted_confidence, frame)
    
    def _perform_voting(self) -> Tuple[Optional[str], float]:
        """Perform confidence-weighted voting on prediction history.
        
        Returns:
            (winning_label, aggregated_confidence) or (None, 0.0)
        """
        if len(self._prediction_history) < 2:
            return None, 0.0
        
        # Aggregate votes by label
        label_votes: Dict[str, List[float]] = {}
        
        for label, confidence in self._prediction_history:
            if label not in label_votes:
                label_votes[label] = []
            label_votes[label].append(confidence)
        
        # Find winner
        best_label = None
        best_score = 0.0
        
        for label, confidences in label_votes.items():
            # Score = count * average_confidence
            count = len(confidences)
            avg_conf = sum(confidences) / count
            score = count * avg_conf
            
            if score > best_score:
                best_score = score
                best_label = label
        
        if best_label is None:
            return None, 0.0
        
        # Calculate final confidence
        label_confidences = label_votes[best_label]
        consistency = len(label_confidences) / len(self._prediction_history)
        avg_confidence = sum(label_confidences) / len(label_confidences)
        
        # Require minimum consistency (e.g., 40% of frames agree)
        if consistency < 0.4:
            return None, 0.0
        
        # Boost confidence based on consistency
        final_confidence = avg_confidence * (0.5 + 0.5 * consistency)
        
        return best_label, min(1.0, final_confidence)
    
    def _update_state(
        self, 
        label: str, 
        confidence: float, 
        frame: GestureFrame
    ) -> Optional[RecognizedGesture]:
        """Update state machine and return gesture if recognized.
        
        Args:
            label: Voted gesture label
            confidence: Aggregated confidence
            frame: Current frame
            
        Returns:
            RecognizedGesture if stable, None otherwise
        """
        current_time = time.time()
        
        if self._state == AggregationState.IDLE:
            # Start tracking new gesture
            self._start_candidate(label, frame.gesture_type, frame.frame_id, current_time)
            self._change_state(AggregationState.TRACKING)
            return None
        
        elif self._state == AggregationState.TRACKING:
            if self._current_candidate is None:
                self._start_candidate(label, frame.gesture_type, frame.frame_id, current_time)
                return None
            
            if label == self._current_candidate.label:
                # Same gesture - update candidate
                self._update_candidate(frame.frame_id, confidence, current_time)
                
                # Check if stable
                if self._current_candidate.duration_frames >= self.stability_threshold:
                    self._change_state(AggregationState.STABLE)
                    return self._finalize_gesture()
            else:
                # Different gesture - start transition
                self._change_state(AggregationState.TRANSITIONING)
                
                # If current candidate was substantial, finalize it first
                if self._current_candidate.duration_frames >= self.stability_threshold // 2:
                    gesture = self._finalize_gesture()
                    self._start_candidate(label, frame.gesture_type, frame.frame_id, current_time)
                    return gesture
                else:
                    # Abandon short candidate, start new one
                    self._start_candidate(label, frame.gesture_type, frame.frame_id, current_time)
            
            return None
        
        elif self._state == AggregationState.STABLE:
            if self._current_candidate and label == self._current_candidate.label:
                # Still same gesture
                self._update_candidate(frame.frame_id, confidence, current_time)
                return None
            else:
                # New gesture starting
                self._change_state(AggregationState.TRACKING)
                self._start_candidate(label, frame.gesture_type, frame.frame_id, current_time)
                return None
        
        elif self._state == AggregationState.TRANSITIONING:
            # Allow brief transition period
            if self._current_candidate and label == self._current_candidate.label:
                self._update_candidate(frame.frame_id, confidence, current_time)
                self._change_state(AggregationState.TRACKING)
            return None
        
        return None
    
    def _start_candidate(
        self, 
        label: str, 
        gesture_type: GestureType,
        frame_id: int, 
        timestamp: float
    ):
        """Start tracking a new gesture candidate."""
        self._current_candidate = GestureCandidate(
            label=label,
            gesture_type=gesture_type,
            start_frame=frame_id,
            end_frame=frame_id,
            frame_ids=[frame_id],
            start_time=timestamp,
            last_seen_time=timestamp
        )
    
    def _update_candidate(self, frame_id: int, confidence: float, timestamp: float):
        """Update current gesture candidate with new frame data."""
        if self._current_candidate:
            self._current_candidate.end_frame = frame_id
            self._current_candidate.frame_ids.append(frame_id)
            self._current_candidate.confidences.append(confidence)
            self._current_candidate.peak_confidence = max(
                self._current_candidate.peak_confidence, 
                confidence
            )
            self._current_candidate.last_seen_time = timestamp
    
    def _finalize_gesture(self) -> Optional[RecognizedGesture]:
        """Finalize current candidate into a recognized gesture."""
        if not self._current_candidate:
            return None
        
        candidate = self._current_candidate
        
        # Create recognized gesture
        gesture = RecognizedGesture(
            label=candidate.label,
            gesture_type=candidate.gesture_type,
            confidence=candidate.average_confidence,
            start_time=candidate.start_time,
            end_time=candidate.last_seen_time,
            frame_count=candidate.duration_frames,
            supporting_frames=candidate.frame_ids.copy()
        )
        
        # Update statistics
        self._total_gestures_recognized += 1
        self._last_stable_gesture = gesture
        
        # Callback
        if self._on_gesture_recognized:
            self._on_gesture_recognized(gesture)
        
        # Reset candidate
        self._current_candidate = None
        
        return gesture
    
    def _change_state(self, new_state: AggregationState):
        """Change aggregation state with callback."""
        if new_state != self._state:
            old_state = self._state
            self._state = new_state
            
            if self._on_state_change:
                self._on_state_change(new_state)
    
    def force_finalize(self) -> Optional[RecognizedGesture]:
        """Force finalization of current gesture (e.g., on timeout).
        
        Returns:
            The finalized gesture if one was being tracked
        """
        if self._current_candidate and self._current_candidate.duration_frames >= 2:
            return self._finalize_gesture()
        return None
    
    def get_current_prediction(self) -> Tuple[Optional[str], float]:
        """Get current real-time prediction (may not be stable).
        
        Returns:
            (label, confidence) of current best prediction
        """
        return self._perform_voting()
    
    def get_state(self) -> AggregationState:
        """Get current aggregation state."""
        return self._state
    
    def get_buffer_size(self) -> int:
        """Get number of frames in buffer."""
        return len(self._frame_buffer)
    
    def get_statistics(self) -> Dict:
        """Get aggregation statistics."""
        return {
            'total_frames_processed': self._frame_count,
            'total_gestures_recognized': self._total_gestures_recognized,
            'current_state': self._state.value,
            'buffer_size': len(self._frame_buffer),
            'current_candidate': self._current_candidate.label if self._current_candidate else None
        }
    
    def clear(self):
        """Clear all buffers and reset state."""
        self._frame_buffer.clear()
        self._prediction_history.clear()
        self._state = AggregationState.IDLE
        self._current_candidate = None
        self._frame_count = 0
        self._no_hand_count = 0
    
    def reset_statistics(self):
        """Reset only statistics, keep buffers."""
        self._total_gestures_recognized = 0
        self._recognition_times.clear()
