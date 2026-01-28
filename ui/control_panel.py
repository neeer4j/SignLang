"""
Control Panel - Clean Minimalist Design
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QLabel, QComboBox, QFrame, QProgressBar, QSizePolicy
)
from PySide6.QtCore import Signal, Qt
from config import ASL_LABELS
from ui.styles import ICONS

class ControlPanel(QWidget):
    # Signals remain the same
    start_camera = Signal()
    stop_camera = Signal()
    start_collection = Signal(str)
    stop_collection = Signal()
    train_model = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._is_collecting = False

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(24)
        layout.setContentsMargins(0, 0, 0, 0)

        # === CAMERA SECTION ===
        cam_section = QVBoxLayout()
        cam_section.setSpacing(12)
        
        title = QLabel("CAMERA CONTROLS")
        title.setObjectName("sectionTitle")
        cam_section.addWidget(title)
        
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)
        
        self.start_btn = QPushButton("Start Camera")
        self.start_btn.setObjectName("success") # Green-ish
        self.start_btn.setHeight = 40
        self.start_btn.clicked.connect(self._on_start_btn)
        
        self.stop_btn = QPushButton("Stop")
        self.stop_btn.setObjectName("danger")
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self._on_stop_btn)
        
        btn_layout.addWidget(self.start_btn, 2)
        btn_layout.addWidget(self.stop_btn, 1)
        cam_section.addLayout(btn_layout)
        
        layout.addLayout(cam_section)

        # === RECOGNITION MODE ===
        mode_section = QVBoxLayout()
        mode_section.setSpacing(12)
        
        title = QLabel("RECOGNITION MODE")
        title.setObjectName("sectionTitle")
        mode_section.addWidget(title)
        
        self.static_btn = QPushButton("Static Signs (A-Z)")
        self.static_btn.setCheckable(True)
        self.static_btn.setChecked(True)
        self.static_btn.clicked.connect(self._ensure_one_mode)
        
        self.dynamic_btn = QPushButton("Dynamic Gestures")
        self.dynamic_btn.setCheckable(True)
        self.dynamic_btn.clicked.connect(self._ensure_one_mode) # For now allow one or both? Let's treat as toggles.
        
        mode_section.addWidget(self.static_btn)
        mode_section.addWidget(self.dynamic_btn)
        layout.addLayout(mode_section)

        # === DATA COLLECTION ===
        data_section = QVBoxLayout()
        data_section.setSpacing(12)
        
        title = QLabel("DATA COLLECTION")
        title.setObjectName("sectionTitle")
        data_section.addWidget(title)
        
        # Label Selection
        label_row = QHBoxLayout()
        label_lbl = QLabel("Target Sign:")
        self.label_combo = QComboBox()
        self.label_combo.addItems(ASL_LABELS)
        label_row.addWidget(label_lbl)
        label_row.addWidget(self.label_combo)
        data_section.addLayout(label_row)
        
        # Action Button
        self.collect_btn = QPushButton("Start Recording")
        self.collect_btn.clicked.connect(self._toggle_collection)
        data_section.addWidget(self.collect_btn)
        
        # Stats
        self.sample_count = QLabel("0 samples")
        self.sample_count.setObjectName("status")
        self.sample_count.setAlignment(Qt.AlignRight)
        data_section.addWidget(self.sample_count)
        
        layout.addLayout(data_section)

        # === TRAINING ===
        train_section = QVBoxLayout()
        train_section.setSpacing(12)
        
        title = QLabel("MODEL")
        title.setObjectName("sectionTitle")
        train_section.addWidget(title)
        
        self.train_btn = QPushButton("Train New Model")
        self.train_btn.setObjectName("primary")
        self.train_btn.clicked.connect(self.train_model.emit)
        train_section.addWidget(self.train_btn)
        
        self.progress = QProgressBar()
        self.progress.setTextVisible(False)
        self.progress.setVisible(False)
        self.progress.setFixedHeight(4)
        train_section.addWidget(self.progress)
        
        layout.addLayout(train_section)
        
        layout.addStretch()

    def _on_start_btn(self):
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.start_camera.emit()

    def _on_stop_btn(self):
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.stop_camera.emit()
        if self._is_collecting:
            self._toggle_collection()

    def _toggle_collection(self):
        if not self._is_collecting:
            self._is_collecting = True
            self.collect_btn.setText("Stop Recording")
            self.collect_btn.setObjectName("danger") # Red for stop
            # Refresh style
            self.collect_btn.style().unpolish(self.collect_btn)
            self.collect_btn.style().polish(self.collect_btn)
            self.start_collection.emit(self.label_combo.currentText())
        else:
            self._is_collecting = False
            self.collect_btn.setText("Start Recording")
            self.collect_btn.setObjectName("") # Reset
            self.collect_btn.style().unpolish(self.collect_btn)
            self.collect_btn.style().polish(self.collect_btn)
            self.stop_collection.emit()

    def _ensure_one_mode(self):
        # Optional: logic if we want mutually exclusive modes, 
        # but currently user could want both. Keeping simple.
        pass

    def update_sample_count(self, count):
        self.sample_count.setText(f"{count} samples")

    def set_training_progress(self, val, msg=""):
        self.progress.setVisible(val > 0 and val < 100)
        self.progress.setValue(val)
        if val == 100:
            self.train_btn.setText("Training Complete")
        elif val > 0:
            self.train_btn.setText(f"Training... {val}%")
        else:
            self.train_btn.setText("Train New Model")

    def is_collecting(self): return self._is_collecting
