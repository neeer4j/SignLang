# Sign Language Processing Pipeline - Architecture Overview

## Overview

This document describes the redesigned sign language processing pipeline that enables:
- **Sentence-level translation** instead of letter-by-letter output
- **Temporal context aggregation** across multiple frames
- **Two-way communication** (sign-to-text and text-to-sign)
- **Unified processing** for camera and video inputs

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         SIGN LANGUAGE PIPELINE                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                   │
│  │   Camera     │    │    Video     │    │   Text       │                   │
│  │   Input      │    │    Input     │    │   Input      │                   │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘                   │
│         │                   │                   │                           │
│         └─────────┬─────────┘                   │                           │
│                   ▼                             │                           │
│  ┌────────────────────────────┐                 │                           │
│  │    Hand Detection &        │                 │                           │
│  │    Feature Extraction      │                 │                           │
│  │    (MediaPipe + Features)  │                 │                           │
│  └────────────┬───────────────┘                 │                           │
│               │                                 │                           │
│               ▼                                 │                           │
│  ┌────────────────────────────┐                 │                           │
│  │   ML Classification +      │                 │                           │
│  │   Heuristic Detection      │                 │                           │
│  └────────────┬───────────────┘                 │                           │
│               │                                 │                           │
│               ▼                                 │                           │
│  ┌────────────────────────────┐                 │                           │
│  │   Temporal Aggregator      │                 │                           │
│  │   (Multi-frame smoothing)  │                 │                           │
│  └────────────┬───────────────┘                 │                           │
│               │                                 │                           │
│               ▼                                 │                           │
│  ┌────────────────────────────┐    ┌────────────┴───────────┐               │
│  │   Sentence Constructor     │    │   Text-to-Sign         │               │
│  │   (Word/sentence building) │    │   Translator           │               │
│  └────────────┬───────────────┘    └────────────┬───────────┘               │
│               │                                 │                           │
│               ▼                                 ▼                           │
│  ┌────────────────────────────┐    ┌────────────────────────────┐           │
│  │   Translation Result       │    │   Sign Visualization       │           │
│  │   (Text output)            │    │   (Visual output)          │           │
│  └────────────────────────────┘    └────────────────────────────┘           │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Core Modules

### 1. `core/pipeline.py` - SignLanguagePipeline

The main orchestrator that coordinates all processing components.

**Key Features:**
- Unified API for camera and video input
- Three operating modes: `LIVE_CONTINUOUS`, `LIVE_ACCUMULATE`, `VIDEO_PROCESS`
- Translation modes: `INSTANT`, `WORD`, `SENTENCE`
- Callback-based event notifications

**Usage:**
```python
from core.pipeline import SignLanguagePipeline, PipelineMode

pipeline = SignLanguagePipeline()
pipeline.start(PipelineMode.LIVE_ACCUMULATE)

# Process frames
result = pipeline.process_gesture('H', 0.85, GestureType.STATIC)

# Get final translation
translation = pipeline.stop_and_translate()
print(translation.text)
```

### 2. `core/temporal_aggregator.py` - TemporalAggregator

Handles temporal smoothing of gesture predictions across multiple frames.

**Key Features:**
- Sliding window with majority voting
- Confidence-weighted predictions
- Gesture boundary detection
- State machine (IDLE → TRACKING → STABLE → TRANSITIONING)
- Configurable stability threshold

**How it works:**
1. Collects predictions over a sliding window (default 15 frames)
2. Performs majority voting with confidence weighting
3. Requires consistency threshold (40% agreement) to output
4. Requires stability threshold (5+ consecutive frames) for stable gesture

### 3. `core/sentence_constructor.py` - SentenceConstructor

Builds readable sentences from recognized gestures.

**Key Features:**
- Letter-to-word grouping
- Word pattern recognition (e.g., "H-E-L-L-O" → "Hello")
- Automatic word timeout (default 1.5s)
- Basic grammar normalization
- Support for word-level gestures

**Word Building Process:**
1. Letters accumulate into current word
2. Word boundaries detected by:
   - Timeout (1.5s of inactivity)
   - Space gesture
   - Word-level gesture
3. Completed words checked against vocabulary
4. Sentence finalized on sentence timeout (3.0s)

### 4. `core/sign_vocabulary.py` - SignVocabulary

Bidirectional vocabulary for sign-text mappings.

**Contents:**
- 26 ASL letters (A-Z)
- 10 numbers (0-9)
- 20+ common words (hello, thank you, yes, no, etc.)
- Control gestures (space, backspace)
- Word patterns for letter-sequence recognition

**Example mappings:**
```
Gesture "WAVE" → Text "Hello" 👋
Gesture "thank_you" → Text "Thank you" 🙏
Letters "H-E-L-P" → Word "Help"
```

### 5. `core/text_to_sign.py` - TextToSignTranslator

Reverse translation from text to sign language representation.

**Process:**
1. Parse and tokenize input text
2. Look up word-level signs first
3. Fall back to fingerspelling for unknown words
4. Generate sign sequence with timing hints

**Output:**
```python
result = translator.translate("Hello friend")
# Returns:
# - Sign 1: "Hello" (word sign, 1.5s)
# - Sign 2: "[FRIEND]" (fingerspell F-R-I-E-N-D, 3s)
```

### 6. `core/gesture_sequence.py` - Data Structures

Core data types for the pipeline:

- **GestureFrame**: Single frame snapshot with landmarks and predictions
- **RecognizedGesture**: Stabilized gesture after temporal analysis
- **GestureSequence**: Collection of gestures forming a translation unit
- **TranslationResult**: Final translation output with metadata

## UI Components

### `ui/pages/live_translation_page.py` - LiveTranslationPage

Updated live translation page with:
- Source tabs (Camera, Video, Text-to-Sign)
- Mode selector (Instant, Word, Sentence)
- Real-time gesture display
- Translation display with preview
- Stop & Translate button for sentence mode

### `ui/sign_visualizer.py` - SignVisualizerWidget

Text-to-sign visualization with:
- Hand landmark canvas
- Letter/word display with animations
- Fingerspelling sequence display
- Playback controls

## Configuration

Key settings in `config.py`:

```python
# Temporal Aggregation
TEMPORAL_WINDOW_SIZE = 15        # Frames for voting window
STABILITY_THRESHOLD = 5          # Frames for stable gesture

# Translation Timeouts
WORD_TIMEOUT = 1.5               # Seconds to finalize word
TRANSLATION_TIME_WINDOW = 3.0    # Seconds to auto-translate

# Confidence
CONFIDENCE_THRESHOLD = 0.55      # Minimum acceptance threshold

# Text-to-Sign
SIGN_DISPLAY_DURATION = 1.5      # Seconds per word sign
LETTER_DISPLAY_DURATION = 0.5    # Seconds per letter
```

## Translation Modes

### 1. Instant Mode
- Each recognized gesture outputs immediately
- Good for: Testing, debugging, single letters

### 2. Word Mode
- Letters accumulate until word timeout
- Words output individually
- Good for: Spelling words, vocabulary practice

### 3. Sentence Mode (Default)
- Gestures accumulate continuously
- Auto-translates on 3-second timeout
- Manual "Stop & Translate" button
- Good for: Natural signing, conversations

## Running the Demo

```bash
python demo_pipeline.py
```

This runs tests for all core components and verifies the pipeline works correctly.

## Academic Considerations

This implementation focuses on:
1. **Functional feasibility** over perfect accuracy
2. **Explainable processing** with clear pipeline stages
3. **Modular design** for extension and experimentation
4. **Real-time capability** suitable for live interaction
5. **Two-way communication** for practical usability

The system is designed as a proof-of-concept suitable for a college major project, demonstrating the key concepts of sign language processing while being achievable within academic constraints.

## Future Extensions

- Additional word-level gestures
- Custom vocabulary training
- Improved grammar correction
- Sign language animation
- Multi-language support
- Cloud-based gesture recognition
