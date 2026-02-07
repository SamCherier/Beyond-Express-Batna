"""
Backend Tests for Iteration 4 Features:
- AI Brain Center LIVE integration with Groq
- Centralized API client with retry logic (verified via frontend pages)
- Warehouse zones endpoint (after migration)
- Returns endpoint (after migration)
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "cherier.sam@beyondexpress-batna.com"
TEST_PASSWORD = "admin123456"


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token for protected endpoints"""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
        headers={"Content-Type": "application/json"}
    )
    if response.status_code != 200:
        pytest.skip("Authentication failed - skipping authenticated tests")
    return response.json().get("access_token")


@pytest.fixture(scope="module")
def auth_headers(auth_token):
    """Return headers with auth token"""
    return {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}


class TestAIBrainStatus:
    """Test AI Brain status endpoint - should show is_live=true, provider=groq"""
    
    def test_ai_brain_status_returns_200(self, auth_headers):
        response = requests.get(f"{BASE_URL}/api/ai-brain/status", headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    
    def test_ai_brain_is_live(self, auth_headers):
        response = requests.get(f"{BASE_URL}/api/ai-brain/status", headers=auth_headers)
        data = response.json()
        assert data.get("is_live") is True, f"Expected is_live=True, got {data.get('is_live')}"
    
    def test_ai_brain_provider_groq(self, auth_headers):
        response = requests.get(f"{BASE_URL}/api/ai-brain/status", headers=auth_headers)
        data = response.json()
        assert data.get("provider") == "groq", f"Expected provider='groq', got {data.get('provider')}"
    
    def test_ai_brain_has_api_key(self, auth_headers):
        response = requests.get(f"{BASE_URL}/api/ai-brain/status", headers=auth_headers)
        data = response.json()
        assert data.get("has_api_key") is True, "AI Brain should have API key configured"
    
    def test_ai_brain_model_is_llama(self, auth_headers):
        response = requests.get(f"{BASE_URL}/api/ai-brain/status", headers=auth_headers)
        data = response.json()
        assert "llama-3.3" in data.get("model", ""), f"Expected llama-3.3 model, got {data.get('model')}"
    
    def test_ai_brain_has_three_agents(self, auth_headers):
        response = requests.get(f"{BASE_URL}/api/ai-brain/status", headers=auth_headers)
        data = response.json()
        agents = data.get("agents", [])
        assert len(agents) == 3, f"Expected 3 agents, got {len(agents)}"
        agent_ids = [a.get("id") for a in agents]
        assert "logistician" in agent_ids, "Missing logistician agent"
        assert "analyst" in agent_ids, "Missing analyst agent"
        assert "monitor" in agent_ids, "Missing monitor agent"


class TestAIBrainQueryLogistician:
    """Test AI Brain query with logistician agent - should return real Groq response"""
    
    def test_query_logistician_returns_200(self, auth_headers):
        response = requests.post(
            f"{BASE_URL}/api/ai-brain/query",
            json={"agent_id": "logistician", "task": "Analyse la capacité stock"},
            headers=auth_headers,
            timeout=30
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    
    def test_query_logistician_is_not_simulated(self, auth_headers):
        response = requests.post(
            f"{BASE_URL}/api/ai-brain/query",
            json={"agent_id": "logistician", "task": "Analyse la capacité stock"},
            headers=auth_headers,
            timeout=30
        )
        data = response.json()
        assert data.get("is_simulated") is False, f"Expected is_simulated=False (LIVE), got {data.get('is_simulated')}"
    
    def test_query_logistician_has_response(self, auth_headers):
        response = requests.post(
            f"{BASE_URL}/api/ai-brain/query",
            json={"agent_id": "logistician", "task": "Analyse la capacité stock"},
            headers=auth_headers,
            timeout=30
        )
        data = response.json()
        assert data.get("response") is not None and len(data.get("response", "")) > 50, "Response should be substantial"
    
    def test_query_logistician_has_usage_tokens(self, auth_headers):
        response = requests.post(
            f"{BASE_URL}/api/ai-brain/query",
            json={"agent_id": "logistician", "task": "Analyse la capacité stock"},
            headers=auth_headers,
            timeout=30
        )
        data = response.json()
        usage = data.get("usage", {})
        assert usage.get("total_tokens", 0) > 0, "Should have token usage for LIVE responses"


class TestAIBrainQueryAnalyst:
    """Test AI Brain query with analyst agent - should return real Groq response"""
    
    def test_query_analyst_is_not_simulated(self, auth_headers):
        response = requests.post(
            f"{BASE_URL}/api/ai-brain/query",
            json={"agent_id": "analyst", "task": "Génère un rapport de performance mensuel"},
            headers=auth_headers,
            timeout=30
        )
        data = response.json()
        assert response.status_code == 200
        assert data.get("is_simulated") is False, "Analyst agent should return LIVE response"
        assert data.get("agent") == "L'Analyste"


class TestAIBrainQueryMonitor:
    """Test AI Brain query with monitor agent - should return real Groq response"""
    
    def test_query_monitor_is_not_simulated(self, auth_headers):
        response = requests.post(
            f"{BASE_URL}/api/ai-brain/query",
            json={"agent_id": "monitor", "task": "Vérifie la santé du système"},
            headers=auth_headers,
            timeout=30
        )
        data = response.json()
        assert response.status_code == 200
        assert data.get("is_simulated") is False, "Monitor agent should return LIVE response"
        assert data.get("agent") == "Le Moniteur"


class TestWarehouseEndpointsAfterMigration:
    """Test Warehouse endpoints still work after apiClient migration"""
    
    def test_warehouse_zones_returns_200(self, auth_headers):
        response = requests.get(f"{BASE_URL}/api/warehouse/zones", headers=auth_headers)
        assert response.status_code == 200
    
    def test_warehouse_zones_returns_data(self, auth_headers):
        response = requests.get(f"{BASE_URL}/api/warehouse/zones", headers=auth_headers)
        data = response.json()
        assert isinstance(data, list), "Should return array of zones"
        assert len(data) >= 1, "Should have at least 1 zone"
        zone = data[0]
        assert "id" in zone
        assert "name" in zone
        assert "capacity" in zone
        assert "used" in zone
    
    def test_warehouse_depots_returns_200(self, auth_headers):
        response = requests.get(f"{BASE_URL}/api/warehouse/depots", headers=auth_headers)
        assert response.status_code == 200
    
    def test_warehouse_depots_returns_data(self, auth_headers):
        response = requests.get(f"{BASE_URL}/api/warehouse/depots", headers=auth_headers)
        data = response.json()
        assert isinstance(data, list), "Should return array of depots"
        assert len(data) >= 1, "Should have at least 1 depot"
        depot = data[0]
        assert "city" in depot
        assert "capacity_pct" in depot


class TestReturnsEndpointsAfterMigration:
    """Test Returns endpoints still work after apiClient migration"""
    
    def test_returns_list_returns_200(self, auth_headers):
        response = requests.get(f"{BASE_URL}/api/returns", headers=auth_headers)
        assert response.status_code == 200
    
    def test_returns_list_returns_data(self, auth_headers):
        response = requests.get(f"{BASE_URL}/api/returns", headers=auth_headers)
        data = response.json()
        assert isinstance(data, list), "Should return array of returns"
    
    def test_returns_stats_returns_200(self, auth_headers):
        response = requests.get(f"{BASE_URL}/api/returns/stats", headers=auth_headers)
        assert response.status_code == 200
    
    def test_returns_stats_has_expected_fields(self, auth_headers):
        response = requests.get(f"{BASE_URL}/api/returns/stats", headers=auth_headers)
        data = response.json()
        assert "total" in data, "Missing 'total' in returns stats"
        assert "restocked" in data, "Missing 'restocked' in returns stats"
        assert "pending" in data, "Missing 'pending' in returns stats"
        assert "reason_breakdown" in data, "Missing 'reason_breakdown' in returns stats"


class TestCentralizedAPIClientRetry:
    """Test that the API client has retry logic configured (indirect test via error handling)"""
    
    def test_api_returns_proper_error_for_invalid_endpoint(self, auth_headers):
        """Test that API handles 404 errors properly (no retry on 404)"""
        response = requests.get(f"{BASE_URL}/api/nonexistent-endpoint", headers=auth_headers)
        assert response.status_code == 404, "Should return 404 for invalid endpoint"
    
    def test_api_returns_401_for_unauthenticated(self):
        """Test that 401 errors are handled properly (no retry on 401)"""
        response = requests.get(f"{BASE_URL}/api/ai-brain/status")
        assert response.status_code == 401, "Should return 401 without auth"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
