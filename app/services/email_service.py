import logging
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders


logger = logging.getLogger(__name__)


class EmailService:
    def __init__(self, settings):
        self.sender = settings.EMAIL_SENDER
        self.password = settings.EMAIL_PASSWORD
        self.recipient = settings.RECIPIENT_EMAIL  # destinatario del correo

    def send_email(self, subject: str, body: str, attachment_path: str = None):
        """
        Envía un email usando SMTP.
        Aquí se implementaría la lógica para enviar el email.
        Por ejemplo, usando smtplib o una librería de terceros.
        """

        # Configuración del mensaje
        message = MIMEMultipart()
        message["From"] = self.sender
        message["To"] = self.recipient
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
                server.sendmail(self.sender, [self.recipient], message.as_string())
                logger.info(f"Correo enviado a {self.recipient} con asunto: {subject}")
        except Exception as e:
            logger.error(f"Error al enviar el correo: {e}")
