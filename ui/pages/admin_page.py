"""
Admin Page
Built-in dashboard for the 'admin' user to manage the application.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFrame, QTableWidget, QTableWidgetItem,
    QHeaderView, QTabWidget, QMessageBox, QTextEdit, QLineEdit, QDialog, QFormLayout
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QColor

from ui.styles import COLORS

class AdminPage(QWidget):
    """Admin dashboard widget."""
    
    def __init__(self, db_service=None, parent=None):
        super().__init__(parent)
        self.db = db_service
        self._setup_ui()
        
    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(40, 40, 40, 40)
        main_layout.setSpacing(20)
        
        # Header
        header = QHBoxLayout()
        title = QLabel("🛡️ Admin Dashboard")
        title.setStyleSheet(f"font-size: 24px; font-weight: 700; color: {COLORS['primary']};")
        
        refresh_btn = QPushButton("🔄 Refresh Data")
        refresh_btn.clicked.connect(self.refresh_all)
        
        header.addWidget(title)
        header.addStretch()
        header.addWidget(refresh_btn)
        main_layout.addLayout(header)
        
        # Tabs
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #2d2d3d; background: #1a1a24; border-radius: 8px; }
            QTabBar::tab { background: #1a1a24; color: #94a3b8; padding: 10px 20px; border-top-left-radius: 8px; border-top-right-radius: 8px; }
            QTabBar::tab:selected { background: #2d2d3d; color: white; border-bottom: 2px solid #8b5cf6; }
        """)
        
        self.users_tab = QWidget()
        self._setup_users_tab()
        
        self.trans_tab = QWidget()
        self._setup_trans_tab()
        
        self.tabs.addTab(self.users_tab, "👥 Users")
        self.tabs.addTab(self.trans_tab, "📜 Translations")
        
        main_layout.addWidget(self.tabs)
        
    def _setup_users_tab(self):
        layout = QVBoxLayout(self.users_tab)
        
        # Actions
        actions = QHBoxLayout()
        del_btn = QPushButton("🗑️ Delete User")
        del_btn.setObjectName("danger")
        del_btn.clicked.connect(self._delete_user)
        actions.addWidget(del_btn)
        actions.addStretch()
        layout.addLayout(actions)
        
        # Table
        self.users_table = QTableWidget()
        self.users_table.setColumnCount(3)
        self.users_table.setHorizontalHeaderLabels(["ID", "Email", "Created At"])
        self.users_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.users_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.users_table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.users_table)
        
    def _setup_trans_tab(self):
        layout = QVBoxLayout(self.trans_tab)
        
        # Actions
        actions = QHBoxLayout()
        del_btn = QPushButton("🗑️ Delete Translation")
        del_btn.setObjectName("danger")
        del_btn.clicked.connect(self._delete_translation)
        actions.addWidget(del_btn)
        actions.addStretch()
        layout.addLayout(actions)
        
        # Table
        self.trans_table = QTableWidget()
        self.trans_table.setColumnCount(5)
        self.trans_table.setHorizontalHeaderLabels(["Sign", "Conf", "Type", "User Email", "Time"])
        self.trans_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.trans_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.trans_table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.trans_table)
        
    def refresh_all(self):
        """Reload all data."""
        if not self.db: return
        
        # Load Users
        try:
            with self.db._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, email, created_at FROM users ORDER BY created_at DESC")
                rows = cursor.fetchall()
                
                self.users_table.setRowCount(len(rows))
                for i, row in enumerate(rows):
                    self.users_table.setItem(i, 0, QTableWidgetItem(str(row['id'])))
                    self.users_table.setItem(i, 1, QTableWidgetItem(str(row['email'])))
                    self.users_table.setItem(i, 2, QTableWidgetItem(str(row['created_at'])))
                    
                # Load Translations
                cursor.execute("""
                    SELECT t.id, t.sign_label, t.confidence, t.gesture_type, u.email, t.created_at 
                    FROM translations t
                    JOIN users u ON t.user_id = u.id
                    ORDER BY t.created_at DESC LIMIT 100
                """)
                t_rows = cursor.fetchall()
                self.trans_table.setRowCount(len(t_rows))
                for i, row in enumerate(t_rows):
                    # Store ID in user role for deletion
                    item = QTableWidgetItem(str(row['sign_label']))
                    item.setData(Qt.UserRole, row['id'])
                    self.trans_table.setItem(i, 0, item)
                    
                    self.trans_table.setItem(i, 1, QTableWidgetItem(f"{row['confidence']*100:.1f}%"))
                    self.trans_table.setItem(i, 2, QTableWidgetItem(str(row['gesture_type'])))
                    self.trans_table.setItem(i, 3, QTableWidgetItem(str(row['email'])))
                    self.trans_table.setItem(i, 4, QTableWidgetItem(str(row['created_at'])))
                    
        except Exception as e:
            print(f"Admin load error: {e}")
            
    def _delete_user(self):
        rows = self.users_table.selectionModel().selectedRows()
        if not rows: return
        
        email = self.users_table.item(rows[0].row(), 1).text()
        if email == "admin":
            QMessageBox.warning(self, "Error", "Cannot delete admin user!")
            return
            
        if QMessageBox.question(self, "Confirm", f"Delete user {email}?") == QMessageBox.Yes:
            user_id = self.users_table.item(rows[0].row(), 0).text()
            try:
                with self.db._get_connection() as conn:
                    conn.execute("DELETE FROM users WHERE id=?", (user_id,))
                self.refresh_all()
            except Exception as e:
                QMessageBox.warning(self, "Error", str(e))

    def _delete_translation(self):
        rows = self.trans_table.selectionModel().selectedRows()
        if not rows: return
        
        if QMessageBox.question(self, "Confirm", "Delete selected translation?") == QMessageBox.Yes:
            tid = self.trans_table.item(rows[0].row(), 0).data(Qt.UserRole)
            try:
                with self.db._get_connection() as conn:
                    conn.execute("DELETE FROM translations WHERE id=?", (tid,))
                self.refresh_all()
            except Exception as e:
                QMessageBox.warning(self, "Error", str(e))
