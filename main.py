#!/usr/bin/env python3
"""
================================================================================
                    SIGN LANGUAGE TRANSLATOR APPLICATION
================================================================================

A comprehensive real-time sign language detection and translation system
designed for two-way communication between sign language users and non-signers.

FEATURES:
---------
    • Real-time sign language to text translation
    • Sentence-level translation with temporal context aggregation
    • Support for camera input and video file processing
    • Text-to-sign reverse translation for two-way communication
    • Word-level gesture recognition (hello, thank you, yes, no, etc.)
    • Letter-by-letter fingerspelling support (A-Z)
    • Configurable translation modes (instant, word, sentence)

TECHNOLOGY STACK:
-----------------
    • Computer Vision: OpenCV, MediaPipe (Hand Landmarker)
    • Machine Learning: scikit-learn (Random Forest Classifier)
    • UI Framework: PySide6 (Qt for Python)
    • Processing Pipeline: Custom temporal aggregation & sentence construction

ARCHITECTURE:
-------------
    The application uses a modular pipeline architecture:
    
    Input Sources          Processing Pipeline           Output
    ┌──────────┐     ┌────────────────────────┐     ┌──────────────┐
    │ Camera   │────▶│ Hand Detection         │     │ Text Display │
    │ Video    │     │ Feature Extraction     │────▶│ Translation  │
    │ Text     │     │ Temporal Aggregation   │     │ Sign Visual  │
    └──────────┘     │ Sentence Construction  │     └──────────────┘
                     └────────────────────────┘

USAGE:
------
    Basic usage:
        python main.py
    
    With options:
        python main.py --mode sentence    # Sentence translation mode
        python main.py --mode instant     # Instant letter output
        python main.py --demo             # Run pipeline demo
        python main.py --debug            # Enable debug logging
        python main.py --help             # Show help message

MODULES:
--------
    core/           - Core processing pipeline
        pipeline.py             - Main SignLanguagePipeline orchestrator
        temporal_aggregator.py  - Multi-frame gesture smoothing
        sentence_constructor.py - Word/sentence building
        sign_vocabulary.py      - Sign-text vocabulary mappings
        text_to_sign.py         - Reverse translation (text → sign)
        gesture_sequence.py     - Data structures
    
    detector/       - Computer vision components
        hand_tracker.py         - MediaPipe hand detection
        features.py             - Feature extraction
        dynamic_gestures.py     - Motion-based gesture tracking
    
    ml/             - Machine learning components
        classifier.py           - Gesture classification
        heuristic_classifier.py - Rule-based classification
        trainer.py              - Model training
    
    ui/             - User interface
        main_window.py          - Application shell
        pages/                  - Application pages
        camera_widget.py        - Camera display
        video_player_widget.py  - Video playback
        sign_visualizer.py      - Text-to-sign display

AUTHOR:
-------
    College Major Project - Sign Language Translation System
    
LICENSE:
--------
    Educational/Academic Use

VERSION:
--------
    2.0.0 - Redesigned with sentence-level translation pipeline

================================================================================
"""

import sys
import os
import argparse
import logging
from typing import Optional

# Add project root to path for imports
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


# =============================================================================
# VERSION INFORMATION
# =============================================================================

__version__ = "2.0.0"
__title__ = "Sign Language Translator"
__description__ = "Real-time sign language detection and translation system"
__author__ = "College Major Project"


# =============================================================================
# LOGGING CONFIGURATION
# =============================================================================

def setup_logging(debug: bool = False, log_file: Optional[str] = None) -> logging.Logger:
    """
    Configure application logging.
    
    Args:
        debug: Enable debug-level logging
        log_file: Optional file path for logging
        
    Returns:
        Configured logger instance
    """
    level = logging.DEBUG if debug else logging.INFO
    
    # Create formatter
    formatter = logging.Formatter(
        fmt='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Setup root logger
    logger = logging.getLogger('signlanguage')
    logger.setLevel(level)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler (optional)
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


# =============================================================================
# COMMAND LINE INTERFACE
# =============================================================================

def create_argument_parser() -> argparse.ArgumentParser:
    """
    Create and configure the command-line argument parser.
    
    Returns:
        Configured ArgumentParser instance
    """
    parser = argparse.ArgumentParser(
        prog='signlanguage',
        description=f'{__title__} v{__version__} - {__description__}',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
EXAMPLES:
    python main.py                    Launch the application
    python main.py --mode sentence    Use sentence translation mode
    python main.py --demo             Run the pipeline demo
    python main.py --debug            Enable debug logging
    
For more information, see ARCHITECTURE.md
        """
    )
    
    # Mode options
    parser.add_argument(
        '--mode', '-m',
        choices=['instant', 'word', 'sentence'],
        default='sentence',
        help='Translation mode: instant (letter-by-letter), word, or sentence (default)'
    )
    
    # Demo mode
    parser.add_argument(
        '--demo',
        action='store_true',
        help='Run the pipeline demo/test instead of launching the GUI'
    )
    
    # Debug options
    parser.add_argument(
        '--debug', '-d',
        action='store_true',
        help='Enable debug logging'
    )
    
    parser.add_argument(
        '--log-file',
        type=str,
        default=None,
        help='Write logs to specified file'
    )
    
    # Version
    parser.add_argument(
        '--version', '-v',
        action='version',
        version=f'%(prog)s {__version__}'
    )
    
    # Headless mode (for testing)
    parser.add_argument(
        '--headless',
        action='store_true',
        help='Run without GUI (for testing pipeline only)'
    )
    
    return parser


# =============================================================================
# APPLICATION STARTUP
# =============================================================================

def check_dependencies() -> bool:
    """
    Check that all required dependencies are available.
    
    Returns:
        True if all dependencies are available
    """
    missing = []
    
    # Check core dependencies
    try:
        import cv2
    except ImportError:
        missing.append('opencv-python')
    
    try:
        import mediapipe
    except ImportError:
        missing.append('mediapipe')
    
    try:
        import sklearn
    except ImportError:
        missing.append('scikit-learn')
    
    try:
        import PySide6
    except ImportError:
        missing.append('PySide6')
    
    try:
        import numpy
    except ImportError:
        missing.append('numpy')
    
    if missing:
        print(f"[ERROR] Missing dependencies: {', '.join(missing)}")
        print(f"        Install with: pip install {' '.join(missing)}")
        return False
    
    return True


def check_model_files() -> dict:
    """
    Check availability of required model files.
    
    Returns:
        Dictionary with model status
    """
    from config import MODELS_DIR, MODEL_PATH, LABELS_PATH
    
    status = {
        'hand_landmarker': os.path.exists(os.path.join(MODELS_DIR, 'hand_landmarker.task')),
        'gesture_model': os.path.exists(MODEL_PATH),
        'labels': os.path.exists(LABELS_PATH),
    }
    
    return status


def print_startup_banner(logger: logging.Logger):
    """Print application startup banner."""
    banner = f"""
    +====================================================================+
    |                                                                    |
    |           SIGN LANGUAGE TRANSLATOR  v{__version__}                   |
    |                                                                    |
    |    Real-time sign language detection and translation system       |
    |    Sentence-level translation - Two-way communication             |
    |                                                                    |
    +====================================================================+
    """
    try:
        print(banner)
    except UnicodeEncodeError:
        # Fallback for terminals that don't support the characters
        print(f"\n  SIGN LANGUAGE TRANSLATOR v{__version__}\n")
    
    # Log startup info
    logger.info(f"Starting {__title__} v{__version__}")
    logger.info(f"Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    logger.info(f"Working directory: {PROJECT_ROOT}")


def run_demo():
    """
    Run the pipeline demonstration/test.
    
    This validates all core components are working correctly.
    """
    print("\n[TEST] Running Pipeline Demo...\n")
    
    # Import and run demo
    try:
        from demo_pipeline import main as demo_main
        demo_main()
    except ImportError:
        print("[ERROR] Demo module not found. Run from project root directory.")
        sys.exit(1)


def run_headless_test():
    """
    Run a headless test of the pipeline without GUI.
    
    Useful for automated testing and CI/CD.
    """
    print("\n[TEST] Running Headless Pipeline Test...\n")
    
    try:
        from core.pipeline import SignLanguagePipeline, PipelineMode
        from core.gesture_sequence import GestureType
    except ImportError as e:
        print(f"[ERROR] Could not import core modules: {e}")
        print("        Make sure the core/ directory exists with all modules.")
        return False
    
    try:
        pipeline = SignLanguagePipeline()
        pipeline.start(PipelineMode.LIVE_ACCUMULATE)
        
        # Simulate some gestures
        test_gestures = [
            ('H', 0.85), ('E', 0.82), ('L', 0.88), 
            ('L', 0.84), ('O', 0.86)
        ]
        
        print("Processing test gestures: H-E-L-L-O")
        for label, conf in test_gestures:
            pipeline.process_gesture(label, conf, GestureType.STATIC)
        
        result = pipeline.stop_and_translate()
        
        print(f"\n[OK] Translation Result: '{result.text}'")
        print(f"     Confidence: {result.confidence:.2%}")
        print(f"     Gestures: {result.gesture_count}")
        
        return result.text != ""
    except Exception as e:
        print(f"[ERROR] Headless test failed: {e}")
        return False


def launch_gui(args: argparse.Namespace, logger: logging.Logger):
    """
    Launch the main GUI application.
    
    Args:
        args: Parsed command-line arguments
        logger: Logger instance
    """
    from PySide6.QtWidgets import QApplication
    from PySide6.QtGui import QFont
    
    from ui.main_window import MainWindow
    import config
    
    # Set default translation mode from command line
    # Use getattr with fallback in case constants aren't defined
    mode_mapping = {
        'instant': getattr(config, 'TRANSLATION_MODE_INSTANT', 'instant'),
        'word': getattr(config, 'TRANSLATION_MODE_WORD', 'word'),
        'sentence': getattr(config, 'TRANSLATION_MODE_SENTENCE', 'sentence'),
    }
    config.DEFAULT_TRANSLATION_MODE = mode_mapping.get(args.mode, 'sentence')
    
    logger.info(f"Translation mode: {args.mode}")
    
    # Create Qt application
    app = QApplication(sys.argv)
    
    # Configure application
    app.setApplicationName(__title__)
    app.setApplicationVersion(__version__)
    app.setOrganizationName("SignLanguageProject")
    
    # Set application-wide font
    font = QFont("Segoe UI", 10)
    app.setFont(font)
    
    logger.info("Creating main window...")
    
    # Create and show main window
    window = MainWindow()
    window.setWindowTitle(f"{__title__} v{__version__}")
    window.show()
    
    logger.info("Application started successfully")
    print("\n[OK] Application is running. Close the window to exit.\n")
    
    # Run event loop
    exit_code = app.exec()
    
    logger.info(f"Application closed with exit code: {exit_code}")
    
    return exit_code


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

def main():
    """
    Main application entry point.
    
    Handles command-line arguments, initializes logging, checks dependencies,
    and launches the appropriate mode (GUI, demo, or headless test).
    
    Returns:
        Exit code (0 for success, non-zero for errors)
    """
    # Parse command-line arguments
    parser = create_argument_parser()
    args = parser.parse_args()
    
    # Setup logging
    logger = setup_logging(debug=args.debug, log_file=args.log_file)
    
    # Print startup banner
    print_startup_banner(logger)
    
    # Check dependencies
    if not check_dependencies():
        return 1
    
    # Check model files
    model_status = check_model_files()
    logger.info(f"Model status: {model_status}")
    
    if not model_status['hand_landmarker']:
        logger.warning("Hand landmarker model not found - download required")
        print("[WARN] Hand landmarker model not found.")
        print("       Download from: https://storage.googleapis.com/mediapipe-models/")
        print("       Place in: models/hand_landmarker.task")
    
    if not model_status['gesture_model']:
        logger.warning("Gesture classification model not found - training required")
        print("[WARN] Gesture model not trained. Use the app to collect data and train.")
    
    # Run appropriate mode
    try:
        if args.demo:
            run_demo()
            return 0
        
        elif args.headless:
            success = run_headless_test()
            return 0 if success else 1
        
        else:
            # Launch GUI application
            return launch_gui(args, logger)
    
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
        print("\n\nGoodbye!")
        return 0
    
    except Exception as e:
        logger.exception(f"Unhandled exception: {e}")
        print(f"\n[ERROR] {e}")
        if args.debug:
            import traceback
            traceback.print_exc()
        return 1


# =============================================================================
# SCRIPT EXECUTION
# =============================================================================

if __name__ == "__main__":
    sys.exit(main())

