"""
SQLite Database Service
Local authentication and data storage using SQLite
"""
import os
import sqlite3
import hashlib
import secrets
import uuid
from typing import Optional, List, Dict, Any
from datetime import datetime
from contextlib import contextmanager

from config import BASE_DIR


# Database path
DB_PATH = os.path.join(BASE_DIR, "signlanguage.db")


class DatabaseService:
    """SQLite database service for users, authentication, and translations."""
    
    _instance: Optional['DatabaseService'] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._init_database()
    
    @contextmanager
    def _get_connection(self):
        """Get a database connection with context management."""
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def _init_database(self):
        """Initialize database tables."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Users table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    salt TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Sessions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    token TEXT UNIQUE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)
            
            # Translations table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS translations (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    sign_label TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    gesture_type TEXT DEFAULT 'static',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)
            
            # Create indexes
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_translations_user_id ON translations(user_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_translations_created_at ON translations(created_at DESC)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_token ON sessions(token)")
            
            print("✅ SQLite database initialized")
    
    @property
    def is_connected(self) -> bool:
        """Always connected for SQLite."""
        return True
    
    # ==================== PASSWORD HASHING ====================
    
    def _hash_password(self, password: str, salt: str = None) -> tuple:
        """Hash password with salt."""
        if salt is None:
            salt = secrets.token_hex(32)
        
        # Use PBKDF2 for secure password hashing
        password_hash = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            100000  # iterations
        ).hex()
        
        return password_hash, salt
    
    def _verify_password(self, password: str, password_hash: str, salt: str) -> bool:
        """Verify password against hash."""
        computed_hash, _ = self._hash_password(password, salt)
        return secrets.compare_digest(computed_hash, password_hash)
    
    # ==================== AUTH OPERATIONS ====================
    
    async def sign_up(self, email: str, password: str) -> Dict[str, Any]:
        """Register a new user."""
        try:
            email = email.lower().strip()
            
            # Validate format (relaxed to allow usernames)
            if not email:
                return {"error": "Username/Email required"}
            
            # Check password strength
            if len(password) < 6:
                return {"error": "Password must be at least 6 characters"}
            
            # Hash password
            password_hash, salt = self._hash_password(password)
            user_id = str(uuid.uuid4())
            
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Check if email already exists
                cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
                if cursor.fetchone():
                    return {"error": "Email already registered"}
                
                # Create user
                cursor.execute("""
                    INSERT INTO users (id, email, password_hash, salt)
                    VALUES (?, ?, ?, ?)
                """, (user_id, email, password_hash, salt))
            
            # Create session
            session = self._create_session(user_id)
            
            return {
                "success": True,
                "user": {
                    "id": user_id,
                    "email": email
                },
                "session": session
            }
        except sqlite3.IntegrityError:
            return {"error": "Email already registered"}
        except Exception as e:
            return {"error": str(e)}
    
    async def sign_in(self, email: str, password: str) -> Dict[str, Any]:
        """Sign in existing user."""
        try:
            email = email.lower().strip()
            
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Find user
                cursor.execute("""
                    SELECT id, email, password_hash, salt 
                    FROM users WHERE email = ?
                """, (email,))
                row = cursor.fetchone()
                
                if not row:
                    return {"error": "Invalid email or password"}
                
                # Verify password
                if not self._verify_password(password, row['password_hash'], row['salt']):
                    return {"error": "Invalid email or password"}
                
                user_id = row['id']
                user_email = row['email']
            
            # Create session
            session = self._create_session(user_id)
            
            return {
                "success": True,
                "user": {
                    "id": user_id,
                    "email": user_email
                },
                "session": session
            }
        except Exception as e:
            return {"error": str(e)}
    
    def _create_session(self, user_id: str) -> Dict[str, Any]:
        """Create a new session for user."""
        session_id = str(uuid.uuid4())
        token = secrets.token_urlsafe(32)
        expires_at = datetime.now().timestamp() + (7 * 24 * 60 * 60)  # 7 days
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO sessions (id, user_id, token, expires_at)
                VALUES (?, ?, ?, datetime(?, 'unixepoch'))
            """, (session_id, user_id, token, expires_at))
        
        return {
            "token": token,
            "expires_at": expires_at
        }
    
    async def sign_out(self, token: str = None) -> Dict[str, Any]:
        """Sign out current user (invalidate session)."""
        try:
            if token:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM sessions WHERE token = ?", (token,))
            return {"success": True}
        except Exception as e:
            return {"error": str(e)}
    
    def get_current_user(self, token: str = None) -> Optional[Dict[str, Any]]:
        """Get user from session token."""
        if not token:
            return None
        
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT u.id, u.email, u.created_at 
                    FROM users u
                    JOIN sessions s ON u.id = s.user_id
                    WHERE s.token = ? AND s.expires_at > datetime('now')
                """, (token,))
                row = cursor.fetchone()
                
                if row:
                    return {
                        "id": row['id'],
                        "email": row['email'],
                        "created_at": row['created_at']
                    }
                return None
        except Exception:
            return None
    
    # ==================== TRANSLATION OPERATIONS ====================
    
    async def save_translation(
        self, 
        user_id: str, 
        sign_label: str, 
        confidence: float,
        gesture_type: str = "static"
    ) -> Dict[str, Any]:
        """Save a translation to history."""
        try:
            translation_id = str(uuid.uuid4())
            
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO translations (id, user_id, sign_label, confidence, gesture_type)
                    VALUES (?, ?, ?, ?, ?)
                """, (translation_id, user_id, sign_label, confidence, gesture_type))
            
            return {"success": True, "id": translation_id}
        except Exception as e:
            return {"error": str(e)}
    
    async def get_translations(
        self, 
        user_id: str, 
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get user's translation history."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, sign_label, confidence, gesture_type, created_at
                    FROM translations
                    WHERE user_id = ?
                    ORDER BY created_at DESC
                    LIMIT ? OFFSET ?
                """, (user_id, limit, offset))
                
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        except Exception as e:
            print(f"Error fetching translations: {e}")
            return []
    
    async def get_translation_stats(self, user_id: str) -> Dict[str, Any]:
        """Get user's translation statistics."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Total count
                cursor.execute("""
                    SELECT COUNT(*) as total FROM translations WHERE user_id = ?
                """, (user_id,))
                total = cursor.fetchone()['total']
                
                # Today's count
                cursor.execute("""
                    SELECT COUNT(*) as today FROM translations 
                    WHERE user_id = ? AND date(created_at) = date('now')
                """, (user_id,))
                today = cursor.fetchone()['today']
                
                # Unique signs
                cursor.execute("""
                    SELECT COUNT(DISTINCT sign_label) as unique_signs 
                    FROM translations WHERE user_id = ?
                """, (user_id,))
                unique_signs = cursor.fetchone()['unique_signs']
                
                return {
                    "total": total,
                    "today": today,
                    "unique_signs": unique_signs
                }
        except Exception as e:
            print(f"Error getting stats: {e}")
            return {"total": 0, "today": 0, "unique_signs": 0}
    
    async def delete_translation(self, translation_id: str, user_id: str) -> Dict[str, Any]:
        """Delete a translation record."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    DELETE FROM translations 
                    WHERE id = ? AND user_id = ?
                """, (translation_id, user_id))
            return {"success": True}
        except Exception as e:
            return {"error": str(e)}
    
    async def clear_history(self, user_id: str) -> Dict[str, Any]:
        """Clear all translation history for a user."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM translations WHERE user_id = ?", (user_id,))
            return {"success": True}
        except Exception as e:
            return {"error": str(e)}


# Global instance
db = DatabaseService()
