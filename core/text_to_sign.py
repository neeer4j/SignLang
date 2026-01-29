"""
Text-to-Sign Translator - Reverse translation from text to sign language

This module handles the conversion of text input into sign language
representations for two-way communication:
- Text parsing and tokenization
- Word-to-sign lookup
- Letter-by-letter fallback
- Sign sequence generation for visualization
"""
import re
from typing import Optional, List, Tuple, Dict, Generator
from dataclasses import dataclass, field
from enum import Enum

from .sign_vocabulary import SignVocabulary, SignDefinition, SignCategory


class SignOutputType(Enum):
    """Types of sign output for visualization."""
    WORD_SIGN = "word"          # Complete word gesture
    LETTER_SPELL = "letter"     # Letter-by-letter spelling
    NUMBER = "number"           # Number gesture
    FINGERSPELL = "fingerspell" # Fingerspelling word


@dataclass
class SignOutput:
    """A single sign to be displayed/animated.
    
    Represents one unit of sign language output for visualization.
    """
    sign_id: str
    text: str                    # Original text
    display_text: str            # What to show user
    output_type: SignOutputType
    
    # Visualization data
    sign_definition: Optional[SignDefinition] = None
    landmark_data: Optional[List] = None  # For animation
    video_path: Optional[str] = None       # For video demo
    
    # Timing hints
    duration_hint: float = 1.0   # Suggested display duration (seconds)
    
    # Fingerspelling letters (if output_type is FINGERSPELL or LETTER_SPELL)
    letters: List[str] = field(default_factory=list)
    
    @property
    def has_animation(self) -> bool:
        return self.landmark_data is not None or self.video_path is not None
    
    @property
    def emoji(self) -> str:
        if self.sign_definition:
            return self.sign_definition.emoji
        return ""


@dataclass
class SignSequenceResult:
    """Result of text-to-sign translation.
    
    Contains the complete sequence of signs for a text input.
    """
    original_text: str
    signs: List[SignOutput] = field(default_factory=list)
    
    # Statistics
    word_count: int = 0
    sign_count: int = 0
    fingerspelled_count: int = 0
    
    @property
    def has_signs(self) -> bool:
        return len(self.signs) > 0
    
    @property
    def total_duration(self) -> float:
        return sum(s.duration_hint for s in self.signs)
    
    def get_display_sequence(self) -> List[str]:
        """Get list of display texts for UI."""
        return [s.display_text for s in self.signs]


class TextToSignTranslator:
    """Translates text into sign language representation.
    
    Supports:
    - Word-level sign lookup
    - Fingerspelling for unknown words
    - Number handling
    - Punctuation and spacing
    - Phrase recognition
    """
    
    def __init__(self, vocabulary: Optional[SignVocabulary] = None):
        """Initialize translator.
        
        Args:
            vocabulary: Sign vocabulary for lookups
        """
        self.vocabulary = vocabulary or SignVocabulary()
        
        # Timing settings (seconds)
        self.word_sign_duration = 1.5
        self.letter_duration = 0.5
        self.pause_duration = 0.3
        
        # Phrase patterns (text -> sign sequence)
        self._phrase_patterns: Dict[str, List[str]] = {
            "thank you": ["thank_you"],
            "i love you": ["i_love_you"],
            "how are you": ["how", "you"],
            "nice to meet you": ["nice", "meet", "you"],
            "my name is": ["my", "name"],
            "what is your name": ["what", "your", "name"],
        }
    
    def translate(self, text: str, expand_fingerspelling: bool = True) -> SignSequenceResult:
        """Translate text to sign sequence.
        
        Args:
            text: Text to translate
            expand_fingerspelling: If True, expands each letter as a separate sign.
                                   If False, bundles letters into one fingerspell unit.
            
        Returns:
            SignSequenceResult with signs to display
        """
        result = SignSequenceResult(original_text=text)
        
        if not text:
            return result
        
        # Normalize text
        text = self._normalize_text(text)
        
        # Check for complete phrase match first
        phrase_signs = self._check_phrase_match(text.lower())
        if phrase_signs:
            for sign_label in phrase_signs:
                sign_output = self._create_word_sign(sign_label)
                if sign_output:
                    result.signs.append(sign_output)
            result.word_count = len(phrase_signs)
            result.sign_count = len(result.signs)
            return result
        
        # Tokenize text
        tokens = self._tokenize(text)
        
        for token in tokens:
            if not token.strip():
                continue
            
            # Check if it's a single letter
            if len(token) == 1 and token.isalpha():
                letter_sign = self._create_letter_sign(token)
                if letter_sign:
                    result.signs.append(letter_sign)
                continue
            
            # Check if it's a number (can be multi-digit)
            if token.isdigit():
                for digit in token:
                    num_sign = self._create_number_sign(digit)
                    if num_sign:
                        result.signs.append(num_sign)
                continue
            
            # Try word-level sign lookup
            word_sign = self._lookup_word_sign(token)
            
            if word_sign:
                result.signs.append(word_sign)
                result.word_count += 1
            else:
                # Fingerspell unknown words - expand each letter
                if expand_fingerspelling:
                    # Each letter becomes a separate sign for proper display
                    letter_signs = self._create_fingerspell_expanded(token)
                    result.signs.extend(letter_signs)
                    result.fingerspelled_count += 1
                else:
                    # Bundle letters into one fingerspell unit
                    fingerspell = self._create_fingerspell(token)
                    if fingerspell:
                        result.signs.append(fingerspell)
                        result.fingerspelled_count += 1
        
        result.sign_count = len(result.signs)
        return result
    
    def translate_streaming(self, text: str) -> Generator[SignOutput, None, None]:
        """Translate text and yield signs one at a time.
        
        Useful for real-time display of signs.
        
        Args:
            text: Text to translate
            
        Yields:
            SignOutput objects one at a time
        """
        result = self.translate(text)
        for sign in result.signs:
            yield sign
    
    def _normalize_text(self, text: str) -> str:
        """Normalize text for translation."""
        # Remove extra whitespace
        text = " ".join(text.split())
        
        # Remove punctuation except apostrophes
        text = re.sub(r"[^\w\s']", " ", text)
        
        return text.strip()
    
    def _tokenize(self, text: str) -> List[str]:
        """Tokenize text into words."""
        return text.split()
    
    def _check_phrase_match(self, text: str) -> Optional[List[str]]:
        """Check if text matches a known phrase."""
        for phrase, signs in self._phrase_patterns.items():
            if text == phrase or text.startswith(phrase + " "):
                return signs
        return None
    
    def _lookup_word_sign(self, word: str) -> Optional[SignOutput]:
        """Look up word in vocabulary."""
        sign_def = self.vocabulary.get_sign_by_text(word)
        
        if sign_def and sign_def.category in [SignCategory.WORD, SignCategory.PHRASE]:
            return SignOutput(
                sign_id=sign_def.id,
                text=word,
                display_text=sign_def.display_text or word,
                output_type=SignOutputType.WORD_SIGN,
                sign_definition=sign_def,
                landmark_data=sign_def.landmark_sequence if sign_def.landmark_sequence else None,
                video_path=sign_def.video_path,
                duration_hint=self.word_sign_duration
            )
        
        return None
    
    def _create_word_sign(self, sign_label: str) -> Optional[SignOutput]:
        """Create sign output from a sign label."""
        sign_def = self.vocabulary.get_sign_by_gesture(sign_label)
        
        if sign_def:
            return SignOutput(
                sign_id=sign_def.id,
                text=sign_def.text,
                display_text=sign_def.display_text,
                output_type=SignOutputType.WORD_SIGN,
                sign_definition=sign_def,
                landmark_data=sign_def.landmark_sequence if sign_def.landmark_sequence else None,
                video_path=sign_def.video_path,
                duration_hint=self.word_sign_duration
            )
        
        return None
    
    def _create_number_sign(self, digit: str) -> Optional[SignOutput]:
        """Create sign for a number."""
        sign_def = self.vocabulary.get_sign_by_text(digit)
        
        if sign_def:
            return SignOutput(
                sign_id=sign_def.id,
                text=digit,
                display_text=digit,
                output_type=SignOutputType.NUMBER,
                sign_definition=sign_def,
                duration_hint=self.letter_duration
            )
        
        # Fallback
        return SignOutput(
            sign_id=f"number_{digit}",
            text=digit,
            display_text=digit,
            output_type=SignOutputType.NUMBER,
            duration_hint=self.letter_duration
        )
    
    def _create_letter_sign(self, letter: str) -> Optional[SignOutput]:
        """Create sign for a single letter.
        
        Args:
            letter: Single letter (A-Z or a-z)
            
        Returns:
            SignOutput for the letter
        """
        if not letter.isalpha() or len(letter) != 1:
            return None
        
        letter = letter.upper()
        sign_def = self.vocabulary.get_sign_by_text(letter)
        
        return SignOutput(
            sign_id=f"letter_{letter.lower()}",
            text=letter,
            display_text=letter,
            output_type=SignOutputType.LETTER_SPELL,
            sign_definition=sign_def,
            duration_hint=self.letter_duration
        )
    
    def _create_fingerspell_expanded(self, word: str) -> List[SignOutput]:
        """Create expanded fingerspelling - each letter as a separate sign.
        
        Args:
            word: Word to fingerspell
            
        Returns:
            List of SignOutput, one per letter
        """
        signs = []
        word_upper = word.upper()
        
        for i, letter in enumerate(word_upper):
            if letter.isalpha():
                sign_def = self.vocabulary.get_sign_by_text(letter)
                
                # Add word context for first and last letters
                if i == 0:
                    description = f"Start of '{word}'"
                elif i == len(word_upper) - 1:
                    description = f"End of '{word}'"
                else:
                    description = f"'{word}' ({i+1}/{len(word_upper)})"
                
                signs.append(SignOutput(
                    sign_id=f"fingerspell_{word.lower()}_{letter.lower()}_{i}",
                    text=letter,
                    display_text=letter,
                    output_type=SignOutputType.LETTER_SPELL,
                    sign_definition=sign_def,
                    duration_hint=self.letter_duration,
                    letters=[letter]  # Single letter in list for consistency
                ))
        
        return signs
    
    def _create_fingerspell(self, word: str) -> SignOutput:
        """Create bundled fingerspelling for a word.
        
        Bundles all letters into one SignOutput for display.
        Use _create_fingerspell_expanded for letter-by-letter display.
        """
        letters = list(word.upper())
        letter_signs = []
        
        for letter in letters:
            if letter.isalpha():
                letter_signs.append(letter)
        
        total_duration = len(letter_signs) * self.letter_duration
        
        return SignOutput(
            sign_id=f"fingerspell_{word.lower()}",
            text=word,
            display_text=f"[{word.upper()}]",
            output_type=SignOutputType.FINGERSPELL,
            letters=letter_signs,
            duration_hint=total_duration
        )
    
    def get_sign_for_letter(self, letter: str) -> Optional[SignOutput]:
        """Get sign for a single letter.
        
        Args:
            letter: Single letter (A-Z)
            
        Returns:
            SignOutput for the letter
        """
        if not letter.isalpha() or len(letter) != 1:
            return None
        
        letter = letter.upper()
        sign_def = self.vocabulary.get_sign_by_text(letter)
        
        return SignOutput(
            sign_id=f"letter_{letter.lower()}",
            text=letter,
            display_text=letter,
            output_type=SignOutputType.LETTER_SPELL,
            sign_definition=sign_def,
            duration_hint=self.letter_duration
        )
    
    def get_available_words(self) -> List[str]:
        """Get list of words that have direct sign representations."""
        word_signs = self.vocabulary.get_all_words()
        return [s.text for s in word_signs]
    
    def add_phrase_pattern(self, phrase: str, sign_labels: List[str]):
        """Add a custom phrase pattern.
        
        Args:
            phrase: Text phrase (will be lowercased)
            sign_labels: List of sign labels to use
        """
        self._phrase_patterns[phrase.lower()] = sign_labels


class SignAnimator:
    """Helper class for animating sign output.
    
    Provides utilities for displaying signs with timing.
    """
    
    def __init__(self, translator: TextToSignTranslator):
        self.translator = translator
        self._current_sequence: Optional[SignSequenceResult] = None
        self._current_index: int = 0
        self._is_playing: bool = False
    
    def load_text(self, text: str):
        """Load text for animation."""
        self._current_sequence = self.translator.translate(text)
        self._current_index = 0
        self._is_playing = False
    
    def start(self):
        """Start animation playback."""
        if self._current_sequence and self._current_sequence.has_signs:
            self._is_playing = True
            self._current_index = 0
    
    def stop(self):
        """Stop animation playback."""
        self._is_playing = False
    
    def get_current_sign(self) -> Optional[SignOutput]:
        """Get current sign to display."""
        if not self._current_sequence or not self._is_playing:
            return None
        
        if self._current_index < len(self._current_sequence.signs):
            return self._current_sequence.signs[self._current_index]
        
        return None
    
    def advance(self) -> bool:
        """Advance to next sign.
        
        Returns:
            True if advanced, False if at end
        """
        if not self._current_sequence:
            return False
        
        self._current_index += 1
        
        if self._current_index >= len(self._current_sequence.signs):
            self._is_playing = False
            return False
        
        return True
    
    def get_progress(self) -> Tuple[int, int]:
        """Get current progress (current, total)."""
        if not self._current_sequence:
            return (0, 0)
        
        return (self._current_index + 1, len(self._current_sequence.signs))
    
    @property
    def is_playing(self) -> bool:
        return self._is_playing
    
    @property
    def is_complete(self) -> bool:
        if not self._current_sequence:
            return True
        return self._current_index >= len(self._current_sequence.signs)
