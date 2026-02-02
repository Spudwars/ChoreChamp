from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

from app import db

settings_bp = Blueprint('settings', __name__)

# Available DiceBear avatar styles
AVATAR_STYLES = [
    {'id': 'bottts', 'name': 'Robots', 'description': 'Friendly robot avatars'},
    {'id': 'avataaars', 'name': 'Avataaars', 'description': 'Cartoon-style human avatars'},
    {'id': 'micah', 'name': 'Micah', 'description': 'Simple illustrated avatars'},
    {'id': 'lorelei', 'name': 'Lorelei', 'description': 'Artistic portrait avatars'},
    {'id': 'pixel-art', 'name': 'Pixel Art', 'description': 'Retro pixel art style'},
    {'id': 'thumbs', 'name': 'Thumbs', 'description': 'Thumbs up characters'},
    {'id': 'fun-emoji', 'name': 'Fun Emoji', 'description': 'Expressive emoji faces'},
    {'id': 'adventurer', 'name': 'Adventurer', 'description': 'Adventure character avatars'},
]


@settings_bp.route('/avatar', methods=['GET', 'POST'])
@login_required
def avatar():
    """Avatar selection page."""
    if request.method == 'POST':
        avatar_style = request.form.get('avatar_style', 'bottts')
        avatar_seed = request.form.get('avatar_seed', '').strip()

        # Validate style
        valid_styles = [s['id'] for s in AVATAR_STYLES]
        if avatar_style not in valid_styles:
            avatar_style = 'bottts'

        # Use name as default seed if empty
        if not avatar_seed:
            avatar_seed = current_user.name

        current_user.avatar_style = avatar_style
        current_user.avatar_seed = avatar_seed
        db.session.commit()

        flash('Avatar updated successfully!', 'success')
        return redirect(url_for('settings.avatar'))

    return render_template(
        'settings/avatar.html',
        avatar_styles=AVATAR_STYLES,
        current_style=current_user.avatar_style or 'bottts',
        current_seed=current_user.avatar_seed or current_user.name
    )
