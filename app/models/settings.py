from datetime import datetime

from app import db


class AppSettings(db.Model):
    """Model for storing application settings in the database."""
    __tablename__ = 'app_settings'

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.Text)
    is_encrypted = db.Column(db.Boolean, default=False)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f'<AppSettings {self.key}>'

    @classmethod
    def get(cls, key, default=None):
        """Get a setting value by key."""
        setting = cls.query.filter_by(key=key).first()
        if setting:
            return setting.value
        return default

    @classmethod
    def set(cls, key, value, is_encrypted=False):
        """Set a setting value."""
        setting = cls.query.filter_by(key=key).first()
        if setting:
            setting.value = value
            setting.is_encrypted = is_encrypted
        else:
            setting = cls(key=key, value=value, is_encrypted=is_encrypted)
            db.session.add(setting)
        db.session.commit()
        return setting
