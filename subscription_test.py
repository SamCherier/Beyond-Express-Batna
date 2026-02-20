#!/usr/bin/env python3
"""
Subscription Management API Testing for Beyond Express - Stores Module
Tests all subscription and plan management endpoints as specified in the review request.
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

# Test user from review request
TEST_USER = {
    "email": "testsubscriptions@test.dz",
    "password": "Test123!",
    "name": "Test Subscriptions User",
    "role": "ecommerce"
}

# Global variables for test session
session_token = None
headers = {}
test_subscription_id = None

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
        print(f"\n{'='*80}")
        print(f"SUBSCRIPTION MANAGEMENT API TEST SUMMARY")
        print(f"{'='*80}")
        print(f"Total Tests: {len(self.results)}")
        print(f"Passed: {self.passed}")
        print(f"Failed: {self.failed}")
        print(f"Success Rate: {(self.passed/len(self.results)*100):.1f}%")
        print(f"{'='*80}")
        
        for result in self.results:
            status = "✅ PASS" if result['success'] else "❌ FAIL"
            print(f"{status} - {result['test']}")
            if not result['success']:
                print(f"    Error: {result['message']}")
                if result['details']:
                    print(f"    Details: {result['details']}")
        print(f"{'='*80}")

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

def test_get_all_plans():
    """Test GET /api/subscriptions/plans (PUBLIC - no auth required)"""
    
    print("📋 Testing Get All Plans (PUBLIC)...")
    
    try:
        response = requests.get(
            f"{API_BASE}/subscriptions/plans",
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            
            # Verify response structure
            if 'plans' in data and 'total' in data:
                plans = data['plans']
                
                # Check if we have 4 plans as expected
                if len(plans) == 4:
                    # Verify plan types
                    plan_types = [plan.get('plan_type') for plan in plans]
                    expected_types = ['free', 'starter', 'pro', 'business']
                    
                    if all(ptype in plan_types for ptype in expected_types):
                        # Verify each plan has required fields
                        valid_plans = True
                        for plan in plans:
                            required_fields = ['plan_type', 'name_fr', 'name_ar', 'name_en', 
                                             'description_fr', 'features', 'pricing', 'is_active']
                            if not all(field in plan for field in required_fields):
                                valid_plans = False
                                break
                        
                        if valid_plans:
                            test_results.add_result(
                                "Get All Plans - Structure",
                                True,
                                f"Retrieved {len(plans)} plans with all required fields"
                            )
                            
                            # Test specific plan features
                            starter_plan = next((p for p in plans if p['plan_type'] == 'starter'), None)
                            if starter_plan:
                                features = starter_plan.get('features', {})
                                pricing = starter_plan.get('pricing', {})
                                
                                # Verify STARTER plan features
                                has_monthly_price = 'monthly_price' in pricing
                                has_order_limit = 'max_orders_per_month' in features
                                
                                test_results.add_result(
                                    "Get All Plans - STARTER Plan Details",
                                    has_monthly_price and has_order_limit,
                                    f"STARTER plan: Monthly price: {pricing.get('monthly_price', 'N/A')} DA, Order limit: {features.get('max_orders_per_month', 'N/A')}"
                                )
                            
                            return True
                        else:
                            test_results.add_result(
                                "Get All Plans - Structure",
                                False,
                                "Some plans missing required fields"
                            )
                            return False
                    else:
                        test_results.add_result(
                            "Get All Plans - Plan Types",
                            False,
                            f"Missing expected plan types. Found: {plan_types}"
                        )
                        return False
                else:
                    test_results.add_result(
                        "Get All Plans - Count",
                        False,
                        f"Expected 4 plans, got {len(plans)}"
                    )
                    return False
            else:
                test_results.add_result(
                    "Get All Plans - Response Format",
                    False,
                    "Response missing 'plans' or 'total' field",
                    str(data)
                )
                return False
        else:
            test_results.add_result(
                "Get All Plans - HTTP Status",
                False,
                f"Request failed with status {response.status_code}",
                response.text
            )
            return False
            
    except Exception as e:
        test_results.add_result(
            "Get All Plans - Request",
            False,
            f"Request failed: {str(e)}"
        )
        return False

def test_get_specific_plan():
    """Test GET /api/subscriptions/plans/{plan_type} (PUBLIC)"""
    
    print("📄 Testing Get Specific Plan (PUBLIC)...")
    
    # Test valid plan types
    valid_plans = ['starter', 'pro', 'free']
    
    for plan_type in valid_plans:
        try:
            response = requests.get(
                f"{API_BASE}/subscriptions/plans/{plan_type}",
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify plan type matches
                if data.get('plan_type') == plan_type:
                    test_results.add_result(
                        f"Get Specific Plan - {plan_type.upper()}",
                        True,
                        f"Retrieved {plan_type} plan: {data.get('name_fr', 'N/A')}"
                    )
                else:
                    test_results.add_result(
                        f"Get Specific Plan - {plan_type.upper()}",
                        False,
                        f"Plan type mismatch: expected {plan_type}, got {data.get('plan_type')}"
                    )
            else:
                test_results.add_result(
                    f"Get Specific Plan - {plan_type.upper()}",
                    False,
                    f"Request failed with status {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            test_results.add_result(
                f"Get Specific Plan - {plan_type.upper()}",
                False,
                f"Request failed: {str(e)}"
            )
    
    # Test invalid plan type (should return 404)
    try:
        response = requests.get(
            f"{API_BASE}/subscriptions/plans/invalid",
            timeout=30
        )
        
        if response.status_code == 404:
            test_results.add_result(
                "Get Specific Plan - Invalid Plan (404)",
                True,
                "Correctly returned 404 for invalid plan type"
            )
        else:
            test_results.add_result(
                "Get Specific Plan - Invalid Plan (404)",
                False,
                f"Expected 404, got {response.status_code}"
            )
            
    except Exception as e:
        test_results.add_result(
            "Get Specific Plan - Invalid Plan (404)",
            False,
            f"Request failed: {str(e)}"
        )

def test_subscribe_to_plan():
    """Test POST /api/subscriptions/subscribe (AUTHENTICATED)"""
    global test_subscription_id
    
    print("💳 Testing Subscribe to Plan (AUTHENTICATED)...")
    
    # Test one subscription to STARTER monthly for the main flow
    try:
        response = requests.post(
            f"{API_BASE}/subscriptions/subscribe",
            json={
                "plan_type": "starter",
                "billing_period": "monthly"
            },
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            
            # Verify response structure
            if data.get('success') and 'subscription' in data:
                subscription = data['subscription']
                test_subscription_id = subscription.get('id')
                
                # Verify subscription details
                correct_plan = subscription.get('plan_type') == 'starter'
                correct_period = subscription.get('billing_period') == 'monthly'
                has_dates = 'start_date' in subscription and 'end_date' in subscription
                has_amount = 'amount_paid' in subscription and subscription['amount_paid'] > 0
                
                if correct_plan and correct_period and has_dates and has_amount:
                    test_results.add_result(
                        "Subscribe - STARTER MONTHLY",
                        True,
                        f"Successfully subscribed to STARTER monthly: {subscription['amount_paid']} DA"
                    )
                    
                    # Test other billing periods separately
                    test_other_billing_periods()
                    
                    return True
                else:
                    test_results.add_result(
                        "Subscribe - STARTER MONTHLY",
                        False,
                        "Subscription created but missing required fields",
                        f"Plan: {subscription.get('plan_type')}, Period: {subscription.get('billing_period')}"
                    )
            else:
                test_results.add_result(
                    "Subscribe - STARTER MONTHLY",
                    False,
                    "Response missing success or subscription field",
                    str(data)
                )
        else:
            test_results.add_result(
                "Subscribe - STARTER MONTHLY",
                False,
                f"Request failed with status {response.status_code}",
                response.text
            )
            
    except Exception as e:
        test_results.add_result(
            "Subscribe - STARTER MONTHLY",
            False,
            f"Request failed: {str(e)}"
        )
    
    return test_subscription_id is not None

def test_other_billing_periods():
    """Test other billing periods (quarterly, biannual, annual)"""
    
    billing_periods = ['quarterly', 'biannual', 'annual']
    
    for billing_period in billing_periods:
        try:
            response = requests.post(
                f"{API_BASE}/subscriptions/subscribe",
                json={
                    "plan_type": "starter",
                    "billing_period": billing_period
                },
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('success') and 'subscription' in data:
                    subscription = data['subscription']
                    
                    # Verify subscription details
                    correct_plan = subscription.get('plan_type') == 'starter'
                    correct_period = subscription.get('billing_period') == billing_period
                    has_amount = 'amount_paid' in subscription and subscription['amount_paid'] > 0
                    
                    if correct_plan and correct_period and has_amount:
                        test_results.add_result(
                            f"Subscribe - STARTER {billing_period.upper()}",
                            True,
                            f"Successfully subscribed to STARTER {billing_period}: {subscription['amount_paid']} DA"
                        )
                    else:
                        test_results.add_result(
                            f"Subscribe - STARTER {billing_period.upper()}",
                            False,
                            "Subscription created but missing required fields"
                        )
                else:
                    test_results.add_result(
                        f"Subscribe - STARTER {billing_period.upper()}",
                        False,
                        "Response missing success or subscription field"
                    )
            else:
                test_results.add_result(
                    f"Subscribe - STARTER {billing_period.upper()}",
                    False,
                    f"Request failed with status {response.status_code}"
                )
                
        except Exception as e:
            test_results.add_result(
                f"Subscribe - STARTER {billing_period.upper()}",
                False,
                f"Request failed: {str(e)}"
            )

def test_get_my_subscription():
    """Test GET /api/subscriptions/my-subscription (AUTHENTICATED)"""
    
    print("📋 Testing Get My Subscription (AUTHENTICATED)...")
    
    try:
        response = requests.get(
            f"{API_BASE}/subscriptions/my-subscription",
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            
            # Should have active subscription from previous test
            if data.get('has_subscription'):
                subscription = data.get('subscription', {})
                
                # Verify subscription details
                is_active = subscription.get('status') == 'active'
                is_starter = subscription.get('plan_type') == 'starter'
                has_dates = 'start_date' in subscription and 'end_date' in subscription
                
                if is_active and is_starter and has_dates:
                    test_results.add_result(
                        "Get My Subscription - Active",
                        True,
                        f"Retrieved active subscription: {subscription.get('plan_type')} {subscription.get('billing_period')}"
                    )
                    return True
                else:
                    test_results.add_result(
                        "Get My Subscription - Active",
                        False,
                        "Subscription found but invalid details",
                        f"Status: {subscription.get('status')}, Plan: {subscription.get('plan_type')}"
                    )
                    return False
            else:
                # If no subscription, should return free plan
                if data.get('current_plan') == 'free':
                    test_results.add_result(
                        "Get My Subscription - Free Plan",
                        True,
                        "No active subscription, correctly showing free plan"
                    )
                    return True
                else:
                    test_results.add_result(
                        "Get My Subscription - No Subscription",
                        False,
                        "No subscription but not showing free plan",
                        str(data)
                    )
                    return False
        else:
            test_results.add_result(
                "Get My Subscription - HTTP Status",
                False,
                f"Request failed with status {response.status_code}",
                response.text
            )
            return False
            
    except Exception as e:
        test_results.add_result(
            "Get My Subscription - Request",
            False,
            f"Request failed: {str(e)}"
        )
        return False

def test_check_feature_limits():
    """Test GET /api/subscriptions/check-limit/{feature} (AUTHENTICATED)"""
    
    print("🔍 Testing Check Feature Limits (AUTHENTICATED)...")
    
    # Test different features
    features = ['orders', 'delivery_companies', 'whatsapp', 'ai_generator', 'pro_dashboard']
    
    for feature in features:
        try:
            response = requests.get(
                f"{API_BASE}/subscriptions/check-limit/{feature}",
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify response structure
                required_fields = ['plan_type', 'feature', 'has_access']
                if all(field in data for field in required_fields):
                    # Verify plan type matches current subscription
                    if data.get('plan_type') == 'starter':
                        # Check specific limits for STARTER plan
                        if feature == 'orders':
                            # STARTER should have max_orders_per_month: 500
                            expected_limit = 500
                            actual_limit = data.get('limit')
                            
                            test_results.add_result(
                                f"Check Limit - {feature.upper()}",
                                actual_limit == expected_limit,
                                f"Orders limit: {actual_limit} (expected: {expected_limit})"
                            )
                        else:
                            test_results.add_result(
                                f"Check Limit - {feature.upper()}",
                                True,
                                f"Feature {feature}: Access={data.get('has_access')}, Limit={data.get('limit', 'N/A')}"
                            )
                    else:
                        test_results.add_result(
                            f"Check Limit - {feature.upper()}",
                            False,
                            f"Plan type mismatch: expected starter, got {data.get('plan_type')}"
                        )
                else:
                    test_results.add_result(
                        f"Check Limit - {feature.upper()}",
                        False,
                        "Response missing required fields",
                        f"Expected: {required_fields}, Got: {list(data.keys())}"
                    )
            else:
                test_results.add_result(
                    f"Check Limit - {feature.upper()}",
                    False,
                    f"Request failed with status {response.status_code}",
                    response.text
                )
                
        except Exception as e:
            test_results.add_result(
                f"Check Limit - {feature.upper()}",
                False,
                f"Request failed: {str(e)}"
            )

def test_upgrade_subscription():
    """Test POST /api/subscriptions/upgrade (AUTHENTICATED)"""
    
    print("⬆️ Testing Upgrade Subscription (AUTHENTICATED)...")
    
    try:
        response = requests.post(
            f"{API_BASE}/subscriptions/upgrade",
            json={
                "new_plan_type": "pro",
                "new_billing_period": "quarterly"
            },
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            
            # Verify upgrade response
            if data.get('success'):
                # Check old and new plan details
                old_plan = data.get('old_plan')
                new_plan = data.get('new_plan')
                subscription = data.get('subscription', {})
                
                # Verify upgrade details
                correct_old = old_plan == 'starter'
                correct_new = new_plan == 'pro'
                correct_subscription = subscription.get('plan_type') == 'pro' and subscription.get('billing_period') == 'quarterly'
                
                if correct_old and correct_new and correct_subscription:
                    test_results.add_result(
                        "Upgrade Subscription - STARTER to PRO",
                        True,
                        f"Successfully upgraded from {old_plan} to {new_plan} (quarterly)"
                    )
                    
                    # Verify old subscription was cancelled by checking my-subscription again
                    verify_response = requests.get(
                        f"{API_BASE}/subscriptions/my-subscription",
                        headers=headers,
                        timeout=30
                    )
                    
                    if verify_response.status_code == 200:
                        verify_data = verify_response.json()
                        if verify_data.get('has_subscription'):
                            current_sub = verify_data.get('subscription', {})
                            if current_sub.get('plan_type') == 'pro':
                                test_results.add_result(
                                    "Upgrade Verification - Current Plan",
                                    True,
                                    "User plan correctly updated to PRO"
                                )
                                return True
                            else:
                                test_results.add_result(
                                    "Upgrade Verification - Current Plan",
                                    False,
                                    f"User plan not updated correctly: {current_sub.get('plan_type')}"
                                )
                        else:
                            test_results.add_result(
                                "Upgrade Verification - Current Plan",
                                False,
                                "No active subscription found after upgrade"
                            )
                    
                    return True
                else:
                    test_results.add_result(
                        "Upgrade Subscription - STARTER to PRO",
                        False,
                        "Upgrade response has incorrect details",
                        f"Old: {old_plan}, New: {new_plan}, Sub plan: {subscription.get('plan_type')}"
                    )
                    return False
            else:
                test_results.add_result(
                    "Upgrade Subscription - STARTER to PRO",
                    False,
                    "Upgrade response indicates failure",
                    str(data)
                )
                return False
        else:
            test_results.add_result(
                "Upgrade Subscription - STARTER to PRO",
                False,
                f"Request failed with status {response.status_code}",
                response.text
            )
            return False
            
    except Exception as e:
        test_results.add_result(
            "Upgrade Subscription - STARTER to PRO",
            False,
            f"Request failed: {str(e)}"
        )
        return False

def test_cancel_subscription():
    """Test POST /api/subscriptions/cancel (AUTHENTICATED)"""
    
    print("❌ Testing Cancel Subscription (AUTHENTICATED)...")
    
    try:
        response = requests.post(
            f"{API_BASE}/subscriptions/cancel",
            json={
                "cancellation_reason": "Testing cancellation"
            },
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            
            # Verify cancellation response
            if data.get('success'):
                previous_plan = data.get('previous_plan')
                
                if previous_plan == 'pro':
                    test_results.add_result(
                        "Cancel Subscription - PRO Plan",
                        True,
                        f"Successfully cancelled {previous_plan} subscription"
                    )
                    
                    # Verify user reverted to FREE plan
                    verify_response = requests.get(
                        f"{API_BASE}/subscriptions/my-subscription",
                        headers=headers,
                        timeout=30
                    )
                    
                    if verify_response.status_code == 200:
                        verify_data = verify_response.json()
                        
                        # Should have no active subscription and show free plan
                        if not verify_data.get('has_subscription') and verify_data.get('current_plan') == 'free':
                            test_results.add_result(
                                "Cancel Verification - Reverted to FREE",
                                True,
                                "User correctly reverted to FREE plan after cancellation"
                            )
                            return True
                        else:
                            test_results.add_result(
                                "Cancel Verification - Reverted to FREE",
                                False,
                                "User not reverted to FREE plan correctly",
                                f"Has subscription: {verify_data.get('has_subscription')}, Current plan: {verify_data.get('current_plan')}"
                            )
                    
                    return True
                else:
                    test_results.add_result(
                        "Cancel Subscription - PRO Plan",
                        False,
                        f"Cancelled wrong plan: {previous_plan} (expected: pro)"
                    )
                    return False
            else:
                test_results.add_result(
                    "Cancel Subscription - PRO Plan",
                    False,
                    "Cancellation response indicates failure",
                    str(data)
                )
                return False
        else:
            test_results.add_result(
                "Cancel Subscription - PRO Plan",
                False,
                f"Request failed with status {response.status_code}",
                response.text
            )
            return False
            
    except Exception as e:
        test_results.add_result(
            "Cancel Subscription - PRO Plan",
            False,
            f"Request failed: {str(e)}"
        )
        return False

def test_user_starts_with_free_plan():
    """Test that user starts with FREE plan by default"""
    
    print("🆓 Testing User Starts with FREE Plan...")
    
    try:
        # Check current user info
        response = requests.get(
            f"{API_BASE}/auth/me",
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            user_data = response.json()
            
            # Check if user has current_plan field set to free
            current_plan = user_data.get('current_plan', 'unknown')
            
            if current_plan == 'free':
                test_results.add_result(
                    "User Default Plan - FREE",
                    True,
                    f"User correctly starts with FREE plan: {current_plan}"
                )
                return True
            else:
                test_results.add_result(
                    "User Default Plan - FREE",
                    False,
                    f"User does not start with FREE plan: {current_plan}"
                )
                return False
        else:
            test_results.add_result(
                "User Default Plan - FREE",
                False,
                f"Failed to get user info: {response.status_code}",
                response.text
            )
            return False
            
    except Exception as e:
        test_results.add_result(
            "User Default Plan - FREE",
            False,
            f"Request failed: {str(e)}"
        )
        return False

def run_subscription_tests():
    """Run all subscription management tests"""
    
    print(f"🚀 Starting Subscription Management API Tests for Beyond Express")
    print(f"Base URL: {BASE_URL}")
    print(f"API Base: {API_BASE}")
    print(f"Test User: {TEST_USER['email']}")
    print(f"{'='*80}")
    
    # Test sequence following the review request flow
    tests = [
        ("Authentication", test_authentication),
        ("User Starts with FREE Plan", test_user_starts_with_free_plan),
        ("Get All Plans (PUBLIC)", test_get_all_plans),
        ("Get Specific Plan (PUBLIC)", test_get_specific_plan),
        ("Subscribe to Plan", test_subscribe_to_plan),
        ("Get My Subscription", test_get_my_subscription),
        ("Check Feature Limits", test_check_feature_limits),
        ("Upgrade Subscription", test_upgrade_subscription),
        ("Cancel Subscription", test_cancel_subscription)
    ]
    
    for test_name, test_func in tests:
        try:
            print(f"\n🔄 Running: {test_name}")
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
    results = run_subscription_tests()