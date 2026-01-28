"""
Live Translation Page - Real-time sign language detection
Premium camera view with predictions panel
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFrame, QGridLayout, QScrollArea,
    QGraphicsDropShadowEffect, QSizePolicy, QTextEdit,
    QProgressBar
)
from PySide6.QtCore import Qt, Signal, Slot, QTimer, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QFont, QColor

from ui.styles import COLORS, ICONS
from ui.camera_widget import CameraWidget
from ml.classifier import Classifier


class PredictionDisplay(QFrame):
    """Large animated prediction display."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self._current_letter = ""
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(16)
        
        # Title
        title = QLabel("Current Prediction")
        title.setObjectName("sectionTitle")
        title.setAlignment(Qt.AlignCenter)
        
        # Large letter display
        self.letter_label = QLabel("?")
        self.letter_label.setObjectName("prediction")
        self.letter_label.setAlignment(Qt.AlignCenter)
        self.letter_label.setMinimumHeight(120)
        
        # Confidence bar
        self.confidence_bar = QProgressBar()
        self.confidence_bar.setMaximum(100)
        self.confidence_bar.setValue(0)
        self.confidence_bar.setTextVisible(False)
        self.confidence_bar.setMinimumHeight(8)
        self.confidence_bar.setMaximumHeight(8)
        
        # Confidence text
        self.confidence_label = QLabel("Confidence: 0%")
        self.confidence_label.setObjectName("status")
        self.confidence_label.setAlignment(Qt.AlignCenter)
        
        # Detection status
        self.status_label = QLabel("👀 Waiting for hand...")
        self.status_label.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 14px;")
        self.status_label.setAlignment(Qt.AlignCenter)
        
        layout.addWidget(title)
        layout.addStretch()
        layout.addWidget(self.letter_label)
        layout.addWidget(self.confidence_bar)
        layout.addWidget(self.confidence_label)
        layout.addWidget(self.status_label)
        layout.addStretch()
        
        # Setup glow effect
        self.glow = QGraphicsDropShadowEffect()
        self.glow.setBlurRadius(0)
        self.glow.setColor(QColor(139, 92, 246, 100))
        self.glow.setOffset(0, 0)
        self.letter_label.setGraphicsEffect(self.glow)
    
    def update_prediction(self, letter, confidence):
        """Update prediction with animation."""
        self.letter_label.setText(letter)
        
        conf_percent = int(confidence * 100)
        self.confidence_bar.setValue(conf_percent)
        self.confidence_label.setText(f"Confidence: {conf_percent}%")
        
        # Color based on confidence
        if confidence >= 0.9:
            color = COLORS['success']
            self.status_label.setText("✨ High confidence!")
        elif confidence >= 0.75:
            color = COLORS['primary']
            self.status_label.setText("👍 Good detection")
        else:
            color = COLORS['warning']
            self.status_label.setText("🤔 Low confidence")
        
        self.letter_label.setStyleSheet(f"color: {color};")
        
        # Animate glow on new letter
        if letter != self._current_letter:
            self._current_letter = letter
            self._animate_glow()
    
    def _animate_glow(self):
        """Animate glow effect on prediction change."""
        # Quick pulse animation
        self.glow_anim = QPropertyAnimation(self.glow, b"blurRadius")
        self.glow_anim.setDuration(300)
        self.glow_anim.setStartValue(0)
        self.glow_anim.setEndValue(40)
        self.glow_anim.setEasingCurve(QEasingCurve.OutCubic)
        self.glow_anim.start()
        
        # Reset after animation
        QTimer.singleShot(300, lambda: self.glow.setBlurRadius(20))
    
    def set_hand_detected(self, detected):
        """Update hand detection status."""
        if not detected:
            self.status_label.setText("👀 Waiting for hand...")
            self.letter_label.setText("?")
            self.confidence_bar.setValue(0)
            self.confidence_label.setText("Confidence: 0%")
            self.letter_label.setStyleSheet(f"color: {COLORS['text_muted']};")
            self._current_letter = ""
    
    def reset(self):
        """Reset display."""
        self.set_hand_detected(False)


class SentenceBuilder(QFrame):
    """Build sentences from detected letters."""
    
    clear_requested = Signal()
    copy_requested = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self._sentence = ""
        self._last_letter = ""
        self._last_letter_time = 0
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)
        
        # Header
        header = QHBoxLayout()
        title = QLabel("📝 Sentence Builder")
        title.setObjectName("sectionTitle")
        
        # Action buttons
        self.copy_btn = QPushButton("📋 Copy")
        self.copy_btn.setObjectName("ghost")
        self.copy_btn.clicked.connect(lambda: self.copy_requested.emit(self._sentence))
        
        self.clear_btn = QPushButton("🗑️ Clear")
        self.clear_btn.setObjectName("ghost")
        self.clear_btn.clicked.connect(self._clear)
        
        header.addWidget(title)
        header.addStretch()
        header.addWidget(self.copy_btn)
        header.addWidget(self.clear_btn)
        layout.addLayout(header)
        
        # Sentence display
        self.sentence_label = QLabel("Start signing to build a sentence...")
        self.sentence_label.setStyleSheet(f"""
            font-size: 24px;
            font-weight: 500;
            color: {COLORS['text_primary']};
            padding: 16px;
            background-color: {COLORS['bg_input']};
            border-radius: 12px;
            min-height: 60px;
        """)
        self.sentence_label.setWordWrap(True)
        self.sentence_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        layout.addWidget(self.sentence_label)
    
    def add_letter(self, letter):
        """Add a letter to the sentence with debouncing."""
        import time
        current_time = time.time()
        
        # Debounce - don't add same letter within 1 second
        if letter == self._last_letter and (current_time - self._last_letter_time) < 1.0:
            return
        
        self._last_letter = letter
        self._last_letter_time = current_time
        
        # Handle special gestures
        if letter.startswith("✨"):
            gesture = letter.replace("✨", "").strip()
            if gesture.lower() == "wave":
                self._sentence += " "
            elif gesture.lower() == "thumbs_up":
                self._sentence += "👍"
        else:
            self._sentence += letter
        
        self._update_display()
    
    def _update_display(self):
        """Update sentence display."""
        if self._sentence:
            self.sentence_label.setText(self._sentence)
        else:
            self.sentence_label.setText("Start signing to build a sentence...")
    
    def _clear(self):
        """Clear the sentence."""
        self._sentence = ""
        self._last_letter = ""
        self._update_display()
        self.clear_requested.emit()
    
    def get_sentence(self):
        return self._sentence


class ModeToggle(QFrame):
    """Toggle between static and dynamic gesture modes."""
    
    mode_changed = Signal(str)  # 'static' or 'dynamic'
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self._current_mode = "static"
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        
        self.static_btn = QPushButton("🔤 Letters (Static)")
        self.static_btn.setCheckable(True)
        self.static_btn.setChecked(True)
        self.static_btn.clicked.connect(lambda: self._set_mode("static"))
        
        self.dynamic_btn = QPushButton("👋 Gestures (Dynamic)")
        self.dynamic_btn.setCheckable(True)
        self.dynamic_btn.clicked.connect(lambda: self._set_mode("dynamic"))
        
        layout.addWidget(self.static_btn)
        layout.addWidget(self.dynamic_btn)
    
    def _set_mode(self, mode):
        self._current_mode = mode
        self.static_btn.setChecked(mode == "static")
        self.dynamic_btn.setChecked(mode == "dynamic")
        self.mode_changed.emit(mode)
    
    def get_mode(self):
        return self._current_mode


class LivePage(QWidget):
    """Live translation page with camera and predictions."""
    
    # Signals
    back_requested = Signal()
    translation_made = Signal(str, float, str)  # label, confidence, type
    
    def __init__(self, classifier=None, db_service=None, user_data=None, parent=None):
        super().__init__(parent)
        self.classifier = classifier or Classifier()
        self.db = db_service
        self.user = user_data or {}
        self._model_loaded = self.classifier.load()
        self._setup_ui()
        self._connect_signals()
    
    def _setup_ui(self):
        """Setup live translation UI."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(32, 24, 32, 24)
        main_layout.setSpacing(20)
        
        # === HEADER ===
        header = QHBoxLayout()
        
        back_btn = QPushButton("← Back")
        back_btn.setObjectName("ghost")
        back_btn.clicked.connect(self.back_requested.emit)
        
        title = QLabel("🔴 Live Translation")
        title.setObjectName("pageTitle")
        
        # Status pills
        self.fps_pill = QLabel("FPS: --")
        self.fps_pill.setObjectName("statusPill")
        
        self.model_pill = QLabel("Model Ready" if self._model_loaded else "No Model")
        if self._model_loaded:
            self.model_pill.setObjectName("statusPillSuccess")
        else:
            self.model_pill.setObjectName("statusPillDanger")
        
        header.addWidget(back_btn)
        header.addWidget(title)
        header.addStretch()
        header.addWidget(self.fps_pill)
        header.addWidget(self.model_pill)
        
        main_layout.addLayout(header)
        
        # === MODE TOGGLE ===
        self.mode_toggle = ModeToggle()
        main_layout.addWidget(self.mode_toggle)
        
        # === MAIN CONTENT ===
        content_layout = QHBoxLayout()
        content_layout.setSpacing(24)
        
        # Left: Camera
        camera_container = QFrame()
        camera_container.setObjectName("cameraView")
        camera_layout = QVBoxLayout(camera_container)
        camera_layout.setContentsMargins(4, 4, 4, 4)
        
        self.camera_widget = CameraWidget()
        camera_layout.addWidget(self.camera_widget)
        
        # Camera controls
        controls = QHBoxLayout()
        controls.setSpacing(12)
        
        self.start_btn = QPushButton("▶️ Start Camera")
        self.start_btn.setObjectName("primary")
        self.start_btn.clicked.connect(self._toggle_camera)
        
        controls.addStretch()
        controls.addWidget(self.start_btn)
        controls.addStretch()
        
        camera_layout.addLayout(controls)
        
        # Right: Prediction Panel
        right_panel = QVBoxLayout()
        right_panel.setSpacing(16)
        
        self.prediction_display = PredictionDisplay()
        self.sentence_builder = SentenceBuilder()
        
        right_panel.addWidget(self.prediction_display, 2)
        right_panel.addWidget(self.sentence_builder, 1)
        
        content_layout.addWidget(camera_container, 3)
        content_layout.addLayout(right_panel, 2)
        
        main_layout.addLayout(content_layout)
    
    def _connect_signals(self):
        """Connect signals."""
        # Camera signals
        self.camera_widget.features_ready.connect(self._on_features)
        self.camera_widget.hand_detected.connect(self._on_hand_detected)
        self.camera_widget.fps_updated.connect(
            lambda f: self.fps_pill.setText(f"FPS: {f:.0f}")
        )
        self.camera_widget.dynamic_gesture_detected.connect(self._on_dynamic_gesture)
        
        # Mode toggle
        self.mode_toggle.mode_changed.connect(self._on_mode_changed)
        
        # Sentence builder
        self.sentence_builder.copy_requested.connect(self._copy_to_clipboard)
    
    def _toggle_camera(self):
        """Start/stop camera."""
        if self.camera_widget.is_active():
            self.camera_widget.stop()
            self.start_btn.setText("▶️ Start Camera")
            self.start_btn.setObjectName("primary")
            self.prediction_display.reset()
        else:
            if self.camera_widget.start():
                self.start_btn.setText("⏹️ Stop Camera")
                self.start_btn.setObjectName("danger")
            else:
                self.start_btn.setText("❌ Camera Error")
        
        # Re-apply style
        self.start_btn.style().unpolish(self.start_btn)
        self.start_btn.style().polish(self.start_btn)
    
    @Slot(object)
    def _on_features(self, features):
        """Handle extracted features for prediction."""
        if not self._model_loaded or not features is not None:
            return
        
        # Only predict in static mode
        if self.mode_toggle.get_mode() != "static":
            return
        
        label, confidence = self.classifier.predict(features)
        
        if label and confidence > 0.75:
            self.prediction_display.update_prediction(label, confidence)
            self.sentence_builder.add_letter(label)
            
            # Save to history
            self._save_translation(label, confidence, "static")
    
    @Slot(str, float)
    def _on_dynamic_gesture(self, name, confidence):
        """Handle dynamic gesture detection."""
        if self.mode_toggle.get_mode() != "dynamic":
            return
        
        display_name = f"✨{name}"
        self.prediction_display.update_prediction(display_name, confidence)
        self.sentence_builder.add_letter(display_name)
        
        # Save to history
        self._save_translation(name, confidence, "dynamic")
    
    @Slot(bool)
    def _on_hand_detected(self, detected):
        """Handle hand detection status."""
        self.prediction_display.set_hand_detected(detected)
    
    def _on_mode_changed(self, mode):
        """Handle mode change."""
        self.camera_widget.set_dynamic_gestures_enabled(mode == "dynamic")
        self.prediction_display.reset()
    
    def _save_translation(self, label, confidence, gesture_type):
        """Save translation to history (async)."""
        if not self.db or self.user.get("guest"):
            return
        
        # Emit signal for parent to handle
        self.translation_made.emit(label, confidence, gesture_type)
    
    def _copy_to_clipboard(self, text):
        """Copy text to clipboard."""
        from PySide6.QtWidgets import QApplication
        QApplication.clipboard().setText(text)
    
    def start_camera(self):
        """Start camera externally."""
        if not self.camera_widget.is_active():
            self._toggle_camera()
    
    def stop_camera(self):
        """Stop camera externally."""
        if self.camera_widget.is_active():
            self._toggle_camera()
    
    def cleanup(self):
        """Cleanup resources."""
        self.camera_widget.release()
