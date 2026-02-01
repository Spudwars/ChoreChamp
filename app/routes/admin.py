from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_required, current_user
from functools import wraps

from app import db
from app.models.user import User
from app.models.chore import ChoreDefinition
from app.models.week import WeekPeriod, WeeklyChoreAssignment, WeeklyPayment
from app.models.chore_log import ChoreLog
from app.services.allowance_service import AllowanceService
from app.services.email_service import EmailService

admin_bp = Blueprint('admin', __name__)


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('Admin access required.', 'error')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


@admin_bp.route('/')
@login_required
@admin_required
def index():
    week = WeekPeriod.get_or_create_current_week()
    children = User.query.filter_by(is_admin=False).all()
    preset_chores = ChoreDefinition.query.filter_by(is_preset=True).all()

    # Get weekly summaries for all children
    allowance_service = AllowanceService()
    summaries = {}
    for child in children:
        summaries[child.id] = allowance_service.calculate_weekly_summary(child.id, week.id)

    return render_template(
        'admin/index.html',
        week=week,
        children=children,
        preset_chores=preset_chores,
        summaries=summaries
    )


@admin_bp.route('/view-child/<int:child_id>')
@admin_bp.route('/view-child/<int:child_id>/week/<int:week_id>')
@login_required
@admin_required
def view_child_dashboard(child_id, week_id=None):
    """View a child's dashboard as a parent for editing."""
    child = User.query.get_or_404(child_id)
    if child.is_admin:
        flash('Cannot view admin user dashboard.', 'error')
        return redirect(url_for('admin.index'))

    # Get specified week or current week
    if week_id:
        week = WeekPeriod.query.get_or_404(week_id)
    else:
        week = WeekPeriod.get_or_create_current_week()

    days = week.get_days()
    today = datetime.now().date()

    # Check if this week is paid (locked)
    payment = WeeklyPayment.query.filter_by(week_id=week.id, user_id=child.id, is_paid=True).first()
    is_locked = payment is not None

    # Get assigned chores for child
    assignments = WeeklyChoreAssignment.query.filter_by(
        week_id=week.id,
        user_id=child.id
    ).all()

    # Build completion status matrix
    completion_status = {}
    for assignment in assignments:
        chore = assignment.chore_definition
        completion_status[assignment.id] = {}

        for day in days:
            if chore.frequency == 'twice_daily':
                completion_status[assignment.id][day] = {
                    'morning': ChoreLog.is_completed(child.id, chore.id, day, slot=1),
                    'evening': ChoreLog.is_completed(child.id, chore.id, day, slot=2)
                }
            else:
                completion_status[assignment.id][day] = {
                    'done': ChoreLog.is_completed(child.id, chore.id, day, slot=1)
                }

    # Calculate weekly totals
    allowance_service = AllowanceService()
    weekly_summary = allowance_service.calculate_weekly_summary(child.id, week.id)
    last_week_summary = allowance_service.get_last_week_summary(child.id)

    return render_template(
        'admin/child_dashboard.html',
        child=child,
        week=week,
        days=days,
        assignments=assignments,
        completion_status=completion_status,
        weekly_summary=weekly_summary,
        last_week_summary=last_week_summary,
        today=today,
        is_locked=is_locked,
        payment=payment
    )


# --- Chore Management ---

@admin_bp.route('/chores', methods=['GET'])
@login_required
@admin_required
def chores():
    preset_chores = ChoreDefinition.query.filter_by(is_preset=True).all()
    all_users = User.query.all()  # Include all users (children and adults)
    return render_template('admin/chores.html', chores=preset_chores, all_users=all_users)


@admin_bp.route('/chores', methods=['POST'])
@login_required
@admin_required
def create_chore():
    name = request.form.get('name')
    amount = request.form.get('amount', type=float, default=0.0)
    frequency = request.form.get('frequency', 'daily')
    times_per_day = request.form.get('times_per_day', type=int, default=1)
    times_per_week = request.form.get('times_per_week', type=int)
    preferred_days = request.form.get('preferred_days', '').strip()
    description = request.form.get('description', '')
    applies_to_all = request.form.get('applies_to_all') == 'on'
    assigned_user_ids = request.form.getlist('assigned_users', type=int)

    if not name:
        flash('Chore name is required.', 'error')
        return redirect(url_for('admin.chores'))

    chore = ChoreDefinition(
        name=name,
        amount=amount,
        frequency=frequency,
        times_per_day=times_per_day,
        times_per_week=times_per_week if frequency == 'flexible' else None,
        preferred_days=preferred_days if frequency == 'specific_days' else None,
        description=description,
        is_preset=True,
        applies_to_all=applies_to_all
    )

    # If not applying to all, assign specific users
    if not applies_to_all and assigned_user_ids:
        assigned_users = User.query.filter(User.id.in_(assigned_user_ids)).all()
        chore.assigned_users = assigned_users

    db.session.add(chore)
    db.session.commit()

    flash(f'Chore "{name}" created successfully.', 'success')
    return redirect(url_for('admin.chores'))


@admin_bp.route('/chores/<int:chore_id>', methods=['POST'])
@login_required
@admin_required
def update_chore(chore_id):
    chore = ChoreDefinition.query.get_or_404(chore_id)

    chore.name = request.form.get('name', chore.name)
    chore.amount = request.form.get('amount', type=float, default=chore.amount)
    chore.frequency = request.form.get('frequency', chore.frequency)
    chore.times_per_day = request.form.get('times_per_day', type=int, default=chore.times_per_day)
    chore.times_per_week = request.form.get('times_per_week', type=int) if chore.frequency == 'flexible' else None
    chore.preferred_days = request.form.get('preferred_days', '').strip() if chore.frequency == 'specific_days' else None
    chore.description = request.form.get('description', chore.description)
    chore.is_active = request.form.get('is_active') == 'on'
    chore.applies_to_all = request.form.get('applies_to_all') == 'on'

    # Update assigned users
    assigned_user_ids = request.form.getlist('assigned_users', type=int)
    if not chore.applies_to_all:
        assigned_users = User.query.filter(User.id.in_(assigned_user_ids)).all()
        chore.assigned_users = assigned_users
    else:
        chore.assigned_users = []

    db.session.commit()

    flash(f'Chore "{chore.name}" updated successfully.', 'success')
    return redirect(url_for('admin.chores'))


@admin_bp.route('/chores/<int:chore_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_chore(chore_id):
    chore = ChoreDefinition.query.get_or_404(chore_id)
    name = chore.name

    # Soft delete - just deactivate
    chore.is_active = False
    db.session.commit()

    flash(f'Chore "{name}" has been deactivated.', 'success')
    return redirect(url_for('admin.chores'))


# --- Ad-hoc Chore Assignment ---

@admin_bp.route('/weeks/<int:week_id>/adhoc', methods=['POST'])
@login_required
@admin_required
def create_adhoc_chore(week_id):
    week = WeekPeriod.query.get_or_404(week_id)
    user_id = request.form.get('user_id', type=int)
    name = request.form.get('name')
    amount = request.form.get('amount', type=float, default=0.0)

    if not user_id or not name:
        flash('User and chore name are required.', 'error')
        return redirect(url_for('admin.index'))

    # Create ad-hoc chore definition
    chore = ChoreDefinition(
        name=name,
        amount=amount,
        frequency='ad_hoc',
        is_preset=False
    )
    db.session.add(chore)
    db.session.flush()

    # Create assignment
    assignment = WeeklyChoreAssignment(
        week_id=week.id,
        chore_id=chore.id,
        user_id=user_id,
        custom_name=name,
        custom_amount=amount
    )
    db.session.add(assignment)
    db.session.commit()

    flash(f'Ad-hoc chore "{name}" assigned successfully.', 'success')
    return redirect(url_for('admin.index'))


# --- User Management ---

@admin_bp.route('/users')
@login_required
@admin_required
def users():
    all_users = User.query.all()
    return render_template('admin/users.html', users=all_users)


@admin_bp.route('/users', methods=['POST'])
@login_required
@admin_required
def create_user():
    name = request.form.get('name')
    is_admin = request.form.get('is_admin') == 'on'
    base_allowance = request.form.get('base_allowance', type=float, default=0.0)

    if not name:
        flash('Name is required.', 'error')
        return redirect(url_for('admin.users'))

    user = User(
        name=name,
        is_admin=is_admin,
        base_allowance=base_allowance
    )

    if is_admin:
        email = request.form.get('email')
        password = request.form.get('password')
        if not email or not password:
            flash('Email and password required for admin users.', 'error')
            return redirect(url_for('admin.users'))
        user.email = email
        user.set_password(password)
    else:
        pin = request.form.get('pin')
        if not pin or len(pin) != 4:
            flash('4-digit PIN required for children.', 'error')
            return redirect(url_for('admin.users'))
        user.set_pin(pin)

    db.session.add(user)
    db.session.commit()

    flash(f'User "{name}" created successfully.', 'success')
    return redirect(url_for('admin.users'))


@admin_bp.route('/users/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def update_user(user_id):
    user = User.query.get_or_404(user_id)

    user.name = request.form.get('name', user.name)
    user.base_allowance = request.form.get('base_allowance', type=float, default=user.base_allowance)

    new_pin = request.form.get('pin')
    if new_pin and len(new_pin) == 4:
        user.set_pin(new_pin)

    new_password = request.form.get('password')
    if new_password and len(new_password) >= 6:
        user.set_password(new_password)

    db.session.commit()

    flash(f'User "{user.name}" updated successfully.', 'success')
    return redirect(url_for('admin.users'))


# --- Payment Management ---

@admin_bp.route('/weeks/<int:week_id>/pay/<int:child_id>', methods=['POST'])
@login_required
@admin_required
def mark_paid(week_id, child_id):
    week = WeekPeriod.query.get_or_404(week_id)
    child = User.query.get_or_404(child_id)

    if child.is_admin:
        flash('Cannot create payment for admin users.', 'error')
        return redirect(url_for('admin.index'))

    # Calculate original amount
    allowance_service = AllowanceService()
    summary = allowance_service.calculate_weekly_summary(child_id, week_id)
    original_amount = summary['total']

    # Get custom amount if provided
    custom_amount = request.form.get('amount', type=float)
    amount = custom_amount if custom_amount is not None else original_amount

    # Get notes
    notes = request.form.get('notes', '').strip() or None

    # Check for existing payment
    payment = WeeklyPayment.query.filter_by(week_id=week_id, user_id=child_id).first()

    if payment:
        payment.original_amount = original_amount
        payment.amount = amount
        payment.notes = notes
        payment.mark_as_paid()
    else:
        payment = WeeklyPayment(
            week_id=week_id,
            user_id=child_id,
            original_amount=original_amount,
            amount=amount,
            notes=notes
        )
        payment.mark_as_paid()
        db.session.add(payment)

    db.session.commit()

    # Send payment confirmation email
    try:
        email_service = EmailService()
        email_service.send_payment_confirmation(child_id, week_id, amount)
    except Exception as e:
        # Log error but don't fail the request
        import logging
        logging.error(f"Failed to send payment email: {e}")

    flash(f'Payment of £{amount:.2f} marked as paid for {child.name}.', 'success')
    return redirect(url_for('admin.index'))


@admin_bp.route('/payments')
@login_required
@admin_required
def payments():
    payments = WeeklyPayment.query.order_by(WeeklyPayment.created_at.desc()).all()
    return render_template('admin/payments.html', payments=payments)


@admin_bp.route('/test-email', methods=['POST'])
@login_required
@admin_required
def test_email():
    """Send a test email to verify email configuration."""
    try:
        email_service = EmailService()
        email_service.send_weekly_summary()
        flash('Test email sent! Check the admin email inbox.', 'success')
    except Exception as e:
        flash(f'Email failed: {str(e)}. Check MAIL_* environment variables.', 'error')
    return redirect(url_for('admin.index'))


@admin_bp.route('/toggle-chore/<int:child_id>', methods=['POST'])
@login_required
@admin_required
def toggle_child_chore(child_id):
    """Toggle a chore completion for a child (admin editing)."""
    from datetime import datetime

    assignment_id = request.form.get('assignment_id', type=int)
    date_str = request.form.get('date')
    slot = request.form.get('slot', 1, type=int)

    if not assignment_id or not date_str:
        return '', 400

    try:
        date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return '', 400

    assignment = WeeklyChoreAssignment.query.get(assignment_id)
    if not assignment or assignment.user_id != child_id:
        return '', 403

    chore = assignment.chore_definition

    # Toggle completion
    ChoreLog.toggle_completion(
        user_id=child_id,
        chore_id=chore.id,
        week_id=assignment.week_id,
        date=date,
        slot=slot,
        amount=assignment.display_amount
    )

    return '', 200
