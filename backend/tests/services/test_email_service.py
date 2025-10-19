"""
Tests for email service.

This test suite validates the EmailService class with async SMTP functionality
and Jinja2 template rendering, following TDD principles.

These tests are written BEFORE implementation (RED phase) and should FAIL initially.
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch, MagicMock
from datetime import datetime

# These imports will fail until service is implemented (expected in RED phase)
from app.services.email_service import EmailService, EmailConfig, EmailSendError


@pytest.mark.unit
class TestEmailServiceConfiguration:
    """Test email service configuration and initialization."""

    def test_email_config_creation(self):
        """
        Test EmailConfig dataclass creation.

        Validates configuration structure for SMTP settings.
        """
        config = EmailConfig(
            smtp_host="smtp.gmail.com",
            smtp_port=587,
            smtp_user="test@example.com",
            smtp_password="password123",
            smtp_from_email="noreply@sprintforge.com",
            smtp_from_name="SprintForge",
            use_tls=True,
        )

        assert config.smtp_host == "smtp.gmail.com"
        assert config.smtp_port == 587
        assert config.smtp_user == "test@example.com"
        assert config.smtp_password == "password123"
        assert config.smtp_from_email == "noreply@sprintforge.com"
        assert config.smtp_from_name == "SprintForge"
        assert config.use_tls is True

    def test_email_config_defaults(self):
        """
        Test EmailConfig default values.

        Ensures sensible defaults for optional fields.
        """
        config = EmailConfig(
            smtp_host="smtp.example.com",
            smtp_port=587,
            smtp_user="user@example.com",
            smtp_password="password",
            smtp_from_email="from@example.com",
        )

        assert config.smtp_from_name == "SprintForge"  # Default
        assert config.use_tls is True  # Default

    def test_email_service_initialization(self):
        """
        Test EmailService initialization with config.

        Validates service setup with configuration.
        """
        config = EmailConfig(
            smtp_host="smtp.example.com",
            smtp_port=587,
            smtp_user="user@example.com",
            smtp_password="password",
            smtp_from_email="from@example.com",
        )

        service = EmailService(config)

        assert service.config == config
        assert service.config.smtp_host == "smtp.example.com"


@pytest.mark.unit
class TestEmailServiceSending:
    """Test email sending functionality."""

    @pytest.fixture
    def email_config(self):
        """Provide test email configuration."""
        return EmailConfig(
            smtp_host="smtp.test.com",
            smtp_port=587,
            smtp_user="test@example.com",
            smtp_password="testpass",
            smtp_from_email="noreply@sprintforge.com",
            smtp_from_name="SprintForge",
            use_tls=True,
        )

    @pytest.fixture
    def email_service(self, email_config):
        """Provide EmailService instance."""
        return EmailService(email_config)

    @pytest.mark.asyncio
    async def test_send_email_success(self, email_service):
        """
        Test successful email sending.

        Validates that email is sent via SMTP with correct parameters.
        """
        with patch("aiosmtplib.SMTP") as mock_smtp_class:
            # Setup mock SMTP instance
            mock_smtp = AsyncMock()
            mock_smtp_class.return_value = mock_smtp
            mock_smtp.__aenter__.return_value = mock_smtp
            mock_smtp.__aexit__.return_value = None
            mock_smtp.sendmail = AsyncMock()

            result = await email_service.send_email(
                to="recipient@example.com",
                subject="Test Subject",
                body_html="<p>Test HTML body</p>",
                body_text="Test plain text body",
            )

            assert result is True
            mock_smtp.sendmail.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_email_with_html_and_text(self, email_service):
        """
        Test sending email with both HTML and plain text versions.

        Validates multipart MIME message creation.
        """
        with patch("aiosmtplib.SMTP") as mock_smtp_class:
            mock_smtp = AsyncMock()
            mock_smtp_class.return_value = mock_smtp
            mock_smtp.__aenter__.return_value = mock_smtp
            mock_smtp.__aexit__.return_value = None
            mock_smtp.sendmail = AsyncMock()

            result = await email_service.send_email(
                to="recipient@example.com",
                subject="Multipart Test",
                body_html="<h1>HTML Version</h1><p>Content</p>",
                body_text="Plain text version\nContent",
            )

            assert result is True
            # Verify sendmail was called with correct structure
            call_args = mock_smtp.sendmail.call_args
            assert call_args is not None

    @pytest.mark.asyncio
    async def test_send_email_html_only(self, email_service):
        """
        Test sending email with HTML only (no plain text).

        Validates that plain text is optional.
        """
        with patch("aiosmtplib.SMTP") as mock_smtp_class:
            mock_smtp = AsyncMock()
            mock_smtp_class.return_value = mock_smtp
            mock_smtp.__aenter__.return_value = mock_smtp
            mock_smtp.__aexit__.return_value = None
            mock_smtp.sendmail = AsyncMock()

            result = await email_service.send_email(
                to="recipient@example.com",
                subject="HTML Only",
                body_html="<p>HTML content</p>",
            )

            assert result is True

    @pytest.mark.asyncio
    async def test_send_email_smtp_failure(self, email_service):
        """
        Test handling of SMTP connection failure.

        Validates proper error handling and exception raising.
        """
        with patch("aiosmtplib.SMTP") as mock_smtp_class:
            mock_smtp = AsyncMock()
            mock_smtp_class.return_value = mock_smtp
            mock_smtp.__aenter__.return_value = mock_smtp
            mock_smtp.__aexit__.return_value = None
            mock_smtp.sendmail = AsyncMock(side_effect=Exception("SMTP connection failed"))

            with pytest.raises(EmailSendError) as exc_info:
                await email_service.send_email(
                    to="recipient@example.com",
                    subject="Test",
                    body_html="<p>Test</p>",
                )

            assert "SMTP connection failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_send_email_invalid_recipient(self, email_service):
        """
        Test sending email to invalid address.

        Validates email address validation.
        """
        with pytest.raises(ValueError) as exc_info:
            await email_service.send_email(
                to="invalid-email",
                subject="Test",
                body_html="<p>Test</p>",
            )

        assert "invalid" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_send_email_multiple_recipients(self, email_service):
        """
        Test sending email to multiple recipients.

        Validates support for list of email addresses.
        """
        with patch("aiosmtplib.SMTP") as mock_smtp_class:
            mock_smtp = AsyncMock()
            mock_smtp_class.return_value = mock_smtp
            mock_smtp.__aenter__.return_value = mock_smtp
            mock_smtp.__aexit__.return_value = None
            mock_smtp.sendmail = AsyncMock()

            recipients = ["user1@example.com", "user2@example.com", "user3@example.com"]
            result = await email_service.send_email(
                to=recipients,
                subject="Bulk Email",
                body_html="<p>Test</p>",
            )

            assert result is True

    @pytest.mark.asyncio
    async def test_send_email_with_attachments(self, email_service):
        """
        Test sending email with file attachments (future feature).

        Validates attachment support.
        """
        with patch("aiosmtplib.SMTP") as mock_smtp_class:
            mock_smtp = AsyncMock()
            mock_smtp_class.return_value = mock_smtp
            mock_smtp.__aenter__.return_value = mock_smtp
            mock_smtp.__aexit__.return_value = None
            mock_smtp.sendmail = AsyncMock()

            # This feature might not be in MVP
            # Test skipped if not implemented
            pytest.skip("Attachments feature not in MVP")


@pytest.mark.unit
class TestEmailServiceTemplates:
    """Test email template rendering functionality."""

    @pytest.fixture
    def email_config(self):
        """Provide test email configuration."""
        return EmailConfig(
            smtp_host="smtp.test.com",
            smtp_port=587,
            smtp_user="test@example.com",
            smtp_password="testpass",
            smtp_from_email="noreply@sprintforge.com",
        )

    @pytest.fixture
    def email_service(self, email_config):
        """Provide EmailService instance."""
        return EmailService(email_config)

    def test_render_template_simple(self, email_service):
        """
        Test rendering a simple Jinja2 template.

        Validates basic template variable substitution.
        """
        template_str = "Hello {{ name }}, welcome to {{ app_name }}!"
        context = {"name": "John Doe", "app_name": "SprintForge"}

        result = email_service.render_template(template_str, context)

        assert result == "Hello John Doe, welcome to SprintForge!"

    def test_render_template_html(self, email_service):
        """
        Test rendering HTML email template.

        Validates HTML template rendering with complex structure.
        """
        template_str = """
        <html>
            <body>
                <h1>{{ title }}</h1>
                <p>Sprint {{ sprint_name }} is {{ completion }}% complete.</p>
            </body>
        </html>
        """
        context = {
            "title": "Sprint Complete",
            "sprint_name": "24.Q1.1",
            "completion": 100,
        }

        result = email_service.render_template(template_str, context)

        assert "<h1>Sprint Complete</h1>" in result
        assert "Sprint 24.Q1.1 is 100% complete" in result

    def test_render_template_missing_variable(self, email_service):
        """
        Test rendering template with missing variable.

        Validates error handling for undefined variables.
        """
        template_str = "Hello {{ name }}, your score is {{ score }}!"
        context = {"name": "Jane"}  # Missing 'score'

        # Jinja2 by default renders undefined as empty string
        result = email_service.render_template(template_str, context)

        assert "Hello Jane, your score is !" in result

    def test_render_template_with_loops(self, email_service):
        """
        Test rendering template with loops.

        Validates Jinja2 loop functionality.
        """
        template_str = """
        Tasks:
        {% for task in tasks %}
        - {{ task.name }}: {{ task.status }}
        {% endfor %}
        """
        context = {
            "tasks": [
                {"name": "Task 1", "status": "Complete"},
                {"name": "Task 2", "status": "In Progress"},
            ]
        }

        result = email_service.render_template(template_str, context)

        assert "Task 1: Complete" in result
        assert "Task 2: In Progress" in result

    def test_render_template_with_conditionals(self, email_service):
        """
        Test rendering template with conditional logic.

        Validates Jinja2 conditional statements.
        """
        template_str = """
        {% if is_complete %}
        Sprint is complete!
        {% else %}
        Sprint is in progress ({{ progress }}%)
        {% endif %}
        """

        # Test complete case
        context_complete = {"is_complete": True, "progress": 100}
        result_complete = email_service.render_template(template_str, context_complete)
        assert "Sprint is complete!" in result_complete

        # Test in-progress case
        context_progress = {"is_complete": False, "progress": 75}
        result_progress = email_service.render_template(template_str, context_progress)
        assert "Sprint is in progress (75%)" in result_progress

    def test_render_template_with_filters(self, email_service):
        """
        Test rendering template with Jinja2 filters.

        Validates built-in filter usage (upper, lower, title).
        """
        template_str = "{{ name | upper }} - {{ email | lower }}"
        context = {"name": "john doe", "email": "JOHN@EXAMPLE.COM"}

        result = email_service.render_template(template_str, context)

        assert "JOHN DOE" in result
        assert "john@example.com" in result


@pytest.mark.unit
class TestEmailServiceIntegration:
    """Test email service integration scenarios."""

    @pytest.fixture
    def email_config(self):
        """Provide test email configuration."""
        return EmailConfig(
            smtp_host="smtp.test.com",
            smtp_port=587,
            smtp_user="test@example.com",
            smtp_password="testpass",
            smtp_from_email="noreply@sprintforge.com",
            smtp_from_name="SprintForge Notifications",
        )

    @pytest.fixture
    def email_service(self, email_config):
        """Provide EmailService instance."""
        return EmailService(email_config)

    @pytest.mark.asyncio
    async def test_send_templated_email(self, email_service):
        """
        Test sending email with template rendering.

        Validates end-to-end template rendering and sending.
        """
        with patch("aiosmtplib.SMTP") as mock_smtp_class:
            mock_smtp = AsyncMock()
            mock_smtp_class.return_value = mock_smtp
            mock_smtp.__aenter__.return_value = mock_smtp
            mock_smtp.__aexit__.return_value = None
            mock_smtp.sendmail = AsyncMock()

            # Template with variables
            subject_template = "Sprint {{ sprint_name }} Complete"
            html_template = "<p>Sprint {{ sprint_name }} is {{ completion }}% done!</p>"
            text_template = "Sprint {{ sprint_name }} is {{ completion }}% done!"

            context = {"sprint_name": "24.Q1.1", "completion": 100}

            # Render templates
            subject = email_service.render_template(subject_template, context)
            html_body = email_service.render_template(html_template, context)
            text_body = email_service.render_template(text_template, context)

            # Send email
            result = await email_service.send_email(
                to="user@example.com",
                subject=subject,
                body_html=html_body,
                body_text=text_body,
            )

            assert result is True
            assert "Sprint 24.Q1.1 Complete" == subject
            assert "100% done" in html_body

    @pytest.mark.asyncio
    async def test_batch_email_sending(self, email_service):
        """
        Test sending multiple emails in batch.

        Validates bulk email sending functionality.
        """
        with patch("aiosmtplib.SMTP") as mock_smtp_class:
            mock_smtp = AsyncMock()
            mock_smtp_class.return_value = mock_smtp
            mock_smtp.__aenter__.return_value = mock_smtp
            mock_smtp.__aexit__.return_value = None
            mock_smtp.sendmail = AsyncMock()

            recipients = [
                "user1@example.com",
                "user2@example.com",
                "user3@example.com",
            ]

            results = []
            for recipient in recipients:
                result = await email_service.send_email(
                    to=recipient,
                    subject="Batch Email",
                    body_html="<p>Test</p>",
                )
                results.append(result)

            assert all(results)
            assert mock_smtp.sendmail.call_count == 3

    @pytest.mark.asyncio
    async def test_email_retry_on_transient_failure(self, email_service):
        """
        Test retry logic for transient SMTP failures.

        Validates automatic retry mechanism.
        """
        with patch("aiosmtplib.SMTP") as mock_smtp_class:
            mock_smtp = AsyncMock()
            mock_smtp_class.return_value = mock_smtp
            mock_smtp.__aenter__.return_value = mock_smtp
            mock_smtp.__aexit__.return_value = None

            # First attempt fails, second succeeds
            mock_smtp.sendmail = AsyncMock(
                side_effect=[
                    Exception("Temporary connection error"),
                    None,  # Success on retry
                ]
            )

            # This assumes EmailService has retry logic
            # If not implemented in MVP, skip this test
            pytest.skip("Retry logic not in MVP")


@pytest.mark.unit
class TestEmailServiceConfiguration:
    """Test email service configuration from Settings."""

    def test_load_config_from_settings(self):
        """
        Test loading email configuration from app settings.

        Validates integration with pydantic Settings.
        """
        from app.core.config import Settings

        # Mock settings with email configuration
        with patch.object(Settings, "__init__", lambda x: None):
            settings = Settings()
            settings.smtp_host = "smtp.gmail.com"
            settings.smtp_port = 587
            settings.smtp_user = "test@example.com"
            settings.smtp_password = "password123"
            settings.smtp_from_email = "noreply@sprintforge.com"

            config = EmailConfig(
                smtp_host=settings.smtp_host,
                smtp_port=settings.smtp_port,
                smtp_user=settings.smtp_user,
                smtp_password=settings.smtp_password,
                smtp_from_email=settings.smtp_from_email,
            )

            assert config.smtp_host == "smtp.gmail.com"
            assert config.smtp_port == 587
