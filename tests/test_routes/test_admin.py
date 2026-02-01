import pytest
from tests.conftest import login_admin, login_child


class TestAdminRoutes:
    """Tests for admin routes."""

    def test_admin_requires_admin_user(self, client, child_user):
        """Test that admin routes require admin privileges."""
        login_child(client, child_user)

        response = client.get('/admin/', follow_redirects=True)

        assert response.status_code == 200
        assert b'Admin access required' in response.data or b'login' in response.data.lower()

    def test_admin_dashboard_loads(self, client, admin_user):
        """Test admin dashboard loads for admin user."""
        login_admin(client, admin_user)

        response = client.get('/admin/')

        assert response.status_code == 200
        assert b'Admin Dashboard' in response.data

    def test_admin_chores_page_loads(self, client, admin_user):
        """Test chores management page loads."""
        login_admin(client, admin_user)

        response = client.get('/admin/chores')

        assert response.status_code == 200
        assert b'Manage Preset Chores' in response.data

    def test_create_chore(self, client, admin_user):
        """Test creating a new chore."""
        login_admin(client, admin_user)

        response = client.post('/admin/chores', data={
            'name': 'New Test Chore',
            'amount': 2.50,
            'frequency': 'daily',
            'times_per_day': 1,
            'description': 'A test chore'
        }, follow_redirects=True)

        assert response.status_code == 200
        assert b'created successfully' in response.data or b'New Test Chore' in response.data

    def test_admin_users_page_loads(self, client, admin_user):
        """Test users management page loads."""
        login_admin(client, admin_user)

        response = client.get('/admin/users')

        assert response.status_code == 200
        assert b'Manage Users' in response.data

    def test_create_child_user(self, client, admin_user):
        """Test creating a new child user."""
        login_admin(client, admin_user)

        response = client.post('/admin/users', data={
            'name': 'New Child',
            'is_admin': '',  # Not checked = child
            'pin': '9999',
            'base_allowance': 5.00
        }, follow_redirects=True)

        assert response.status_code == 200
        assert b'created successfully' in response.data or b'New Child' in response.data

    def test_mark_payment(self, client, admin_user, child_user, current_week, assigned_chores):
        """Test marking a payment as paid."""
        login_admin(client, admin_user)

        response = client.post(
            f"/admin/weeks/{current_week['id']}/pay/{child_user['id']}",
            follow_redirects=True
        )

        assert response.status_code == 200
        assert b'marked as paid' in response.data or b'Paid' in response.data

    def test_payments_page_loads(self, client, admin_user):
        """Test payments history page loads."""
        login_admin(client, admin_user)

        response = client.get('/admin/payments')

        assert response.status_code == 200
        assert b'Payment History' in response.data

    def test_create_adhoc_chore(self, client, admin_user, child_user, current_week):
        """Test creating an ad-hoc chore."""
        login_admin(client, admin_user)

        response = client.post(f"/admin/weeks/{current_week['id']}/adhoc", data={
            'user_id': child_user['id'],
            'name': 'Help with Garden',
            'amount': 5.00
        }, follow_redirects=True)

        assert response.status_code == 200
        assert b'assigned successfully' in response.data or b'Help with Garden' in response.data
