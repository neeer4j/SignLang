"""
Login Page - Premium Authentication UI (Redesigned)
Modern centered glass-card design with slideshow background
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QLineEdit, QFrame, QGraphicsDropShadowEffect,
    QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QPropertyAnimation, QEasingCurve, QTimer, QPoint, QSize, Property
from PySide6.QtGui import QFont, QColor, QPainter, QLinearGradient, QBrush, QPen, QPixmap
import os

from ui.styles import COLORS

class ImageBackground(QWidget):
    """Background widget with slideshow cross-fade."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.pixmaps = []
        self.current_idx = 0
        self.next_idx = 1
        self._fade_factor = 0.0  # 0.0 = current, 1.0 = next
        
        # Load images
        self._load_images()
        
        # Transition animation
        self.anim = QPropertyAnimation(self, b"fade_factor")
        self.anim.setDuration(1500) # 1.5s fade
        self.anim.setEasingCurve(QEasingCurve.InOutQuad)
        self.anim.finished.connect(self._on_transition_finished)
        
        # Slideshow timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.next_slide)
        if len(self.pixmaps) > 1:
            self.timer.start(8000) # 8 seconds
        
    def _load_images(self):
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        assets_dir = os.path.join(base_dir, "assets")
        
        valid_exts = {".jpg", ".jpeg", ".png", ".webp"}
        if os.path.exists(assets_dir):
            for f in sorted(os.listdir(assets_dir)):
                if os.path.splitext(f)[1].lower() in valid_exts:
                    full_path = os.path.join(assets_dir, f)
                    pm = QPixmap(full_path)
                    if not pm.isNull():
                        self.pixmaps.append(pm)
        
        if not self.pixmaps:
            print("Warning: No images found in assets")
            
    def next_slide(self):
        if len(self.pixmaps) < 2:
            return
        self.next_idx = (self.current_idx + 1) % len(self.pixmaps)
        self.anim.setStartValue(0.0)
        self.anim.setEndValue(1.0)
        self.anim.start()
        
    def _on_transition_finished(self):
        self.current_idx = self.next_idx
        self._fade_factor = 0.0
        self.update()
        
    def get_fade_factor(self):
        return self._fade_factor
        
    def set_fade_factor(self, val):
        self._fade_factor = val
        self.update()
        
    fade_factor = Property(float, get_fade_factor, set_fade_factor)
            
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        if not self.pixmaps:
            painter.fillRect(self.rect(), QColor("#0f0f14"))
            return

        # Helper to draw scaled pixmap
        def draw_pixmap(pm, opacity=1.0):
            if opacity <= 0: return
            scaled = pm.scaled(
                self.size(), 
                Qt.KeepAspectRatioByExpanding, 
                Qt.SmoothTransformation
            )
            x = (self.width() - scaled.width()) // 2
            y = (self.height() - scaled.height()) // 2
            painter.setOpacity(opacity)
            painter.drawPixmap(x, y, scaled)

        # Draw current image
        draw_pixmap(self.pixmaps[self.current_idx], 1.0 - self._fade_factor)
        
        # Draw next image (if fading)
        if self._fade_factor > 0:
            draw_pixmap(self.pixmaps[self.next_idx], self._fade_factor)
            
        # Reset opacity for overlay
        painter.setOpacity(1.0)
        # Dark overlay
        painter.fillRect(self.rect(), QColor(0, 0, 0, 80))

class GlassCard(QFrame):
    """Semi-transparent card container."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QFrame {
                background-color: rgba(30, 30, 40, 0.7);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 24px;
            }
        """)
        # Add shadow
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(80)
        shadow.setColor(QColor(0, 0, 0, 100))
        shadow.setOffset(0, 20)
        self.setGraphicsEffect(shadow)

class StyledLineEdit(QLineEdit):
    """Modern input field."""
    def __init__(self, placeholder="", is_password=False, parent=None):
        super().__init__(parent)
        self.setPlaceholderText(placeholder)
        if is_password:
            self.setEchoMode(QLineEdit.Password)
            
        self.setStyleSheet(f"""
            QLineEdit {{
                background-color: rgba(20, 20, 25, 0.6);
                border: 2px solid rgba(255, 255, 255, 0.08);
                border-radius: 12px;
                padding: 16px;
                color: white;
                font-size: 14px;
                font-family: 'Segoe UI';
            }}
            QLineEdit:focus {{
                border-color: {COLORS['primary']};
                background-color: rgba(20, 20, 25, 0.9);
            }}
        """)
        self.setMinimumHeight(54)

class LoginPage(QWidget):
    """
    Redesigned Login Page
    Centered glass card layout
    """
    login_successful = Signal(dict)
    signup_successful = Signal(dict)
    
    def __init__(self, db_service=None, parent=None):
        super().__init__(parent)
        self.db = db_service
        self.is_login_mode = True
        self._setup_ui()
        self._connect_signals()
        
    def _setup_ui(self):
        # 1. Background Layer (Full Window)
        self.bg = ImageBackground(self)
        self.bg.setGeometry(0, 0, 3000, 2000) # Oversized to cover resize
        self.bg.lower()
        
        # 2. Main Layout (Centered)
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignCenter)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # 3. Glass Card Container
        self.card = GlassCard()
        self.card.setFixedSize(440, 680)
        
        card_layout = QVBoxLayout(self.card)
        card_layout.setContentsMargins(40, 50, 40, 50)
        card_layout.setSpacing(20)
        
        # === BRANDING ===
        logo_area = QVBoxLayout()
        logo_area.setSpacing(10)
        
        icon_label = QLabel("👋")
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setStyleSheet("font-size: 64px; background: transparent; border: none;")
        
        app_title = QLabel("SignLang")
        app_title.setAlignment(Qt.AlignCenter)
        app_title.setStyleSheet("""
            font-size: 28px; 
            font-weight: 800; 
            color: white; 
            letter-spacing: -0.5px;
            background: transparent;
            border: none;
        """)
        
        logo_area.addWidget(icon_label)
        logo_area.addWidget(app_title)
        card_layout.addLayout(logo_area)
        
        card_layout.addSpacing(10)
        
        # === HEADER TEXT ===
        self.header_title = QLabel("Welcome Back")
        self.header_title.setAlignment(Qt.AlignCenter)
        self.header_title.setStyleSheet("""
            font-size: 20px; 
            font-weight: 600; 
            color: white;
            background: transparent;
            border: none;
        """)
        
        self.header_subtitle = QLabel("Sign in to your account")
        self.header_subtitle.setAlignment(Qt.AlignCenter)
        self.header_subtitle.setStyleSheet(f"""
            font-size: 14px; 
            color: {COLORS['text_muted']};
            background: transparent;
            border: none;
        """)
        
        card_layout.addWidget(self.header_title)
        card_layout.addWidget(self.header_subtitle)
        
        card_layout.addSpacing(20)
        
        # === FORM INPUTS ===
        self.email_input = StyledLineEdit("Email or Username")
        self.password_input = StyledLineEdit("Password", is_password=True)
        self.confirm_input = StyledLineEdit("Confirm Password", is_password=True)
        self.confirm_input.hide()
        
        card_layout.addWidget(self.email_input)
        card_layout.addWidget(self.password_input)
        card_layout.addWidget(self.confirm_input)
        
        # === MESSAGES ===
        self.error_label = QLabel()
        self.error_label.setAlignment(Qt.AlignCenter)
        self.error_label.setStyleSheet(f"color: {COLORS['danger']}; font-size: 13px; background: transparent; border: none;")
        self.error_label.hide()
        card_layout.addWidget(self.error_label)
        
        self.success_label = QLabel()
        self.success_label.setAlignment(Qt.AlignCenter)
        self.success_label.setStyleSheet(f"color: {COLORS['success']}; font-size: 13px; background: transparent; border: none;")
        self.success_label.hide()
        card_layout.addWidget(self.success_label)
        
        card_layout.addSpacing(10)
        
        # === MAIN BUTTON ===
        self.submit_btn = QPushButton("Sign In")
        self.submit_btn.setCursor(Qt.PointingHandCursor)
        self.submit_btn.setMinimumHeight(54)
        self.submit_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {COLORS['primary']}, stop:1 {COLORS['accent']});
                color: white;
                font-weight: bold;
                font-size: 15px;
                border-radius: 12px;
                border: none;
            }}
            QPushButton:hover {{
                opacity: 0.9;
            }}
            QPushButton:pressed {{
                background: {COLORS['primary_hover']};
            }}
            QPushButton:disabled {{
                background: {COLORS['bg_card']};
                color: {COLORS['text_disabled']};
            }}
        """)
        card_layout.addWidget(self.submit_btn)
        
        # === FOOTER ACTIONS ===
        self.toggle_btn = QPushButton("Create an account")
        self.toggle_btn.setCursor(Qt.PointingHandCursor)
        self.toggle_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {COLORS['text_secondary']};
                font-size: 13px;
                border: none;
            }}
            QPushButton:hover {{
                color: white;
            }}
        """)
        
        self.skip_btn = QPushButton("Continue as Guest")
        self.skip_btn.setCursor(Qt.PointingHandCursor)
        self.skip_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {COLORS['text_muted']};
                font-size: 12px;
                border: none;
            }}
            QPushButton:hover {{
                color: {COLORS['text_secondary']};
            }}
        """)
        
        card_layout.addWidget(self.toggle_btn)
        card_layout.addStretch()
        card_layout.addWidget(self.skip_btn, alignment=Qt.AlignCenter)
        
        main_layout.addWidget(self.card)
        
    def resizeEvent(self, event):
        """Keep background full size."""
        self.bg.setGeometry(self.rect())
        super().resizeEvent(event)
        
    def _connect_signals(self):
        self.submit_btn.clicked.connect(self._handle_submit)
        self.toggle_btn.clicked.connect(self._toggle_mode)
        self.skip_btn.clicked.connect(self._skip_login)
        self.email_input.returnPressed.connect(self.password_input.setFocus)
        self.password_input.returnPressed.connect(self._handle_submit)
        self.confirm_input.returnPressed.connect(self._handle_submit)

    def _toggle_mode(self):
        self.is_login_mode = not self.is_login_mode
        self._clear_messages()
        
        if self.is_login_mode:
            self.header_title.setText("Welcome Back")
            self.header_subtitle.setText("Sign in to your account")
            self.submit_btn.setText("Sign In")
            self.toggle_btn.setText("Create an account")
            self.confirm_input.hide()
            self.card.setFixedSize(440, 680)
        else:
            self.header_title.setText("Join SignLang")
            self.header_subtitle.setText("Create your free account")
            self.submit_btn.setText("Sign Up")
            self.toggle_btn.setText("Already have an account?")
            self.confirm_input.show()
            self.card.setFixedSize(440, 740) # Slightly taller for extra field

    def _handle_submit(self):
        email = self.email_input.text().strip()
        password = self.password_input.text()
        
        if not email or not password:
            self._show_error("Please fill in all fields")
            return
            
        if not self.is_login_mode and password != self.confirm_input.text():
            self._show_error("Passwords do not match")
            return
            
        self.submit_btn.setEnabled(False)
        self.submit_btn.setText("Processing...")
        
        # Async Auth Call
        if self.db:
            import asyncio
            loop = asyncio.new_event_loop()
            try:
                if self.is_login_mode:
                    res = loop.run_until_complete(self.db.sign_in(email, password))
                else:
                    res = loop.run_until_complete(self.db.sign_up(email, password))
                loop.close()
                
                if "error" in res:
                    self._show_error(res["error"])
                    self.submit_btn.setEnabled(True)
                    self.submit_btn.setText("Sign In" if self.is_login_mode else "Sign Up")
                else:
                    self._show_success("Success!")
                    QTimer.singleShot(800, lambda: self._complete_auth(res.get("user")))
            except Exception as e:
                self._show_error(str(e))
                self.submit_btn.setEnabled(True)
        else:
            self._complete_auth({"id": "offline", "email": email})

    def _complete_auth(self, user):
        if self.is_login_mode:
            self.login_successful.emit(user)
        else:
            self.signup_successful.emit(user)
            
    def _skip_login(self):
        self.login_successful.emit({"id": "guest", "email": "Guest", "guest": True})

    def _show_error(self, msg):
        self.error_label.setText(msg)
        self.error_label.show()
        self.success_label.hide()
        
    def _show_success(self, msg):
        self.success_label.setText(msg)
        self.success_label.show()
        self.error_label.hide()

    def _clear_messages(self):
        self.error_label.hide()
        self.success_label.hide()

    def clear_form(self):
        self.email_input.clear()
        self.password_input.clear()
        self.confirm_input.clear()
        self._clear_messages()
        self.submit_btn.setEnabled(True)
