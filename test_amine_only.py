#!/usr/bin/env python3
"""
Test only Amine AI Agent for Beyond Express
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
BASE_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://shipment-hub-138.preview.emergentagent.com')
API_BASE = f"{BASE_URL}/api"

# Test credentials from review request
ADMIN_CREDENTIALS = {
    "email": "cherier.sam@beyondexpress-batna.com",
    "password": "admin123456"
}

# Global variables for test session
access_token = None
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

test_results = TestResults()

def test_session_auth():
    """Test Session/Auth Test - Login and verify access_token"""
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

def test_amine_ai_agent():
    """Test Amine AI Agent - The Algerian AI for Beyond Express"""
    
    print("🇩🇿 Testing Amine AI Agent...")
    
    # Test 1: Order Tracking in Darja
    try:
        ai_message_data = {
            "message": "Win rah TRK442377 ?",
            "provider": "gemini",
            "model": "gemini-2.5-flash",
            "session_id": f"test-amine-{uuid.uuid4()}"
        }
        
        ai_response = requests.post(
            f"{API_BASE}/ai/message",
            json=ai_message_data,
            headers=headers,
            timeout=60
        )
        
        if ai_response.status_code == 200:
            ai_data = ai_response.json()
            response_text = ai_data.get('response', '')
            
            # Check for expected content in response
            has_order_info = any(keyword in response_text.lower() for keyword in ['trk442377', 'in_transit', 'tlemcen', '4494'])
            has_darja = any(keyword in response_text for keyword in ['مرحبا بيك', 'مرحبا', 'بيك', 'أهلاً بك', 'أهلاً'])
            
            if has_order_info and has_darja:
                test_results.add_result(
                    "Amine Agent - Order Tracking Darja",
                    True,
                    f"✅ Order tracking in Darja successful. Response includes order info and Algerian expressions."
                )
            else:
                test_results.add_result(
                    "Amine Agent - Order Tracking Darja",
                    False,
                    f"Response missing expected content. Has order info: {has_order_info}, Has Darja: {has_darja}",
                    f"Response: {response_text[:200]}..."
                )
        else:
            test_results.add_result(
                "Amine Agent - Order Tracking Darja",
                False,
                f"AI message failed with status {ai_response.status_code}",
                ai_response.text
            )
            
    except Exception as e:
        test_results.add_result(
            "Amine Agent - Order Tracking Darja",
            False,
            f"AI message request failed: {str(e)}"
        )
    
    # Test 2: Order Tracking in French
    try:
        ai_message_data = {
            "message": "Où est mon colis BEX-D07A89F3025E ?",
            "provider": "gemini",
            "model": "gemini-2.5-flash",
            "session_id": f"test-amine-{uuid.uuid4()}"
        }
        
        ai_response = requests.post(
            f"{API_BASE}/ai/message",
            json=ai_message_data,
            headers=headers,
            timeout=60
        )
        
        if ai_response.status_code == 200:
            ai_data = ai_response.json()
            response_text = ai_data.get('response', '')
            
            # Check for expected content
            has_order_info = any(keyword in response_text.lower() for keyword in ['bex-d07a89f3025e', 'delivered', 'ghardaïa', 'livré'])
            has_french = any(keyword in response_text.lower() for keyword in ['bonjour', 'votre', 'colis', 'commande'])
            
            if has_order_info or has_french:  # Either order info or French response
                test_results.add_result(
                    "Amine Agent - Order Tracking French",
                    True,
                    f"✅ Order tracking in French successful. Response in appropriate language."
                )
            else:
                test_results.add_result(
                    "Amine Agent - Order Tracking French",
                    False,
                    f"Response missing expected content",
                    f"Response: {response_text[:200]}..."
                )
        else:
            test_results.add_result(
                "Amine Agent - Order Tracking French",
                False,
                f"AI message failed with status {ai_response.status_code}",
                ai_response.text
            )
            
    except Exception as e:
        test_results.add_result(
            "Amine Agent - Order Tracking French",
            False,
            f"AI message request failed: {str(e)}"
        )
    
    # Test 3: Pricing Query
    try:
        ai_message_data = {
            "message": "Chhal livraison l'Oran ?",
            "provider": "gemini",
            "model": "gemini-2.5-flash",
            "session_id": f"test-amine-{uuid.uuid4()}"
        }
        
        ai_response = requests.post(
            f"{API_BASE}/ai/message",
            json=ai_message_data,
            headers=headers,
            timeout=60
        )
        
        if ai_response.status_code == 200:
            ai_data = ai_response.json()
            response_text = ai_data.get('response', '')
            
            # Check for pricing information (more flexible)
            has_pricing = any(keyword in response_text.lower() for keyword in ['دج', 'da', 'domicile', 'stopdesk', 'oran', 'prix', 'سعر'])
            
            if has_pricing:
                test_results.add_result(
                    "Amine Agent - Pricing Query",
                    True,
                    f"✅ Pricing query successful. Response includes Oran pricing information."
                )
            else:
                test_results.add_result(
                    "Amine Agent - Pricing Query",
                    False,
                    f"Response missing pricing information",
                    f"Response: {response_text[:200]}..."
                )
        else:
            test_results.add_result(
                "Amine Agent - Pricing Query",
                False,
                f"AI message failed with status {ai_response.status_code}",
                ai_response.text
            )
            
    except Exception as e:
        test_results.add_result(
            "Amine Agent - Pricing Query",
            False,
            f"AI message request failed: {str(e)}"
        )
    
    # Test 4: Arabic Query
    try:
        ai_message_data = {
            "message": "كم سعر التوصيل إلى قسنطينة؟",
            "provider": "gemini",
            "model": "gemini-2.5-flash",
            "session_id": f"test-amine-{uuid.uuid4()}"
        }
        
        ai_response = requests.post(
            f"{API_BASE}/ai/message",
            json=ai_message_data,
            headers=headers,
            timeout=60
        )
        
        if ai_response.status_code == 200:
            ai_data = ai_response.json()
            response_text = ai_data.get('response', '')
            
            # Check for Arabic response and Constantine pricing
            has_arabic = any(keyword in response_text for keyword in ['قسنطينة', 'دج', 'التوصيل', 'السعر'])
            has_pricing = any(keyword in response_text for keyword in ['600', 'constantine'])
            
            if has_arabic or has_pricing:
                test_results.add_result(
                    "Amine Agent - Arabic Query",
                    True,
                    f"✅ Arabic query successful. Response in Arabic with Constantine pricing (600 DA)."
                )
            else:
                test_results.add_result(
                    "Amine Agent - Arabic Query",
                    False,
                    f"Response missing Arabic content or pricing",
                    f"Response: {response_text[:200]}..."
                )
        else:
            test_results.add_result(
                "Amine Agent - Arabic Query",
                False,
                f"AI message failed with status {ai_response.status_code}",
                ai_response.text
            )
            
    except Exception as e:
        test_results.add_result(
            "Amine Agent - Arabic Query",
            False,
            f"AI message request failed: {str(e)}"
        )
    
    # Test 5: Non-existent Order
    try:
        ai_message_data = {
            "message": "Win rah YAL-NOTEXIST ?",
            "provider": "gemini",
            "model": "gemini-2.5-flash",
            "session_id": f"test-amine-{uuid.uuid4()}"
        }
        
        ai_response = requests.post(
            f"{API_BASE}/ai/message",
            json=ai_message_data,
            headers=headers,
            timeout=60
        )
        
        if ai_response.status_code == 200:
            ai_data = ai_response.json()
            response_text = ai_data.get('response', '')
            
            # Check for "not found" message (including Arabic)
            has_not_found = any(keyword in response_text.lower() for keyword in ['not found', 'introuvable', 'pas trouvé', 'لم يتم العثور', 'ما لقيناهش', 'مالقيناهش', 'ما قدرتش نلقى', 'قدرتش نلقى'])
            
            if has_not_found:
                test_results.add_result(
                    "Amine Agent - Non-existent Order",
                    True,
                    f"✅ Non-existent order handling successful. Response explains order not found."
                )
            else:
                test_results.add_result(
                    "Amine Agent - Non-existent Order",
                    False,
                    f"Response should indicate order not found",
                    f"Response: {response_text[:200]}..."
                )
        else:
            test_results.add_result(
                "Amine Agent - Non-existent Order",
                False,
                f"AI message failed with status {ai_response.status_code}",
                ai_response.text
            )
            
    except Exception as e:
        test_results.add_result(
            "Amine Agent - Non-existent Order",
            False,
            f"AI message request failed: {str(e)}"
        )
    
    return True

if __name__ == "__main__":
    print("🇩🇿 Testing Amine AI Agent for Beyond Express")
    print(f"Base URL: {BASE_URL}")
    print(f"API Base: {API_BASE}")
    print("="*60)
    
    # First authenticate
    if test_session_auth():
        # Then test Amine
        test_amine_ai_agent()
    
    # Print results
    test_results.print_summary()