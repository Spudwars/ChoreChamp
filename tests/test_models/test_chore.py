import pytest
from app import db
from app.models.chore import ChoreDefinition


class TestChoreDefinitionModel:
    """Tests for ChoreDefinition model."""

    def test_create_daily_chore(self, app):
        """Test creating a daily chore."""
        with app.app_context():
            chore = ChoreDefinition(
                name='Make Bed',
                amount=0.50,
                frequency='daily',
                description='Make your bed each morning'
            )
            db.session.add(chore)
            db.session.commit()

            assert chore.id is not None
            assert chore.name == 'Make Bed'
            assert chore.amount == 0.50
            assert chore.frequency == 'daily'
            assert chore.weekly_target == 7
            assert chore.max_weekly_amount == 3.50

    def test_create_twice_daily_chore(self, app):
        """Test creating a twice-daily chore (like teeth brushing)."""
        with app.app_context():
            chore = ChoreDefinition(
                name='Brush Teeth',
                amount=0.25,
                frequency='twice_daily',
                times_per_day=2
            )
            db.session.add(chore)
            db.session.commit()

            assert chore.frequency == 'twice_daily'
            assert chore.times_per_day == 2
            assert chore.weekly_target == 14  # 7 days × 2 times
            assert chore.max_weekly_amount == 3.50  # 0.25 × 14

    def test_create_weekly_chore(self, app):
        """Test creating a weekly chore."""
        with app.app_context():
            chore = ChoreDefinition(
                name='Take Out Rubbish',
                amount=1.00,
                frequency='weekly'
            )
            db.session.add(chore)
            db.session.commit()

            assert chore.weekly_target == 1
            assert chore.max_weekly_amount == 1.00

    def test_create_adhoc_chore(self, app):
        """Test creating an ad-hoc chore."""
        with app.app_context():
            chore = ChoreDefinition(
                name='Help with Garden',
                amount=5.00,
                frequency='ad_hoc',
                is_preset=False
            )
            db.session.add(chore)
            db.session.commit()

            assert chore.is_preset is False
            assert chore.weekly_target == 1
            assert chore.max_weekly_amount == 5.00

    def test_chore_active_status(self, app):
        """Test chore active/inactive status."""
        with app.app_context():
            chore = ChoreDefinition(name='Test', amount=1.00)
            db.session.add(chore)
            db.session.commit()

            assert chore.is_active is True

            chore.is_active = False
            db.session.commit()

            assert chore.is_active is False

    def test_chore_repr(self, app):
        """Test chore string representation."""
        with app.app_context():
            chore = ChoreDefinition(name='Make Bed', amount=0.50)
            assert 'Make Bed' in repr(chore)
            assert '0.5' in repr(chore)
