"""Email service for sending notifications via SMTP."""

import re
from dataclasses import dataclass
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List, Optional, Union

import aiosmtplib
import structlog
from jinja2 import Template

logger = structlog.get_logger(__name__)


class EmailSendError(Exception):
    """Exception raised when email sending fails."""

    pass


@dataclass
class EmailConfig:
    """Configuration for email service."""

    smtp_host: str
    smtp_port: int
    smtp_user: str
    smtp_password: str
    smtp_from_email: str
    smtp_from_name: str = "SprintForge"
    use_tls: bool = True


class EmailService:
    """Service for sending emails using async SMTP."""

    # Email validation regex pattern
    EMAIL_PATTERN = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")

    def __init__(self, config: EmailConfig):
        """
        Initialize email service with configuration.

        Args:
            config: EmailConfig instance with SMTP settings
        """
        self.config = config

    def _validate_email(self, email: str) -> bool:
        """
        Validate email address format.

        Args:
            email: Email address to validate

        Returns:
            True if valid, False otherwise
        """
        return bool(self.EMAIL_PATTERN.match(email))

    def _validate_emails(self, emails: Union[str, List[str]]) -> None:
        """
        Validate email address(es).

        Args:
            emails: Single email or list of emails

        Raises:
            ValueError: If any email is invalid
        """
        email_list = [emails] if isinstance(emails, str) else emails

        for email in email_list:
            if not self._validate_email(email):
                raise ValueError(f"Invalid email address: {email}")

    async def send_email(
        self,
        to: Union[str, List[str]],
        subject: str,
        body_html: str,
        body_text: Optional[str] = None,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None,
    ) -> bool:
        """
        Send an email via SMTP.

        Args:
            to: Recipient email address(es) - single string or list
            subject: Email subject line
            body_html: HTML version of email body
            body_text: Plain text version of email body (optional)
            from_email: Sender email (defaults to config.smtp_from_email)
            from_name: Sender name (defaults to config.smtp_from_name)

        Returns:
            True if sent successfully

        Raises:
            ValueError: If email address is invalid
            EmailSendError: If SMTP sending fails
        """
        try:
            # Validate recipient email(s)
            self._validate_emails(to)

            # Normalize recipients to list
            recipients = [to] if isinstance(to, str) else to

            from_email = from_email or self.config.smtp_from_email
            from_name = from_name or self.config.smtp_from_name
            from_address = f"{from_name} <{from_email}>"

            # Create message
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = from_address
            message["To"] = ", ".join(recipients)

            # Attach plain text version (if provided)
            if body_text:
                part_text = MIMEText(body_text, "plain")
                message.attach(part_text)

            # Attach HTML version
            part_html = MIMEText(body_html, "html")
            message.attach(part_html)

            # Send email via SMTP
            async with aiosmtplib.SMTP(
                hostname=self.config.smtp_host,
                port=self.config.smtp_port,
                use_tls=self.config.use_tls,
            ) as smtp:
                if self.config.smtp_user and self.config.smtp_password:
                    await smtp.login(self.config.smtp_user, self.config.smtp_password)

                await smtp.sendmail(from_address, recipients, message.as_string())

            logger.info(
                "email_sent", to=recipients, subject=subject, from_email=from_email
            )
            return True

        except ValueError:
            # Re-raise validation errors
            raise

        except Exception as e:
            logger.error(
                "email_send_failed", to=to, subject=subject, error=str(e), exc_info=True
            )
            raise EmailSendError(f"Failed to send email: {str(e)}") from e

    def render_template(self, template_string: str, context: dict) -> str:
        """
        Render email template string with context.

        Args:
            template_string: Jinja2 template string
            context: Dictionary of template variables

        Returns:
            Rendered template string
        """
        try:
            template = Template(template_string)
            return template.render(**context)

        except Exception as e:
            logger.error("template_render_failed", error=str(e), exc_info=True)
            # Return simple fallback
            return "Notification from SprintForge"
