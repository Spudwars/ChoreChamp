from datetime import datetime
from flask_login import UserMixin
import bcrypt

from app import db


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)

    # Authentication - children use PIN, adults use password
    pin_hash = db.Column(db.String(128), nullable=True)
    password_hash = db.Column(db.String(128), nullable=True)

    # Account status
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    # Allowance settings (for children)
    base_allowance = db.Column(db.Float, default=0.0, nullable=False)

    # Avatar settings (DiceBear)
    avatar_style = db.Column(db.String(50), default='bottts')
    avatar_seed = db.Column(db.String(100))

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    chore_logs = db.relationship('ChoreLog', backref='user', lazy='dynamic')
    payments = db.relationship('WeeklyPayment', backref='user', lazy='dynamic')

    def set_pin(self, pin):
        """Set PIN for child authentication (4 digits)."""
        if not pin or len(pin) != 4 or not pin.isdigit():
            raise ValueError("PIN must be exactly 4 digits")
        self.pin_hash = bcrypt.hashpw(pin.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def check_pin(self, pin):
        """Verify PIN for child authentication."""
        if not self.pin_hash or not pin:
            return False
        return bcrypt.checkpw(pin.encode('utf-8'), self.pin_hash.encode('utf-8'))

    def set_password(self, password):
        """Set password for adult authentication."""
        if not password or len(password) < 6:
            raise ValueError("Password must be at least 6 characters")
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def check_password(self, password):
        """Verify password for adult authentication."""
        if not self.password_hash or not password:
            return False
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))

    @property
    def is_child(self):
        """Check if user is a child (non-admin)."""
        return not self.is_admin

    @property
    def avatar_url(self):
        """Get DiceBear avatar URL."""
        style = self.avatar_style or 'bottts'
        seed = self.avatar_seed or self.name
        return f"https://api.dicebear.com/7.x/{style}/svg?seed={seed}"

    def __repr__(self):
        role = "Admin" if self.is_admin else "Child"
        return f'<User {self.name} ({role})>'
