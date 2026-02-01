#!/usr/bin/env python
"""Entry point for ChoreChamp application."""
import os
from app import create_app, db
from app.models import User, ChoreDefinition, WeekPeriod

app = create_app(os.environ.get('FLASK_CONFIG', 'development'))


@app.cli.command('init-db')
def init_db():
    """Initialize the database with tables."""
    db.create_all()
    print('Database tables created.')


@app.cli.command('seed')
def seed_data():
    """Seed the database with sample data."""
    # Create admin user
    admin = User.query.filter_by(email='admin@chorechamp.local').first()
    if not admin:
        admin = User(
            name='Parent',
            email='admin@chorechamp.local',
            is_admin=True
        )
        admin.set_password('password123')
        db.session.add(admin)
        print('Created admin user: admin@chorechamp.local / password123')

    # Create sample children
    children_data = [
        {'name': 'Emma', 'pin': '1234', 'base_allowance': 3.00},
        {'name': 'Jack', 'pin': '5678', 'base_allowance': 3.00},
    ]

    for child_data in children_data:
        child = User.query.filter_by(name=child_data['name'], is_admin=False).first()
        if not child:
            child = User(
                name=child_data['name'],
                is_admin=False,
                base_allowance=child_data['base_allowance']
            )
            child.set_pin(child_data['pin'])
            db.session.add(child)
            print(f"Created child: {child_data['name']} (PIN: {child_data['pin']})")

    # Create preset chores
    chores_data = [
        {'name': 'Brush Teeth', 'amount': 0.25, 'frequency': 'twice_daily', 'times_per_day': 2,
         'description': 'Brush teeth morning and evening'},
        {'name': 'Make Bed', 'amount': 0.50, 'frequency': 'daily',
         'description': 'Make your bed each morning'},
        {'name': 'Tidy Room', 'amount': 1.00, 'frequency': 'daily',
         'description': 'Keep your room tidy'},
        {'name': 'Help with Dishes', 'amount': 0.75, 'frequency': 'daily',
         'description': 'Help load or unload the dishwasher'},
        {'name': 'Take Out Rubbish', 'amount': 1.00, 'frequency': 'weekly',
         'description': 'Take the bins out on collection day'},
    ]

    for chore_data in chores_data:
        chore = ChoreDefinition.query.filter_by(name=chore_data['name']).first()
        if not chore:
            chore = ChoreDefinition(
                name=chore_data['name'],
                amount=chore_data['amount'],
                frequency=chore_data['frequency'],
                times_per_day=chore_data.get('times_per_day', 1),
                description=chore_data.get('description', ''),
                is_preset=True
            )
            db.session.add(chore)
            print(f"Created chore: {chore_data['name']} (£{chore_data['amount']})")

    db.session.commit()
    print('Seed data complete!')


@app.shell_context_processor
def make_shell_context():
    """Make database models available in flask shell."""
    return {
        'db': db,
        'User': User,
        'ChoreDefinition': ChoreDefinition,
        'WeekPeriod': WeekPeriod,
    }


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
