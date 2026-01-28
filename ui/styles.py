"""
PySide6 Styles - Premium Professional Dark Theme
Modern, user-friendly design with smooth aesthetics
"""

# ==================== COLOR PALETTE ====================
# Premium dark theme with vibrant accents
COLORS = {
    # Backgrounds - Deep, rich darks
    'bg_app': '#0f0f14',           # Almost black
    'bg_panel': '#1a1a24',         # Dark panels
    'bg_card': '#242432',          # Card backgrounds
    'bg_card_hover': '#2d2d3d',    # Card hover state
    'bg_input': '#16161e',         # Input fields
    'bg_sidebar': '#12121a',       # Sidebar
    
    # Primary - Vibrant Purple/Indigo
    'primary': '#8b5cf6',          # Violet-500
    'primary_hover': '#7c3aed',    # Violet-600
    'primary_light': '#a78bfa',    # Violet-400
    'primary_glow': 'rgba(139, 92, 246, 0.3)',
    
    # Accent - Cyan/Teal
    'accent': '#06b6d4',           # Cyan-500
    'accent_hover': '#0891b2',     # Cyan-600
    'accent_light': '#22d3ee',     # Cyan-400
    
    # Semantic Colors
    'success': '#10b981',          # Emerald-500
    'success_bg': 'rgba(16, 185, 129, 0.1)',
    'warning': '#f59e0b',          # Amber-500
    'warning_bg': 'rgba(245, 158, 11, 0.1)',
    'danger': '#ef4444',           # Red-500
    'danger_bg': 'rgba(239, 68, 68, 0.1)',
    
    # Text
    'text_primary': '#f8fafc',     # Almost white
    'text_secondary': '#94a3b8',   # Slate-400
    'text_muted': '#64748b',       # Slate-500
    'text_disabled': '#475569',    # Slate-600
    
    # Borders & Dividers
    'border': '#2d2d3d',
    'border_light': '#3d3d50',
    'divider': '#1e1e2a',
    
    # Gradients (for buttons and highlights)
    'gradient_start': '#8b5cf6',
    'gradient_end': '#06b6d4',
}

# ==================== PREMIUM DARK THEME ====================
DARK_THEME = """
/* ========== GLOBAL RESET & BASE ========== */
QWidget {
    background-color: #0f0f14;
    color: #f8fafc;
    font-family: 'Segoe UI', 'SF Pro Display', -apple-system, sans-serif;
    font-size: 14px;
    selection-background-color: #8b5cf6;
    selection-color: white;
}

QMainWindow {
    background-color: #0f0f14;
}

/* ========== TYPOGRAPHY ========== */
QLabel {
    color: #f8fafc;
    border: none;
    background: transparent;
}

QLabel#appTitle {
    font-size: 28px;
    font-weight: 700;
    color: #f8fafc;
    letter-spacing: -0.5px;
}

QLabel#title {
    font-size: 24px;
    font-weight: 700;
    color: #f8fafc;
    letter-spacing: -0.5px;
}

QLabel#pageTitle {
    font-size: 20px;
    font-weight: 600;
    color: #f8fafc;
}

QLabel#subtitle {
    font-size: 14px;
    color: #94a3b8;
    font-weight: 500;
}

QLabel#sectionTitle {
    font-size: 12px;
    font-weight: 700;
    text-transform: uppercase;
    color: #64748b;
    letter-spacing: 1.5px;
}

QLabel#prediction {
    font-size: 96px;
    font-weight: 800;
    color: #8b5cf6;
}

QLabel#predictionSmall {
    font-size: 48px;
    font-weight: 700;
    color: #8b5cf6;
}

QLabel#confidence {
    font-size: 18px;
    font-weight: 600;
    color: #10b981;
}

QLabel#status {
    color: #94a3b8;
    font-size: 13px;
}

QLabel#errorText {
    color: #ef4444;
    font-size: 13px;
}

QLabel#successText {
    color: #10b981;
    font-size: 13px;
}

QLabel#welcomeText {
    font-size: 32px;
    font-weight: 700;
    color: #f8fafc;
}

QLabel#statsNumber {
    font-size: 36px;
    font-weight: 700;
    color: #8b5cf6;
}

QLabel#statsLabel {
    font-size: 12px;
    font-weight: 600;
    color: #64748b;
    text-transform: uppercase;
    letter-spacing: 1px;
}

/* ========== CARDS & FRAMES ========== */
QFrame#card {
    background-color: #1a1a24;
    border: 1px solid #2d2d3d;
    border-radius: 16px;
}

QFrame#cardHover {
    background-color: #1a1a24;
    border: 1px solid #2d2d3d;
    border-radius: 16px;
}

QFrame#cardHover:hover {
    background-color: #242432;
    border-color: #3d3d50;
}

QFrame#highlightCard {
    background-color: #1a1a24;
    border: 1px solid #8b5cf6;
    border-radius: 16px;
}

QFrame#cameraView {
    background-color: #000000;
    border-radius: 16px;
    border: 2px solid #2d2d3d;
}

QFrame#sidebar {
    background-color: #12121a;
    border-right: 1px solid #1e1e2a;
}

QFrame#divider {
    background-color: #2d2d3d;
    max-height: 1px;
    min-height: 1px;
}

/* ========== BUTTONS - MODERN STYLE ========== */
QPushButton {
    background-color: #1a1a24;
    border: 1px solid #2d2d3d;
    border-radius: 10px;
    color: #f8fafc;
    padding: 12px 20px;
    font-weight: 600;
    font-size: 14px;
}

QPushButton:hover {
    background-color: #242432;
    border-color: #3d3d50;
}

QPushButton:pressed {
    background-color: #12121a;
}

QPushButton:disabled {
    background-color: #12121a;
    color: #475569;
    border-color: #1e1e2a;
}

/* Primary Button - Gradient style */
QPushButton#primary {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #8b5cf6, stop:1 #7c3aed);
    border: none;
    color: white;
    padding: 14px 28px;
    font-weight: 600;
}

QPushButton#primary:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #7c3aed, stop:1 #6d28d9);
}

QPushButton#primary:pressed {
    background: #6d28d9;
}

QPushButton#primary:disabled {
    background: #3d3d50;
    color: #64748b;
}

/* Secondary Button */
QPushButton#secondary {
    background-color: transparent;
    border: 2px solid #8b5cf6;
    color: #8b5cf6;
}

QPushButton#secondary:hover {
    background-color: rgba(139, 92, 246, 0.1);
    border-color: #a78bfa;
    color: #a78bfa;
}

/* Accent Button - Cyan */
QPushButton#accent {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #06b6d4, stop:1 #0891b2);
    border: none;
    color: white;
}

QPushButton#accent:hover {
    background: #0891b2;
}

/* Success Button */
QPushButton#success {
    background-color: rgba(16, 185, 129, 0.15);
    color: #10b981;
    border: 1px solid rgba(16, 185, 129, 0.3);
}

QPushButton#success:hover {
    background-color: rgba(16, 185, 129, 0.25);
    border-color: #10b981;
}

/* Danger Button */
QPushButton#danger {
    background-color: rgba(239, 68, 68, 0.15);
    color: #ef4444;
    border: 1px solid rgba(239, 68, 68, 0.3);
}

QPushButton#danger:hover {
    background-color: rgba(239, 68, 68, 0.25);
    border-color: #ef4444;
}

/* Ghost Button - Minimal */
QPushButton#ghost {
    background: transparent;
    border: none;
    color: #94a3b8;
    padding: 8px 12px;
}

QPushButton#ghost:hover {
    color: #f8fafc;
    background: rgba(255, 255, 255, 0.05);
}

/* Nav Button - Sidebar navigation */
QPushButton#navButton {
    background: transparent;
    border: none;
    border-radius: 12px;
    color: #94a3b8;
    padding: 14px 16px;
    text-align: left;
    font-weight: 500;
}

QPushButton#navButton:hover {
    background: rgba(139, 92, 246, 0.1);
    color: #f8fafc;
}

QPushButton#navButton:checked {
    background: rgba(139, 92, 246, 0.15);
    color: #8b5cf6;
    border-left: 3px solid #8b5cf6;
}

/* Icon Button - Round */
QPushButton#iconButton {
    background: #1a1a24;
    border: 1px solid #2d2d3d;
    border-radius: 12px;
    padding: 12px;
    min-width: 44px;
    max-width: 44px;
    min-height: 44px;
    max-height: 44px;
}

QPushButton#iconButton:hover {
    background: #242432;
    border-color: #8b5cf6;
}

/* Toggle Buttons */
QPushButton:checked {
    background: rgba(139, 92, 246, 0.15);
    border-color: #8b5cf6;
    color: #8b5cf6;
}

/* ========== INPUTS ========== */
QLineEdit {
    background-color: #16161e;
    border: 2px solid #2d2d3d;
    border-radius: 12px;
    color: #f8fafc;
    padding: 14px 16px;
    font-size: 14px;
}

QLineEdit:focus {
    border-color: #8b5cf6;
    background-color: #1a1a24;
}

QLineEdit:hover {
    border-color: #3d3d50;
}

QLineEdit::placeholder {
    color: #64748b;
}

QLineEdit#searchInput {
    background-color: #1a1a24;
    border-radius: 24px;
    padding-left: 44px;
}

QTextEdit {
    background-color: #16161e;
    border: 2px solid #2d2d3d;
    border-radius: 12px;
    color: #f8fafc;
    padding: 12px;
}

QTextEdit:focus {
    border-color: #8b5cf6;
}

QComboBox {
    background-color: #16161e;
    border: 2px solid #2d2d3d;
    border-radius: 12px;
    padding: 12px 16px;
    color: #f8fafc;
    font-size: 14px;
}

QComboBox:hover {
    border-color: #3d3d50;
}

QComboBox:focus {
    border-color: #8b5cf6;
}

QComboBox::drop-down {
    border: none;
    padding-right: 12px;
}

QComboBox QAbstractItemView {
    background-color: #1a1a24;
    border: 1px solid #2d2d3d;
    border-radius: 8px;
    selection-background-color: #8b5cf6;
    padding: 4px;
}

/* ========== PROGRESS BAR ========== */
QProgressBar {
    background-color: #16161e;
    border: none;
    border-radius: 8px;
    height: 8px;
    text-align: center;
}

QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #8b5cf6, stop:1 #06b6d4);
    border-radius: 8px;
}

/* ========== SCROLLBAR - Minimal ========== */
QScrollBar:vertical {
    background: transparent;
    width: 10px;
    margin: 4px;
}

QScrollBar::handle:vertical {
    background: #2d2d3d;
    border-radius: 5px;
    min-height: 40px;
}

QScrollBar::handle:vertical:hover {
    background: #3d3d50;
}

QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {
    height: 0px;
}

QScrollBar:horizontal {
    background: transparent;
    height: 10px;
    margin: 4px;
}

QScrollBar::handle:horizontal {
    background: #2d2d3d;
    border-radius: 5px;
    min-width: 40px;
}

/* ========== STATUS PILLS ========== */
QLabel#statusPill {
    background-color: #1a1a24;
    border: 1px solid #2d2d3d;
    border-radius: 16px;
    padding: 6px 14px;
    font-size: 12px;
    font-weight: 600;
}

QLabel#statusPillSuccess {
    background-color: rgba(16, 185, 129, 0.15);
    border: 1px solid rgba(16, 185, 129, 0.3);
    color: #10b981;
    border-radius: 16px;
    padding: 6px 14px;
    font-size: 12px;
    font-weight: 600;
}

QLabel#statusPillWarning {
    background-color: rgba(245, 158, 11, 0.15);
    border: 1px solid rgba(245, 158, 11, 0.3);
    color: #f59e0b;
    border-radius: 16px;
    padding: 6px 14px;
    font-size: 12px;
    font-weight: 600;
}

QLabel#statusPillDanger {
    background-color: rgba(239, 68, 68, 0.15);
    border: 1px solid rgba(239, 68, 68, 0.3);
    color: #ef4444;
    border-radius: 16px;
    padding: 6px 14px;
    font-size: 12px;
    font-weight: 600;
}

/* ========== TOOLTIPS ========== */
QToolTip {
    background-color: #1a1a24;
    border: 1px solid #2d2d3d;
    border-radius: 8px;
    color: #f8fafc;
    padding: 8px 12px;
    font-size: 13px;
}

/* ========== LIST WIDGETS ========== */
QListWidget {
    background-color: transparent;
    border: none;
    outline: none;
}

QListWidget::item {
    background-color: #1a1a24;
    border: 1px solid #2d2d3d;
    border-radius: 12px;
    padding: 16px;
    margin: 4px 0px;
}

QListWidget::item:hover {
    background-color: #242432;
    border-color: #3d3d50;
}

QListWidget::item:selected {
    background-color: rgba(139, 92, 246, 0.15);
    border-color: #8b5cf6;
}

/* ========== TABLE WIDGET ========== */
QTableWidget {
    background-color: #1a1a24;
    border: 1px solid #2d2d3d;
    border-radius: 12px;
    gridline-color: #2d2d3d;
}

QTableWidget::item {
    padding: 12px;
    border-bottom: 1px solid #1e1e2a;
}

QTableWidget::item:selected {
    background-color: rgba(139, 92, 246, 0.15);
}

QHeaderView::section {
    background-color: #12121a;
    color: #64748b;
    border: none;
    padding: 12px 16px;
    font-weight: 600;
    font-size: 12px;
    text-transform: uppercase;
    letter-spacing: 1px;
}

/* ========== MESSAGE BOX ========== */
QMessageBox {
    background-color: #1a1a24;
}

QMessageBox QLabel {
    color: #f8fafc;
}

QMessageBox QPushButton {
    min-width: 80px;
}

/* ========== ANIMATIONS HELPER CLASSES ========== */
QFrame#glowCard {
    background-color: #1a1a24;
    border: 2px solid #8b5cf6;
    border-radius: 16px;
}
"""

# ==================== ICONS (Emoji based for now) ====================
ICONS = {
    'camera_on': '📹',
    'camera_off': '🎥',
    'start': '▶️',
    'stop': '⏹️',
    'record': '⏺️',
    'train': '🧠',
    'save': '💾',
    'success': '✅',
    'error': '❌',
    'warning': '⚠️',
    'wave': '👋',
    'hand': '✋',
    'copy': '📋',
    'clear': '🗑️',
    'user': '👤',
    'logout': '🚪',
    'settings': '⚙️',
    'history': '📜',
    'dashboard': '📊',
    'home': '🏠',
    'live': '🔴',
    'profile': '👤',
    'email': '📧',
    'lock': '🔒',
    'eye': '👁️',
    'search': '🔍',
    'refresh': '🔄',
    'delete': '🗑️',
    'edit': '✏️',
    'info': 'ℹ️',
    'close': '✕',
    'menu': '☰',
    'back': '←',
    'forward': '→',
    'up': '↑',
    'down': '↓',
    'check': '✓',
    'star': '⭐',
    'fire': '🔥',
    'sparkle': '✨',
}

# ==================== ANIMATION HELPERS ====================
def get_fade_in_style():
    """Returns stylesheet for fade-in effect (use with QPropertyAnimation)"""
    return """
        QWidget {
            background-color: rgba(15, 15, 20, 0);
        }
    """

def get_glow_effect_style(color='#8b5cf6'):
    """Returns stylesheet with glow effect"""
    return f"""
        QFrame {{
            border: 2px solid {color};
            background-color: rgba(139, 92, 246, 0.05);
        }}
    """
