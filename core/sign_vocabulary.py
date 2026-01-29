"""
Sign Vocabulary - Word and phrase gesture mappings

This module contains the vocabulary of recognizable signs,
including letters, numbers, common words, and phrases.
Supports both sign-to-text and text-to-sign lookups.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
import json
import os


class SignCategory(Enum):
    """Categories of signs in the vocabulary."""
    LETTER = "letter"
    NUMBER = "number"
    WORD = "word"
    PHRASE = "phrase"
    PUNCTUATION = "punctuation"
    CONTROL = "control"  # Space, backspace, etc.


@dataclass
class SignDefinition:
    """Definition of a sign in the vocabulary.
    
    Contains information about how to recognize and display a sign.
    """
    id: str                          # Unique identifier
    text: str                        # English text representation
    category: SignCategory
    
    # Recognition info
    gesture_labels: List[str]        # Labels that trigger this sign
    is_dynamic: bool = False         # Requires motion tracking
    min_confidence: float = 0.6      # Minimum confidence threshold
    
    # Display info
    display_text: str = ""           # How to display (defaults to text)
    emoji: str = ""                  # Optional emoji representation
    description: str = ""            # Human-readable description
    
    # Animation/visualization
    landmark_sequence: List[Any] = field(default_factory=list)  # For text-to-sign
    video_path: Optional[str] = None  # Path to demonstration video
    animation_data: Dict = field(default_factory=dict)
    
    # Synonyms and variations
    synonyms: List[str] = field(default_factory=list)
    variations: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        if not self.display_text:
            self.display_text = self.text


class SignVocabulary:
    """Sign language vocabulary with bidirectional lookup.
    
    Supports:
    - Gesture label to text (sign-to-text translation)
    - Text to gesture info (text-to-sign translation)
    - Common words and phrases recognition
    - Dynamic gesture definitions
    """
    
    def __init__(self):
        self._signs: Dict[str, SignDefinition] = {}
        self._gesture_to_sign: Dict[str, str] = {}  # gesture_label -> sign_id
        self._text_to_sign: Dict[str, str] = {}     # text -> sign_id
        self._word_patterns: Dict[str, str] = {}    # letter sequence -> word
        
        self._load_default_vocabulary()
    
    def _load_default_vocabulary(self):
        """Load default ASL vocabulary."""
        # === LETTERS (A-Z) ===
        for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
            is_dynamic = letter in ['J', 'Z']  # J and Z require motion
            self._add_sign(SignDefinition(
                id=f"letter_{letter.lower()}",
                text=letter,
                category=SignCategory.LETTER,
                gesture_labels=[letter, letter.lower()],
                is_dynamic=is_dynamic,
                display_text=letter,
                description=f"ASL letter {letter}"
            ))
        
        # === NUMBERS (0-9) ===
        number_words = ['zero', 'one', 'two', 'three', 'four', 
                        'five', 'six', 'seven', 'eight', 'nine']
        for i, word in enumerate(number_words):
            self._add_sign(SignDefinition(
                id=f"number_{i}",
                text=str(i),
                category=SignCategory.NUMBER,
                gesture_labels=[str(i), word],
                display_text=str(i),
                description=f"Number {i}"
            ))
        
        # === COMMON WORDS ===
        common_words = [
            # Greetings
            SignDefinition(
                id="word_hello",
                text="Hello",
                category=SignCategory.WORD,
                gesture_labels=["hello", "wave", "WAVE", "hi"],
                is_dynamic=True,
                emoji="👋",
                description="Wave hand for hello"
            ),
            SignDefinition(
                id="word_goodbye",
                text="Goodbye",
                category=SignCategory.WORD,
                gesture_labels=["goodbye", "bye"],
                is_dynamic=True,
                emoji="👋",
                description="Wave goodbye"
            ),
            
            # Courtesy
            SignDefinition(
                id="word_thanks",
                text="Thank you",
                category=SignCategory.WORD,
                gesture_labels=["thank_you", "thanks", "thankyou"],
                emoji="🙏",
                description="Touch chin and move forward"
            ),
            SignDefinition(
                id="word_please",
                text="Please",
                category=SignCategory.WORD,
                gesture_labels=["please"],
                description="Circular motion on chest"
            ),
            SignDefinition(
                id="word_sorry",
                text="Sorry",
                category=SignCategory.WORD,
                gesture_labels=["sorry"],
                emoji="🙇",
                description="Fist on chest in circular motion"
            ),
            
            # Responses
            SignDefinition(
                id="word_yes",
                text="Yes",
                category=SignCategory.WORD,
                gesture_labels=["yes", "thumbs_up", "THUMBS_UP"],
                emoji="👍",
                description="Fist nodding like a head"
            ),
            SignDefinition(
                id="word_no",
                text="No",
                category=SignCategory.WORD,
                gesture_labels=["no", "thumbs_down", "THUMBS_DOWN"],
                emoji="👎",
                description="Index and middle finger tap thumb"
            ),
            
            # Pronouns
            SignDefinition(
                id="word_i",
                text="I",
                category=SignCategory.WORD,
                gesture_labels=["i", "me", "I_POINT"],
                description="Point to self"
            ),
            SignDefinition(
                id="word_you",
                text="You",
                category=SignCategory.WORD,
                gesture_labels=["you", "YOU_POINT"],
                description="Point to other person"
            ),
            
            # Common verbs
            SignDefinition(
                id="word_want",
                text="Want",
                category=SignCategory.WORD,
                gesture_labels=["want"],
                description="Hands pull toward body"
            ),
            SignDefinition(
                id="word_need",
                text="Need",
                category=SignCategory.WORD,
                gesture_labels=["need"],
                description="X hand moves down"
            ),
            SignDefinition(
                id="word_help",
                text="Help",
                category=SignCategory.WORD,
                gesture_labels=["help"],
                emoji="🆘",
                description="Thumbs up on flat hand, lift up"
            ),
            SignDefinition(
                id="word_stop",
                text="Stop",
                category=SignCategory.WORD,
                gesture_labels=["stop", "STOP_HAND"],
                emoji="✋",
                description="Flat hand chops into other palm"
            ),
            SignDefinition(
                id="word_love",
                text="Love",
                category=SignCategory.WORD,
                gesture_labels=["love", "heart"],
                emoji="❤️",
                description="Cross arms over chest"
            ),
            SignDefinition(
                id="word_iloveyou",
                text="I love you",
                category=SignCategory.PHRASE,
                gesture_labels=["i_love_you", "ily", "ILY"],
                emoji="🤟",
                description="ILY handshape (thumb, index, pinky)"
            ),
            
            # Questions
            SignDefinition(
                id="word_what",
                text="What?",
                category=SignCategory.WORD,
                gesture_labels=["what"],
                description="Hands palm up, shake slightly"
            ),
            SignDefinition(
                id="word_where",
                text="Where?",
                category=SignCategory.WORD,
                gesture_labels=["where"],
                description="Shake pointed index finger"
            ),
            SignDefinition(
                id="word_how",
                text="How?",
                category=SignCategory.WORD,
                gesture_labels=["how"],
                description="Backs of hands together, roll forward"
            ),
            
            # Common nouns
            SignDefinition(
                id="word_name",
                text="Name",
                category=SignCategory.WORD,
                gesture_labels=["name"],
                description="H hands tap each other"
            ),
            SignDefinition(
                id="word_water",
                text="Water",
                category=SignCategory.WORD,
                gesture_labels=["water"],
                emoji="💧",
                description="W hand taps chin"
            ),
            SignDefinition(
                id="word_food",
                text="Food",
                category=SignCategory.WORD,
                gesture_labels=["food", "eat"],
                emoji="🍽️",
                description="Flat O to mouth"
            ),
        ]
        
        for sign in common_words:
            self._add_sign(sign)
        
        # === CONTROL GESTURES ===
        controls = [
            SignDefinition(
                id="ctrl_space",
                text=" ",
                category=SignCategory.CONTROL,
                gesture_labels=["space", "SPACE", "_"],
                display_text="[SPACE]",
                description="Space between words"
            ),
            SignDefinition(
                id="ctrl_backspace",
                text="[DELETE]",
                category=SignCategory.CONTROL,
                gesture_labels=["backspace", "delete"],
                display_text="[DELETE]",
                description="Delete last character"
            ),
            SignDefinition(
                id="ctrl_enter",
                text="[ENTER]",
                category=SignCategory.CONTROL,
                gesture_labels=["enter", "newline"],
                display_text="[ENTER]",
                description="New line / Confirm"
            ),
        ]
        
        for sign in controls:
            self._add_sign(sign)
        
        # === COMMON LETTER PATTERNS TO WORDS ===
        self._word_patterns = {
            "HI": "Hi",
            "BYE": "Bye", 
            "OK": "OK",
            "YES": "Yes",
            "NO": "No",
            "HELP": "Help",
            "STOP": "Stop",
            "LOVE": "Love",
            "THANK": "Thank",
            "THANKS": "Thanks",
            "PLEASE": "Please",
            "SORRY": "Sorry",
            "WATER": "Water",
            "FOOD": "Food",
            "NAME": "Name",
            "HELLO": "Hello",
            "GOOD": "Good",
            "BAD": "Bad",
            "HOW": "How",
            "WHAT": "What",
            "WHERE": "Where",
            "WHEN": "When",
            "WHO": "Who",
            "WHY": "Why",
        }
    
    def _add_sign(self, sign: SignDefinition):
        """Add a sign to the vocabulary."""
        self._signs[sign.id] = sign
        
        # Map gesture labels to sign
        for label in sign.gesture_labels:
            self._gesture_to_sign[label.upper()] = sign.id
            self._gesture_to_sign[label.lower()] = sign.id
        
        # Map text to sign
        self._text_to_sign[sign.text.upper()] = sign.id
        self._text_to_sign[sign.text.lower()] = sign.id
        
        # Add synonyms
        for syn in sign.synonyms:
            self._text_to_sign[syn.upper()] = sign.id
            self._text_to_sign[syn.lower()] = sign.id
    
    def get_sign_by_gesture(self, gesture_label: str) -> Optional[SignDefinition]:
        """Look up sign by gesture label (for sign-to-text)."""
        sign_id = self._gesture_to_sign.get(gesture_label)
        if sign_id:
            return self._signs.get(sign_id)
        return None
    
    def get_sign_by_text(self, text: str) -> Optional[SignDefinition]:
        """Look up sign by text (for text-to-sign)."""
        sign_id = self._text_to_sign.get(text)
        if not sign_id:
            sign_id = self._text_to_sign.get(text.upper())
        if not sign_id:
            sign_id = self._text_to_sign.get(text.lower())
        if sign_id:
            return self._signs.get(sign_id)
        return None
    
    def gesture_to_text(self, gesture_label: str) -> str:
        """Convert gesture label to text representation."""
        sign = self.get_sign_by_gesture(gesture_label)
        if sign:
            return sign.display_text
        return gesture_label
    
    def text_to_gesture_info(self, text: str) -> Optional[SignDefinition]:
        """Get gesture information for text (for text-to-sign)."""
        return self.get_sign_by_text(text)
    
    def recognize_word_pattern(self, letters: str) -> Optional[str]:
        """Try to recognize a word from a sequence of letters."""
        upper = letters.upper()
        if upper in self._word_patterns:
            return self._word_patterns[upper]
        return None
    
    def is_word_gesture(self, gesture_label: str) -> bool:
        """Check if gesture represents a complete word."""
        sign = self.get_sign_by_gesture(gesture_label)
        if sign:
            return sign.category in [SignCategory.WORD, SignCategory.PHRASE]
        return False
    
    def is_dynamic_gesture(self, gesture_label: str) -> bool:
        """Check if gesture requires motion tracking."""
        sign = self.get_sign_by_gesture(gesture_label)
        if sign:
            return sign.is_dynamic
        return False
    
    def get_all_words(self) -> List[SignDefinition]:
        """Get all word-level signs in vocabulary."""
        return [
            s for s in self._signs.values() 
            if s.category in [SignCategory.WORD, SignCategory.PHRASE]
        ]
    
    def get_all_letters(self) -> List[SignDefinition]:
        """Get all letter signs in vocabulary."""
        return [
            s for s in self._signs.values()
            if s.category == SignCategory.LETTER
        ]
    
    def search_vocabulary(self, query: str) -> List[SignDefinition]:
        """Search vocabulary by text, description, or labels."""
        query_lower = query.lower()
        results = []
        
        for sign in self._signs.values():
            if (query_lower in sign.text.lower() or
                query_lower in sign.description.lower() or
                any(query_lower in label.lower() for label in sign.gesture_labels)):
                results.append(sign)
        
        return results
    
    def add_custom_word(self, text: str, gesture_labels: List[str], 
                        description: str = "", emoji: str = "") -> str:
        """Add a custom word to the vocabulary.
        
        Returns the sign ID of the new word.
        """
        sign_id = f"custom_{text.lower().replace(' ', '_')}"
        
        sign = SignDefinition(
            id=sign_id,
            text=text,
            category=SignCategory.WORD,
            gesture_labels=gesture_labels,
            description=description,
            emoji=emoji
        )
        
        self._add_sign(sign)
        return sign_id
    
    def export_vocabulary(self) -> Dict:
        """Export vocabulary to dictionary for saving."""
        return {
            sign_id: {
                'text': sign.text,
                'category': sign.category.value,
                'gesture_labels': sign.gesture_labels,
                'is_dynamic': sign.is_dynamic,
                'description': sign.description,
                'emoji': sign.emoji
            }
            for sign_id, sign in self._signs.items()
        }
