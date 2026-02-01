from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user

from app import db
from app.models.chore import ChoreDefinition
from app.models.week import WeekPeriod, WeeklyChoreAssignment
from app.models.chore_log import ChoreLog
from app.services.allowance_service import AllowanceService

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/')
@dashboard_bp.route('/dashboard')
@login_required
def index():
    # Get current week
    week = WeekPeriod.get_or_create_current_week()
    days = week.get_days()

    # Get assigned chores for current user
    assignments = WeeklyChoreAssignment.query.filter_by(
        week_id=week.id,
        user_id=current_user.id
    ).all()

    # If no assignments, create default ones from preset chores
    if not assignments:
        preset_chores = ChoreDefinition.query.filter_by(is_preset=True, is_active=True).all()
        for chore in preset_chores:
            assignment = WeeklyChoreAssignment(
                week_id=week.id,
                chore_id=chore.id,
                user_id=current_user.id
            )
            db.session.add(assignment)
        db.session.commit()
        assignments = WeeklyChoreAssignment.query.filter_by(
            week_id=week.id,
            user_id=current_user.id
        ).all()

    # Build completion status matrix
    completion_status = {}
    for assignment in assignments:
        chore = assignment.chore_definition
        completion_status[assignment.id] = {}

        for day in days:
            if chore.frequency == 'twice_daily':
                # Track morning and evening separately
                completion_status[assignment.id][day] = {
                    'morning': ChoreLog.is_completed(current_user.id, chore.id, day, slot=1),
                    'evening': ChoreLog.is_completed(current_user.id, chore.id, day, slot=2)
                }
            else:
                completion_status[assignment.id][day] = {
                    'done': ChoreLog.is_completed(current_user.id, chore.id, day, slot=1)
                }

    # Calculate weekly totals
    allowance_service = AllowanceService()
    weekly_summary = allowance_service.calculate_weekly_summary(current_user.id, week.id)
    last_week_summary = allowance_service.get_last_week_summary(current_user.id)

    return render_template(
        'dashboard/index.html',
        week=week,
        days=days,
        assignments=assignments,
        completion_status=completion_status,
        weekly_summary=weekly_summary,
        last_week_summary=last_week_summary,
        today=datetime.now().date()
    )


@dashboard_bp.route('/chores/toggle', methods=['POST'])
@login_required
def toggle_chore():
    """HTMX endpoint to toggle chore completion."""
    assignment_id = request.form.get('assignment_id', type=int)
    date_str = request.form.get('date')
    slot = request.form.get('slot', 1, type=int)

    if not assignment_id or not date_str:
        return jsonify({'error': 'Missing parameters'}), 400

    # Parse date
    try:
        date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': 'Invalid date format'}), 400

    # Get assignment
    assignment = WeeklyChoreAssignment.query.get(assignment_id)
    if not assignment or assignment.user_id != current_user.id:
        return jsonify({'error': 'Invalid assignment'}), 403

    chore = assignment.chore_definition

    # Toggle completion
    is_completed, log = ChoreLog.toggle_completion(
        user_id=current_user.id,
        chore_id=chore.id,
        week_id=assignment.week_id,
        date=date,
        slot=slot,
        amount=assignment.display_amount
    )

    # Get updated counts for twice_daily chores
    completion_count = ChoreLog.get_completion_count(
        current_user.id, chore.id, assignment.week_id
    )

    # Calculate updated weekly total
    allowance_service = AllowanceService()
    weekly_summary = allowance_service.calculate_weekly_summary(
        current_user.id, assignment.week_id
    )

    return render_template(
        'dashboard/partials/chore_cell.html',
        assignment=assignment,
        date=date,
        slot=slot,
        is_completed=is_completed,
        completion_count=completion_count,
        weekly_summary=weekly_summary
    )


@dashboard_bp.route('/weekly-summary')
@login_required
def weekly_summary():
    """HTMX endpoint to get updated weekly summary."""
    week = WeekPeriod.get_or_create_current_week()
    allowance_service = AllowanceService()
    summary = allowance_service.calculate_weekly_summary(current_user.id, week.id)
    return render_template('dashboard/partials/weekly_summary.html', weekly_summary=summary)


@dashboard_bp.route('/chores/add-adhoc', methods=['POST'])
@login_required
def add_adhoc_chore():
    """Allow child to add their own ad-hoc chore."""
    name = request.form.get('name')
    amount = request.form.get('amount', type=float, default=0.50)

    if not name or len(name.strip()) < 2:
        return '<div class="text-red-500 text-sm">Please enter a chore name</div>', 400

    # Create ad-hoc chore definition
    chore = ChoreDefinition(
        name=name.strip(),
        amount=amount,
        frequency='ad_hoc',
        is_preset=False,
        created_by_user_id=current_user.id
    )
    db.session.add(chore)
    db.session.flush()

    # Get current week
    week = WeekPeriod.get_or_create_current_week()

    # Create assignment
    assignment = WeeklyChoreAssignment(
        week_id=week.id,
        chore_id=chore.id,
        user_id=current_user.id,
        custom_name=name.strip(),
        custom_amount=amount
    )
    db.session.add(assignment)
    db.session.commit()

    # Return success message that will trigger a page reload
    return '''
    <div class="text-green-600 text-sm" id="adhoc-success">
        Added! Refreshing...
        <script>setTimeout(() => window.location.reload(), 500);</script>
    </div>
    '''
