import pytest
from datetime import date, timedelta

from app import create_app, db
from app.models.user import User
from app.models.chore import ChoreDefinition
from app.models.week import WeekPeriod, WeeklyChoreAssignment
from app.models.chore_log import ChoreLog


@pytest.fixture
def app():
    """Create application for testing."""
    app = create_app('testing')
    app.config['WTF_CSRF_ENABLED'] = False

    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Create test CLI runner."""
    return app.test_cli_runner()


@pytest.fixture
def admin_user(app):
    """Create an admin user."""
    with app.app_context():
        user = User(
            name='Test Admin',
            email='admin@test.com',
            is_admin=True
        )
        user.set_password('password123')
        db.session.add(user)
        db.session.commit()

        # Refresh to get the ID
        db.session.refresh(user)
        return {
            'id': user.id,
            'name': user.name,
            'email': user.email,
            'password': 'password123'
        }


@pytest.fixture
def child_user(app):
    """Create a child user."""
    with app.app_context():
        user = User(
            name='Test Child',
            is_admin=False,
            base_allowance=3.00
        )
        user.set_pin('1234')
        db.session.add(user)
        db.session.commit()

        db.session.refresh(user)
        return {
            'id': user.id,
            'name': user.name,
            'pin': '1234',
            'base_allowance': 3.00
        }


@pytest.fixture
def sample_chores(app):
    """Create sample chores."""
    with app.app_context():
        chores = [
            ChoreDefinition(
                name='Brush Teeth',
                amount=0.25,
                frequency='twice_daily',
                times_per_day=2,
                is_preset=True
            ),
            ChoreDefinition(
                name='Make Bed',
                amount=0.50,
                frequency='daily',
                is_preset=True
            ),
            ChoreDefinition(
                name='Take Out Rubbish',
                amount=1.00,
                frequency='weekly',
                is_preset=True
            ),
        ]

        for chore in chores:
            db.session.add(chore)
        db.session.commit()

        return [
            {'id': c.id, 'name': c.name, 'amount': c.amount, 'frequency': c.frequency}
            for c in chores
        ]


@pytest.fixture
def current_week(app):
    """Create current week period."""
    with app.app_context():
        week = WeekPeriod.get_or_create_current_week()
        return {
            'id': week.id,
            'start_date': week.start_date,
            'end_date': week.end_date
        }


@pytest.fixture
def assigned_chores(app, child_user, sample_chores, current_week):
    """Create chore assignments for child."""
    with app.app_context():
        assignments = []
        for chore_data in sample_chores:
            assignment = WeeklyChoreAssignment(
                week_id=current_week['id'],
                chore_id=chore_data['id'],
                user_id=child_user['id']
            )
            db.session.add(assignment)
            assignments.append(assignment)

        db.session.commit()

        return [
            {'id': a.id, 'chore_id': a.chore_id, 'user_id': a.user_id}
            for a in assignments
        ]


def login_admin(client, admin_user):
    """Helper to login as admin."""
    return client.post('/login', data={
        'login_type': 'adult',
        'email': admin_user['email'],
        'password': admin_user['password']
    }, follow_redirects=True)


def login_child(client, child_user):
    """Helper to login as child."""
    return client.post('/login', data={
        'login_type': 'child',
        'user_id': child_user['id'],
        'pin': child_user['pin']
    }, follow_redirects=True)
