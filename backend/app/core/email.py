"""
Email notification service for LibreWork
Supports multiple email providers: SendGrid, SMTP, Resend
"""
from typing import Optional, Dict, Any
import os
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Email templates
RESERVATION_CONFIRMATION_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #4F46E5; color: white; padding: 20px; text-align: center; }}
        .content {{ background-color: #f9f9f9; padding: 20px; margin: 20px 0; }}
        .details {{ background-color: white; padding: 15px; border-left: 4px solid #4F46E5; margin: 15px 0; }}
        .code {{ font-size: 24px; font-weight: bold; color: #4F46E5; text-align: center; padding: 15px; background-color: #f0f0f0; }}
        .footer {{ text-align: center; color: #666; font-size: 12px; padding: 20px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Reservation Confirmed!</h1>
        </div>
        <div class="content">
            <p>Hi {user_name},</p>
            <p>Your reservation has been confirmed. Here are the details:</p>
            
            <div class="details">
                <p><strong>Establishment:</strong> {establishment_name}</p>
                <p><strong>Space:</strong> {space_name}</p>
                <p><strong>Date:</strong> {date}</p>
                <p><strong>Time:</strong> {start_time} - {end_time}</p>
                <p><strong>Credits Charged:</strong> {credits}</p>
            </div>
            
            <p><strong>Your Validation Code:</strong></p>
            <div class="code">{validation_code}</div>
            
            <p>Show this code when you arrive at the establishment.</p>
        </div>
        <div class="footer">
            <p>LibreWork - Find Your Perfect Space</p>
            <p>© {year} LibreWork. All rights reserved.</p>
        </div>
    </div>
</body>
</html>
"""

CANCELLATION_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #EF4444; color: white; padding: 20px; text-align: center; }}
        .content {{ background-color: #f9f9f9; padding: 20px; margin: 20px 0; }}
        .footer {{ text-align: center; color: #666; font-size: 12px; padding: 20px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Reservation Cancelled</h1>
        </div>
        <div class="content">
            <p>Hi {user_name},</p>
            <p>Your reservation has been cancelled:</p>
            <p><strong>Establishment:</strong> {establishment_name}</p>
            <p><strong>Date & Time:</strong> {datetime}</p>
            <p><strong>Credits Refunded:</strong> {refund}</p>
        </div>
        <div class="footer">
            <p>LibreWork - Find Your Perfect Space</p>
        </div>
    </div>
</body>
</html>
"""

REMINDER_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #10B981; color: white; padding: 20px; text-align: center; }}
        .content {{ background-color: #f9f9f9; padding: 20px; margin: 20px 0; }}
        .footer {{ text-align: center; color: #666; font-size: 12px; padding: 20px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Upcoming Reservation Reminder</h1>
        </div>
        <div class="content">
            <p>Hi {user_name},</p>
            <p>This is a friendly reminder about your upcoming reservation:</p>
            <p><strong>Establishment:</strong> {establishment_name}</p>
            <p><strong>Time:</strong> {time}</p>
            <p><strong>Validation Code:</strong> {validation_code}</p>
        </div>
        <div class="footer">
            <p>LibreWork - Find Your Perfect Space</p>
        </div>
    </div>
</body>
</html>
"""


class EmailService:
    """Email service supporting multiple providers."""
    
    def __init__(self):
        self.provider = os.getenv("EMAIL_PROVIDER", "smtp")  # smtp, sendgrid, resend
        self.from_email = os.getenv("EMAIL_FROM", "noreply@librework.app")
        self.from_name = os.getenv("EMAIL_FROM_NAME", "LibreWork")
        
        # Provider-specific config
        if self.provider == "sendgrid":
            self.api_key = os.getenv("SENDGRID_API_KEY")
        elif self.provider == "smtp":
            self.smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
            self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
            self.smtp_user = os.getenv("SMTP_USER")
            self.smtp_password = os.getenv("SMTP_PASSWORD")
        elif self.provider == "resend":
            self.api_key = os.getenv("RESEND_API_KEY")
    
    def send_email(self, to_email: str, subject: str, html_content: str) -> bool:
        """Send email using configured provider."""
        try:
            if self.provider == "sendgrid":
                return self._send_sendgrid(to_email, subject, html_content)
            elif self.provider == "smtp":
                return self._send_smtp(to_email, subject, html_content)
            elif self.provider == "resend":
                return self._send_resend(to_email, subject, html_content)
            else:
                print(f"Unknown email provider: {self.provider}")
                return False
        except Exception as e:
            print(f"Error sending email: {e}")
            return False
    
    def _send_smtp(self, to_email: str, subject: str, html_content: str) -> bool:
        """Send via SMTP."""
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = f"{self.from_name} <{self.from_email}>"
        msg['To'] = to_email
        
        html_part = MIMEText(html_content, 'html')
        msg.attach(html_part)
        
        with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
            server.starttls()
            if self.smtp_user and self.smtp_password:
                server.login(self.smtp_user, self.smtp_password)
            server.send_message(msg)
        
        return True
    
    def _send_sendgrid(self, to_email: str, subject: str, html_content: str) -> bool:
        """Send via SendGrid."""
        from sendgrid import SendGridAPIClient
        from sendgrid.helpers.mail import Mail
        
        message = Mail(
            from_email=self.from_email,
            to_emails=to_email,
            subject=subject,
            html_content=html_content
        )
        
        sg = SendGridAPIClient(self.api_key)
        response = sg.send(message)
        return response.status_code in [200, 202]
    
    def _send_resend(self, to_email: str, subject: str, html_content: str) -> bool:
        """Send via Resend."""
        import requests
        
        response = requests.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            },
            json={
                "from": f"{self.from_name} <{self.from_email}>",
                "to": [to_email],
                "subject": subject,
                "html": html_content
            }
        )
        return response.status_code == 200
    
    def send_reservation_confirmation(self, user_data: Dict[str, Any], reservation_data: Dict[str, Any]) -> bool:
        """Send reservation confirmation email."""
        html = RESERVATION_CONFIRMATION_TEMPLATE.format(
            user_name=user_data.get("full_name", "User"),
            establishment_name=reservation_data["establishment_name"],
            space_name=reservation_data["space_name"],
            date=reservation_data["date"],
            start_time=reservation_data["start_time"],
            end_time=reservation_data["end_time"],
            credits=reservation_data["credits"],
            validation_code=reservation_data["validation_code"],
            year=datetime.now().year
        )
        
        return self.send_email(
            to_email=user_data["email"],
            subject="Reservation Confirmed - LibreWork",
            html_content=html
        )
    
    def send_cancellation(self, user_data: Dict[str, Any], reservation_data: Dict[str, Any]) -> bool:
        """Send cancellation email."""
        html = CANCELLATION_TEMPLATE.format(
            user_name=user_data.get("full_name", "User"),
            establishment_name=reservation_data["establishment_name"],
            datetime=reservation_data["datetime"],
            refund=reservation_data.get("refund", 0)
        )
        
        return self.send_email(
            to_email=user_data["email"],
            subject="Reservation Cancelled - LibreWork",
            html_content=html
        )
    
    def send_reminder(self, user_data: Dict[str, Any], reservation_data: Dict[str, Any]) -> bool:
        """Send reservation reminder."""
        html = REMINDER_TEMPLATE.format(
            user_name=user_data.get("full_name", "User"),
            establishment_name=reservation_data["establishment_name"],
            time=reservation_data["time"],
            validation_code=reservation_data["validation_code"]
        )
        
        return self.send_email(
            to_email=user_data["email"],
            subject="Upcoming Reservation Reminder - LibreWork",
            html_content=html
        )


# Global email service instance
email_service = EmailService()

