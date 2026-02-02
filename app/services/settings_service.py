import os
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from app.models.settings import AppSettings


class SettingsService:
    """Service for managing application settings with optional encryption."""

    # Email setting keys
    EMAIL_SETTINGS = [
        'MAIL_SERVER',
        'MAIL_PORT',
        'MAIL_USE_TLS',
        'MAIL_USERNAME',
        'MAIL_PASSWORD',
        'MAIL_DEFAULT_SENDER',
    ]

    def __init__(self):
        self._fernet = None

    @property
    def fernet(self):
        """Get or create Fernet cipher for encryption/decryption."""
        if self._fernet is None:
            # Get encryption key from environment or generate from secret key
            encryption_key = os.environ.get('SETTINGS_ENCRYPTION_KEY')
            if not encryption_key:
                # Derive key from SECRET_KEY
                secret_key = os.environ.get('SECRET_KEY', 'default-secret-key').encode()
                salt = b'chorechamp-settings-salt'
                kdf = PBKDF2HMAC(
                    algorithm=hashes.SHA256(),
                    length=32,
                    salt=salt,
                    iterations=100000,
                )
                key = base64.urlsafe_b64encode(kdf.derive(secret_key))
            else:
                key = encryption_key.encode()
            self._fernet = Fernet(key)
        return self._fernet

    def encrypt(self, value):
        """Encrypt a string value."""
        if not value:
            return value
        return self.fernet.encrypt(value.encode()).decode()

    def decrypt(self, value):
        """Decrypt an encrypted value."""
        if not value:
            return value
        try:
            return self.fernet.decrypt(value.encode()).decode()
        except Exception:
            return value  # Return as-is if decryption fails

    def get_setting(self, key, default=None):
        """Get a setting value, decrypting if necessary."""
        setting = AppSettings.query.filter_by(key=key).first()
        if setting:
            if setting.is_encrypted:
                return self.decrypt(setting.value)
            return setting.value
        return default

    def set_setting(self, key, value, encrypt=False):
        """Set a setting value, encrypting if specified."""
        if encrypt and value:
            stored_value = self.encrypt(value)
        else:
            stored_value = value
        AppSettings.set(key, stored_value, is_encrypted=encrypt)

    def get_email_settings(self):
        """Get all email settings as a dictionary."""
        settings = {}
        for key in self.EMAIL_SETTINGS:
            settings[key] = self.get_setting(key)
        return settings

    def save_email_settings(self, settings_dict):
        """Save email settings from a dictionary."""
        for key in self.EMAIL_SETTINGS:
            if key in settings_dict:
                value = settings_dict[key]
                # Encrypt password
                encrypt = key == 'MAIL_PASSWORD'
                # Skip empty password updates (keep existing)
                if key == 'MAIL_PASSWORD' and not value:
                    continue
                self.set_setting(key, value, encrypt=encrypt)

    def get_mail_config(self):
        """
        Get mail configuration for Flask-Mail.
        Falls back to environment variables if not set in DB.
        """
        config = {}
        db_settings = self.get_email_settings()

        # MAIL_SERVER
        config['MAIL_SERVER'] = db_settings.get('MAIL_SERVER') or os.environ.get('MAIL_SERVER', 'localhost')

        # MAIL_PORT
        port = db_settings.get('MAIL_PORT') or os.environ.get('MAIL_PORT', '587')
        config['MAIL_PORT'] = int(port) if port else 587

        # MAIL_USE_TLS
        tls = db_settings.get('MAIL_USE_TLS')
        if tls is not None:
            config['MAIL_USE_TLS'] = tls.lower() in ('true', '1', 'yes')
        else:
            config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'True').lower() in ('true', '1', 'yes')

        # MAIL_USERNAME
        config['MAIL_USERNAME'] = db_settings.get('MAIL_USERNAME') or os.environ.get('MAIL_USERNAME')

        # MAIL_PASSWORD
        config['MAIL_PASSWORD'] = db_settings.get('MAIL_PASSWORD') or os.environ.get('MAIL_PASSWORD')

        # MAIL_DEFAULT_SENDER
        config['MAIL_DEFAULT_SENDER'] = db_settings.get('MAIL_DEFAULT_SENDER') or os.environ.get('MAIL_DEFAULT_SENDER')

        return config
