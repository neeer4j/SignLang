"""
History Page - Translation history with filtering
Beautiful list view with search and delete functionality
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFrame, QScrollArea, QLineEdit,
    QListWidget, QListWidgetItem, QGraphicsDropShadowEffect,
    QMessageBox, QComboBox
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont, QColor

from ui.styles import COLORS, ICONS
from datetime import datetime


class HistoryItem(QFrame):
    """Single history entry card."""
    
    delete_requested = Signal(str)  # translation_id
    
    def __init__(self, data, parent=None):
        super().__init__(parent)
        self.data = data
        self.setObjectName("cardHover")
        self.setCursor(Qt.PointingHandCursor)
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(16)
        
        # Sign label (large)
        sign_label = QLabel(self.data.get("sign_label", "?"))
        sign_label.setStyleSheet(f"""
            font-size: 32px;
            font-weight: 700;
            color: {COLORS['primary']};
            min-width: 50px;
            background: transparent;
        """)
        sign_label.setAlignment(Qt.AlignCenter)
        
        # Details
        details_layout = QVBoxLayout()
        details_layout.setSpacing(4)
        
        # Gesture type badge
        gesture_type = self.data.get("gesture_type", "static")
        type_color = COLORS['primary'] if gesture_type == "static" else COLORS['accent']
        type_label = QLabel(f"{'🔤' if gesture_type == 'static' else '👋'} {gesture_type.title()} Gesture")
        type_label.setStyleSheet(f"""
            font-size: 12px;
            font-weight: 600;
            color: {type_color};
            background: transparent;
        """)
        
        # Confidence
        confidence = self.data.get("confidence", 0)
        conf_percent = int(confidence * 100) if confidence <= 1 else int(confidence)
        conf_label = QLabel(f"Confidence: {conf_percent}%")
        conf_label.setStyleSheet(f"""
            font-size: 13px;
            color: {COLORS['text_secondary']};
            background: transparent;
        """)
        
        details_layout.addWidget(type_label)
        details_layout.addWidget(conf_label)
        
        # Timestamp
        created_at = self.data.get("created_at", "")
        if created_at:
            try:
                dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                time_str = dt.strftime("%b %d, %Y at %I:%M %p")
            except:
                time_str = created_at
        else:
            time_str = "Just now"
        
        time_label = QLabel(time_str)
        time_label.setStyleSheet(f"""
            font-size: 13px;
            color: {COLORS['text_muted']};
            background: transparent;
        """)
        
        # Delete button
        delete_btn = QPushButton("🗑️")
        delete_btn.setObjectName("iconButton")
        delete_btn.setToolTip("Delete this entry")
        delete_btn.clicked.connect(lambda: self.delete_requested.emit(self.data.get("id", "")))
        
        layout.addWidget(sign_label)
        layout.addLayout(details_layout)
        layout.addStretch()
        layout.addWidget(time_label)
        layout.addWidget(delete_btn)


class HistoryPage(QWidget):
    """Translation history page with search and filtering."""
    
    back_requested = Signal()
    
    def __init__(self, db_service=None, user_data=None, parent=None):
        super().__init__(parent)
        self.db = db_service
        self.user = user_data or {}
        self._history_items = []
        self._filtered_items = []
        self._setup_ui()
        self._load_history()
    
    def _setup_ui(self):
        """Setup history page UI."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(40, 32, 40, 32)
        main_layout.setSpacing(24)
        
        # === HEADER ===
        header = QHBoxLayout()
        
        back_btn = QPushButton("← Back")
        back_btn.setObjectName("ghost")
        back_btn.clicked.connect(self.back_requested.emit)
        
        title = QLabel("📜 Translation History")
        title.setObjectName("pageTitle")
        
        # Stats
        self.count_label = QLabel("0 translations")
        self.count_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 14px;")
        
        header.addWidget(back_btn)
        header.addWidget(title)
        header.addStretch()
        header.addWidget(self.count_label)
        
        main_layout.addLayout(header)
        
        # === FILTERS ===
        filter_layout = QHBoxLayout()
        filter_layout.setSpacing(16)
        
        # Search
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Search translations...")
        self.search_input.setObjectName("searchInput")
        self.search_input.textChanged.connect(self._filter_history)
        
        # Type filter
        self.type_filter = QComboBox()
        self.type_filter.addItems(["All Types", "Static (Letters)", "Dynamic (Gestures)"])
        self.type_filter.currentIndexChanged.connect(self._filter_history)
        
        # Refresh button
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.clicked.connect(self._load_history)
        
        # Clear all button
        self.clear_btn = QPushButton("🗑️ Clear All")
        self.clear_btn.setObjectName("danger")
        self.clear_btn.clicked.connect(self._clear_all)
        
        filter_layout.addWidget(self.search_input, 3)
        filter_layout.addWidget(self.type_filter, 1)
        filter_layout.addWidget(refresh_btn)
        filter_layout.addWidget(self.clear_btn)
        
        main_layout.addLayout(filter_layout)
        
        # === HISTORY LIST ===
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background: transparent;
            }
        """)
        
        self.list_container = QWidget()
        self.list_container.setStyleSheet("background: transparent;")
        self.list_layout = QVBoxLayout(self.list_container)
        self.list_layout.setContentsMargins(0, 0, 0, 0)
        self.list_layout.setSpacing(12)
        
        scroll_area.setWidget(self.list_container)
        main_layout.addWidget(scroll_area)
        
        # === EMPTY STATE ===
        self.empty_state = QFrame()
        self.empty_state.setObjectName("card")
        empty_layout = QVBoxLayout(self.empty_state)
        empty_layout.setAlignment(Qt.AlignCenter)
        empty_layout.setContentsMargins(40, 60, 40, 60)
        
        empty_icon = QLabel("📭")
        empty_icon.setStyleSheet("font-size: 64px; background: transparent;")
        empty_icon.setAlignment(Qt.AlignCenter)
        
        empty_title = QLabel("No translations yet")
        empty_title.setStyleSheet(f"""
            font-size: 20px;
            font-weight: 600;
            color: {COLORS['text_primary']};
            background: transparent;
        """)
        empty_title.setAlignment(Qt.AlignCenter)
        
        empty_desc = QLabel("Start translating to see your history here")
        empty_desc.setStyleSheet(f"""
            font-size: 14px;
            color: {COLORS['text_muted']};
            background: transparent;
        """)
        empty_desc.setAlignment(Qt.AlignCenter)
        
        empty_layout.addWidget(empty_icon)
        empty_layout.addWidget(empty_title)
        empty_layout.addWidget(empty_desc)
        
        self.list_layout.addWidget(self.empty_state)
        self.empty_state.hide()
    
    def _load_history(self):
        """Load history from database."""
        # Clear existing items
        self._clear_list()
        
        if not self.db or self.user.get("guest"):
            self._show_empty_state("Sign in to save your translation history")
            return
        
        try:
            import asyncio
            loop = asyncio.new_event_loop()
            history = loop.run_until_complete(
                self.db.get_translations(self.user.get("id", ""), limit=100)
            )
            loop.close()
            
            self._history_items = history
            self._filtered_items = history
            self._render_list()
            
        except Exception as e:
            print(f"Failed to load history: {e}")
            self._show_empty_state(f"Failed to load history: {str(e)}")
    
    def _render_list(self):
        """Render the filtered history list."""
        self._clear_list()
        
        if not self._filtered_items:
            self._show_empty_state()
            return
        
        self.empty_state.hide()
        self.count_label.setText(f"{len(self._filtered_items)} translations")
        
        for item_data in self._filtered_items:
            item = HistoryItem(item_data)
            item.delete_requested.connect(self._delete_item)
            self.list_layout.addWidget(item)
        
        # Add spacer at the end
        self.list_layout.addStretch()
    
    def _clear_list(self):
        """Clear the list view (except empty state)."""
        while self.list_layout.count():
            item = self.list_layout.takeAt(0)
            widget = item.widget()
            if widget and widget is not self.empty_state:
                widget.deleteLater()
    
    def _filter_history(self):
        """Filter history based on search and type."""
        search_text = self.search_input.text().lower()
        type_filter = self.type_filter.currentIndex()
        
        self._filtered_items = []
        
        for item in self._history_items:
            # Search filter
            if search_text and search_text not in item.get("sign_label", "").lower():
                continue
            
            # Type filter
            gesture_type = item.get("gesture_type", "static")
            if type_filter == 1 and gesture_type != "static":
                continue
            if type_filter == 2 and gesture_type != "dynamic":
                continue
            
            self._filtered_items.append(item)
        
        self._render_list()
    
    def _delete_item(self, translation_id):
        """Delete a single translation."""
        if not self.db or not translation_id:
            return
        
        reply = QMessageBox.question(
            self, "Delete Translation",
            "Are you sure you want to delete this entry?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                import asyncio
                loop = asyncio.new_event_loop()
                loop.run_until_complete(
                    self.db.delete_translation(translation_id, self.user.get("id", ""))
                )
                loop.close()
                
                # Refresh list
                self._load_history()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete: {e}")
    
    def _clear_all(self):
        """Clear all translation history."""
        if not self.db or self.user.get("guest"):
            return
        
        reply = QMessageBox.warning(
            self, "Clear All History",
            "Are you sure you want to delete ALL your translation history?\n\nThis action cannot be undone.",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                import asyncio
                loop = asyncio.new_event_loop()
                loop.run_until_complete(
                    self.db.clear_history(self.user.get("id", ""))
                )
                loop.close()
                
                self._history_items = []
                self._filtered_items = []
                self._render_list()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to clear history: {e}")
    
    def _show_empty_state(self, message=None):
        """Show empty state."""
        # Re-add to layout if needed
        if self.empty_state.parent() != self.list_container:
            self.list_layout.addWidget(self.empty_state)
        self.empty_state.show()
        self.count_label.setText("0 translations")
        
        if message:
            # Update empty state message if provided
            pass
    
    def refresh(self):
        """Refresh history."""
        self._load_history()
    
    def update_user(self, user_data):
        """Update user data."""
        self.user = user_data
        self._load_history()
