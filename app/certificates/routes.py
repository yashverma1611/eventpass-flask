import os
from flask import Blueprint, render_template, abort, redirect, url_for, flash, send_from_directory, current_app
from flask_login import login_required, current_user
from app import db
from app.models import Event, Registration, Attendance, Certificate
from app.certificates.utils import create_personalized_certificate

certs_bp = Blueprint('certificates', __name__)

@certs_bp.route('/verify/<cert_id>')
def verify_certificate(cert_id):
    """
    Public verification endpoint accessed by scanning the certificate QR code.
    Displays authentic credentials or flags invalid records.
    """
    certificate = Certificate.query.filter_by(cert_id=cert_id).first()
    if not certificate:
        return render_template('certificates/verify_failed.html', cert_id=cert_id), 404

    reg = certificate.registration
    return render_template(
        'certificates/verify_success.html',
        certificate=certificate,
        student_name=reg.student.username.title(),
        student_email=reg.student.email,
        event_title=reg.event.title,
        event_date=reg.event.date.strftime("%d %B %Y"),
        venue=reg.event.venue,
        status="AUTHENTIC & VERIFIED"
    )


@certs_bp.route('/download/<cert_id>')
def download_certificate(cert_id):
    """
    Streams and downloads the vector PDF certificate.
    """
    certificate = Certificate.query.filter_by(cert_id=cert_id).first_or_404()
    certificate.download_count += 1
    db.session.commit()

    certs_dir = os.path.join(current_app.root_path, 'static', 'certs')
    return send_from_directory(
        certs_dir,
        certificate.pdf_file_path,
        as_attachment=True,
        download_name=f"Certificate_{certificate.cert_id}.pdf"
    )


@certs_bp.route('/bulk-issue/<int:event_id>', methods=['POST'])
@login_required
def bulk_issue_certificates(event_id):
    """
    Generates personalized QR certificates for all attendees marked as present.
    """
    event = Event.query.get_or_404(event_id)
    if current_user.id != event.organizer_id and current_user.role != 'ADMIN':
        abort(403)

    # Fetch all attendees marked present who do not already have a certificate
    attended_regs = Registration.query.join(Attendance).filter(
        Registration.event_id == event.id,
        Attendance.is_present == True,
        Registration.certificate == None
    ).all()

    if not attended_regs:
        flash("No un-certified attendees marked present. Please mark attendance first.", "warning")
        return redirect(url_for('events.manage_event', event_id=event.id))

    success_count = 0
    for reg in attended_regs:
        try:
            cert_id, pdf_name, qr_name = create_personalized_certificate(reg)
            cert = Certificate(
                registration_id=reg.id,
                cert_id=cert_id,
                pdf_file_path=pdf_name,
                qr_code_path=qr_name,
                email_status='SENT'
            )
            db.session.add(cert)
            success_count += 1
        except Exception as e:
            print(f"[ERROR] Failed to generate cert for reg {reg.id}: {e}")

    db.session.commit()
    flash(f"Successfully generated {success_count} verified certificates with QR codes!", "success")
    return redirect(url_for('events.manage_event', event_id=event.id))
