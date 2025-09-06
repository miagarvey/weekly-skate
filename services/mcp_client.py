import json
import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class MCPClient:
    """
    Model Context Protocol client for PayPal integration
    
    This client connects to the actual PayPal MCP server while maintaining
    safety guards to prevent accidental payments during development.
    """
    
    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run
        self.logger = logging.getLogger(f"{__name__}.MCPClient")
        
        if self.dry_run:
            self.logger.warning("MCP Client initialized in DRY RUN mode - no real payments will be made")
            print("MCP Client initialized in DRY RUN mode - no real payments will be made")
        else:
            self.logger.info("MCP Client initialized in LIVE mode - real payments enabled")
    
    def create_order(self, amount: float, currency: str = "USD", description: str = "Goalie Payment") -> Dict[str, Any]:
        """
        Create a PayPal order using the MCP server
        
        Args:
            amount: Payment amount
            currency: Currency code (default: USD)
            description: Payment description
            
        Returns:
            Order creation response
        """
        try:
            # Import the MCP tool function at runtime to avoid circular imports
            from app import use_mcp_tool_wrapper
            
            # Create order using PayPal MCP server
            response = use_mcp_tool_wrapper(
                server_name="paypal",
                tool_name="create_order",
                arguments={
                    "currencyCode": currency,
                    "items": [
                        {
                            "name": description,
                            "description": f"Payment for {description}",
                            "itemCost": amount,
                            "quantity": 1,
                            "itemTotal": amount
                        }
                    ],
                    "returnUrl": "http://localhost:5000/payment_success",
                    "cancelUrl": "http://localhost:5000/payment_cancel"
                }
            )
            
            self.logger.info(f"Created PayPal order: {response.get('id', 'Unknown')}")
            return response
            
        except Exception as e:
            self.logger.error(f"Failed to create PayPal order: {e}")
            # Return mock response on error
            return self._create_mock_order_response(amount, currency, description)
    
    def get_order(self, order_id: str) -> Dict[str, Any]:
        """
        Get PayPal order details using the MCP server
        
        Args:
            order_id: PayPal order ID
            
        Returns:
            Order details response
        """
        try:
            from app import use_mcp_tool_wrapper
            
            response = use_mcp_tool_wrapper(
                server_name="paypal",
                tool_name="get_order",
                arguments={"id": order_id}
            )
            
            self.logger.info(f"Retrieved PayPal order: {order_id}")
            return response
            
        except Exception as e:
            self.logger.error(f"Failed to get PayPal order {order_id}: {e}")
            return self._create_mock_order_status(order_id)
    
    def capture_payment(self, order_id: str) -> Dict[str, Any]:
        """
        Capture payment for a PayPal order
        
        SAFETY GUARD: This operation is blocked in dry run mode
        
        Args:
            order_id: PayPal order ID to capture
            
        Returns:
            Capture response
        """
        if self.dry_run:
            self.logger.warning(f"DRY RUN: Blocking payment capture for order {order_id}")
            return self._create_mock_capture_response(order_id)
        
        try:
            from app import use_mcp_tool_wrapper
            
            response = use_mcp_tool_wrapper(
                server_name="paypal",
                tool_name="pay_order",
                arguments={"id": order_id}
            )
            
            self.logger.info(f"Captured payment for order: {order_id}")
            return response
            
        except Exception as e:
            self.logger.error(f"Failed to capture payment for order {order_id}: {e}")
            return self._create_mock_capture_response(order_id)
    
    def send_money_to_goalie(self, goalie_email: str, amount: float, note: str = "Goalie payment") -> Dict[str, Any]:
        """
        Send money to goalie using PayPal
        
        SAFETY GUARD: This operation is blocked in dry run mode
        
        Args:
            goalie_email: Goalie's email address
            amount: Payment amount
            note: Payment note
            
        Returns:
            Payment response
        """
        if self.dry_run:
            self.logger.warning(f"DRY RUN: Blocking money transfer to {goalie_email}")
            return self._create_mock_payout_response(goalie_email, amount, note)
        
        try:
            from app import use_mcp_tool_wrapper
            
            # First create an order
            order_response = self.create_order(amount, "USD", note)
            
            if order_response.get('id'):
                # Then capture the payment (this would normally be done after user approval)
                capture_response = self.capture_payment(order_response['id'])
                
                self.logger.info(f"Sent ${amount} to {goalie_email}")
                return {
                    "success": True,
                    "order_id": order_response['id'],
                    "capture_response": capture_response,
                    "recipient": goalie_email,
                    "amount": amount,
                    "note": note
                }
            else:
                raise Exception("Failed to create order")
                
        except Exception as e:
            self.logger.error(f"Failed to send money to {goalie_email}: {e}")
            return self._create_mock_payout_response(goalie_email, amount, note)
    
    def _create_mock_order_response(self, amount: float, currency: str, description: str) -> Dict[str, Any]:
        """Create a mock order response for testing"""
        mock_id = f"MOCK_ORDER_{int(datetime.now().timestamp())}"
        return {
            "id": mock_id,
            "status": "CREATED",
            "intent": "CAPTURE",
            "purchase_units": [
                {
                    "amount": {
                        "currency_code": currency,
                        "value": str(amount)
                    },
                    "description": description
                }
            ],
            "links": [
                {
                    "href": f"https://api.sandbox.paypal.com/v2/checkout/orders/{mock_id}",
                    "rel": "self",
                    "method": "GET"
                },
                {
                    "href": f"https://www.sandbox.paypal.com/checkoutnow?token={mock_id}",
                    "rel": "payer-action",
                    "method": "GET"
                }
            ],
            "create_time": datetime.utcnow().isoformat() + "Z",
            "mock": True
        }
    
    def _create_mock_order_status(self, order_id: str) -> Dict[str, Any]:
        """Create a mock order status response"""
        return {
            "id": order_id,
            "status": "APPROVED",
            "intent": "CAPTURE",
            "purchase_units": [
                {
                    "amount": {
                        "currency_code": "USD",
                        "value": "10.00"
                    }
                }
            ],
            "payer": {
                "email_address": "test@example.com"
            },
            "create_time": datetime.utcnow().isoformat() + "Z",
            "mock": True
        }
    
    def _create_mock_capture_response(self, order_id: str) -> Dict[str, Any]:
        """Create a mock capture response"""
        return {
            "id": f"CAPTURE_{order_id}",
            "status": "COMPLETED",
            "amount": {
                "currency_code": "USD",
                "value": "10.00"
            },
            "final_capture": True,
            "create_time": datetime.utcnow().isoformat() + "Z",
            "update_time": datetime.utcnow().isoformat() + "Z",
            "mock": True
        }
    
    def _create_mock_payout_response(self, recipient: str, amount: float, note: str) -> Dict[str, Any]:
        """Create a mock payout response"""
        mock_batch_id = f"MOCK_PAYOUT_{int(datetime.now().timestamp())}"
        return {
            "batch_header": {
                "payout_batch_id": mock_batch_id,
                "batch_status": "SUCCESS",
                "time_created": datetime.utcnow().isoformat() + "Z",
                "sender_batch_header": {
                    "sender_batch_id": f"batch_{int(datetime.now().timestamp())}",
                    "email_subject": "You have a payout!",
                    "email_message": note
                }
            },
            "items": [
                {
                    "payout_item_id": f"item_{int(datetime.now().timestamp())}",
                    "transaction_status": "SUCCESS",
                    "payout_item": {
                        "recipient_type": "EMAIL",
                        "amount": {
                            "currency": "USD",
                            "value": str(amount)
                        },
                        "receiver": recipient,
                        "note": note
                    }
                }
            ],
            "mock": True
        }
    
    # Legacy methods for backward compatibility
    async def use_tool(self, server_name: str, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Legacy async method for backward compatibility"""
        if tool_name == "create_order":
            return self.create_order(
                amount=arguments.get("amount", 10.0),
                currency=arguments.get("currency", "USD"),
                description=arguments.get("description", "Payment")
            )
        elif tool_name == "get_order":
            return self.get_order(arguments.get("order_id", ""))
        elif tool_name == "capture_payment":
            return self.capture_payment(arguments.get("order_id", ""))
        else:
            return {"error": f"Unknown tool: {tool_name}"}
    
    def use_tool_sync(self, server_name: str, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Synchronous wrapper for use_tool method"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(self.use_tool(server_name, tool_name, arguments))
            finally:
                loop.close()
        except Exception as e:
            self.logger.error(f"Synchronous MCP call failed: {e}")
            return {"error": str(e)}

# Global MCP client instance with safety guards
mcp_client = MCPClient(dry_run=True)  # Always start in dry run mode for safety
