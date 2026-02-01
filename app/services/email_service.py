from datetime import datetime
from flask import current_app, render_template
from flask_mail import Message

from app import mail, db
from app.models.user import User
from app.models.week import WeekPeriod
from app.services.allowance_service import AllowanceService


class EmailService:
    """Service for sending email notifications."""

    def __init__(self):
        self.allowance_service = AllowanceService()

    def send_weekly_summary(self, week_id=None):
        """
        Send weekly summary emails to all parents.

        Args:
            week_id: Optional week ID. Defaults to current week.
        """
        if week_id is None:
            week = WeekPeriod.get_or_create_current_week()
            week_id = week.id
        else:
            week = WeekPeriod.query.get(week_id)

        if not week:
            return False

        # Get all children
        children = User.query.filter_by(is_admin=False).all()

        # Get all admin users with email
        admins = User.query.filter(
            User.is_admin == True,
            User.email.isnot(None)
        ).all()

        if not admins:
            current_app.logger.warning("No admin users with email addresses found")
            return False

        # Build summary for all children
        summaries = []
        for child in children:
            summary = self.allowance_service.calculate_weekly_summary(child.id, week_id)
            teeth_count = self.allowance_service.get_teeth_brushing_count(child.id, week_id)
            summaries.append({
                'child': child,
                'summary': summary,
                'teeth_brushing': f"{teeth_count[0]}/{teeth_count[1]}"
            })

        # Send email to each admin
        for admin in admins:
            try:
                self._send_summary_email(admin, week, summaries)
            except Exception as e:
                current_app.logger.error(f"Failed to send email to {admin.email}: {e}")

        return True

    def _send_summary_email(self, admin, week, summaries):
        """Send summary email to a single admin."""
        subject = f"ChoreChamp Weekly Summary - {week.start_date.strftime('%b %d')} to {week.end_date.strftime('%b %d, %Y')}"

        # Calculate totals
        total_earned = sum(s['summary']['total'] for s in summaries)
        total_paid = sum(
            s['summary']['total'] for s in summaries
            if s['summary']['is_paid']
        )
        total_unpaid = total_earned - total_paid

        html_body = render_template(
            'email/weekly_summary.html',
            admin=admin,
            week=week,
            summaries=summaries,
            total_earned=total_earned,
            total_paid=total_paid,
            total_unpaid=total_unpaid
        )

        text_body = self._generate_text_summary(admin, week, summaries)

        msg = Message(
            subject=subject,
            recipients=[admin.email],
            body=text_body,
            html=html_body
        )

        mail.send(msg)

    def _generate_text_summary(self, admin, week, summaries):
        """Generate plain text version of the summary."""
        lines = [
            f"ChoreChamp Weekly Summary",
            f"Week: {week.start_date.strftime('%B %d')} - {week.end_date.strftime('%B %d, %Y')}",
            "",
            f"Hi {admin.name},",
            "",
            "Here's the weekly chore summary:",
            ""
        ]

        for s in summaries:
            child = s['child']
            summary = s['summary']
            lines.append(f"--- {child.name} ---")
            lines.append(f"Base Allowance: £{summary['base_allowance']:.2f}")
            lines.append(f"Chores Earned: £{summary['chores_earned']:.2f}")
            lines.append(f"Total: £{summary['total']:.2f}")
            lines.append(f"Completion: {summary['completion_percentage']}%")
            lines.append(f"Teeth Brushing: {s['teeth_brushing']}")
            lines.append(f"Payment Status: {'Paid' if summary['is_paid'] else 'Pending'}")
            lines.append("")

            if summary['chore_details']:
                lines.append("Chore Details:")
                for chore in summary['chore_details']:
                    lines.append(f"  - {chore['name']}: {chore['completions']}/{chore['target']} (£{chore['amount_earned']:.2f})")
                lines.append("")

        lines.append("--")
        lines.append("ChoreChamp - Making chores fun!")

        return "\n".join(lines)

    def send_payment_confirmation(self, user_id, week_id, amount):
        """
        Send payment confirmation email to parents.

        Args:
            user_id: Child user ID
            week_id: Week ID
            amount: Amount paid
        """
        user = User.query.get(user_id)
        week = WeekPeriod.query.get(week_id)

        if not user or not week:
            return False

        admins = User.query.filter(
            User.is_admin == True,
            User.email.isnot(None)
        ).all()

        subject = f"ChoreChamp: Payment Recorded for {user.name}"

        for admin in admins:
            try:
                msg = Message(
                    subject=subject,
                    recipients=[admin.email],
                    body=f"""
Hi {admin.name},

A payment has been recorded in ChoreChamp:

Child: {user.name}
Week: {week.start_date.strftime('%B %d')} - {week.end_date.strftime('%B %d, %Y')}
Amount: £{amount:.2f}
Date: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}

--
ChoreChamp
                    """.strip()
                )
                mail.send(msg)
            except Exception as e:
                current_app.logger.error(f"Failed to send payment email to {admin.email}: {e}")

        return True
