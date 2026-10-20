import json
import logging
import urllib.error
import urllib.request

from api.core.config import settings

logger = logging.getLogger(__name__)


def send_brevo_email(to_email: str, to_name: str, subject: str, html_content: str) -> bool:
    api_key = settings.BREVO_API_KEY
    if not api_key:
        logger.warning("BREVO_API_KEY is not set. Falling back to console output.")
        return False

    sender_email = (settings.EMAIL_FROM or "no-reply@omomi.me").strip()
    payload = {
        "sender": {"name": "us.", "email": sender_email},
        "to": [{"email": to_email.strip(), "name": to_name.strip()}],
        "subject": subject,
        "htmlContent": html_content,
    }

    req = urllib.request.Request(
        "https://api.brevo.com/v3/smtp/email",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "api-key": api_key.strip(),
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            if resp.status in (200, 201, 202):
                logger.info("Email successfully sent to %s via Brevo", to_email)
                return True
            logger.warning("Brevo returned status %s", resp.status)
            return False
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="replace")
        logger.error("Brevo HTTPError %s: %s", e.code, err_body)
        return False
    except Exception as e:
        logger.error("Failed to send email via Brevo: %s", e)
        return False


def send_bored_email(partner_email: str, partner_name: str, sender_name: str) -> bool:
    subject = f"{sender_name} is bored 👀"
    html = f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="utf-8"></head>
    <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #080811; color: #f8fafc; padding: 40px 20px; text-align: center;">
      <div style="max-width: 440px; margin: 0 auto; background: linear-gradient(135deg, rgba(255,255,255,0.1), rgba(255,255,255,0.03)); border: 1px solid rgba(255,255,255,0.15); border-radius: 28px; padding: 36px; box-shadow: 0 20px 50px rgba(0,0,0,0.5);">
        <p style="font-size: 11px; font-weight: 800; letter-spacing: 0.16em; text-transform: uppercase; color: #ff007f; margin: 0 0 12px 0;">YOUR LITTLE UNIVERSE</p>
        <h1 style="font-size: 26px; font-weight: 800; margin: 0 0 16px 0; color: #ffffff;">{sender_name} is bored 👀</h1>
        <p style="font-size: 14px; line-height: 1.6; color: rgba(255,255,255,0.7); margin: 0 0 28px 0;">
          {sender_name} just sent you a signal on <strong>us.</strong> Come say hi, answer today's question, or play a quick round of Would You Rather together!
        </p>
        <a href="http://localhost:3000" style="display: inline-block; background: linear-gradient(110deg, #ff007f, #ff5500); color: #ffffff; text-decoration: none; padding: 14px 28px; border-radius: 999px; font-weight: 800; font-size: 14px; box-shadow: 0 8px 24px rgba(255,0,127,0.4);">
          Open us. →
        </a>
      </div>
      <p style="font-size: 11px; color: rgba(255,255,255,0.3); margin-top: 24px;">Sent with love from us.</p>
    </body>
    </html>
    """
    return send_brevo_email(partner_email, partner_name, subject, html)
