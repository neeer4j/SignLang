"""
Prediction Panel - Clean Minimalist Design
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QFrame, QSizePolicy, QPushButton, QTextEdit, QApplication,
    QScrollArea
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont
from ui.styles import ICONS

class PredictionPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.history = []
        self.sentence = ""
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(24)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # === PREDICTION DISPLAY ===
        pred_section = QVBoxLayout()
        pred_section.setSpacing(0)
        
        title = QLabel("DETECTED SIGN")
        title.setObjectName("sectionTitle")
        title.setAlignment(Qt.AlignCenter)
        pred_section.addWidget(title)
        
        self.pred_label = QLabel("—")
        self.pred_label.setObjectName("prediction")
        self.pred_label.setAlignment(Qt.AlignCenter)
        self.pred_label.setFixedHeight(120)
        pred_section.addWidget(self.pred_label)
        
        self.conf_label = QLabel("Waiting for hand...")
        self.conf_label.setObjectName("status")
        self.conf_label.setAlignment(Qt.AlignCenter)
        pred_section.addWidget(self.conf_label)
        
        layout.addLayout(pred_section)

        # === SENTENCE BUILDER ===
        sent_section = QVBoxLayout()
        sent_section.setSpacing(12)
        
        title = QLabel("SENTENCE")
        title.setObjectName("sectionTitle")
        sent_section.addWidget(title)
        
        self.text_area = QTextEdit()
        self.text_area.setPlaceholderText("Signs will appear here...")
        self.text_area.setFixedHeight(100)
        sent_section.addWidget(self.text_area)
        
        # Tools
        tools_layout = QHBoxLayout()
        tools_layout.setSpacing(8)
        
        self.space_btn = QPushButton("Space")
        self.space_btn.clicked.connect(lambda: self._add_text(" "))
        
        self.back_btn = QPushButton("⌫")
        self.back_btn.setFixedWidth(40)
        self.back_btn.clicked.connect(self._backspace)
        
        self.copy_btn = QPushButton("Copy")
        self.copy_btn.setObjectName("primary")
        self.copy_btn.clicked.connect(self._copy)
        
        self.clear_btn = QPushButton("Clear")
        self.clear_btn.clicked.connect(self._clear)
        
        tools_layout.addWidget(self.space_btn)
        tools_layout.addWidget(self.back_btn)
        tools_layout.addWidget(self.clear_btn)
        tools_layout.addWidget(self.copy_btn)
        sent_section.addLayout(tools_layout)
        
        layout.addLayout(sent_section)
        
        # === HISTORY ===
        hist_section = QVBoxLayout()
        hist_section.setSpacing(8)
        
        title = QLabel("HISTORY")
        title.setObjectName("sectionTitle")
        hist_section.addWidget(title)
        
        self.history_lbl = QLabel("No signs yet")
        self.history_lbl.setObjectName("status")
        self.history_lbl.setWordWrap(True)
        hist_section.addWidget(self.history_lbl)
        
        layout.addLayout(hist_section)
        layout.addStretch()

    def update_prediction(self, sign, conf):
        display_text = sign
        is_dynamic = sign.startswith("✨")
        if is_dynamic:
            display_text = sign.replace("✨", "")
            
        self.pred_label.setText(display_text)
        self.conf_label.setText(f"{conf:.0%} Confidence")
        
        # Update history
        if not self.history or self.history[-1] != display_text:
            self.history.append(display_text)
            self.history = self.history[-10:] # Keep last 10
            self.history_lbl.setText(" ".join(self.history))
            
            # Logic for sentence addition
            if not is_dynamic:
                self._add_text(display_text)

    def add_letter_to_sentence(self, text):
        self._add_text(text)

    def _add_text(self, text):
        self.text_area.insertPlainText(text)
        self.text_area.ensureCursorVisible()

    def _backspace(self):
        self.text_area.textCursor().deletePreviousChar()

    def _clear(self):
        self.text_area.clear()

    def _copy(self):
        QApplication.clipboard().setText(self.text_area.toPlainText())
        orig = self.copy_btn.text()
        self.copy_btn.setText("Copied!")
        QTimer.singleShot(2000, lambda: self.copy_btn.setText(orig))

    def set_hand_status(self, detected):
        if not detected:
            self.conf_label.setText("No Hand Detected")
            self.pred_label.setText("—")
