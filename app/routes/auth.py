from datetime import timedelta
from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, login_required, current_user

from app import db
from app.models.user import User

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        login_type = request.form.get('login_type', 'child')

        if login_type == 'child':
            # PIN-based authentication
            user_id = request.form.get('user_id')
            pin = request.form.get('pin')

            if not user_id or not pin:
                flash('Please select a user and enter your PIN.', 'error')
                return redirect(url_for('auth.login'))

            user = User.query.get(user_id)
            if user and user.is_child and user.check_pin(pin):
                login_user(user, remember=True)
                session.permanent = True
                session['session_type'] = 'child'
                return redirect(url_for('dashboard.index'))
            else:
                flash('Invalid PIN. Please try again.', 'error')
                return redirect(url_for('auth.login'))
        else:
            # Password-based authentication for adults
            email = request.form.get('email')
            password = request.form.get('password')

            if not email or not password:
                flash('Please enter your email and password.', 'error')
                return redirect(url_for('auth.login'))

            user = User.query.filter_by(email=email).first()
            if user and user.is_admin and user.check_password(password):
                login_user(user, remember=True)
                session.permanent = True
                session['session_type'] = 'adult'
                return redirect(url_for('admin.index'))
            else:
                flash('Invalid email or password.', 'error')
                return redirect(url_for('auth.login'))

    # Get children for PIN login
    children = User.query.filter_by(is_admin=False).all()
    return render_template('auth/login.html', children=children)


@auth_bp.route('/logout', methods=['GET', 'POST'])
def logout():
    """Log out the current user and clear session."""
    from flask import make_response
    logout_user()
    session.clear()
    response = make_response(redirect(url_for('auth.login')))
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response


@auth_bp.route('/pin-pad')
def pin_pad():
    """HTMX endpoint to render PIN pad for selected child."""
    user_id = request.args.get('user_id')
    if not user_id:
        return ''
    user = User.query.get(user_id)
    if not user or user.is_admin:
        return ''
    return render_template('auth/partials/pin_pad.html', user=user)
