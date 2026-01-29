"""
Live Translation Page - Real-time sign language detection
Premium camera view with video support and sentence-level translation
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFrame, QGridLayout, QScrollArea,
    QGraphicsDropShadowEffect, QSizePolicy, QTextEdit,
    QProgressBar, QTabWidget, QStackedWidget
)
from PySide6.QtCore import Qt, Signal, Slot, QTimer, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QFont, QColor

from ui.styles import COLORS, ICONS
from ui.camera_widget import CameraWidget
from ui.video_player_widget import VideoPlayerWidget
from ml.classifier import Classifier
from ml.gesture_accumulator import GestureAccumulator
from config import TRANSLATION_TIME_WINDOW, CONFIDENCE_THRESHOLD


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
    """Build sentences from detected letters with accumulation mode."""
    
    clear_requested = Signal()
    copy_requested = Signal(str)
    translate_requested = Signal()  # New signal for manual translate
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self._sentence = ""
        self._last_letter = ""
        self._last_letter_time = 0
        self._accumulation_mode = False  # Sentence mode vs instant mode
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
        
        # Buffer preview (for accumulation mode)
        self.buffer_label = QLabel("")
        self.buffer_label.setStyleSheet(f"""
            font-size: 14px;
            color: {COLORS['text_secondary']};
            padding: 8px;
        """)
        self.buffer_label.setWordWrap(True)
        self.buffer_label.hide()
        layout.addWidget(self.buffer_label)
    
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
    
    def set_sentence(self, text):
        """Set sentence directly (used by accumulator)."""
        self._sentence = text
        self._update_display()
    
    def set_buffer_preview(self, preview):
        """Show buffer preview in accumulation mode."""
        if preview:
            self.buffer_label.setText(f"📦 Buffer: {preview}")
            self.buffer_label.show()
        else:
            self.buffer_label.hide()
    
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
        self.buffer_label.hide()
        self.clear_requested.emit()
    
    def get_sentence(self):
        return self._sentence


class ModeToggle(QFrame):
    """Toggle between static, dynamic, and hybrid modes."""
    
    mode_changed = Signal(str)  # 'static', 'dynamic', or 'hybrid'
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self._current_mode = "hybrid"  # Default to hybrid for "normal" usage
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        
        self.static_btn = QPushButton("🔤 Letters")
        self.static_btn.setCheckable(True)
        self.static_btn.clicked.connect(lambda: self._set_mode("static"))
        
        self.dynamic_btn = QPushButton("👋 Gestures")
        self.dynamic_btn.setCheckable(True)
        self.dynamic_btn.clicked.connect(lambda: self._set_mode("dynamic"))
        
        self.hybrid_btn = QPushButton("⚡ Both (Hybrid)")
        self.hybrid_btn.setCheckable(True)
        self.hybrid_btn.setChecked(True)
        self.hybrid_btn.clicked.connect(lambda: self._set_mode("hybrid"))
        
        layout.addWidget(self.static_btn)
        layout.addWidget(self.dynamic_btn)
        layout.addWidget(self.hybrid_btn)
    
    def _set_mode(self, mode):
        self._current_mode = mode
        self.static_btn.setChecked(mode == "static")
        self.dynamic_btn.setChecked(mode == "dynamic")
        self.hybrid_btn.setChecked(mode == "hybrid")
        self.mode_changed.emit(mode)
    
    def get_mode(self):
        return self._current_mode


class TranslationModeToggle(QFrame):
    """Toggle between instant and sentence translation modes."""
    
    mode_changed = Signal(str)  # 'instant' or 'sentence'
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self._current_mode = "instant"
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        
        label = QLabel("Translation Mode:")
        label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-weight: bold;")
        layout.addWidget(label)
        
        self.instant_btn = QPushButton("⚡ Instant (Letter)")
        self.instant_btn.setCheckable(True)
        self.instant_btn.setChecked(True)
        self.instant_btn.setToolTip("Show each letter immediately as detected")
        self.instant_btn.clicked.connect(lambda: self._set_mode("instant"))
        
        self.sentence_btn = QPushButton("📝 Sentence")
        self.sentence_btn.setCheckable(True)
        self.sentence_btn.setToolTip("Accumulate gestures and translate as sentence")
        self.sentence_btn.clicked.connect(lambda: self._set_mode("sentence"))
        
        layout.addWidget(self.instant_btn)
        layout.addWidget(self.sentence_btn)
        layout.addStretch()
    
    def _set_mode(self, mode):
        self._current_mode = mode
        self.instant_btn.setChecked(mode == "instant")
        self.sentence_btn.setChecked(mode == "sentence")
        self.mode_changed.emit(mode)
    
    def get_mode(self):
        return self._current_mode


class SourceTabs(QFrame):
    """Tabs for switching between camera and video sources."""
    
    source_changed = Signal(str)  # 'camera' or 'video'
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_source = "camera"
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        self.camera_btn = QPushButton("📷 Camera")
        self.camera_btn.setCheckable(True)
        self.camera_btn.setChecked(True)
        self.camera_btn.clicked.connect(lambda: self._set_source("camera"))
        self.camera_btn.setStyleSheet(self._tab_style(True))
        
        self.video_btn = QPushButton("🎬 Video File")
        self.video_btn.setCheckable(True)
        self.video_btn.clicked.connect(lambda: self._set_source("video"))
        self.video_btn.setStyleSheet(self._tab_style(False))
        
        layout.addWidget(self.camera_btn)
        layout.addWidget(self.video_btn)
        layout.addStretch()
    
    def _tab_style(self, active):
        if active:
            return f"""
                QPushButton {{
                    background-color: {COLORS['accent']};
                    color: {COLORS['text_primary']};
                    border: none;
                    border-radius: 8px 8px 0 0;
                    padding: 12px 24px;
                    font-weight: bold;
                    font-size: 14px;
                }}
            """
        return f"""
            QPushButton {{
                background-color: {COLORS['bg_panel']};
                color: {COLORS['text_secondary']};
                border: none;
                border-radius: 8px 8px 0 0;
                padding: 12px 24px;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['bg_card']};
            }}
        """
    
    def _set_source(self, source):
        self._current_source = source
        self.camera_btn.setChecked(source == "camera")
        self.video_btn.setChecked(source == "video")
        self.camera_btn.setStyleSheet(self._tab_style(source == "camera"))
        self.video_btn.setStyleSheet(self._tab_style(source == "video"))
        self.source_changed.emit(source)
    
    def get_source(self):
        return self._current_source


class LivePage(QWidget):
    """Live translation page with camera, video support, and sentence translation."""
    
    # Signals
    back_requested = Signal()
    translation_made = Signal(str, float, str)  # label, confidence, type
    
    def __init__(self, classifier=None, db_service=None, user_data=None, parent=None):
        super().__init__(parent)
        self.classifier = classifier or Classifier()
        self.db = db_service
        self.user = user_data or {}
        self._model_loaded = self.classifier.load()
        
        # Gesture accumulator for sentence mode
        self.accumulator = GestureAccumulator(
            time_window=TRANSLATION_TIME_WINDOW,
            confidence_threshold=CONFIDENCE_THRESHOLD
        )
        
        # Translation mode
        self._translation_mode = "instant"  # 'instant' or 'sentence'
        
        # Auto-translate timer
        self._auto_translate_timer = QTimer()
        self._auto_translate_timer.timeout.connect(self._check_auto_translate)
        self._auto_translate_timer.setInterval(500)  # Check every 500ms
        
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
        
        # === MODE TOGGLES ===
        toggles_row = QHBoxLayout()
        toggles_row.setSpacing(16)
        
        self.mode_toggle = ModeToggle()
        self.translation_mode_toggle = TranslationModeToggle()
        
        toggles_row.addWidget(self.mode_toggle)
        toggles_row.addWidget(self.translation_mode_toggle)
        toggles_row.addStretch()
        
        main_layout.addLayout(toggles_row)
        
        # === SOURCE TABS ===
        self.source_tabs = SourceTabs()
        main_layout.addWidget(self.source_tabs)
        
        # === MAIN CONTENT ===
        content_layout = QHBoxLayout()
        content_layout.setSpacing(24)
        
        # Left: Source (Camera or Video) - Stacked widget
        source_container = QFrame()
        source_container.setObjectName("cameraView")
        source_layout = QVBoxLayout(source_container)
        source_layout.setContentsMargins(4, 4, 4, 4)
        
        self.source_stack = QStackedWidget()
        
        # Camera widget
        self.camera_widget = CameraWidget()
        self.source_stack.addWidget(self.camera_widget)
        
        # Video player widget
        self.video_widget = VideoPlayerWidget()
        self.source_stack.addWidget(self.video_widget)
        
        source_layout.addWidget(self.source_stack)
        
        # Camera controls (shown when camera is active)
        self.camera_controls = QFrame()
        camera_ctrl_layout = QHBoxLayout(self.camera_controls)
        camera_ctrl_layout.setSpacing(12)
        
        self.start_btn = QPushButton("▶️ Start Camera")
        self.start_btn.setObjectName("primary")
        self.start_btn.clicked.connect(self._toggle_camera)
        
        camera_ctrl_layout.addStretch()
        camera_ctrl_layout.addWidget(self.start_btn)
        camera_ctrl_layout.addStretch()
        
        source_layout.addWidget(self.camera_controls)
        
        # Right: Prediction Panel
        right_panel = QVBoxLayout()
        right_panel.setSpacing(16)
        
        self.prediction_display = PredictionDisplay()
        self.sentence_builder = SentenceBuilder()
        
        # Stop/Translate button (for sentence mode)
        self.translate_btn = QPushButton("🛑 Stop & Translate")
        self.translate_btn.setObjectName("primary")
        self.translate_btn.clicked.connect(self._manual_translate)
        self.translate_btn.setMinimumHeight(50)
        self.translate_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['success']};
                color: {COLORS['text_primary']};
                border: none;
                border-radius: 12px;
                padding: 16px;
                font-weight: bold;
                font-size: 16px;
            }}
            QPushButton:hover {{
                background-color: #00b359;
            }}
        """)
        self.translate_btn.hide()  # Hidden in instant mode
        
        right_panel.addWidget(self.prediction_display, 2)
        right_panel.addWidget(self.translate_btn)
        right_panel.addWidget(self.sentence_builder, 1)
        
        content_layout.addWidget(source_container, 3)
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
        self.camera_widget.emotion_detected.connect(self._on_emotion_detected)
        self.camera_widget.heuristic_gesture_detected.connect(self._on_heuristic_gesture)
        
        # Video widget signals
        self.video_widget.features_ready.connect(self._on_features)
        self.video_widget.hand_detected.connect(self._on_hand_detected)
        self.video_widget.fps_updated.connect(
            lambda f: self.fps_pill.setText(f"FPS: {f:.0f}")
        )
        self.video_widget.dynamic_gesture_detected.connect(self._on_dynamic_gesture)
        self.video_widget.heuristic_gesture_detected.connect(self._on_heuristic_gesture)
        self.video_widget.video_finished.connect(self._on_video_finished)
        
        # Mode toggles
        self.mode_toggle.mode_changed.connect(self._on_mode_changed)
        self.translation_mode_toggle.mode_changed.connect(self._on_translation_mode_changed)
        
        # Source tabs
        self.source_tabs.source_changed.connect(self._on_source_changed)
        
        # Sentence builder
        self.sentence_builder.copy_requested.connect(self._copy_to_clipboard)
        self.sentence_builder.clear_requested.connect(self._on_sentence_cleared)
    
    def _on_source_changed(self, source):
        """Handle source tab change."""
        if source == "camera":
            self.source_stack.setCurrentIndex(0)
            self.camera_controls.show()
            # Stop video if playing
            if self.video_widget.is_active():
                self.video_widget.release()
        else:  # video
            self.source_stack.setCurrentIndex(1)
            self.camera_controls.hide()
            # Stop camera if running
            if self.camera_widget.is_active():
                self.camera_widget.stop()
                self.start_btn.setText("▶️ Start Camera")
    
    def _on_translation_mode_changed(self, mode):
        """Handle translation mode change."""
        self._translation_mode = mode
        
        if mode == "sentence":
            self.translate_btn.show()
            self.accumulator.start_accumulating()
            self._auto_translate_timer.start()
        else:
            self.translate_btn.hide()
            self.accumulator.stop_accumulating()
            self._auto_translate_timer.stop()
        
        # Clear state
        self.accumulator.clear()
        self.sentence_builder.set_buffer_preview("")
    
    def _check_auto_translate(self):
        """Check if auto-translate should trigger."""
        if self._translation_mode != "sentence":
            return
        
        if self.accumulator.check_auto_translate():
            self._manual_translate()
    
    def _manual_translate(self):
        """Manually trigger translation in sentence mode."""
        if self.accumulator.get_buffer_count() == 0:
            return
        
        # Get translated text
        translated = self.accumulator.translate_and_clear()
        
        if translated:
            self.sentence_builder.set_sentence(translated)
            self.sentence_builder.set_buffer_preview("")
            
            # Save to history
            self._save_translation(translated, 1.0, "sentence")
    
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
        if not self._model_loaded or features is None:
            return
        
        # Predict in static or hybrid mode
        mode = self.mode_toggle.get_mode()
        if mode not in ["static", "hybrid"]:
            return
        
        label, confidence = self.classifier.predict(features)
        
        if label and confidence > CONFIDENCE_THRESHOLD:
            self.prediction_display.update_prediction(label, confidence)
            
            if self._translation_mode == "instant":
                # Instant mode: add directly to sentence
                self.sentence_builder.add_letter(label)
                self._save_translation(label, confidence, "static")
            else:
                # Sentence mode: add to accumulator
                self.accumulator.add_gesture(label, confidence, "static")
                self.sentence_builder.set_buffer_preview(
                    self.accumulator.get_buffer_preview()
                )
    
    @Slot(str, float)
    def _on_dynamic_gesture(self, name, confidence):
        """Handle dynamic gesture detection."""
        mode = self.mode_toggle.get_mode()
        if mode not in ["dynamic", "hybrid"]:
            return
        
        display_name = f"✨{name}"
        self.prediction_display.update_prediction(display_name, confidence)
        
        if self._translation_mode == "instant":
            self.sentence_builder.add_letter(display_name)
            self._save_translation(name, confidence, "dynamic")
        else:
            self.accumulator.add_gesture(name, confidence, "dynamic")
            self.sentence_builder.set_buffer_preview(
                self.accumulator.get_buffer_preview()
            )
    
    @Slot(bool)
    def _on_hand_detected(self, detected):
        """Handle hand detection status."""
        self.prediction_display.set_hand_detected(detected)
    
    @Slot(str, float)
    def _on_emotion_detected(self, emotion_name, confidence):
        """Handle detected emotion from face detection."""
        # Update status in prediction display with emotion
        emoji_map = {
            'happy': '😊',
            'sad': '😢',
            'surprised': '😮',
            'angry': '😠',
            'neutral': '😐'
        }
        emoji = emoji_map.get(emotion_name, '😐')
        self.prediction_display.status_label.setText(f"{emoji} Feeling: {emotion_name.capitalize()}")
    
    @Slot(str, float)
    def _on_heuristic_gesture(self, gesture_name, confidence):
        """Handle heuristic gesture detection (more reliable than ML model)."""
        # Predict in static or hybrid mode
        mode = self.mode_toggle.get_mode()
        if mode not in ["static", "hybrid"]:
            return
        
        # Update display with heuristic prediction
        self.prediction_display.update_prediction(f"✨{gesture_name}", confidence)
        
        if self._translation_mode == "instant":
            self.sentence_builder.add_letter(gesture_name)
            self._save_translation(gesture_name, confidence, "heuristic")
        else:
            self.accumulator.add_gesture(gesture_name, confidence, "heuristic")
            self.sentence_builder.set_buffer_preview(
                self.accumulator.get_buffer_preview()
            )
    
    def _on_mode_changed(self, mode):
        """Handle mode change."""
        # Enable dynamic gestures for Dynamic AND Hybrid modes
        enable_dynamic = mode in ["dynamic", "hybrid"]
        self.camera_widget.set_dynamic_gestures_enabled(enable_dynamic)
        self.video_widget.set_dynamic_gestures_enabled(enable_dynamic)
        self.prediction_display.reset()
    
    def _on_video_finished(self):
        """Handle video playback finished."""
        # Auto-translate when video ends in sentence mode
        if self._translation_mode == "sentence":
            self._manual_translate()
    
    def _on_sentence_cleared(self):
        """Handle sentence builder clear."""
        self.accumulator.clear()
    
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
        if self.source_tabs.get_source() == "camera" and not self.camera_widget.is_active():
            self._toggle_camera()
    
    def stop_camera(self):
        """Stop camera externally."""
        if self.camera_widget.is_active():
            self._toggle_camera()
    
    def cleanup(self):
        """Cleanup resources."""
        self._auto_translate_timer.stop()
        self.camera_widget.release()
        self.video_widget.release()
