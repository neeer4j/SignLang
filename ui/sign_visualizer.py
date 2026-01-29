"""
Sign Visualization Component - Display sign language visually

This module provides UI components for displaying sign language:
- Hand landmark visualization
- Letter/word display with animations
- Fingerspelling sequence display
- Sign demonstration playback
"""
import numpy as np
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QFrame, QPushButton, QTextEdit, QProgressBar,
    QStackedWidget, QScrollArea, QSizePolicy,
    QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, Signal, Slot, QTimer, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QFont, QColor, QPainter, QPen, QBrush, QPainterPath

from ui.styles import COLORS

# Hand landmark connections for visualization
HAND_CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 4),      # Thumb
    (0, 5), (5, 6), (6, 7), (7, 8),      # Index
    (0, 9), (9, 10), (10, 11), (11, 12), # Middle
    (0, 13), (13, 14), (14, 15), (15, 16), # Ring
    (0, 17), (17, 18), (18, 19), (19, 20), # Pinky
    (5, 9), (9, 13), (13, 17)            # Palm
]


class HandLandmarkCanvas(QWidget):
    """Canvas for drawing hand landmark visualization."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(300, 300)
        
        # Landmark data
        self._landmarks = None  # 21 x 3 array
        
        # Styling
        self._landmark_color = QColor(0, 255, 128)
        self._connection_color = QColor(255, 255, 255)
        self._landmark_radius = 8
        self._connection_width = 2
        
        # Animation
        self._pulse_phase = 0.0
        self._animation_timer = QTimer()
        self._animation_timer.timeout.connect(self._update_animation)
        
        self.setStyleSheet(f"background-color: {COLORS['bg_dark']};")
    
    def set_landmarks(self, landmarks: np.ndarray):
        """Set hand landmarks to display.
        
        Args:
            landmarks: 21 x 3 numpy array of normalized coordinates
        """
        self._landmarks = landmarks
        self.update()
    
    def clear_landmarks(self):
        """Clear displayed landmarks."""
        self._landmarks = None
        self.update()
    
    def start_animation(self):
        """Start pulse animation."""
        self._animation_timer.start(50)
    
    def stop_animation(self):
        """Stop pulse animation."""
        self._animation_timer.stop()
    
    def _update_animation(self):
        """Update animation state."""
        self._pulse_phase += 0.1
        if self._pulse_phase > 2 * np.pi:
            self._pulse_phase = 0
        self.update()
    
    def paintEvent(self, event):
        """Paint the landmarks."""
        super().paintEvent(event)
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw background
        painter.fillRect(self.rect(), QColor(COLORS['bg_dark']))
        
        if self._landmarks is None:
            # Draw placeholder
            self._draw_placeholder(painter)
            return
        
        # Map landmarks to widget coordinates
        width = self.width()
        height = self.height()
        margin = 30
        
        def to_pixel(lm):
            # Landmarks are normalized [0, 1], flip y for screen coords
            x = margin + lm[0] * (width - 2 * margin)
            y = margin + lm[1] * (height - 2 * margin)
            return int(x), int(y)
        
        # Draw connections
        pen = QPen(self._connection_color, self._connection_width)
        painter.setPen(pen)
        
        for start_idx, end_idx in HAND_CONNECTIONS:
            if start_idx < len(self._landmarks) and end_idx < len(self._landmarks):
                x1, y1 = to_pixel(self._landmarks[start_idx])
                x2, y2 = to_pixel(self._landmarks[end_idx])
                painter.drawLine(x1, y1, x2, y2)
        
        # Draw landmarks
        pulse = np.sin(self._pulse_phase) * 0.3 + 1.0
        
        for i, lm in enumerate(self._landmarks):
            x, y = to_pixel(lm)
            
            # Fingertips get larger markers
            radius = self._landmark_radius
            if i in [4, 8, 12, 16, 20]:  # Fingertips
                radius = int(radius * 1.3 * pulse)
            
            # Draw landmark circle
            brush = QBrush(self._landmark_color)
            painter.setBrush(brush)
            painter.setPen(QPen(Qt.white, 1))
            painter.drawEllipse(x - radius, y - radius, radius * 2, radius * 2)
    
    def _draw_placeholder(self, painter):
        """Draw placeholder when no landmarks."""
        painter.setPen(QPen(QColor(COLORS['text_muted']), 2))
        
        # Draw hand outline placeholder
        width = self.width()
        height = self.height()
        
        # Simple hand outline
        path = QPainterPath()
        cx, cy = width // 2, height // 2
        
        # Draw a simple hand shape
        painter.drawText(
            self.rect(),
            Qt.AlignCenter,
            "✋\n\nWaiting for sign..."
        )


class SignLetterDisplay(QFrame):
    """Display for showing current sign letter/word."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("signLetterDisplay")
        self._current_letter = ""
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Large letter/word display
        self.letter_label = QLabel("?")
        self.letter_label.setAlignment(Qt.AlignCenter)
        self.letter_label.setStyleSheet(f"""
            font-size: 96px;
            font-weight: bold;
            color: {COLORS['accent']};
            background: transparent;
        """)
        
        # Description
        self.description_label = QLabel("")
        self.description_label.setAlignment(Qt.AlignCenter)
        self.description_label.setStyleSheet(f"""
            font-size: 16px;
            color: {COLORS['text_secondary']};
            background: transparent;
        """)
        
        layout.addWidget(self.letter_label)
        layout.addWidget(self.description_label)
        
        # Glow effect
        self._glow = QGraphicsDropShadowEffect()
        self._glow.setBlurRadius(30)
        self._glow.setColor(QColor(139, 92, 246, 150))
        self._glow.setOffset(0, 0)
        self.letter_label.setGraphicsEffect(self._glow)
        
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_card']};
                border-radius: 16px;
            }}
        """)
    
    def set_letter(self, letter: str, description: str = ""):
        """Set the displayed letter/word.
        
        Args:
            letter: Letter or word to display
            description: Optional description
        """
        self.letter_label.setText(letter)
        self.description_label.setText(description)
        
        if letter != self._current_letter:
            self._current_letter = letter
            self._animate_change()
    
    def _animate_change(self):
        """Animate letter change."""
        # Pulse the glow
        anim = QPropertyAnimation(self._glow, b"blurRadius")
        anim.setDuration(200)
        anim.setStartValue(0)
        anim.setEndValue(40)
        anim.setEasingCurve(QEasingCurve.OutCubic)
        anim.start()
        
        # Reset after animation
        QTimer.singleShot(200, lambda: self._glow.setBlurRadius(20))
    
    def clear(self):
        """Clear the display."""
        self.letter_label.setText("?")
        self.description_label.setText("")
        self._current_letter = ""


class FingerspellSequence(QFrame):
    """Display for fingerspelling sequence."""
    
    current_index_changed = Signal(int)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._letters = []
        self._current_index = -1
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        
        # Title
        title = QLabel("Fingerspelling")
        title.setStyleSheet(f"color: {COLORS['text_secondary']}; font-weight: bold;")
        layout.addWidget(title)
        
        # Letters container
        self.letters_container = QHBoxLayout()
        self.letters_container.setSpacing(8)
        layout.addLayout(self.letters_container)
        
        # Progress
        self.progress = QProgressBar()
        self.progress.setMaximum(100)
        self.progress.setTextVisible(False)
        self.progress.setMaximumHeight(4)
        layout.addWidget(self.progress)
        
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_panel']};
                border-radius: 12px;
            }}
        """)
    
    def set_word(self, word: str):
        """Set word to fingerspell.
        
        Args:
            word: Word to spell out
        """
        self._letters = list(word.upper())
        self._current_index = -1
        self._rebuild_display()
    
    def _rebuild_display(self):
        """Rebuild the letter display."""
        # Clear existing
        while self.letters_container.count():
            item = self.letters_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Add letter labels
        for i, letter in enumerate(self._letters):
            label = QLabel(letter)
            label.setAlignment(Qt.AlignCenter)
            label.setFixedSize(40, 40)
            label.setStyleSheet(f"""
                font-size: 20px;
                font-weight: bold;
                color: {COLORS['text_secondary']};
                background-color: {COLORS['bg_card']};
                border-radius: 8px;
            """)
            self.letters_container.addWidget(label)
        
        self.progress.setValue(0)
    
    def advance(self):
        """Advance to next letter."""
        if self._current_index < len(self._letters) - 1:
            self._current_index += 1
            self._update_highlight()
            self.current_index_changed.emit(self._current_index)
            return self._letters[self._current_index]
        return None
    
    def _update_highlight(self):
        """Update letter highlighting."""
        for i in range(self.letters_container.count()):
            item = self.letters_container.itemAt(i)
            if item and item.widget():
                label = item.widget()
                if i == self._current_index:
                    label.setStyleSheet(f"""
                        font-size: 24px;
                        font-weight: bold;
                        color: {COLORS['text_primary']};
                        background-color: {COLORS['accent']};
                        border-radius: 8px;
                    """)
                elif i < self._current_index:
                    label.setStyleSheet(f"""
                        font-size: 20px;
                        font-weight: bold;
                        color: {COLORS['success']};
                        background-color: {COLORS['bg_card']};
                        border-radius: 8px;
                    """)
                else:
                    label.setStyleSheet(f"""
                        font-size: 20px;
                        font-weight: bold;
                        color: {COLORS['text_secondary']};
                        background-color: {COLORS['bg_card']};
                        border-radius: 8px;
                    """)
        
        # Update progress
        if self._letters:
            progress = (self._current_index + 1) / len(self._letters) * 100
            self.progress.setValue(int(progress))
    
    def reset(self):
        """Reset to beginning."""
        self._current_index = -1
        self._update_highlight()
        self.progress.setValue(0)
    
    def get_current_letter(self) -> str:
        """Get currently highlighted letter."""
        if 0 <= self._current_index < len(self._letters):
            return self._letters[self._current_index]
        return ""


class SignVisualizerWidget(QFrame):
    """Main widget for text-to-sign visualization.
    
    Displays signs for text input using:
    - Hand landmark animation
    - Letter/word display
    - Fingerspelling sequences
    """
    
    playback_finished = Signal()
    sign_changed = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._is_playing = False
        self._current_sign_index = 0
        self._signs = []
        self._setup_ui()
        
        # Playback timer
        self._playback_timer = QTimer()
        self._playback_timer.timeout.connect(self._advance_sign)
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        # Header
        header = QHBoxLayout()
        
        title = QLabel("📤 Text to Sign")
        title.setObjectName("sectionTitle")
        header.addWidget(title)
        header.addStretch()
        
        layout.addLayout(header)
        
        # Text input area
        input_frame = QFrame()
        input_frame.setObjectName("card")
        input_layout = QVBoxLayout(input_frame)
        
        input_label = QLabel("Enter text to convert to sign language:")
        input_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        input_layout.addWidget(input_label)
        
        self.text_input = QTextEdit()
        self.text_input.setPlaceholderText("Type your message here...")
        self.text_input.setMaximumHeight(80)
        self.text_input.setStyleSheet(f"""
            QTextEdit {{
                background-color: {COLORS['bg_input']};
                color: {COLORS['text_primary']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                padding: 12px;
                font-size: 14px;
            }}
        """)
        input_layout.addWidget(self.text_input)
        
        # Convert button
        button_row = QHBoxLayout()
        
        self.convert_btn = QPushButton("🔄 Convert to Signs")
        self.convert_btn.setObjectName("primary")
        self.convert_btn.clicked.connect(self._on_convert_clicked)
        button_row.addWidget(self.convert_btn)
        
        self.play_btn = QPushButton("▶️ Play")
        self.play_btn.clicked.connect(self._toggle_playback)
        self.play_btn.setEnabled(False)
        button_row.addWidget(self.play_btn)
        
        self.reset_btn = QPushButton("⏮️ Reset")
        self.reset_btn.clicked.connect(self._reset_playback)
        self.reset_btn.setEnabled(False)
        button_row.addWidget(self.reset_btn)
        
        button_row.addStretch()
        input_layout.addLayout(button_row)
        
        layout.addWidget(input_frame)
        
        # Visualization area
        viz_layout = QHBoxLayout()
        
        # Hand landmark canvas
        self.landmark_canvas = HandLandmarkCanvas()
        self.landmark_canvas.setMinimumSize(250, 250)
        viz_layout.addWidget(self.landmark_canvas)
        
        # Sign display
        right_panel = QVBoxLayout()
        
        self.letter_display = SignLetterDisplay()
        self.letter_display.setMinimumHeight(200)
        right_panel.addWidget(self.letter_display)
        
        self.fingerspell_widget = FingerspellSequence()
        self.fingerspell_widget.hide()
        right_panel.addWidget(self.fingerspell_widget)
        
        viz_layout.addLayout(right_panel)
        
        layout.addLayout(viz_layout)
        
        # Status bar
        self.status_label = QLabel("Enter text and click Convert")
        self.status_label.setStyleSheet(f"color: {COLORS['text_muted']};")
        layout.addWidget(self.status_label)
        
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_secondary']};
                border-radius: 12px;
            }}
        """)
    
    def set_signs(self, signs: list):
        """Set signs to display.
        
        Args:
            signs: List of SignOutput objects
        """
        self._signs = signs
        self._current_sign_index = 0
        self._is_playing = False
        
        if signs:
            self.play_btn.setEnabled(True)
            self.reset_btn.setEnabled(True)
            self.status_label.setText(f"Ready to show {len(signs)} signs")
            self._show_current_sign()
        else:
            self.play_btn.setEnabled(False)
            self.reset_btn.setEnabled(False)
            self.status_label.setText("No signs to display")
    
    def _on_convert_clicked(self):
        """Handle convert button click."""
        text = self.text_input.toPlainText().strip()
        if not text:
            self.status_label.setText("Please enter some text")
            return
        
        # Import here to avoid circular dependency
        from core.text_to_sign import TextToSignTranslator
        translator = TextToSignTranslator()
        result = translator.translate(text)
        
        self.set_signs(result.signs)
    
    def _toggle_playback(self):
        """Toggle playback start/pause."""
        if self._is_playing:
            self._pause_playback()
        else:
            self._start_playback()
    
    def _start_playback(self):
        """Start sign playback."""
        if not self._signs:
            return
        
        self._is_playing = True
        self.play_btn.setText("⏸️ Pause")
        self._show_current_sign()
        
        # Calculate display time for current sign
        current_sign = self._signs[self._current_sign_index]
        duration_ms = int(current_sign.duration_hint * 1000)
        self._playback_timer.start(duration_ms)
        
        self.landmark_canvas.start_animation()
    
    def _pause_playback(self):
        """Pause sign playback."""
        self._is_playing = False
        self.play_btn.setText("▶️ Play")
        self._playback_timer.stop()
        self.landmark_canvas.stop_animation()
    
    def _reset_playback(self):
        """Reset to first sign."""
        self._pause_playback()
        self._current_sign_index = 0
        if self._signs:
            self._show_current_sign()
        self.fingerspell_widget.reset()
    
    def _advance_sign(self):
        """Advance to next sign."""
        self._current_sign_index += 1
        
        if self._current_sign_index >= len(self._signs):
            # Finished
            self._pause_playback()
            self._current_sign_index = len(self._signs) - 1
            self.status_label.setText("Playback complete")
            self.playback_finished.emit()
            return
        
        self._show_current_sign()
        
        # Set timer for next sign
        current_sign = self._signs[self._current_sign_index]
        duration_ms = int(current_sign.duration_hint * 1000)
        self._playback_timer.setInterval(duration_ms)
    
    def _show_current_sign(self):
        """Display current sign."""
        if not self._signs or self._current_sign_index >= len(self._signs):
            return
        
        sign = self._signs[self._current_sign_index]
        
        # Update letter display
        display_text = sign.display_text
        if sign.emoji:
            display_text = f"{sign.emoji}\n{display_text}"
        
        description = ""
        if sign.sign_definition:
            description = sign.sign_definition.description
        
        self.letter_display.set_letter(display_text, description)
        
        # Handle fingerspelling
        if sign.letters and len(sign.letters) > 1:
            self.fingerspell_widget.set_word("".join(sign.letters))
            self.fingerspell_widget.show()
        else:
            self.fingerspell_widget.hide()
        
        # Update landmarks if available
        if sign.landmark_data:
            self.landmark_canvas.set_landmarks(np.array(sign.landmark_data))
        else:
            self.landmark_canvas.clear_landmarks()
        
        # Update status
        progress = f"{self._current_sign_index + 1}/{len(self._signs)}"
        self.status_label.setText(f"Showing: {sign.text} ({progress})")
        
        # Emit signal
        self.sign_changed.emit(sign.text)
    
    def clear(self):
        """Clear all content."""
        self._signs = []
        self._current_sign_index = 0
        self._pause_playback()
        self.letter_display.clear()
        self.landmark_canvas.clear_landmarks()
        self.fingerspell_widget.hide()
        self.text_input.clear()
        self.play_btn.setEnabled(False)
        self.reset_btn.setEnabled(False)
        self.status_label.setText("Enter text and click Convert")
