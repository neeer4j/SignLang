"""
Sign Language Detector - Main Entry Point

A real-time sign language detection application using:
- OpenCV for video capture
- MediaPipe for hand tracking
- scikit-learn (RandomForest) for gesture classification
- PySide6 for the UI

Usage:
    python main.py
"""
import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont

from ui.main_window import MainWindow


def main():
    """Application entry point."""
    # Create application
    app = QApplication(sys.argv)
    
    # Set application-wide font
    font = QFont("Segoe UI", 10)
    app.setFont(font)
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    # Run event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
