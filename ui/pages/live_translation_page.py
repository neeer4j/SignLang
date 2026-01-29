"""
Live Translation Page - Redesigned with Core Processing Pipeline

Real-time sign language detection with:
- Unified camera/video processing
- Sentence-level translation
- Text-to-sign reverse communication
- Temporal sequence aggregation
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFrame, QGridLayout, QScrollArea,
    QGraphicsDropShadowEffect, QSizePolicy, QTextEdit,
    QProgressBar, QTabWidget, QStackedWidget, QSplitter
)
from PySide6.QtCore import Qt, Signal, Slot, QTimer, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QFont, QColor

from ui.styles import COLORS, ICONS
from ui.camera_widget import CameraWidget
from ui.video_player_widget import VideoPlayerWidget
from ui.sign_visualizer import SignVisualizerWidget
from ml.classifier import Classifier

from core.pipeline import SignLanguagePipeline, PipelineMode, PipelineConfig
from core.gesture_sequence import GestureType, RecognizedGesture, TranslationResult
from core.text_to_sign import TextToSignTranslator

import config


class TranslationDisplay(QFrame):
    """Display for showing current translation with live preview."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)
        
        # Header
        header = QHBoxLayout()
        title = QLabel("📝 Translation")
        title.setObjectName("sectionTitle")
        header.addWidget(title)
        header.addStretch()
        
        # Status indicator
        self.status_label = QLabel("⏸️ Ready")
        self.status_label.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 12px;")
        header.addWidget(self.status_label)
        
        layout.addLayout(header)
        
        # Main translation text
        self.translation_text = QLabel("Start signing to translate...")
        self.translation_text.setStyleSheet(f"""
            font-size: 28px;
            font-weight: 600;
            color: {COLORS['text_primary']};
            padding: 20px;
            background-color: {COLORS['bg_input']};
            border-radius: 12px;
            min-height: 80px;
        """)
        self.translation_text.setWordWrap(True)
        self.translation_text.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        layout.addWidget(self.translation_text)
        
        # Preview (buffer) text
        self.preview_label = QLabel("")
        self.preview_label.setStyleSheet(f"""
            font-size: 14px;
            color: {COLORS['text_secondary']};
            padding: 8px 12px;
        """)
        self.preview_label.setWordWrap(True)
        layout.addWidget(self.preview_label)
        
        # Statistics row
        stats_row = QHBoxLayout()
        
        self.word_count_label = QLabel("Words: 0")
        self.word_count_label.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 12px;")
        stats_row.addWidget(self.word_count_label)
        
        self.gesture_count_label = QLabel("Gestures: 0")
        self.gesture_count_label.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 12px;")
        stats_row.addWidget(self.gesture_count_label)
        
        self.confidence_label = QLabel("Confidence: --")
        self.confidence_label.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 12px;")
        stats_row.addWidget(self.confidence_label)
        
        stats_row.addStretch()
        layout.addLayout(stats_row)
    
    def set_translation(self, text: str):
        """Set the main translation text."""
        if text:
            self.translation_text.setText(text)
        else:
            self.translation_text.setText("Start signing to translate...")
    
    def set_preview(self, preview: str):
        """Set the preview/buffer text."""
        if preview and preview != "(waiting...)":
            self.preview_label.setText(f"📦 Building: {preview}")
            self.preview_label.show()
        else:
            self.preview_label.hide()
    
    def set_statistics(self, words: int, gestures: int, confidence: float):
        """Update statistics display."""
        self.word_count_label.setText(f"Words: {words}")
        self.gesture_count_label.setText(f"Gestures: {gestures}")
        if confidence > 0:
            self.confidence_label.setText(f"Confidence: {confidence:.0%}")
        else:
            self.confidence_label.setText("Confidence: --")
    
    def set_status(self, status: str, is_active: bool = False):
        """Set status indicator."""
        if is_active:
            self.status_label.setText(f"🔴 {status}")
            self.status_label.setStyleSheet(f"color: {COLORS['danger']}; font-size: 12px;")
        else:
            self.status_label.setText(f"⏸️ {status}")
            self.status_label.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 12px;")
    
    def clear(self):
        """Clear the display."""
        self.set_translation("")
        self.set_preview("")
        self.set_statistics(0, 0, 0)
        self.set_status("Ready")


class CurrentGestureDisplay(QFrame):
    """Compact display for current gesture recognition."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setAlignment(Qt.AlignCenter)
        
        # Current gesture
        self.gesture_label = QLabel("?")
        self.gesture_label.setAlignment(Qt.AlignCenter)
        self.gesture_label.setStyleSheet(f"""
            font-size: 64px;
            font-weight: bold;
            color: {COLORS['primary']};
            background: transparent;
        """)
        
        # Confidence bar
        self.confidence_bar = QProgressBar()
        self.confidence_bar.setMaximum(100)
        self.confidence_bar.setValue(0)
        self.confidence_bar.setTextVisible(False)
        self.confidence_bar.setMaximumHeight(6)
        
        # Type label
        self.type_label = QLabel("Waiting...")
        self.type_label.setAlignment(Qt.AlignCenter)
        self.type_label.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 12px;")
        
        layout.addWidget(self.gesture_label)
        layout.addWidget(self.confidence_bar)
        layout.addWidget(self.type_label)
        
        # Glow effect
        glow = QGraphicsDropShadowEffect()
        glow.setBlurRadius(20)
        glow.setColor(QColor(139, 92, 246, 100))
        glow.setOffset(0, 0)
        self.gesture_label.setGraphicsEffect(glow)
    
    def update_gesture(self, label: str, confidence: float, gesture_type: str = ""):
        """Update displayed gesture."""
        self.gesture_label.setText(label)
        self.confidence_bar.setValue(int(confidence * 100))
        
        if gesture_type:
            self.type_label.setText(gesture_type.capitalize())
        
        # Color based on confidence
        if confidence >= 0.8:
            color = COLORS['success']
        elif confidence >= 0.6:
            color = COLORS['primary']
        else:
            color = COLORS['warning']
        
        self.gesture_label.setStyleSheet(f"""
            font-size: 64px;
            font-weight: bold;
            color: {color};
            background: transparent;
        """)
    
    def set_no_hand(self):
        """Set no hand detected state."""
        self.gesture_label.setText("👋")
        self.confidence_bar.setValue(0)
        self.type_label.setText("Show your hand")
        self.gesture_label.setStyleSheet(f"""
            font-size: 64px;
            font-weight: bold;
            color: {COLORS['text_muted']};
            background: transparent;
        """)
    
    def clear(self):
        """Clear display."""
        self.set_no_hand()


class ModeSelector(QFrame):
    """Mode selection for translation behavior."""
    
    mode_changed = Signal(str)  # 'instant', 'sentence', or 'word'
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_mode = "sentence"
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        
        label = QLabel("Mode:")
        label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-weight: bold;")
        layout.addWidget(label)
        
        self.instant_btn = QPushButton("⚡ Instant")
        self.instant_btn.setCheckable(True)
        self.instant_btn.setToolTip("Output each letter/gesture immediately")
        self.instant_btn.clicked.connect(lambda: self._set_mode("instant"))
        
        self.word_btn = QPushButton("📖 Word")
        self.word_btn.setCheckable(True)
        self.word_btn.setToolTip("Accumulate letters into words")
        self.word_btn.clicked.connect(lambda: self._set_mode("word"))
        
        self.sentence_btn = QPushButton("📝 Sentence")
        self.sentence_btn.setCheckable(True)
        self.sentence_btn.setChecked(True)
        self.sentence_btn.setToolTip("Build complete sentences before output")
        self.sentence_btn.clicked.connect(lambda: self._set_mode("sentence"))
        
        layout.addWidget(self.instant_btn)
        layout.addWidget(self.word_btn)
        layout.addWidget(self.sentence_btn)
        layout.addStretch()
        
        self.setStyleSheet(f"background-color: {COLORS['bg_panel']}; border-radius: 8px;")
    
    def _set_mode(self, mode: str):
        self._current_mode = mode
        self.instant_btn.setChecked(mode == "instant")
        self.word_btn.setChecked(mode == "word")
        self.sentence_btn.setChecked(mode == "sentence")
        self.mode_changed.emit(mode)
    
    def get_mode(self) -> str:
        return self._current_mode


class SourceSelector(QFrame):
    """Source selection tabs (camera/video)."""
    
    source_changed = Signal(str)  # 'camera' or 'video'
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._current = "camera"
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        self.camera_btn = QPushButton("📷 Camera")
        self.camera_btn.setCheckable(True)
        self.camera_btn.setChecked(True)
        self.camera_btn.clicked.connect(lambda: self._set_source("camera"))
        self._apply_tab_style(self.camera_btn, True)
        
        self.video_btn = QPushButton("🎬 Video File")
        self.video_btn.setCheckable(True)
        self.video_btn.clicked.connect(lambda: self._set_source("video"))
        self._apply_tab_style(self.video_btn, False)
        
        self.text_btn = QPushButton("📤 Text to Sign")
        self.text_btn.setCheckable(True)
        self.text_btn.clicked.connect(lambda: self._set_source("text"))
        self._apply_tab_style(self.text_btn, False)
        
        layout.addWidget(self.camera_btn)
        layout.addWidget(self.video_btn)
        layout.addWidget(self.text_btn)
        layout.addStretch()
    
    def _apply_tab_style(self, btn: QPushButton, active: bool):
        if active:
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {COLORS['primary']};
                    color: {COLORS['text_primary']};
                    border: none;
                    border-radius: 8px 8px 0 0;
                    padding: 12px 20px;
                    font-weight: bold;
                }}
            """)
        else:
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {COLORS['bg_panel']};
                    color: {COLORS['text_secondary']};
                    border: none;
                    border-radius: 8px 8px 0 0;
                    padding: 12px 20px;
                }}
                QPushButton:hover {{
                    background-color: {COLORS['bg_card']};
                }}
            """)
    
    def _set_source(self, source: str):
        self._current = source
        self.camera_btn.setChecked(source == "camera")
        self.video_btn.setChecked(source == "video")
        self.text_btn.setChecked(source == "text")
        self._apply_tab_style(self.camera_btn, source == "camera")
        self._apply_tab_style(self.video_btn, source == "video")
        self._apply_tab_style(self.text_btn, source == "text")
        self.source_changed.emit(source)
    
    def get_source(self) -> str:
        return self._current


class LiveTranslationPage(QWidget):
    """Redesigned live translation page with new processing pipeline.
    
    Features:
    - Sentence-level translation with temporal aggregation
    - Camera and video input support
    - Text-to-sign reverse communication
    - Real-time preview and statistics
    """
    
    back_requested = Signal()
    translation_made = Signal(str, float, str)  # text, confidence, type
    
    def __init__(self, classifier=None, db_service=None, user_data=None, parent=None):
        super().__init__(parent)
        self.classifier = classifier or Classifier()
        self.db = db_service
        self.user = user_data or {}
        
        # Initialize pipeline
        self.pipeline = SignLanguagePipeline(PipelineConfig(
            aggregation_window=config.TEMPORAL_WINDOW_SIZE,
            stability_threshold=config.STABILITY_THRESHOLD,
            min_confidence=config.CONFIDENCE_THRESHOLD,
            word_timeout=config.WORD_TIMEOUT,
            sentence_timeout=config.TRANSLATION_TIME_WINDOW
        ))
        
        # Load classifier
        self._model_loaded = self.classifier.load()
        
        # State
        self._is_translating = False
        self._current_source = "camera"
        
        # Auto-check timer
        self._check_timer = QTimer()
        self._check_timer.timeout.connect(self._check_pipeline_status)
        self._check_timer.setInterval(500)
        
        self._setup_ui()
        self._connect_signals()
        self._setup_pipeline_callbacks()
    
    def _setup_ui(self):
        """Setup the UI layout."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 20, 24, 20)
        main_layout.setSpacing(16)
        
        # === HEADER ===
        header = QHBoxLayout()
        
        back_btn = QPushButton("← Back")
        back_btn.setObjectName("ghost")
        back_btn.clicked.connect(self.back_requested.emit)
        
        title = QLabel("🔴 Live Translation")
        title.setObjectName("pageTitle")
        
        self.fps_label = QLabel("FPS: --")
        self.fps_label.setObjectName("statusPill")
        
        self.model_label = QLabel("✓ Model Ready" if self._model_loaded else "✗ No Model")
        self.model_label.setObjectName("statusPillSuccess" if self._model_loaded else "statusPillDanger")
        
        header.addWidget(back_btn)
        header.addWidget(title)
        header.addStretch()
        header.addWidget(self.fps_label)
        header.addWidget(self.model_label)
        
        main_layout.addLayout(header)
        
        # === MODE SELECTOR ===
        self.mode_selector = ModeSelector()
        main_layout.addWidget(self.mode_selector)
        
        # === SOURCE TABS ===
        self.source_selector = SourceSelector()
        main_layout.addWidget(self.source_selector)
        
        # === MAIN CONTENT ===
        content_splitter = QSplitter(Qt.Horizontal)
        
        # Left: Source widgets stack
        source_container = QFrame()
        source_container.setObjectName("sourceContainer")
        source_layout = QVBoxLayout(source_container)
        source_layout.setContentsMargins(4, 4, 4, 4)
        
        self.source_stack = QStackedWidget()
        
        # Camera widget
        self.camera_widget = CameraWidget()
        self.source_stack.addWidget(self.camera_widget)
        
        # Video widget
        self.video_widget = VideoPlayerWidget()
        self.source_stack.addWidget(self.video_widget)
        
        # Text-to-sign widget
        self.sign_visualizer = SignVisualizerWidget()
        self.source_stack.addWidget(self.sign_visualizer)
        
        source_layout.addWidget(self.source_stack)
        
        # Camera controls
        self.camera_controls = QFrame()
        cam_ctrl_layout = QHBoxLayout(self.camera_controls)
        
        self.start_btn = QPushButton("▶️ Start Translation")
        self.start_btn.setObjectName("primary")
        self.start_btn.clicked.connect(self._toggle_translation)
        
        self.stop_translate_btn = QPushButton("🛑 Stop & Translate")
        self.stop_translate_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['success']};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #0ea566;
            }}
        """)
        self.stop_translate_btn.clicked.connect(self._stop_and_translate)
        self.stop_translate_btn.hide()
        
        cam_ctrl_layout.addStretch()
        cam_ctrl_layout.addWidget(self.start_btn)
        cam_ctrl_layout.addWidget(self.stop_translate_btn)
        cam_ctrl_layout.addStretch()
        
        source_layout.addWidget(self.camera_controls)
        
        content_splitter.addWidget(source_container)
        
        # Right: Results panel
        right_panel = QFrame()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setSpacing(16)
        
        # Current gesture display
        self.gesture_display = CurrentGestureDisplay()
        self.gesture_display.setMaximumHeight(200)
        right_layout.addWidget(self.gesture_display)
        
        # Translation display
        self.translation_display = TranslationDisplay()
        right_layout.addWidget(self.translation_display, 1)
        
        # Action buttons
        action_row = QHBoxLayout()
        
        self.copy_btn = QPushButton("📋 Copy")
        self.copy_btn.setObjectName("ghost")
        self.copy_btn.clicked.connect(self._copy_translation)
        
        self.clear_btn = QPushButton("🗑️ Clear")
        self.clear_btn.setObjectName("ghost")
        self.clear_btn.clicked.connect(self._clear_translation)
        
        self.space_btn = QPushButton("␣ Space")
        self.space_btn.setObjectName("ghost")
        self.space_btn.clicked.connect(self._insert_space)
        
        self.delete_btn = QPushButton("⌫ Delete")
        self.delete_btn.setObjectName("ghost")
        self.delete_btn.clicked.connect(self._delete_last)
        
        action_row.addWidget(self.copy_btn)
        action_row.addWidget(self.clear_btn)
        action_row.addStretch()
        action_row.addWidget(self.space_btn)
        action_row.addWidget(self.delete_btn)
        
        right_layout.addLayout(action_row)
        
        content_splitter.addWidget(right_panel)
        content_splitter.setSizes([600, 400])
        
        main_layout.addWidget(content_splitter, 1)
    
    def _connect_signals(self):
        """Connect UI signals."""
        # Source selector
        self.source_selector.source_changed.connect(self._on_source_changed)
        
        # Mode selector
        self.mode_selector.mode_changed.connect(self._on_mode_changed)
        
        # Camera widget
        self.camera_widget.features_ready.connect(self._on_features)
        self.camera_widget.hand_detected.connect(self._on_hand_detected)
        self.camera_widget.fps_updated.connect(
            lambda f: self.fps_label.setText(f"FPS: {f:.0f}")
        )
        self.camera_widget.heuristic_gesture_detected.connect(self._on_heuristic_gesture)
        self.camera_widget.dynamic_gesture_detected.connect(self._on_dynamic_gesture)
        
        # Video widget
        self.video_widget.features_ready.connect(self._on_features)
        self.video_widget.hand_detected.connect(self._on_hand_detected)
        self.video_widget.fps_updated.connect(
            lambda f: self.fps_label.setText(f"FPS: {f:.0f}")
        )
        self.video_widget.heuristic_gesture_detected.connect(self._on_heuristic_gesture)
        self.video_widget.dynamic_gesture_detected.connect(self._on_dynamic_gesture)
        self.video_widget.video_finished.connect(self._on_video_finished)
    
    def _setup_pipeline_callbacks(self):
        """Setup callbacks from the processing pipeline."""
        self.pipeline.set_on_gesture_recognized(self._on_gesture_recognized)
        self.pipeline.set_on_text_updated(self._on_text_updated)
        self.pipeline.set_on_translation_complete(self._on_translation_complete)
    
    # === Source Handling ===
    
    def _on_source_changed(self, source: str):
        """Handle source tab change."""
        self._current_source = source
        
        # Stop any ongoing translation
        if self._is_translating:
            self._stop_translation()
        
        # Switch stack
        if source == "camera":
            self.source_stack.setCurrentIndex(0)
            self.camera_controls.show()
        elif source == "video":
            self.source_stack.setCurrentIndex(1)
            self.camera_controls.hide()
        else:  # text
            self.source_stack.setCurrentIndex(2)
            self.camera_controls.hide()
        
        # Stop other sources
        if source != "camera" and self.camera_widget.is_running:
            self.camera_widget.stop()
        if source != "video" and self.video_widget.is_active():
            self.video_widget.release()
    
    def _on_mode_changed(self, mode: str):
        """Handle translation mode change."""
        # Update button visibility
        if mode == "sentence":
            self.stop_translate_btn.show() if self._is_translating else None
        else:
            self.stop_translate_btn.hide()
        
        # Clear and restart if translating
        if self._is_translating:
            self.pipeline.clear()
            self.translation_display.clear()
            self.gesture_display.clear()
    
    # === Translation Control ===
    
    def _toggle_translation(self):
        """Start or stop translation."""
        if self._is_translating:
            self._stop_translation()
        else:
            self._start_translation()
    
    def _start_translation(self):
        """Start translation."""
        self._is_translating = True
        
        # Start appropriate source
        if self._current_source == "camera":
            if not self.camera_widget.start():
                self._is_translating = False
                return
        
        # Start pipeline
        mode = PipelineMode.LIVE_ACCUMULATE if self.mode_selector.get_mode() == "sentence" else PipelineMode.LIVE_CONTINUOUS
        self.pipeline.start(mode)
        
        # Update UI
        self.start_btn.setText("⏹️ Stop")
        self.start_btn.setObjectName("danger")
        self.start_btn.style().unpolish(self.start_btn)
        self.start_btn.style().polish(self.start_btn)
        
        if self.mode_selector.get_mode() == "sentence":
            self.stop_translate_btn.show()
        
        self.translation_display.set_status("Translating...", True)
        self._check_timer.start()
    
    def _stop_translation(self):
        """Stop translation without finalizing."""
        self._is_translating = False
        
        # Stop sources
        self.camera_widget.stop()
        
        # Stop pipeline
        self.pipeline.stop()
        
        # Update UI
        self.start_btn.setText("▶️ Start Translation")
        self.start_btn.setObjectName("primary")
        self.start_btn.style().unpolish(self.start_btn)
        self.start_btn.style().polish(self.start_btn)
        
        self.stop_translate_btn.hide()
        self.translation_display.set_status("Stopped")
        self._check_timer.stop()
    
    def _stop_and_translate(self):
        """Stop and finalize translation."""
        if not self._is_translating:
            return
        
        # Get final translation
        result = self.pipeline.stop_and_translate()
        
        self._is_translating = False
        
        # Stop camera
        self.camera_widget.stop()
        
        # Update UI with result
        if result.text:
            self.translation_display.set_translation(result.text)
            self.translation_display.set_preview("")
            self.translation_display.set_statistics(
                result.word_count,
                result.gesture_count,
                result.confidence
            )
            
            # Save to history
            self._save_translation(result)
        
        # Update buttons
        self.start_btn.setText("▶️ Start Translation")
        self.start_btn.setObjectName("primary")
        self.start_btn.style().unpolish(self.start_btn)
        self.start_btn.style().polish(self.start_btn)
        
        self.stop_translate_btn.hide()
        self.translation_display.set_status("Complete")
        self._check_timer.stop()
    
    # === Gesture Processing ===
    
    @Slot(object)
    def _on_features(self, features):
        """Handle extracted features from camera/video."""
        if not self._is_translating or not self._model_loaded or features is None:
            return
        
        # Get ML prediction
        label, confidence = self.classifier.predict(features)
        
        if label and confidence > config.CONFIDENCE_THRESHOLD:
            # Process through pipeline
            self.pipeline.process_frame(
                landmarks=None,  # Features already extracted
                features=features,
                predicted_label=label,
                confidence=confidence,
                gesture_type=GestureType.STATIC
            )
    
    @Slot(str, float)
    def _on_heuristic_gesture(self, gesture: str, confidence: float):
        """Handle heuristic gesture detection."""
        if not self._is_translating:
            return
        
        # Heuristic gestures are pre-smoothed, process directly
        self.pipeline.process_gesture(
            label=gesture,
            confidence=confidence,
            gesture_type=GestureType.STATIC
        )
        
        # Update gesture display
        self.gesture_display.update_gesture(gesture, confidence, "heuristic")
    
    @Slot(str, float)
    def _on_dynamic_gesture(self, gesture: str, confidence: float):
        """Handle dynamic gesture detection."""
        if not self._is_translating:
            return
        
        self.pipeline.process_gesture(
            label=gesture,
            confidence=confidence,
            gesture_type=GestureType.DYNAMIC
        )
        
        self.gesture_display.update_gesture(f"✨{gesture}", confidence, "dynamic")
    
    @Slot(bool)
    def _on_hand_detected(self, detected: bool):
        """Handle hand detection status."""
        if not detected:
            self.gesture_display.set_no_hand()
    
    def _on_video_finished(self):
        """Handle video playback finished."""
        if self._is_translating:
            self._stop_and_translate()
    
    # === Pipeline Callbacks ===
    
    def _on_gesture_recognized(self, gesture: RecognizedGesture):
        """Handle gesture recognition from pipeline."""
        self.gesture_display.update_gesture(
            gesture.label,
            gesture.confidence,
            gesture.gesture_type.value
        )
    
    def _on_text_updated(self, text: str, preview: str):
        """Handle text update from pipeline."""
        self.translation_display.set_translation(text)
        self.translation_display.set_preview(preview)
        
        # Update statistics
        stats = self.pipeline.get_statistics()
        self.translation_display.set_statistics(
            stats.get('word_count', 0),
            stats.get('gesture_count', 0),
            0.0  # Will be set on completion
        )
    
    def _on_translation_complete(self, result: TranslationResult):
        """Handle translation completion."""
        self.translation_display.set_translation(result.text)
        self.translation_display.set_preview("")
        self.translation_display.set_statistics(
            result.word_count,
            result.gesture_count,
            result.confidence
        )
        
        self._save_translation(result)
    
    def _check_pipeline_status(self):
        """Periodic check for pipeline status."""
        if not self._is_translating:
            return
        
        # Check for auto-translate timeout in sentence mode
        if self.mode_selector.get_mode() == "sentence":
            # This is handled internally by pipeline
            pass
    
    # === Actions ===
    
    def _copy_translation(self):
        """Copy translation to clipboard."""
        from PySide6.QtWidgets import QApplication
        text = self.translation_display.translation_text.text()
        if text and text != "Start signing to translate...":
            QApplication.clipboard().setText(text)
    
    def _clear_translation(self):
        """Clear current translation."""
        self.pipeline.clear()
        self.translation_display.clear()
        self.gesture_display.clear()
    
    def _insert_space(self):
        """Insert a word boundary."""
        if self._is_translating:
            self.pipeline.insert_space()
    
    def _delete_last(self):
        """Delete last character/word."""
        if self._is_translating:
            self.pipeline.delete_last(delete_word=False)
    
    def _save_translation(self, result: TranslationResult):
        """Save translation to history."""
        if not self.db or self.user.get("guest"):
            return
        
        self.translation_made.emit(
            result.text,
            result.confidence,
            "sentence"
        )
    
    # === Lifecycle ===
    
    def cleanup(self):
        """Cleanup resources."""
        self._check_timer.stop()
        if self._is_translating:
            self._stop_translation()
        self.camera_widget.stop()
        self.video_widget.release()


# Alias for compatibility with existing code
LivePage = LiveTranslationPage
