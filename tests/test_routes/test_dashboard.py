import pytest
from tests.conftest import login_child


class TestDashboardRoutes:
    """Tests for dashboard routes."""

    def test_dashboard_loads(self, client, child_user, sample_chores):
        """Test dashboard page loads for authenticated user."""
        login_child(client, child_user)

        response = client.get('/dashboard')

        assert response.status_code == 200
        assert b'My Chores' in response.data

    def test_dashboard_shows_week(self, client, child_user, sample_chores, current_week):
        """Test dashboard shows current week."""
        login_child(client, child_user)

        response = client.get('/dashboard')

        assert response.status_code == 200
        # Check for day abbreviations
        assert b'Mon' in response.data or b'Tue' in response.data

    def test_dashboard_shows_chores(self, client, child_user, assigned_chores):
        """Test dashboard shows assigned chores."""
        login_child(client, child_user)

        response = client.get('/dashboard')

        assert response.status_code == 200
        assert b'Brush Teeth' in response.data or b'Make Bed' in response.data

    def test_dashboard_shows_weekly_summary(self, client, child_user, assigned_chores):
        """Test dashboard shows weekly summary."""
        login_child(client, child_user)

        response = client.get('/dashboard')

        assert response.status_code == 200
        # Check for base allowance display
        assert b'3.00' in response.data or b'Base' in response.data

    def test_toggle_chore_completion(self, client, child_user, assigned_chores, current_week, app):
        """Test toggling chore completion via HTMX."""
        login_child(client, child_user)

        from datetime import date
        today = date.today().isoformat()

        response = client.post('/chores/toggle', data={
            'assignment_id': assigned_chores[1]['id'],  # Make Bed
            'date': today,
            'slot': 1
        })

        assert response.status_code == 200
        # Response should contain updated summary HTML

    def test_weekly_summary_endpoint(self, client, child_user, assigned_chores):
        """Test weekly summary HTMX endpoint."""
        login_child(client, child_user)

        response = client.get('/weekly-summary')

        assert response.status_code == 200
