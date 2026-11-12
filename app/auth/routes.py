from functools import wraps
from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models import User

auth_bp = Blueprint('auth', __name__)

def role_required(*allowed_roles):
    """Decorator ensuring only users with specified roles can access the endpoint."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('auth.login', next=request.url))
            if current_user.role not in allowed_roles and current_user.role != 'ADMIN':
                flash("Access denied: You do not possess the required permissions.", "danger")
                abort(403)
            if current_user.role == 'ORGANIZER' and not current_user.is_approved:
                flash("Your organizer account is pending administrative approval.", "warning")
                return redirect(url_for('auth.pending_approval'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('events.list_events'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        role = request.form.get('role', 'STUDENT')

        if not username or not email or not password:
            flash("All fields are required.", "danger")
            return render_template('auth/register.html')

        if User.query.filter_by(email=email).first():
            flash("An account with this email already exists.", "warning")
            return render_template('auth/register.html')

        is_approved = True if role == 'STUDENT' else False

        user = User(
            username=username,
            email=email,
            role=role,
            is_approved=is_approved
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        if role == 'ORGANIZER':
            flash("Registration successful! Your organizer account is awaiting admin approval.", "info")
            return redirect(url_for('auth.login'))

        flash("Registration successful! Please log in.", "success")
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('events.list_events'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        remember = bool(request.form.get('remember'))

        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user, remember=remember)
            flash(f"Welcome back, {user.username}!", "success")
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('events.list_events'))

        flash("Invalid email or password. Please try again.", "danger")

    return render_template('auth/login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash("You have been securely logged out.", "info")
    return redirect(url_for('auth.login'))


@auth_bp.route('/pending-approval')
@login_required
def pending_approval():
    return render_template('auth/pending_approval.html')
