#!/usr/bin/env python3
"""
Backend API Testing for Beyond Express - Phase 2 Orders Page Advanced Features
Tests all backend endpoints for the Orders Page Advanced Features implementation.
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
BASE_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://elogistics-hub.preview.emergentagent.com')
API_BASE = f"{BASE_URL}/api"

# Test data - realistic Algerian data
TEST_USER = {
    "email": "admin@beyondexpress.dz",
    "password": "admin123",
    "name": "Admin Test User",
    "role": "admin"
}

TEST_ORDER_DATA = {
    "recipient": {
        "name": "Ahmed Benali",
        "phone": "0555123456",
        "address": "Rue Didouche Mourad, Cité El Badr",
        "wilaya": "Alger",
        "commune": "Bab Ezzouar"
    },
    "product_name": "Smartphone Samsung Galaxy A54",
    "product_description": "Téléphone portable Samsung Galaxy A54 5G 128GB",
    "cod_amount": 45000.0,
    "weight": 0.5,
    "dimensions": "15x8x1 cm",
    "delivery_type": "standard"
}

TEST_TRACKING_EVENT = {
    "status": "in_transit",
    "location": "Centre de tri Alger",
    "notes": "Colis en cours de traitement au centre de tri"
}

# Global variables for test session
session_token = None
test_order_id = None
headers = {}

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

def test_authentication():
    """Test user authentication and get session token"""
    global session_token, headers
    
    print("🔐 Testing Authentication...")
    
    # First try to register the user
    try:
        register_response = requests.post(
            f"{API_BASE}/auth/register",
            json=TEST_USER,
            timeout=30
        )
        
        if register_response.status_code == 200:
            print("✅ User registered successfully")
        elif register_response.status_code == 400 and "already registered" in register_response.text:
            print("ℹ️ User already exists, proceeding with login")
        else:
            print(f"⚠️ Registration failed: {register_response.status_code} - {register_response.text}")
    except Exception as e:
        print(f"⚠️ Registration request failed: {str(e)}")
    
    try:
        # Test login
        response = requests.post(
            f"{API_BASE}/auth/login",
            json={"email": TEST_USER["email"], "password": TEST_USER["password"]},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            session_token = data.get('access_token')
            headers = {'Authorization': f'Bearer {session_token}'}
            
            test_results.add_result(
                "Authentication - Login",
                True,
                f"Successfully logged in as {data.get('user', {}).get('name', 'Unknown')}"
            )
            return True
        else:
            test_results.add_result(
                "Authentication - Login",
                False,
                f"Login failed with status {response.status_code}",
                response.text
            )
            return False
            
    except Exception as e:
        test_results.add_result(
            "Authentication - Login",
            False,
            f"Login request failed: {str(e)}"
        )
        return False

def test_order_creation():
    """Test order creation with wilaya/commune"""
    global test_order_id
    
    print("📦 Testing Order Creation...")
    
    try:
        response = requests.post(
            f"{API_BASE}/orders",
            json=TEST_ORDER_DATA,
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            test_order_id = data.get('id')
            
            # Verify wilaya and commune are included
            recipient = data.get('recipient', {})
            has_wilaya = 'wilaya' in recipient and recipient['wilaya'] == TEST_ORDER_DATA['recipient']['wilaya']
            has_commune = 'commune' in recipient and recipient['commune'] == TEST_ORDER_DATA['recipient']['commune']
            
            if has_wilaya and has_commune:
                test_results.add_result(
                    "Order Creation with Wilaya/Commune",
                    True,
                    f"Order created successfully with ID: {test_order_id}"
                )
                return True
            else:
                test_results.add_result(
                    "Order Creation with Wilaya/Commune",
                    False,
                    "Order created but missing wilaya/commune data",
                    f"Wilaya: {recipient.get('wilaya')}, Commune: {recipient.get('commune')}"
                )
                return False
        else:
            test_results.add_result(
                "Order Creation with Wilaya/Commune",
                False,
                f"Order creation failed with status {response.status_code}",
                response.text
            )
            return False
            
    except Exception as e:
        test_results.add_result(
            "Order Creation with Wilaya/Commune",
            False,
            f"Order creation request failed: {str(e)}"
        )
        return False

def test_get_orders():
    """Test getting orders list"""
    
    print("📋 Testing Get Orders...")
    
    try:
        response = requests.get(
            f"{API_BASE}/orders",
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            
            if isinstance(data, list):
                # Check if orders include wilaya/commune
                has_location_data = False
                for order in data:
                    recipient = order.get('recipient', {})
                    if 'wilaya' in recipient and 'commune' in recipient:
                        has_location_data = True
                        break
                
                test_results.add_result(
                    "Get Orders List",
                    True,
                    f"Retrieved {len(data)} orders, location data present: {has_location_data}"
                )
                return True
            else:
                test_results.add_result(
                    "Get Orders List",
                    False,
                    "Response is not a list",
                    str(data)
                )
                return False
        else:
            test_results.add_result(
                "Get Orders List",
                False,
                f"Get orders failed with status {response.status_code}",
                response.text
            )
            return False
            
    except Exception as e:
        test_results.add_result(
            "Get Orders List",
            False,
            f"Get orders request failed: {str(e)}"
        )
        return False

def test_tracking_events():
    """Test tracking events GET and POST"""
    
    print("🚚 Testing Tracking Events...")
    
    if not test_order_id:
        test_results.add_result(
            "Tracking Events",
            False,
            "No test order ID available"
        )
        return False
    
    # Test POST - Add tracking event
    try:
        response = requests.post(
            f"{API_BASE}/orders/{test_order_id}/tracking",
            json=TEST_TRACKING_EVENT,
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            test_results.add_result(
                "Add Tracking Event",
                True,
                "Tracking event added successfully"
            )
        else:
            test_results.add_result(
                "Add Tracking Event",
                False,
                f"Add tracking event failed with status {response.status_code}",
                response.text
            )
            return False
            
    except Exception as e:
        test_results.add_result(
            "Add Tracking Event",
            False,
            f"Add tracking event request failed: {str(e)}"
        )
        return False
    
    # Test GET - Get tracking events
    try:
        response = requests.get(
            f"{API_BASE}/orders/{test_order_id}/tracking",
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            
            if isinstance(data, list):
                test_results.add_result(
                    "Get Tracking Events",
                    True,
                    f"Retrieved {len(data)} tracking events"
                )
                return True
            else:
                test_results.add_result(
                    "Get Tracking Events",
                    False,
                    "Response is not a list",
                    str(data)
                )
                return False
        else:
            test_results.add_result(
                "Get Tracking Events",
                False,
                f"Get tracking events failed with status {response.status_code}",
                response.text
            )
            return False
            
    except Exception as e:
        test_results.add_result(
            "Get Tracking Events",
            False,
            f"Get tracking events request failed: {str(e)}"
        )
        return False

def test_bulk_status_update():
    """Test bulk status update"""
    
    print("🔄 Testing Bulk Status Update...")
    
    if not test_order_id:
        test_results.add_result(
            "Bulk Status Update",
            False,
            "No test order ID available"
        )
        return False
    
    try:
        response = requests.patch(
            f"{API_BASE}/orders/{test_order_id}/status",
            params={"status": "in_transit"},
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            test_results.add_result(
                "Bulk Status Update",
                True,
                "Order status updated successfully"
            )
            return True
        else:
            test_results.add_result(
                "Bulk Status Update",
                False,
                f"Status update failed with status {response.status_code}",
                response.text
            )
            return False
            
    except Exception as e:
        test_results.add_result(
            "Bulk Status Update",
            False,
            f"Status update request failed: {str(e)}"
        )
        return False

def test_bulk_bordereau_generation():
    """Test bulk bordereau generation"""
    
    print("📄 Testing Bulk Bordereau Generation...")
    
    if not test_order_id:
        test_results.add_result(
            "Bulk Bordereau Generation",
            False,
            "No test order ID available"
        )
        return False
    
    try:
        response = requests.post(
            f"{API_BASE}/orders/bordereau",
            json=[test_order_id],
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            # Check if response is PDF
            content_type = response.headers.get('content-type', '')
            if 'application/pdf' in content_type:
                test_results.add_result(
                    "Bulk Bordereau Generation",
                    True,
                    f"PDF generated successfully, size: {len(response.content)} bytes"
                )
                return True
            else:
                test_results.add_result(
                    "Bulk Bordereau Generation",
                    False,
                    f"Response is not PDF, content-type: {content_type}"
                )
                return False
        else:
            test_results.add_result(
                "Bulk Bordereau Generation",
                False,
                f"Bordereau generation failed with status {response.status_code}",
                response.text
            )
            return False
            
    except Exception as e:
        test_results.add_result(
            "Bulk Bordereau Generation",
            False,
            f"Bordereau generation request failed: {str(e)}"
        )
        return False

def test_ai_chat():
    """Test AI chat for risk score"""
    
    print("🤖 Testing AI Chat for Risk Score...")
    
    ai_message = {
        "message": "Analyse risk for order: COD 15000 DA, Wilaya: Alger",
        "model": "gpt-4o",
        "provider": "openai",
        "session_id": f"test-{uuid.uuid4()}"
    }
    
    try:
        response = requests.post(
            f"{API_BASE}/ai-chat",
            params=ai_message,
            headers=headers,
            timeout=60  # AI requests may take longer
        )
        
        if response.status_code == 200:
            data = response.json()
            
            if 'response' in data and data['response']:
                test_results.add_result(
                    "AI Chat for Risk Score",
                    True,
                    f"AI response received: {data['response'][:100]}..."
                )
                return True
            else:
                test_results.add_result(
                    "AI Chat for Risk Score",
                    False,
                    "AI response is empty or missing",
                    str(data)
                )
                return False
        else:
            test_results.add_result(
                "AI Chat for Risk Score",
                False,
                f"AI chat failed with status {response.status_code}",
                response.text
            )
            return False
            
    except Exception as e:
        test_results.add_result(
            "AI Chat for Risk Score",
            False,
            f"AI chat request failed: {str(e)}"
        )
        return False

def run_all_tests():
    """Run all backend tests"""
    
    print(f"🚀 Starting Backend API Tests for Beyond Express")
    print(f"Base URL: {BASE_URL}")
    print(f"API Base: {API_BASE}")
    print(f"{'='*60}")
    
    # Test sequence
    tests = [
        ("Authentication", test_authentication),
        ("Order Creation", test_order_creation),
        ("Get Orders", test_get_orders),
        ("Tracking Events", test_tracking_events),
        ("Bulk Status Update", test_bulk_status_update),
        ("Bulk Bordereau Generation", test_bulk_bordereau_generation),
        ("AI Chat", test_ai_chat)
    ]
    
    for test_name, test_func in tests:
        try:
            success = test_func()
            if not success and test_name == "Authentication":
                print("❌ Authentication failed - stopping tests")
                break
        except Exception as e:
            test_results.add_result(
                test_name,
                False,
                f"Test execution failed: {str(e)}"
            )
    
    # Print results
    test_results.print_summary()
    
    return test_results

if __name__ == "__main__":
    test_results = TestResults()
    results = run_all_tests()