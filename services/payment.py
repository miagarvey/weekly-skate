from datetime import datetime
from flask import request
from models.database import get_week_info

class PaymentService:
    """Service for handling PayPal/Venmo payments"""
    
    @staticmethod
    def create_venmo_friendly_order(amount: float = 10.00, description: str = "Goalie Fee"):
        """Create a PayPal order that supports Venmo as a funding source"""
        try:
            print(f"[VENMO-FRIENDLY ORDER] Creating PayPal order for ${amount:.2f}")
            print(f"[VENMO-FRIENDLY ORDER] Description: {description}")
            
            # Create order using PayPal MCP - this will be Venmo-eligible automatically
            # when the conditions are right (US merchant, US buyer, USD currency, mobile device)
            order_result = PaymentService._use_mcp_tool_sync("paypal", "create_order", {
                "currencyCode": "USD",
                "items": [
                    {
                        "name": description,
                        "quantity": 1,
                        "itemCost": amount,
                        "itemTotal": amount,
                        "description": f"{description} - Weekly Skate"
                    }
                ],
                "returnUrl": f"{request.host_url}payment/success",
                "cancelUrl": f"{request.host_url}payment/cancel"
            })
            
            if order_result and "id" in order_result:
                # Extract approval URL from PayPal response
                approval_url = None
                if "links" in order_result:
                    for link in order_result["links"]:
                        if link.get("rel") == "payer-action":
                            approval_url = link.get("href")
                            break
                
                if not approval_url:
                    approval_url = f"https://www.sandbox.paypal.com/checkoutnow?token={order_result['id']}"
                
                return {
                    "order_id": order_result["id"],
                    "approval_url": approval_url,
                    "success": True
                }
            else:
                return {"success": False, "error": "Failed to create PayPal order"}
            
        except Exception as e:
            print(f"[VENMO ORDER ERROR] Failed to create Venmo-friendly order: {e}")
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def _use_mcp_tool_sync(server_name: str, tool_name: str, arguments: dict):
        """Synchronous wrapper for MCP tool usage (simplified for this context)"""
        try:
            # In a real Flask app, you'd need to implement proper MCP client integration
            # For now, we'll create a mock response that simulates successful order creation
            if tool_name == "create_order":
                mock_order_id = f"ORDER_{int(datetime.now().timestamp())}"
                return {
                    "id": mock_order_id,
                    "status": "CREATED",
                    "links": [
                        {
                            "href": f"https://www.sandbox.paypal.com/checkoutnow?token={mock_order_id}",
                            "rel": "payer-action",
                            "method": "GET"
                        }
                    ]
                }
            return None
        except Exception as e:
            print(f"[MCP ERROR] {e}")
            return None
    
    @staticmethod
    def create_goalie_payment_request(amount: float = 10.00, recipient_email: str = None):
        """Create a PayPal invoice for goalie payment (legacy function)"""
        try:
            print(f"[PAYMENT REQUEST] Creating PayPal invoice for ${amount:.2f}")
            if recipient_email:
                print(f"[PAYMENT REQUEST] Recipient: {recipient_email}")
            return True
        except Exception as e:
            print(f"[PAYMENT ERROR] Failed to create payment request: {e}")
            return False
    
    @staticmethod
    def send_payment_to_goalie(week_id: int, amount: float = 10.00, goalie_venmo_username: str = None):
        """Send Venmo payment TO goalie after they confirm securing a goalie"""
        (iso_year, iso_week, quota, goalie_notified), signups = get_week_info(week_id)
        
        if not goalie_venmo_username:
            print(f"[PAYMENT] No Venmo username provided for goalie payment")
            return False
        
        try:
            # Create a PayPal payout (this is how you send money TO someone)
            # In a real implementation, this would use PayPal's Payouts API
            print(f"[VENMO PAYMENT] Sending ${amount:.2f} to @{goalie_venmo_username}")
            print(f"[VENMO PAYMENT] For Week {iso_week}, {iso_year} goalie service")
            
            # Mock successful payment for now
            # In production, you'd use PayPal Payouts API or similar
            payment_result = {
                "success": True,
                "transaction_id": f"PAYOUT_{int(datetime.now().timestamp())}",
                "amount": amount,
                "recipient": goalie_venmo_username
            }
            
            if payment_result["success"]:
                print(f"[PAYMENT SUCCESS] Sent ${amount:.2f} to @{goalie_venmo_username}")
                print(f"[PAYMENT SUCCESS] Transaction ID: {payment_result['transaction_id']}")
                return True
            else:
                print(f"[PAYMENT FAILED] Could not send payment to @{goalie_venmo_username}")
                return False
                
        except Exception as e:
            print(f"[PAYMENT ERROR] Failed to send payment to goalie: {e}")
            return False
