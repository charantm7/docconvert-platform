import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from api_gateway.authentication.api.security import render_email_template
from api_gateway.handlers.decorators import log_service_action
from api_gateway.settings import settings

@log_service_action("send_email_verification_link")
def send_email_verification_link(link: str, to_email: str) -> None:
    subject = "Verify Your DocPipe Account"

    html = render_email_template(
        "verify_email.html",
        context={"verification_link": link}
    )

    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = settings.EMAIL_FROM
    message["To"] = to_email
    message.attach(MIMEText(html, "html"))

    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.starttls()
            server.login(settings.EMAIL_FROM, settings.EMAIL_PASSWORD)
            server.send_message(message)

    except smtplib.SMTPAuthenticationError as e:
        print("Auth error", str(e))
    except Exception as e:
        print("Exception", str(e))

@log_service_action("send_password_reset_link")
def send_password_reset_link(link: str, to_email: str) -> None:
    subject = "Reset Your DocConvert Password"

    html = render_email_template(
        "password_reset.html",
        context={"reset_password_link": link}
    )

    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = settings.EMAIL_FROM
    message["To"] = to_email
    message.attach(MIMEText(html, "html"))

    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.starttls()
            server.login(settings.EMAIL_FROM, settings.EMAIL_PASSWORD)
            server.send_message(message)

    except smtplib.SMTPAuthenticationError as e:
        print("Auth error", str(e))
    except Exception as e:
        print("Exception", str(e))
