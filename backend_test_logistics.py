#!/usr/bin/env python3
"""
Backend API Testing for Logistics OS - Unified Tracking System & Time Travel
Tests critical features: Session/Auth, Orders API with Carrier Fields, Unified Tracking System, Time Travel
"""

import requests
import json
import uuid
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/app/frontend/.env')

# Configuration
BASE_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://cargo-command-18.preview.emergentagent.com')
API_BASE = f"{BASE_URL}/api"

# Test credentials from review request
ADMIN_CREDENTIALS = {
    "email": "cherier.sam@beyondexpress-batna.com",
    "password": "admin123456"
}

# Test order ID from review request
TEST_ORDER_ID = "8c1b0c8a-7a6d-441a-b168-a06e1c74e90e"

# Test data for Time Travel test
TIME_TRAVEL_ORDER_DATA = {
    "recipient": {
        "name": "Test Client",
        "phone": "0555999888",
        "address": "Test",
        "wilaya": "Ghardaïa",
        "commune": "Ghardaïa"
    },
    "description": "Time Travel Test",
    "cod_amount": 3000,
    "delivery_type": "Livraison à domicile"
}

# Global variables for test session
access_token = None
headers = {}
time_travel_order_id = None

class TestResults:
    def __init__(self):
        self.results = []
        self.passed = 0
        self.failed = 0
    
    def add_result(self, test_name, success, message, details=None):
        self.results.append({
            'test': test_name,
            'success': success,
            'message': message,
            'details': details,
            'timestamp': datetime.now().isoformat()
        })
        if success:
            self.passed += 1
        else:
            self.failed += 1
    
    def print_summary(self):
        print(f"\n{'='*60}")
        print(f"TEST SUMMARY")
        print(f"{'='*60}")
        print(f"Total Tests: {len(self.results)}")
        print(f"Passed: {self.passed}")
        print(f"Failed: {self.failed}")
        print(f"Success Rate: {(self.passed/len(self.results)*100):.1f}%")
        print(f"{'='*60}")
        
        for result in self.results:
            status = "✅ PASS" if result['success'] else "❌ FAIL"
            print(f"{status} - {result['test']}")
            if not result['success']:
                print(f"    Error: {result['message']}")
                if result['details']:
                    print(f"    Details: {result['details']}")
        print(f"{'='*60}")

def test_session_auth():
    """Test 1: Session/Auth Test - Login and verify access_token"""
    global access_token, headers
    
    print("🔐 Testing Session/Auth...")
    
    try:
        # Test login with admin credentials
        response = requests.post(
            f"{API_BASE}/auth/login",
            json=ADMIN_CREDENTIALS,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            access_token = data.get('access_token')
            headers = {'Authorization': f'Bearer {access_token}'}
            
            test_results.add_result(
                "Session/Auth - Login",
                True,
                f"Successfully logged in. Access token received: {access_token[:20]}..."
            )
            
            # Test GET /api/auth/me with the token
            me_response = requests.get(
                f"{API_BASE}/auth/me",
                headers=headers,
                timeout=30
            )
            
            if me_response.status_code == 200:
                user_data = me_response.json()
                test_results.add_result(
                    "Session/Auth - /auth/me",
                    True,
                    f"Token verification successful. User: {user_data.get('name', 'Unknown')}"
                )
                return True
            else:
                test_results.add_result(
                    "Session/Auth - /auth/me",
                    False,
                    f"/auth/me failed with status {me_response.status_code}",
                    me_response.text
                )
                return False
        else:
            test_results.add_result(
                "Session/Auth - Login",
                False,
                f"Login failed with status {response.status_code}",
                response.text
            )
            return False
            
    except Exception as e:
        test_results.add_result(
            "Session/Auth - Login",
            False,
            f"Login request failed: {str(e)}"
        )
        return False

def test_orders_api_with_carrier_fields():
    """Test 2: Orders API with Carrier Fields - GET /api/orders should return orders with carrier fields"""
    
    print("📦 Testing Orders API with Carrier Fields...")
    
    try:
        response = requests.get(
            f"{API_BASE}/orders",
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            
            if isinstance(data, dict) and 'orders' in data:
                orders = data['orders']
            elif isinstance(data, list):
                orders = data
            else:
                test_results.add_result(
                    "Orders API - Response Format",
                    False,
                    "Unexpected response format",
                    str(data)
                )
                return False
            
            if len(orders) > 0:
                # Check for carrier fields in orders
                carrier_fields_found = 0
                test_order_found = False
                
                for order in orders:
                    has_carrier_type = 'carrier_type' in order
                    has_carrier_tracking = 'carrier_tracking_id' in order
                    
                    if has_carrier_type and has_carrier_tracking:
                        carrier_fields_found += 1
                    
                    # Check for the specific test order
                    if order.get('id') == TEST_ORDER_ID:
                        test_order_found = True
                        carrier_type = order.get('carrier_type')
                        carrier_tracking = order.get('carrier_tracking_id')
                        
                        if carrier_type == 'ZR Express':
                            test_results.add_result(
                                "Orders API - Test Order ZR Express",
                                True,
                                f"Test order {TEST_ORDER_ID} found with ZR Express carrier"
                            )
                        else:
                            test_results.add_result(
                                "Orders API - Test Order ZR Express",
                                False,
                                f"Test order found but carrier_type is '{carrier_type}', expected 'ZR Express'"
                            )
                
                test_results.add_result(
                    "Orders API - Carrier Fields",
                    carrier_fields_found > 0,
                    f"Found {carrier_fields_found}/{len(orders)} orders with carrier fields (carrier_type, carrier_tracking_id)"
                )
                
                if not test_order_found:
                    test_results.add_result(
                        "Orders API - Test Order Exists",
                        False,
                        f"Test order {TEST_ORDER_ID} not found in orders list"
                    )
                
                return carrier_fields_found > 0
            else:
                test_results.add_result(
                    "Orders API - Orders Count",
                    False,
                    "No orders found in response"
                )
                return False
        else:
            test_results.add_result(
                "Orders API - Response",
                False,
                f"GET /api/orders failed with status {response.status_code}",
                response.text
            )
            return False
            
    except Exception as e:
        test_results.add_result(
            "Orders API - Request",
            False,
            f"GET /api/orders request failed: {str(e)}"
        )
        return False

def test_unified_tracking_time_travel():
    """Test 3: Unified Tracking System - Time Travel Test"""
    global time_travel_order_id
    
    print("🚀 Testing Unified Tracking System - Time Travel...")
    
    # Step 1: Create a new test order for Ghardaïa
    try:
        create_response = requests.post(
            f"{API_BASE}/orders",
            json=TIME_TRAVEL_ORDER_DATA,
            headers=headers,
            timeout=30
        )
        
        if create_response.status_code == 200:
            order_data = create_response.json()
            time_travel_order_id = order_data.get('id')
            
            test_results.add_result(
                "Time Travel - Order Creation",
                True,
                f"Test order created for Ghardaïa with ID: {time_travel_order_id}"
            )
        else:
            test_results.add_result(
                "Time Travel - Order Creation",
                False,
                f"Order creation failed with status {create_response.status_code}",
                create_response.text
            )
            return False
            
    except Exception as e:
        test_results.add_result(
            "Time Travel - Order Creation",
            False,
            f"Order creation request failed: {str(e)}"
        )
        return False
    
    # Step 2: Ship it with Smart Router
    try:
        ship_response = requests.post(
            f"{API_BASE}/shipping/bulk-ship",
            json={
                "order_ids": [time_travel_order_id],
                "use_smart_routing": True
            },
            headers=headers,
            timeout=30
        )
        
        if ship_response.status_code == 200:
            ship_data = ship_response.json()
            results = ship_data.get('results', [])
            
            if results and len(results) > 0:
                result = results[0]
                carrier_name = result.get('carrier_name', '')
                
                if 'ZR Express' in carrier_name or 'zr_express' in carrier_name.lower():
                    test_results.add_result(
                        "Time Travel - Smart Router ZR Assignment",
                        True,
                        f"Order assigned to ZR Express (southern coverage): {carrier_name}"
                    )
                else:
                    test_results.add_result(
                        "Time Travel - Smart Router ZR Assignment",
                        False,
                        f"Expected ZR Express for Ghardaïa, got: {carrier_name}"
                    )
            else:
                test_results.add_result(
                    "Time Travel - Smart Router Response",
                    False,
                    "No results in bulk-ship response",
                    str(ship_data)
                )
        else:
            test_results.add_result(
                "Time Travel - Smart Router",
                False,
                f"Bulk ship failed with status {ship_response.status_code}",
                ship_response.text
            )
            return False
            
    except Exception as e:
        test_results.add_result(
            "Time Travel - Smart Router",
            False,
            f"Bulk ship request failed: {str(e)}"
        )
        return False
    
    # Step 3: Test Time Travel - First call (should change to in_transit)
    try:
        sync_response_1 = requests.post(
            f"{API_BASE}/shipping/sync-status/{time_travel_order_id}",
            json={"force_advance": True},
            headers=headers,
            timeout=30
        )
        
        if sync_response_1.status_code == 200:
            sync_data_1 = sync_response_1.json()
            new_status_1 = sync_data_1.get('new_status', '')
            
            if new_status_1 == 'in_transit':
                test_results.add_result(
                    "Time Travel - First Advance",
                    True,
                    f"First time travel successful: status changed to {new_status_1}"
                )
            else:
                test_results.add_result(
                    "Time Travel - First Advance",
                    False,
                    f"Expected 'in_transit', got '{new_status_1}'",
                    str(sync_data_1)
                )
        else:
            test_results.add_result(
                "Time Travel - First Advance",
                False,
                f"First sync failed with status {sync_response_1.status_code}",
                sync_response_1.text
            )
            
    except Exception as e:
        test_results.add_result(
            "Time Travel - First Advance",
            False,
            f"First sync request failed: {str(e)}"
        )
    
    # Step 4: Test Time Travel - Second call (should change to delivered)
    try:
        sync_response_2 = requests.post(
            f"{API_BASE}/shipping/sync-status/{time_travel_order_id}",
            json={"force_advance": True},
            headers=headers,
            timeout=30
        )
        
        if sync_response_2.status_code == 200:
            sync_data_2 = sync_response_2.json()
            new_status_2 = sync_data_2.get('new_status', '')
            
            if new_status_2 == 'delivered':
                test_results.add_result(
                    "Time Travel - Second Advance",
                    True,
                    f"Second time travel successful: status changed to {new_status_2}"
                )
            else:
                test_results.add_result(
                    "Time Travel - Second Advance",
                    False,
                    f"Expected 'delivered', got '{new_status_2}'",
                    str(sync_data_2)
                )
        else:
            test_results.add_result(
                "Time Travel - Second Advance",
                False,
                f"Second sync failed with status {sync_response_2.status_code}",
                sync_response_2.text
            )
            
    except Exception as e:
        test_results.add_result(
            "Time Travel - Second Advance",
            False,
            f"Second sync request failed: {str(e)}"
        )
    
    return True

def test_timeline_api():
    """Test 4: Timeline API Test - GET /api/shipping/timeline/{order_id}"""
    
    print("📊 Testing Timeline API...")
    
    # Test with the time travel order if available, otherwise use test order
    test_order = time_travel_order_id if time_travel_order_id else TEST_ORDER_ID
    
    try:
        response = requests.get(
            f"{API_BASE}/shipping/timeline/{test_order}",
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            
            # Check required fields
            required_fields = ['current_status', 'carrier_type', 'carrier_tracking_id', 'timeline']
            missing_fields = [field for field in required_fields if field not in data]
            
            if not missing_fields:
                timeline = data.get('timeline', [])
                
                # Verify timeline structure
                timeline_valid = True
                step_count = 0
                
                for step in timeline:
                    if not isinstance(step, dict):
                        timeline_valid = False
                        break
                    
                    step_fields = ['status', 'label', 'completed', 'current']
                    if not all(field in step for field in step_fields):
                        timeline_valid = False
                        break
                    
                    step_count += 1
                
                if timeline_valid and step_count > 0:
                    test_results.add_result(
                        "Timeline API - Structure",
                        True,
                        f"Timeline API returned valid structure with {step_count} steps. Current status: {data.get('current_status')}"
                    )
                    
                    # Check for specific timeline steps
                    expected_steps = ['pending', 'preparing', 'in_transit', 'delivered']
                    found_steps = [step.get('status') for step in timeline]
                    matching_steps = [step for step in expected_steps if step in found_steps]
                    
                    test_results.add_result(
                        "Timeline API - Expected Steps",
                        len(matching_steps) >= 3,
                        f"Found {len(matching_steps)}/{len(expected_steps)} expected timeline steps: {matching_steps}"
                    )
                    
                    return True
                else:
                    test_results.add_result(
                        "Timeline API - Timeline Structure",
                        False,
                        f"Invalid timeline structure or empty timeline",
                        f"Timeline: {timeline}"
                    )
                    return False
            else:
                test_results.add_result(
                    "Timeline API - Required Fields",
                    False,
                    f"Missing required fields: {missing_fields}",
                    str(data)
                )
                return False
        else:
            test_results.add_result(
                "Timeline API - Response",
                False,
                f"Timeline API failed with status {response.status_code}",
                response.text
            )
            return False
            
    except Exception as e:
        test_results.add_result(
            "Timeline API - Request",
            False,
            f"Timeline API request failed: {str(e)}"
        )
        return False

def main():
    """Run all Logistics OS backend tests"""
    global test_results
    test_results = TestResults()
    
    print("🚀 Starting Logistics OS Backend Testing")
    print("=" * 60)
    print("Testing critical features:")
    print("1. Session/Auth Test")
    print("2. Orders API with Carrier Fields") 
    print("3. Unified Tracking System - Time Travel Test")
    print("4. Timeline API Test")
    print("=" * 60)
    
    # Test 1: Session/Auth
    if not test_session_auth():
        print("❌ Authentication failed - stopping tests")
        test_results.print_summary()
        return
    
    # Test 2: Orders API with Carrier Fields
    test_orders_api_with_carrier_fields()
    
    # Test 3: Unified Tracking System - Time Travel
    test_unified_tracking_time_travel()
    
    # Test 4: Timeline API
    test_timeline_api()
    
    # Print final summary
    test_results.print_summary()
    
    print("\n🎯 LOGISTICS OS BACKEND TEST COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    main()