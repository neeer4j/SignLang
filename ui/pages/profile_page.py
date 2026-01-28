"""
Profile Page - User settings and account management
Clean profile view with stats and logout
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFrame, QGridLayout, QMessageBox,
    QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QColor

from ui.styles import COLORS, ICONS


class ProfileCard(QFrame):
    """User profile display card."""
    
    def __init__(self, user_data, parent=None):
        super().__init__(parent)
        self.user = user_data or {}
        self.setObjectName("card")
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)
        layout.setAlignment(Qt.AlignCenter)
        
        # Avatar circle
        avatar_frame = QFrame()
        avatar_frame.setFixedSize(100, 100)
        avatar_frame.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {COLORS['primary']}, stop:1 {COLORS['accent']});
                border-radius: 50px;
            }}
        """)
        avatar_layout = QVBoxLayout(avatar_frame)
        avatar_layout.setContentsMargins(0, 0, 0, 0)
        
        # Get initials from email
        email = self.user.get("email", "User")
        initials = email[0].upper() if email else "U"
        
        initial_label = QLabel(initials)
        initial_label.setStyleSheet("""
            font-size: 40px;
            font-weight: 700;
            color: white;
            background: transparent;
        """)
        initial_label.setAlignment(Qt.AlignCenter)
        avatar_layout.addWidget(initial_label)
        
        # Center the avatar
        avatar_container = QHBoxLayout()
        avatar_container.addStretch()
        avatar_container.addWidget(avatar_frame)
        avatar_container.addStretch()
        layout.addLayout(avatar_container)
        
        # User name
        name = email.split("@")[0].title() if "@" in email else email
        name_label = QLabel(name)
        name_label.setStyleSheet(f"""
            font-size: 24px;
            font-weight: 700;
            color: {COLORS['text_primary']};
        """)
        name_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(name_label)
        
        # Email
        email_label = QLabel(email)
        email_label.setStyleSheet(f"""
            font-size: 14px;
            color: {COLORS['text_secondary']};
        """)
        email_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(email_label)
        
        # Account status badge
        if self.user.get("guest"):
            status = "Guest Account"
            status_color = COLORS['warning']
        elif self.user.get("offline"):
            status = "Offline Mode"
            status_color = COLORS['text_muted']
        else:
            status = "Verified Account"
            status_color = COLORS['success']
        
        status_badge = QLabel(f"• {status}")
        status_badge.setStyleSheet(f"""
            font-size: 13px;
            font-weight: 600;
            color: {status_color};
        """)
        status_badge.setAlignment(Qt.AlignCenter)
        layout.addWidget(status_badge)
    
    def update_user(self, user_data):
        """Update user data."""
        self.user = user_data
        # Would need to refresh UI


class StatsRow(QFrame):
    """Row of user statistics."""
    
    def __init__(self, stats=None, parent=None):
        super().__init__(parent)
        self.stats = stats or {}
        self.setObjectName("card")
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(0)
        
        stats_data = [
            (str(self.stats.get("total", 0)), "Total\nTranslations"),
            (str(self.stats.get("unique_signs", 0)), "Unique\nSigns"),
            (str(self.stats.get("today", 0)), "Today's\nSessions"),
            ("0", "Day\nStreak"),
        ]
        
        for i, (value, label) in enumerate(stats_data):
            stat_layout = QVBoxLayout()
            stat_layout.setAlignment(Qt.AlignCenter)
            
            value_label = QLabel(value)
            value_label.setStyleSheet(f"""
                font-size: 28px;
                font-weight: 700;
                color: {COLORS['primary']};
            """)
            value_label.setAlignment(Qt.AlignCenter)
            
            label_label = QLabel(label)
            label_label.setStyleSheet(f"""
                font-size: 12px;
                color: {COLORS['text_muted']};
                text-align: center;
            """)
            label_label.setAlignment(Qt.AlignCenter)
            
            stat_layout.addWidget(value_label)
            stat_layout.addWidget(label_label)
            layout.addLayout(stat_layout)
            
            # Add divider between stats
            if i < len(stats_data) - 1:
                divider = QFrame()
                divider.setStyleSheet(f"background-color: {COLORS['border']}; max-width: 1px;")
                divider.setFixedWidth(1)
                layout.addWidget(divider)


class SettingsSection(QFrame):
    """Settings and actions section."""
    
    logout_requested = Signal()
    password_change_requested = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)
        
        # Section title
        title = QLabel("⚙️ Account Settings")
        title.setObjectName("sectionTitle")
        layout.addWidget(title)
        
        # Settings buttons
        settings = [
            ("🔑", "Change Password", self._change_password),
            ("🔔", "Notifications", self._show_coming_soon),
            ("🎨", "Appearance", self._show_coming_soon),
            ("📤", "Export Data", self._show_coming_soon),
            ("❓", "Help & Support", self._show_coming_soon),
        ]
        
        for icon, text, action in settings:
            btn = QPushButton(f"{icon}  {text}")
            btn.setObjectName("navButton")
            btn.setStyleSheet("""
                QPushButton {
                    text-align: left;
                    padding: 14px 16px;
                }
            """)
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(action)
            layout.addWidget(btn)
        
        layout.addSpacing(20)
        
        # Danger zone
        danger_title = QLabel("⚠️ Danger Zone")
        danger_title.setObjectName("sectionTitle")
        danger_title.setStyleSheet(f"color: {COLORS['danger']};")
        layout.addWidget(danger_title)
        
        logout_btn = QPushButton("🚪  Sign Out")
        logout_btn.setObjectName("danger")
        logout_btn.setCursor(Qt.PointingHandCursor)
        logout_btn.clicked.connect(self.logout_requested.emit)
        layout.addWidget(logout_btn)
    
    def _change_password(self):
        self.password_change_requested.emit()
    
    def _show_coming_soon(self):
        QMessageBox.information(
            self, "Coming Soon",
            "This feature is coming in a future update! 🚀"
        )


class ProfilePage(QWidget):
    """User profile and settings page."""
    
    back_requested = Signal()
    logout_requested = Signal()
    
    def __init__(self, user_data=None, db_service=None, parent=None):
        super().__init__(parent)
        self.user = user_data or {}
        self.db = db_service
        self._stats = {}
        self._setup_ui()
        self._load_stats()
    
    def _setup_ui(self):
        """Setup profile page UI."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(40, 32, 40, 32)
        main_layout.setSpacing(24)
        
        # === HEADER ===
        header = QHBoxLayout()
        
        back_btn = QPushButton("← Back")
        back_btn.setObjectName("ghost")
        back_btn.clicked.connect(self.back_requested.emit)
        
        title = QLabel("👤 Profile & Settings")
        title.setObjectName("pageTitle")
        
        header.addWidget(back_btn)
        header.addWidget(title)
        header.addStretch()
        
        main_layout.addLayout(header)
        
        # === CONTENT ===
        content_layout = QHBoxLayout()
        content_layout.setSpacing(24)
        
        # Left column: Profile + Stats
        left_column = QVBoxLayout()
        left_column.setSpacing(20)
        
        self.profile_card = ProfileCard(self.user)
        self.stats_row = StatsRow(self._stats)
        
        left_column.addWidget(self.profile_card)
        left_column.addWidget(self.stats_row)
        left_column.addStretch()
        
        # Right column: Settings
        self.settings_section = SettingsSection()
        self.settings_section.logout_requested.connect(self._handle_logout)
        self.settings_section.password_change_requested.connect(self._change_password)
        
        content_layout.addLayout(left_column, 1)
        content_layout.addWidget(self.settings_section, 1)
        
        main_layout.addLayout(content_layout)
        
        # === APP INFO ===
        info_frame = QFrame()
        info_frame.setObjectName("card")
        info_layout = QHBoxLayout(info_frame)
        info_layout.setContentsMargins(24, 16, 24, 16)
        
        app_name = QLabel("Sign Language Detector")
        app_name.setStyleSheet(f"font-weight: 600; color: {COLORS['text_primary']};")
        
        version = QLabel("v2.0.0")
        version.setStyleSheet(f"color: {COLORS['text_muted']};")
        
        made_with = QLabel("Made with ❤️ using Python, MediaPipe & scikit-learn")
        made_with.setStyleSheet(f"color: {COLORS['text_muted']};")
        
        info_layout.addWidget(app_name)
        info_layout.addWidget(version)
        info_layout.addStretch()
        info_layout.addWidget(made_with)
        
        main_layout.addWidget(info_frame)
    
    def _load_stats(self):
        """Load user statistics."""
        if not self.db or self.user.get("guest"):
            return
        
        try:
            import asyncio
            loop = asyncio.new_event_loop()
            self._stats = loop.run_until_complete(
                self.db.get_translation_stats(self.user.get("id", ""))
            )
            loop.close()
            
            # Update stats display
            self._update_stats_display()
        except Exception as e:
            print(f"Failed to load stats: {e}")
    
    def _update_stats_display(self):
        """Update the stats row with new data."""
        # Would need to rebuild stats_row widget
        pass
    
    def _handle_logout(self):
        """Handle logout request."""
        reply = QMessageBox.question(
            self, "Sign Out",
            "Are you sure you want to sign out?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            if self.db:
                try:
                    import asyncio
                    loop = asyncio.new_event_loop()
                    loop.run_until_complete(self.db.sign_out())
                    loop.close()
                except:
                    pass
            
            self.logout_requested.emit()
    
    def _change_password(self):
        """Handle password change request."""
        if self.user.get("guest") or self.user.get("offline"):
            QMessageBox.information(
                self, "Not Available",
                "Password change is not available in offline mode."
            )
            return
        
        QMessageBox.information(
            self, "Change Password",
            "To change your password, please visit your Supabase dashboard or use the password reset feature on the login page."
        )
    
    def update_user(self, user_data):
        """Update user data."""
        self.user = user_data
        self._load_stats()
    
    def refresh(self):
        """Refresh profile data."""
        self._load_stats()
