from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from app.models import User, Event, Registration, Certificate
from app.auth.routes import role_required

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/dashboard')
@login_required
@role_required('ADMIN')
def dashboard():
    total_users = User.query.count()
    total_events = Event.query.count()
    total_registrations = Registration.query.filter_by(status='CONFIRMED').count()
    total_certs = Certificate.query.count()

    pending_organizers = User.query.filter_by(role='ORGANIZER', is_approved=False).all()
    recent_events = Event.query.order_by(Event.created_at.desc()).limit(5).all()

    return render_template(
        'admin/dashboard.html',
        total_users=total_users,
        total_events=total_events,
        total_registrations=total_registrations,
        total_certs=total_certs,
        pending_organizers=pending_organizers,
        recent_events=recent_events
    )


@admin_bp.route('/approve-organizer/<int:user_id>', methods=['POST'])
@login_required
@role_required('ADMIN')
def approve_organizer(user_id):
    user = User.query.get_or_404(user_id)
    user.is_approved = True
    db.session.commit()
    flash(f"Organizer account for {user.username} has been approved!", "success")
    return redirect(url_for('admin.dashboard'))
