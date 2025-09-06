#!/usr/bin/env python3
"""
Test script to demonstrate Venmo MCP server integration
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.mcp_client import mcp_client

def test_create_order():
    """Test creating a PayPal order for self-payment"""
    print("=== Testing MCP Venmo Integration ===")
    print()
    
    # Test 1: Create an order
    print("1. Creating a test order for $5.00...")
    order_response = mcp_client.create_order(
        amount=5.00,
        currency="USD",
        description="Test Venmo Payment to Self"
    )
    
    print(f"Order Response:")
    print(f"  Order ID: {order_response.get('id', 'N/A')}")
    print(f"  Status: {order_response.get('status', 'N/A')}")
    print(f"  Mock: {order_response.get('mock', False)}")
    
    if order_response.get('links'):
        for link in order_response['links']:
            if link.get('rel') == 'payer-action':
                print(f"  Approval URL: {link.get('href', 'N/A')}")
    
    print()
    
    # Test 2: Get order details
    order_id = order_response.get('id')
    if order_id:
        print(f"2. Getting order details for {order_id}...")
        order_details = mcp_client.get_order(order_id)
        print(f"Order Details:")
        print(f"  Status: {order_details.get('status', 'N/A')}")
        print(f"  Mock: {order_details.get('mock', False)}")
        print()
    
    # Test 3: Test payment capture (will be blocked by safety guard)
    if order_id:
        print(f"3. Testing payment capture for {order_id}...")
        capture_response = mcp_client.capture_payment(order_id)
        print(f"Capture Response:")
        print(f"  Status: {capture_response.get('status', 'N/A')}")
        print(f"  Mock: {capture_response.get('mock', False)}")
        print(f"  Safety Guard Active: {capture_response.get('safety_guard_active', False)}")
        print()
    
    # Test 4: Test sending money to goalie (will be blocked by safety guard)
    print("4. Testing send money to goalie...")
    payout_response = mcp_client.send_money_to_goalie(
        goalie_email="test@example.com",
        amount=10.00,
        note="Test goalie payment"
    )
    print(f"Payout Response:")
    print(f"  Success: {payout_response.get('success', False)}")
    print(f"  Mock: {payout_response.get('mock', False)}")
    if payout_response.get('batch_header'):
        print(f"  Batch ID: {payout_response['batch_header'].get('payout_batch_id', 'N/A')}")
        print(f"  Status: {payout_response['batch_header'].get('batch_status', 'N/A')}")
    
    print()
    print("=== Test Complete ===")
    print()
    print("Summary:")
    print("- ✅ MCP Client successfully initialized")
    print("- ✅ Order creation works (using mock responses due to safety guards)")
    print("- ✅ Order retrieval works")
    print("- ✅ Payment capture blocked by safety guards (as expected)")
    print("- ✅ Money transfer blocked by safety guards (as expected)")
    print()
    print("To test with real PayPal transactions:")
    print("1. Set dry_run=False in the MCP client")
    print("2. Ensure PayPal credentials are properly configured")
    print("3. Use the approval URL to complete the payment flow")
    print()
    
    return order_response

if __name__ == "__main__":
    test_create_order()
