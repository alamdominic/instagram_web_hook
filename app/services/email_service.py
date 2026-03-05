"""Email service for sending reports via SMTP."""

import logging
import os
import smtplib
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


logger = logging.getLogger(__name__)


class EmailService:
    """Send emails with optional file attachments using SMTP."""

    def __init__(self, settings):
        """Initialize the email service with configuration settings.

        Args:
            settings: Application settings object.
        """
        self.sender = settings.EMAIL_SENDER
        self.password = settings.EMAIL_PASSWORD
        self.recipients = [
            email.strip()
            for email in settings.RECIPIENT_EMAIL.split(",")
            if email.strip()
        ]

    def send_email(self, subject: str, body: str, attachment_path: str = None):
        """Send an email message using SMTP.

        Args:
            subject (str): Email subject line.
            body (str): Plain text body.
            attachment_path (str, optional): Path to attachment file.
        """

        # Configuración del mensaje
        message = MIMEMultipart()
        message["From"] = self.sender
        message["To"] = ", ".join(self.recipients)
        message["Subject"] = subject

        # Cuerpo del mensaje
        message.attach(MIMEText(body, "plain"))

        # Adjuntar archivo (log o pdf)
        if attachment_path and os.path.exists(attachment_path):
            with open(attachment_path, "rb") as attachment:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(attachment.read())

            encoders.encode_base64(part)
            part.add_header(
                "Content-Disposition",
                f"attachment; filename={os.path.basename(attachment_path)}",
            )
            message.attach(part)

        # Enviar correo
        try:
            with smtplib.SMTP("smtp.gmail.com", 587) as server:
                server.starttls()
                server.login(self.sender, self.password)
                # sendmail requiere lista de destinatarios
                server.sendmail(self.sender, self.recipients, message.as_string())
                logger.info(
                    "Correo enviado a %s destinatarios con asunto: %s",
                    len(self.recipients),
                    subject,
                )
        except Exception as e:
            logger.error(f"Error al enviar el correo: {e}")
