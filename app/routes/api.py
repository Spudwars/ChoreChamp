from datetime import datetime
from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity

from app import db
from app.models.user import User
from app.models.chore import ChoreDefinition
from app.models.week import WeekPeriod, WeeklyChoreAssignment
from app.models.chore_log import ChoreLog
from app.services.allowance_service import AllowanceService

api_bp = Blueprint('api', __name__)


@api_bp.route('/auth/login', methods=['POST'])
def login():
    """JWT authentication endpoint."""
    data = request.get_json()

    if not data:
        return jsonify({'error': 'Missing request body'}), 400

    auth_type = data.get('type', 'pin')

    if auth_type == 'pin':
        user_id = data.get('user_id')
        pin = data.get('pin')

        if not user_id or not pin:
            return jsonify({'error': 'Missing user_id or pin'}), 400

        user = User.query.get(user_id)
        if not user or not user.check_pin(pin):
            return jsonify({'error': 'Invalid credentials'}), 401

    else:
        email = data.get('email')
        password = data.get('password')

        if not email or not password:
            return jsonify({'error': 'Missing email or password'}), 400

        user = User.query.filter_by(email=email).first()
        if not user or not user.check_password(password):
            return jsonify({'error': 'Invalid credentials'}), 401

    access_token = create_access_token(identity=str(user.id))
    return jsonify({
        'access_token': access_token,
        'user': {
            'id': user.id,
            'name': user.name,
            'is_admin': user.is_admin
        }
    })


@api_bp.route('/weeks/current', methods=['GET'])
@jwt_required()
def current_week():
    """Get current week data."""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)

    if not user:
        return jsonify({'error': 'User not found'}), 404

    week = WeekPeriod.get_or_create_current_week()

    # Get assignments
    assignments = WeeklyChoreAssignment.query.filter_by(
        week_id=week.id,
        user_id=user_id
    ).all()

    # Build response
    chores_data = []
    for assignment in assignments:
        chore = assignment.chore_definition
        completions = ChoreLog.query.filter_by(
            user_id=user_id,
            chore_id=chore.id,
            week_id=week.id
        ).all()

        chores_data.append({
            'assignment_id': assignment.id,
            'chore_id': chore.id,
            'name': assignment.display_name,
            'amount': assignment.display_amount,
            'frequency': chore.frequency,
            'weekly_target': chore.weekly_target,
            'completions': [
                {
                    'date': c.completed_date.isoformat(),
                    'slot': c.completion_slot,
                    'amount_earned': c.amount_earned
                }
                for c in completions
            ]
        })

    # Calculate summary
    allowance_service = AllowanceService()
    summary = allowance_service.calculate_weekly_summary(user_id, week.id)

    return jsonify({
        'week': {
            'id': week.id,
            'start_date': week.start_date.isoformat(),
            'end_date': week.end_date.isoformat()
        },
        'chores': chores_data,
        'summary': summary
    })


@api_bp.route('/chores/<int:chore_id>/complete', methods=['POST'])
@jwt_required()
def complete_chore(chore_id):
    """Mark a chore as complete."""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)

    if not user:
        return jsonify({'error': 'User not found'}), 404

    data = request.get_json() or {}
    date_str = data.get('date', datetime.now().date().isoformat())
    slot = data.get('slot', 1)

    try:
        date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': 'Invalid date format'}), 400

    chore = ChoreDefinition.query.get(chore_id)
    if not chore:
        return jsonify({'error': 'Chore not found'}), 404

    week = WeekPeriod.get_or_create_week_for_date(date)

    # Check assignment exists
    assignment = WeeklyChoreAssignment.query.filter_by(
        week_id=week.id,
        chore_id=chore_id,
        user_id=user_id
    ).first()

    if not assignment:
        return jsonify({'error': 'Chore not assigned to user'}), 403

    is_completed, log = ChoreLog.toggle_completion(
        user_id=user_id,
        chore_id=chore_id,
        week_id=week.id,
        date=date,
        slot=slot,
        amount=assignment.display_amount
    )

    # Get updated summary
    allowance_service = AllowanceService()
    summary = allowance_service.calculate_weekly_summary(user_id, week.id)

    return jsonify({
        'is_completed': is_completed,
        'date': date_str,
        'slot': slot,
        'amount_earned': assignment.display_amount if is_completed else 0,
        'weekly_summary': summary
    })


@api_bp.route('/users', methods=['GET'])
@jwt_required()
def list_users():
    """List all children (for user selection)."""
    children = User.query.filter_by(is_admin=False).all()
    return jsonify({
        'users': [
            {
                'id': u.id,
                'name': u.name
            }
            for u in children
        ]
    })
