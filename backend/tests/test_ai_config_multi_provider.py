"""
Multi-Provider AI Configuration Tests
Tests for:
- GET /api/ai-config/providers - List all providers with models and status
- POST /api/ai-config/providers/save-key - Save API key for a provider
- POST /api/ai-config/providers/test - Test provider connection
- GET /api/ai-config/agent-matrix - Get agent assignments
- POST /api/ai-config/agent-matrix - Update agent assignment
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token for admin user."""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": "final_admin@qa.com",
        "password": "Final123!"
    })
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip("Authentication failed")


@pytest.fixture
def api_client(auth_token):
    """Authenticated API client."""
    session = requests.Session()
    session.headers.update({
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    })
    return session


class TestGetProviders:
    """Test GET /api/ai-config/providers endpoint."""
    
    def test_returns_4_providers(self, api_client):
        """Verify endpoint returns exactly 4 providers."""
        response = api_client.get(f"{BASE_URL}/api/ai-config/providers")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 4
        provider_ids = [p["id"] for p in data]
        assert "openrouter" in provider_ids
        assert "groq" in provider_ids
        assert "together" in provider_ids
        assert "moonshot" in provider_ids
    
    def test_provider_has_required_fields(self, api_client):
        """Verify each provider has required fields."""
        response = api_client.get(f"{BASE_URL}/api/ai-config/providers")
        data = response.json()
        for provider in data:
            assert "id" in provider
            assert "name" in provider
            assert "models" in provider
            assert "has_key" in provider
            assert "key_masked" in provider
            assert isinstance(provider["models"], list)
            assert len(provider["models"]) > 0
    
    def test_openrouter_has_key(self, api_client):
        """Verify OpenRouter has a saved key."""
        response = api_client.get(f"{BASE_URL}/api/ai-config/providers")
        data = response.json()
        openrouter = next((p for p in data if p["id"] == "openrouter"), None)
        assert openrouter is not None
        assert openrouter["has_key"] is True
        assert openrouter["key_masked"].endswith("ad49")
    
    def test_models_have_id_and_label(self, api_client):
        """Verify each model has id and label fields."""
        response = api_client.get(f"{BASE_URL}/api/ai-config/providers")
        data = response.json()
        for provider in data:
            for model in provider["models"]:
                assert "id" in model
                assert "label" in model
    
    def test_unauthenticated_access_denied(self):
        """Verify endpoint requires authentication."""
        response = requests.get(f"{BASE_URL}/api/ai-config/providers")
        assert response.status_code == 401


class TestSaveProviderKey:
    """Test POST /api/ai-config/providers/save-key endpoint."""
    
    def test_save_key_success(self, api_client):
        """Verify API key can be saved successfully."""
        response = api_client.post(f"{BASE_URL}/api/ai-config/providers/save-key", json={
            "provider": "together",
            "api_key": "TEST_key_1234567890abcdefghij"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "sauvegardée" in data["message"]
    
    def test_save_key_verify_persistence(self, api_client):
        """Verify saved key appears in providers list."""
        # First save a key
        api_client.post(f"{BASE_URL}/api/ai-config/providers/save-key", json={
            "provider": "together",
            "api_key": "TEST_key_abcdefghijklmnop"
        })
        
        # Verify it's saved
        response = api_client.get(f"{BASE_URL}/api/ai-config/providers")
        data = response.json()
        together = next((p for p in data if p["id"] == "together"), None)
        assert together is not None
        assert together["has_key"] is True
        assert together["key_masked"].endswith("mnop")
    
    def test_save_key_invalid_provider(self, api_client):
        """Verify error for invalid provider."""
        response = api_client.post(f"{BASE_URL}/api/ai-config/providers/save-key", json={
            "provider": "invalid_provider",
            "api_key": "test-key"
        })
        assert response.status_code == 400
        assert "inconnu" in response.json()["detail"].lower()
    
    def test_save_key_unauthenticated(self):
        """Verify endpoint requires authentication."""
        response = requests.post(f"{BASE_URL}/api/ai-config/providers/save-key", json={
            "provider": "groq",
            "api_key": "test"
        })
        assert response.status_code == 401


class TestProviderConnectionTest:
    """Test POST /api/ai-config/providers/test endpoint."""
    
    def test_openrouter_graceful_error(self, api_client):
        """Verify OpenRouter returns graceful error (rate limit / 402)."""
        response = api_client.post(f"{BASE_URL}/api/ai-config/providers/test", json={
            "provider": "openrouter"
        })
        # Should not crash - returns 200 with error message
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "error" in data
        # Should have HTTP error code in message
        assert "HTTP" in data["error"] or "error" in data["error"].lower()
    
    def test_provider_no_key_graceful_error(self, api_client):
        """Verify graceful error when no key configured."""
        response = api_client.post(f"{BASE_URL}/api/ai-config/providers/test", json={
            "provider": "moonshot"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "clé" in data["error"].lower() or "configurée" in data["error"].lower()
    
    def test_invalid_provider_error(self, api_client):
        """Verify error for invalid provider."""
        response = api_client.post(f"{BASE_URL}/api/ai-config/providers/test", json={
            "provider": "invalid"
        })
        assert response.status_code == 400
    
    def test_unauthenticated_test(self):
        """Verify endpoint requires authentication."""
        response = requests.post(f"{BASE_URL}/api/ai-config/providers/test", json={
            "provider": "openrouter"
        })
        assert response.status_code == 401


class TestGetAgentMatrix:
    """Test GET /api/ai-config/agent-matrix endpoint."""
    
    def test_returns_3_agents(self, api_client):
        """Verify matrix returns all 3 agents."""
        response = api_client.get(f"{BASE_URL}/api/ai-config/agent-matrix")
        assert response.status_code == 200
        data = response.json()
        assert "logistician" in data
        assert "analyst" in data
        assert "monitor" in data
    
    def test_agent_has_provider_and_model(self, api_client):
        """Verify each agent has provider and model assigned."""
        response = api_client.get(f"{BASE_URL}/api/ai-config/agent-matrix")
        data = response.json()
        for agent_id, config in data.items():
            assert "provider" in config
            assert "model" in config
            assert config["provider"] in ["openrouter", "groq", "together", "moonshot"]
    
    def test_unauthenticated_access_denied(self):
        """Verify endpoint requires authentication."""
        response = requests.get(f"{BASE_URL}/api/ai-config/agent-matrix")
        assert response.status_code == 401


class TestUpdateAgentMatrix:
    """Test POST /api/ai-config/agent-matrix endpoint."""
    
    def test_update_agent_success(self, api_client):
        """Verify agent assignment can be updated."""
        response = api_client.post(f"{BASE_URL}/api/ai-config/agent-matrix", json={
            "agent_id": "analyst",
            "provider": "openrouter",
            "model": "qwen/qwen3-4b:free"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["agent"] == "analyst"
        assert data["provider"] == "openrouter"
        assert data["model"] == "qwen/qwen3-4b:free"
    
    def test_update_persists_in_get(self, api_client):
        """Verify update persists when fetched."""
        # Update
        api_client.post(f"{BASE_URL}/api/ai-config/agent-matrix", json={
            "agent_id": "monitor",
            "provider": "openrouter",
            "model": "deepseek/deepseek-r1-0528:free"
        })
        
        # Verify
        response = api_client.get(f"{BASE_URL}/api/ai-config/agent-matrix")
        data = response.json()
        assert data["monitor"]["model"] == "deepseek/deepseek-r1-0528:free"
    
    def test_update_invalid_provider(self, api_client):
        """Verify error for invalid provider."""
        response = api_client.post(f"{BASE_URL}/api/ai-config/agent-matrix", json={
            "agent_id": "analyst",
            "provider": "invalid_provider",
            "model": "some-model"
        })
        assert response.status_code == 400
    
    def test_unauthenticated_update(self):
        """Verify endpoint requires authentication."""
        response = requests.post(f"{BASE_URL}/api/ai-config/agent-matrix", json={
            "agent_id": "analyst",
            "provider": "openrouter",
            "model": "test"
        })
        assert response.status_code == 401


@pytest.fixture(scope="module", autouse=True)
def cleanup_test_data(auth_token):
    """Cleanup after tests - reset to default state."""
    yield
    # Reset agent matrix to defaults
    session = requests.Session()
    session.headers.update({
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    })
    default_model = "meta-llama/llama-3.3-70b-instruct:free"
    for agent in ["logistician", "analyst", "monitor"]:
        session.post(f"{BASE_URL}/api/ai-config/agent-matrix", json={
            "agent_id": agent,
            "provider": "openrouter",
            "model": default_model
        })
