"""Email service for sending notifications via SMTP."""

import aiosmtplib
import structlog
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from jinja2 import Environment, FileSystemLoader, select_autoescape
from pathlib import Path
from typing import Optional, List

from app.core.config import get_settings

logger = structlog.get_logger(__name__)


class EmailService:
    """Service for sending emails using async SMTP."""

    def __init__(self):
        """Initialize email service with SMTP configuration."""
        self.settings = get_settings()

        # Initialize Jinja2 environment for email templates
        template_dir = Path(__file__).parent.parent / "templates" / "emails"
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(template_dir)),
            autoescape=select_autoescape(['html', 'xml']),
            trim_blocks=True,
            lstrip_blocks=True,
        )

    async def send_email(
        self,
        to_email: str,
        subject: str,
        body_html: str,
        body_text: str,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None,
    ) -> bool:
        """
        Send an email via SMTP.

        Args:
            to_email: Recipient email address
            subject: Email subject line
            body_html: HTML version of email body
            body_text: Plain text version of email body
            from_email: Sender email (defaults to settings.smtp_from_email)
            from_name: Sender name (defaults to settings.smtp_from_name)

        Returns:
            True if sent successfully, False otherwise
        """
        try:
            from_email = from_email or self.settings.smtp_from_email
            from_name = from_name or self.settings.smtp_from_name
            from_address = f"{from_name} <{from_email}>"

            # Create message
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = from_address
            message["To"] = to_email

            # Attach both plain text and HTML versions
            part_text = MIMEText(body_text, "plain")
            part_html = MIMEText(body_html, "html")
            message.attach(part_text)
            message.attach(part_html)

            # Send email via SMTP
            async with aiosmtplib.SMTP(
                hostname=self.settings.smtp_host,
                port=self.settings.smtp_port,
                use_tls=self.settings.smtp_use_tls,
            ) as smtp:
                if self.settings.smtp_user and self.settings.smtp_password:
                    await smtp.login(
                        self.settings.smtp_user,
                        self.settings.smtp_password
                    )

                await smtp.send_message(message)

            logger.info(
                "email_sent",
                to=to_email,
                subject=subject,
                from_email=from_email
            )
            return True

        except Exception as e:
            logger.error(
                "email_send_failed",
                to=to_email,
                subject=subject,
                error=str(e),
                exc_info=True
            )
            return False

    def render_template(
        self,
        template_name: str,
        context: dict
    ) -> tuple[str, str]:
        """
        Render email template with context.

        Args:
            template_name: Name of template file (e.g., 'sprint_complete.html')
            context: Dictionary of template variables

        Returns:
            Tuple of (html_body, text_body)
        """
        try:
            # Render HTML template
            html_template = self.jinja_env.get_template(f"{template_name}.html")
            html_body = html_template.render(**context)

            # Render text template
            text_template = self.jinja_env.get_template(f"{template_name}.txt")
            text_body = text_template.render(**context)

            return html_body, text_body

        except Exception as e:
            logger.error(
                "template_render_failed",
                template=template_name,
                error=str(e),
                exc_info=True
            )
            # Return simple fallback
            return f"<p>Notification from SprintForge</p>", "Notification from SprintForge"

    async def send_templated_email(
        self,
        to_email: str,
        subject: str,
        template_name: str,
        context: dict,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None,
    ) -> bool:
        """
        Send an email using a template.

        Args:
            to_email: Recipient email address
            subject: Email subject line
            template_name: Name of template file (without extension)
            context: Dictionary of template variables
            from_email: Sender email (optional)
            from_name: Sender name (optional)

        Returns:
            True if sent successfully, False otherwise
        """
        html_body, text_body = self.render_template(template_name, context)
        return await self.send_email(
            to_email=to_email,
            subject=subject,
            body_html=html_body,
            body_text=text_body,
            from_email=from_email,
            from_name=from_name,
        )


# Singleton instance
_email_service: Optional[EmailService] = None


def get_email_service() -> EmailService:
    """Get singleton email service instance."""
    global _email_service
    if _email_service is None:
        _email_service = EmailService()
    return _email_service
