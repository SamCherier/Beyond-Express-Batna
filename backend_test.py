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
BASE_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://beyond-logistics.preview.emergentagent.com')
API_BASE = f"{BASE_URL}/api"

# Test data - realistic Algerian data
TEST_USER = {
    "email": "admin@beyondexpress.dz",
    "password": "admin123",
    "name": "Admin Test User",
    "role": "admin"
}

# Admin user mentioned in review request
ADMIN_USER_ID = "9d275120-3f24-4c1a-86d4-3aeff0fa3e95"

TEST_ORDER_DATA = {
    "recipient": {
        "name": "Ahmed Benali",
        "phone": "0555123456",
        "address": "Rue Didouche Mourad, Cité El Badr",
        "wilaya": "Alger",
        "commune": "Bab Ezzouar"
    },
    "description": "Smartphone Samsung Galaxy A54 5G 128GB - Téléphone portable",
    "cod_amount": 45000.0,
    "service_type": "E-COMMERCE"
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
    """Test getting orders list - CRITICAL: Test for updated_at KeyError fix"""
    
    print("📋 Testing Get Orders (Critical Bug Fix Verification)...")
    
    try:
        response = requests.get(
            f"{API_BASE}/orders",
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            
            if isinstance(data, list):
                print(f"✅ SUCCESS: GET /api/orders returned 200 OK with {len(data)} orders")
                
                # Verify all orders have required fields including updated_at
                missing_fields = []
                orders_with_all_fields = 0
                
                required_fields = ['id', 'tracking_id', 'status', 'cod_amount', 'recipient', 'sender', 'updated_at']
                
                for i, order in enumerate(data):
                    order_missing = []
                    for field in required_fields:
                        if field not in order:
                            order_missing.append(field)
                    
                    if order_missing:
                        missing_fields.append(f"Order {i+1}: missing {order_missing}")
                    else:
                        orders_with_all_fields += 1
                    
                    # Check recipient structure
                    recipient = order.get('recipient', {})
                    if not isinstance(recipient, dict) or 'wilaya' not in recipient or 'commune' not in recipient:
                        missing_fields.append(f"Order {i+1}: recipient missing wilaya/commune")
                
                if not missing_fields:
                    test_results.add_result(
                        "Get Orders List - Critical Bug Fix",
                        True,
                        f"✅ CRITICAL FIX VERIFIED: All {len(data)} orders have required fields including updated_at. No KeyError occurred."
                    )
                    return True
                else:
                    test_results.add_result(
                        "Get Orders List - Critical Bug Fix",
                        False,
                        f"Some orders missing required fields: {orders_with_all_fields}/{len(data)} complete",
                        "; ".join(missing_fields[:5])  # Show first 5 issues
                    )
                    return False
            else:
                test_results.add_result(
                    "Get Orders List - Critical Bug Fix",
                    False,
                    "Response is not a list",
                    str(data)
                )
                return False
        elif response.status_code == 500:
            test_results.add_result(
                "Get Orders List - Critical Bug Fix",
                False,
                "❌ CRITICAL: 500 Internal Server Error - KeyError bug may still exist!",
                response.text
            )
            return False
        else:
            test_results.add_result(
                "Get Orders List - Critical Bug Fix",
                False,
                f"Get orders failed with status {response.status_code}",
                response.text
            )
            return False
            
    except Exception as e:
        test_results.add_result(
            "Get Orders List - Critical Bug Fix",
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

def test_dashboard_orders_by_status():
    """Test dashboard orders by status endpoint"""
    
    print("📊 Testing Dashboard - Orders by Status...")
    
    try:
        response = requests.get(
            f"{API_BASE}/dashboard/orders-by-status",
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            
            if isinstance(data, list):
                # Check if response has correct structure
                valid_structure = True
                french_labels_found = False
                
                for item in data:
                    if not isinstance(item, dict) or 'name' not in item or 'value' not in item:
                        valid_structure = False
                        break
                    
                    # Check for French labels
                    french_statuses = ["En stock", "Préparation", "Prêt", "En transit", "Livré", "Retourné"]
                    if item['name'] in french_statuses:
                        french_labels_found = True
                
                if valid_structure:
                    test_results.add_result(
                        "Dashboard - Orders by Status",
                        True,
                        f"Retrieved {len(data)} status groups, French labels: {french_labels_found}"
                    )
                    return True
                else:
                    test_results.add_result(
                        "Dashboard - Orders by Status",
                        False,
                        "Response structure invalid - missing name/value fields",
                        str(data)
                    )
                    return False
            else:
                test_results.add_result(
                    "Dashboard - Orders by Status",
                    False,
                    "Response is not a list",
                    str(data)
                )
                return False
        else:
            test_results.add_result(
                "Dashboard - Orders by Status",
                False,
                f"Orders by status failed with status {response.status_code}",
                response.text
            )
            return False
            
    except Exception as e:
        test_results.add_result(
            "Dashboard - Orders by Status",
            False,
            f"Orders by status request failed: {str(e)}"
        )
        return False

def test_dashboard_revenue_evolution():
    """Test dashboard revenue evolution endpoint"""
    
    print("📈 Testing Dashboard - Revenue Evolution...")
    
    try:
        response = requests.get(
            f"{API_BASE}/dashboard/revenue-evolution",
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            
            if isinstance(data, list) and len(data) == 7:
                # Check if response has correct structure for 7 days
                valid_structure = True
                french_days_found = False
                
                french_days = ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"]
                
                for item in data:
                    if not isinstance(item, dict) or 'name' not in item or 'date' not in item or 'revenus' not in item:
                        valid_structure = False
                        break
                    
                    # Check for French day names
                    if item['name'] in french_days:
                        french_days_found = True
                
                if valid_structure:
                    total_revenue = sum(item['revenus'] for item in data)
                    test_results.add_result(
                        "Dashboard - Revenue Evolution",
                        True,
                        f"Retrieved 7 days revenue data, French days: {french_days_found}, Total: {total_revenue} DA"
                    )
                    return True
                else:
                    test_results.add_result(
                        "Dashboard - Revenue Evolution",
                        False,
                        "Response structure invalid - missing name/date/revenus fields",
                        str(data)
                    )
                    return False
            else:
                test_results.add_result(
                    "Dashboard - Revenue Evolution",
                    False,
                    f"Response should be list of 7 items, got {len(data) if isinstance(data, list) else 'not a list'}",
                    str(data)
                )
                return False
        else:
            test_results.add_result(
                "Dashboard - Revenue Evolution",
                False,
                f"Revenue evolution failed with status {response.status_code}",
                response.text
            )
            return False
            
    except Exception as e:
        test_results.add_result(
            "Dashboard - Revenue Evolution",
            False,
            f"Revenue evolution request failed: {str(e)}"
        )
        return False

def test_dashboard_top_wilayas():
    """Test dashboard top wilayas endpoint"""
    
    print("🗺️ Testing Dashboard - Top Wilayas...")
    
    try:
        response = requests.get(
            f"{API_BASE}/dashboard/top-wilayas",
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            
            if isinstance(data, list):
                # Check if response has correct structure
                valid_structure = True
                has_algerian_wilayas = False
                
                algerian_wilayas = ["Alger", "Oran", "Constantine", "Batna", "Blida", "Sétif", "Annaba"]
                
                for item in data:
                    if not isinstance(item, dict) or 'name' not in item or 'value' not in item:
                        valid_structure = False
                        break
                    
                    # Check for Algerian wilaya names
                    if item['name'] in algerian_wilayas or item['name'] == "Non spécifié":
                        has_algerian_wilayas = True
                
                if valid_structure:
                    test_results.add_result(
                        "Dashboard - Top Wilayas",
                        True,
                        f"Retrieved {len(data)} wilayas (max 5), Algerian names: {has_algerian_wilayas}"
                    )
                    return True
                else:
                    test_results.add_result(
                        "Dashboard - Top Wilayas",
                        False,
                        "Response structure invalid - missing name/value fields",
                        str(data)
                    )
                    return False
            else:
                test_results.add_result(
                    "Dashboard - Top Wilayas",
                    False,
                    "Response is not a list",
                    str(data)
                )
                return False
        else:
            test_results.add_result(
                "Dashboard - Top Wilayas",
                False,
                f"Top wilayas failed with status {response.status_code}",
                response.text
            )
            return False
            
    except Exception as e:
        test_results.add_result(
            "Dashboard - Top Wilayas",
            False,
            f"Top wilayas request failed: {str(e)}"
        )
        return False

def test_orders_count_verification():
    """Test orders count matches expected 20 orders from review request"""
    
    print("🔢 Testing Orders Count Verification...")
    
    try:
        response = requests.get(
            f"{API_BASE}/orders",
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            
            if isinstance(data, list):
                order_count = len(data)
                expected_count = 20  # From review request
                
                # Check if we have the expected number of orders
                if order_count >= expected_count:
                    test_results.add_result(
                        "Orders Count Verification",
                        True,
                        f"✅ Found {order_count} orders (expected at least {expected_count})"
                    )
                    
                    # Verify admin user assignment
                    admin_orders = [order for order in data if order.get('user_id') == ADMIN_USER_ID]
                    test_results.add_result(
                        "Admin User Orders Assignment",
                        len(admin_orders) > 0,
                        f"Found {len(admin_orders)} orders assigned to admin user {ADMIN_USER_ID}"
                    )
                    return True
                else:
                    test_results.add_result(
                        "Orders Count Verification",
                        False,
                        f"Expected at least {expected_count} orders, found {order_count}",
                        "Database may not have been properly populated with test orders"
                    )
                    return False
            else:
                test_results.add_result(
                    "Orders Count Verification",
                    False,
                    "Response is not a list",
                    str(data)
                )
                return False
        else:
            test_results.add_result(
                "Orders Count Verification",
                False,
                f"Orders count check failed with status {response.status_code}",
                response.text
            )
            return False
            
    except Exception as e:
        test_results.add_result(
            "Orders Count Verification",
            False,
            f"Orders count check request failed: {str(e)}"
        )
        return False

def test_dashboard_stats():
    """Test existing dashboard stats endpoint"""
    
    print("📋 Testing Dashboard - Stats...")
    
    try:
        response = requests.get(
            f"{API_BASE}/dashboard/stats",
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            
            required_fields = ['total_orders', 'total_users', 'total_products', 'in_transit']
            
            if isinstance(data, dict) and all(field in data for field in required_fields):
                test_results.add_result(
                    "Dashboard - Stats",
                    True,
                    f"Stats retrieved: Orders={data['total_orders']}, Users={data['total_users']}, Products={data['total_products']}, In Transit={data['in_transit']}"
                )
                return True
            else:
                test_results.add_result(
                    "Dashboard - Stats",
                    False,
                    "Response missing required fields",
                    f"Expected: {required_fields}, Got: {list(data.keys()) if isinstance(data, dict) else 'not a dict'}"
                )
                return False
        else:
            test_results.add_result(
                "Dashboard - Stats",
                False,
                f"Dashboard stats failed with status {response.status_code}",
                response.text
            )
            return False
            
    except Exception as e:
        test_results.add_result(
            "Dashboard - Stats",
            False,
            f"Dashboard stats request failed: {str(e)}"
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
        ("AI Chat", test_ai_chat),
        ("Dashboard Stats", test_dashboard_stats),
        ("Dashboard Orders by Status", test_dashboard_orders_by_status),
        ("Dashboard Revenue Evolution", test_dashboard_revenue_evolution),
        ("Dashboard Top Wilayas", test_dashboard_top_wilayas)
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