"""
PHANTOM — Alerting Service (Twilio SMS + Voice)
Sends real-time SMS and voice call alerts when critical attacks are detected.
"""

import os
import time
from datetime import datetime
from dotenv import load_dotenv, find_dotenv

# Load .env from project root
dotenv_path = find_dotenv(usecwd=True)
if not dotenv_path:
    # Fallback: look relative to this file
    dotenv_path = os.path.join(os.path.dirname(__file__), "..", ".env")
load_dotenv(dotenv_path)

# ── Anti-spam control ─────────────────────────────────────────
_last_alert_time = 0
ALERT_COOLDOWN = 60  # seconds between alerts


def can_send_alert():
    global _last_alert_time
    now = time.time()

    if now - _last_alert_time < ALERT_COOLDOWN:
        return False

    _last_alert_time = now
    return True


# ── Twilio client (created at runtime, NOT import time) ───────
def get_client():
    try:
        from twilio.rest import Client
    except ImportError:
        raise Exception("Twilio not installed. Run: pip install twilio")

    sid = os.getenv("TWILIO_ACCOUNT_SID")
    token = os.getenv("TWILIO_AUTH_TOKEN")

    if not sid or not token:
        raise Exception("Twilio credentials missing in environment variables")

    return Client(sid, token)


# ── Core Alert Function ───────────────────────────────────────
def send_critical_alert(ip: str, attack_type: str, confidence: float):
    """
    Sends SMS + Voice call for critical attacks.
    Called automatically when PHANTOM blocks an IP.
    """

    if not can_send_alert():
        print(f"[ALERT] Skipped alert for {ip} (cooldown active)")
        return

    phone_from = os.getenv("TWILIO_PHONE")
    phone_to = os.getenv("ALERT_PHONE")

    if not phone_from or not phone_to:
        print("[ALERT ERROR] Phone numbers missing in .env")
        return

    message = (
        f"[PHANTOM ALERT]\n"
        f"Critical attack detected!\n"
        f"IP: {ip}\n"
        f"Type: {attack_type}\n"
        f"Confidence: {confidence:.2f}\n"
        f"Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}"
    )

    try:
        client = get_client()

        # ── SMS ALERT ───────────────────────────────
        client.messages.create(
            body=message,
            from_=phone_from,
            to=phone_to
        )
        print(f"[ALERT] SMS sent for attack from {ip}")

        # ── VOICE CALL ALERT ─────────────────────────
        client.calls.create(
            twiml=f"""
            <Response>
                <Say voice="alice">
                    Critical security alert from Phantom.
                    A {attack_type} attack has been detected from IP address {ip}
                    with {confidence:.0%} confidence.
                    The IP has been automatically blocked.
                    Please check the admin dashboard immediately.
                </Say>
            </Response>
            """,
            from_=phone_from,
            to=phone_to
        )
        print(f"[ALERT] Voice call initiated for attack from {ip}")

    except Exception as e:
        print(f"[ALERT ERROR] {e}")
