import pytest
from datetime import date, timedelta

from app import db
from app.models.user import User
from app.models.chore import ChoreDefinition
from app.models.week import WeekPeriod, WeeklyChoreAssignment
from app.models.chore_log import ChoreLog
from app.services.allowance_service import AllowanceService


class TestAllowanceService:
    """Tests for AllowanceService."""

    def test_calculate_weekly_summary_empty(self, app, child_user, current_week):
        """Test summary with no chores completed."""
        with app.app_context():
            service = AllowanceService()
            summary = service.calculate_weekly_summary(
                child_user['id'],
                current_week['id']
            )

            assert summary['base_allowance'] == 3.00
            assert summary['chores_earned'] == 0.00
            assert summary['total'] == 3.00
            assert summary['chores_completed'] == 0
            assert summary['is_paid'] is False

    def test_calculate_weekly_summary_with_completions(self, app, child_user, sample_chores, current_week):
        """Test summary with some chores completed."""
        with app.app_context():
            # Create assignments
            for chore_data in sample_chores:
                assignment = WeeklyChoreAssignment(
                    week_id=current_week['id'],
                    chore_id=chore_data['id'],
                    user_id=child_user['id']
                )
                db.session.add(assignment)
            db.session.commit()

            # Complete the 'Make Bed' chore for 3 days
            make_bed = next(c for c in sample_chores if c['name'] == 'Make Bed')
            today = date.today()

            for i in range(3):
                log = ChoreLog(
                    user_id=child_user['id'],
                    chore_id=make_bed['id'],
                    week_id=current_week['id'],
                    completed_date=today - timedelta(days=i),
                    amount_earned=0.50
                )
                db.session.add(log)
            db.session.commit()

            service = AllowanceService()
            summary = service.calculate_weekly_summary(
                child_user['id'],
                current_week['id']
            )

            assert summary['base_allowance'] == 3.00
            assert summary['chores_earned'] == 1.50  # 3 × £0.50
            assert summary['total'] == 4.50  # £3.00 base + £1.50 earned

    def test_teeth_brushing_count(self, app, child_user, current_week):
        """Test teeth brushing counter (x/14)."""
        with app.app_context():
            # Create teeth brushing chore
            teeth = ChoreDefinition(
                name='Brush Teeth',
                amount=0.25,
                frequency='twice_daily',
                times_per_day=2,
                is_preset=True
            )
            db.session.add(teeth)
            db.session.commit()

            # Log some completions (morning and evening for 2 days)
            today = date.today()
            for day_offset in range(2):
                for slot in [1, 2]:  # morning and evening
                    log = ChoreLog(
                        user_id=child_user['id'],
                        chore_id=teeth.id,
                        week_id=current_week['id'],
                        completed_date=today - timedelta(days=day_offset),
                        completion_slot=slot,
                        amount_earned=0.25
                    )
                    db.session.add(log)
            db.session.commit()

            service = AllowanceService()
            completed, target = service.get_teeth_brushing_count(
                child_user['id'],
                current_week['id']
            )

            assert completed == 4  # 2 days × 2 times
            assert target == 14  # 7 days × 2 times

    def test_chore_toggle(self, app, child_user, sample_chores, current_week):
        """Test toggling chore completion."""
        with app.app_context():
            make_bed = next(c for c in sample_chores if c['name'] == 'Make Bed')
            today = date.today()

            # Toggle on
            is_completed, log = ChoreLog.toggle_completion(
                user_id=child_user['id'],
                chore_id=make_bed['id'],
                week_id=current_week['id'],
                date=today,
                slot=1,
                amount=0.50
            )

            assert is_completed is True
            assert log is not None
            assert log.amount_earned == 0.50

            # Toggle off
            is_completed, log = ChoreLog.toggle_completion(
                user_id=child_user['id'],
                chore_id=make_bed['id'],
                week_id=current_week['id'],
                date=today,
                slot=1,
                amount=0.50
            )

            assert is_completed is False
            assert log is None

    def test_completion_percentage(self, app, child_user, sample_chores, current_week):
        """Test completion percentage calculation."""
        with app.app_context():
            # Create assignment for just one chore
            make_bed = next(c for c in sample_chores if c['name'] == 'Make Bed')
            assignment = WeeklyChoreAssignment(
                week_id=current_week['id'],
                chore_id=make_bed['id'],
                user_id=child_user['id']
            )
            db.session.add(assignment)

            # Complete 3 out of 7 days
            today = date.today()
            for i in range(3):
                log = ChoreLog(
                    user_id=child_user['id'],
                    chore_id=make_bed['id'],
                    week_id=current_week['id'],
                    completed_date=today - timedelta(days=i),
                    amount_earned=0.50
                )
                db.session.add(log)
            db.session.commit()

            service = AllowanceService()
            summary = service.calculate_weekly_summary(
                child_user['id'],
                current_week['id']
            )

            # Should be about 42.9% (3/7)
            assert summary['completion_percentage'] == pytest.approx(42.9, rel=0.1)
