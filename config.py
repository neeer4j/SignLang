"""
Sign Language Detector - Configuration
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
MODELS_DIR = os.path.join(BASE_DIR, "models")

# Ensure directories exist
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(MODELS_DIR, exist_ok=True)

# Camera Settings
CAMERA_INDEX = 0
FRAME_WIDTH = 640
FRAME_HEIGHT = 480
FPS = 30

# MediaPipe Settings
MAX_HANDS = 1
MIN_DETECTION_CONFIDENCE = 0.7
MIN_TRACKING_CONFIDENCE = 0.5

# Video-specific settings (lower threshold for compressed video content)
VIDEO_DETECTION_CONFIDENCE = 0.5

# Model Settings
MODEL_PATH = os.path.join(MODELS_DIR, "gesture_model.pkl")
LABELS_PATH = os.path.join(MODELS_DIR, "labels.pkl")

# ASL Alphabet Labels
ASL_LABELS = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")

# UI Colors (Dark Theme)
COLORS = {
    "bg_primary": "#1a1a2e",
    "bg_secondary": "#16213e",
    "bg_card": "#0f3460",
    "accent": "#e94560",
    "accent_hover": "#ff6b6b",
    "text_primary": "#ffffff",
    "text_secondary": "#a0a0a0",
    "success": "#00d26a",
    "warning": "#ffc107",
}

# ============================================================
# CORE PIPELINE SETTINGS (Redesigned Sign Language Processing)
# ============================================================

# Temporal Aggregation Settings
TEMPORAL_WINDOW_SIZE = 15        # Frames to consider for voting/smoothing
STABILITY_THRESHOLD = 5          # Consecutive frames for stable recognition
TRANSITION_FRAMES = 3            # Tolerance frames during gesture transition

# Translation Settings (Sentence Mode)
TRANSLATION_TIME_WINDOW = 3.0    # Seconds of inactivity before auto-translate
WORD_TIMEOUT = 1.5               # Seconds of inactivity to finalize a word
LETTER_DEBOUNCE_TIME = 0.8       # Minimum time between same letter
CONFIDENCE_THRESHOLD = 0.55      # Minimum confidence for gesture acceptance

# Translation Modes
TRANSLATION_MODE_INSTANT = "instant"      # Output each gesture immediately
TRANSLATION_MODE_SENTENCE = "sentence"    # Accumulate and output sentences
TRANSLATION_MODE_WORD = "word"            # Output complete words

# Default translation mode
DEFAULT_TRANSLATION_MODE = TRANSLATION_MODE_SENTENCE

# Gesture Recognition Settings
ENABLE_WORD_RECOGNITION = True   # Try to recognize word patterns from letters
ENABLE_DYNAMIC_GESTURES = True   # Enable motion-based gesture recognition
ENABLE_HEURISTICS = True         # Use geometric heuristics for reliable detection

# Text-to-Sign Settings
SIGN_DISPLAY_DURATION = 1.5      # Seconds to display each word sign
LETTER_DISPLAY_DURATION = 0.5    # Seconds to display each letter
FINGERSPELL_SPEED = 0.4          # Seconds per letter when fingerspelling

# ============================================================
# VIDEO PROCESSING SETTINGS
# ============================================================

SUPPORTED_VIDEO_FORMATS = ['.mp4', '.avi', '.mov', '.mkv', '.webm', '.flv', '.wmv']
DEFAULT_PLAYBACK_SPEED = 1.0
VIDEO_FAST_MODE_INTERVAL = 10    # ms between frames in fast mode
VIDEO_NORMAL_INTERVAL = 33       # ms between frames (~30 FPS)

# Video-specific processing
VIDEO_AUTO_TRANSLATE_ON_END = True  # Auto-translate when video ends
