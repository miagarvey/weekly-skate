import os
from typing import List

# Optional Twilio (safe to leave unset; we'll "dry-run" to console)
try:
    from twilio.rest import Client
except Exception:
    Client = None  # type: ignore

from models.database import get_broadcast_numbers

class MessagingService:
    def __init__(self):
        self.twilio_sid = os.environ.get("TWILIO_ACCOUNT_SID")
        self.twilio_auth = os.environ.get("TWILIO_AUTH_TOKEN")
        self.twilio_from = os.environ.get("TWILIO_FROM")
        self.dry_run = os.environ.get("TWILIO_DRY_RUN", "0") == "1"
    
    def _get_twilio_client(self):
        """Get Twilio client if credentials are available"""
        if self.twilio_sid and self.twilio_auth and Client is not None:
            return Client(self.twilio_sid, self.twilio_auth)
        return None
    
    def send_sms(self, to: str, body: str):
        """Send SMS message to a phone number"""
        if self.dry_run:
            print(f"[SMS DRY-RUN to {to}]\n{body}\n---")
            return
        
        client = self._get_twilio_client()
        if client and (self.twilio_from or os.environ.get("TWILIO_MESSAGING_SERVICE_SID")):
            try:
                params = {"to": to, "body": body}
                if os.environ.get("TWILIO_MESSAGING_SERVICE_SID"):
                    params["messaging_service_sid"] = os.environ["TWILIO_MESSAGING_SERVICE_SID"]
                else:
                    params["from_"] = self.twilio_from
                msg = client.messages.create(**params)
                print(f"[SMS SENT] to {to} sid={msg.sid}")
            except Exception as e:
                print(f"[SMS ERROR] to {to}: {e}")
        else:
            print(f"[SMS DRY-RUN to {to}]\n{body}\n---")
    
    def format_signup_list(self, signups) -> str:
        """Format signup list for SMS messages"""
        if not signups:
            return "No signups yet."
        lines = ["Weekly Skate Signups:"]
        for idx, (name, phone, created_at) in enumerate(signups, 1):
            p = phone or "(no phone)"
            t = created_at.split(".")[0].replace("T", " ")
            lines.append(f"{idx}. {name} {p} – {t}")
        return "\n".join(lines)
    
    def broadcast_signups(self, signups) -> int:
        """Broadcast signup list to all broadcast numbers"""
        nums = get_broadcast_numbers()
        if not nums:
            return 0
        body = self.format_signup_list(signups)
        for n in nums:
            self.send_sms(n, body)
        return len(nums)
