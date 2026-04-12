import smtplib
from email.message import EmailMessage
import logging
from app.core.config_loader import settings
from jinja2 import Environment, FileSystemLoader, select_autoescape
import os
import datetime

logger = logging.getLogger(__name__)


# ----------------------------------------------------
# Setup Templated Emails
# -------------------------------------------

TEMPLATES_DIR = os.path.join(os.getcwd(), 'app', 'templates')
SUPPORT_EMAIL = "support@pdfautomator.com"

jinja_env = Environment(
    loader=FileSystemLoader(TEMPLATES_DIR),
    autoescape=select_autoescape(['html', 'xml'])
)


# ----------------------------------------------------
# Create transport (connect to SMTP server)
# ----------------------------------------------------


def create_transport():
    try:
        print("Connecting to email server...")
        server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT)
        server.ehlo()  # Identify yourself to the server

        if settings.SMTP_USER and settings.SMTP_PASS:
            # Upgrade the connection to TLS
            server.starttls()
            server.ehlo()  # Re-identify after TLS upgrade
            logger.info("Logging in to email server...")
            server.login(settings.SMTP_USER, settings.SMTP_PASS)

        logger.info("Connected to email server via TLS")
        return server

    except Exception as e:
        logger.warning(
            "Unable to connect to email server. Check SMTP settings.")
        logger.error(e)
        return None


transport = None

# ----------------------------------------------------
# Send an email
# ----------------------------------------------------


def get_transport():
    global transport
    if transport is None:
        transport = create_transport()
    else:
        try:
            status = transport.noop()[0]
            if status != 250:
                raise smtplib.SMTPServerDisconnected()
        except Exception:
            transport = create_transport()
    return transport


def send_email(to: str, subject: str, html: str, text: str = None):
    """
    Send an email
    :param to: recipient email
    :param subject: subject line
    :param text: plain text message
    """

    transport = get_transport()

    logger.info(f"Sending email to {to} ...")

    if transport is None:
        logger.error("No email transport available.")
        return

    try:
        msg = EmailMessage()
        msg['From'] = settings.SMTP_USER
        msg['To'] = to
        msg['Subject'] = subject

        msg.set_content(
            text or "This is a HTML email. Please view in an HTML compatible email viewer.")

        if html:
            msg.add_alternative(html, subtype='html')

        transport.send_message(msg)
        logger.info(f"Email sent to {to}")
    except Exception as e:
        logger.error(f"Failed to send email to {to}")
        logger.error(e)

# ----------------------------------------------------
# Reset password email
# ----------------------------------------------------


def send_reset_password_email(to: str, token: str):
    subject = "Reset password"
    reset_password_url = f"{settings.FRONTEND_URL}/auth/reset-password?token={token}"
    html = render_template("auth.html",
                           title="Reset your password",
                           message="Please click the button below to reset your password.",
                           cta_link=reset_password_url,
                           cta_title="Reset Password",
                           sent_on=sent_on(),
                           support_email=SUPPORT_EMAIL
                           )

    send_email(to, subject, html)

# ----------------------------------------------------
# Verification email
# ----------------------------------------------------


def send_verification_email(to: str, token: str):
    subject = "Email Verification"
    verification_url = f"{settings.FRONTEND_URL}/auth/verify-email?token={token}"
    html = render_template("auth.html",
                           title="Verify your email",
                           message="Please click the button below to verify your email address.",
                           cta_link=verification_url,
                           cta_title="Verify Email",
                           sent_on=sent_on(),
                           support_email=SUPPORT_EMAIL
                           )
    send_email(to, subject, html)


def render_template(name: str, **context) -> str:
    template = jinja_env.get_template(name)
    return template.render(**context)


def sent_on():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
