import pytest
from tests.conftest import login_admin, login_child


class TestAuthRoutes:
    """Tests for authentication routes."""

    def test_login_page_loads(self, client):
        """Test login page is accessible."""
        response = client.get('/login')
        assert response.status_code == 200
        assert b'ChoreChamp' in response.data
        assert b"I'm a Kid" in response.data
        assert b"I'm a Parent" in response.data

    def test_child_login_success(self, client, child_user):
        """Test successful child login with PIN."""
        response = client.post('/login', data={
            'login_type': 'child',
            'user_id': child_user['id'],
            'pin': child_user['pin']
        }, follow_redirects=True)

        assert response.status_code == 200
        assert b'My Chores' in response.data or b'Dashboard' in response.data

    def test_child_login_wrong_pin(self, client, child_user):
        """Test child login with wrong PIN."""
        response = client.post('/login', data={
            'login_type': 'child',
            'user_id': child_user['id'],
            'pin': '0000'  # Wrong PIN
        }, follow_redirects=True)

        assert response.status_code == 200
        assert b'Invalid PIN' in response.data

    def test_admin_login_success(self, client, admin_user):
        """Test successful admin login with password."""
        response = client.post('/login', data={
            'login_type': 'adult',
            'email': admin_user['email'],
            'password': admin_user['password']
        }, follow_redirects=True)

        assert response.status_code == 200
        assert b'Admin' in response.data or b'Dashboard' in response.data

    def test_admin_login_wrong_password(self, client, admin_user):
        """Test admin login with wrong password."""
        response = client.post('/login', data={
            'login_type': 'adult',
            'email': admin_user['email'],
            'password': 'wrongpassword'
        }, follow_redirects=True)

        assert response.status_code == 200
        assert b'Invalid email or password' in response.data

    def test_logout(self, client, child_user):
        """Test logout functionality."""
        # Login first
        login_child(client, child_user)

        # Then logout - should redirect to login page
        response = client.get('/logout', follow_redirects=True)

        assert response.status_code == 200
        # Should be on login page
        assert b'Login' in response.data or b'ChoreChamp' in response.data

    def test_protected_route_requires_login(self, client):
        """Test that protected routes require authentication."""
        response = client.get('/dashboard', follow_redirects=True)

        assert response.status_code == 200
        assert b'log in' in response.data.lower() or b'login' in response.data.lower()
