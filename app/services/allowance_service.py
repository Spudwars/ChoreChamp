from datetime import timedelta

from app.models.user import User
from app.models.chore import ChoreDefinition
from app.models.week import WeekPeriod, WeeklyChoreAssignment, WeeklyPayment
from app.models.chore_log import ChoreLog


class AllowanceService:
    """Service for calculating allowances and weekly summaries."""

    def calculate_weekly_summary(self, user_id, week_id):
        """
        Calculate the weekly summary for a user.

        Returns:
            dict: {
                'base_allowance': float,
                'chores_earned': float,
                'total': float,
                'chores_completed': int,
                'chores_target': int,
                'is_paid': bool,
                'chore_details': list
            }
        """
        user = User.query.get(user_id)
        if not user:
            return None

        week = WeekPeriod.query.get(week_id)
        if not week:
            return None

        # Get all assignments for this user in this week
        assignments = WeeklyChoreAssignment.query.filter_by(
            week_id=week_id,
            user_id=user_id
        ).all()

        chores_earned = 0.0
        chores_completed = 0
        chores_target = 0
        chore_details = []

        for assignment in assignments:
            chore = assignment.chore_definition

            # Get completion count for this chore
            completions = ChoreLog.query.filter_by(
                user_id=user_id,
                chore_id=chore.id,
                week_id=week_id
            ).all()

            completion_count = len(completions)
            target = chore.weekly_target
            amount_earned = sum(c.amount_earned for c in completions)

            chores_earned += amount_earned
            chores_completed += completion_count
            chores_target += target

            chore_details.append({
                'assignment_id': assignment.id,
                'chore_id': chore.id,
                'name': assignment.display_name,
                'amount_per_completion': assignment.display_amount,
                'frequency': chore.frequency,
                'completions': completion_count,
                'target': target,
                'amount_earned': amount_earned,
                'percentage': round((completion_count / target * 100) if target > 0 else 0, 1)
            })

        # Check payment status
        payment = WeeklyPayment.query.filter_by(
            week_id=week_id,
            user_id=user_id
        ).first()

        base_allowance = user.base_allowance
        total = base_allowance + chores_earned

        return {
            'base_allowance': base_allowance,
            'chores_earned': round(chores_earned, 2),
            'total': round(total, 2),
            'chores_completed': chores_completed,
            'chores_target': chores_target,
            'completion_percentage': round((chores_completed / chores_target * 100) if chores_target > 0 else 0, 1),
            'is_paid': payment.is_paid if payment else False,
            'paid_at': payment.paid_at if payment else None,
            'chore_details': chore_details
        }

    def get_teeth_brushing_count(self, user_id, week_id):
        """
        Get teeth brushing completion count (x/14).

        Returns:
            tuple: (completed, target) e.g., (10, 14)
        """
        # Find teeth brushing chore
        teeth_chore = ChoreDefinition.query.filter(
            ChoreDefinition.name.ilike('%teeth%'),
            ChoreDefinition.frequency == 'twice_daily'
        ).first()

        if not teeth_chore:
            return (0, 14)

        completions = ChoreLog.query.filter_by(
            user_id=user_id,
            chore_id=teeth_chore.id,
            week_id=week_id
        ).count()

        return (completions, 14)

    def calculate_total_earned(self, user_id, start_date=None, end_date=None):
        """
        Calculate total earnings for a user across multiple weeks.

        Args:
            user_id: User ID
            start_date: Optional start date filter
            end_date: Optional end date filter

        Returns:
            float: Total amount earned
        """
        query = ChoreLog.query.filter_by(user_id=user_id)

        if start_date:
            query = query.filter(ChoreLog.completed_date >= start_date)
        if end_date:
            query = query.filter(ChoreLog.completed_date <= end_date)

        logs = query.all()
        return sum(log.amount_earned for log in logs)

    def get_unpaid_weeks(self, user_id):
        """
        Get list of weeks with unpaid balances.

        Returns:
            list: List of dicts with week info and amounts
        """
        # Get all weeks with assignments for this user
        assignments = WeeklyChoreAssignment.query.filter_by(user_id=user_id).all()
        week_ids = set(a.week_id for a in assignments)

        unpaid_weeks = []
        for week_id in week_ids:
            payment = WeeklyPayment.query.filter_by(
                week_id=week_id,
                user_id=user_id,
                is_paid=True
            ).first()

            if not payment:
                summary = self.calculate_weekly_summary(user_id, week_id)
                week = WeekPeriod.query.get(week_id)
                if summary['total'] > 0:
                    unpaid_weeks.append({
                        'week_id': week_id,
                        'start_date': week.start_date,
                        'end_date': week.end_date,
                        'amount': summary['total']
                    })

        return sorted(unpaid_weeks, key=lambda x: x['start_date'])

    def get_last_week_summary(self, user_id):
        """
        Get summary for the previous week.

        Returns:
            dict or None: Last week's summary with chores_completed and total
        """
        current_week = WeekPeriod.get_or_create_current_week()
        last_week_start = current_week.start_date - timedelta(days=7)

        last_week = WeekPeriod.query.filter_by(start_date=last_week_start).first()
        if not last_week:
            return None

        summary = self.calculate_weekly_summary(user_id, last_week.id)
        if not summary:
            return None

        return {
            'chores_completed': summary['chores_completed'],
            'total': summary['total'],
            'week_start': last_week.start_date,
            'week_end': last_week.end_date
        }

    def get_adjacent_weeks(self, week_id):
        """
        Get the previous and next week periods for navigation.

        Args:
            week_id: Current week ID

        Returns:
            tuple: (previous_week, next_week) - either can be None
        """
        current_week = WeekPeriod.query.get(week_id)
        if not current_week:
            return (None, None)

        # Get previous week
        prev_week_start = current_week.start_date - timedelta(days=7)
        previous_week = WeekPeriod.query.filter_by(start_date=prev_week_start).first()

        # Get next week
        next_week_start = current_week.start_date + timedelta(days=7)
        next_week = WeekPeriod.query.filter_by(start_date=next_week_start).first()

        return (previous_week, next_week)

    def get_12_week_history(self, user_id):
        """
        Returns last 12 weeks of data for charting.

        Args:
            user_id: User ID

        Returns:
            list: List of dicts with week_label, chores_completed, total_earned
        """
        weeks = []
        current_week = WeekPeriod.get_or_create_current_week()

        for i in range(12):
            week_start = current_week.start_date - timedelta(weeks=i)
            week = WeekPeriod.query.filter_by(start_date=week_start).first()
            if week:
                summary = self.calculate_weekly_summary(user_id, week.id)
                if summary:
                    weeks.append({
                        'week_label': week.start_date.strftime('%d %b'),
                        'chores_completed': summary['chores_completed'],
                        'total_earned': summary['total']
                    })
                else:
                    weeks.append({
                        'week_label': week.start_date.strftime('%d %b'),
                        'chores_completed': 0,
                        'total_earned': 0.0
                    })

        return list(reversed(weeks))  # Oldest first
