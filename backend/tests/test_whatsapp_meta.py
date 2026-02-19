"""
WhatsApp Meta Cloud API Backend Tests
Testing zero-cost direct Meta integration (no Twilio)
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

@pytest.fixture
def api_client():
    """Shared requests session"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session


class TestWhatsAppMetaStatus:
    """Tests for GET /api/whatsapp-meta/status"""
    
    def test_status_returns_200(self, api_client):
        response = api_client.get(f"{BASE_URL}/api/whatsapp-meta/status")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    
    def test_status_returns_configured_field(self, api_client):
        response = api_client.get(f"{BASE_URL}/api/whatsapp-meta/status")
        data = response.json()
        assert "configured" in data, "Missing 'configured' field"
        assert isinstance(data["configured"], bool)
    
    def test_status_returns_enabled_field(self, api_client):
        response = api_client.get(f"{BASE_URL}/api/whatsapp-meta/status")
        data = response.json()
        assert "enabled" in data, "Missing 'enabled' field"
        assert isinstance(data["enabled"], bool)
    
    def test_status_returns_triggers(self, api_client):
        response = api_client.get(f"{BASE_URL}/api/whatsapp-meta/status")
        data = response.json()
        assert "triggers" in data, "Missing 'triggers' field"
        triggers = data["triggers"]
        assert "OUT_FOR_DELIVERY" in triggers, "Missing OUT_FOR_DELIVERY trigger"
        assert "DELIVERED" in triggers, "Missing DELIVERED trigger"
        assert triggers["OUT_FOR_DELIVERY"] == "delivery_update"
        assert triggers["DELIVERED"] == "delivery_confirmed"
    
    def test_status_returns_templates(self, api_client):
        response = api_client.get(f"{BASE_URL}/api/whatsapp-meta/status")
        data = response.json()
        assert "templates" in data, "Missing 'templates' field"
        templates = data["templates"]
        assert len(templates) == 3, f"Expected 3 templates, got {len(templates)}"


class TestWhatsAppMetaTemplates:
    """Tests for GET /api/whatsapp-meta/templates"""
    
    def test_templates_returns_200(self, api_client):
        response = api_client.get(f"{BASE_URL}/api/whatsapp-meta/templates")
        assert response.status_code == 200
    
    def test_templates_returns_3_templates(self, api_client):
        response = api_client.get(f"{BASE_URL}/api/whatsapp-meta/templates")
        data = response.json()
        assert "templates" in data
        templates = data["templates"]
        assert len(templates) == 3, f"Expected 3 templates, got {len(templates)}"
    
    def test_templates_contains_hello_world(self, api_client):
        response = api_client.get(f"{BASE_URL}/api/whatsapp-meta/templates")
        data = response.json()
        template_names = [t["name"] for t in data["templates"]]
        assert "hello_world" in template_names
    
    def test_templates_contains_delivery_update(self, api_client):
        response = api_client.get(f"{BASE_URL}/api/whatsapp-meta/templates")
        data = response.json()
        template_names = [t["name"] for t in data["templates"]]
        assert "delivery_update" in template_names
    
    def test_templates_contains_delivery_confirmed(self, api_client):
        response = api_client.get(f"{BASE_URL}/api/whatsapp-meta/templates")
        data = response.json()
        template_names = [t["name"] for t in data["templates"]]
        assert "delivery_confirmed" in template_names
    
    def test_templates_have_required_fields(self, api_client):
        response = api_client.get(f"{BASE_URL}/api/whatsapp-meta/templates")
        data = response.json()
        for tpl in data["templates"]:
            assert "name" in tpl, "Template missing 'name'"
            assert "language" in tpl, "Template missing 'language'"
            assert "category" in tpl, "Template missing 'category'"
            assert "label" in tpl, "Template missing 'label'"
            assert "description" in tpl, "Template missing 'description'"


class TestWhatsAppMetaConfigure:
    """Tests for POST /api/whatsapp-meta/configure"""
    
    def test_configure_returns_200(self, api_client):
        payload = {"phone_id": "TEST_123456789", "access_token": "TEST_token_abc123"}
        response = api_client.post(f"{BASE_URL}/api/whatsapp-meta/configure", json=payload)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    
    def test_configure_returns_success(self, api_client):
        payload = {"phone_id": "TEST_789012345", "access_token": "TEST_token_xyz456"}
        response = api_client.post(f"{BASE_URL}/api/whatsapp-meta/configure", json=payload)
        data = response.json()
        assert data.get("success") is True
        assert "message" in data
    
    def test_configure_updates_status(self, api_client):
        # First configure
        payload = {"phone_id": "TEST_update_status", "access_token": "TEST_token_update"}
        api_client.post(f"{BASE_URL}/api/whatsapp-meta/configure", json=payload)
        
        # Verify status updated
        status_response = api_client.get(f"{BASE_URL}/api/whatsapp-meta/status")
        status_data = status_response.json()
        assert status_data["configured"] is True
        assert status_data["phone_id_set"] is True
        assert status_data["token_set"] is True


class TestWhatsAppMetaLogs:
    """Tests for GET /api/whatsapp-meta/logs"""
    
    def test_logs_returns_200(self, api_client):
        response = api_client.get(f"{BASE_URL}/api/whatsapp-meta/logs")
        assert response.status_code == 200
    
    def test_logs_returns_logs_array(self, api_client):
        response = api_client.get(f"{BASE_URL}/api/whatsapp-meta/logs")
        data = response.json()
        assert "logs" in data, "Missing 'logs' field"
        assert isinstance(data["logs"], list)


class TestWhatsAppMetaTriggers:
    """Tests for GET /api/whatsapp-meta/triggers"""
    
    def test_triggers_returns_200(self, api_client):
        response = api_client.get(f"{BASE_URL}/api/whatsapp-meta/triggers")
        assert response.status_code == 200
    
    def test_triggers_returns_expected_structure(self, api_client):
        response = api_client.get(f"{BASE_URL}/api/whatsapp-meta/triggers")
        data = response.json()
        assert "triggers" in data
        assert "active" in data
        assert "OUT_FOR_DELIVERY" in data["triggers"]
        assert "DELIVERED" in data["triggers"]
