import json
from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request, abort, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import Event, Registration, Attendance
from app.auth.routes import role_required

events_bp = Blueprint('events', __name__)

@events_bp.route('/')
def list_events():
    search = request.args.get('search', '').strip()
    category = request.args.get('category', '').strip()

    query = Event.query.filter_by(is_active=True)
    if search:
        query = query.filter(Event.title.ilike(f'%{search}%') | Event.description.ilike(f'%{search}%'))
    if category and category != 'All':
        query = query.filter_by(category=category)

    events = query.order_by(Event.date.asc()).all()
    categories = ['All', 'Hackathon', 'Workshop', 'Seminar', 'Conference', 'Cultural']

    return render_template('events/index.html', events=events, categories=categories, selected_category=category, search=search)


@events_bp.route('/<int:event_id>')
def event_detail(event_id):
    event = Event.query.get_or_404(event_id)
    is_registered = False
    user_reg = None
    if current_user.is_authenticated:
        user_reg = Registration.query.filter_by(user_id=current_user.id, event_id=event.id, status='CONFIRMED').first()
        is_registered = bool(user_reg)

    form_fields = event.get_form_fields()
    return render_template('events/event_detail.html', event=event, is_registered=is_registered, user_reg=user_reg, form_fields=form_fields)


@events_bp.route('/create', methods=['GET', 'POST'])
@login_required
@role_required('ORGANIZER', 'ADMIN')
def create_event():
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        venue = request.form.get('venue', '').strip()
        date_str = request.form.get('date', '')
        category = request.form.get('category', 'Workshop')
        capacity = int(request.form.get('capacity', 100))
        
        # Pricing & Offers Controls (Admin Authority)
        base_price = float(request.form.get('base_price', 0.0) or 0.0)
        discount = float(request.form.get('discount', 0.0) or 0.0)
        promo_code = request.form.get('promo_code', '').strip().upper()
        active_offer_title = request.form.get('active_offer_title', '').strip()

        # Admin-Issued Attendee Registration Form Schema
        issued_fields = [
            {"id": "fullName", "label": "Attendee Full Name", "type": "text", "required": True},
            {"id": "email", "label": "Email Address", "type": "email", "required": True}
        ]
        if request.form.get('field_phone'):
            issued_fields.append({"id": "phone", "label": "WhatsApp / Contact Mobile", "type": "tel", "required": True})
        if request.form.get('field_college'):
            issued_fields.append({"id": "college", "label": "College / University Name", "type": "text", "required": True})
        if request.form.get('field_roll'):
            issued_fields.append({"id": "rollNo", "label": "Student Roll / Enrollment No", "type": "text", "required": True})
        if request.form.get('field_dept'):
            issued_fields.append({"id": "department", "label": "Academic Dept & Semester", "type": "text", "required": True})

        if not title or not description or not venue or not date_str:
            flash("All mandatory fields must be completed.", "danger")
            return render_template('events/create_event.html')

        try:
            event_date = datetime.strptime(date_str, '%Y-%m-%dT%H:%M')
        except ValueError:
            event_date = datetime.now()

        event = Event(
            organizer_id=current_user.id,
            title=title,
            description=description,
            venue=venue,
            date=event_date,
            category=category,
            capacity=capacity,
            base_price=base_price,
            discount=discount,
            promo_code=promo_code,
            active_offer_title=active_offer_title or f"Save ₹{discount:.0f} with code {promo_code}",
            required_fields_json=json.dumps(issued_fields)
        )
        db.session.add(event)
        db.session.commit()

        flash(f"Event '{title}' published successfully with custom pricing & attendee form!", "success")
        return redirect(url_for('events.event_detail', event_id=event.id))

    return render_template('events/create_event.html')


@events_bp.route('/gate/check-in', methods=['GET', 'POST'])
@login_required
def gate_check_in():
    """
    Main Entrance Gate Staff Check-In Panel.
    Validates pass code and explicitly shows WHICH EVENT the visitor came for.
    """
    if current_user.role not in ['GATE_STAFF', 'ORGANIZER', 'ADMIN']:
        flash("Access restricted to authorized entrance gate officers.", "danger")
        return redirect(url_for('events.list_events'))

    verification_result = None
    pass_code = ""

    if request.method == 'POST':
        pass_code = request.form.get('pass_code', '').strip().upper()
        # Handle QR payload format: "EVENTPASS:CODE:NAME:EVENTID"
        if pass_code.startswith("EVENTPASS:"):
            parts = pass_code.split(":")
            if len(parts) >= 2:
                pass_code = parts[1]

        reg = Registration.query.filter_by(reg_number=pass_code).first()

        if not reg:
            verification_result = {
                "status": "INVALID",
                "message": f"Pass Code '{pass_code}' was not found in the university database.",
                "event_title": None,
                "attendee_name": None
            }
        else:
            # Check attendance state
            att = Attendance.query.filter_by(registration_id=reg.id).first()
            if att and att.is_present:
                # ALREADY ADMITTED
                verification_result = {
                    "status": "ALREADY_CHECKED_IN",
                    "message": "Visitor was already admitted previously! Potential ticket duplication.",
                    "event_title": reg.event.title,
                    "event_venue": reg.event.venue,
                    "event_date": reg.event.date.strftime('%b %d, %Y • %I:%M %p'),
                    "attendee_name": reg.attendee_name or reg.student.username,
                    "attendee_college": reg.attendee_college or "Registered Student",
                    "checked_in_at": att.marked_at.strftime('%I:%M %p'),
                    "gate_officer": att.gate_officer_name or "Gate Staff"
                }
            else:
                # FIRST TIME VALID ADMISSION
                if not att:
                    att = Attendance(
                        registration_id=reg.id,
                        is_present=True,
                        marked_by=current_user.id,
                        gate_name="Main Entrance Gate #1",
                        gate_officer_name=current_user.username
                    )
                    db.session.add(att)
                else:
                    att.is_present = True
                    att.marked_at = datetime.utcnow()
                    att.marked_by = current_user.id
                    att.gate_officer_name = current_user.username

                db.session.commit()
                verification_result = {
                    "status": "ADMITTED",
                    "message": "Valid Pass Confirmed. Admission Granted.",
                    "event_title": reg.event.title,
                    "event_venue": reg.event.venue,
                    "event_date": reg.event.date.strftime('%b %d, %Y • %I:%M %p'),
                    "attendee_name": reg.attendee_name or reg.student.username,
                    "attendee_college": reg.attendee_college or "Registered Student",
                    "attendee_roll": reg.attendee_roll or "N/A",
                    "checked_in_at": att.marked_at.strftime('%I:%M %p'),
                    "gate_officer": current_user.username
                }

    # Fetch recent gate admissions
    recent_admissions = Attendance.query.filter_by(is_present=True).order_by(Attendance.marked_at.desc()).limit(15).all()

    return render_template(
        'events/gate_check_in.html',
        verification_result=verification_result,
        pass_code=pass_code,
        recent_admissions=recent_admissions
    )
