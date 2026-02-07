"""
Backend Tests for Iteration 3: White-label, Logout/Session, Warehouse MongoDB
Tests: logout endpoints, logout-all, warehouse zones/depots from MongoDB
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "cherier.sam@beyondexpress-batna.com"
TEST_PASSWORD = "admin123456"


class TestAuth:
    """Authentication and session management tests"""

    def test_login_success(self):
        """Test login returns access_token and user"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        
        data = response.json()
        assert "access_token" in data, "Missing access_token"
        assert "user" in data, "Missing user object"
        assert data["user"]["email"] == TEST_EMAIL
        assert data["user"]["role"] == "admin"
        print(f"✅ Login successful, user: {data['user']['name']}")

    def test_login_invalid_credentials(self):
        """Test login fails with wrong password"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": "wrongpassword123"
        })
        assert response.status_code == 401, "Should return 401 for invalid credentials"
        print("✅ Invalid credentials correctly rejected")


class TestLogoutEndpoints:
    """New logout endpoints from iteration 3"""
    
    @pytest.fixture
    def auth_token(self):
        """Get fresh auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["access_token"]

    def test_logout_endpoint_exists(self, auth_token):
        """Test POST /api/auth/logout works"""
        response = requests.post(
            f"{BASE_URL}/api/auth/logout",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200, f"Logout failed: {response.text}"
        
        data = response.json()
        assert "message" in data
        assert "Logged out" in data["message"]
        print(f"✅ Logout successful: {data['message']}")

    def test_logout_all_devices_endpoint(self, auth_token):
        """Test POST /api/auth/logout-all works"""
        response = requests.post(
            f"{BASE_URL}/api/auth/logout-all",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200, f"Logout-all failed: {response.text}"
        
        data = response.json()
        assert "message" in data
        assert "sessions" in data["message"].lower() or "logged out" in data["message"].lower()
        print(f"✅ Logout-all successful: {data['message']}")

    def test_logout_without_auth(self):
        """Test logout works even without auth (graceful)"""
        response = requests.post(f"{BASE_URL}/api/auth/logout")
        # Should succeed (graceful logout) not 401
        assert response.status_code == 200, f"Logout without auth should be graceful: {response.text}"
        print("✅ Logout without auth is graceful")


class TestWarehouseAPI:
    """Warehouse zones/depots from MongoDB - iteration 3 feature"""
    
    @pytest.fixture
    def auth_token(self):
        """Get fresh auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["access_token"]

    def test_get_warehouse_zones(self, auth_token):
        """Test GET /api/warehouse/zones returns zones from MongoDB"""
        response = requests.get(
            f"{BASE_URL}/api/warehouse/zones",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200, f"Get zones failed: {response.text}"
        
        zones = response.json()
        assert isinstance(zones, list), "Zones should be a list"
        assert len(zones) >= 4, f"Expected at least 4 zones, got {len(zones)}"
        
        # Validate zone structure
        for zone in zones:
            assert "id" in zone, "Zone missing id"
            assert "name" in zone, "Zone missing name"
            assert "capacity" in zone, "Zone missing capacity"
            assert "used" in zone, "Zone missing used"
            assert "zone_type" in zone, "Zone missing zone_type"
        
        # Check expected zones exist
        zone_names = [z["name"] for z in zones]
        expected_names = ["Zone Froide A1", "Zone Sèche A2", "Zone Fragile B1", "Zone Standard B2"]
        for name in expected_names:
            assert name in zone_names, f"Missing expected zone: {name}"
        
        print(f"✅ Got {len(zones)} zones from MongoDB: {zone_names}")

    def test_get_warehouse_depots(self, auth_token):
        """Test GET /api/warehouse/depots returns depots from MongoDB"""
        response = requests.get(
            f"{BASE_URL}/api/warehouse/depots",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200, f"Get depots failed: {response.text}"
        
        depots = response.json()
        assert isinstance(depots, list), "Depots should be a list"
        assert len(depots) >= 4, f"Expected at least 4 depots, got {len(depots)}"
        
        # Validate depot structure
        for depot in depots:
            assert "id" in depot, "Depot missing id"
            assert "city" in depot, "Depot missing city"
            assert "capacity_pct" in depot, "Depot missing capacity_pct"
        
        # Check expected cities
        cities = [d["city"] for d in depots]
        expected_cities = ["Alger", "Oran", "Constantine", "Batna"]
        for city in expected_cities:
            assert city in cities, f"Missing expected depot: {city}"
        
        print(f"✅ Got {len(depots)} depots from MongoDB: {cities}")

    def test_get_warehouse_stats(self, auth_token):
        """Test GET /api/warehouse/stats returns real capacity data"""
        response = requests.get(
            f"{BASE_URL}/api/warehouse/stats",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200, f"Get stats failed: {response.text}"
        
        stats = response.json()
        assert "total_capacity" in stats, "Missing total_capacity"
        assert "total_used" in stats, "Missing total_used"
        assert "percentage" in stats, "Missing percentage"
        assert "zones_count" in stats, "Missing zones_count"
        
        # Validate values are realistic
        assert stats["total_capacity"] > 0, "Capacity should be positive"
        assert stats["total_used"] >= 0, "Used should be non-negative"
        assert 0 <= stats["percentage"] <= 100, "Percentage should be 0-100"
        assert stats["zones_count"] >= 4, "Should have at least 4 zones"
        
        print(f"✅ Warehouse stats: {stats['total_used']}/{stats['total_capacity']} ({stats['percentage']}%)")

    def test_warehouse_zones_require_auth(self):
        """Test warehouse endpoints require authentication"""
        response = requests.get(f"{BASE_URL}/api/warehouse/zones")
        assert response.status_code == 401, "Zones should require auth"
        print("✅ Warehouse zones correctly require auth")

    def test_warehouse_depots_require_auth(self):
        """Test depots endpoint requires authentication"""
        response = requests.get(f"{BASE_URL}/api/warehouse/depots")
        assert response.status_code == 401, "Depots should require auth"
        print("✅ Warehouse depots correctly require auth")


class TestDashboardStats:
    """Dashboard endpoints"""
    
    @pytest.fixture
    def auth_token(self):
        """Get fresh auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["access_token"]

    def test_dashboard_stats(self, auth_token):
        """Test GET /api/dashboard/stats"""
        response = requests.get(
            f"{BASE_URL}/api/dashboard/stats",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200, f"Dashboard stats failed: {response.text}"
        
        data = response.json()
        assert "total_orders" in data
        assert "total_users" in data
        assert "total_products" in data
        assert "in_transit" in data
        print(f"✅ Dashboard stats: orders={data['total_orders']}, users={data['total_users']}")

    def test_orders_by_status(self, auth_token):
        """Test GET /api/dashboard/orders-by-status"""
        response = requests.get(
            f"{BASE_URL}/api/dashboard/orders-by-status",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200, f"Orders by status failed: {response.text}"
        
        data = response.json()
        assert isinstance(data, list)
        print(f"✅ Orders by status: {len(data)} status groups")


class TestReturnsAPI:
    """Returns/RMA module tests"""
    
    @pytest.fixture
    def auth_token(self):
        """Get fresh auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["access_token"]

    def test_get_returns(self, auth_token):
        """Test GET /api/returns"""
        response = requests.get(
            f"{BASE_URL}/api/returns",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200, f"Get returns failed: {response.text}"
        
        data = response.json()
        assert isinstance(data, list) or "returns" in data
        print(f"✅ Returns API working")

    def test_get_returns_stats(self, auth_token):
        """Test GET /api/returns/stats"""
        response = requests.get(
            f"{BASE_URL}/api/returns/stats",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200, f"Get returns stats failed: {response.text}"
        
        data = response.json()
        assert "total" in data or "pending" in data
        print(f"✅ Returns stats: {data}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
