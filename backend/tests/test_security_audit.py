"""
Security Audit + Feature Tests - Iteration 7
Tests for:
- Authentication (register, login)
- AI Brain endpoints (status, query with simulation fallback)
- WhatsApp Meta status (no credentials exposed)
- Dashboard endpoints (stats, orders-by-status, revenue-evolution)
- Security: No API keys exposed in responses
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
API_URL = f"{BASE_URL}/api"

# Test credentials
ADMIN_EMAIL = "cherier.sam@beyondexpress-batna.com"
ADMIN_PASSWORD = "admin123456"

# Test user for register tests
TEST_USER_EMAIL = f"test_user_{uuid.uuid4().hex[:8]}@test.com"
TEST_USER_PASSWORD = "testpassword123"


@pytest.fixture(scope="module")
def session():
    """Shared requests session"""
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


@pytest.fixture(scope="module")
def admin_token(session):
    """Get admin authentication token"""
    response = session.post(f"{API_URL}/auth/login", json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    })
    assert response.status_code == 200, f"Admin login failed: {response.text}"
    data = response.json()
    return data.get("token") or data.get("access_token")


@pytest.fixture(scope="module")
def auth_session(session, admin_token):
    """Session with auth header"""
    session.headers.update({"Authorization": f"Bearer {admin_token}"})
    return session


class TestAuthentication:
    """Test authentication endpoints - register and login"""

    def test_register_new_user(self, session):
        """POST /api/auth/register - creates new user and returns valid response"""
        response = session.post(f"{API_URL}/auth/register", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD,
            "name": "Test User",
            "role": "ecommerce"
        })
        assert response.status_code in [200, 201], f"Register failed: {response.status_code} - {response.text}"
        data = response.json()
        # Verify user data is returned - could be nested in 'user' or direct
        user_data = data.get("user", data)
        assert "email" in user_data, f"Missing email in response: {data}"
        assert "id" in user_data, f"Missing id in response: {data}"
        print(f"Register successful: {user_data.get('email')}")

    def test_login_with_registered_user(self, session):
        """POST /api/auth/login - works with newly registered user"""
        response = session.post(f"{API_URL}/auth/login", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.status_code} - {response.text}"
        data = response.json()
        assert "token" in data or "access_token" in data, f"No token in response: {data}"
        print(f"Login successful for {TEST_USER_EMAIL}")

    def test_login_admin(self, session):
        """POST /api/auth/login - admin login works"""
        response = session.post(f"{API_URL}/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Admin login failed: {response.status_code}"
        data = response.json()
        assert "token" in data or "access_token" in data
        print("Admin login successful")


class TestAIBrainEndpoints:
    """Test AI Brain endpoints"""

    def test_ai_brain_status(self, auth_session):
        """GET /api/ai-brain/status - returns correct state"""
        response = auth_session.get(f"{API_URL}/ai-brain/status")
        assert response.status_code == 200, f"AI Brain status failed: {response.status_code}"
        data = response.json()
        
        # Verify expected fields
        assert "has_api_key" in data, f"Missing has_api_key field: {data}"
        assert "is_live" in data, f"Missing is_live field: {data}"
        assert "model" in data, f"Missing model field: {data}"
        assert "provider" in data, f"Missing provider field: {data}"
        assert "agents" in data, f"Missing agents field: {data}"
        
        # Security: ensure no actual API key is exposed
        response_text = response.text.lower()
        assert "gsk_" not in response_text, "API key leaked in response!"
        assert "eaa" not in response_text, "Access token leaked in response!"
        
        print(f"AI Brain status: has_key={data['has_api_key']}, is_live={data['is_live']}, provider={data['provider']}")

    def test_ai_brain_query(self, auth_session):
        """POST /api/ai-brain/query - returns response (simulation fallback if needed)"""
        response = auth_session.post(f"{API_URL}/ai-brain/query", json={
            "agent_id": "logistician",
            "task": "Analyse la capacité stock"
        })
        assert response.status_code == 200, f"AI Brain query failed: {response.status_code} - {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "response" in data, f"Missing response field: {data}"
        assert "agent" in data, f"Missing agent field: {data}"
        assert "model" in data, f"Missing model field: {data}"
        
        # Either live or simulated should work
        print(f"AI Brain query: agent={data['agent']}, simulated={data.get('is_simulated', 'N/A')}")

    def test_ai_brain_query_analyst(self, auth_session):
        """POST /api/ai-brain/query - test analyst agent"""
        response = auth_session.post(f"{API_URL}/ai-brain/query", json={
            "agent_id": "analyst",
            "task": "Génère un rapport de performance mensuel"
        })
        assert response.status_code == 200, f"Analyst query failed: {response.status_code}"
        data = response.json()
        assert "response" in data
        print(f"Analyst agent response received, simulated={data.get('is_simulated', 'N/A')}")

    def test_ai_brain_query_monitor(self, auth_session):
        """POST /api/ai-brain/query - test monitor agent"""
        response = auth_session.post(f"{API_URL}/ai-brain/query", json={
            "agent_id": "monitor",
            "task": "Vérifie la santé du système"
        })
        assert response.status_code == 200, f"Monitor query failed: {response.status_code}"
        data = response.json()
        assert "response" in data
        print(f"Monitor agent response received, simulated={data.get('is_simulated', 'N/A')}")


class TestWhatsAppMetaEndpoints:
    """Test WhatsApp Meta endpoints - verify no credentials exposed"""

    def test_whatsapp_status(self, auth_session):
        """GET /api/whatsapp-meta/status - returns config state without exposing credentials"""
        response = auth_session.get(f"{API_URL}/whatsapp-meta/status")
        assert response.status_code == 200, f"WhatsApp status failed: {response.status_code}"
        data = response.json()
        
        # Verify expected status fields
        assert "configured" in data, f"Missing configured field: {data}"
        assert "enabled" in data, f"Missing enabled field: {data}"
        assert "phone_id_set" in data, f"Missing phone_id_set field: {data}"
        assert "token_set" in data, f"Missing token_set field: {data}"
        
        # Security: ensure no actual credentials exposed
        response_text = response.text
        assert "EAA" not in response_text, "Access token leaked in response!"
        # Phone ID should not be fully exposed
        assert len(response_text) < 5000, "Response too large, possible data leak"
        
        print(f"WhatsApp status: configured={data['configured']}, phone_id_set={data['phone_id_set']}, token_set={data['token_set']}")

    def test_whatsapp_templates(self, auth_session):
        """GET /api/whatsapp-meta/templates - returns available templates"""
        response = auth_session.get(f"{API_URL}/whatsapp-meta/templates")
        assert response.status_code == 200, f"Templates failed: {response.status_code}"
        data = response.json()
        assert "templates" in data, f"Missing templates field: {data}"
        print(f"WhatsApp templates count: {len(data['templates'])}")

    def test_whatsapp_logs(self, auth_session):
        """GET /api/whatsapp-meta/logs - returns send logs"""
        response = auth_session.get(f"{API_URL}/whatsapp-meta/logs")
        assert response.status_code == 200, f"Logs failed: {response.status_code}"
        data = response.json()
        assert "logs" in data, f"Missing logs field: {data}"
        print(f"WhatsApp logs count: {len(data['logs'])}")


class TestDashboardEndpoints:
    """Test dashboard endpoints"""

    def test_dashboard_stats(self, auth_session):
        """GET /api/dashboard/stats - returns dashboard statistics"""
        response = auth_session.get(f"{API_URL}/dashboard/stats")
        assert response.status_code == 200, f"Dashboard stats failed: {response.status_code}"
        data = response.json()
        # Verify some expected fields exist
        assert isinstance(data, dict), f"Expected dict response: {data}"
        print(f"Dashboard stats keys: {list(data.keys())[:5]}")

    def test_dashboard_orders_by_status(self, auth_session):
        """GET /api/dashboard/orders-by-status - returns order breakdown"""
        response = auth_session.get(f"{API_URL}/dashboard/orders-by-status")
        assert response.status_code == 200, f"Orders by status failed: {response.status_code}"
        data = response.json()
        assert isinstance(data, (dict, list)), f"Expected dict/list response: {data}"
        print(f"Orders by status response type: {type(data).__name__}")

    def test_dashboard_revenue_evolution(self, auth_session):
        """GET /api/dashboard/revenue-evolution - returns revenue data"""
        response = auth_session.get(f"{API_URL}/dashboard/revenue-evolution")
        assert response.status_code == 200, f"Revenue evolution failed: {response.status_code}"
        data = response.json()
        assert isinstance(data, (dict, list)), f"Expected dict/list response: {data}"
        print(f"Revenue evolution response type: {type(data).__name__}")


class TestSecurityNoAPIKeysExposed:
    """Security tests - verify no API keys in any response"""

    def test_no_groq_key_in_ai_brain_status(self, auth_session):
        """Verify GROQ_API_KEY not exposed in AI brain status"""
        response = auth_session.get(f"{API_URL}/ai-brain/status")
        assert response.status_code == 200
        response_text = response.text.lower()
        assert "gsk_" not in response_text, "Groq API key pattern found in response!"
        print("Security check passed: No Groq key in AI brain status")

    def test_no_whatsapp_token_in_status(self, auth_session):
        """Verify WHATSAPP_ACCESS_TOKEN not exposed in status"""
        response = auth_session.get(f"{API_URL}/whatsapp-meta/status")
        assert response.status_code == 200
        response_text = response.text
        # EAA prefix is common for Facebook/Meta access tokens
        assert "EAA" not in response_text, "WhatsApp access token pattern found!"
        print("Security check passed: No WhatsApp token in status")

    def test_no_credentials_in_ai_query_response(self, auth_session):
        """Verify no credentials leak in AI query response"""
        response = auth_session.post(f"{API_URL}/ai-brain/query", json={
            "agent_id": "logistician",
            "task": "Test query"
        })
        assert response.status_code == 200
        response_text = response.text.lower()
        assert "gsk_" not in response_text
        assert "eaa" not in response_text.upper()
        print("Security check passed: No credentials in AI query response")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
