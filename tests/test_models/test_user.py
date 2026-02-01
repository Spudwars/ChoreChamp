import pytest
from app import db
from app.models.user import User


class TestUserModel:
    """Tests for User model."""

    def test_create_child_user(self, app):
        """Test creating a child user with PIN."""
        with app.app_context():
            user = User(name='Emma', is_admin=False, base_allowance=5.00)
            user.set_pin('1234')
            db.session.add(user)
            db.session.commit()

            assert user.id is not None
            assert user.name == 'Emma'
            assert user.is_admin is False
            assert user.is_child is True
            assert user.base_allowance == 5.00
            assert user.check_pin('1234') is True
            assert user.check_pin('0000') is False

    def test_create_admin_user(self, app):
        """Test creating an admin user with password."""
        with app.app_context():
            user = User(name='Parent', email='parent@test.com', is_admin=True)
            user.set_password('securepass123')
            db.session.add(user)
            db.session.commit()

            assert user.id is not None
            assert user.is_admin is True
            assert user.is_child is False
            assert user.check_password('securepass123') is True
            assert user.check_password('wrongpass') is False

    def test_pin_validation(self, app):
        """Test PIN validation rules."""
        with app.app_context():
            user = User(name='Test', is_admin=False)

            # PIN must be 4 digits
            with pytest.raises(ValueError):
                user.set_pin('123')  # Too short

            with pytest.raises(ValueError):
                user.set_pin('12345')  # Too long

            with pytest.raises(ValueError):
                user.set_pin('abcd')  # Not digits

            # Valid PIN
            user.set_pin('0000')
            assert user.check_pin('0000') is True

    def test_password_validation(self, app):
        """Test password validation rules."""
        with app.app_context():
            user = User(name='Test', is_admin=True)

            # Password must be at least 6 characters
            with pytest.raises(ValueError):
                user.set_password('12345')  # Too short

            # Valid password
            user.set_password('123456')
            assert user.check_password('123456') is True

    def test_user_repr(self, app):
        """Test user string representation."""
        with app.app_context():
            child = User(name='Emma', is_admin=False)
            admin = User(name='Parent', is_admin=True)

            assert 'Emma' in repr(child)
            assert 'Child' in repr(child)
            assert 'Parent' in repr(admin)
            assert 'Admin' in repr(admin)
