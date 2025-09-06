from __future__ import annotations
import os
import logging
from datetime import datetime

from flask import Flask, request, redirect, url_for, render_template, jsonify
import re

# Import our modular components
from models import init_db, Signup
from models.database import (
    get_week_info, set_quota, add_broadcast_number, remove_broadcast_number,
    get_broadcast_numbers, get_goalie_phone, set_goalie_phone, mark_goalie_notified,
    get_goalie_venmo_username, store_goalie_venmo_username
)
from models.models import is_e164
from services import MessagingService, PaymentService, NLPService
from services.mcp_client import mcp_client
from utils import WeekUtils, require_admin
from utils.config import Config, validate_startup_config
from utils.security import SecurityManager, require_rate_limit, rate_limiter

# Validate configuration and setup logging
validate_startup_config()

app = Flask(__name__)
app.secret_key = Config.SECRET_KEY

# Configure Flask app
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Initialize services with configuration
messaging = MessagingService()
payment = PaymentService()
nlp = NLPService()

# Initialize database
init_db()

# Setup logging
logger = logging.getLogger(__name__)
logger.info("Weekly Skate App starting up")
logger.info(f"Environment: {Config.FLASK_ENV}")
logger.info(f"Debug mode: {Config.FLASK_DEBUG}")
logger.info(f"Twilio dry run: {Config.TWILIO_DRY_RUN}")

def use_mcp_tool_wrapper(server_name: str, tool_name: str, arguments: dict):
    """
    Wrapper function to use MCP tools from within the app
    
    This function provides a bridge between the MCP client and the Flask app,
    allowing the MCP client to call MCP tools without circular imports.
    """
    try:
        # Import here to avoid circular imports
        from cline import use_mcp_tool
        
        # Use the actual MCP tool
        result = use_mcp_tool(server_name, tool_name, arguments)
        logger.info(f"MCP Tool {server_name}.{tool_name} executed successfully")
        return result
        
    except ImportError:
        # Fallback if cline module is not available
        logger.warning(f"MCP tool {server_name}.{tool_name} not available - using mock response")
        return {
            "mock": True,
            "server": server_name,
            "tool": tool_name,
            "arguments": arguments,
            "message": "MCP tool not available - mock response"
        }
    except Exception as e:
        logger.error(f"MCP Tool {server_name}.{tool_name} failed: {e}")
        raise

def notify_goalie_if_needed(week_id: int):
    """Check if goalie needs to be notified and send SMS if quota reached"""
    (iso_year, iso_week, quota, goalie_notified), signups = get_week_info(week_id)
    if goalie_notified:
        return False
    if len(signups) >= quota:
        goalie_phone = get_goalie_phone()
        if not goalie_phone:
            print("[goalie_notify] quota reached but no goalie phone set")
            return False
        body = (
            f"Quota reached for Week {iso_week}, {iso_year}!\n"
            f"Total signups: {len(signups)} (quota {quota}).\n"
            f"Please secure a goalie.\n\n" + messaging.format_signup_list(signups)
        )
        messaging.send_sms(goalie_phone, body)
        mark_goalie_notified(week_id)
        return True
    return False

# --- Routes ---
@app.get("/")
def home():
    week_id = WeekUtils.get_or_create_current_week()
    (iso_year, iso_week, quota, goalie_notified), signups = get_week_info(week_id)
    return render_template(
        "home.html",
        iso_year=iso_year,
        iso_week=iso_week,
        quota=quota,
        count=len(signups),
        signups=signups
    )

@app.post("/signup")
def submit_signup():
    week_id = WeekUtils.get_or_create_current_week()
    # validate
    try:
        data = Signup(name=request.form.get("name",""), phone=request.form.get("phone"))
    except Exception as e:
        return redirect(url_for("home") + f"?error={str(e)}")

    # insert
    from contextlib import closing
    from models.database import db
    with closing(db()) as conn:
        conn.execute(
            "INSERT INTO signups(week_id, name, phone, created_at) VALUES(?,?,?,?)",
            (week_id, data.name, data.phone, datetime.utcnow().isoformat())
        )
        conn.commit()

    # auto-notify goalie if quota hit (one-time)
    notify_goalie_if_needed(week_id)
    return redirect(url_for("home"))

# --- Admin panel ---
@app.get("/admin")
def admin():
    require_admin()
    week_id = WeekUtils.get_or_create_current_week()
    (iso_year, iso_week, quota, goalie_notified), signups = get_week_info(week_id)
    numbers = get_broadcast_numbers()
    goalie_phone = get_goalie_phone()
    return render_template(
        "admin.html",
        token=request.args.get("token",""),
        iso_year=iso_year, iso_week=iso_week,
        quota=quota, count=len(signups),
        goalie_notified=bool(goalie_notified),
        numbers=numbers, goalie_phone=goalie_phone
    )

@app.post("/admin/quota")
def admin_set_quota():
    require_admin()
    week_id = WeekUtils.get_or_create_current_week()
    q = int(request.form.get("quota","0"))
    if q < 1:
        return redirect(url_for("admin", token=request.args.get("token","")) + "?error=bad_quota")
    set_quota(week_id, q)
    return redirect(url_for("admin", token=request.args.get("token","")))

@app.post("/admin/broadcast/add")
def admin_add_number():
    require_admin()
    phone = request.form.get("phone","").strip()
    if not is_e164(phone):
        return redirect(url_for("admin", token=request.args.get("token","")) + "?error=bad_phone")
    add_broadcast_number(phone)
    return redirect(url_for("admin", token=request.args.get("token","")))

@app.post("/admin/broadcast/remove")
def admin_remove_number():
    require_admin()
    phone = request.form.get("phone","").strip()
    remove_broadcast_number(phone)
    return redirect(url_for("admin", token=request.args.get("token","")))

@app.post("/admin/broadcast/send")
def admin_broadcast():
    require_admin()
    week_id = WeekUtils.get_or_create_current_week()
    _, signups = get_week_info(week_id)
    messaging.broadcast_signups(signups)
    return redirect(url_for("admin", token=request.args.get("token","")))

@app.post("/admin/goalie")
def admin_set_goalie():
    require_admin()
    phone = request.form.get("goalie_phone","").strip()
    if phone and not is_e164(phone):
        return redirect(url_for("admin", token=request.args.get("token","")) + "?error=bad_goalie")
    set_goalie_phone(phone)
    return redirect(url_for("admin", token=request.args.get("token","")))

@app.post("/admin/notify-goalie")
def admin_notify_goalie():
    require_admin()
    week_id = WeekUtils.get_or_create_current_week()
    notify_goalie_if_needed(week_id)
    return redirect(url_for("admin", token=request.args.get("token","")))

@app.post("/admin/test-sms")
def admin_test_sms():
    require_admin()
    phone = request.form.get("test_phone","").strip() or get_goalie_phone()
    if not phone:
        return redirect(url_for("admin", token=request.args.get("token","")) + "?error=no_phone")
    messaging.send_sms(phone, "Test from Weekly Skate admin.")
    return redirect(url_for("admin", token=request.args.get("token","")) + "?ok=test_sent")

@app.post("/admin/test-payment")
def admin_test_payment():
    require_admin()
    try:
        success = payment.create_goalie_payment_request(1.00, "test@example.com")
        if success:
            return redirect(url_for("admin", token=request.args.get("token","")) + "?ok=payment_test_sent")
        else:
            return redirect(url_for("admin", token=request.args.get("token","")) + "?error=payment_test_failed")
    except Exception as e:
        print(f"[PAYMENT TEST ERROR] {e}")
        return redirect(url_for("admin", token=request.args.get("token","")) + "?error=payment_test_error")

@app.post("/admin/test-venmo")
def admin_test_venmo():
    require_admin()
    try:
        result = payment.create_venmo_friendly_order(10.00, "Test Goalie Fee")
        if result["success"]:
            return redirect(url_for("admin", token=request.args.get("token","")) + f"?ok=venmo_test_created&order_id={result['order_id']}")
        else:
            return redirect(url_for("admin", token=request.args.get("token","")) + "?error=venmo_test_failed")
    except Exception as e:
        print(f"[VENMO TEST ERROR] {e}")
        return redirect(url_for("admin", token=request.args.get("token","")) + "?error=venmo_test_error")

@app.post("/admin/pay-goalie")
def admin_pay_goalie():
    require_admin()
    try:
        venmo_username = request.form.get("venmo_username","").strip()
        amount = float(request.form.get("amount", 10.00))
        
        if not venmo_username:
            return redirect(url_for("admin", token=request.args.get("token","")) + "?error=no_venmo_username")
        
        week_id = WeekUtils.get_or_create_current_week()
        success = payment.send_payment_to_goalie(week_id, amount, venmo_username)
        
        if success:
            return redirect(url_for("admin", token=request.args.get("token","")) + f"?ok=goalie_paid&amount={amount}&username={venmo_username}")
        else:
            return redirect(url_for("admin", token=request.args.get("token","")) + "?error=goalie_payment_failed")
            
    except Exception as e:
        print(f"[GOALIE PAYMENT ERROR] {e}")
        return redirect(url_for("admin", token=request.args.get("token","")) + "?error=goalie_payment_error")

# --- Payment Routes ---
@app.get("/payment/success")
def payment_success():
    order_id = request.args.get("token")  # PayPal passes order ID as 'token'
    print(f"[PAYMENT SUCCESS] Order ID: {order_id}")
    return render_template("payment_success.html", order_id=order_id)

@app.get("/payment/cancel")
def payment_cancel():
    order_id = request.args.get("token")
    print(f"[PAYMENT CANCELLED] Order ID: {order_id}")
    return render_template("payment_cancel.html", order_id=order_id)

@app.get("/pay-goalie")
def pay_goalie_page():
    """Page with Venmo-enabled PayPal checkout for goalie payment"""
    return render_template("pay_goalie.html")

@app.post("/create-goalie-order")
def create_goalie_order():
    """API endpoint to create a Venmo-friendly PayPal order"""
    try:
        amount = float(request.form.get("amount", 10.00))
        result = payment.create_venmo_friendly_order(amount, "Weekly Skate Goalie Fee")
        
        if result["success"]:
            return {"success": True, "order_id": result["order_id"], "approval_url": result["approval_url"]}
        else:
            return {"success": False, "error": result.get("error", "Unknown error")}, 400
            
    except Exception as e:
        print(f"[CREATE ORDER ERROR] {e}")
        return {"success": False, "error": str(e)}, 500

@app.post("/sms-webhook")
@SecurityManager.require_twilio_signature
@require_rate_limit(lambda: SecurityManager.sanitize_phone_number(request.form.get('From', '')))
def sms_webhook():
    """Twilio webhook endpoint for incoming SMS messages with security"""
    try:
        # Get message details from Twilio webhook
        from_phone = request.form.get('From', '').strip()
        message_body = request.form.get('Body', '').strip()
        message_sid = request.form.get('MessageSid', '')
        
        print(f"[SMS WEBHOOK] Received message from {from_phone}")
        print(f"[SMS WEBHOOK] Message: {message_body}")
        print(f"[SMS WEBHOOK] SID: {message_sid}")
        
        # Check if this is from the goalie phone
        goalie_phone = get_goalie_phone()
        if not goalie_phone or from_phone != goalie_phone:
            print(f"[SMS WEBHOOK] Message not from goalie phone ({goalie_phone}), ignoring")
            return '<?xml version="1.0" encoding="UTF-8"?><Response></Response>', 200
        
        # Check if we have a current week that needs goalie confirmation
        week_id = WeekUtils.get_current_week_needing_goalie()
        if not week_id:
            print(f"[SMS WEBHOOK] No current week needing goalie confirmation")
            return '<?xml version="1.0" encoding="UTF-8"?><Response></Response>', 200
        
        # Use sophisticated NLP to analyze the message
        nlp_result = nlp.analyze_message(message_body)
        
        if nlp_result.is_confirmation:
            print(f"[SMS WEBHOOK] Goalie confirmation detected!")
            print(f"[SMS WEBHOOK] Confidence: {nlp_result.confidence.value} ({nlp_result.confidence_score:.2f})")
            
            # Get or prompt for Venmo username
            venmo_username = get_goalie_venmo_username(from_phone)
            
            # For high confidence confirmations, proceed immediately
            if nlp.is_high_confidence(message_body) or venmo_username:
                if not venmo_username:
                    # Ask for Venmo username with confidence-aware message
                    response_message = (
                        f"Great! I'm {nlp_result.confidence_score*100:.0f}% confident you confirmed the goalie. "
                        "To send your payment, please reply with your Venmo username (e.g., @username)"
                    )
                    messaging.send_sms(from_phone, response_message)
                    print(f"[SMS WEBHOOK] Requested Venmo username from goalie (high confidence)")
                else:
                    # Send payment automatically
                    success = payment.send_payment_to_goalie(week_id, 10.00, venmo_username)
                    if success:
                        response_message = f"Payment sent to @{venmo_username}! Thanks for securing the goalie. (Confidence: {nlp_result.confidence_score*100:.0f}%)"
                        messaging.send_sms(from_phone, response_message)
                        print(f"[SMS WEBHOOK] Automatic payment sent to @{venmo_username}")
                    else:
                        response_message = "Payment failed. Please contact admin."
                        messaging.send_sms(from_phone, response_message)
                        print(f"[SMS WEBHOOK] Payment failed for @{venmo_username}")
            
            # For medium confidence, ask for confirmation
            elif nlp_result.confidence == nlp.ConfidenceLevel.MEDIUM:
                response_message = (
                    f"I think you confirmed the goalie (confidence: {nlp_result.confidence_score*100:.0f}%). "
                    "Please reply 'YES' to confirm and proceed with payment, or 'NO' if I misunderstood."
                )
                messaging.send_sms(from_phone, response_message)
                print(f"[SMS WEBHOOK] Requested explicit confirmation (medium confidence)")
        
        # Check if message contains Venmo username (for when we asked for it)
        elif nlp.extract_venmo_username(message_body):
            venmo_username = nlp.extract_venmo_username(message_body)
            store_goalie_venmo_username(from_phone, venmo_username)
            
            # Now send the payment
            success = payment.send_payment_to_goalie(week_id, 10.00, venmo_username)
            if success:
                response_message = f"Payment sent to @{venmo_username}! Thanks for securing the goalie."
                messaging.send_sms(from_phone, response_message)
                print(f"[SMS WEBHOOK] Payment sent to newly provided @{venmo_username}")
            else:
                response_message = "Payment failed. Please contact admin."
                messaging.send_sms(from_phone, response_message)
                print(f"[SMS WEBHOOK] Payment failed for newly provided @{venmo_username}")
        
        else:
            print(f"[SMS WEBHOOK] Message did not match confirmation or Venmo username patterns")
        
        # Return empty TwiML response
        return '<?xml version="1.0" encoding="UTF-8"?><Response></Response>', 200
        
    except Exception as e:
        print(f"[SMS WEBHOOK ERROR] {e}")
        return '<?xml version="1.0" encoding="UTF-8"?><Response></Response>', 500

# (Optional) quick health
@app.get("/health")
def health():
    return {"ok": True, "time": datetime.utcnow().isoformat()}

if __name__ == "__main__":
    app.run(debug=True)
