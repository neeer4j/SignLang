"""
Video Player Widget - Video upload and playback controls for sign language detection

Displays pre-recorded video with player controls (play/pause, seek, speed)
and integrates with the gesture processing pipeline.
Uses VIDEO mode for MediaPipe hand tracking for better temporal consistency.
"""
from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QSlider, QComboBox, QFileDialog, QWidget, QProgressBar
)
from PySide6.QtCore import Qt, QTimer, Signal, Slot
from PySide6.QtGui import QImage, QPixmap
import cv2
import os

from detector.video_source import VideoFileSource
from detector.hand_tracker import HandTracker
from detector.features import FeatureExtractor
from detector.dynamic_gestures import DynamicGestureTracker
from ml.heuristic_classifier import HeuristicClassifier
from ui.styles import COLORS
from config import VIDEO_DETECTION_CONFIDENCE


class VideoPlayerWidget(QFrame):
    """Widget for video file playback with hand tracking overlay."""
    
    # Signals
    features_ready = Signal(object)           # Emitted when features are extracted
    hand_detected = Signal(bool)              # Emitted when hand detection status changes
    fps_updated = Signal(float)               # Emitted with current FPS
    dynamic_gesture_detected = Signal(str, float)  # (gesture_name, confidence)
    heuristic_gesture_detected = Signal(str, float)  # Reliable gesture from geometry
    video_loaded = Signal(str)                # Emitted when video is loaded (filename)
    video_finished = Signal()                 # Emitted when video reaches end
    progress_updated = Signal(float)          # Emitted with progress (0-1)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("videoPlayerFrame")
        
        # Components - Use VIDEO mode for better tracking in pre-recorded videos
        self.video_source = VideoFileSource()
        self.hand_tracker = HandTracker(
            use_video_mode=True, 
            detection_confidence=VIDEO_DETECTION_CONFIDENCE
        )
        self.feature_extractor = FeatureExtractor()
        self.dynamic_tracker = DynamicGestureTracker()
        self.heuristic_classifier = HeuristicClassifier()
        
        # State
        self._is_loaded = False
        self._is_playing = False
        self._last_hand_detected = False
        self.dynamic_gestures_enabled = True
        self._fast_mode = False
        
        # Setup UI
        self._setup_ui()
        
        # Frame timer
        self.timer = QTimer()
        self.timer.timeout.connect(self._update_frame)
    
    def _setup_ui(self):
        """Setup the widget UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        
        # Video display
        self.video_label = QLabel()
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setMinimumSize(640, 480)
        self.video_label.setStyleSheet(f"""
            background-color: #000000;
            border-radius: 12px;
            color: {COLORS['text_secondary']};
            font-size: 16px;
        """)
        self.video_label.setText("📂 No video loaded\nClick 'Upload Video' to select a file")
        layout.addWidget(self.video_label)
        
        # Controls container
        controls_container = QFrame()
        controls_container.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_card']};
                border-radius: 12px;
                padding: 12px;
            }}
        """)
        controls_layout = QVBoxLayout(controls_container)
        controls_layout.setSpacing(12)
        
        # Progress bar
        progress_row = QHBoxLayout()
        
        self.time_label = QLabel("0:00")
        self.time_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 12px;")
        progress_row.addWidget(self.time_label)
        
        self.progress_slider = QSlider(Qt.Horizontal)
        self.progress_slider.setRange(0, 1000)
        self.progress_slider.setValue(0)
        self.progress_slider.setEnabled(False)
        self.progress_slider.sliderPressed.connect(self._on_slider_pressed)
        self.progress_slider.sliderReleased.connect(self._on_slider_released)
        self.progress_slider.setStyleSheet(f"""
            QSlider::groove:horizontal {{
                background: {COLORS['bg_panel']};
                height: 6px;
                border-radius: 3px;
            }}
            QSlider::handle:horizontal {{
                background: {COLORS['accent']};
                width: 16px;
                height: 16px;
                margin: -5px 0;
                border-radius: 8px;
            }}
            QSlider::sub-page:horizontal {{
                background: {COLORS['accent']};
                border-radius: 3px;
            }}
        """)
        progress_row.addWidget(self.progress_slider, 1)
        
        self.duration_label = QLabel("0:00")
        self.duration_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 12px;")
        progress_row.addWidget(self.duration_label)
        
        controls_layout.addLayout(progress_row)
        
        # Playback controls row
        playback_row = QHBoxLayout()
        playback_row.setSpacing(12)
        
        # Upload button
        self.upload_btn = QPushButton("📂 Upload Video")
        self.upload_btn.clicked.connect(self._open_file_dialog)
        self.upload_btn.setStyleSheet(self._button_style())
        playback_row.addWidget(self.upload_btn)
        
        playback_row.addStretch()
        
        # Play/Pause button
        self.play_btn = QPushButton("▶ Play")
        self.play_btn.clicked.connect(self._toggle_playback)
        self.play_btn.setEnabled(False)
        self.play_btn.setStyleSheet(self._button_style(primary=True))
        playback_row.addWidget(self.play_btn)
        
        # Stop button
        self.stop_btn = QPushButton("⏹ Stop")
        self.stop_btn.clicked.connect(self._stop_video)
        self.stop_btn.setEnabled(False)
        self.stop_btn.setStyleSheet(self._button_style())
        playback_row.addWidget(self.stop_btn)
        
        playback_row.addStretch()
        
        # Speed control
        speed_label = QLabel("Speed:")
        speed_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        playback_row.addWidget(speed_label)
        
        self.speed_combo = QComboBox()
        self.speed_combo.addItems(["0.25x", "0.5x", "1x", "1.5x", "2x"])
        self.speed_combo.setCurrentText("1x")
        self.speed_combo.currentTextChanged.connect(self._on_speed_changed)
        self.speed_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {COLORS['bg_panel']};
                color: {COLORS['text_primary']};
                border: 1px solid {COLORS['bg_card']};
                border-radius: 6px;
                padding: 6px 12px;
                min-width: 70px;
            }}
            QComboBox::drop-down {{
                border: none;
            }}
            QComboBox QAbstractItemView {{
                background-color: {COLORS['bg_panel']};
                color: {COLORS['text_primary']};
                selection-background-color: {COLORS['accent']};
            }}
        """)
        playback_row.addWidget(self.speed_combo)
        
        # Fast mode toggle
        self.fast_mode_btn = QPushButton("⚡ Fast")
        self.fast_mode_btn.setCheckable(True)
        self.fast_mode_btn.setToolTip("Process video at maximum speed")
        self.fast_mode_btn.clicked.connect(self._toggle_fast_mode)
        self.fast_mode_btn.setStyleSheet(self._button_style())
        playback_row.addWidget(self.fast_mode_btn)
        
        controls_layout.addLayout(playback_row)
        
        layout.addWidget(controls_container)
    
    def _button_style(self, primary=False) -> str:
        """Get button stylesheet."""
        if primary:
            return f"""
                QPushButton {{
                    background-color: {COLORS['accent']};
                    color: {COLORS['text_primary']};
                    border: none;
                    border-radius: 8px;
                    padding: 10px 20px;
                    font-weight: bold;
                    font-size: 14px;
                }}
                QPushButton:hover {{
                    background-color: {COLORS['accent_hover']};
                }}
                QPushButton:disabled {{
                    background-color: {COLORS['bg_panel']};
                    color: {COLORS['text_secondary']};
                }}
            """
        return f"""
            QPushButton {{
                background-color: {COLORS['bg_panel']};
                color: {COLORS['text_primary']};
                border: none;
                border-radius: 8px;
                padding: 10px 16px;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['bg_card']};
            }}
            QPushButton:checked {{
                background-color: {COLORS['accent']};
            }}
            QPushButton:disabled {{
                color: {COLORS['text_secondary']};
            }}
        """
    
    def _open_file_dialog(self):
        """Open file dialog to select video."""
        file_filter = "Video Files (*.mp4 *.avi *.mov *.mkv *.webm *.flv *.wmv)"
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Sign Language Video",
            "",
            file_filter
        )
        
        if file_path:
            self.load_video(file_path)
    
    def load_video(self, file_path: str) -> bool:
        """Load a video file.
        
        Args:
            file_path: Path to video file
            
        Returns:
            True if loaded successfully
        """
        # Stop current video if playing
        self._stop_video()
        
        # Load new video
        if not self.video_source.load(file_path):
            self.video_label.setText("❌ Error loading video\nPlease try a different file")
            return False
        
        self._is_loaded = True
        self._is_playing = False
        
        # Update UI
        filename = os.path.basename(file_path)
        self.video_label.setText(f"✅ Loaded: {filename}\nClick Play to start")
        
        # Update duration label
        duration = self.video_source.get_duration()
        self.duration_label.setText(self._format_time(duration))
        
        # Enable controls
        self.play_btn.setEnabled(True)
        self.stop_btn.setEnabled(True)
        self.progress_slider.setEnabled(True)
        
        # Reset state for new video
        self.dynamic_tracker.clear()
        self.heuristic_classifier.clear()
        self.hand_tracker.reset_timestamp()
        
        # Emit signal
        self.video_loaded.emit(filename)
        
        # Show first frame
        self._show_current_frame()
        
        return True
    
    def _show_current_frame(self):
        """Display current frame without advancing."""
        if not self._is_loaded:
            return
        
        success, frame_bgr, frame_rgb = self.video_source.read()
        if success:
            self._process_and_display(frame_bgr, frame_rgb)
        
        # Seek back to show frame without advancing
        progress = self.video_source.get_progress()
        if progress > 0:
            self.video_source.seek(max(0, progress - 0.001))
    
    def _toggle_playback(self):
        """Toggle play/pause."""
        if not self._is_loaded:
            return
        
        if self._is_playing:
            self._pause_video()
        else:
            self._play_video()
    
    def _play_video(self):
        """Start video playback."""
        if not self._is_loaded:
            return
        
        self._is_playing = True
        self.video_source.resume()
        self.play_btn.setText("⏸ Pause")
        
        # Start frame timer (high frequency for smooth playback)
        timer_interval = 10 if self._fast_mode else 33  # ~100 FPS fast, ~30 FPS normal
        self.timer.start(timer_interval)
    
    def _pause_video(self):
        """Pause video playback."""
        self._is_playing = False
        self.video_source.pause()
        self.play_btn.setText("▶ Play")
        self.timer.stop()
    
    def _stop_video(self):
        """Stop and reset video."""
        self.timer.stop()
        self.video_source.stop()
        self._is_playing = False
        self._is_loaded = False
        
        # Reset UI
        self.play_btn.setText("▶ Play")
        self.play_btn.setEnabled(False)
        self.stop_btn.setEnabled(False)
        self.progress_slider.setEnabled(False)
        self.progress_slider.setValue(0)
        self.time_label.setText("0:00")
        self.video_label.setText("📂 No video loaded\nClick 'Upload Video' to select a file")
        self.video_label.setPixmap(QPixmap())
        
        # Reset trackers
        self.dynamic_tracker.clear()
    
    def _update_frame(self):
        """Process and display next frame."""
        if not self._is_loaded or not self._is_playing:
            return
        
        success, frame_bgr, frame_rgb = self.video_source.read()
        
        if not success:
            # Check if video finished
            if self.video_source.is_finished():
                self._pause_video()
                self.video_finished.emit()
            return
        
        self._process_and_display(frame_bgr, frame_rgb)
        
        # Update progress
        progress = self.video_source.get_progress()
        self.progress_slider.blockSignals(True)
        self.progress_slider.setValue(int(progress * 1000))
        self.progress_slider.blockSignals(False)
        
        current_time = self.video_source.get_current_time()
        self.time_label.setText(self._format_time(current_time))
        
        self.progress_updated.emit(progress)
    
    def _process_and_display(self, frame_bgr, frame_rgb):
        """Process frame for hand detection and display."""
        # Process with MediaPipe (uses VIDEO mode for temporal consistency)
        self.hand_tracker.process(frame_rgb)
        
        # Check hand detection
        hand_detected = self.hand_tracker.has_hand()
        if hand_detected != self._last_hand_detected:
            self.hand_detected.emit(hand_detected)
            self._last_hand_detected = hand_detected
        
        # Get landmarks
        landmarks = None
        if hand_detected:
            landmarks = self.hand_tracker.get_landmarks()
            
            # Extract features for ML-based gesture recognition
            features = self.feature_extractor.extract(landmarks)
            self.features_ready.emit(features)
            
            # Heuristic gesture detection (more reliable than ML on varied video content)
            heuristic_label, heuristic_conf = self.heuristic_classifier.predict(landmarks)
            if heuristic_label and heuristic_conf > 0.5:
                self.heuristic_gesture_detected.emit(heuristic_label, heuristic_conf)
        
        # Dynamic gesture tracking
        if self.dynamic_gestures_enabled:
            gesture_name, confidence = self.dynamic_tracker.update(landmarks)
            if gesture_name is not None and confidence > 0.6:
                self.dynamic_gesture_detected.emit(gesture_name, confidence)
        
        # Draw landmarks
        frame_bgr = self.hand_tracker.draw_landmarks(frame_bgr)
        
        # Display
        self._display_frame(frame_bgr)
        
        # Emit FPS
        self.fps_updated.emit(self.video_source.get_fps())
    
    def _display_frame(self, frame_bgr):
        """Convert and display frame."""
        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        h, w, ch = frame_rgb.shape
        bytes_per_line = ch * w
        
        q_image = QImage(frame_rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(q_image)
        
        scaled_pixmap = pixmap.scaled(
            self.video_label.size(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
        self.video_label.setPixmap(scaled_pixmap)
    
    def _on_slider_pressed(self):
        """Handle slider press (pause during seek)."""
        if self._is_playing:
            self.timer.stop()
    
    def _on_slider_released(self):
        """Handle slider release (seek to position)."""
        if not self._is_loaded:
            return
        
        position = self.progress_slider.value() / 1000.0
        self.video_source.seek(position)
        
        # Update time display
        current_time = position * self.video_source.get_duration()
        self.time_label.setText(self._format_time(current_time))
        
        # Show frame at new position
        self._show_current_frame()
        
        # Resume if was playing
        if self._is_playing:
            self.timer.start()
    
    def _on_speed_changed(self, speed_text: str):
        """Handle speed change."""
        speed = float(speed_text.replace("x", ""))
        self.video_source.set_playback_speed(speed)
    
    def _toggle_fast_mode(self):
        """Toggle fast processing mode."""
        self._fast_mode = self.fast_mode_btn.isChecked()
        self.video_source.set_fast_mode(self._fast_mode)
        
        if self._is_playing:
            timer_interval = 10 if self._fast_mode else 33
            self.timer.setInterval(timer_interval)
    
    def _format_time(self, seconds: float) -> str:
        """Format seconds as M:SS."""
        minutes = int(seconds) // 60
        secs = int(seconds) % 60
        return f"{minutes}:{secs:02d}"
    
    def set_dynamic_gestures_enabled(self, enabled: bool):
        """Enable or disable dynamic gesture recognition."""
        self.dynamic_gestures_enabled = enabled
        if not enabled:
            self.dynamic_tracker.clear()
    
    def is_active(self) -> bool:
        """Check if video is loaded and playing."""
        return self._is_playing
    
    def is_loaded(self) -> bool:
        """Check if video is loaded."""
        return self._is_loaded
    
    def release(self):
        """Clean up resources."""
        self._stop_video()
        self.hand_tracker.release()
