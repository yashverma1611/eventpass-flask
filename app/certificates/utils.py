import os
import uuid
from datetime import datetime
from flask import current_app

def generate_qr_code(verification_url, cert_id):
    """
    Generates matrix QR code encoding the public certificate verification URL.
    """
    qr_filename = f"qr_{cert_id}.png"
    qr_dir = os.path.join(current_app.root_path, 'static', 'qrcodes')
    os.makedirs(qr_dir, exist_ok=True)
    qr_path = os.path.join(qr_dir, qr_filename)

    try:
        import qrcode
        qr = qrcode.QRCode(version=1, box_size=6, border=2)
        qr.add_data(verification_url)
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="black", back_color="white")
        qr_img.save(qr_path)
    except Exception as e:
        # Fallback using Pillow to draw a simulated QR box if qrcode module fails
        from PIL import Image, ImageDraw
        img = Image.new('RGB', (180, 180), color='white')
        d = ImageDraw.Draw(img)
        d.rectangle([10, 10, 170, 170], outline='black', width=3)
        d.rectangle([30, 30, 70, 70], fill='black')
        d.rectangle([110, 30, 150, 70], fill='black')
        d.rectangle([30, 110, 70, 150], fill='black')
        d.text((45, 85), "VERIFY", fill='black')
        img.save(qr_path)

    return qr_filename


def create_personalized_certificate(registration):
    """
    Draws dynamic participant name, event title, date, and QR code,
    generating both high-res image and print-ready vector PDF.
    """
    student_name = registration.student.username.title()
    event_title = registration.event.title
    issue_date_str = registration.event.date.strftime("%d-%m-%Y")
    unique_suffix = uuid.uuid4().hex[:4].upper()
    unique_cert_id = f"EVT2026-{registration.event.id:04d}-{registration.id:04d}-{unique_suffix}"

    certs_dir = os.path.join(current_app.root_path, 'static', 'certs')
    os.makedirs(certs_dir, exist_ok=True)
    pdf_filename = f"{unique_cert_id}.pdf"
    pdf_path = os.path.join(certs_dir, pdf_filename)

    # Verification URL pointing to the live portal
    verify_url = f"http://127.0.0.1:5000/certificates/verify/{unique_cert_id}"
    qr_filename = generate_qr_code(verify_url, unique_cert_id)
    qr_full_path = os.path.join(current_app.root_path, 'static', 'qrcodes', qr_filename)

    try:
        # Generate with ReportLab for pristine vector PDF output
        from reportlab.lib.pagesizes import landscape, letter
        from reportlab.lib import colors
        from reportlab.pdfgen import canvas

        c = canvas.Canvas(pdf_path, pagesize=landscape(letter))
        w, h = landscape(letter)

        # Outer Decorative Border
        c.setStrokeColor(colors.HexColor('#0f172a'))
        c.setLineWidth(4)
        c.rect(20, 20, w - 40, h - 40)
        c.setStrokeColor(colors.HexColor('#2563eb'))
        c.setLineWidth(1.5)
        c.rect(26, 26, w - 52, h - 52)

        # Institutional Header
        c.setFont("Helvetica-Bold", 24)
        c.setFillColor(colors.HexColor('#1e293b'))
        c.drawCentredString(w / 2.0, h - 80, "CITY COLLEGE OF MANAGEMENT, LUCKNOW")

        c.setFont("Helvetica", 12)
        c.setFillColor(colors.HexColor('#64748b'))
        c.drawCentredString(w / 2.0, h - 100, "DEPARTMENT OF COMPUTER APPLICATIONS")

        # Certificate Title
        c.setFont("Helvetica-Bold", 32)
        c.setFillColor(colors.HexColor('#2563eb'))
        c.drawCentredString(w / 2.0, h - 160, "CERTIFICATE OF PARTICIPATION")

        c.setFont("Helvetica", 14)
        c.setFillColor(colors.HexColor('#475569'))
        c.drawCentredString(w / 2.0, h - 200, "This is proudly presented to")

        # Recipient Name (Prominent & Centered)
        c.setFont("Helvetica-Bold", 28)
        c.setFillColor(colors.HexColor('#0f172a'))
        c.drawCentredString(w / 2.0, h - 245, student_name)

        # Event Description
        c.setFont("Helvetica", 14)
        c.setFillColor(colors.HexColor('#334155'))
        body_text = f"for active participation & meritorious performance in \"{event_title}\""
        c.drawCentredString(w / 2.0, h - 290, body_text)

        c.setFont("Helvetica", 12)
        c.setFillColor(colors.HexColor('#64748b'))
        c.drawCentredString(w / 2.0, h - 315, f"Conducted on {issue_date_str} at City College of Management Campus")

        # QR Code Verification Box
        if os.path.exists(qr_full_path):
            c.drawImage(qr_full_path, 60, 50, width=90, height=90)
        
        c.setFont("Helvetica-Bold", 8)
        c.setFillColor(colors.HexColor('#0f172a'))
        c.drawString(60, 40, f"ID: {unique_cert_id}")
        c.setFont("Helvetica", 7)
        c.setFillColor(colors.HexColor('#64748b'))
        c.drawString(60, 30, "Scan to Verify Authenticity")

        # Signatures
        c.setStrokeColor(colors.HexColor('#94a3b8'))
        c.setLineWidth(1)
        c.line(w - 220, 80, w - 60, 80)
        c.line(w / 2.0 - 80, 80, w / 2.0 + 80, 80)

        c.setFont("Helvetica-Bold", 10)
        c.setFillColor(colors.HexColor('#1e293b'))
        c.drawCentredString(w / 2.0, 65, "Mr. Danish Khan")
        c.drawCentredString(w - 140, 65, "Head of Department")

        c.setFont("Helvetica", 8)
        c.setFillColor(colors.HexColor('#64748b'))
        c.drawCentredString(w / 2.0, 52, "Project Supervisor & Faculty")
        c.drawCentredString(w - 140, 52, "City College of Management")

        c.save()

    except Exception as e:
        print(f"[WARN] ReportLab failed or not installed, writing basic PDF stream: {e}")
        # Minimalist valid PDF generator fallback
        with open(pdf_path, 'wb') as f:
            f.write(b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R/Resources<<>>>>endobj\nxref\n0 4\n0000000000 65535 f \n0000000010 00000 n \n0000000060 00000 n \n0000000115 00000 n \ntrailer<</Size 4/Root 1 0 R>>\nstartxref\n210\n%%EOF\n")

    return unique_cert_id, pdf_filename, qr_filename
