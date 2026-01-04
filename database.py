"""
Database Models for User Authentication & Investment Tracking
==============================================================
SQLite database with User, Portfolio, Investment, and Alert models.
"""

import sqlite3
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import json


class Database:
    """Database handler for user authentication and portfolio management."""
    
    def __init__(self, db_path: str = "market_alerts.db"):
        """Initialize database connection."""
        self.db_path = db_path
        self.init_database()
    
    def get_connection(self):
        """Get database connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_database(self):
        """Create database tables if they don't exist."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                full_name TEXT,
                phone TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                is_active BOOLEAN DEFAULT 1,
                alert_preferences TEXT DEFAULT '{}',
                investment_limit REAL DEFAULT 0
            )
        ''')
        
        # JWT tokens table (for token blacklist/refresh)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tokens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                token TEXT UNIQUE NOT NULL,
                expires_at TIMESTAMP NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_revoked BOOLEAN DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        # Portfolios table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS portfolios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                portfolio_name TEXT NOT NULL,
                total_value REAL DEFAULT 0,
                available_cash REAL DEFAULT 0,
                invested_amount REAL DEFAULT 0,
                profit_loss REAL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        # Investments table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS investments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                portfolio_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                stock_symbol TEXT NOT NULL,
                quantity REAL NOT NULL,
                buy_price REAL NOT NULL,
                current_price REAL,
                buy_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'active',
                profit_loss REAL DEFAULT 0,
                notes TEXT,
                FOREIGN KEY (portfolio_id) REFERENCES portfolios(id),
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        # User alerts table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                stock_symbol TEXT NOT NULL,
                alert_type TEXT NOT NULL,
                alert_message TEXT NOT NULL,
                severity TEXT DEFAULT 'medium',
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                acknowledged_at TIMESTAMP,
                user_response TEXT,
                metadata TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        # Alert preferences table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS alert_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                stock_symbol TEXT,
                alert_types TEXT NOT NULL,
                threshold_price_drop REAL DEFAULT 4.0,
                threshold_price_spike REAL DEFAULT 5.0,
                threshold_volatility REAL DEFAULT 0.03,
                notify_email BOOLEAN DEFAULT 1,
                notify_sms BOOLEAN DEFAULT 0,
                require_confirmation BOOLEAN DEFAULT 1,
                is_active BOOLEAN DEFAULT 1,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        # Transaction history
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                portfolio_id INTEGER NOT NULL,
                transaction_type TEXT NOT NULL,
                stock_symbol TEXT,
                quantity REAL,
                price REAL,
                amount REAL NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                description TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (portfolio_id) REFERENCES portfolios(id)
            )
        ''')
        
        conn.commit()
        conn.close()
        print("✅ Database initialized successfully")
    
    # ==================== USER MANAGEMENT ====================
    
    def hash_password(self, password: str) -> str:
        """Hash password using SHA-256."""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def create_user(self, username: str, email: str, password: str, 
                   full_name: str = None, phone: str = None) -> Optional[int]:
        """Create new user account."""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            password_hash = self.hash_password(password)
            
            cursor.execute('''
                INSERT INTO users (username, email, password_hash, full_name, phone)
                VALUES (?, ?, ?, ?, ?)
            ''', (username, email, password_hash, full_name, phone))
            
            user_id = cursor.lastrowid
            
            # Create default portfolio
            cursor.execute('''
                INSERT INTO portfolios (user_id, portfolio_name, available_cash)
                VALUES (?, ?, ?)
            ''', (user_id, "My Portfolio", 10000.0))
            
            # Create default alert settings
            cursor.execute('''
                INSERT INTO alert_settings (user_id, alert_types)
                VALUES (?, ?)
            ''', (user_id, json.dumps(['price_drop', 'price_spike', 'volatility_spike'])))
            
            conn.commit()
            conn.close()
            
            return user_id
        except sqlite3.IntegrityError as e:
            print(f"Error creating user: {e}")
            return None
    
    def authenticate_user(self, username: str, password: str) -> Optional[Dict]:
        """Authenticate user and return user data."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        password_hash = self.hash_password(password)
        
        cursor.execute('''
            SELECT id, username, email, full_name, phone, created_at, 
                   alert_preferences, investment_limit
            FROM users
            WHERE username = ? AND password_hash = ? AND is_active = 1
        ''', (username, password_hash))
        
        user = cursor.fetchone()
        
        if user:
            # Update last login
            cursor.execute('''
                UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?
            ''', (user['id'],))
            conn.commit()
            
            user_dict = dict(user)
            conn.close()
            return user_dict
        
        conn.close()
        return None
    
    def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        """Get user by ID."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, username, email, full_name, phone, created_at, 
                   last_login, alert_preferences, investment_limit
            FROM users WHERE id = ? AND is_active = 1
        ''', (user_id,))
        
        user = cursor.fetchone()
        conn.close()
        
        return dict(user) if user else None
    
    def update_user_profile(self, user_id: int, **kwargs) -> bool:
        """Update user profile."""
        allowed_fields = ['full_name', 'phone', 'alert_preferences', 'investment_limit']
        updates = {k: v for k, v in kwargs.items() if k in allowed_fields}
        
        if not updates:
            return False
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        set_clause = ", ".join([f"{k} = ?" for k in updates.keys()])
        values = list(updates.values()) + [user_id]
        
        cursor.execute(f'''
            UPDATE users SET {set_clause} WHERE id = ?
        ''', values)
        
        conn.commit()
        conn.close()
        return True
    
    # ==================== TOKEN MANAGEMENT ====================
    
    def save_token(self, user_id: int, token: str, expires_in_hours: int = 24) -> bool:
        """Save JWT token to database."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        expires_at = datetime.now() + timedelta(hours=expires_in_hours)
        
        cursor.execute('''
            INSERT INTO tokens (user_id, token, expires_at)
            VALUES (?, ?, ?)
        ''', (user_id, token, expires_at))
        
        conn.commit()
        conn.close()
        return True
    
    def is_token_valid(self, token: str) -> bool:
        """Check if token is valid and not revoked."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id FROM tokens
            WHERE token = ? AND expires_at > CURRENT_TIMESTAMP AND is_revoked = 0
        ''', (token,))
        
        result = cursor.fetchone()
        conn.close()
        return result is not None
    
    def revoke_token(self, token: str) -> bool:
        """Revoke a token."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE tokens SET is_revoked = 1 WHERE token = ?
        ''', (token,))
        
        conn.commit()
        conn.close()
        return True
    
    # ==================== PORTFOLIO MANAGEMENT ====================
    
    def get_user_portfolio(self, user_id: int) -> Optional[Dict]:
        """Get user's portfolio."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM portfolios WHERE user_id = ? ORDER BY id DESC LIMIT 1
        ''', (user_id,))
        
        portfolio = cursor.fetchone()
        conn.close()
        
        return dict(portfolio) if portfolio else None
    
    def get_user_investments(self, user_id: int, status: str = 'active') -> List[Dict]:
        """Get user's investments."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM investments
            WHERE user_id = ? AND status = ?
            ORDER BY buy_date DESC
        ''', (user_id, status))
        
        investments = cursor.fetchall()
        conn.close()
        
        return [dict(inv) for inv in investments]
    
    def create_investment(self, user_id: int, portfolio_id: int, 
                         stock_symbol: str, quantity: float, 
                         buy_price: float, notes: str = None) -> Optional[int]:
        """Create new investment."""
        total_cost = quantity * buy_price
        
        # Check available cash
        portfolio = self.get_user_portfolio(user_id)
        if not portfolio or portfolio['available_cash'] < total_cost:
            return None
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Create investment
        cursor.execute('''
            INSERT INTO investments 
            (portfolio_id, user_id, stock_symbol, quantity, buy_price, current_price, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (portfolio_id, user_id, stock_symbol, quantity, buy_price, buy_price, notes))
        
        investment_id = cursor.lastrowid
        
        # Update portfolio
        cursor.execute('''
            UPDATE portfolios
            SET available_cash = available_cash - ?,
                invested_amount = invested_amount + ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (total_cost, total_cost, portfolio_id))
        
        # Record transaction
        cursor.execute('''
            INSERT INTO transactions
            (user_id, portfolio_id, transaction_type, stock_symbol, quantity, price, amount, description)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, portfolio_id, 'BUY', stock_symbol, quantity, buy_price, total_cost, 
              f'Bought {quantity} shares of {stock_symbol}'))
        
        conn.commit()
        conn.close()
        
        return investment_id
    
    def update_investment_price(self, investment_id: int, current_price: float) -> bool:
        """Update current price and P/L for investment."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE investments
            SET current_price = ?,
                profit_loss = (current_price - buy_price) * quantity
            WHERE id = ?
        ''', (current_price, investment_id))
        
        conn.commit()
        conn.close()
        return True
    
    # ==================== ALERT MANAGEMENT ====================
    
    def create_alert(self, user_id: int, stock_symbol: str, alert_type: str,
                    alert_message: str, severity: str = 'medium', 
                    metadata: Dict = None) -> int:
        """Create new alert for user."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO user_alerts
            (user_id, stock_symbol, alert_type, alert_message, severity, metadata)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, stock_symbol, alert_type, alert_message, severity, 
              json.dumps(metadata) if metadata else None))
        
        alert_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return alert_id
    
    def get_user_alerts(self, user_id: int, status: str = 'pending', 
                       limit: int = 50) -> List[Dict]:
        """Get user's alerts."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if status:
            cursor.execute('''
                SELECT * FROM user_alerts
                WHERE user_id = ? AND status = ?
                ORDER BY created_at DESC LIMIT ?
            ''', (user_id, status, limit))
        else:
            cursor.execute('''
                SELECT * FROM user_alerts
                WHERE user_id = ?
                ORDER BY created_at DESC LIMIT ?
            ''', (user_id, limit))
        
        alerts = cursor.fetchall()
        conn.close()
        
        return [dict(alert) for alert in alerts]
    
    def acknowledge_alert(self, alert_id: int, user_response: str = None) -> bool:
        """Mark alert as acknowledged."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE user_alerts
            SET status = 'acknowledged',
                acknowledged_at = CURRENT_TIMESTAMP,
                user_response = ?
            WHERE id = ?
        ''', (user_response, alert_id))
        
        conn.commit()
        conn.close()
        return True
    
    def get_alert_settings(self, user_id: int, stock_symbol: str = None) -> Optional[Dict]:
        """Get user's alert settings."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if stock_symbol:
            cursor.execute('''
                SELECT * FROM alert_settings
                WHERE user_id = ? AND (stock_symbol = ? OR stock_symbol IS NULL)
                ORDER BY stock_symbol DESC LIMIT 1
            ''', (user_id, stock_symbol))
        else:
            cursor.execute('''
                SELECT * FROM alert_settings
                WHERE user_id = ? AND stock_symbol IS NULL
                LIMIT 1
            ''', (user_id,))
        
        settings = cursor.fetchone()
        conn.close()
        
        return dict(settings) if settings else None
    
    def update_alert_settings(self, user_id: int, **kwargs) -> bool:
        """Update alert settings."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Check if settings exist
        cursor.execute('SELECT id FROM alert_settings WHERE user_id = ? AND stock_symbol IS NULL', (user_id,))
        existing = cursor.fetchone()
        
        if existing:
            allowed_fields = ['alert_types', 'threshold_price_drop', 'threshold_price_spike',
                            'threshold_volatility', 'notify_email', 'notify_sms', 
                            'require_confirmation', 'is_active']
            updates = {k: v for k, v in kwargs.items() if k in allowed_fields}
            
            if updates:
                set_clause = ", ".join([f"{k} = ?" for k in updates.keys()])
                values = list(updates.values()) + [user_id]
                
                cursor.execute(f'''
                    UPDATE alert_settings SET {set_clause}
                    WHERE user_id = ? AND stock_symbol IS NULL
                ''', values)
        
        conn.commit()
        conn.close()
        return True
    
    def get_transactions(self, user_id: int, limit: int = 100) -> List[Dict]:
        """Get user's transaction history."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM transactions
            WHERE user_id = ?
            ORDER BY timestamp DESC LIMIT ?
        ''', (user_id, limit))
        
        transactions = cursor.fetchall()
        conn.close()
        
        return [dict(txn) for txn in transactions]


if __name__ == "__main__":
    # Initialize database
    db = Database()
    
    # Test user creation
    print("\n🧪 Testing Database...")
    user_id = db.create_user(
        username="demo_user",
        email="demo@example.com",
        password="demo123",
        full_name="Demo User",
        phone="+1234567890"
    )
    
    if user_id:
        print(f"✅ User created with ID: {user_id}")
        
        # Test authentication
        user = db.authenticate_user("demo_user", "demo123")
        if user:
            print(f"✅ Authentication successful: {user['username']}")
        
        # Test portfolio
        portfolio = db.get_user_portfolio(user_id)
        if portfolio:
            print(f"✅ Portfolio created: ${portfolio['available_cash']} available")
    
    print("\n✅ Database ready!")
