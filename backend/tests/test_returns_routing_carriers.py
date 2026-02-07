"""
Backend Tests for Returns/RMA, Smart Routing, and Carriers APIs
Testing Phase 1-3 features of Logistics OS (Beyond Express)
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://beyond-express-next.preview.emergentagent.com')

# Test credentials
ADMIN_EMAIL = "cherier.sam@beyondexpress-batna.com"
ADMIN_PASSWORD = "admin123456"

class TestAuth:
    """Authentication tests"""
    
    def test_admin_login_success(self):
        """Test admin login with valid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data, "No access_token in response"
        assert "user" in data, "No user in response"
        assert data["user"]["email"] == ADMIN_EMAIL
        assert data["user"]["role"] == "admin"
    
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "wrong@email.com",
            "password": "wrongpassword"
        })
        assert response.status_code == 401
    
    def test_auth_me_requires_token(self):
        """Test /auth/me requires authentication"""
        response = requests.get(f"{BASE_URL}/api/auth/me")
        assert response.status_code == 401


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token for admin user"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    })
    if response.status_code != 200:
        pytest.skip("Authentication failed")
    return response.json()["access_token"]


@pytest.fixture(scope="module")
def auth_headers(auth_token):
    """Auth headers for authenticated requests"""
    return {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    }


class TestReturnsAPI:
    """Tests for Returns/RMA module - CRUD operations"""
    
    def test_get_returns_list(self, auth_headers):
        """GET /api/returns - Get list of returns"""
        response = requests.get(f"{BASE_URL}/api/returns", headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
    
    def test_get_returns_stats(self, auth_headers):
        """GET /api/returns/stats - Get stats with reason_breakdown"""
        response = requests.get(f"{BASE_URL}/api/returns/stats", headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "total" in data, "Stats should have total"
        assert "pending" in data, "Stats should have pending"
        assert "restocked" in data, "Stats should have restocked"
        assert "discarded" in data, "Stats should have discarded"
        assert "reason_breakdown" in data, "Stats should have reason_breakdown"
    
    def test_create_return_auto_decision(self, auth_headers):
        """POST /api/returns - Create return with auto-decision logic"""
        test_tracking = f"TEST-BEX-{uuid.uuid4().hex[:8].upper()}"
        payload = {
            "tracking_id": test_tracking,
            "customer_name": "Test Customer",
            "wilaya": "Alger",
            "reason": "absent",  # Should auto-decide: restock
            "notes": "Test return"
        }
        response = requests.post(f"{BASE_URL}/api/returns", headers=auth_headers, json=payload)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        # Validate auto-decision fields
        assert data["tracking_id"] == test_tracking
        assert data["status"] == "pending"
        assert data["decision"] == "restock", "Absent reason should auto-decide restock"
        assert data["decision_label"] == "Remise en Stock"
        assert "id" in data
        
        return data["id"]
    
    def test_create_return_damaged_discards(self, auth_headers):
        """POST /api/returns - Damaged items should auto-decide discard"""
        test_tracking = f"TEST-BEX-{uuid.uuid4().hex[:8].upper()}"
        payload = {
            "tracking_id": test_tracking,
            "customer_name": "Test Damaged",
            "wilaya": "Oran",
            "reason": "damaged",
            "notes": "Product arrived damaged"
        }
        response = requests.post(f"{BASE_URL}/api/returns", headers=auth_headers, json=payload)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        assert data["decision"] == "discard", "Damaged reason should auto-decide discard"
        assert data["decision_label"] == "Mise au Rebut"
    
    def test_update_return_status(self, auth_headers):
        """PATCH /api/returns/{id} - Update return status"""
        # First create a return
        test_tracking = f"TEST-BEX-{uuid.uuid4().hex[:8].upper()}"
        create_response = requests.post(f"{BASE_URL}/api/returns", headers=auth_headers, json={
            "tracking_id": test_tracking,
            "customer_name": "Test Update",
            "wilaya": "Constantine",
            "reason": "customer_request"
        })
        assert create_response.status_code == 200
        return_id = create_response.json()["id"]
        
        # Update status to restocked
        update_response = requests.patch(
            f"{BASE_URL}/api/returns/{return_id}",
            headers=auth_headers,
            json={"status": "restocked"}
        )
        assert update_response.status_code == 200, f"Update failed: {update_response.text}"
        updated = update_response.json()
        assert updated["status"] == "restocked"
    
    def test_returns_requires_auth(self):
        """Test that returns API requires authentication"""
        response = requests.get(f"{BASE_URL}/api/returns")
        assert response.status_code == 401


class TestSmartRoutingAPI:
    """Tests for Smart Circuit Routing API with Haversine algorithm"""
    
    def test_get_wilayas_with_coords(self):
        """GET /api/routing/wilayas - Get wilayas with coordinates"""
        response = requests.get(f"{BASE_URL}/api/routing/wilayas")
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 40, "Should have 40+ Algerian wilayas"
        
        # Check data structure
        first = data[0]
        assert "name" in first
        assert "lat" in first
        assert "lng" in first
        assert "is_south" in first
    
    def test_optimize_route(self):
        """POST /api/routing/optimize - Optimize delivery route"""
        payload = {
            "driver_location": {
                "lat": 35.56,
                "lng": 6.17,
                "wilaya": "Batna"
            },
            "deliveries": [
                {
                    "id": "del-1",
                    "customer_name": "Client Alger",
                    "address": "123 Rue Test",
                    "wilaya": "Alger"
                },
                {
                    "id": "del-2",
                    "customer_name": "Client Setif",
                    "address": "456 Ave Test",
                    "wilaya": "Setif"
                },
                {
                    "id": "del-3",
                    "customer_name": "Client Batna",
                    "address": "789 Blvd Test",
                    "wilaya": "Batna"
                }
            ]
        }
        response = requests.post(f"{BASE_URL}/api/routing/optimize", json=payload)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        # Validate response structure
        assert "optimized_route" in data
        assert "total_distance_km" in data
        assert "total_estimated_minutes" in data
        assert "stops_count" in data
        assert data["stops_count"] == 3
        
        # Batna delivery should be first (same wilaya priority)
        route = data["optimized_route"]
        assert len(route) == 3
        assert route[0]["same_wilaya"] == True, "First stop should be same wilaya (Batna)"
    
    def test_optimize_empty_deliveries(self):
        """POST /api/routing/optimize - Handle empty deliveries"""
        payload = {
            "driver_location": {
                "lat": 36.75,
                "lng": 3.04,
                "wilaya": "Alger"
            },
            "deliveries": []
        }
        response = requests.post(f"{BASE_URL}/api/routing/optimize", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["stops_count"] == 0
        assert data["total_distance_km"] == 0


class TestCarriersAPI:
    """Tests for Carriers API - Now requires authentication"""
    
    def test_carriers_requires_auth(self):
        """GET /api/carriers - Should require authentication"""
        response = requests.get(f"{BASE_URL}/api/carriers")
        assert response.status_code == 401, "Carriers should require authentication now"
    
    def test_get_carriers_authenticated(self, auth_headers):
        """GET /api/carriers - Get carriers list with auth"""
        response = requests.get(f"{BASE_URL}/api/carriers", headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert isinstance(data, list)
        
        # Check carrier structure
        if len(data) > 0:
            carrier = data[0]
            assert "carrier_type" in carrier
            assert "name" in carrier
    
    def test_get_preconfigured_carriers(self):
        """GET /api/carriers/preconfigured - Public endpoint"""
        response = requests.get(f"{BASE_URL}/api/carriers/preconfigured")
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "carriers" in data


class TestDashboardStats:
    """Tests for dashboard statistics endpoints"""
    
    def test_dashboard_stats(self, auth_headers):
        """GET /api/dashboard/stats - Get dashboard stats"""
        response = requests.get(f"{BASE_URL}/api/dashboard/stats", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "total_orders" in data
        assert "total_users" in data
        assert "in_transit" in data
    
    def test_orders_by_status(self, auth_headers):
        """GET /api/dashboard/orders-by-status"""
        response = requests.get(f"{BASE_URL}/api/dashboard/orders-by-status", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_revenue_evolution(self, auth_headers):
        """GET /api/dashboard/revenue-evolution"""
        response = requests.get(f"{BASE_URL}/api/dashboard/revenue-evolution", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_top_wilayas(self, auth_headers):
        """GET /api/dashboard/top-wilayas"""
        response = requests.get(f"{BASE_URL}/api/dashboard/top-wilayas", headers=auth_headers)
        assert response.status_code == 200


class TestPublicEndpoints:
    """Tests for public endpoints (no auth required)"""
    
    def test_public_tracking_invalid_id(self):
        """GET /api/public/track/{tracking_id} - Invalid tracking"""
        response = requests.get(f"{BASE_URL}/api/public/track/INVALID-123")
        assert response.status_code == 404


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
