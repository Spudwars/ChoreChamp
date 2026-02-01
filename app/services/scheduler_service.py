from flask_apscheduler import APScheduler

from app.services.email_service import EmailService

scheduler = APScheduler()


def init_scheduler(app):
    """Initialize the scheduler with the Flask app."""
    scheduler.init_app(app)

    # Add weekly email job - Sunday at 7pm
    scheduler.add_job(
        id='weekly_summary_email',
        func=send_weekly_summary_job,
        trigger='cron',
        day_of_week='sun',
        hour=19,
        minute=0
    )

    scheduler.start()


def send_weekly_summary_job():
    """Job function to send weekly summary emails."""
    from flask import current_app

    with current_app.app_context():
        email_service = EmailService()
        try:
            email_service.send_weekly_summary()
            current_app.logger.info("Weekly summary emails sent successfully")
        except Exception as e:
            current_app.logger.error(f"Failed to send weekly summary emails: {e}")
