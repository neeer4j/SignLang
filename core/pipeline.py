"""
Sign Language Processing Pipeline - Unified processing for camera and video

This is the main pipeline class that orchestrates all components:
- Gesture detection (camera or video input)
- Temporal aggregation
- Sentence construction
- Translation output

Supports:
- Live camera input
- Video file input
- Continuous translation mode
- Manual stop/translate mode
- Text-to-sign reverse translation
"""
import time
import threading
from typing import Optional, Callable, Dict, Any, Tuple, List
from dataclasses import dataclass, field
from enum import Enum
from queue import Queue, Empty

import numpy as np

from .temporal_aggregator import TemporalAggregator, AggregationState
from .sentence_constructor import SentenceConstructor, ContinuousSentenceBuilder
from .sign_vocabulary import SignVocabulary
from .text_to_sign import TextToSignTranslator, SignSequenceResult
from .gesture_sequence import (
    GestureFrame, RecognizedGesture, GestureSequence,
    GestureType, TranslationResult
)


class PipelineMode(Enum):
    """Operating modes for the pipeline."""
    IDLE = "idle"                  # Not processing
    LIVE_CONTINUOUS = "live"       # Live camera, continuous output
    LIVE_ACCUMULATE = "accumulate" # Live camera, accumulate until stop
    VIDEO_PROCESS = "video"        # Video file processing
    TEXT_TO_SIGN = "text_to_sign"  # Reverse translation mode


class TranslationMode(Enum):
    """Translation output modes."""
    INSTANT = "instant"        # Output each recognized gesture immediately
    SENTENCE = "sentence"      # Accumulate and output complete sentences
    WORD = "word"             # Output complete words


@dataclass
class PipelineConfig:
    """Configuration for the processing pipeline."""
    # Temporal aggregation
    aggregation_window: int = 15
    stability_threshold: int = 5
    min_confidence: float = 0.5
    
    # Sentence construction
    word_timeout: float = 1.5
    sentence_timeout: float = 3.0
    
    # Translation
    translation_mode: TranslationMode = TranslationMode.SENTENCE
    auto_translate_enabled: bool = True
    
    # Input settings
    target_fps: int = 30
    
    # Feature flags
    enable_word_recognition: bool = True
    enable_dynamic_gestures: bool = True
    enable_heuristics: bool = True


@dataclass 
class PipelineState:
    """Current state of the pipeline."""
    mode: PipelineMode = PipelineMode.IDLE
    is_processing: bool = False
    frames_processed: int = 0
    gestures_recognized: int = 0
    
    # Current output
    current_text: str = ""
    current_preview: str = ""
    last_gesture: Optional[str] = None
    last_confidence: float = 0.0
    
    # Timing
    start_time: float = 0.0
    last_update_time: float = 0.0


class SignLanguagePipeline:
    """Main pipeline for sign language processing.
    
    Integrates all processing components:
    - Temporal aggregation for stable gesture recognition
    - Sentence construction for meaningful output
    - Text-to-sign translation for two-way communication
    
    Usage:
        pipeline = SignLanguagePipeline()
        pipeline.start(PipelineMode.LIVE_CONTINUOUS)
        
        # In frame processing loop:
        result = pipeline.process_frame(landmarks, features, confidence)
        if result:
            print(f"Translation: {result.text}")
        
        # To get final translation:
        final = pipeline.stop_and_translate()
    """
    
    def __init__(self, config: Optional[PipelineConfig] = None):
        """Initialize the pipeline.
        
        Args:
            config: Pipeline configuration (uses defaults if None)
        """
        self.config = config or PipelineConfig()
        
        # Core components
        self.vocabulary = SignVocabulary()
        
        self.aggregator = TemporalAggregator(
            window_size=self.config.aggregation_window,
            stability_threshold=self.config.stability_threshold,
            min_confidence=self.config.min_confidence,
            fps=self.config.target_fps
        )
        
        self.sentence_builder = ContinuousSentenceBuilder(
            vocabulary=self.vocabulary,
            auto_finalize_timeout=self.config.sentence_timeout
        )
        
        self.text_to_sign = TextToSignTranslator(
            vocabulary=self.vocabulary
        )
        
        # State
        self._state = PipelineState()
        self._frame_id = 0
        
        # Callbacks
        self._on_gesture_recognized: Optional[Callable[[RecognizedGesture], None]] = None
        self._on_text_updated: Optional[Callable[[str, str], None]] = None
        self._on_translation_complete: Optional[Callable[[TranslationResult], None]] = None
        self._on_state_changed: Optional[Callable[[PipelineState], None]] = None
        
        # Setup internal callbacks
        self._setup_callbacks()
        
        # Auto-translate timer tracking
        self._last_gesture_time = 0.0
    
    def _setup_callbacks(self):
        """Setup internal component callbacks."""
        # When aggregator recognizes a gesture
        self.aggregator.set_on_gesture_recognized(self._handle_recognized_gesture)
        
        # When sentence builder updates text
        self.sentence_builder.set_on_text_updated(self._handle_text_updated)
        self.sentence_builder.set_on_sentence_completed(self._handle_sentence_complete)
    
    # === Public API ===
    
    def start(self, mode: PipelineMode = PipelineMode.LIVE_CONTINUOUS):
        """Start the processing pipeline.
        
        Args:
            mode: Operating mode for the pipeline
        """
        self.clear()
        
        self._state.mode = mode
        self._state.is_processing = True
        self._state.start_time = time.time()
        
        self._notify_state_change()
    
    def stop(self):
        """Stop the pipeline without translating."""
        self._state.is_processing = False
        self._state.mode = PipelineMode.IDLE
        self._notify_state_change()
    
    def stop_and_translate(self) -> TranslationResult:
        """Stop pipeline and get final translation.
        
        Returns:
            TranslationResult with complete translation
        """
        # Force finalize any pending gesture
        self.aggregator.force_finalize()
        
        # Get final translation
        result = self.sentence_builder.finalize()
        
        # Stop
        self._state.is_processing = False
        self._state.mode = PipelineMode.IDLE
        
        self._notify_state_change()
        
        return result
    
    def process_frame(
        self,
        landmarks: Optional[np.ndarray],
        features: Optional[np.ndarray] = None,
        predicted_label: Optional[str] = None,
        confidence: float = 0.0,
        gesture_type: GestureType = GestureType.STATIC,
        timestamp: Optional[float] = None
    ) -> Optional[str]:
        """Process a single frame through the pipeline.
        
        Args:
            landmarks: Hand landmarks (21 x 3 array)
            features: Extracted features for classification
            predicted_label: ML model prediction (if available)
            confidence: Prediction confidence
            gesture_type: Type of gesture detected
            timestamp: Frame timestamp (uses current time if None)
            
        Returns:
            Updated text if changed, None otherwise
        """
        if not self._state.is_processing:
            return None
        
        self._frame_id += 1
        current_time = timestamp or time.time()
        
        # Create frame object
        frame = GestureFrame(
            timestamp=current_time,
            frame_id=self._frame_id,
            landmarks=landmarks,
            features=features,
            predicted_label=predicted_label,
            confidence=confidence,
            gesture_type=gesture_type,
            hand_detected=landmarks is not None
        )
        
        # Update state
        self._state.frames_processed = self._frame_id
        self._state.last_update_time = current_time
        
        if predicted_label and confidence > 0:
            self._state.last_gesture = predicted_label
            self._state.last_confidence = confidence
        
        # Process through aggregator
        recognized = self.aggregator.process_frame(frame)
        
        # Check for auto-translate timeout
        if self.config.auto_translate_enabled and self._state.mode == PipelineMode.LIVE_ACCUMULATE:
            self._check_auto_translate()
        
        # Return current text
        return self._state.current_text if recognized else None
    
    def process_gesture(
        self,
        label: str,
        confidence: float,
        gesture_type: GestureType = GestureType.STATIC
    ) -> Optional[str]:
        """Process a pre-recognized gesture (skip aggregation).
        
        Useful when gesture has already been temporally smoothed
        by another component.
        
        Args:
            label: Gesture label
            confidence: Recognition confidence
            gesture_type: Type of gesture
            
        Returns:
            Updated text if changed
        """
        if not self._state.is_processing:
            return None
        
        if confidence < self.config.min_confidence:
            return None
        
        # Create recognized gesture directly
        current_time = time.time()
        
        gesture = RecognizedGesture(
            label=label,
            gesture_type=gesture_type,
            confidence=confidence,
            start_time=current_time,
            end_time=current_time,
            frame_count=1,
            is_word_level=self.vocabulary.is_word_gesture(label)
        )
        
        # Set semantic meaning if word-level
        if gesture.is_word_level:
            sign = self.vocabulary.get_sign_by_gesture(label)
            if sign:
                gesture.semantic_meaning = sign.text
        
        # Process through sentence builder
        self._handle_recognized_gesture(gesture)
        
        return self._state.current_text
    
    def translate_text_to_sign(self, text: str) -> SignSequenceResult:
        """Translate text to sign language representation.
        
        Args:
            text: Text to translate
            
        Returns:
            SignSequenceResult with sign sequence for display
        """
        return self.text_to_sign.translate(text)
    
    def get_current_text(self) -> str:
        """Get current accumulated text."""
        return self.sentence_builder.get_current_text()
    
    def get_preview(self) -> str:
        """Get preview text (including partial words)."""
        return self.sentence_builder.get_preview()
    
    def get_state(self) -> PipelineState:
        """Get current pipeline state."""
        self._state.current_text = self.sentence_builder.get_current_text()
        self._state.current_preview = self.sentence_builder.get_preview()
        return self._state
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get processing statistics."""
        return {
            'mode': self._state.mode.value,
            'frames_processed': self._state.frames_processed,
            'gestures_recognized': self._state.gestures_recognized,
            'current_text': self._state.current_text,
            'aggregator_stats': self.aggregator.get_statistics(),
            'word_count': self.sentence_builder.constructor.get_word_count(),
            'gesture_count': self.sentence_builder.constructor.get_gesture_count()
        }
    
    def clear(self):
        """Clear all accumulated data."""
        self.aggregator.clear()
        self.sentence_builder.clear()
        
        self._state = PipelineState()
        self._frame_id = 0
        self._last_gesture_time = 0.0
    
    def insert_space(self):
        """Manually insert a word boundary."""
        self.sentence_builder.constructor.insert_space()
        self._update_state_text()
    
    def delete_last(self, delete_word: bool = False):
        """Delete last letter or word.
        
        Args:
            delete_word: If True, delete whole word; else delete letter
        """
        if delete_word:
            self.sentence_builder.constructor.remove_last_word()
        else:
            self.sentence_builder.constructor.remove_last_letter()
        self._update_state_text()
    
    # === Callbacks ===
    
    def set_on_gesture_recognized(self, callback: Callable[[RecognizedGesture], None]):
        """Set callback for gesture recognition events."""
        self._on_gesture_recognized = callback
    
    def set_on_text_updated(self, callback: Callable[[str, str], None]):
        """Set callback for text updates (text, preview)."""
        self._on_text_updated = callback
    
    def set_on_translation_complete(self, callback: Callable[[TranslationResult], None]):
        """Set callback for translation completion."""
        self._on_translation_complete = callback
    
    def set_on_state_changed(self, callback: Callable[[PipelineState], None]):
        """Set callback for state changes."""
        self._on_state_changed = callback
    
    # === Internal handlers ===
    
    def _handle_recognized_gesture(self, gesture: RecognizedGesture):
        """Handle a recognized gesture from aggregator."""
        self._state.gestures_recognized += 1
        self._last_gesture_time = time.time()
        
        # Check if it's a word-level gesture
        if self.vocabulary.is_word_gesture(gesture.label):
            gesture.is_word_level = True
            sign = self.vocabulary.get_sign_by_gesture(gesture.label)
            if sign:
                gesture.semantic_meaning = sign.text
        
        # Add to sentence builder
        self.sentence_builder.add_gesture(gesture)
        
        # External callback
        if self._on_gesture_recognized:
            self._on_gesture_recognized(gesture)
        
        self._update_state_text()
    
    def _handle_text_updated(self, text: str, preview: str):
        """Handle text update from sentence builder."""
        self._state.current_text = text
        self._state.current_preview = preview
        
        if self._on_text_updated:
            self._on_text_updated(text, preview)
    
    def _handle_sentence_complete(self, result: TranslationResult):
        """Handle sentence completion."""
        if self._on_translation_complete:
            self._on_translation_complete(result)
    
    def _check_auto_translate(self):
        """Check and trigger auto-translate if needed."""
        if self._last_gesture_time == 0:
            return
        
        elapsed = time.time() - self._last_gesture_time
        
        if elapsed >= self.config.sentence_timeout:
            # Check timeouts
            self.sentence_builder.check_timeouts()
    
    def _update_state_text(self):
        """Update state with current text."""
        self._state.current_text = self.sentence_builder.get_current_text()
        self._state.current_preview = self.sentence_builder.get_preview()
    
    def _notify_state_change(self):
        """Notify state change callback."""
        if self._on_state_changed:
            self._on_state_changed(self._state)


class PipelineManager:
    """Manages multiple pipeline instances and modes.
    
    Provides a higher-level interface for switching between
    different processing modes and input sources.
    """
    
    def __init__(self):
        self.pipeline = SignLanguagePipeline()
        self._is_running = False
    
    def start_live_translation(self, accumulate: bool = True):
        """Start live camera translation.
        
        Args:
            accumulate: If True, accumulate until stop; else continuous output
        """
        mode = PipelineMode.LIVE_ACCUMULATE if accumulate else PipelineMode.LIVE_CONTINUOUS
        self.pipeline.start(mode)
        self._is_running = True
    
    def start_video_translation(self):
        """Start video file translation."""
        self.pipeline.start(PipelineMode.VIDEO_PROCESS)
        self._is_running = True
    
    def stop_translation(self) -> TranslationResult:
        """Stop and get translation result."""
        result = self.pipeline.stop_and_translate()
        self._is_running = False
        return result
    
    def translate_text(self, text: str) -> SignSequenceResult:
        """Translate text to sign language."""
        return self.pipeline.translate_text_to_sign(text)
    
    @property
    def is_running(self) -> bool:
        return self._is_running
    
    @property
    def current_text(self) -> str:
        return self.pipeline.get_current_text()
