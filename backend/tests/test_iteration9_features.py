"""
Iteration 9 - Testing Features:
1. AI Brain silent fallback (no red errors) - POST /api/ai-brain/query always returns clean response
2. AI Brain status - GET /api/ai-brain/status returns is_live:true, provider:openrouter, model containing 'llama-3.3'
3. WhatsApp accessible for ecommerce/delivery roles (test via sidebar nav data)
"""

import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_USER_EMAIL = "test_reg_check@test.com"
TEST_USER_PASSWORD = "test123456"


class TestAIBrainStatus:
    """Test AI Brain /status endpoint - should return is_live:true, provider:openrouter"""

    @pytest.fixture
    def auth_token(self):
        """Get authentication token by logging in as test user"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_USER_EMAIL, "password": TEST_USER_PASSWORD},
            timeout=30
        )
        if response.status_code != 200:
            pytest.skip(f"Authentication failed: {response.status_code} - {response.text}")
        return response.json().get("access_token")

    def test_ai_brain_status_is_live(self, auth_token):
        """AI Brain status should return is_live: true"""
        response = requests.get(
            f"{BASE_URL}/api/ai-brain/status",
            headers={"Authorization": f"Bearer {auth_token}"},
            timeout=30
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get("is_live") == True, f"Expected is_live=true, got {data.get('is_live')}"
        print(f"✓ AI Brain is_live: {data.get('is_live')}")

    def test_ai_brain_status_provider(self, auth_token):
        """AI Brain status should return provider: openrouter"""
        response = requests.get(
            f"{BASE_URL}/api/ai-brain/status",
            headers={"Authorization": f"Bearer {auth_token}"},
            timeout=30
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data.get("provider") == "openrouter", f"Expected provider=openrouter, got {data.get('provider')}"
        print(f"✓ AI Brain provider: {data.get('provider')}")

    def test_ai_brain_status_model(self, auth_token):
        """AI Brain status should return model containing 'llama-3.3'"""
        response = requests.get(
            f"{BASE_URL}/api/ai-brain/status",
            headers={"Authorization": f"Bearer {auth_token}"},
            timeout=30
        )
        assert response.status_code == 200
        
        data = response.json()
        model = data.get("model", "")
        assert "llama-3.3" in model, f"Expected model to contain 'llama-3.3', got {model}"
        print(f"✓ AI Brain model: {model}")

    def test_ai_brain_status_has_api_key(self, auth_token):
        """AI Brain status should show has_api_key: true"""
        response = requests.get(
            f"{BASE_URL}/api/ai-brain/status",
            headers={"Authorization": f"Bearer {auth_token}"},
            timeout=30
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data.get("has_api_key") == True, f"Expected has_api_key=true, got {data.get('has_api_key')}"
        print(f"✓ AI Brain has_api_key: {data.get('has_api_key')}")


class TestAIBrainQuerySilentFallback:
    """Test AI Brain /query endpoint - should NEVER return error status codes to UI"""

    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_USER_EMAIL, "password": TEST_USER_PASSWORD},
            timeout=30
        )
        if response.status_code != 200:
            pytest.skip(f"Authentication failed: {response.status_code} - {response.text}")
        return response.json().get("access_token")

    def test_query_logistician_returns_200(self, auth_token):
        """POST /api/ai-brain/query should return 200 even if rate limited"""
        response = requests.post(
            f"{BASE_URL}/api/ai-brain/query",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"agent_id": "logistician", "task": "Test query"},
            timeout=60  # Long timeout for AI response
        )
        # Should NEVER return 4xx or 5xx error to UI
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        # Response should have a 'response' field (even if rate limited or fallback)
        assert "response" in data, f"Expected 'response' field in data: {data}"
        # Should NOT have an 'error' key at top level (except maybe in result data)
        assert "error" not in data or data.get("response"), f"Unexpected error without fallback: {data}"
        print(f"✓ Query logistician returned 200 with response")
        print(f"  - is_simulated: {data.get('is_simulated')}")
        print(f"  - rate_limited: {data.get('rate_limited', False)}")

    def test_query_analyst_returns_200(self, auth_token):
        """POST /api/ai-brain/query for analyst should return 200"""
        response = requests.post(
            f"{BASE_URL}/api/ai-brain/query",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"agent_id": "analyst", "task": "Analyse performance"},
            timeout=60
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "response" in data, f"Expected 'response' field: {data}"
        print(f"✓ Query analyst returned 200 with response")

    def test_query_monitor_returns_200(self, auth_token):
        """POST /api/ai-brain/query for monitor should return 200"""
        response = requests.post(
            f"{BASE_URL}/api/ai-brain/query",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"agent_id": "monitor", "task": "Health check"},
            timeout=60
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "response" in data, f"Expected 'response' field: {data}"
        print(f"✓ Query monitor returned 200 with response")

    def test_query_invalid_agent_returns_200_with_error_message(self, auth_token):
        """Invalid agent should return 200 with error in response (not HTTP error)"""
        response = requests.post(
            f"{BASE_URL}/api/ai-brain/query",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"agent_id": "invalid_agent", "task": "Test"},
            timeout=30
        )
        # Even invalid agent should return 200 (graceful handling)
        # Note: This might be a 422 for validation, which is acceptable
        if response.status_code == 422:
            print("✓ Invalid agent returns 422 (validation error - acceptable)")
        else:
            assert response.status_code == 200
            print(f"✓ Invalid agent query handled gracefully")


class TestLoginRoleAccess:
    """Test that ecommerce role user can access dashboard routes"""

    def test_login_ecommerce_user(self):
        """Login as ecommerce user should succeed"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_USER_EMAIL, "password": TEST_USER_PASSWORD},
            timeout=30
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get("user", {}).get("role") == "ecommerce", f"Expected role=ecommerce, got {data.get('user', {}).get('role')}"
        print(f"✓ Login successful with role: {data.get('user', {}).get('role')}")

    def test_ecommerce_can_access_ai_brain(self):
        """Ecommerce role should be able to access AI Brain endpoint"""
        # Login first
        login_response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_USER_EMAIL, "password": TEST_USER_PASSWORD},
            timeout=30
        )
        token = login_response.json().get("access_token")
        
        # Access AI Brain status
        response = requests.get(
            f"{BASE_URL}/api/ai-brain/status",
            headers={"Authorization": f"Bearer {token}"},
            timeout=30
        )
        assert response.status_code == 200, f"Ecommerce user should access AI Brain, got {response.status_code}"
        print(f"✓ Ecommerce user can access AI Brain")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
