"""
Core Sign Language Processing Module

This module contains the redesigned sign language processing pipeline with:
- Unified input processing (camera and video)
- Temporal sequence aggregation
- Sentence-level translation
- Text-to-sign reverse translation

Architecture:
    Input (Camera/Video) → GestureDetector → TemporalAggregator → SentenceConstructor → Output
                                                                              ↓
    Text Input → TextToSignTranslator → SignVisualizer → Visual Output
"""

from .pipeline import SignLanguagePipeline
from .temporal_aggregator import TemporalAggregator
from .sentence_constructor import SentenceConstructor
from .text_to_sign import TextToSignTranslator
from .sign_vocabulary import SignVocabulary
from .gesture_sequence import GestureSequence, GestureFrame

__all__ = [
    'SignLanguagePipeline',
    'TemporalAggregator', 
    'SentenceConstructor',
    'TextToSignTranslator',
    'SignVocabulary',
    'GestureSequence',
    'GestureFrame',
]
