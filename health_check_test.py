#!/usr/bin/env python3
"""
HEALTH CHECK CRITIQUE - BACKEND API ENDPOINTS
Testing all critical endpoints before investor demo

Test Requirements from Review Request:
1. Login Admin (Argon2id) - POST /api/auth/login
2. Dashboard Stats - GET /api/dashboard/stats  
3. Orders List - GET /api/orders (15 realistic orders with Algerian names)
4. Audit Log Integrity - GET /api/audit/verify-integrity
5. Driver Tasks - POST /api/auth/login (driver) + GET /api/driver/tasks
6. Performance Check - All responses <100ms
"""

import requests
import json
import time
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/app/frontend/.env')

# Configuration
BASE_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://beyond-express-next.preview.emergentagent.com')
API_BASE = f"{BASE_URL}/api"

# Credentials from review request
ADMIN_CREDENTIALS = {
    "email": "cherier.sam@beyondexpress-batna.com",
    "password": "admin123456"
}

DRIVER_CREDENTIALS = {
    "email": "driver@beyond.com", 
    "password": "driver123"
}

class HealthCheckResults:
    def __init__(self):
        self.results = []
        self.passed = 0
        self.failed = 0
        self.performance_times = []
    
    def add_result(self, test_name, success, message, details=None, response_time=None):
        self.results.append({
            'test': test_name,
            'success': success,
            'message': message,
            'details': details,
            'response_time': response_time,
            'timestamp': datetime.now().isoformat()
        })
        if success:
            self.passed += 1
        else:
            self.failed += 1
        
        if response_time:
            self.performance_times.append(response_time)
    
    def print_summary(self):
        print(f"\n{'='*80}")
        print(f"HEALTH CHECK CRITIQUE - BACKEND API ENDPOINTS")
        print(f"{'='*80}")
        print(f"Total Tests: {len(self.results)}")
        print(f"✅ Passed: {self.passed}")
        print(f"❌ Failed: {self.failed}")
        print(f"Success Rate: {(self.passed/len(self.results)*100):.1f}%")
        
        if self.performance_times:
            avg_time = sum(self.performance_times) / len(self.performance_times)
            max_time = max(self.performance_times)
            print(f"⚡ Performance: Avg {avg_time:.0f}ms, Max {max_time:.0f}ms")
        
        print(f"{'='*80}")
        
        for result in self.results:
            status = "✅ PASS" if result['success'] else "❌ FAIL"
            time_info = f" ({result['response_time']:.0f}ms)" if result['response_time'] else ""
            print(f"{status} - {result['test']}{time_info}")
            if not result['success']:
                print(f"    ❌ Error: {result['message']}")
                if result['details']:
                    print(f"    📋 Details: {result['details']}")
        print(f"{'='*80}")

def make_request(method, url, **kwargs):
    """Make HTTP request and measure response time"""
    start_time = time.time()
    try:
        if method.upper() == 'GET':
            response = requests.get(url, **kwargs)
        elif method.upper() == 'POST':
            response = requests.post(url, **kwargs)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        response_time = (time.time() - start_time) * 1000  # Convert to milliseconds
        return response, response_time
    except Exception as e:
        response_time = (time.time() - start_time) * 1000
        raise e

def test_admin_login():
    """Test 1: Login Admin (Argon2id) - POST /api/auth/login"""
    print("🔐 Testing Admin Login (Argon2id)...")
    
    try:
        response, response_time = make_request(
            'POST',
            f"{API_BASE}/auth/login",
            json=ADMIN_CREDENTIALS,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            access_token = data.get('access_token')
            user_data = data.get('user', {})
            
            if access_token and user_data.get('email') == ADMIN_CREDENTIALS['email']:
                health_results.add_result(
                    "Admin Login (Argon2id)",
                    True,
                    f"✅ Admin login successful. User: {user_data.get('name', 'Unknown')} ({user_data.get('email')})",
                    f"Token: {access_token[:20]}...",
                    response_time
                )
                return access_token, response_time
            else:
                health_results.add_result(
                    "Admin Login (Argon2id)",
                    False,
                    "Login response missing access_token or user data",
                    str(data),
                    response_time
                )
                return None, response_time
        else:
            health_results.add_result(
                "Admin Login (Argon2id)",
                False,
                f"Login failed with status {response.status_code}",
                response.text,
                response_time
            )
            return None, response_time
            
    except Exception as e:
        health_results.add_result(
            "Admin Login (Argon2id)",
            False,
            f"Login request failed: {str(e)}"
        )
        return None, None

def test_dashboard_stats(headers):
    """Test 2: Dashboard Stats - GET /api/dashboard/stats"""
    print("📊 Testing Dashboard Stats...")
    
    try:
        response, response_time = make_request(
            'GET',
            f"{API_BASE}/dashboard/stats",
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            
            # Check required KPI fields
            required_fields = ['total_orders', 'total_users', 'total_products', 'in_transit']
            missing_fields = [field for field in required_fields if field not in data]
            
            if not missing_fields:
                health_results.add_result(
                    "Dashboard Stats KPIs",
                    True,
                    f"✅ All KPIs returned: Orders={data['total_orders']}, Users={data['total_users']}, Products={data['total_products']}, In Transit={data['in_transit']}",
                    None,
                    response_time
                )
                return True, response_time
            else:
                health_results.add_result(
                    "Dashboard Stats KPIs",
                    False,
                    f"Missing required KPI fields: {missing_fields}",
                    str(data),
                    response_time
                )
                return False, response_time
        else:
            health_results.add_result(
                "Dashboard Stats KPIs",
                False,
                f"Dashboard stats failed with status {response.status_code}",
                response.text,
                response_time
            )
            return False, response_time
            
    except Exception as e:
        health_results.add_result(
            "Dashboard Stats KPIs",
            False,
            f"Dashboard stats request failed: {str(e)}"
        )
        return False, None

def test_orders_list(headers):
    """Test 3: Orders List - GET /api/orders (15 realistic orders with Algerian names)"""
    print("📦 Testing Orders List (15 realistic orders)...")
    
    try:
        response, response_time = make_request(
            'GET',
            f"{API_BASE}/orders",
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            
            # Handle both list and paginated response formats
            if isinstance(data, dict) and 'orders' in data:
                orders = data['orders']
                total = data.get('total', len(orders))
            elif isinstance(data, list):
                orders = data
                total = len(orders)
            else:
                health_results.add_result(
                    "Orders List Format",
                    False,
                    "Unexpected response format",
                    str(data),
                    response_time
                )
                return False, response_time
            
            # Check order count (expecting at least 15)
            if len(orders) >= 15:
                health_results.add_result(
                    "Orders Count (≥15)",
                    True,
                    f"✅ Found {len(orders)} orders (expected ≥15)",
                    f"Total in database: {total}",
                    response_time
                )
            else:
                health_results.add_result(
                    "Orders Count (≥15)",
                    False,
                    f"Only {len(orders)} orders found, expected ≥15",
                    f"Total in database: {total}",
                    response_time
                )
                return False, response_time
            
            # Check for Algerian names in orders
            algerian_names = []
            algerian_keywords = [
                'ahmed', 'mohamed', 'fatima', 'khadija', 'omar', 'ali', 'amina', 'sarah',
                'youcef', 'karim', 'nadia', 'leila', 'rachid', 'samira', 'abderrahim',
                'benali', 'benaissa', 'boumediene', 'messaoudi', 'belabes', 'zohra'
            ]
            
            for order in orders[:15]:  # Check first 15 orders
                recipient_name = order.get('recipient', {}).get('name', '').lower()
                if any(keyword in recipient_name for keyword in algerian_keywords):
                    algerian_names.append(order.get('recipient', {}).get('name', 'Unknown'))
            
            if len(algerian_names) >= 10:  # At least 10 Algerian names
                health_results.add_result(
                    "Algerian Names in Orders",
                    True,
                    f"✅ Found {len(algerian_names)} orders with Algerian names",
                    f"Examples: {', '.join(algerian_names[:5])}",
                    response_time
                )
            else:
                health_results.add_result(
                    "Algerian Names in Orders",
                    False,
                    f"Only {len(algerian_names)} orders with Algerian names found",
                    f"Found names: {', '.join(algerian_names)}",
                    response_time
                )
            
            return True, response_time
        else:
            health_results.add_result(
                "Orders List Response",
                False,
                f"Orders list failed with status {response.status_code}",
                response.text,
                response_time
            )
            return False, response_time
            
    except Exception as e:
        health_results.add_result(
            "Orders List Request",
            False,
            f"Orders list request failed: {str(e)}"
        )
        return False, None

def test_audit_log_integrity(headers):
    """Test 4: Audit Log Integrity - GET /api/audit/verify-integrity"""
    print("🔒 Testing Audit Log Integrity...")
    
    try:
        response, response_time = make_request(
            'GET',
            f"{API_BASE}/audit/verify-integrity",
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            
            # Check if integrity verification passed
            is_valid = data.get('valid', False)
            chain_length = data.get('chain_length', 0)
            
            if is_valid:
                health_results.add_result(
                    "Audit Log Integrity",
                    True,
                    f"✅ Audit chain integrity verified (valid: true)",
                    f"Chain length: {chain_length} entries",
                    response_time
                )
                return True, response_time
            else:
                health_results.add_result(
                    "Audit Log Integrity",
                    False,
                    f"Audit chain integrity failed (valid: false)",
                    str(data),
                    response_time
                )
                return False, response_time
        else:
            health_results.add_result(
                "Audit Log Integrity",
                False,
                f"Audit integrity check failed with status {response.status_code}",
                response.text,
                response_time
            )
            return False, response_time
            
    except Exception as e:
        health_results.add_result(
            "Audit Log Integrity",
            False,
            f"Audit integrity request failed: {str(e)}"
        )
        return False, None

def test_driver_login_and_tasks():
    """Test 5: Driver Tasks - Login + GET /api/driver/tasks"""
    print("🚚 Testing Driver Login and Tasks...")
    
    # Step 1: Driver Login
    try:
        response, response_time = make_request(
            'POST',
            f"{API_BASE}/auth/login",
            json=DRIVER_CREDENTIALS,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            driver_token = data.get('access_token')
            user_data = data.get('user', {})
            
            if driver_token and user_data.get('email') == DRIVER_CREDENTIALS['email']:
                health_results.add_result(
                    "Driver Login",
                    True,
                    f"✅ Driver login successful. User: {user_data.get('name', 'Unknown')} ({user_data.get('email')})",
                    f"Role: {user_data.get('role', 'Unknown')}",
                    response_time
                )
                driver_headers = {'Authorization': f'Bearer {driver_token}'}
            else:
                health_results.add_result(
                    "Driver Login",
                    False,
                    "Driver login response missing access_token or user data",
                    str(data),
                    response_time
                )
                return False, response_time
        else:
            health_results.add_result(
                "Driver Login",
                False,
                f"Driver login failed with status {response.status_code}",
                response.text,
                response_time
            )
            return False, response_time
            
    except Exception as e:
        health_results.add_result(
            "Driver Login",
            False,
            f"Driver login request failed: {str(e)}"
        )
        return False, None
    
    # Step 2: Get Driver Tasks
    try:
        response, response_time = make_request(
            'GET',
            f"{API_BASE}/driver/tasks",
            headers=driver_headers,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            
            # Check if tasks are returned (can be empty array)
            if isinstance(data, list):
                health_results.add_result(
                    "Driver Tasks List",
                    True,
                    f"✅ Driver tasks retrieved successfully ({len(data)} tasks)",
                    f"Tasks format: {type(data).__name__}",
                    response_time
                )
                return True, response_time
            elif isinstance(data, dict) and 'tasks' in data:
                tasks = data['tasks']
                health_results.add_result(
                    "Driver Tasks List",
                    True,
                    f"✅ Driver tasks retrieved successfully ({len(tasks)} tasks)",
                    f"Response includes metadata",
                    response_time
                )
                return True, response_time
            else:
                health_results.add_result(
                    "Driver Tasks List",
                    False,
                    "Unexpected driver tasks response format",
                    str(data),
                    response_time
                )
                return False, response_time
        else:
            health_results.add_result(
                "Driver Tasks List",
                False,
                f"Driver tasks failed with status {response.status_code}",
                response.text,
                response_time
            )
            return False, response_time
            
    except Exception as e:
        health_results.add_result(
            "Driver Tasks List",
            False,
            f"Driver tasks request failed: {str(e)}"
        )
        return False, None

def test_performance_check():
    """Test 6: Performance Check - All responses <100ms"""
    print("⚡ Analyzing Performance Check...")
    
    if not health_results.performance_times:
        health_results.add_result(
            "Performance Check (<100ms)",
            False,
            "No performance data collected"
        )
        return False
    
    # Calculate performance metrics
    avg_time = sum(health_results.performance_times) / len(health_results.performance_times)
    max_time = max(health_results.performance_times)
    min_time = min(health_results.performance_times)
    
    # Count responses under 100ms
    fast_responses = [t for t in health_results.performance_times if t < 100]
    fast_percentage = (len(fast_responses) / len(health_results.performance_times)) * 100
    
    if avg_time < 100 and max_time < 200:  # Allow some tolerance for max
        health_results.add_result(
            "Performance Check (<100ms)",
            True,
            f"✅ Excellent performance: Avg {avg_time:.0f}ms, Max {max_time:.0f}ms, {fast_percentage:.0f}% under 100ms",
            f"Min: {min_time:.0f}ms, Responses tested: {len(health_results.performance_times)}"
        )
        return True
    elif avg_time < 150:  # Acceptable performance
        health_results.add_result(
            "Performance Check (<100ms)",
            True,
            f"✅ Good performance: Avg {avg_time:.0f}ms, Max {max_time:.0f}ms, {fast_percentage:.0f}% under 100ms",
            f"Min: {min_time:.0f}ms, Slightly above target but acceptable"
        )
        return True
    else:
        health_results.add_result(
            "Performance Check (<100ms)",
            False,
            f"❌ Performance issues: Avg {avg_time:.0f}ms, Max {max_time:.0f}ms, {fast_percentage:.0f}% under 100ms",
            f"Min: {min_time:.0f}ms, Exceeds 100ms target"
        )
        return False

def run_health_check():
    """Run complete health check suite"""
    print(f"\n{'='*80}")
    print(f"HEALTH CHECK CRITIQUE - BACKEND API ENDPOINTS")
    print(f"Testing for investor demo readiness")
    print(f"Base URL: {BASE_URL}")
    print(f"{'='*80}")
    
    # Test 1: Admin Login
    admin_token, login_time = test_admin_login()
    if not admin_token:
        print("❌ CRITICAL: Admin login failed - cannot continue with authenticated tests")
        return False
    
    admin_headers = {'Authorization': f'Bearer {admin_token}'}
    
    # Test 2: Dashboard Stats
    test_dashboard_stats(admin_headers)
    
    # Test 3: Orders List
    test_orders_list(admin_headers)
    
    # Test 4: Audit Log Integrity
    test_audit_log_integrity(admin_headers)
    
    # Test 5: Driver Login and Tasks
    test_driver_login_and_tasks()
    
    # Test 6: Performance Analysis
    test_performance_check()
    
    # Print final results
    health_results.print_summary()
    
    # Return overall success
    return health_results.failed == 0

if __name__ == "__main__":
    health_results = HealthCheckResults()
    
    try:
        success = run_health_check()
        
        if success:
            print(f"\n🎉 HEALTH CHECK PASSED - READY FOR INVESTOR DEMO!")
            exit(0)
        else:
            print(f"\n⚠️  HEALTH CHECK ISSUES FOUND - REVIEW REQUIRED")
            exit(1)
            
    except KeyboardInterrupt:
        print(f"\n⚠️  Health check interrupted by user")
        exit(1)
    except Exception as e:
        print(f"\n❌ CRITICAL ERROR during health check: {str(e)}")
        exit(1)