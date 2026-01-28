"""
Dashboard Page - Main hub after login
Beautiful overview with stats and quick navigation
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFrame, QGridLayout, QScrollArea,
    QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, Signal, QTimer, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QFont, QColor

from ui.styles import COLORS, ICONS


class StatCard(QFrame):
    """Animated statistic card with icon and value."""
    
    def __init__(self, icon, value, label, color=None, parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self.setCursor(Qt.PointingHandCursor)
        self.color = color or COLORS['primary']
        self._setup_ui(icon, value, label)
        self._setup_hover_effect()
    
    def _setup_ui(self, icon, value, label):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)
        
        # Icon container
        icon_container = QFrame()
        icon_container.setFixedSize(56, 56)
        icon_container.setStyleSheet(f"""
            QFrame {{
                background-color: {self.color}20;
                border-radius: 14px;
                border: 1px solid {self.color}40;
            }}
        """)
        icon_layout = QVBoxLayout(icon_container)
        icon_layout.setContentsMargins(0, 0, 0, 0)
        icon_label = QLabel(icon)
        icon_label.setStyleSheet("font-size: 24px; background: transparent; border: none;")
        icon_label.setAlignment(Qt.AlignCenter)
        icon_layout.addWidget(icon_label)
        
        # Value
        self.value_label = QLabel(str(value))
        self.value_label.setObjectName("statsNumber")
        self.value_label.setStyleSheet(f"color: {self.color};")
        
        # Label
        self.label_label = QLabel(label)
        self.label_label.setObjectName("statsLabel")
        
        layout.addWidget(icon_container)
        layout.addStretch()
        layout.addWidget(self.value_label)
        layout.addWidget(self.label_label)
    
    def _setup_hover_effect(self):
        self.shadow = QGraphicsDropShadowEffect()
        self.shadow.setBlurRadius(0)
        self.shadow.setColor(QColor(self.color))
        self.shadow.setOffset(0, 0)
        self.setGraphicsEffect(self.shadow)
    
    def enterEvent(self, event):
        self.anim = QPropertyAnimation(self.shadow, b"blurRadius")
        self.anim.setDuration(200)
        self.anim.setStartValue(0)
        self.anim.setEndValue(30)
        self.anim.start()
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        self.anim = QPropertyAnimation(self.shadow, b"blurRadius")
        self.anim.setDuration(200)
        self.anim.setStartValue(30)
        self.anim.setEndValue(0)
        self.anim.start()
        super().leaveEvent(event)
    
    def update_value(self, value):
        self.value_label.setText(str(value))


class QuickActionCard(QFrame):
    """Large action card for main navigation."""
    
    clicked = Signal()
    
    def __init__(self, icon, title, description, color, parent=None):
        super().__init__(parent)
        self.setCursor(Qt.PointingHandCursor)
        self.color = color
        self._setup_ui(icon, title, description)
        self._apply_style()
    
    def _setup_ui(self, icon, title, description):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        # Icon (left side)
        icon_label = QLabel(icon)
        icon_label.setStyleSheet("font-size: 32px; background: transparent; border: none;")
        icon_label.setFixedSize(48, 48)
        icon_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(icon_label)
        
        # Content (middle)
        content = QVBoxLayout()
        content.setSpacing(4)
        
        title_label = QLabel(title)
        title_label.setStyleSheet(f"""
            font-size: 16px;
            font-weight: 600;
            color: {COLORS['text_primary']};
            background: transparent;
            border: none;
        """)
        
        desc_label = QLabel(description)
        desc_label.setStyleSheet(f"""
            font-size: 13px;
            color: {COLORS['text_muted']};
            background: transparent;
            border: none;
        """)
        
        content.addWidget(title_label)
        content.addWidget(desc_label)
        layout.addLayout(content)
        
        layout.addStretch()
        
        # Arrow (right side)
        arrow = QLabel("→")
        arrow.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 18px; background: transparent; border: none;")
        layout.addWidget(arrow)
    
    def _apply_style(self):
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_card']};
                border: 1px solid {COLORS['border']};
                border-left: 4px solid {self.color};
                border-radius: 12px;
            }}
            QFrame:hover {{
                background-color: {COLORS['bg_card_hover']};
                border-color: {self.color};
            }}
        """)
    
    def mousePressEvent(self, event):
        self.clicked.emit()
        super().mousePressEvent(event)


class DashboardPage(QWidget):
    """Main dashboard with overview and quick navigation."""
    
    # Navigation signals
    navigate_to_live = Signal()
    navigate_to_history = Signal()
    navigate_to_profile = Signal()
    navigate_to_training = Signal()
    
    def __init__(self, user_data=None, db_service=None, parent=None):
        super().__init__(parent)
        self.user = user_data or {}
        self.db = db_service
        self._setup_ui()
        self._load_stats()
    
    def _setup_ui(self):
        """Setup dashboard UI."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(40, 40, 40, 40)
        main_layout.setSpacing(32)
        
        # === HEADER ===
        header = QHBoxLayout()
        
        # Welcome section
        welcome_box = QVBoxLayout()
        welcome_box.setSpacing(4)
        
        # Get user name from email
        email = self.user.get("email", "User")
        name = email.split("@")[0].title() if "@" in email else email
        
        greeting = self._get_greeting()
        welcome_label = QLabel(f"{greeting}, {name}! 👋")
        welcome_label.setObjectName("welcomeText")
        
        subtitle = QLabel("Ready to practice sign language today?")
        subtitle.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 16px;")
        
        welcome_box.addWidget(welcome_label)
        welcome_box.addWidget(subtitle)
        
        header.addLayout(welcome_box)
        header.addStretch()
        
        # Quick action buttons in header
        if not self.user.get("guest"):
            profile_btn = QPushButton(f"👤 {name[:8]}")
            profile_btn.setObjectName("ghost")
            profile_btn.clicked.connect(self.navigate_to_profile.emit)
            header.addWidget(profile_btn)
        
        main_layout.addLayout(header)
        
        # === STATS ROW ===
        stats_label = QLabel("📊 Your Statistics")
        stats_label.setObjectName("sectionTitle")
        main_layout.addWidget(stats_label)
        
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(20)
        
        self.total_card = StatCard("📝", "0", "Total Translations", COLORS['primary'])
        self.today_card = StatCard("📅", "0", "Today's Sessions", COLORS['accent'])
        self.unique_card = StatCard("✨", "0", "Unique Signs", COLORS['success'])
        self.streak_card = StatCard("🔥", "0", "Day Streak", "#f59e0b")
        
        stats_layout.addWidget(self.total_card)
        stats_layout.addWidget(self.today_card)
        stats_layout.addWidget(self.unique_card)
        stats_layout.addWidget(self.streak_card)
        
        main_layout.addLayout(stats_layout)
        
        # === QUICK ACTIONS ===
        actions_label = QLabel("🚀 Quick Actions")
        actions_label.setObjectName("sectionTitle")
        main_layout.addWidget(actions_label)
        
        actions_layout = QGridLayout()
        actions_layout.setSpacing(20)
        
        # Live Translation Card
        live_card = QuickActionCard(
            "🔴",
            "Live Translation",
            "Start real-time recognition",
            COLORS['primary']
        )
        live_card.clicked.connect(self.navigate_to_live.emit)
        
        # History Card
        history_card = QuickActionCard(
            "📜",
            "History",
            "View past sessions",
            COLORS['accent']
        )
        history_card.clicked.connect(self.navigate_to_history.emit)
        
        # Training Card
        train_card = QuickActionCard(
            "🧠",
            "Train Model",
            "Teach new custom gestures",
            COLORS['success']
        )
        train_card.clicked.connect(self.navigate_to_training.emit)
        
        # Profile Card
        profile_card = QuickActionCard(
            "⚙️",
            "Settings",
            "Manage account & prefs",
            "#64748b"
        )
        profile_card.clicked.connect(self.navigate_to_profile.emit)
        
        actions_layout.addWidget(live_card, 0, 0)
        actions_layout.addWidget(history_card, 0, 1)
        actions_layout.addWidget(train_card, 1, 0)
        actions_layout.addWidget(profile_card, 1, 1)
        
        main_layout.addLayout(actions_layout)
        
        # === TIPS SECTION ===
        tips_frame = QFrame()
        tips_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['warning_bg']};
                border: 1px solid {COLORS['warning']}40;
                border-radius: 12px;
            }}
        """)
        tips_layout = QHBoxLayout(tips_frame)
        tips_layout.setContentsMargins(16, 12, 16, 12)
        tips_layout.setSpacing(12)
        
        tip_icon = QLabel("💡")
        tip_icon.setStyleSheet("font-size: 18px; background: transparent; border: none;")
        
        tip_text = QLabel("Tip: Ensure good lighting for better hand recognition accuracy.")
        tip_text.setStyleSheet(f"color: {COLORS['warning']}; font-size: 13px; font-weight: 500; background: transparent; border: none;")
        
        tips_layout.addWidget(tip_icon)
        tips_layout.addWidget(tip_text)
        tips_layout.addStretch()
        
        main_layout.addWidget(tips_frame)
        main_layout.addStretch()
    
    def _get_greeting(self):
        """Get time-appropriate greeting."""
        from datetime import datetime
        hour = datetime.now().hour
        
        if hour < 12:
            return "Good morning"
        elif hour < 17:
            return "Good afternoon"
        else:
            return "Good evening"
    
    def _load_stats(self):
        """Load user statistics from database."""
        if not self.db or self.user.get("guest"):
            return
        
        try:
            import asyncio
            loop = asyncio.new_event_loop()
            stats = loop.run_until_complete(
                self.db.get_translation_stats(self.user.get("id", ""))
            )
            loop.close()
            
            self.total_card.update_value(stats.get("total", 0))
            self.today_card.update_value(stats.get("today", 0))
            self.unique_card.update_value(stats.get("unique_signs", 0))
        except Exception as e:
            print(f"Failed to load stats: {e}")
    
    def update_user(self, user_data):
        """Update user data and refresh stats."""
        self.user = user_data
        self._load_stats()
    
    def refresh_stats(self):
        """Refresh statistics."""
        self._load_stats()
