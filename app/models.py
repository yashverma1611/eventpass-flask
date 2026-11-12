from datetime import datetime
import uuid
import json
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db, login_manager

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default='STUDENT', nullable=False)  # STUDENT, ORGANIZER, GATE_STAFF, ADMIN
    is_approved = db.Column(db.BooleanField, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    organized_events = db.relationship('Event', backref='organizer', lazy=True)
    registrations = db.relationship('Registration', backref='student', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def is_organizer(self):
        return self.role in ['ORGANIZER', 'ADMIN']

    def is_admin(self):
        return self.role == 'ADMIN'

    def is_gate_staff(self):
        return self.role in ['GATE_STAFF', 'ORGANIZER', 'ADMIN']

    def __repr__(self):
        return f'<User {self.username} [{self.role}]>'


class Event(db.Model):
    __tablename__ = 'events'

    id = db.Column(db.Integer, primary_key=True)
    organizer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    venue = db.Column(db.String(150), nullable=False)
    category = db.Column(db.String(50), default='Workshop')  # Hackathon, Workshop, Seminar, Cultural
    capacity = db.Column(db.Integer, default=100, nullable=False)
    
    # Pricing & Offers Controls (Admin Authority)
    base_price = db.Column(db.Float, default=0.0, nullable=False)
    discount = db.Column(db.Float, default=0.0, nullable=False)
    promo_code = db.Column(db.String(50), nullable=True)
    active_offer_title = db.Column(db.String(150), nullable=True)
    
    # Custom Information Form Schema issued at publishing
    required_fields_json = db.Column(db.Text, default='[]')  # JSON array of field configurations

    banner_image = db.Column(db.String(200), default='default_banner.jpg')
    cert_template_path = db.Column(db.String(200), default='default_template.png')
    is_active = db.Column(db.BooleanField, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    registrations = db.relationship('Registration', backref='event', cascade='all, delete-orphan', lazy=True)

    @property
    def final_price(self):
        return max(0.0, self.base_price - self.discount)

    @property
    def confirmed_count(self):
        return len([r for r in self.registrations if r.status == 'CONFIRMED'])

    @property
    def available_seats(self):
        return max(0, self.capacity - self.confirmed_count)

    @property
    def capacity_percentage(self):
        if self.capacity == 0:
            return 100
        return min(100, int((self.confirmed_count / self.capacity) * 100))

    def get_form_fields(self):
        try:
            return json.loads(self.required_fields_json) if self.required_fields_json else []
        except Exception:
            return []

    def __repr__(self):
        return f'<Event {self.title}>'


class Registration(db.Model):
    __tablename__ = 'registrations'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey('events.id'), nullable=False)
    reg_number = db.Column(db.String(36), unique=True, default=lambda: f"EVT-PASS-{str(uuid.uuid4())[:6].upper()}")
    status = db.Column(db.String(20), default='CONFIRMED')  # CONFIRMED, CANCELLED
    
    # Attendee info captured from admin-issued form
    attendee_name = db.Column(db.String(100), nullable=True)
    attendee_email = db.Column(db.String(120), nullable=True)
    attendee_phone = db.Column(db.String(20), nullable=True)
    attendee_college = db.Column(db.String(150), nullable=True)
    attendee_roll = db.Column(db.String(50), nullable=True)
    custom_responses_json = db.Column(db.Text, default='{}')

    # Settlement details
    amount_paid = db.Column(db.Float, default=0.0)
    payment_mode = db.Column(db.String(30), default='UPI_QR')  # UPI_QR, CARD, FREE
    payment_ref = db.Column(db.String(100), nullable=True)

    registered_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('user_id', 'event_id', name='uq_user_event_registration'),
    )

    attendance = db.relationship('Attendance', backref='registration', uselist=False, cascade='all, delete-orphan')
    certificate = db.relationship('Certificate', backref='registration', uselist=False, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Registration {self.reg_number} - Event {self.event_id}>'


class Attendance(db.Model):
    __tablename__ = 'attendance'

    id = db.Column(db.Integer, primary_key=True)
    registration_id = db.Column(db.Integer, db.ForeignKey('registrations.id'), unique=True, nullable=False)
    is_present = db.Column(db.BooleanField, default=False)
    marked_at = db.Column(db.DateTime, default=datetime.utcnow)
    marked_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    gate_name = db.Column(db.String(50), default='Main Gate #1 Entrance')
    gate_officer_name = db.Column(db.String(100), default='Officer R. K. Sharma')

    def __repr__(self):
        return f'<Attendance Reg:{self.registration_id} Present:{self.is_present} Gate:{self.gate_name}>'


class Certificate(db.Model):
    __tablename__ = 'certificates'

    id = db.Column(db.Integer, primary_key=True)
    registration_id = db.Column(db.Integer, db.ForeignKey('registrations.id'), unique=True, nullable=False)
    cert_id = db.Column(db.String(50), unique=True, nullable=False)  # e.g., EVT2026-0001-A9F2
    pdf_file_path = db.Column(db.String(255), nullable=False)
    qr_code_path = db.Column(db.String(255), nullable=False)
    issue_date = db.Column(db.Date, default=datetime.utcnow().date)
    email_status = db.Column(db.String(20), default='SENT')  # SENT, FAILED, PENDING
    download_count = db.Column(db.Integer, default=0)

    def __repr__(self):
        return f'<Certificate {self.cert_id}>'
