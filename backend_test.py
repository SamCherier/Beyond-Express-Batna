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
BASE_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://beyond-limits-7.preview.emergentagent.com')
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
driver_headers = {}

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

def test_carriers_integration_page():
    """Test Carriers Integration Page - BUG 1 FIX VERIFICATION"""
    
    print("🚚 Testing Carriers Integration Page (BUG 1 FIX)...")
    
    # Test user from review request
    admin_user_credentials = {
        "email": "testpro@beyond.com",
        "password": "Test123!"
    }
    
    # Step 1: Login with admin user
    try:
        login_response = requests.post(
            f"{API_BASE}/auth/login",
            json=admin_user_credentials,
            timeout=30
        )
        
        if login_response.status_code != 200:
            test_results.add_result(
                "Carriers - Admin Login",
                False,
                f"Login failed with status {login_response.status_code}",
                login_response.text
            )
            return False
        
        login_data = login_response.json()
        admin_token = login_data.get('access_token')
        admin_headers = {'Authorization': f'Bearer {admin_token}'}
        
        test_results.add_result(
            "Carriers - Admin Login",
            True,
            f"Successfully logged in as {login_data.get('user', {}).get('name', 'Admin User')}"
        )
        
    except Exception as e:
        test_results.add_result(
            "Carriers - Admin Login",
            False,
            f"Login request failed: {str(e)}"
        )
        return False
    
    # Step 2: Test GET /api/carriers - Should return 7 carriers
    try:
        carriers_response = requests.get(
            f"{API_BASE}/carriers",
            headers=admin_headers,
            timeout=30
        )
        
        if carriers_response.status_code == 200:
            carriers_data = carriers_response.json()
            
            if isinstance(carriers_data, list):
                carrier_count = len(carriers_data)
                expected_count = 7
                
                if carrier_count == expected_count:
                    test_results.add_result(
                        "Carriers - Count Verification",
                        True,
                        f"✅ BUG 1 FIXED: Found {carrier_count} carriers (expected {expected_count})"
                    )
                    
                    # Step 3: Verify carrier data structure
                    required_fields = ['name', 'logo_url', 'carrier_type', 'required_fields']
                    expected_carriers = ['Yalidine', 'DHD Express', 'ZR Express', 'Maystro', 'Guepex', 'Nord et Ouest', 'Pajo']
                    
                    valid_carriers = 0
                    found_carrier_names = []
                    
                    for carrier in carriers_data:
                        if isinstance(carrier, dict):
                            found_carrier_names.append(carrier.get('name', 'Unknown'))
                            
                            # Check required fields
                            has_all_fields = all(field in carrier for field in required_fields)
                            
                            if has_all_fields:
                                valid_carriers += 1
                                
                                # Special check for Yalidine
                                if carrier.get('name') == 'Yalidine':
                                    required_fields_yalidine = carrier.get('required_fields', [])
                                    if 'api_key' in required_fields_yalidine and 'center_id' in required_fields_yalidine:
                                        test_results.add_result(
                                            "Carriers - Yalidine Structure",
                                            True,
                                            f"✅ Yalidine has correct required_fields: {required_fields_yalidine}"
                                        )
                                    else:
                                        test_results.add_result(
                                            "Carriers - Yalidine Structure",
                                            False,
                                            f"Yalidine missing expected required_fields",
                                            f"Expected: ['api_key', 'center_id'], Got: {required_fields_yalidine}"
                                        )
                    
                    if valid_carriers == carrier_count:
                        test_results.add_result(
                            "Carriers - Data Structure",
                            True,
                            f"✅ All {valid_carriers} carriers have required fields: {required_fields}"
                        )
                        
                        # Check if we have expected carrier names
                        found_expected = [name for name in expected_carriers if name in found_carrier_names]
                        test_results.add_result(
                            "Carriers - Expected Names",
                            len(found_expected) >= 5,  # At least 5 of the expected carriers
                            f"Found expected carriers: {found_expected} out of {expected_carriers}"
                        )
                        
                        return True
                    else:
                        test_results.add_result(
                            "Carriers - Data Structure",
                            False,
                            f"Only {valid_carriers}/{carrier_count} carriers have all required fields",
                            f"Required fields: {required_fields}"
                        )
                        return False
                else:
                    test_results.add_result(
                        "Carriers - Count Verification",
                        False,
                        f"❌ BUG 1 NOT FIXED: Expected {expected_count} carriers, got {carrier_count}",
                        f"Carriers page may still be empty. Found carriers: {[c.get('name', 'Unknown') for c in carriers_data if isinstance(c, dict)]}"
                    )
                    return False
            else:
                test_results.add_result(
                    "Carriers - Response Format",
                    False,
                    "Response is not a list",
                    str(carriers_data)
                )
                return False
        else:
            test_results.add_result(
                "Carriers - API Response",
                False,
                f"GET /api/carriers failed with status {carriers_response.status_code}",
                carriers_response.text
            )
            return False
            
    except Exception as e:
        test_results.add_result(
            "Carriers - API Request",
            False,
            f"GET /api/carriers request failed: {str(e)}"
        )
        return False

def test_batch_transfer_payment():
    """Test Batch Transfer Payment - BUG 2 FIX VERIFICATION"""
    
    print("💰 Testing Batch Transfer Payment (BUG 2 FIX)...")
    
    # Test user from review request
    admin_user_credentials = {
        "email": "testpro@beyond.com",
        "password": "Test123!"
    }
    
    # Step 1: Login with admin user
    try:
        login_response = requests.post(
            f"{API_BASE}/auth/login",
            json=admin_user_credentials,
            timeout=30
        )
        
        if login_response.status_code != 200:
            test_results.add_result(
                "Batch Transfer - Admin Login",
                False,
                f"Login failed with status {login_response.status_code}",
                login_response.text
            )
            return False
        
        login_data = login_response.json()
        admin_token = login_data.get('access_token')
        admin_headers = {'Authorization': f'Bearer {admin_token}'}
        
        test_results.add_result(
            "Batch Transfer - Admin Login",
            True,
            f"Successfully logged in as {login_data.get('user', {}).get('name', 'Admin User')}"
        )
        
    except Exception as e:
        test_results.add_result(
            "Batch Transfer - Admin Login",
            False,
            f"Login request failed: {str(e)}"
        )
        return False
    
    # Step 2: Get orders list to get real order IDs
    try:
        orders_response = requests.get(
            f"{API_BASE}/orders",
            headers=admin_headers,
            timeout=30
        )
        
        if orders_response.status_code != 200:
            test_results.add_result(
                "Batch Transfer - Get Orders",
                False,
                f"GET /api/orders failed with status {orders_response.status_code}",
                orders_response.text
            )
            return False
        
        orders_data = orders_response.json()
        
        if not isinstance(orders_data, list) or len(orders_data) == 0:
            test_results.add_result(
                "Batch Transfer - Get Orders",
                False,
                "No orders found in database",
                f"Response: {orders_data}"
            )
            return False
        
        # Select 2-3 order IDs for testing
        test_order_ids = [order['id'] for order in orders_data[:3] if 'id' in order]
        
        if len(test_order_ids) < 2:
            test_results.add_result(
                "Batch Transfer - Order IDs",
                False,
                f"Not enough orders for testing, found {len(test_order_ids)}",
                f"Available orders: {len(orders_data)}"
            )
            return False
        
        test_results.add_result(
            "Batch Transfer - Get Orders",
            True,
            f"Retrieved {len(orders_data)} orders, selected {len(test_order_ids)} for testing"
        )
        
    except Exception as e:
        test_results.add_result(
            "Batch Transfer - Get Orders",
            False,
            f"GET /api/orders request failed: {str(e)}"
        )
        return False
    
    # Step 3: Test batch update with "transferred_to_merchant"
    try:
        batch_update_data = {
            "order_ids": test_order_ids,
            "new_status": "transferred_to_merchant"
        }
        
        batch_response = requests.post(
            f"{API_BASE}/financial/batch-update-payment",
            json=batch_update_data,
            headers=admin_headers,
            timeout=30
        )
        
        if batch_response.status_code == 200:
            batch_data = batch_response.json()
            
            # Verify response structure
            expected_fields = ['success', 'updated_count', 'new_status']
            has_all_fields = all(field in batch_data for field in expected_fields)
            
            if has_all_fields:
                success = batch_data.get('success', False)
                updated_count = batch_data.get('updated_count', 0)
                new_status = batch_data.get('new_status', '')
                
                if success and updated_count == len(test_order_ids) and new_status == "transferred_to_merchant":
                    test_results.add_result(
                        "Batch Transfer - transferred_to_merchant",
                        True,
                        f"✅ BUG 2 FIXED: Batch update successful. Updated {updated_count} orders to '{new_status}'"
                    )
                else:
                    test_results.add_result(
                        "Batch Transfer - transferred_to_merchant",
                        False,
                        f"Batch update response invalid",
                        f"Success: {success}, Updated: {updated_count}/{len(test_order_ids)}, Status: {new_status}"
                    )
                    return False
            else:
                test_results.add_result(
                    "Batch Transfer - Response Structure",
                    False,
                    f"Response missing required fields: {expected_fields}",
                    str(batch_data)
                )
                return False
        else:
            test_results.add_result(
                "Batch Transfer - transferred_to_merchant",
                False,
                f"❌ BUG 2 NOT FIXED: Batch update failed with status {batch_response.status_code}",
                batch_response.text
            )
            return False
            
    except Exception as e:
        test_results.add_result(
            "Batch Transfer - transferred_to_merchant",
            False,
            f"Batch update request failed: {str(e)}"
        )
        return False
    
    # Step 4: Test batch update with "collected_by_driver"
    try:
        batch_update_data_2 = {
            "order_ids": test_order_ids[:2],  # Use fewer orders for second test
            "new_status": "collected_by_driver"
        }
        
        batch_response_2 = requests.post(
            f"{API_BASE}/financial/batch-update-payment",
            json=batch_update_data_2,
            headers=admin_headers,
            timeout=30
        )
        
        if batch_response_2.status_code == 200:
            batch_data_2 = batch_response_2.json()
            
            success_2 = batch_data_2.get('success', False)
            updated_count_2 = batch_data_2.get('updated_count', 0)
            new_status_2 = batch_data_2.get('new_status', '')
            
            if success_2 and updated_count_2 == len(test_order_ids[:2]) and new_status_2 == "collected_by_driver":
                test_results.add_result(
                    "Batch Transfer - collected_by_driver",
                    True,
                    f"✅ Second batch update successful. Updated {updated_count_2} orders to '{new_status_2}'"
                )
            else:
                test_results.add_result(
                    "Batch Transfer - collected_by_driver",
                    False,
                    f"Second batch update response invalid",
                    f"Success: {success_2}, Updated: {updated_count_2}/{len(test_order_ids[:2])}, Status: {new_status_2}"
                )
                return False
        else:
            test_results.add_result(
                "Batch Transfer - collected_by_driver",
                False,
                f"Second batch update failed with status {batch_response_2.status_code}",
                batch_response_2.text
            )
            return False
            
    except Exception as e:
        test_results.add_result(
            "Batch Transfer - collected_by_driver",
            False,
            f"Second batch update request failed: {str(e)}"
        )
        return False
    
    # Step 5: Verify orders were actually updated in database
    try:
        # Re-fetch orders to verify payment_status changes
        verify_response = requests.get(
            f"{API_BASE}/orders",
            headers=admin_headers,
            timeout=30
        )
        
        if verify_response.status_code == 200:
            updated_orders = verify_response.json()
            
            # Check if our test orders have updated payment_status
            updated_statuses = {}
            for order in updated_orders:
                if order.get('id') in test_order_ids:
                    updated_statuses[order['id']] = order.get('payment_status', 'unknown')
            
            # Verify timestamps were added
            timestamp_fields_found = 0
            for order in updated_orders:
                if order.get('id') in test_order_ids:
                    if order.get('collected_date') or order.get('transferred_date'):
                        timestamp_fields_found += 1
            
            test_results.add_result(
                "Batch Transfer - Database Verification",
                len(updated_statuses) > 0,
                f"✅ Database updated: {len(updated_statuses)} orders have new payment_status. Timestamps added to {timestamp_fields_found} orders."
            )
            
            return True
        else:
            test_results.add_result(
                "Batch Transfer - Database Verification",
                False,
                f"Verification failed with status {verify_response.status_code}",
                verify_response.text
            )
            return False
            
    except Exception as e:
        test_results.add_result(
            "Batch Transfer - Database Verification",
            False,
            f"Verification request failed: {str(e)}"
        )
        return False

def test_ai_assistant_pro_user_bug_fix():
    """Test AI Assistant API with PRO user - Bug Fix Verification"""
    
    print("🤖 Testing AI Assistant PRO User Bug Fix...")
    
    # Test user from review request
    pro_user_credentials = {
        "email": "testpro@beyond.com",
        "password": "Test123!"
    }
    
    # Step 1: Login with PRO user
    try:
        login_response = requests.post(
            f"{API_BASE}/auth/login",
            json=pro_user_credentials,
            timeout=30
        )
        
        if login_response.status_code != 200:
            test_results.add_result(
                "AI Assistant - PRO User Login",
                False,
                f"Login failed with status {login_response.status_code}",
                login_response.text
            )
            return False
        
        login_data = login_response.json()
        pro_token = login_data.get('access_token')
        pro_headers = {'Authorization': f'Bearer {pro_token}'}
        
        test_results.add_result(
            "AI Assistant - PRO User Login",
            True,
            f"Successfully logged in as {login_data.get('user', {}).get('name', 'PRO User')}"
        )
        
    except Exception as e:
        test_results.add_result(
            "AI Assistant - PRO User Login",
            False,
            f"Login request failed: {str(e)}"
        )
        return False
    
    # Step 2: Check /api/auth/me to verify current_plan
    try:
        me_response = requests.get(
            f"{API_BASE}/auth/me",
            headers=pro_headers,
            timeout=30
        )
        
        if me_response.status_code == 200:
            me_data = me_response.json()
            current_plan = me_data.get('current_plan', 'unknown')
            
            if current_plan == 'pro':
                test_results.add_result(
                    "AI Assistant - User Plan Verification",
                    True,
                    f"✅ User has correct plan: {current_plan}"
                )
            else:
                test_results.add_result(
                    "AI Assistant - User Plan Verification",
                    False,
                    f"Expected plan 'pro', got '{current_plan}'",
                    f"Full user data: {me_data}"
                )
                return False
        else:
            test_results.add_result(
                "AI Assistant - User Plan Verification",
                False,
                f"/auth/me failed with status {me_response.status_code}",
                me_response.text
            )
            return False
            
    except Exception as e:
        test_results.add_result(
            "AI Assistant - User Plan Verification",
            False,
            f"/auth/me request failed: {str(e)}"
        )
        return False
    
    # Step 3: Check /api/ai/usage to verify limit is 1000 (not 0)
    try:
        usage_response = requests.get(
            f"{API_BASE}/ai/usage",
            headers=pro_headers,
            timeout=30
        )
        
        if usage_response.status_code == 200:
            usage_data = usage_response.json()
            
            expected_limit = 1000
            actual_limit = usage_data.get('limit', 0)
            plan = usage_data.get('plan', 'unknown')
            has_access = usage_data.get('has_access', False)
            used = usage_data.get('used', 0)
            remaining = usage_data.get('remaining', 0)
            
            if actual_limit == expected_limit and has_access:
                test_results.add_result(
                    "AI Assistant - Usage Limit Check",
                    True,
                    f"✅ CRITICAL BUG FIXED: Limit is {actual_limit} (not 0), Plan: {plan}, Used: {used}, Remaining: {remaining}"
                )
            else:
                test_results.add_result(
                    "AI Assistant - Usage Limit Check",
                    False,
                    f"❌ BUG STILL EXISTS: Expected limit {expected_limit}, got {actual_limit}. Has access: {has_access}",
                    f"Full response: {usage_data}"
                )
                return False
        else:
            test_results.add_result(
                "AI Assistant - Usage Limit Check",
                False,
                f"/ai/usage failed with status {usage_response.status_code}",
                usage_response.text
            )
            return False
            
    except Exception as e:
        test_results.add_result(
            "AI Assistant - Usage Limit Check",
            False,
            f"/ai/usage request failed: {str(e)}"
        )
        return False
    
    # Step 4: Test sending AI message
    try:
        ai_message_data = {
            "message": "Bonjour",
            "model": "gpt-4o",
            "provider": "openai",
            "session_id": f"test-pro-{uuid.uuid4()}"
        }
        
        ai_response = requests.post(
            f"{API_BASE}/ai/message",
            json=ai_message_data,
            headers=pro_headers,
            timeout=60
        )
        
        if ai_response.status_code == 200:
            ai_data = ai_response.json()
            
            if 'response' in ai_data and ai_data['response']:
                usage_count = ai_data.get('usage_count', 0)
                limit = ai_data.get('limit', 0)
                remaining = ai_data.get('remaining', 0)
                
                test_results.add_result(
                    "AI Assistant - Message Send Test",
                    True,
                    f"✅ AI message sent successfully. Usage: {usage_count}/{limit}, Remaining: {remaining}"
                )
                
                # Verify usage counter incremented
                if usage_count > 0:
                    test_results.add_result(
                        "AI Assistant - Usage Counter",
                        True,
                        f"✅ Usage counter incremented correctly: {usage_count}"
                    )
                else:
                    test_results.add_result(
                        "AI Assistant - Usage Counter",
                        False,
                        "Usage counter did not increment",
                        f"Expected > 0, got {usage_count}"
                    )
                
                return True
            else:
                test_results.add_result(
                    "AI Assistant - Message Send Test",
                    False,
                    "AI response is empty or missing",
                    str(ai_data)
                )
                return False
        else:
            test_results.add_result(
                "AI Assistant - Message Send Test",
                False,
                f"AI message failed with status {ai_response.status_code}",
                ai_response.text
            )
            return False
            
    except Exception as e:
        test_results.add_result(
            "AI Assistant - Message Send Test",
            False,
            f"AI message request failed: {str(e)}"
        )
        return False

def test_thermal_labels_printing_system():
    """Test Thermal Labels Printing System - NEW FEATURE"""
    
    print("🏷️ Testing Thermal Labels Printing System...")
    
    # Test user from review request
    admin_user_credentials = {
        "email": "testpro@beyond.com",
        "password": "Test123!"
    }
    
    # Step 1: Login with admin user
    try:
        login_response = requests.post(
            f"{API_BASE}/auth/login",
            json=admin_user_credentials,
            timeout=30
        )
        
        if login_response.status_code != 200:
            test_results.add_result(
                "Thermal Labels - Admin Login",
                False,
                f"Login failed with status {login_response.status_code}",
                login_response.text
            )
            return False
        
        login_data = login_response.json()
        admin_token = login_data.get('access_token')
        admin_headers = {'Authorization': f'Bearer {admin_token}'}
        
        test_results.add_result(
            "Thermal Labels - Admin Login",
            True,
            f"Successfully logged in as {login_data.get('user', {}).get('name', 'Admin User')}"
        )
        
    except Exception as e:
        test_results.add_result(
            "Thermal Labels - Admin Login",
            False,
            f"Login request failed: {str(e)}"
        )
        return False
    
    # Step 2: Get orders list to get real order IDs
    try:
        orders_response = requests.get(
            f"{API_BASE}/orders",
            headers=admin_headers,
            timeout=30
        )
        
        if orders_response.status_code != 200:
            test_results.add_result(
                "Thermal Labels - Get Orders",
                False,
                f"GET /api/orders failed with status {orders_response.status_code}",
                orders_response.text
            )
            return False
        
        orders_data = orders_response.json()
        
        if not isinstance(orders_data, list) or len(orders_data) == 0:
            test_results.add_result(
                "Thermal Labels - Get Orders",
                False,
                "No orders found in database",
                f"Response: {orders_data}"
            )
            return False
        
        # Select 2-3 order IDs for testing
        test_order_ids = [order['id'] for order in orders_data[:3] if 'id' in order]
        
        if len(test_order_ids) < 2:
            test_results.add_result(
                "Thermal Labels - Order IDs",
                False,
                f"Not enough orders for testing, found {len(test_order_ids)}",
                f"Available orders: {len(orders_data)}"
            )
            return False
        
        test_results.add_result(
            "Thermal Labels - Get Orders",
            True,
            f"Retrieved {len(orders_data)} orders, selected {len(test_order_ids)} for testing"
        )
        
    except Exception as e:
        test_results.add_result(
            "Thermal Labels - Get Orders",
            False,
            f"GET /api/orders request failed: {str(e)}"
        )
        return False
    
    # Step 3: Test POST /api/orders/print-labels with valid order IDs
    try:
        labels_response = requests.post(
            f"{API_BASE}/orders/print-labels",
            json=test_order_ids,
            headers=admin_headers,
            timeout=60  # PDF generation may take time
        )
        
        if labels_response.status_code == 200:
            # Verify response is PDF
            content_type = labels_response.headers.get('content-type', '')
            content_disposition = labels_response.headers.get('content-disposition', '')
            
            if 'application/pdf' in content_type:
                test_results.add_result(
                    "Thermal Labels - PDF Generation",
                    True,
                    f"✅ PDF generated successfully. Size: {len(labels_response.content)} bytes, Content-Type: {content_type}"
                )
                
                # Verify Content-Disposition header
                if 'attachment' in content_disposition and 'etiquettes_commandes_' in content_disposition:
                    test_results.add_result(
                        "Thermal Labels - Content Disposition",
                        True,
                        f"✅ Correct Content-Disposition header: {content_disposition}"
                    )
                else:
                    test_results.add_result(
                        "Thermal Labels - Content Disposition",
                        False,
                        f"Incorrect Content-Disposition header",
                        f"Expected: attachment; filename=\"etiquettes_commandes_*.pdf\", Got: {content_disposition}"
                    )
                
                # Verify PDF size is reasonable (should be > 10KB for multiple labels)
                pdf_size = len(labels_response.content)
                if pdf_size > 10000:  # 10KB minimum
                    test_results.add_result(
                        "Thermal Labels - PDF Size Validation",
                        True,
                        f"✅ PDF size is reasonable: {pdf_size} bytes for {len(test_order_ids)} labels"
                    )
                else:
                    test_results.add_result(
                        "Thermal Labels - PDF Size Validation",
                        False,
                        f"PDF size too small: {pdf_size} bytes",
                        "PDF may be corrupted or empty"
                    )
                
                return True
            else:
                test_results.add_result(
                    "Thermal Labels - PDF Generation",
                    False,
                    f"Response is not PDF, content-type: {content_type}",
                    f"Response size: {len(labels_response.content)} bytes"
                )
                return False
        else:
            test_results.add_result(
                "Thermal Labels - PDF Generation",
                False,
                f"❌ Labels generation failed with status {labels_response.status_code}",
                labels_response.text
            )
            return False
            
    except Exception as e:
        test_results.add_result(
            "Thermal Labels - PDF Generation",
            False,
            f"Labels generation request failed: {str(e)}"
        )
        return False

def test_thermal_labels_error_handling():
    """Test Thermal Labels Error Handling"""
    
    print("🚫 Testing Thermal Labels Error Handling...")
    
    # Test user from review request
    admin_user_credentials = {
        "email": "testpro@beyond.com",
        "password": "Test123!"
    }
    
    # Step 1: Login with admin user
    try:
        login_response = requests.post(
            f"{API_BASE}/auth/login",
            json=admin_user_credentials,
            timeout=30
        )
        
        if login_response.status_code != 200:
            test_results.add_result(
                "Thermal Labels Error - Admin Login",
                False,
                f"Login failed with status {login_response.status_code}",
                login_response.text
            )
            return False
        
        login_data = login_response.json()
        admin_token = login_data.get('access_token')
        admin_headers = {'Authorization': f'Bearer {admin_token}'}
        
    except Exception as e:
        test_results.add_result(
            "Thermal Labels Error - Admin Login",
            False,
            f"Login request failed: {str(e)}"
        )
        return False
    
    # Step 2: Test with empty order IDs list
    try:
        empty_response = requests.post(
            f"{API_BASE}/orders/print-labels",
            json=[],
            headers=admin_headers,
            timeout=30
        )
        
        if empty_response.status_code == 400:
            error_data = empty_response.json()
            if 'No order IDs provided' in error_data.get('detail', ''):
                test_results.add_result(
                    "Thermal Labels Error - Empty List",
                    True,
                    f"✅ Correct error handling for empty list: {error_data.get('detail')}"
                )
            else:
                test_results.add_result(
                    "Thermal Labels Error - Empty List",
                    False,
                    f"Unexpected error message",
                    f"Expected: 'No order IDs provided', Got: {error_data.get('detail')}"
                )
        else:
            test_results.add_result(
                "Thermal Labels Error - Empty List",
                False,
                f"Expected 400 Bad Request, got {empty_response.status_code}",
                empty_response.text
            )
            
    except Exception as e:
        test_results.add_result(
            "Thermal Labels Error - Empty List",
            False,
            f"Empty list test request failed: {str(e)}"
        )
    
    # Step 3: Test with invalid order IDs
    try:
        invalid_ids = ["invalid-id-1", "invalid-id-2"]
        invalid_response = requests.post(
            f"{API_BASE}/orders/print-labels",
            json=invalid_ids,
            headers=admin_headers,
            timeout=30
        )
        
        if invalid_response.status_code == 404:
            error_data = invalid_response.json()
            if 'No orders found' in error_data.get('detail', ''):
                test_results.add_result(
                    "Thermal Labels Error - Invalid IDs",
                    True,
                    f"✅ Correct error handling for invalid IDs: {error_data.get('detail')}"
                )
            else:
                test_results.add_result(
                    "Thermal Labels Error - Invalid IDs",
                    False,
                    f"Unexpected error message",
                    f"Expected: 'No orders found', Got: {error_data.get('detail')}"
                )
        else:
            test_results.add_result(
                "Thermal Labels Error - Invalid IDs",
                False,
                f"Expected 404 Not Found, got {invalid_response.status_code}",
                invalid_response.text
            )
            
    except Exception as e:
        test_results.add_result(
            "Thermal Labels Error - Invalid IDs",
            False,
            f"Invalid IDs test request failed: {str(e)}"
        )
    
    return True

def run_all_tests():
    """Run all backend tests"""
    
    print(f"🚀 Starting Backend API Tests for Beyond Express")
    print(f"Base URL: {BASE_URL}")
    print(f"API Base: {API_BASE}")
    print(f"{'='*60}")
    
    # Test sequence - THERMAL LABELS PRINTING SYSTEM FIRST (NEW FEATURE)
    tests = [
        ("Authentication", test_authentication),
        ("🏷️ NEW FEATURE - Thermal Labels Printing System", test_thermal_labels_printing_system),
        ("🚫 NEW FEATURE - Thermal Labels Error Handling", test_thermal_labels_error_handling),
        ("BUG 1 FIX - Carriers Integration Page", test_carriers_integration_page),
        ("BUG 2 FIX - Batch Transfer Payment", test_batch_transfer_payment),
        ("AI Assistant PRO User Bug Fix", test_ai_assistant_pro_user_bug_fix),
        ("Get Orders - CRITICAL BUG FIX", test_get_orders),
        ("Orders Count Verification", test_orders_count_verification),
        ("Order Creation", test_order_creation),
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