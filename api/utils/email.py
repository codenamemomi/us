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


def send_async(fn, *args, **kwargs) -> None:
    """Run an email sending function in a daemon background thread so the HTTP request is not blocked."""
    import threading

    t = threading.Thread(target=fn, args=args, kwargs=kwargs, daemon=True)
    t.start()


def send_welcome_account_email(user_email: str, user_name: str, invite_code: str) -> bool:
    """Sweet HTML welcome email sent when a new account is created."""
    app_url = (getattr(settings, "FRONTEND_URL", None) or "http://localhost:3000").rstrip("/")
    subject = f"Welcome to us, {user_name}! Here's your invite code ✨"

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Welcome to us.</title>
</head>
<body style="margin: 0; padding: 0; background-color: #080811; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color: #f8fafc;">
  <table role="presentation" width="100%" border="0" cellspacing="0" cellpadding="0" style="background-color: #080811; padding: 40px 16px;">
    <tr>
      <td align="center">
        <!-- Main Card -->
        <table role="presentation" width="100%" border="0" cellspacing="0" cellpadding="0" style="max-width: 520px; background: #100b22; background: linear-gradient(160deg, rgba(255, 255, 255, 0.12) 0%, rgba(255, 255, 255, 0.03) 100%), #100b22; border: 1px solid rgba(255, 255, 255, 0.16); border-radius: 28px; box-shadow: 0 24px 60px rgba(0, 0, 0, 0.6); overflow: hidden;">
          <tr>
            <td style="padding: 40px 36px 32px 36px; text-align: center;">
              
              <!-- Brand Logo -->
              <div style="margin-bottom: 24px;">
                <span style="font-size: 32px; font-weight: 900; letter-spacing: -0.04em; color: #ffffff;">us<span style="color: #ff007f;">.</span></span>
              </div>

              <!-- Eyebrow Pill -->
              <div style="display: inline-block; margin-bottom: 16px;">
                <span style="font-size: 11px; font-weight: 800; letter-spacing: 0.18em; text-transform: uppercase; color: #ff007f; background: rgba(255, 0, 127, 0.15); border: 1px solid rgba(255, 0, 127, 0.3); border-radius: 999px; padding: 5px 14px;">
                  Your little universe starts here
                </span>
              </div>

              <!-- Heading -->
              <h1 style="font-size: 26px; font-weight: 800; color: #ffffff; line-height: 1.25; margin: 0 0 16px 0;">
                Welcome to us, {user_name}!
              </h1>

              <!-- Intro Copy -->
              <p style="font-size: 14px; line-height: 1.65; color: rgba(255, 255, 255, 0.72); margin: 0 0 24px 0;">
                You've created your quiet corner of the internet. No feeds, no ads, no algorithms—just a private space built for two.
              </p>

              <!-- Invite Box -->
              <div style="background: rgba(255, 0, 127, 0.08); border: 1px dashed rgba(255, 0, 127, 0.4); border-radius: 20px; padding: 22px 16px; margin: 24px 0; text-align: center;">
                <p style="font-size: 11px; font-weight: 800; letter-spacing: 0.14em; text-transform: uppercase; color: #ff007f; margin: 0 0 8px 0;">
                  Step 1: Invite your person
                </p>
                <div style="font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; font-size: 30px; font-weight: 900; letter-spacing: 0.22em; color: #ffffff; margin: 6px 0;">
                  {invite_code}
                </div>
                <p style="font-size: 12px; line-height: 1.5; color: rgba(255, 255, 255, 0.6); margin: 8px 0 0 0;">
                  Share this code with your partner so they can join you.
                </p>
              </div>

              <!-- Action Button -->
              <div style="margin: 32px 0 24px 0;">
                <a href="{app_url}/invite" style="display: inline-block; background: #ff007f; background: linear-gradient(110deg, #ff007f 0%, #ff5500 100%); color: #ffffff; text-decoration: none; padding: 15px 36px; border-radius: 999px; font-weight: 800; font-size: 14px; letter-spacing: 0.02em; box-shadow: 0 10px 30px rgba(255, 0, 127, 0.45);">
                  Share invite code →
                </a>
              </div>

              <!-- Feature preview bullets -->
              <table role="presentation" width="100%" border="0" cellspacing="0" cellpadding="0" style="margin-top: 24px; border-top: 1px solid rgba(255, 255, 255, 0.08); padding-top: 24px; text-align: left;">
                <tr>
                  <td style="padding: 8px 0; font-size: 13px; color: rgba(255, 255, 255, 0.65); line-height: 1.5;">
                    💬 <strong style="color: #ffffff;">Daily Prompts:</strong> One thoughtful question each day. Answers unlock when both of you reply.
                  </td>
                </tr>
                <tr>
                  <td style="padding: 8px 0; font-size: 13px; color: rgba(255, 255, 255, 0.65); line-height: 1.5;">
                    🎮 <strong style="color: #ffffff;">Tiny Games:</strong> Play "Would You Rather" in sync to see how aligned your minds really are.
                  </td>
                </tr>
                <tr>
                  <td style="padding: 8px 0; font-size: 13px; color: rgba(255, 255, 255, 0.65); line-height: 1.5;">
                    ✨ <strong style="color: #ffffff;">Always in Sync:</strong> Live online status, bored alerts, and milestone trackers.
                  </td>
                </tr>
              </table>

            </td>
          </tr>
        </table>

        <!-- Footer -->
        <table role="presentation" width="100%" border="0" cellspacing="0" cellpadding="0" style="max-width: 520px; text-align: center; margin-top: 20px;">
          <tr>
            <td style="font-size: 12px; color: rgba(255, 255, 255, 0.35);">
              Sent with love from <strong style="color: rgba(255, 255, 255, 0.5);">us.</strong>
            </td>
          </tr>
        </table>

      </td>
    </tr>
  </table>
</body>
</html>"""
    return send_brevo_email(user_email, user_name, subject, html)


def send_couple_connected_email(user_email: str, user_name: str, partner_name: str) -> bool:
    """Sweet celebratory HTML email sent when the second partner joins and couple is complete."""
    app_url = (getattr(settings, "FRONTEND_URL", None) or "http://localhost:3000").rstrip("/")
    subject = f"You & {partner_name} are officially connected on us! 💕"

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>You're connected on us.</title>
</head>
<body style="margin: 0; padding: 0; background-color: #080811; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color: #f8fafc;">
  <table role="presentation" width="100%" border="0" cellspacing="0" cellpadding="0" style="background-color: #080811; padding: 40px 16px;">
    <tr>
      <td align="center">
        <!-- Main Card -->
        <table role="presentation" width="100%" border="0" cellspacing="0" cellpadding="0" style="max-width: 520px; background: #100b22; background: linear-gradient(160deg, rgba(255, 255, 255, 0.12) 0%, rgba(255, 255, 255, 0.03) 100%), #100b22; border: 1px solid rgba(255, 255, 255, 0.16); border-radius: 28px; box-shadow: 0 24px 60px rgba(0, 0, 0, 0.6); overflow: hidden;">
          <tr>
            <td style="padding: 40px 36px 32px 36px; text-align: center;">
              
              <!-- Brand Logo -->
              <div style="margin-bottom: 24px;">
                <span style="font-size: 32px; font-weight: 900; letter-spacing: -0.04em; color: #ffffff;">us<span style="color: #ff007f;">.</span></span>
              </div>

              <!-- Avatar Pair Badge -->
              <div style="display: inline-block; margin-bottom: 20px;">
                <table role="presentation" border="0" cellspacing="0" cellpadding="0" style="background: rgba(255, 255, 255, 0.08); border: 1px solid rgba(255, 255, 255, 0.2); border-radius: 999px; padding: 7px 22px;">
                  <tr>
                    <td style="font-size: 15px; font-weight: 800; color: #ffffff;">
                      <span style="color: #ffffff;">{user_name}</span>
                      <span style="color: #ff007f; margin: 0 8px;">+</span>
                      <span style="color: #ffffff;">{partner_name}</span>
                    </td>
                  </tr>
                </table>
              </div>

              <!-- Eyebrow Pill -->
              <div style="margin-bottom: 14px;">
                <span style="font-size: 11px; font-weight: 800; letter-spacing: 0.18em; text-transform: uppercase; color: #ff007f; background: rgba(255, 0, 127, 0.15); border: 1px solid rgba(255, 0, 127, 0.3); border-radius: 999px; padding: 5px 14px;">
                  Your space is complete ✨
                </span>
              </div>

              <!-- Heading -->
              <h1 style="font-size: 28px; font-weight: 800; color: #ffffff; line-height: 1.25; margin: 0 0 16px 0;">
                You two are officially connected!
              </h1>

              <!-- Intro Copy -->
              <p style="font-size: 15px; line-height: 1.65; color: rgba(255, 255, 255, 0.75); margin: 0 0 20px 0;">
                {partner_name} just joined your couple space. Your two-person corner of the universe is now linked and live in real-time.
              </p>

              <!-- Daily Prompt Callout Box -->
              <div style="background: rgba(255, 85, 0, 0.08); border: 1px solid rgba(255, 85, 0, 0.3); border-radius: 20px; padding: 20px; margin: 24px 0; text-align: center;">
                <p style="font-size: 11px; font-weight: 800; letter-spacing: 0.14em; text-transform: uppercase; color: #ff5500; margin: 0 0 6px 0;">
                  Today's Question Is Ready
                </p>
                <p style="font-size: 14px; font-weight: 600; color: #ffffff; margin: 0; line-height: 1.5;">
                  Jump in and write your secret answer before {partner_name} does!
                </p>
              </div>

              <!-- Action Button -->
              <div style="margin: 32px 0 24px 0;">
                <a href="{app_url}" style="display: inline-block; background: #ff007f; background: linear-gradient(110deg, #ff007f 0%, #ff5500 100%); color: #ffffff; text-decoration: none; padding: 15px 38px; border-radius: 999px; font-weight: 800; font-size: 15px; letter-spacing: 0.02em; box-shadow: 0 10px 30px rgba(255, 0, 127, 0.45);">
                  Enter Your Space →
                </a>
              </div>

              <!-- Highlights -->
              <p style="font-size: 12px; color: rgba(255, 255, 255, 0.45); margin: 0; line-height: 1.6;">
                Save <strong>us.</strong> to your phone's home screen for the full app experience.
              </p>

            </td>
          </tr>
        </table>

        <!-- Footer -->
        <table role="presentation" width="100%" border="0" cellspacing="0" cellpadding="0" style="max-width: 520px; text-align: center; margin-top: 20px;">
          <tr>
            <td style="font-size: 12px; color: rgba(255, 255, 255, 0.35);">
              Built with care for <strong style="color: rgba(255, 255, 255, 0.5);">{user_name} &amp; {partner_name}</strong> • us.
            </td>
          </tr>
        </table>

      </td>
    </tr>
  </table>
</body>
</html>"""
    return send_brevo_email(user_email, user_name, subject, html)


def send_bored_email(partner_email: str, partner_name: str, sender_name: str) -> bool:
    app_url = (getattr(settings, "FRONTEND_URL", None) or "http://localhost:3000").rstrip("/")
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
        <a href="{app_url}" style="display: inline-block; background: linear-gradient(110deg, #ff007f, #ff5500); color: #ffffff; text-decoration: none; padding: 14px 28px; border-radius: 999px; font-weight: 800; font-size: 14px; box-shadow: 0 8px 24px rgba(255,0,127,0.4);">
          Open us. →
        </a>
      </div>
      <p style="font-size: 11px; color: rgba(255,255,255,0.3); margin-top: 24px;">Sent with love from us.</p>
    </body>
    </html>
    """
    return send_brevo_email(partner_email, partner_name, subject, html)
