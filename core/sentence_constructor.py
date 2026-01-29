"""
Sentence Constructor - Build meaningful sentences from gesture sequences

This module handles the transformation of recognized gesture sequences
into coherent, readable text:
- Letter-to-word grouping
- Word boundary detection
- Basic grammar correction
- Punctuation insertion
- Word pattern recognition
"""
import re
import time
from typing import Optional, List, Tuple, Dict, Set
from dataclasses import dataclass, field
from enum import Enum

from .gesture_sequence import (
    RecognizedGesture, GestureSequence, GestureType,
    TranslationResult
)
from .sign_vocabulary import SignVocabulary, SignCategory


class ConstructionMode(Enum):
    """Modes for sentence construction."""
    LETTER_BY_LETTER = "letter"    # Pure letter spelling
    WORD_RECOGNITION = "word"      # Try to recognize words
    HYBRID = "hybrid"              # Mix of both
    CONTINUOUS = "continuous"      # Continuous sentence building


@dataclass
class WordCandidate:
    """A potential word being built from letters."""
    letters: List[str] = field(default_factory=list)
    start_time: float = 0.0
    confidences: List[float] = field(default_factory=list)
    
    def get_text(self) -> str:
        return "".join(self.letters)
    
    @property
    def length(self) -> int:
        return len(self.letters)
    
    @property
    def average_confidence(self) -> float:
        if not self.confidences:
            return 0.0
        return sum(self.confidences) / len(self.confidences)


class SentenceConstructor:
    """Constructs readable sentences from gesture sequences.
    
    Handles:
    - Accumulating gestures into words
    - Word pattern recognition
    - Space/delimiter detection
    - Sentence formatting
    - Basic grammar normalization
    """
    
    def __init__(
        self,
        vocabulary: Optional[SignVocabulary] = None,
        mode: ConstructionMode = ConstructionMode.HYBRID,
        word_timeout: float = 1.5,
        sentence_timeout: float = 3.0
    ):
        """Initialize the sentence constructor.
        
        Args:
            vocabulary: Sign vocabulary for word recognition
            mode: Construction mode
            word_timeout: Seconds of inactivity to finalize word
            sentence_timeout: Seconds of inactivity to finalize sentence
        """
        self.vocabulary = vocabulary or SignVocabulary()
        self.mode = mode
        self.word_timeout = word_timeout
        self.sentence_timeout = sentence_timeout
        
        # Current state
        self._current_word = WordCandidate()
        self._words: List[str] = []
        self._gesture_sequence = GestureSequence()
        
        # Timing
        self._last_gesture_time: float = 0.0
        self._sentence_start_time: float = 0.0
        
        # Accumulated text
        self._raw_text: str = ""
        self._formatted_text: str = ""
        
        # Word boundary markers
        self._word_delimiters = {'WAVE', 'SPACE', ' ', '_', 'PAUSE'}
        
        # Common abbreviations to expand
        self._abbreviations = {
            'TY': 'Thank you',
            'TYS': 'Thank you so much',
            'NP': 'No problem',
            'PLZ': 'Please',
            'PLS': 'Please',
            'ILY': 'I love you',
            'OMG': 'Oh my god',
            'BTW': 'By the way',
            'IDK': "I don't know",
            'NVM': 'Never mind',
        }
    
    def add_gesture(self, gesture: RecognizedGesture) -> Optional[str]:
        """Add a recognized gesture to the sentence.
        
        Args:
            gesture: The recognized gesture
            
        Returns:
            Updated text if changed, None otherwise
        """
        current_time = time.time()
        
        # Record in sequence
        self._gesture_sequence.add_gesture(gesture)
        
        # Check for timeout (word boundary)
        if self._last_gesture_time > 0:
            elapsed = current_time - self._last_gesture_time
            if elapsed > self.word_timeout:
                self._finalize_word()
        
        self._last_gesture_time = current_time
        
        if self._sentence_start_time == 0:
            self._sentence_start_time = current_time
        
        # Process gesture based on type
        if gesture.is_word_level or self.vocabulary.is_word_gesture(gesture.label):
            # Word-level gesture - insert as word
            self._finalize_word()  # Finalize any pending letters
            word_text = self._get_word_text(gesture)
            self._words.append(word_text)
            
        elif gesture.label.upper() in self._word_delimiters:
            # Space/delimiter gesture
            self._finalize_word()
            
        elif self._is_letter_or_number(gesture.label):
            # Letter or number - add to current word
            self._current_word.letters.append(gesture.label.upper())
            self._current_word.confidences.append(gesture.confidence)
        
        # Update text
        self._update_text()
        
        return self._formatted_text
    
    def _is_letter_or_number(self, label: str) -> bool:
        """Check if label is a single letter or number."""
        return len(label) == 1 and (label.isalpha() or label.isdigit())
    
    def _get_word_text(self, gesture: RecognizedGesture) -> str:
        """Get text representation of a word gesture."""
        if gesture.semantic_meaning:
            return gesture.semantic_meaning
        
        sign = self.vocabulary.get_sign_by_gesture(gesture.label)
        if sign:
            return sign.text
        
        return gesture.label
    
    def _finalize_word(self):
        """Finalize current word and add to words list."""
        if self._current_word.length == 0:
            return
        
        word_text = self._current_word.get_text()
        
        # Try to recognize as known word/pattern
        if self.mode in [ConstructionMode.WORD_RECOGNITION, ConstructionMode.HYBRID]:
            recognized = self.vocabulary.recognize_word_pattern(word_text)
            if recognized:
                word_text = recognized
            else:
                # Check abbreviations
                abbrev = self._abbreviations.get(word_text.upper())
                if abbrev:
                    word_text = abbrev
        
        if word_text:
            self._words.append(word_text)
        
        # Reset current word
        self._current_word = WordCandidate(start_time=time.time())
    
    def _update_text(self):
        """Update raw and formatted text from words."""
        # Build raw text from words and current partial word
        parts = self._words.copy()
        
        # Add current word in progress (if any)
        if self._current_word.length > 0:
            parts.append(self._current_word.get_text())
        
        self._raw_text = " ".join(parts)
        
        # Format text
        self._formatted_text = self._format_text(self._raw_text)
    
    def _format_text(self, text: str) -> str:
        """Apply formatting and basic grammar normalization.
        
        Args:
            text: Raw text
            
        Returns:
            Formatted text
        """
        if not text:
            return ""
        
        # Normalize whitespace
        text = " ".join(text.split())
        
        # Capitalize first letter
        if text:
            text = text[0].upper() + text[1:]
        
        # Capitalize "I" when standalone
        text = re.sub(r'\bi\b', 'I', text)
        
        # Common contractions
        contractions = {
            r'\bI M\b': "I'm",
            r'\bDONT\b': "don't",
            r'\bWONT\b': "won't",
            r'\bCANT\b': "can't",
            r'\bYOURE\b': "you're",
            r'\bTHEYRE\b': "they're",
            r'\bWERE\b': "we're",
            r'\bILL\b': "I'll",
            r'\bYOULL\b': "you'll",
        }
        
        for pattern, replacement in contractions.items():
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
        
        return text
    
    def check_timeout(self) -> Tuple[bool, bool]:
        """Check for word and sentence timeouts.
        
        Returns:
            (word_timeout, sentence_timeout) booleans
        """
        if self._last_gesture_time == 0:
            return False, False
        
        elapsed = time.time() - self._last_gesture_time
        
        word_timeout = elapsed >= self.word_timeout
        sentence_timeout = elapsed >= self.sentence_timeout
        
        return word_timeout, sentence_timeout
    
    def finalize_sentence(self) -> TranslationResult:
        """Finalize and return the complete sentence.
        
        Returns:
            TranslationResult with the complete translation
        """
        # Finalize any pending word
        self._finalize_word()
        self._update_text()
        
        # Mark sequence as complete
        self._gesture_sequence.is_complete = True
        self._gesture_sequence.translated_text = self._formatted_text
        self._gesture_sequence.translation_confidence = (
            self._gesture_sequence.average_confidence
        )
        
        # Create result
        result = TranslationResult(
            text=self._formatted_text,
            confidence=self._gesture_sequence.average_confidence,
            source_sequence=self._gesture_sequence,
            gesture_count=len(self._gesture_sequence.gestures),
            capture_duration=time.time() - self._sentence_start_time if self._sentence_start_time else 0,
            word_count=len(self._words),
            average_gesture_confidence=self._gesture_sequence.average_confidence
        )
        
        return result
    
    def get_current_text(self) -> str:
        """Get current formatted text (may be incomplete)."""
        self._update_text()
        return self._formatted_text
    
    def get_raw_text(self) -> str:
        """Get raw unformatted text."""
        return self._raw_text
    
    def get_preview(self) -> str:
        """Get preview of current state for UI display.
        
        Returns:
            String showing words + current partial word
        """
        parts = []
        
        # Add finalized words
        for word in self._words:
            parts.append(word)
        
        # Add current word in progress
        if self._current_word.length > 0:
            parts.append(f"[{self._current_word.get_text()}]")
        
        return " ".join(parts) if parts else "(waiting...)"
    
    def get_gesture_count(self) -> int:
        """Get total number of gestures in sequence."""
        return len(self._gesture_sequence.gestures)
    
    def get_word_count(self) -> int:
        """Get number of completed words."""
        return len(self._words)
    
    def clear(self):
        """Clear all accumulated data."""
        self._current_word = WordCandidate()
        self._words.clear()
        self._gesture_sequence = GestureSequence()
        self._last_gesture_time = 0.0
        self._sentence_start_time = 0.0
        self._raw_text = ""
        self._formatted_text = ""
    
    def remove_last_word(self) -> bool:
        """Remove the last word (for correction).
        
        Returns:
            True if a word was removed
        """
        if self._current_word.length > 0:
            self._current_word = WordCandidate()
            self._update_text()
            return True
        elif self._words:
            self._words.pop()
            self._update_text()
            return True
        return False
    
    def remove_last_letter(self) -> bool:
        """Remove the last letter (for correction).
        
        Returns:
            True if a letter was removed
        """
        if self._current_word.length > 0:
            self._current_word.letters.pop()
            if self._current_word.confidences:
                self._current_word.confidences.pop()
            self._update_text()
            return True
        elif self._words:
            # Pop last word and convert to current partial word
            last_word = self._words.pop()
            if len(last_word) > 1:
                self._current_word.letters = list(last_word[:-1])
            self._update_text()
            return True
        return False
    
    def insert_space(self):
        """Manually insert a space (word boundary)."""
        self._finalize_word()
        self._update_text()
    
    def get_sequence(self) -> GestureSequence:
        """Get the underlying gesture sequence."""
        return self._gesture_sequence


class ContinuousSentenceBuilder:
    """Builds sentences continuously with real-time updates.
    
    Designed for live translation where text is updated as
    gestures are recognized, with visual feedback for
    partial words and confidence.
    """
    
    def __init__(
        self,
        vocabulary: Optional[SignVocabulary] = None,
        auto_finalize_timeout: float = 3.0
    ):
        self.constructor = SentenceConstructor(
            vocabulary=vocabulary,
            mode=ConstructionMode.CONTINUOUS
        )
        self.auto_finalize_timeout = auto_finalize_timeout
        
        # Callbacks
        self._on_text_updated: Optional[callable] = None
        self._on_word_completed: Optional[callable] = None
        self._on_sentence_completed: Optional[callable] = None
    
    def set_on_text_updated(self, callback: callable):
        """Set callback for text updates."""
        self._on_text_updated = callback
    
    def set_on_word_completed(self, callback: callable):
        """Set callback for word completion."""
        self._on_word_completed = callback
    
    def set_on_sentence_completed(self, callback: callable):
        """Set callback for sentence completion."""
        self._on_sentence_completed = callback
    
    def add_gesture(self, gesture: RecognizedGesture):
        """Add gesture and trigger appropriate callbacks."""
        prev_word_count = self.constructor.get_word_count()
        
        text = self.constructor.add_gesture(gesture)
        
        new_word_count = self.constructor.get_word_count()
        
        # Check for word completion
        if new_word_count > prev_word_count:
            if self._on_word_completed:
                self._on_word_completed(self.constructor._words[-1])
        
        # Notify text update
        if self._on_text_updated and text:
            self._on_text_updated(text, self.constructor.get_preview())
    
    def check_timeouts(self):
        """Check and handle timeouts."""
        word_timeout, sentence_timeout = self.constructor.check_timeout()
        
        if sentence_timeout:
            self.finalize()
        elif word_timeout:
            # Force word finalization
            prev_count = self.constructor.get_word_count()
            self.constructor._finalize_word()
            self.constructor._update_text()
            
            if self.constructor.get_word_count() > prev_count:
                if self._on_word_completed:
                    self._on_word_completed(self.constructor._words[-1])
                if self._on_text_updated:
                    self._on_text_updated(
                        self.constructor.get_current_text(),
                        self.constructor.get_preview()
                    )
    
    def finalize(self) -> TranslationResult:
        """Finalize current sentence."""
        result = self.constructor.finalize_sentence()
        
        if self._on_sentence_completed and result.text:
            self._on_sentence_completed(result)
        
        return result
    
    def clear(self):
        """Clear and reset."""
        self.constructor.clear()
    
    def get_current_text(self) -> str:
        """Get current text."""
        return self.constructor.get_current_text()
    
    def get_preview(self) -> str:
        """Get preview text."""
        return self.constructor.get_preview()
