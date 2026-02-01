from datetime import datetime

from app import db


# Association table for chore-to-user assignments (which users a preset chore applies to)
chore_user_assignments = db.Table('chore_user_assignments',
    db.Column('chore_id', db.Integer, db.ForeignKey('chore_definitions.id'), primary_key=True),
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True)
)


class ChoreDefinition(db.Model):
    __tablename__ = 'chore_definitions'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    amount = db.Column(db.Float, default=0.0, nullable=False)

    # Frequency settings
    # 'daily' = once per day
    # 'twice_daily' = twice per day (e.g., teeth brushing)
    # 'weekly' = once per week
    # 'flexible' = X times per week on any days
    # 'specific_days' = only on certain days
    # 'ad_hoc' = one-time/special chores
    frequency = db.Column(db.String(20), default='daily', nullable=False)
    times_per_day = db.Column(db.Integer, default=1, nullable=False)

    # For 'flexible' frequency: how many times per week needed for 100%
    times_per_week = db.Column(db.Integer, nullable=True)

    # For 'specific_days' frequency: comma-separated day numbers (0=Mon, 6=Sun)
    # e.g., "0,5" for Monday and Saturday
    preferred_days = db.Column(db.String(20), nullable=True)

    # Whether this is a preset chore (vs ad-hoc)
    is_preset = db.Column(db.Boolean, default=True, nullable=False)

    # Whether this chore applies to all users (children) by default
    applies_to_all = db.Column(db.Boolean, default=True, nullable=False)

    # Who created this chore (null for system presets)
    created_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    # Active status
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    assignments = db.relationship('WeeklyChoreAssignment', backref='chore_definition', lazy='dynamic')
    created_by = db.relationship('User', backref='created_chores', foreign_keys=[created_by_user_id])
    # Users this chore specifically applies to (when applies_to_all is False)
    assigned_users = db.relationship('User', secondary=chore_user_assignments, backref='assigned_chores')

    def applies_to_user(self, user):
        """Check if this chore applies to a specific user."""
        if self.applies_to_all:
            return True
        return user in self.assigned_users

    @property
    def weekly_target(self):
        """Calculate the target number of completions per week."""
        if self.frequency == 'twice_daily':
            return 7 * self.times_per_day  # e.g., 14 for teeth brushing
        elif self.frequency == 'daily':
            return 7
        elif self.frequency == 'weekly':
            return 1
        elif self.frequency == 'flexible':
            return self.times_per_week or 1
        elif self.frequency == 'specific_days':
            return len(self.get_preferred_days())
        else:  # ad_hoc
            return 1

    @property
    def max_weekly_amount(self):
        """Calculate maximum amount earnable per week."""
        return self.amount * self.weekly_target

    def get_preferred_days(self):
        """Return list of preferred day numbers (0=Mon, 6=Sun)."""
        if not self.preferred_days:
            return []
        return [int(d.strip()) for d in self.preferred_days.split(',') if d.strip().isdigit()]

    def is_preferred_day(self, day_num):
        """Check if a day number is a preferred day."""
        if self.frequency != 'specific_days' or not self.preferred_days:
            return True
        return day_num in self.get_preferred_days()

    def __repr__(self):
        return f'<ChoreDefinition {self.name} (£{self.amount})>'
