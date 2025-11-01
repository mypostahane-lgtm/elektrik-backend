import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()

GMAIL_EMAIL = os.getenv('GMAIL_EMAIL')
GMAIL_APP_PASSWORD = os.getenv('GMAIL_APP_PASSWORD')
RECIPIENT_EMAIL = os.getenv('RECIPIENT_EMAIL')


def send_contact_email(name: str, phone: str, email: str, service: str, message: str):
    """
    Send contact form email via Gmail SMTP
    """
    try:
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f'Yeni Teklif Talebi - {service}'
        msg['From'] = GMAIL_EMAIL
        msg['To'] = RECIPIENT_EMAIL

        # Create HTML content
        html_content = f"""
        <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background-color: #1e40af; color: white; padding: 20px; text-align: center; }}
                    .content {{ background-color: #f3f4f6; padding: 20px; }}
                    .field {{ margin-bottom: 15px; }}
                    .field-label {{ font-weight: bold; color: #1e40af; }}
                    .field-value {{ margin-top: 5px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h2>⚡ Yeni Teklif Talebi</h2>
                    </div>
                    <div class="content">
                        <div class="field">
                            <div class="field-label">👤 Ad Soyad:</div>
                            <div class="field-value">{name}</div>
                        </div>
                        <div class="field">
                            <div class="field-label">📞 Telefon:</div>
                            <div class="field-value">{phone}</div>
                        </div>
                        <div class="field">
                            <div class="field-label">📧 Email:</div>
                            <div class="field-value">{email}</div>
                        </div>
                        <div class="field">
                            <div class="field-label">🔧 Hizmet:</div>
                            <div class="field-value">{service}</div>
                        </div>
                        <div class="field">
                            <div class="field-label">💬 Mesaj:</div>
                            <div class="field-value">{message}</div>
                        </div>
                    </div>
                </div>
            </body>
        </html>
        """

        # Attach HTML content
        html_part = MIMEText(html_content, 'html')
        msg.attach(html_part)

        # Send email
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(GMAIL_EMAIL, GMAIL_APP_PASSWORD)
            server.send_message(msg)

        return True
    except Exception as e:
        print(f"Email gönderme hatası: {str(e)}")
        return False

