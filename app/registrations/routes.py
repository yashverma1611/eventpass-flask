from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.models import Event, Registration
import json

reg_bp = Blueprint('registrations', __name__)

@reg_bp.route('/register/<int:event_id>', methods=['POST'])
@login_required
def register_for_event(event_id):
    event = Event.query.filter_by(id=event_id, is_active=True).first_or_404()

    # Step 1: Duplicate Registration Guard
    existing_reg = Registration.query.filter_by(user_id=current_user.id, event_id=event.id).first()
    if existing_reg:
        flash("You are already registered for this event.", "warning")
        return redirect(url_for('events.event_detail', event_id=event.id))

    # Step 2: Capacity Ceiling Validation (Real-Time Seats)
    confirmed_count = Registration.query.filter_by(event_id=event.id, status='CONFIRMED').count()
    if confirmed_count >= event.capacity:
        flash("Registration Closed: This event has reached its maximum seat capacity.", "danger")
        return redirect(url_for('events.event_detail', event_id=event.id))

    # Step 3: Capture Dynamic Attendee Information Form
    attendee_name = request.form.get('fullName', current_user.username).strip()
    attendee_email = request.form.get('email', current_user.email).strip()
    attendee_phone = request.form.get('phone', '').strip()
    attendee_college = request.form.get('college', 'City College of Management').strip()
    attendee_roll = request.form.get('rollNo', '').strip()

    # Step 4: Process Pricing, Promo Codes & Payment Selection
    applied_promo = request.form.get('promo_code', '').strip().upper()
    discount_amount = 0.0
    if applied_promo and event.promo_code and applied_promo == event.promo_code.upper():
        discount_amount = event.discount

    final_price = max(0.0, event.base_price - discount_amount)
    payment_mode = request.form.get('payment_mode', 'UPI_QR')
    payment_ref = request.form.get('payment_ref', 'UPI-AUTO-SETTLED')

    # Step 5: Atomic Registration Creation
    new_reg = Registration(
        user_id=current_user.id,
        event_id=event.id,
        status='CONFIRMED',
        attendee_name=attendee_name,
        attendee_email=attendee_email,
        attendee_phone=attendee_phone,
        attendee_college=attendee_college,
        attendee_roll=attendee_roll,
        amount_paid=final_price,
        payment_mode=payment_mode,
        payment_ref=payment_ref
    )
    db.session.add(new_reg)
    db.session.commit()

    flash(f"Pass Confirmed! Successfully registered for '{event.title}'. Pass Code: {new_reg.reg_number}", "success")
    return redirect(url_for('registrations.my_events'))


@reg_bp.route('/my-events')
@login_required
def my_events():
    user_registrations = Registration.query.filter_by(user_id=current_user.id).order_by(Registration.registered_at.desc()).all()
    return render_template('registrations/my_events.html', registrations=user_registrations)


@reg_bp.route('/cancel/<int:reg_id>', methods=['POST'])
@login_required
def cancel_registration(reg_id):
    reg = Registration.query.get_or_404(reg_id)
    if reg.user_id != current_user.id:
        flash("Unauthorized action.", "danger")
        return redirect(url_for('registrations.my_events'))

    reg.status = 'CANCELLED'
    db.session.commit()
    flash(f"Registration for '{reg.event.title}' has been cancelled.", "info")
    return redirect(url_for('registrations.my_events'))
