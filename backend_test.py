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
BASE_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://logistics-os.preview.emergentagent.com')
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

def test_yalidine_carrier_status_api():
    """Test Yalidine Carrier Status API - Should return not configured"""
    
    print("🚚 Testing Yalidine Carrier Status API...")
    
    # Test user from review request
    admin_user_credentials = {
        "email": "cherier.sam@beyondexpress-batna.com",
        "password": "admin123456"
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
                "Yalidine Carrier Status - Admin Login",
                False,
                f"Login failed with status {login_response.status_code}",
                login_response.text
            )
            return False
        
        login_data = login_response.json()
        admin_token = login_data.get('access_token')
        admin_headers = {'Authorization': f'Bearer {admin_token}'}
        
        test_results.add_result(
            "Yalidine Carrier Status - Admin Login",
            True,
            f"Successfully logged in as {login_data.get('user', {}).get('name', 'Admin User')}"
        )
        
    except Exception as e:
        test_results.add_result(
            "Yalidine Carrier Status - Admin Login",
            False,
            f"Login request failed: {str(e)}"
        )
        return False
    
    # Step 2: Test GET /api/shipping/carrier-status/yalidine
    try:
        carrier_status_response = requests.get(
            f"{API_BASE}/shipping/carrier-status/yalidine",
            headers=admin_headers,
            timeout=30
        )
        
        if carrier_status_response.status_code == 200:
            status_data = carrier_status_response.json()
            
            # Verify response structure
            expected_fields = ['carrier_type', 'is_configured', 'is_active', 'can_ship', 'message']
            has_all_fields = all(field in status_data for field in expected_fields)
            
            if has_all_fields:
                carrier_type = status_data.get('carrier_type')
                is_configured = status_data.get('is_configured')
                is_active = status_data.get('is_active')
                can_ship = status_data.get('can_ship')
                message = status_data.get('message', '')
                
                # Should return not configured as per review request
                if carrier_type == 'yalidine' and not is_configured:
                    test_results.add_result(
                        "Yalidine Carrier Status - Not Configured",
                        True,
                        f"✅ Yalidine correctly returns not configured: is_configured={is_configured}, can_ship={can_ship}, message='{message}'"
                    )
                    return True
                else:
                    test_results.add_result(
                        "Yalidine Carrier Status - Not Configured",
                        False,
                        f"Expected not configured, got is_configured={is_configured}",
                        f"Full response: {status_data}"
                    )
                    return False
            else:
                test_results.add_result(
                    "Yalidine Carrier Status - Response Structure",
                    False,
                    f"Response missing required fields: {expected_fields}",
                    str(status_data)
                )
                return False
        else:
            test_results.add_result(
                "Yalidine Carrier Status - API Response",
                False,
                f"GET /api/shipping/carrier-status/yalidine failed with status {carrier_status_response.status_code}",
                carrier_status_response.text
            )
            return False
            
    except Exception as e:
        test_results.add_result(
            "Yalidine Carrier Status - API Request",
            False,
            f"GET /api/shipping/carrier-status/yalidine request failed: {str(e)}"
        )
        return False


def test_algeria_wilayas_module():
    """Test Algeria Wilayas Module Functions"""
    
    print("🗺️ Testing Algeria Wilayas Module...")
    
    # Test data from review request
    test_cases = [
        ("Alger", 16),
        ("Batna", 5),
        ("Tizi Ouzou", 15),
        ("Oran", 31),
        ("Constantine", 25)
    ]
    
    try:
        # Import and test the module functions directly
        import sys
        sys.path.append('/app/backend')
        
        from services.carriers.algeria_wilayas import get_wilaya_id, get_wilaya_name, is_valid_wilaya
        
        # Test get_wilaya_id function
        all_passed = True
        for wilaya_name, expected_id in test_cases:
            actual_id = get_wilaya_id(wilaya_name)
            
            if actual_id == expected_id:
                test_results.add_result(
                    f"Algeria Wilayas - get_wilaya_id({wilaya_name})",
                    True,
                    f"✅ {wilaya_name} correctly mapped to ID {actual_id}"
                )
            else:
                test_results.add_result(
                    f"Algeria Wilayas - get_wilaya_id({wilaya_name})",
                    False,
                    f"Expected ID {expected_id}, got {actual_id}",
                    f"Wilaya: {wilaya_name}"
                )
                all_passed = False
        
        # Test is_valid_wilaya function
        for wilaya_name, _ in test_cases:
            is_valid = is_valid_wilaya(wilaya_name)
            
            if is_valid:
                test_results.add_result(
                    f"Algeria Wilayas - is_valid_wilaya({wilaya_name})",
                    True,
                    f"✅ {wilaya_name} correctly validated as valid"
                )
            else:
                test_results.add_result(
                    f"Algeria Wilayas - is_valid_wilaya({wilaya_name})",
                    False,
                    f"{wilaya_name} should be valid but returned False"
                )
                all_passed = False
        
        # Test get_wilaya_name function (reverse lookup)
        test_id = 16  # Alger
        wilaya_name = get_wilaya_name(test_id)
        
        if wilaya_name == "Alger":
            test_results.add_result(
                f"Algeria Wilayas - get_wilaya_name({test_id})",
                True,
                f"✅ ID {test_id} correctly mapped to name '{wilaya_name}'"
            )
        else:
            test_results.add_result(
                f"Algeria Wilayas - get_wilaya_name({test_id})",
                False,
                f"Expected 'Alger', got '{wilaya_name}'",
                f"ID: {test_id}"
            )
            all_passed = False
        
        return all_passed
        
    except ImportError as e:
        test_results.add_result(
            "Algeria Wilayas - Module Import",
            False,
            f"Failed to import algeria_wilayas module: {str(e)}"
        )
        return False
    except Exception as e:
        test_results.add_result(
            "Algeria Wilayas - Module Test",
            False,
            f"Error testing algeria_wilayas module: {str(e)}"
        )
        return False


def test_yalidine_adapter_data_mapping():
    """Test YalidineAdapter Data Mapping Functions"""
    
    print("📱 Testing YalidineAdapter Data Mapping...")
    
    try:
        # Import YalidineAdapter
        import sys
        sys.path.append('/app/backend')
        
        from services.carriers.yalidine import YalidineCarrier
        
        # Create YalidineAdapter instance in test mode
        carrier = YalidineCarrier({'api_key': 'test', 'api_token': 'test'}, test_mode=True)
        
        # Test phone formatting
        phone_test_cases = [
            ("+213555123456", "0555123456"),
            ("0555123456", "0555123456"),
            ("555123456", "0555123456")
        ]
        
        all_passed = True
        for input_phone, expected_output in phone_test_cases:
            formatted_phone = carrier._format_phone(input_phone)
            
            if formatted_phone == expected_output:
                test_results.add_result(
                    f"YalidineAdapter - Phone Format ({input_phone})",
                    True,
                    f"✅ Phone {input_phone} correctly formatted to {formatted_phone}"
                )
            else:
                test_results.add_result(
                    f"YalidineAdapter - Phone Format ({input_phone})",
                    False,
                    f"Expected {expected_output}, got {formatted_phone}",
                    f"Input: {input_phone}"
                )
                all_passed = False
        
        # Test name parsing
        name_test_cases = [
            ("Ahmed Benali", ("Ahmed", "Benali")),
            ("Mohammed", ("Mohammed", "")),
            ("Ali Ben Ahmed Mansour", ("Ali", "Ben Ahmed Mansour"))
        ]
        
        for input_name, expected_output in name_test_cases:
            firstname, lastname = carrier._parse_customer_name(input_name)
            
            if (firstname, lastname) == expected_output:
                test_results.add_result(
                    f"YalidineAdapter - Name Parse ({input_name})",
                    True,
                    f"✅ Name '{input_name}' correctly parsed to firstname='{firstname}', lastname='{lastname}'"
                )
            else:
                test_results.add_result(
                    f"YalidineAdapter - Name Parse ({input_name})",
                    False,
                    f"Expected {expected_output}, got ({firstname}, {lastname})",
                    f"Input: {input_name}"
                )
                all_passed = False
        
        return all_passed
        
    except ImportError as e:
        test_results.add_result(
            "YalidineAdapter - Module Import",
            False,
            f"Failed to import YalidineCarrier: {str(e)}"
        )
        return False
    except Exception as e:
        test_results.add_result(
            "YalidineAdapter - Data Mapping Test",
            False,
            f"Error testing YalidineAdapter data mapping: {str(e)}"
        )
        return False


def test_smart_routing_engine_shipping_api():
    """Test Smart Routing Engine - Shipping API Endpoints"""
    
    print("🚀 Testing Smart Routing Engine - Shipping API...")
    
    # Test user credentials from review request
    admin_user_credentials = {
        "email": "cherier.sam@beyondexpress-batna.com",
        "password": "admin123456"
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
                "Smart Routing - Admin Login",
                False,
                f"Login failed with status {login_response.status_code}",
                login_response.text
            )
            return False
        
        login_data = login_response.json()
        admin_token = login_data.get('access_token')
        admin_headers = {'Authorization': f'Bearer {admin_token}'}
        
        test_results.add_result(
            "Smart Routing - Admin Login",
            True,
            f"Successfully logged in as {login_data.get('user', {}).get('name', 'Admin User')}"
        )
        
    except Exception as e:
        test_results.add_result(
            "Smart Routing - Admin Login",
            False,
            f"Login request failed: {str(e)}"
        )
        return False
    
    # Step 2: Test GET /api/shipping/active-carriers (should be empty initially)
    try:
        carriers_response = requests.get(
            f"{API_BASE}/shipping/active-carriers",
            headers=admin_headers,
            timeout=30
        )
        
        if carriers_response.status_code == 200:
            carriers_data = carriers_response.json()
            
            if isinstance(carriers_data, dict) and 'carriers' in carriers_data:
                carriers_list = carriers_data['carriers']
                
                if isinstance(carriers_list, list) and len(carriers_list) == 0:
                    test_results.add_result(
                        "Smart Routing - Active Carriers (Empty)",
                        True,
                        f"✅ GET /api/shipping/active-carriers returns empty list as expected: {carriers_data}"
                    )
                else:
                    test_results.add_result(
                        "Smart Routing - Active Carriers (Empty)",
                        True,
                        f"✅ GET /api/shipping/active-carriers returns carriers list: {len(carriers_list)} carriers found"
                    )
            else:
                test_results.add_result(
                    "Smart Routing - Active Carriers (Empty)",
                    False,
                    "Response structure invalid - missing 'carriers' field",
                    str(carriers_data)
                )
                return False
        else:
            test_results.add_result(
                "Smart Routing - Active Carriers (Empty)",
                False,
                f"GET /api/shipping/active-carriers failed with status {carriers_response.status_code}",
                carriers_response.text
            )
            return False
            
    except Exception as e:
        test_results.add_result(
            "Smart Routing - Active Carriers (Empty)",
            False,
            f"Active carriers request failed: {str(e)}"
        )
        return False
    
    # Step 3: Test GET /api/shipping/tracking/{order_id} with a real order
    try:
        # First get orders to find a real order ID
        orders_response = requests.get(
            f"{API_BASE}/orders",
            headers=admin_headers,
            timeout=30
        )
        
        if orders_response.status_code == 200:
            orders_data = orders_response.json()
            
            if isinstance(orders_data, list) and len(orders_data) > 0:
                test_order_id = orders_data[0].get('id')
                
                if test_order_id:
                    tracking_response = requests.get(
                        f"{API_BASE}/shipping/tracking/{test_order_id}",
                        headers=admin_headers,
                        timeout=30
                    )
                    
                    if tracking_response.status_code == 200:
                        tracking_data = tracking_response.json()
                        
                        # Check response structure
                        expected_fields = ['order_id', 'carrier_synced']
                        has_required_fields = all(field in tracking_data for field in expected_fields)
                        
                        if has_required_fields:
                            test_results.add_result(
                                "Smart Routing - Tracking API",
                                True,
                                f"✅ GET /api/shipping/tracking/{test_order_id} returns valid response: carrier_synced={tracking_data.get('carrier_synced')}"
                            )
                        else:
                            test_results.add_result(
                                "Smart Routing - Tracking API",
                                False,
                                f"Response missing required fields: {expected_fields}",
                                str(tracking_data)
                            )
                    else:
                        test_results.add_result(
                            "Smart Routing - Tracking API",
                            False,
                            f"GET /api/shipping/tracking/{test_order_id} failed with status {tracking_response.status_code}",
                            tracking_response.text
                        )
                else:
                    test_results.add_result(
                        "Smart Routing - Tracking API",
                        False,
                        "No valid order ID found for tracking test",
                        "Cannot test tracking without order ID"
                    )
            else:
                test_results.add_result(
                    "Smart Routing - Tracking API",
                    False,
                    "No orders found for tracking test",
                    f"Orders response: {orders_data}"
                )
        else:
            test_results.add_result(
                "Smart Routing - Tracking API",
                False,
                f"Failed to get orders for tracking test: {orders_response.status_code}",
                orders_response.text
            )
            
    except Exception as e:
        test_results.add_result(
            "Smart Routing - Tracking API",
            False,
            f"Tracking API test failed: {str(e)}"
        )
    
    return True

def test_webhooks_endpoints():
    """Test Webhooks Endpoints"""
    
    print("🔗 Testing Webhooks Endpoints...")
    
    # Step 1: Test GET /api/webhooks/test (should return status "ok")
    try:
        test_response = requests.get(
            f"{API_BASE}/webhooks/test",
            timeout=30
        )
        
        if test_response.status_code == 200:
            test_data = test_response.json()
            
            if isinstance(test_data, dict) and test_data.get('status') == 'ok':
                test_results.add_result(
                    "Webhooks - Test Endpoint",
                    True,
                    f"✅ GET /api/webhooks/test returns status 'ok': {test_data}"
                )
            else:
                test_results.add_result(
                    "Webhooks - Test Endpoint",
                    False,
                    f"Expected status 'ok', got: {test_data.get('status')}",
                    str(test_data)
                )
                return False
        else:
            test_results.add_result(
                "Webhooks - Test Endpoint",
                False,
                f"GET /api/webhooks/test failed with status {test_response.status_code}",
                test_response.text
            )
            return False
            
    except Exception as e:
        test_results.add_result(
            "Webhooks - Test Endpoint",
            False,
            f"Webhooks test request failed: {str(e)}"
        )
        return False
    
    # Step 2: Test POST /api/webhooks/yalidine (simulated webhook)
    try:
        yalidine_webhook_payload = {
            "tracking": "YAL-TEST123",
            "order_id": "BEX-TEST",
            "status": "Livré",
            "center": "Alger"
        }
        
        yalidine_response = requests.post(
            f"{API_BASE}/webhooks/yalidine",
            json=yalidine_webhook_payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if yalidine_response.status_code == 200:
            yalidine_data = yalidine_response.json()
            
            if isinstance(yalidine_data, dict) and yalidine_data.get('status') == 'received':
                test_results.add_result(
                    "Webhooks - Yalidine Webhook",
                    True,
                    f"✅ POST /api/webhooks/yalidine accepts payload and returns 'received': {yalidine_data}"
                )
            else:
                test_results.add_result(
                    "Webhooks - Yalidine Webhook",
                    False,
                    f"Expected status 'received', got: {yalidine_data.get('status')}",
                    str(yalidine_data)
                )
                return False
        else:
            test_results.add_result(
                "Webhooks - Yalidine Webhook",
                False,
                f"POST /api/webhooks/yalidine failed with status {yalidine_response.status_code}",
                yalidine_response.text
            )
            return False
            
    except Exception as e:
        test_results.add_result(
            "Webhooks - Yalidine Webhook",
            False,
            f"Yalidine webhook request failed: {str(e)}"
        )
        return False
    
    return True

def test_carriers_configuration():
    """Test Carrier Configuration API"""
    
    print("🚚 Testing Carrier Configuration API...")
    
    # Test user credentials from review request
    admin_user_credentials = {
        "email": "cherier.sam@beyondexpress-batna.com",
        "password": "admin123456"
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
                "Carriers Config - Admin Login",
                False,
                f"Login failed with status {login_response.status_code}",
                login_response.text
            )
            return False
        
        login_data = login_response.json()
        admin_token = login_data.get('access_token')
        admin_headers = {'Authorization': f'Bearer {admin_token}'}
        
        test_results.add_result(
            "Carriers Config - Admin Login",
            True,
            f"Successfully logged in as {login_data.get('user', {}).get('name', 'Admin User')}"
        )
        
    except Exception as e:
        test_results.add_result(
            "Carriers Config - Admin Login",
            False,
            f"Login request failed: {str(e)}"
        )
        return False
    
    # Step 2: Test GET /api/carriers (get carriers list)
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
                expected_carriers = ['Yalidine', 'DHD Express', 'ZR Express', 'Maystro', 'Guepex', 'Nord et Ouest', 'Pajo']
                
                # Check if we have the expected carriers
                found_carrier_names = [carrier.get('name', 'Unknown') for carrier in carriers_data if isinstance(carrier, dict)]
                
                if carrier_count >= 5:  # At least 5 carriers expected
                    test_results.add_result(
                        "Carriers Config - List Carriers",
                        True,
                        f"✅ GET /api/carriers returns {carrier_count} carriers: {found_carrier_names}"
                    )
                    
                    # Verify carrier structure
                    required_fields = ['name', 'carrier_type']
                    valid_carriers = 0
                    
                    for carrier in carriers_data:
                        if isinstance(carrier, dict):
                            has_required_fields = all(field in carrier for field in required_fields)
                            if has_required_fields:
                                valid_carriers += 1
                    
                    if valid_carriers == carrier_count:
                        test_results.add_result(
                            "Carriers Config - Carrier Structure",
                            True,
                            f"✅ All {valid_carriers} carriers have required fields: {required_fields}"
                        )
                    else:
                        test_results.add_result(
                            "Carriers Config - Carrier Structure",
                            False,
                            f"Only {valid_carriers}/{carrier_count} carriers have required fields",
                            f"Required: {required_fields}"
                        )
                    
                    return True
                else:
                    test_results.add_result(
                        "Carriers Config - List Carriers",
                        False,
                        f"Expected at least 5 carriers, got {carrier_count}",
                        f"Found carriers: {found_carrier_names}"
                    )
                    return False
            else:
                test_results.add_result(
                    "Carriers Config - List Carriers",
                    False,
                    "Response is not a list",
                    str(carriers_data)
                )
                return False
        else:
            test_results.add_result(
                "Carriers Config - List Carriers",
                False,
                f"GET /api/carriers failed with status {carriers_response.status_code}",
                carriers_response.text
            )
            return False
            
    except Exception as e:
        test_results.add_result(
            "Carriers Config - List Carriers",
            False,
            f"Carriers list request failed: {str(e)}"
        )
        return False

def test_admin_dashboard_critical():
    """Test Dashboard Admin (P0 - CRITIQUE) - Critical fix verification"""
    
    print("🔥 Testing Admin Dashboard Critical Fix...")
    
    # Admin user from review request
    admin_credentials = {
        "email": "cherier.sam@beyondexpress-batna.com",
        "password": "admin123456"
    }
    
    # Step 1: Login with admin user
    try:
        login_response = requests.post(
            f"{API_BASE}/auth/login",
            json=admin_credentials,
            timeout=30
        )
        
        if login_response.status_code == 200:
            login_data = login_response.json()
            admin_token = login_data.get('access_token')
            admin_headers = {'Authorization': f'Bearer {admin_token}'}
            
            test_results.add_result(
                "Admin Dashboard - Critical Login",
                True,
                f"✅ CRITICAL: Admin login successful with {admin_credentials['email']}"
            )
            
            # Step 2: Test dashboard endpoints to verify no white screen
            dashboard_endpoints = [
                "/dashboard/stats",
                "/dashboard/orders-by-status", 
                "/dashboard/revenue-evolution",
                "/dashboard/top-wilayas"
            ]
            
            dashboard_success = 0
            for endpoint in dashboard_endpoints:
                try:
                    dash_response = requests.get(
                        f"{API_BASE}{endpoint}",
                        headers=admin_headers,
                        timeout=30
                    )
                    
                    if dash_response.status_code == 200:
                        dashboard_success += 1
                    else:
                        print(f"⚠️ Dashboard endpoint {endpoint} failed: {dash_response.status_code}")
                        
                except Exception as e:
                    print(f"⚠️ Dashboard endpoint {endpoint} error: {str(e)}")
            
            if dashboard_success == len(dashboard_endpoints):
                test_results.add_result(
                    "Admin Dashboard - No White Screen",
                    True,
                    f"✅ CRITICAL: All {dashboard_success} dashboard endpoints working - no white screen crash"
                )
            else:
                test_results.add_result(
                    "Admin Dashboard - No White Screen", 
                    False,
                    f"❌ CRITICAL: Only {dashboard_success}/{len(dashboard_endpoints)} dashboard endpoints working",
                    "Dashboard may still have white screen issues"
                )
            
            return True
            
        else:
            test_results.add_result(
                "Admin Dashboard - Critical Login",
                False,
                f"❌ CRITICAL: Admin login failed with status {login_response.status_code}",
                f"Credentials: {admin_credentials['email']} / {admin_credentials['password']}"
            )
            return False
            
    except Exception as e:
        test_results.add_result(
            "Admin Dashboard - Critical Login",
            False,
            f"❌ CRITICAL: Admin login request failed: {str(e)}"
        )
        return False

def test_driver_pwa_critical():
    """Test Driver PWA (P1) - Driver login and tasks verification"""
    
    print("🚛 Testing Driver PWA Critical...")
    
    # Driver user from review request
    driver_credentials = {
        "email": "driver@beyond.com", 
        "password": "driver123"
    }
    
    # Step 1: Login with driver user
    try:
        login_response = requests.post(
            f"{API_BASE}/auth/login",
            json=driver_credentials,
            timeout=30
        )
        
        if login_response.status_code == 200:
            login_data = login_response.json()
            driver_token = login_data.get('access_token')
            driver_headers = {'Authorization': f'Bearer {driver_token}'}
            user_role = login_data.get('user', {}).get('role', 'unknown')
            
            test_results.add_result(
                "Driver PWA - Login",
                True,
                f"✅ Driver login successful with {driver_credentials['email']}, role: {user_role}"
            )
            
            # Step 2: Test GET /api/driver/tasks
            try:
                tasks_response = requests.get(
                    f"{API_BASE}/driver/tasks",
                    headers=driver_headers,
                    timeout=30
                )
                
                if tasks_response.status_code == 200:
                    tasks_data = tasks_response.json()
                    
                    # Verify response structure
                    if isinstance(tasks_data, dict) and 'tasks' in tasks_data:
                        tasks_list = tasks_data.get('tasks', [])
                        task_count = tasks_data.get('count', 0)
                        
                        test_results.add_result(
                            "Driver PWA - Tasks Structure",
                            True,
                            f"✅ /driver/tasks returns proper structure: {task_count} tasks found"
                        )
                        
                        # Verify task structure if tasks exist
                        if len(tasks_list) > 0:
                            first_task = tasks_list[0]
                            required_fields = ['order_id', 'tracking_id', 'status', 'client_name', 'client_phone', 'address', 'wilaya', 'commune', 'cod_amount']
                            
                            missing_fields = [field for field in required_fields if field not in first_task]
                            
                            if not missing_fields:
                                test_results.add_result(
                                    "Driver PWA - Task Data Structure",
                                    True,
                                    f"✅ Task structure complete: client={first_task.get('client_name')}, tracking={first_task.get('tracking_id')}, COD={first_task.get('cod_amount')} DA"
                                )
                            else:
                                test_results.add_result(
                                    "Driver PWA - Task Data Structure",
                                    False,
                                    f"Task missing required fields: {missing_fields}",
                                    f"Available fields: {list(first_task.keys())}"
                                )
                        else:
                            test_results.add_result(
                                "Driver PWA - Task Data Structure",
                                True,
                                "✅ No tasks assigned to driver (empty list is valid)"
                            )
                        
                        return True
                    else:
                        test_results.add_result(
                            "Driver PWA - Tasks Structure",
                            False,
                            "Response missing 'tasks' field or not a dict",
                            str(tasks_data)
                        )
                        return False
                else:
                    test_results.add_result(
                        "Driver PWA - Tasks API",
                        False,
                        f"❌ GET /api/driver/tasks failed with status {tasks_response.status_code}",
                        tasks_response.text
                    )
                    return False
                    
            except Exception as e:
                test_results.add_result(
                    "Driver PWA - Tasks API",
                    False,
                    f"GET /api/driver/tasks request failed: {str(e)}"
                )
                return False
            
        else:
            test_results.add_result(
                "Driver PWA - Login",
                False,
                f"❌ Driver login failed with status {login_response.status_code}",
                f"Credentials: {driver_credentials['email']} / {driver_credentials['password']}"
            )
            return False
            
    except Exception as e:
        test_results.add_result(
            "Driver PWA - Login",
            False,
            f"Driver login request failed: {str(e)}"
        )
        return False

def test_driver_api_curl_simulation():
    """Test API Driver with curl simulation - As specified in review request"""
    
    print("🔧 Testing Driver API with curl simulation...")
    
    # Step 1: Login driver and get token (simulating curl command)
    driver_credentials = {
        "email": "driver@beyond.com",
        "password": "driver123"
    }
    
    try:
        # Simulate: curl -s -X POST "$API_URL/api/auth/login" -H "Content-Type: application/json" -d '{"email":"driver@beyond.com","password":"driver123"}'
        login_response = requests.post(
            f"{API_BASE}/auth/login",
            json=driver_credentials,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if login_response.status_code == 200:
            login_data = login_response.json()
            driver_token = login_data.get('access_token')
            
            if driver_token:
                test_results.add_result(
                    "Driver API Curl - Token Extraction",
                    True,
                    f"✅ Token extracted successfully: {driver_token[:20]}..."
                )
                
                # Step 2: Test GET /api/driver/tasks with token (simulating curl command)
                try:
                    # Simulate: curl -s "$API_URL/api/driver/tasks" -H "Authorization: Bearer $TOKEN"
                    tasks_response = requests.get(
                        f"{API_BASE}/driver/tasks",
                        headers={"Authorization": f"Bearer {driver_token}"},
                        timeout=30
                    )
                    
                    if tasks_response.status_code == 200:
                        tasks_data = tasks_response.json()
                        
                        # Verify the 3 test orders are visible as mentioned in review request
                        if isinstance(tasks_data, dict) and 'tasks' in tasks_data:
                            task_count = tasks_data.get('count', 0)
                            tasks_list = tasks_data.get('tasks', [])
                            
                            test_results.add_result(
                                "Driver API Curl - Tasks Response",
                                True,
                                f"✅ curl simulation successful: GET /api/driver/tasks returned {task_count} tasks"
                            )
                            
                            # Check if we have the expected test orders
                            if task_count >= 3:
                                test_results.add_result(
                                    "Driver API Curl - Test Orders Visible",
                                    True,
                                    f"✅ Expected test orders visible: {task_count} tasks found (≥3 expected)"
                                )
                            else:
                                test_results.add_result(
                                    "Driver API Curl - Test Orders Visible",
                                    False,
                                    f"Expected at least 3 test orders, found {task_count}",
                                    "Review request mentions '3 ordres test' should be visible"
                                )
                            
                            return True
                        else:
                            test_results.add_result(
                                "Driver API Curl - Tasks Response",
                                False,
                                "Response structure invalid",
                                str(tasks_data)
                            )
                            return False
                    else:
                        test_results.add_result(
                            "Driver API Curl - Tasks Response",
                            False,
                            f"❌ curl simulation failed: GET /api/driver/tasks returned {tasks_response.status_code}",
                            tasks_response.text
                        )
                        return False
                        
                except Exception as e:
                    test_results.add_result(
                        "Driver API Curl - Tasks Response",
                        False,
                        f"curl tasks request failed: {str(e)}"
                    )
                    return False
            else:
                test_results.add_result(
                    "Driver API Curl - Token Extraction",
                    False,
                    "No access_token in login response",
                    str(login_data)
                )
                return False
        else:
            test_results.add_result(
                "Driver API Curl - Login",
                False,
                f"❌ curl login simulation failed with status {login_response.status_code}",
                login_response.text
            )
            return False
            
    except Exception as e:
        test_results.add_result(
            "Driver API Curl - Login",
            False,
            f"curl login simulation request failed: {str(e)}"
        )
        return False

def test_driver_authentication():
    """Test driver authentication with driver@beyond.com"""
    global driver_headers
    
    print("🚗 Testing Driver Authentication...")
    
    driver_credentials = {
        "email": "driver@beyond.com",
        "password": "Driver123!"
    }
    
    try:
        # Test login with driver credentials
        response = requests.post(
            f"{API_BASE}/auth/login",
            json=driver_credentials,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            driver_token = data.get('access_token')
            driver_headers = {'Authorization': f'Bearer {driver_token}'}
            
            # Verify user role is delivery
            user_data = data.get('user', {})
            user_role = user_data.get('role', '')
            
            if user_role == 'delivery':
                test_results.add_result(
                    "Driver Authentication - Login",
                    True,
                    f"Successfully logged in as driver: {user_data.get('name', 'Driver User')}"
                )
                return True
            else:
                test_results.add_result(
                    "Driver Authentication - Login",
                    False,
                    f"User role is '{user_role}', expected 'delivery'",
                    f"User data: {user_data}"
                )
                return False
        else:
            test_results.add_result(
                "Driver Authentication - Login",
                False,
                f"Driver login failed with status {response.status_code}",
                response.text
            )
            return False
            
    except Exception as e:
        test_results.add_result(
            "Driver Authentication - Login",
            False,
            f"Driver login request failed: {str(e)}"
        )
        return False

def test_driver_authorization():
    """Test that non-driver users cannot access driver endpoints"""
    
    print("🔒 Testing Driver Authorization...")
    
    # Test with admin user (should be denied)
    try:
        response = requests.get(
            f"{API_BASE}/driver/tasks",
            headers=headers,  # Admin headers
            timeout=30
        )
        
        if response.status_code == 403:
            error_data = response.json()
            if "Access denied. Drivers only." in error_data.get('detail', ''):
                test_results.add_result(
                    "Driver Authorization - Non-Driver Access",
                    True,
                    f"✅ Correctly denied access to non-driver user: {error_data.get('detail')}"
                )
                return True
            else:
                test_results.add_result(
                    "Driver Authorization - Non-Driver Access",
                    False,
                    f"Unexpected error message",
                    f"Expected: 'Access denied. Drivers only.', Got: {error_data.get('detail')}"
                )
                return False
        else:
            test_results.add_result(
                "Driver Authorization - Non-Driver Access",
                False,
                f"Expected 403 Forbidden, got {response.status_code}",
                response.text
            )
            return False
            
    except Exception as e:
        test_results.add_result(
            "Driver Authorization - Non-Driver Access",
            False,
            f"Authorization test request failed: {str(e)}"
        )
        return False

def test_driver_tasks():
    """Test GET /api/driver/tasks endpoint"""
    
    print("📋 Testing Driver Tasks Endpoint...")
    
    try:
        response = requests.get(
            f"{API_BASE}/driver/tasks",
            headers=driver_headers,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            
            # Verify response structure
            required_fields = ['tasks', 'count', 'driver_id', 'driver_name']
            has_all_fields = all(field in data for field in required_fields)
            
            if has_all_fields:
                tasks = data.get('tasks', [])
                task_count = data.get('count', 0)
                
                test_results.add_result(
                    "Driver Tasks - Response Structure",
                    True,
                    f"✅ Retrieved {task_count} tasks for driver {data.get('driver_name')}"
                )
                
                # Verify task structure if tasks exist
                if tasks and len(tasks) > 0:
                    first_task = tasks[0]
                    task_required_fields = ['order_id', 'tracking_id', 'status', 'client', 'cod_amount', 'shipping_cost']
                    
                    task_valid = all(field in first_task for field in task_required_fields)
                    
                    if task_valid:
                        client = first_task.get('client', {})
                        client_fields = ['name', 'phone', 'address', 'wilaya', 'commune']
                        client_valid = all(field in client for field in client_fields)
                        
                        if client_valid:
                            test_results.add_result(
                                "Driver Tasks - Task Structure",
                                True,
                                f"✅ Task structure valid. Sample: Order {first_task.get('tracking_id')}, Client: {client.get('name')}, COD: {first_task.get('cod_amount')} DZD"
                            )
                        else:
                            test_results.add_result(
                                "Driver Tasks - Task Structure",
                                False,
                                f"Client structure missing fields: {client_fields}",
                                f"Client data: {client}"
                            )
                    else:
                        test_results.add_result(
                            "Driver Tasks - Task Structure",
                            False,
                            f"Task structure missing fields: {task_required_fields}",
                            f"Task data: {first_task}"
                        )
                else:
                    test_results.add_result(
                        "Driver Tasks - Task Count",
                        True,
                        f"✅ No tasks assigned to driver (expected if no orders are IN_TRANSIT/PICKED_UP/OUT_FOR_DELIVERY)"
                    )
                
                return True
            else:
                test_results.add_result(
                    "Driver Tasks - Response Structure",
                    False,
                    f"Response missing required fields: {required_fields}",
                    f"Response data: {data}"
                )
                return False
        else:
            test_results.add_result(
                "Driver Tasks - API Response",
                False,
                f"GET /api/driver/tasks failed with status {response.status_code}",
                response.text
            )
            return False
            
    except Exception as e:
        test_results.add_result(
            "Driver Tasks - API Request",
            False,
            f"Driver tasks request failed: {str(e)}"
        )
        return False

def test_driver_update_status_delivered():
    """Test POST /api/driver/update-status with DELIVERED status"""
    
    print("✅ Testing Driver Update Status - DELIVERED...")
    
    # First, get a task to update
    try:
        tasks_response = requests.get(
            f"{API_BASE}/driver/tasks",
            headers=driver_headers,
            timeout=30
        )
        
        if tasks_response.status_code != 200:
            test_results.add_result(
                "Driver Update Status - Get Tasks",
                False,
                f"Failed to get tasks: {tasks_response.status_code}",
                tasks_response.text
            )
            return False
        
        tasks_data = tasks_response.json()
        tasks = tasks_data.get('tasks', [])
        
        if not tasks:
            # No tasks available for testing
            test_results.add_result(
                "Driver Update Status - No Tasks",
                True,
                "No tasks available for testing (expected if no orders assigned to driver)"
            )
            return True
        
        # Use first task
        test_order_id = tasks[0].get('order_id')
        
        if not test_order_id:
            test_results.add_result(
                "Driver Update Status - Order ID",
                False,
                "No valid order ID found in tasks"
            )
            return False
        
        # Test DELIVERED status update
        update_data = {
            "order_id": test_order_id,
            "new_status": "DELIVERED",
            "location": "Livré à domicile",
            "notes": "Client satisfait"
        }
        
        response = requests.post(
            f"{API_BASE}/driver/update-status",
            json=update_data,
            headers=driver_headers,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            
            # Verify response structure
            required_fields = ['success', 'new_status', 'payment_status']
            has_all_fields = all(field in data for field in required_fields)
            
            if has_all_fields:
                success = data.get('success', False)
                new_status = data.get('new_status', '')
                payment_status = data.get('payment_status', '')
                
                # CRITICAL: Verify payment_status was auto-updated to collected_by_driver
                if success and new_status == "DELIVERED" and payment_status == "collected_by_driver":
                    test_results.add_result(
                        "Driver Update Status - DELIVERED",
                        True,
                        f"✅ CRITICAL LOGIC WORKING: Status updated to DELIVERED, payment_status auto-updated to 'collected_by_driver'"
                    )
                    return True
                else:
                    test_results.add_result(
                        "Driver Update Status - DELIVERED",
                        False,
                        f"❌ CRITICAL LOGIC FAILED: Expected payment_status='collected_by_driver', got '{payment_status}'",
                        f"Success: {success}, Status: {new_status}, Payment: {payment_status}"
                    )
                    return False
            else:
                test_results.add_result(
                    "Driver Update Status - Response Structure",
                    False,
                    f"Response missing required fields: {required_fields}",
                    f"Response: {data}"
                )
                return False
        else:
            test_results.add_result(
                "Driver Update Status - DELIVERED",
                False,
                f"Status update failed with status {response.status_code}",
                response.text
            )
            return False
            
    except Exception as e:
        test_results.add_result(
            "Driver Update Status - DELIVERED",
            False,
            f"Status update request failed: {str(e)}"
        )
        return False

def test_driver_update_status_failed_no_reason():
    """Test POST /api/driver/update-status with FAILED status but no reason (should fail)"""
    
    print("❌ Testing Driver Update Status - FAILED without reason...")
    
    # Get a task to update
    try:
        tasks_response = requests.get(
            f"{API_BASE}/driver/tasks",
            headers=driver_headers,
            timeout=30
        )
        
        if tasks_response.status_code != 200:
            test_results.add_result(
                "Driver Update Status - Get Tasks for FAILED",
                False,
                f"Failed to get tasks: {tasks_response.status_code}",
                tasks_response.text
            )
            return False
        
        tasks_data = tasks_response.json()
        tasks = tasks_data.get('tasks', [])
        
        if not tasks:
            test_results.add_result(
                "Driver Update Status - FAILED No Reason",
                True,
                "No tasks available for testing (expected if no orders assigned to driver)"
            )
            return True
        
        # Use first task
        test_order_id = tasks[0].get('order_id')
        
        # Test FAILED status update WITHOUT failure_reason
        update_data = {
            "order_id": test_order_id,
            "new_status": "FAILED",
            "notes": "Appelé 3 fois, pas de réponse"
            # Missing failure_reason intentionally
        }
        
        response = requests.post(
            f"{API_BASE}/driver/update-status",
            json=update_data,
            headers=driver_headers,
            timeout=30
        )
        
        # Should return 400 Bad Request
        if response.status_code == 400:
            error_data = response.json()
            error_message = error_data.get('detail', '')
            
            if "Failure reason is required when marking order as FAILED" in error_message:
                test_results.add_result(
                    "Driver Update Status - FAILED No Reason",
                    True,
                    f"✅ Correctly rejected FAILED status without reason: {error_message}"
                )
                return True
            else:
                test_results.add_result(
                    "Driver Update Status - FAILED No Reason",
                    False,
                    f"Unexpected error message",
                    f"Expected: 'Failure reason is required...', Got: {error_message}"
                )
                return False
        else:
            test_results.add_result(
                "Driver Update Status - FAILED No Reason",
                False,
                f"Expected 400 Bad Request, got {response.status_code}",
                response.text
            )
            return False
            
    except Exception as e:
        test_results.add_result(
            "Driver Update Status - FAILED No Reason",
            False,
            f"Status update request failed: {str(e)}"
        )
        return False

def test_driver_update_status_failed_with_reason():
    """Test POST /api/driver/update-status with FAILED status and reason (should succeed)"""
    
    print("❌ Testing Driver Update Status - FAILED with reason...")
    
    # Get a task to update
    try:
        tasks_response = requests.get(
            f"{API_BASE}/driver/tasks",
            headers=driver_headers,
            timeout=30
        )
        
        if tasks_response.status_code != 200:
            test_results.add_result(
                "Driver Update Status - Get Tasks for FAILED with Reason",
                False,
                f"Failed to get tasks: {tasks_response.status_code}",
                tasks_response.text
            )
            return False
        
        tasks_data = tasks_response.json()
        tasks = tasks_data.get('tasks', [])
        
        if not tasks:
            test_results.add_result(
                "Driver Update Status - FAILED with Reason",
                True,
                "No tasks available for testing (expected if no orders assigned to driver)"
            )
            return True
        
        # Use first task
        test_order_id = tasks[0].get('order_id')
        
        # Test FAILED status update WITH failure_reason
        update_data = {
            "order_id": test_order_id,
            "new_status": "FAILED",
            "failure_reason": "Client absent",
            "notes": "Appelé 3 fois, pas de réponse"
        }
        
        response = requests.post(
            f"{API_BASE}/driver/update-status",
            json=update_data,
            headers=driver_headers,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            
            success = data.get('success', False)
            new_status = data.get('new_status', '')
            
            if success and new_status == "FAILED":
                test_results.add_result(
                    "Driver Update Status - FAILED with Reason",
                    True,
                    f"✅ FAILED status update successful with reason: 'Client absent'"
                )
                return True
            else:
                test_results.add_result(
                    "Driver Update Status - FAILED with Reason",
                    False,
                    f"Update response invalid",
                    f"Success: {success}, Status: {new_status}"
                )
                return False
        else:
            test_results.add_result(
                "Driver Update Status - FAILED with Reason",
                False,
                f"Status update failed with status {response.status_code}",
                response.text
            )
            return False
            
    except Exception as e:
        test_results.add_result(
            "Driver Update Status - FAILED with Reason",
            False,
            f"Status update request failed: {str(e)}"
        )
        return False

def test_driver_stats():
    """Test GET /api/driver/stats endpoint"""
    
    print("📊 Testing Driver Stats Endpoint...")
    
    try:
        response = requests.get(
            f"{API_BASE}/driver/stats",
            headers=driver_headers,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            
            # Verify response structure
            required_fields = ['driver_id', 'driver_name', 'today', 'pending', 'message']
            has_all_fields = all(field in data for field in required_fields)
            
            if has_all_fields:
                today_stats = data.get('today', {})
                pending_stats = data.get('pending', {})
                message = data.get('message', '')
                
                # Verify today stats structure
                today_required = ['deliveries', 'failed', 'total_cash_collected']
                today_valid = all(field in today_stats for field in today_required)
                
                # Verify pending stats structure
                pending_required = ['pending_deliveries', 'total_cash_to_transfer']
                pending_valid = all(field in pending_stats for field in pending_required)
                
                if today_valid and pending_valid:
                    deliveries = today_stats.get('deliveries', 0)
                    failed = today_stats.get('failed', 0)
                    cash_collected = today_stats.get('total_cash_collected', 0)
                    pending_deliveries = pending_stats.get('pending_deliveries', 0)
                    cash_to_transfer = pending_stats.get('total_cash_to_transfer', 0)
                    
                    test_results.add_result(
                        "Driver Stats - Response Structure",
                        True,
                        f"✅ Stats retrieved: Today: {deliveries} deliveries, {failed} failed, {cash_collected} DZD collected. Pending: {pending_deliveries} deliveries, {cash_to_transfer} DZD to transfer"
                    )
                    
                    # Verify message format
                    if "Vous devez verser" in message and "DZD aujourd'hui" in message:
                        test_results.add_result(
                            "Driver Stats - Message Format",
                            True,
                            f"✅ Message format correct: {message}"
                        )
                    else:
                        test_results.add_result(
                            "Driver Stats - Message Format",
                            False,
                            f"Message format incorrect",
                            f"Expected: 'Vous devez verser X DZD aujourd'hui', Got: {message}"
                        )
                    
                    return True
                else:
                    test_results.add_result(
                        "Driver Stats - Stats Structure",
                        False,
                        f"Stats structure invalid",
                        f"Today valid: {today_valid}, Pending valid: {pending_valid}"
                    )
                    return False
            else:
                test_results.add_result(
                    "Driver Stats - Response Structure",
                    False,
                    f"Response missing required fields: {required_fields}",
                    f"Response data: {data}"
                )
                return False
        else:
            test_results.add_result(
                "Driver Stats - API Response",
                False,
                f"GET /api/driver/stats failed with status {response.status_code}",
                response.text
            )
            return False
            
    except Exception as e:
        test_results.add_result(
            "Driver Stats - API Request",
            False,
            f"Driver stats request failed: {str(e)}"
        )
        return False

def test_cross_driver_access():
    """Test that driver cannot access orders not assigned to them"""
    
    print("🔒 Testing Cross-Driver Access Security...")
    
    # This test requires having orders assigned to different drivers
    # For now, we'll test with a non-existent order ID
    
    try:
        fake_order_id = "non-existent-order-id"
        
        update_data = {
            "order_id": fake_order_id,
            "new_status": "DELIVERED",
            "notes": "Attempting to update non-assigned order"
        }
        
        response = requests.post(
            f"{API_BASE}/driver/update-status",
            json=update_data,
            headers=driver_headers,
            timeout=30
        )
        
        if response.status_code == 404:
            error_data = response.json()
            error_message = error_data.get('detail', '')
            
            if "Order not found or not assigned to this driver" in error_message:
                test_results.add_result(
                    "Cross-Driver Access Security",
                    True,
                    f"✅ Correctly denied access to non-assigned order: {error_message}"
                )
                return True
            else:
                test_results.add_result(
                    "Cross-Driver Access Security",
                    False,
                    f"Unexpected error message",
                    f"Expected: 'Order not found or not assigned to this driver', Got: {error_message}"
                )
                return False
        else:
            test_results.add_result(
                "Cross-Driver Access Security",
                False,
                f"Expected 404 Not Found, got {response.status_code}",
                response.text
            )
            return False
            
    except Exception as e:
        test_results.add_result(
            "Cross-Driver Access Security",
            False,
            f"Cross-driver access test failed: {str(e)}"
        )
        return False

def run_all_tests():
    """Run all backend tests - CRITICAL DEMO FIXES FIRST"""
    
    print(f"🚀 Starting Backend API Tests for Beyond Express - CRITICAL DEMO FIXES")
    print(f"Base URL: {BASE_URL}")
    print(f"API Base: {API_BASE}")
    print(f"{'='*60}")
    print(f"🔥 PRIORITY: Testing critical fixes for demo")
    print(f"{'='*60}")
    
    # Test sequence - CRITICAL DEMO FIXES FIRST
    tests = [
        ("🚚 YALIDINE - Carrier Status API", test_yalidine_carrier_status_api),
        ("🗺️ YALIDINE - Algeria Wilayas Module", test_algeria_wilayas_module),
        ("📱 YALIDINE - Adapter Data Mapping", test_yalidine_adapter_data_mapping),
        ("🚀 SMART ROUTING ENGINE - Shipping API", test_smart_routing_engine_shipping_api),
        ("🔗 WEBHOOKS - Test Endpoints", test_webhooks_endpoints),
        ("🚚 CARRIERS - Configuration API", test_carriers_configuration),
        ("🔥 P0 CRITICAL - Admin Dashboard", test_admin_dashboard_critical),
        ("🚛 P1 CRITICAL - Driver PWA", test_driver_pwa_critical),
        ("🔧 P1 CRITICAL - Driver API curl simulation", test_driver_api_curl_simulation),
        ("Authentication", test_authentication),
        ("🚗 DRIVER API - Authentication", test_driver_authentication),
        ("🔒 DRIVER API - Authorization", test_driver_authorization),
        ("📋 DRIVER API - Tasks", test_driver_tasks),
        ("✅ DRIVER API - Update Status DELIVERED", test_driver_update_status_delivered),
        ("❌ DRIVER API - Update Status FAILED (No Reason)", test_driver_update_status_failed_no_reason),
        ("❌ DRIVER API - Update Status FAILED (With Reason)", test_driver_update_status_failed_with_reason),
        ("📊 DRIVER API - Stats", test_driver_stats),
        ("🔒 DRIVER API - Cross-Driver Access Security", test_cross_driver_access),
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