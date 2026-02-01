import pytest
from unittest.mock import patch, MagicMock

from app import db
from app.models.user import User
from app.services.email_service import EmailService


class TestEmailService:
    """Tests for EmailService."""

    def test_generate_text_summary(self, app, admin_user, child_user, current_week):
        """Test generating plain text summary."""
        with app.app_context():
            # Get the actual user objects
            admin = User.query.get(admin_user['id'])
            child = User.query.get(child_user['id'])
            week = db.session.get(
                __import__('app.models.week', fromlist=['WeekPeriod']).WeekPeriod,
                current_week['id']
            )

            service = EmailService()

            summaries = [{
                'child': child,
                'summary': {
                    'base_allowance': 3.00,
                    'chores_earned': 1.50,
                    'total': 4.50,
                    'completion_percentage': 50.0,
                    'is_paid': False,
                    'chore_details': [
                        {'name': 'Make Bed', 'completions': 3, 'target': 7, 'amount_earned': 1.50}
                    ]
                },
                'teeth_brushing': '6/14'
            }]

            text = service._generate_text_summary(admin, week, summaries)

            assert 'ChoreChamp Weekly Summary' in text
            assert child.name in text
            assert '£3.00' in text
            assert '£1.50' in text
            assert '6/14' in text

    @patch('app.services.email_service.mail')
    def test_send_weekly_summary(self, mock_mail, app, admin_user, child_user, current_week, assigned_chores):
        """Test sending weekly summary emails."""
        with app.app_context():
            service = EmailService()

            # Should not raise an exception
            result = service.send_weekly_summary(current_week['id'])

            assert result is True
            # Verify mail.send was called
            assert mock_mail.send.called

    @patch('app.services.email_service.mail')
    def test_send_payment_confirmation(self, mock_mail, app, admin_user, child_user, current_week):
        """Test sending payment confirmation email."""
        with app.app_context():
            service = EmailService()

            result = service.send_payment_confirmation(
                child_user['id'],
                current_week['id'],
                4.50
            )

            assert result is True
            assert mock_mail.send.called

    def test_send_weekly_summary_no_admins(self, app, child_user, current_week):
        """Test handling when no admin users exist."""
        with app.app_context():
            # Remove admin users
            User.query.filter_by(is_admin=True).delete()
            db.session.commit()

            service = EmailService()
            result = service.send_weekly_summary(current_week['id'])

            assert result is False
