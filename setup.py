#!/usr/bin/env python
"""Setup script for ChoreChamp - creates database and seed data."""
import os
import sys

# Add the app directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models.user import User
from app.models.chore import ChoreDefinition


def setup():
    """Set up the database and seed data."""
    app = create_app('development')

    with app.app_context():
        print("Creating database tables...")
        db.create_all()
        print("Done!")

        # Check if we need to seed
        if User.query.first() is None:
            print("\nSeeding database with sample data...")
            seed_data()
        else:
            print("\nDatabase already has data. Skipping seed.")

        print("\n" + "=" * 50)
        print("ChoreChamp is ready!")
        print("=" * 50)
        print("\nTo start the server, run:")
        print("  python run.py")
        print("\nDefault login credentials:")
        print("  Admin: admin@chorechamp.local / password123")
        print("  Child: Emma (PIN: 1234) or Jack (PIN: 5678)")
        print("=" * 50)


def seed_data():
    """Seed the database with sample data."""
    # Create admin users
    admins_data = [
        {'name': 'Chris', 'email': 'chris@chorechamp.local', 'password': 'password123'},
        {'name': 'Riina', 'email': 'riina@chorechamp.local', 'password': 'password123'},
    ]

    for admin_data in admins_data:
        admin = User(
            name=admin_data['name'],
            email=admin_data['email'],
            is_admin=True
        )
        admin.set_password(admin_data['password'])
        db.session.add(admin)
        print(f"  Created admin: {admin_data['email']} / {admin_data['password']}")

    # Create sample children
    children_data = [
        {'name': 'Nico', 'pin': '1234', 'base_allowance': 3.00},
        {'name': 'Jack', 'pin': '5678', 'base_allowance': 3.00},
    ]

    for child_data in children_data:
        child = User(
            name=child_data['name'],
            is_admin=False,
            base_allowance=child_data['base_allowance']
        )
        child.set_pin(child_data['pin'])
        db.session.add(child)
        print(f"  Created child: {child_data['name']} (PIN: {child_data['pin']})")

    # Create preset chores
    chores_data = [
        {'name': 'Brush Teeth', 'amount': 0.25, 'frequency': 'twice_daily', 'times_per_day': 2,
         'description': 'Brush teeth morning and evening'},
        {'name': 'Make Bed', 'amount': 0.50, 'frequency': 'daily',
         'description': 'Make your bed each morning'},
        {'name': 'Tidy Room', 'amount': 1.00, 'frequency': 'flexible', 'times_per_week': 3,
         'description': 'Keep your room tidy (3 times per week)'},
        {'name': 'Help with Dishes', 'amount': 0.75, 'frequency': 'daily',
         'description': 'Help load or unload the dishwasher'},
        {'name': 'Take Out Rubbish', 'amount': 1.00, 'frequency': 'weekly',
         'description': 'Take the bins out on collection day'},
        {'name': 'Piano Practice', 'amount': 1.00, 'frequency': 'specific_days', 'preferred_days': '0,5',
         'description': 'Practice piano (Monday and Saturday)'},
        {'name': 'Reading', 'amount': 0.50, 'frequency': 'flexible', 'times_per_week': 4,
         'description': 'Read for 20 minutes (4 times per week)'},
    ]

    for chore_data in chores_data:
        chore = ChoreDefinition(
            name=chore_data['name'],
            amount=chore_data['amount'],
            frequency=chore_data['frequency'],
            times_per_day=chore_data.get('times_per_day', 1),
            times_per_week=chore_data.get('times_per_week'),
            preferred_days=chore_data.get('preferred_days'),
            description=chore_data.get('description', ''),
            is_preset=True
        )
        db.session.add(chore)
        print(f"  Created chore: {chore_data['name']} (£{chore_data['amount']})")

    db.session.commit()
    print("\nSeed data complete!")


if __name__ == '__main__':
    setup()
