import base64
from email.message import EmailMessage
import io
import smtplib
import qrcode
from sqlalchemy.orm import Session

from ..helpers import models, schemas


def create(db: Session, qcode: schemas.QR_CodeCreate):
    db_qrcode = models.QR_Code(qcode)
    db.add(db_qrcode)
    db.commit()
    db.refresh(db_qrcode)
    return db_qrcode


def delete(db: Session, identifiant: int):
    return db.query(models.QR_Code).filter(models.QR_Code.id == identifiant).delete()

def get_by_data(db: Session, data: str):
    return db.query(models.QR_Code).filter(models.QR_Code.data == data).first()


def generate_qr_code(data: str) -> bytes:
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    # Add data to the QR code
    qr.add_data(data)
    qr.make(fit=True)
    
    # Create a bute buffer to store the image data
    img_buffer = io.BytesIO()
    
    # Save the QR code as a PNG image(adjest format if needed)
    qr.make_image(fill_color="black", back_color="white").save(img_buffer, format="PNG")
    img_buffer.seek(0)
    
    return img_buffer.getvalue()


def send_email(to_email: str, qr_code_image: bytes):
    # Create the email content
    msg = EmailMessage()
    msg['Subject'] = 'Votre Code QR'
    msg["From"] = 'admin@pearl.com'
    msg["To"] = to_email
    msg.set_content("Bonjour, voici votre code QR")
    
    # Attach the QR code image to the email
    # qr_code_bas64 = base64.b64encode(qr_code_image).decode('ascii')
    msg.add_attachment(qr_code_image, maintype="image", subtype="png", filename="qr_code.png")
    
    try:
        smtp_server = 'smtp-srv.pearl.com'
        smtp_port = 25
        smtp_user = 'steevi'
        smtp_password = 'tozlife3'

        with smtplib.SMTP(smtp_server, smtp_port) as server:
            # server.starttls()  # Secure the connection
            server.login(smtp_user, smtp_password)
            server.send_message(msg)
            print("Email sent successfully!")
    except Exception as e:
        print(f"Failed to send email: {e}")