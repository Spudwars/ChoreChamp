import pytest
import json


class TestAPIRoutes:
    """Tests for REST API routes."""

    def test_api_login_child(self, client, child_user):
        """Test API login for child user."""
        response = client.post('/api/v1/auth/login',
            data=json.dumps({
                'type': 'pin',
                'user_id': child_user['id'],
                'pin': child_user['pin']
            }),
            content_type='application/json'
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'access_token' in data
        assert data['user']['name'] == child_user['name']

    def test_api_login_admin(self, client, admin_user):
        """Test API login for admin user."""
        response = client.post('/api/v1/auth/login',
            data=json.dumps({
                'type': 'password',
                'email': admin_user['email'],
                'password': admin_user['password']
            }),
            content_type='application/json'
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'access_token' in data
        assert data['user']['is_admin'] is True

    def test_api_login_invalid_credentials(self, client, child_user):
        """Test API login with invalid credentials."""
        response = client.post('/api/v1/auth/login',
            data=json.dumps({
                'type': 'pin',
                'user_id': child_user['id'],
                'pin': '0000'  # Wrong PIN
            }),
            content_type='application/json'
        )

        assert response.status_code == 401

    def test_api_current_week_requires_auth(self, client):
        """Test that current week endpoint requires authentication."""
        response = client.get('/api/v1/weeks/current')

        assert response.status_code == 401

    def test_api_current_week(self, client, child_user, assigned_chores):
        """Test getting current week data."""
        # Login first
        login_response = client.post('/api/v1/auth/login',
            data=json.dumps({
                'type': 'pin',
                'user_id': child_user['id'],
                'pin': child_user['pin']
            }),
            content_type='application/json'
        )
        token = json.loads(login_response.data)['access_token']

        # Get current week
        response = client.get('/api/v1/weeks/current',
            headers={'Authorization': f'Bearer {token}'}
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'week' in data
        assert 'chores' in data
        assert 'summary' in data

    def test_api_complete_chore(self, client, child_user, assigned_chores, current_week):
        """Test completing a chore via API."""
        # Login first
        login_response = client.post('/api/v1/auth/login',
            data=json.dumps({
                'type': 'pin',
                'user_id': child_user['id'],
                'pin': child_user['pin']
            }),
            content_type='application/json'
        )
        token = json.loads(login_response.data)['access_token']

        # Complete a chore
        from datetime import date
        chore_id = assigned_chores[1]['chore_id']  # Make Bed

        response = client.post(f'/api/v1/chores/{chore_id}/complete',
            data=json.dumps({
                'date': date.today().isoformat(),
                'slot': 1
            }),
            content_type='application/json',
            headers={'Authorization': f'Bearer {token}'}
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['is_completed'] is True

    def test_api_list_users(self, client, admin_user, child_user):
        """Test listing users via API."""
        # Login as admin
        login_response = client.post('/api/v1/auth/login',
            data=json.dumps({
                'type': 'password',
                'email': admin_user['email'],
                'password': admin_user['password']
            }),
            content_type='application/json'
        )
        token = json.loads(login_response.data)['access_token']

        # Get users
        response = client.get('/api/v1/users',
            headers={'Authorization': f'Bearer {token}'}
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'users' in data
        # Should only list children
        user_names = [u['name'] for u in data['users']]
        assert child_user['name'] in user_names
