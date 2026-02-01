from datetime import datetime

from app import db


class ChoreLog(db.Model):
    __tablename__ = 'chore_logs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    chore_id = db.Column(db.Integer, db.ForeignKey('chore_definitions.id'), nullable=False)
    week_id = db.Column(db.Integer, db.ForeignKey('week_periods.id'), nullable=False)
    assignment_id = db.Column(db.Integer, db.ForeignKey('weekly_chore_assignments.id'), nullable=True)

    # Completion details
    completed_date = db.Column(db.Date, nullable=False)
    completed_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # For twice_daily chores, track which completion (1=morning, 2=evening)
    completion_slot = db.Column(db.Integer, default=1, nullable=False)

    # Amount earned for this completion
    amount_earned = db.Column(db.Float, default=0.0, nullable=False)

    # Relationships
    chore_definition = db.relationship('ChoreDefinition', backref='logs')

    @classmethod
    def is_completed(cls, user_id, chore_id, date, slot=1):
        """Check if a chore is completed for a specific date and slot."""
        return cls.query.filter_by(
            user_id=user_id,
            chore_id=chore_id,
            completed_date=date,
            completion_slot=slot
        ).first() is not None

    @classmethod
    def get_completion_count(cls, user_id, chore_id, week_id):
        """Get the number of completions for a chore in a week."""
        return cls.query.filter_by(
            user_id=user_id,
            chore_id=chore_id,
            week_id=week_id
        ).count()

    @classmethod
    def toggle_completion(cls, user_id, chore_id, week_id, date, slot=1, amount=0.0):
        """Toggle chore completion status. Returns (is_now_completed, log_entry)."""
        existing = cls.query.filter_by(
            user_id=user_id,
            chore_id=chore_id,
            completed_date=date,
            completion_slot=slot
        ).first()

        if existing:
            db.session.delete(existing)
            db.session.commit()
            return False, None
        else:
            log = cls(
                user_id=user_id,
                chore_id=chore_id,
                week_id=week_id,
                completed_date=date,
                completion_slot=slot,
                amount_earned=amount
            )
            db.session.add(log)
            db.session.commit()
            return True, log

    def __repr__(self):
        return f'<ChoreLog {self.chore_id} on {self.completed_date}>'
