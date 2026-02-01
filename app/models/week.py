from datetime import datetime, timedelta

from app import db


class WeekPeriod(db.Model):
    __tablename__ = 'week_periods'

    id = db.Column(db.Integer, primary_key=True)
    start_date = db.Column(db.Date, nullable=False, unique=True)  # Always a Monday
    end_date = db.Column(db.Date, nullable=False)  # Always a Sunday

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    assignments = db.relationship('WeeklyChoreAssignment', backref='week_period', lazy='dynamic')
    payments = db.relationship('WeeklyPayment', backref='week_period', lazy='dynamic')
    chore_logs = db.relationship('ChoreLog', backref='week_period', lazy='dynamic')

    @classmethod
    def get_or_create_current_week(cls):
        """Get or create the current week period."""
        today = datetime.now().date()
        # Find Monday of current week
        monday = today - timedelta(days=today.weekday())
        sunday = monday + timedelta(days=6)

        week = cls.query.filter_by(start_date=monday).first()
        if not week:
            week = cls(start_date=monday, end_date=sunday)
            db.session.add(week)
            db.session.commit()
        return week

    @classmethod
    def get_or_create_week_for_date(cls, date):
        """Get or create the week period containing a specific date."""
        # Find Monday of the week containing the date
        monday = date - timedelta(days=date.weekday())
        sunday = monday + timedelta(days=6)

        week = cls.query.filter_by(start_date=monday).first()
        if not week:
            week = cls(start_date=monday, end_date=sunday)
            db.session.add(week)
            db.session.commit()
        return week

    def get_days(self):
        """Return list of dates in this week."""
        return [self.start_date + timedelta(days=i) for i in range(7)]

    def __repr__(self):
        return f'<WeekPeriod {self.start_date} to {self.end_date}>'


class WeeklyChoreAssignment(db.Model):
    __tablename__ = 'weekly_chore_assignments'

    id = db.Column(db.Integer, primary_key=True)
    week_id = db.Column(db.Integer, db.ForeignKey('week_periods.id'), nullable=False)
    chore_id = db.Column(db.Integer, db.ForeignKey('chore_definitions.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # For ad-hoc chores, store custom name/amount
    custom_name = db.Column(db.String(100), nullable=True)
    custom_amount = db.Column(db.Float, nullable=True)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user = db.relationship('User', backref='chore_assignments')

    @property
    def display_name(self):
        """Get the display name (custom or from definition)."""
        return self.custom_name or self.chore_definition.name

    @property
    def display_amount(self):
        """Get the display amount (custom or from definition)."""
        if self.custom_amount is not None:
            return self.custom_amount
        return self.chore_definition.amount

    def __repr__(self):
        return f'<WeeklyChoreAssignment {self.display_name} for week {self.week_id}>'


class WeeklyPayment(db.Model):
    __tablename__ = 'weekly_payments'

    id = db.Column(db.Integer, primary_key=True)
    week_id = db.Column(db.Integer, db.ForeignKey('week_periods.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # Payment details
    amount = db.Column(db.Float, nullable=False)
    is_paid = db.Column(db.Boolean, default=False, nullable=False)
    paid_at = db.Column(db.DateTime, nullable=True)
    notes = db.Column(db.Text, nullable=True)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def mark_as_paid(self):
        """Mark this payment as paid."""
        self.is_paid = True
        self.paid_at = datetime.utcnow()

    def __repr__(self):
        status = "Paid" if self.is_paid else "Pending"
        return f'<WeeklyPayment £{self.amount} ({status})>'
