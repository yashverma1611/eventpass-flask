import json
from datetime import datetime, timedelta
from app import create_app, db
from app.models import User, Event, Registration, Attendance, Certificate
from app.certificates.utils import create_personalized_certificate

app = create_app()

def seed():
    with app.app_context():
        db.create_all()

        # Check if already seeded
        if User.query.filter_by(email='admin@eventpass.edu').first():
            print("[INFO] Database already contains initial seed data.")
            return

        print("[INFO] Seeding initial EventPass users, gate staff, events, pricing, and sample certificates...")

        # 1. Seed Users (Including Gate Staff)
        admin = User(username='Admin Danish Khan', email='admin@eventpass.edu', role='ADMIN', is_approved=True)
        admin.set_password('admin123')

        gate_staff = User(username='Officer R. K. Sharma', email='gate1@eventpass.edu', role='GATE_STAFF', is_approved=True)
        gate_staff.set_password('gate123')

        organizer = User(username='Dept. of Computer Applications', email='organizer@eventpass.edu', role='ORGANIZER', is_approved=True)
        organizer.set_password('org123')

        student1 = User(username='Sanjogita', email='sanjogita@ccm.edu.in', role='STUDENT', is_approved=True)
        student1.set_password('student123')

        student2 = User(username='Rahul Sharma', email='rahul@ccm.edu.in', role='STUDENT', is_approved=True)
        student2.set_password('student123')

        student3 = User(username='Pooja Verma', email='pooja@ccm.edu.in', role='STUDENT', is_approved=True)
        student3.set_password('student123')

        db.session.add_all([admin, gate_staff, organizer, student1, student2, student3])
        db.session.commit()

        # 2. Form schema sample
        sample_fields = [
            {"id": "fullName", "label": "Attendee Full Name", "type": "text", "required": True},
            {"id": "email", "label": "Email Address", "type": "email", "required": True},
            {"id": "phone", "label": "WhatsApp / Contact Mobile", "type": "tel", "required": True},
            {"id": "college", "label": "College / University Name", "type": "text", "required": True},
            {"id": "rollNo", "label": "Student Roll / Enrollment No", "type": "text", "required": True}
        ]

        # 3. Seed Events with Pricing, Offers & Form Schemas
        event1 = Event(
            organizer_id=organizer.id,
            title='National Python & AI Hackathon 2026',
            description='A 36-hour inter-collegiate coding hackathon focusing on generative AI, full-stack microservices, and practical machine learning solutions. Teams build, pitch, and demo to industry leaders.',
            venue='Central Auditorium & Tech Labs, City College of Management',
            date=datetime.now() + timedelta(days=5),
            category='Hackathon',
            capacity=150,
            base_price=499.0,
            discount=200.0,
            promo_code='TECH200',
            active_offer_title='Early Bird Offer: Save ₹200',
            required_fields_json=json.dumps(sample_fields)
        )

        event2 = Event(
            organizer_id=organizer.id,
            title='Spring Boot 3 & Micro-Architecture Masterclass',
            description='Comprehensive hands-on training exploring Jakarta EE, REST APIs, stateless JWT authorization, and Spring Data JPA persistence.',
            venue='Computer Lab 03, MCA Block',
            date=datetime.now() + timedelta(days=12),
            category='Workshop',
            capacity=50,
            base_price=299.0,
            discount=100.0,
            promo_code='STUDENT100',
            active_offer_title='Student Concession: ₹100 OFF',
            required_fields_json=json.dumps(sample_fields)
        )

        event3 = Event(
            organizer_id=organizer.id,
            title='Cybersecurity & Defensive Engineering Symposium',
            description='Specialized technical seminar covering OWASP Top 10 vulnerabilities, cryptographic hashing algorithms, and network forensics.',
            venue='Seminar Hall 2, Admin Block',
            date=datetime.now() - timedelta(days=2),  # Past event for certificate demo
            category='Seminar',
            capacity=80,
            base_price=199.0,
            discount=50.0,
            promo_code='CYBER50',
            active_offer_title='Special Pass: ₹50 OFF',
            required_fields_json=json.dumps(sample_fields)
        )

        db.session.add_all([event1, event2, event3])
        db.session.commit()

        # 4. Seed Registrations for Event 1 & Event 3
        reg1 = Registration(
            user_id=student1.id,
            event_id=event1.id,
            status='CONFIRMED',
            attendee_name='Sanjogita',
            attendee_email='sanjogita@ccm.edu.in',
            attendee_phone='9453193268',
            attendee_college='City College of Management',
            attendee_roll='2511755060102',
            amount_paid=299.0,
            payment_mode='UPI_QR',
            payment_ref='UPI-TXN-88192'
        )
        reg2 = Registration(
            user_id=student2.id,
            event_id=event1.id,
            status='CONFIRMED',
            attendee_name='Rahul Sharma',
            attendee_email='rahul@ccm.edu.in',
            attendee_phone='9123456789',
            attendee_college='City College of Management',
            attendee_roll='2511755060012',
            amount_paid=299.0,
            payment_mode='UPI_QR'
        )
        reg3 = Registration(
            user_id=student1.id,
            event_id=event3.id,
            status='CONFIRMED',
            attendee_name='Sanjogita',
            attendee_email='sanjogita@ccm.edu.in',
            attendee_phone='9453193268',
            attendee_college='City College of Management',
            attendee_roll='2511755060102',
            amount_paid=149.0,
            payment_mode='UPI_QR'
        )

        db.session.add_all([reg1, reg2, reg3])
        db.session.commit()

        # 5. Mark Attendance and Issue Certificate for Student 1 on Past Event 3
        att1 = Attendance(
            registration_id=reg3.id,
            is_present=True,
            marked_by=gate_staff.id,
            gate_name='Main Entrance Gate #1',
            gate_officer_name='Officer R. K. Sharma'
        )
        db.session.add(att1)
        db.session.commit()

        cert_id, pdf_path, qr_path = create_personalized_certificate(reg3)
        cert1 = Certificate(
            registration_id=reg3.id,
            cert_id=cert_id,
            pdf_file_path=pdf_path,
            qr_code_path=qr_path,
            email_status='SENT',
            download_count=1
        )
        db.session.add(cert1)
        db.session.commit()

        print(f"[SUCCESS] EventPass database successfully seeded!")
        print(f"Sample Verified Certificate generated with ID: {cert_id}")
        print("Gate Staff Login: gate1@eventpass.edu / gate123")
        print("Admin Login: admin@eventpass.edu / admin123")
        print("Student Login: sanjogita@ccm.edu.in / student123")

if __name__ == '__main__':
    seed()
