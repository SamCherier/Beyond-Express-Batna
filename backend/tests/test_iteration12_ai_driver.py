"""
Iteration 12 Tests - AI Chat Rewrite + Driver Verification + Order Status
Tests the following:
1. AI Chat: POST /api/ai-chat accepts JSON body {message, session_id}
2. AI Chat: Works for admin AND delivery roles (no 403)
3. AI Chat: Returns clean fallback text when API key expired/missing
4. AI Chat History: GET /api/ai-chat/history returns sessions
5. AI Brain: POST /api/ai-brain/query works for delivery role
6. Driver Tasks: GET /api/driver/tasks works for delivery role
7. Driver Status: POST /api/driver/update-status with JSON body
8. Order Status: PATCH /api/orders/{id}/status accepts JSON body
9. WhatsApp: GET /api/whatsapp/conversations works for delivery role
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "final_admin@qa.com"
ADMIN_PASSWORD = "Final123!"
DRIVER_EMAIL = "final_delivery@qa.com"
DRIVER_PASSWORD = "Final123!"


@pytest.fixture(scope="module")
def admin_session():
    """Login as admin and return session with auth"""
    session = requests.Session()
    response = session.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
    )
    assert response.status_code == 200, f"Admin login failed: {response.text}"
    data = response.json()
    token = data.get("access_token")
    session.headers.update({"Authorization": f"Bearer {token}"})
    return session


@pytest.fixture(scope="module")
def driver_session():
    """Login as driver (delivery) and return session with auth"""
    session = requests.Session()
    response = session.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": DRIVER_EMAIL, "password": DRIVER_PASSWORD}
    )
    assert response.status_code == 200, f"Driver login failed: {response.text}"
    data = response.json()
    token = data.get("access_token")
    session.headers.update({"Authorization": f"Bearer {token}"})
    return session


class TestAIChatEndpoint:
    """Test the rewritten AI Chat endpoint - POST /api/ai-chat"""
    
    def test_ai_chat_accepts_json_body_admin(self, admin_session):
        """AI Chat accepts JSON body {message, session_id} for admin"""
        response = admin_session.post(
            f"{BASE_URL}/api/ai-chat",
            json={"message": "Bonjour, qu'est-ce que Beyond Express?", "session_id": None}
        )
        assert response.status_code == 200, f"AI chat failed: {response.status_code} - {response.text}"
        data = response.json()
        # Verify response structure
        assert "response" in data, "Response should contain 'response' field"
        assert "session_id" in data, "Response should contain 'session_id' field"
        # Verify we get text back (either AI response or fallback)
        assert isinstance(data["response"], str), "Response should be a string"
        assert len(data["response"]) > 0, "Response should not be empty"
        print(f"✅ Admin AI Chat response: {data['response'][:100]}...")
    
    def test_ai_chat_works_for_delivery_role(self, driver_session):
        """AI Chat should work for delivery role (no 403)"""
        response = driver_session.post(
            f"{BASE_URL}/api/ai-chat",
            json={"message": "Quelles sont mes livraisons du jour?", "session_id": None}
        )
        # Should NOT return 403 - drivers should have access
        assert response.status_code == 200, f"Driver AI chat blocked: {response.status_code} - {response.text}"
        data = response.json()
        assert "response" in data
        assert "session_id" in data
        print(f"✅ Driver AI Chat response: {data['response'][:100]}...")
    
    def test_ai_chat_returns_fallback_not_error(self, admin_session):
        """AI Chat should return clean fallback message, not crash on API errors"""
        response = admin_session.post(
            f"{BASE_URL}/api/ai-chat",
            json={"message": "Test message for fallback", "session_id": None}
        )
        assert response.status_code == 200, "Should return 200 even if AI API fails"
        data = response.json()
        # Should return text response, not error
        assert "response" in data
        assert isinstance(data["response"], str)
        # Even if fallback, should be a French message not an error trace
        assert "Traceback" not in data["response"], "Should not return error traceback"
        print(f"✅ AI Chat fallback/response: {data['response'][:100]}...")
    
    def test_ai_chat_with_session_id(self, admin_session):
        """AI Chat should maintain session when session_id provided"""
        # First message
        resp1 = admin_session.post(
            f"{BASE_URL}/api/ai-chat",
            json={"message": "Premier message de test"}
        )
        assert resp1.status_code == 200
        session_id = resp1.json()["session_id"]
        assert session_id is not None
        
        # Second message with same session
        resp2 = admin_session.post(
            f"{BASE_URL}/api/ai-chat",
            json={"message": "Deuxième message", "session_id": session_id}
        )
        assert resp2.status_code == 200
        assert resp2.json()["session_id"] == session_id
        print(f"✅ Session maintained: {session_id}")


class TestAIChatHistory:
    """Test AI Chat History endpoint - GET /api/ai-chat/history"""
    
    def test_get_chat_history(self, admin_session):
        """GET /api/ai-chat/history returns saved sessions"""
        response = admin_session.get(f"{BASE_URL}/api/ai-chat/history")
        assert response.status_code == 200, f"Chat history failed: {response.text}"
        data = response.json()
        # Should be a list of sessions
        assert isinstance(data, list), "History should be a list"
        # If sessions exist, verify structure
        if len(data) > 0:
            session = data[0]
            assert "session_id" in session or "id" in session
            assert "user_id" in session
            print(f"✅ Found {len(data)} chat sessions")
        else:
            print("✅ Chat history returned empty list (no sessions yet)")
    
    def test_driver_can_access_own_history(self, driver_session):
        """Driver can access their own chat history"""
        response = driver_session.get(f"{BASE_URL}/api/ai-chat/history")
        assert response.status_code == 200, f"Driver history blocked: {response.text}"
        data = response.json()
        assert isinstance(data, list)
        print(f"✅ Driver chat history accessible: {len(data)} sessions")


class TestAIBrainEndpoint:
    """Test AI Brain query endpoint - POST /api/ai-brain/query"""
    
    def test_ai_brain_query_admin(self, admin_session):
        """Admin can query AI brain"""
        response = admin_session.post(
            f"{BASE_URL}/api/ai-brain/query",
            json={"agent_id": "logistician", "task": "Optimiser les routes de livraison pour Alger"}
        )
        assert response.status_code == 200, f"AI Brain query failed: {response.text}"
        data = response.json()
        assert "response" in data or "result" in data or "answer" in data
        print(f"✅ AI Brain admin query successful")
    
    def test_ai_brain_query_driver(self, driver_session):
        """Driver can query AI brain (no 403)"""
        response = driver_session.post(
            f"{BASE_URL}/api/ai-brain/query",
            json={"agent_id": "logistician", "task": "Comment optimiser mes livraisons aujourd'hui?"}
        )
        # Should NOT be 403 - drivers should have access
        assert response.status_code == 200, f"Driver AI Brain blocked: {response.status_code} - {response.text}"
        print(f"✅ Driver AI Brain query successful")
    
    def test_ai_brain_status(self, admin_session):
        """GET /api/ai-brain/status works"""
        response = admin_session.get(f"{BASE_URL}/api/ai-brain/status")
        assert response.status_code == 200
        data = response.json()
        assert "enabled" in data or "status" in data or "provider" in data
        print(f"✅ AI Brain status: {data}")


class TestDriverEndpoints:
    """Test Driver-specific endpoints"""
    
    def test_driver_tasks_endpoint(self, driver_session):
        """GET /api/driver/tasks works for delivery role"""
        response = driver_session.get(f"{BASE_URL}/api/driver/tasks")
        assert response.status_code == 200, f"Driver tasks failed: {response.text}"
        data = response.json()
        # Should return tasks array
        assert "tasks" in data, "Response should contain 'tasks' field"
        assert isinstance(data["tasks"], list), "Tasks should be a list"
        assert "count" in data, "Response should contain 'count' field"
        print(f"✅ Driver tasks: {data['count']} tasks found")
    
    def test_driver_stats_endpoint(self, driver_session):
        """GET /api/driver/stats works for delivery role"""
        response = driver_session.get(f"{BASE_URL}/api/driver/stats")
        assert response.status_code == 200, f"Driver stats failed: {response.text}"
        data = response.json()
        assert "driver_id" in data or "today" in data
        print(f"✅ Driver stats retrieved successfully")


class TestOrderStatusUpdate:
    """Test Order Status PATCH endpoint with JSON body"""
    
    def test_order_status_accepts_json_body(self, admin_session):
        """PATCH /api/orders/{id}/status accepts JSON body {status: 'delivered'}"""
        # First get an order to update
        orders_resp = admin_session.get(f"{BASE_URL}/api/orders?page=1&limit=1")
        assert orders_resp.status_code == 200
        orders_data = orders_resp.json()
        
        if orders_data.get("orders") and len(orders_data["orders"]) > 0:
            order_id = orders_data["orders"][0]["id"]
            
            # Update status with JSON body
            response = admin_session.patch(
                f"{BASE_URL}/api/orders/{order_id}/status",
                json={"status": "in_transit"}
            )
            assert response.status_code == 200, f"Order status update failed: {response.text}"
            data = response.json()
            assert "message" in data
            print(f"✅ Order {order_id} status updated with JSON body")
        else:
            # No orders to test, but endpoint should still work
            response = admin_session.patch(
                f"{BASE_URL}/api/orders/test-nonexistent/status",
                json={"status": "delivered"}
            )
            # 404 is acceptable for non-existent order
            assert response.status_code in [200, 404], f"Unexpected status: {response.status_code}"
            print("✅ Order status endpoint accepts JSON body (no orders to test)")
    
    def test_order_status_rejects_missing_body(self, admin_session):
        """PATCH /api/orders/{id}/status requires JSON body"""
        response = admin_session.patch(
            f"{BASE_URL}/api/orders/test-id/status"
            # No JSON body
        )
        # Should return 422 (validation error) without body
        assert response.status_code == 422, f"Expected 422, got {response.status_code}"
        print("✅ Order status correctly requires JSON body")


class TestWhatsAppForDriver:
    """Test WhatsApp endpoints work for driver role"""
    
    def test_whatsapp_conversations_driver(self, driver_session):
        """GET /api/whatsapp/conversations works for delivery role"""
        response = driver_session.get(f"{BASE_URL}/api/whatsapp/conversations")
        # Should NOT return 403
        assert response.status_code == 200, f"WhatsApp conversations blocked for driver: {response.status_code} - {response.text}"
        data = response.json()
        assert "conversations" in data or "total" in data or isinstance(data, list)
        print(f"✅ Driver can access WhatsApp conversations")


class TestAuthEndpoints:
    """Basic auth endpoint verification"""
    
    def test_admin_login_works(self):
        """Admin credentials work"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["user"]["role"] == "admin"
        print("✅ Admin login successful")
    
    def test_driver_login_works(self):
        """Driver credentials work"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": DRIVER_EMAIL, "password": DRIVER_PASSWORD}
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["user"]["role"] == "delivery"
        print("✅ Driver login successful")
    
    def test_auth_me_works(self, admin_session):
        """GET /api/auth/me returns user info"""
        response = admin_session.get(f"{BASE_URL}/api/auth/me")
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == ADMIN_EMAIL
        print("✅ Auth me endpoint works")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
