"""
Main Window - Application shell with navigation
Premium multi-page application with sidebar navigation
"""
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QMessageBox, QFrame, QStackedWidget,
    QPushButton, QGraphicsDropShadowEffect, QSizePolicy
)
from PySide6.QtCore import Qt, Slot, QThread, Signal, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QFont, QColor

from ui.styles import DARK_THEME, COLORS, ICONS
from ui.pages.login_page import LoginPage
from ui.pages.dashboard_page import DashboardPage
from ui.pages.live_page import LivePage
from ui.pages.history_page import HistoryPage
from ui.pages.profile_page import ProfilePage
from ui.pages.admin_page import AdminPage

from ml.classifier import Classifier
from ml.data_collector import DataCollector
from ml.trainer import Trainer

# Import database service if available
try:
    from backend.services.db import db as database_service
except ImportError:
    database_service = None


class TrainerThread(QThread):
    """Background thread for model training."""
    progress = Signal(int, str)
    finished = Signal(dict)
    error = Signal(str)
    
    def __init__(self):
        super().__init__()
        self.trainer = Trainer()
    
    def run(self):
        try:
            self.progress.emit(10, "Loading training data...")
            features, labels = DataCollector.load_all_data()
            if features is None or len(features) == 0:
                self.error.emit("No training data found.")
                return
            self.progress.emit(30, f"Training on {len(labels)} samples...")
            accuracy = self.trainer.train(features, labels)
            self.progress.emit(70, "Saving model...")
            self.trainer.save()
            self.progress.emit(100, "Done")
            self.finished.emit(self.trainer.get_training_summary())
        except Exception as e:
            self.error.emit(str(e))


class NavButton(QPushButton):
    """Navigation sidebar button."""
    
    def __init__(self, icon, text, parent=None):
        super().__init__(f"{icon}  {text}", parent)
        self.setObjectName("navButton")
        self.setCheckable(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(48)


class Sidebar(QFrame):
    """Navigation sidebar."""
    
    navigate = Signal(str)  # page name
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("sidebar")
        self.setFixedWidth(240)
        self._current_button = None
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 24, 16, 24)
        layout.setSpacing(8)
        
        # Logo/Brand
        brand_layout = QHBoxLayout()
        brand_layout.setSpacing(12)
        
        logo = QLabel("✋")
        logo.setStyleSheet("font-size: 28px; background: transparent;")
        
        brand_text = QLabel("SignLang")
        brand_text.setStyleSheet(f"""
            font-size: 20px;
            font-weight: 700;
            color: {COLORS['text_primary']};
            background: transparent;
        """)
        
        brand_layout.addWidget(logo)
        brand_layout.addWidget(brand_text)
        brand_layout.addStretch()
        
        layout.addLayout(brand_layout)
        layout.addSpacing(32)
        
        # Navigation buttons
        self.nav_buttons = {}
        
        nav_items = [
            ("dashboard", "🏠", "Dashboard"),
            ("live", "🔴", "Live Translation"),
            ("history", "📜", "History"),
            ("profile", "👤", "Profile"),
        ]
        
        for page_id, icon, text in nav_items:
            btn = NavButton(icon, text)
            btn.clicked.connect(lambda checked, p=page_id: self._on_nav_click(p))
            self.nav_buttons[page_id] = btn
            layout.addWidget(btn)
            
        # Admin Button (Special case)
        self.admin_btn = NavButton("🛡️", "Admin Panel")
        self.admin_btn.clicked.connect(lambda: self._on_nav_click("admin"))
        self.admin_btn.hide() # Hidden by default
        self.nav_buttons["admin"] = self.admin_btn
        layout.addWidget(self.admin_btn)
        
        layout.addStretch()
        
        # Version info
        version_label = QLabel("v2.0.0")
        version_label.setStyleSheet(f"""
            color: {COLORS['text_muted']};
            font-size: 12px;
            background: transparent;
        """)
        version_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(version_label)
    
    def _on_nav_click(self, page_id):
        self.navigate.emit(page_id)
    
    def set_active(self, page_id):
        """Set the active navigation button."""
        for btn_id, btn in self.nav_buttons.items():
            btn.setChecked(btn_id == page_id)
            
    def show_admin_link(self, show=True):
        if show:
            self.admin_btn.show()
        else:
            self.admin_btn.hide()


class MainWindow(QMainWindow):
    """Main application window with multi-page navigation."""
    
    def __init__(self):
        super().__init__()
        
        # Services
        self.db = database_service
        self.classifier = Classifier()
        self.data_collector = DataCollector()
        self.trainer_thread = None
        
        # State
        self.user = None
        self.model_loaded = self.classifier.load()
        
        self._setup_ui()
        self._connect_signals()
        
        # Start with login page
        self._show_login()
    
    def _setup_ui(self):
        """Setup the main UI."""
        self.setWindowTitle("Sign Language Detector")
        self.setMinimumSize(1400, 900)
        self.setStyleSheet(DARK_THEME)
        
        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        
        # Main layout
        self.main_layout = QHBoxLayout(central)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # Sidebar (hidden initially)
        self.sidebar = Sidebar()
        self.sidebar.hide()
        self.main_layout.addWidget(self.sidebar)
        
        # Page container
        self.page_stack = QStackedWidget()
        self.main_layout.addWidget(self.page_stack)
        
        # Create pages
        self._create_pages()
    
    def _create_pages(self):
        """Create all application pages."""
        # Login page
        self.login_page = LoginPage(self.db)
        self.page_stack.addWidget(self.login_page)
        
        # Dashboard
        self.dashboard_page = DashboardPage(self.user, self.db)
        self.page_stack.addWidget(self.dashboard_page)
        
        # Live translation
        self.live_page = LivePage(self.classifier, self.db, self.user)
        self.page_stack.addWidget(self.live_page)
        
        # History
        self.history_page = HistoryPage(self.db, self.user)
        self.page_stack.addWidget(self.history_page)
        
        # Profile
        self.profile_page = ProfilePage(self.user, self.db)
        self.page_stack.addWidget(self.profile_page)
        
        # Admin Page
        self.admin_page = AdminPage(self.db)
        self.page_stack.addWidget(self.admin_page)
    
    def _connect_signals(self):
        """Connect all signals."""
        # Login signals
        self.login_page.login_successful.connect(self._on_login)
        self.login_page.signup_successful.connect(self._on_login)
        
        # Sidebar navigation
        self.sidebar.navigate.connect(self._navigate_to)
        
        # Dashboard navigation
        self.dashboard_page.navigate_to_live.connect(lambda: self._navigate_to("live"))
        self.dashboard_page.navigate_to_history.connect(lambda: self._navigate_to("history"))
        self.dashboard_page.navigate_to_profile.connect(lambda: self._navigate_to("profile"))
        self.dashboard_page.navigate_to_training.connect(self._start_training)
        
        # Page back buttons
        self.live_page.back_requested.connect(lambda: self._navigate_to("dashboard"))
        self.history_page.back_requested.connect(lambda: self._navigate_to("dashboard"))
        self.profile_page.back_requested.connect(lambda: self._navigate_to("dashboard"))
        
        # Live page translation events
        self.live_page.translation_made.connect(self._save_translation)
        
        # Profile logout
        self.profile_page.logout_requested.connect(self._on_logout)
    
    def _show_login(self):
        """Show login page."""
        self.sidebar.hide()
        self.page_stack.setCurrentWidget(self.login_page)
    
    @Slot(dict)
    def _on_login(self, user_data):
        """Handle successful login."""
        self.user = user_data
        
        # Update all pages with user data
        self.dashboard_page.update_user(user_data)
        self.live_page.user = user_data
        self.history_page.update_user(user_data)
        self.profile_page.update_user(user_data)
        
        # Check if admin
        is_admin = user_data.get("email") == "admin"
        self.sidebar.show_admin_link(is_admin)
        
        # Show main app
        self.sidebar.show()
        if is_admin:
             self._navigate_to("admin")
        else:
             self._navigate_to("dashboard")
        
        # Clear login form
        self.login_page.clear_form()
    
    def _on_logout(self):
        """Handle logout."""
        self.user = None
        
        # Stop any active camera
        self.live_page.stop_camera()
        
        # Show login
        self._show_login()
    
    def _navigate_to(self, page_id):
        """Navigate to a page."""
        self.sidebar.set_active(page_id)
        
        if page_id == "dashboard":
            self.dashboard_page.refresh_stats()
            self.page_stack.setCurrentWidget(self.dashboard_page)
        elif page_id == "live":
            self.page_stack.setCurrentWidget(self.live_page)
        elif page_id == "history":
            self.history_page.refresh()
            self.page_stack.setCurrentWidget(self.history_page)
        elif page_id == "profile":
            self.profile_page.refresh()
            self.page_stack.setCurrentWidget(self.profile_page)
        elif page_id == "admin":
            self.admin_page.refresh_all()
            self.page_stack.setCurrentWidget(self.admin_page)
    
    @Slot(str, float, str)
    def _save_translation(self, label, confidence, gesture_type):
        """Save translation to database."""
        if not self.db or not self.user or self.user.get("guest"):
            return
        
        try:
            import asyncio
            loop = asyncio.new_event_loop()
            loop.run_until_complete(
                self.db.save_translation(
                    self.user.get("id", ""),
                    label,
                    confidence,
                    gesture_type
                )
            )
            loop.close()
        except Exception as e:
            print(f"Failed to save translation: {e}")
    
    def _start_training(self):
        """Start model training."""
        if self.trainer_thread and self.trainer_thread.isRunning():
            QMessageBox.warning(self, "Training", "Training is already in progress.")
            return
        
        reply = QMessageBox.question(
            self, "Train Model",
            "Start training a new model with collected data?\n\nThis may take a few minutes.",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
        
        self.trainer_thread = TrainerThread()
        self.trainer_thread.progress.connect(self._on_training_progress)
        self.trainer_thread.finished.connect(self._on_training_done)
        self.trainer_thread.error.connect(self._on_training_error)
        self.trainer_thread.start()
    
    @Slot(int, str)
    def _on_training_progress(self, percent, message):
        """Handle training progress updates."""
        # Could show a progress dialog here
        print(f"Training: {percent}% - {message}")
    
    @Slot(dict)
    def _on_training_done(self, summary):
        """Handle training completion."""
        self.model_loaded = self.classifier.load()
        QMessageBox.information(
            self, "Training Complete",
            f"Model trained successfully!\n\nAccuracy: {summary['accuracy']:.1%}"
        )
    
    @Slot(str)
    def _on_training_error(self, error):
        """Handle training error."""
        QMessageBox.critical(self, "Training Error", f"Training failed:\n{error}")
    
    def closeEvent(self, event):
        """Handle window close."""
        # Stop camera
        self.live_page.cleanup()
        
        # Stop training thread
        if self.trainer_thread and self.trainer_thread.isRunning():
            self.trainer_thread.quit()
            self.trainer_thread.wait()
        
        event.accept()
