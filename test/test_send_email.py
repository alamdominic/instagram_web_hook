"""Tests for EmailService SMTP behavior."""

from email import message_from_string
from unittest.mock import MagicMock, patch
from app.services.email_service import EmailService
from app.config.settings import settings


def _extract_message_from_sendmail(mock_server):
    """Extract the MIME message passed to sendmail.

    Args:
        mock_server: Mocked SMTP server.

    Returns:
        email.message.Message: Parsed email message.
    """
    args, _ = mock_server.sendmail.call_args
    return message_from_string(args[2])


def _parse_recipients(value: str):
    """Parse comma-separated recipients into a list.

    Args:
        value (str): Comma-separated recipients.

    Returns:
        list[str]: Cleaned email addresses.
    """
    return [email.strip() for email in value.split(",") if email.strip()]


def test_send_email_without_attachment():
    """Validate SMTP call without attachments."""
    email_service = EmailService(settings)

    with patch("smtplib.SMTP") as mock_smtp:
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        email_service.send_email("Asunto de prueba", "Cuerpo del mensaje")

        mock_server.login.assert_called_once_with(
            settings.EMAIL_SENDER, settings.EMAIL_PASSWORD
        )
        assert mock_server.sendmail.called

        message = _extract_message_from_sendmail(mock_server)
        assert message.get("To") == ", ".join(
            _parse_recipients(settings.RECIPIENT_EMAIL)
        )
        assert message.get("Subject") == "Asunto de prueba"
        assert message.get_content_type() == "multipart/mixed"


def test_send_email_with_attachment(tmp_path):
    """Validate SMTP call with an attachment.

    Args:
        tmp_path: Pytest temp path fixture.
    """
    email_service = EmailService(settings)

    attachment_path = tmp_path / "reporte.txt"
    attachment_path.write_text("contenido de prueba", encoding="utf-8")

    with patch("smtplib.SMTP") as mock_smtp:
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        email_service.send_email(
            "Asunto con adjunto",
            "Cuerpo del mensaje",
            attachment_path=str(attachment_path),
        )

        mock_server.login.assert_called_once_with(
            settings.EMAIL_SENDER, settings.EMAIL_PASSWORD
        )
        assert mock_server.sendmail.called

        message = _extract_message_from_sendmail(mock_server)
        filenames = [part.get_filename() for part in message.walk()]
        assert "reporte.txt" in filenames
