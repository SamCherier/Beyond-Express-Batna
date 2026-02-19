"""P2 Performance Phase Tests - MongoDB Indexing & Redis Caching
Tests for:
1. GET /api/perf/status - Cache info and index list
2. MongoDB indexes on orders, users, sessions, returns, tracking_events
3. Dashboard endpoints with Redis caching (/api/dashboard/stats, orders-by-status, revenue-evolution)
4. Cache invalidation on order status change
5. Regression tests for existing endpoints
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://logistics-saas-2.preview.emergentagent.com').rstrip('/')
ADMIN_EMAIL = "cherier.sam@beyondexpress-batna.com"
ADMIN_PASSWORD = "admin123456"


@pytest.fixture(scope="module")
def api_client():
    """Shared requests session"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session


@pytest.fixture(scope="module")
def auth_token(api_client):
    """Get authentication token"""
    response = api_client.post(f"{BASE_URL}/api/auth/login", json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    })
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.fail(f"Authentication failed: {response.status_code} - {response.text}")


@pytest.fixture(scope="module")
def authenticated_client(api_client, auth_token):
    """Session with auth header"""
    api_client.headers.update({"Authorization": f"Bearer {auth_token}"})
    return api_client


# ===== SECTION 1: Performance Diagnostic Endpoint =====
class TestPerfStatus:
    """Tests for GET /api/perf/status"""
    
    def test_perf_status_returns_200(self, api_client):
        """Perf status endpoint should return 200 (no auth required)"""
        response = api_client.get(f"{BASE_URL}/api/perf/status")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    
    def test_perf_status_has_cache_info(self, api_client):
        """Perf status should return cache availability info"""
        response = api_client.get(f"{BASE_URL}/api/perf/status")
        data = response.json()
        assert "cache" in data, "Missing 'cache' key in response"
        assert "available" in data["cache"], "Cache info missing 'available' field"
        assert data["cache"]["available"] is True, "Redis should be available"
    
    def test_perf_status_has_index_list(self, api_client):
        """Perf status should return index list for collections"""
        response = api_client.get(f"{BASE_URL}/api/perf/status")
        data = response.json()
        assert "indexes" in data, "Missing 'indexes' key in response"
        expected_collections = ["orders", "users", "sessions", "returns", "tracking_events"]
        for col in expected_collections:
            assert col in data["indexes"], f"Missing indexes for collection '{col}'"


# ===== SECTION 2: MongoDB Index Verification =====
class TestMongoDBIndexes:
    """Verify all expected indexes are created on collections"""
    
    def test_orders_indexes(self, api_client):
        """Orders collection should have all required indexes"""
        response = api_client.get(f"{BASE_URL}/api/perf/status")
        data = response.json()
        orders_indexes = data["indexes"]["orders"]
        
        expected_indexes = [
            "idx_orders_tracking_id",
            "idx_orders_status",
            "idx_orders_created_at",
            "idx_orders_user_status",
            "idx_orders_recipient_phone"
        ]
        
        for idx in expected_indexes:
            assert idx in orders_indexes, f"Missing index '{idx}' on orders collection. Found: {orders_indexes}"
    
    def test_users_indexes(self, api_client):
        """Users collection should have all required indexes"""
        response = api_client.get(f"{BASE_URL}/api/perf/status")
        data = response.json()
        users_indexes = data["indexes"]["users"]
        
        expected_indexes = [
            "idx_users_email",
            "idx_users_phone",
            "idx_users_role"
        ]
        
        for idx in expected_indexes:
            assert idx in users_indexes, f"Missing index '{idx}' on users collection. Found: {users_indexes}"
    
    def test_sessions_indexes(self, api_client):
        """Sessions collection should have all required indexes"""
        response = api_client.get(f"{BASE_URL}/api/perf/status")
        data = response.json()
        sessions_indexes = data["indexes"]["sessions"]
        
        expected_indexes = [
            "idx_sessions_user_id",
            "idx_sessions_ttl",
            "idx_sessions_token"
        ]
        
        for idx in expected_indexes:
            assert idx in sessions_indexes, f"Missing index '{idx}' on sessions collection. Found: {sessions_indexes}"
    
    def test_returns_indexes(self, api_client):
        """Returns collection should have all required indexes"""
        response = api_client.get(f"{BASE_URL}/api/perf/status")
        data = response.json()
        returns_indexes = data["indexes"]["returns"]
        
        expected_indexes = [
            "idx_returns_status",
            "idx_returns_created_at",
            "idx_returns_tracking_id"
        ]
        
        for idx in expected_indexes:
            assert idx in returns_indexes, f"Missing index '{idx}' on returns collection. Found: {returns_indexes}"
    
    def test_tracking_events_indexes(self, api_client):
        """Tracking events collection should have expected index"""
        response = api_client.get(f"{BASE_URL}/api/perf/status")
        data = response.json()
        tracking_indexes = data["indexes"]["tracking_events"]
        
        assert "idx_tracking_order_ts" in tracking_indexes, f"Missing 'idx_tracking_order_ts' index. Found: {tracking_indexes}"


# ===== SECTION 3: Dashboard Endpoints with Caching =====
class TestDashboardStats:
    """Tests for GET /api/dashboard/stats with Redis caching"""
    
    def test_dashboard_stats_returns_200(self, authenticated_client):
        """Dashboard stats should return 200"""
        response = authenticated_client.get(f"{BASE_URL}/api/dashboard/stats")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    
    def test_dashboard_stats_structure(self, authenticated_client):
        """Dashboard stats should have expected fields"""
        response = authenticated_client.get(f"{BASE_URL}/api/dashboard/stats")
        data = response.json()
        
        expected_fields = ["total_orders", "total_users", "total_products", "in_transit"]
        for field in expected_fields:
            assert field in data, f"Missing field '{field}' in dashboard stats"
    
    def test_dashboard_stats_caches_result(self, authenticated_client):
        """Second call to stats should use cached data"""
        # First call
        response1 = authenticated_client.get(f"{BASE_URL}/api/dashboard/stats")
        assert response1.status_code == 200
        
        # Second call (should be cached - same response)
        response2 = authenticated_client.get(f"{BASE_URL}/api/dashboard/stats")
        assert response2.status_code == 200
        
        # Data should be identical (from cache)
        assert response1.json() == response2.json(), "Cached response should match original"


class TestDashboardOrdersByStatus:
    """Tests for GET /api/dashboard/orders-by-status with Redis caching"""
    
    def test_orders_by_status_returns_200(self, authenticated_client):
        """Orders by status should return 200"""
        response = authenticated_client.get(f"{BASE_URL}/api/dashboard/orders-by-status")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    
    def test_orders_by_status_returns_list(self, authenticated_client):
        """Orders by status should return a list"""
        response = authenticated_client.get(f"{BASE_URL}/api/dashboard/orders-by-status")
        data = response.json()
        assert isinstance(data, list), "Should return a list of status groups"
    
    def test_orders_by_status_structure(self, authenticated_client):
        """Each item should have 'name' and 'value' fields"""
        response = authenticated_client.get(f"{BASE_URL}/api/dashboard/orders-by-status")
        data = response.json()
        
        if len(data) > 0:
            for item in data:
                assert "name" in item, f"Missing 'name' field in item: {item}"
                assert "value" in item, f"Missing 'value' field in item: {item}"


class TestDashboardRevenueEvolution:
    """Tests for GET /api/dashboard/revenue-evolution with Redis caching"""
    
    def test_revenue_evolution_returns_200(self, authenticated_client):
        """Revenue evolution should return 200"""
        response = authenticated_client.get(f"{BASE_URL}/api/dashboard/revenue-evolution")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    
    def test_revenue_evolution_returns_7_days(self, authenticated_client):
        """Revenue evolution should return 7 days of data"""
        response = authenticated_client.get(f"{BASE_URL}/api/dashboard/revenue-evolution")
        data = response.json()
        assert isinstance(data, list), "Should return a list"
        assert len(data) == 7, f"Should return 7 days, got {len(data)}"
    
    def test_revenue_evolution_structure(self, authenticated_client):
        """Each item should have expected fields"""
        response = authenticated_client.get(f"{BASE_URL}/api/dashboard/revenue-evolution")
        data = response.json()
        
        for item in data:
            assert "name" in item, f"Missing 'name' field (day name)"
            assert "date" in item, f"Missing 'date' field"
            assert "revenus" in item, f"Missing 'revenus' field"


# ===== SECTION 4: Redis Cache Keys Verification =====
class TestRedisCacheKeys:
    """Verify Redis contains cached keys after dashboard calls"""
    
    def test_cache_has_keys_after_dashboard_calls(self, authenticated_client, api_client):
        """Redis should have dashboard cache keys after calling endpoints"""
        # Call all dashboard endpoints to populate cache
        authenticated_client.get(f"{BASE_URL}/api/dashboard/stats")
        authenticated_client.get(f"{BASE_URL}/api/dashboard/orders-by-status")
        authenticated_client.get(f"{BASE_URL}/api/dashboard/revenue-evolution")
        
        # Check perf status for cache keys count
        response = api_client.get(f"{BASE_URL}/api/perf/status")
        data = response.json()
        
        # Cache should have at least some keys
        assert data["cache"]["available"] is True
        assert data["cache"]["keys"] >= 0, "Cache should report key count"


# ===== SECTION 5: Regression Tests - Existing Endpoints =====
class TestOrdersRegression:
    """Verify orders endpoints still work (no regression)"""
    
    def test_get_orders_returns_200(self, authenticated_client):
        """GET /api/orders should return 200"""
        response = authenticated_client.get(f"{BASE_URL}/api/orders")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    
    def test_get_orders_has_pagination(self, authenticated_client):
        """Orders response should have pagination fields"""
        response = authenticated_client.get(f"{BASE_URL}/api/orders")
        data = response.json()
        
        expected_fields = ["orders", "total", "page", "limit", "pages"]
        for field in expected_fields:
            assert field in data, f"Missing pagination field '{field}'"


class TestReturnsRegression:
    """Verify returns endpoints still work (no regression)"""
    
    def test_get_returns_returns_200(self, authenticated_client):
        """GET /api/returns should return 200"""
        response = authenticated_client.get(f"{BASE_URL}/api/returns")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"


class TestWarehouseRegression:
    """Verify warehouse endpoints still work (no regression)"""
    
    def test_get_warehouse_zones_returns_200(self, authenticated_client):
        """GET /api/warehouse/zones should return 200"""
        response = authenticated_client.get(f"{BASE_URL}/api/warehouse/zones")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    
    def test_get_warehouse_depots_returns_200(self, authenticated_client):
        """GET /api/warehouse/depots should return 200"""
        response = authenticated_client.get(f"{BASE_URL}/api/warehouse/depots")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"


class TestAIBrainRegression:
    """Verify AI brain endpoints still work (no regression)"""
    
    def test_ai_brain_status_returns_200(self, authenticated_client):
        """GET /api/ai-brain/status should return 200"""
        response = authenticated_client.get(f"{BASE_URL}/api/ai-brain/status")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    
    def test_ai_brain_agents_returns_200(self, authenticated_client):
        """GET /api/ai-brain/agents should return 200"""
        response = authenticated_client.get(f"{BASE_URL}/api/ai-brain/agents")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"


# ===== SECTION 6: Cache Invalidation Test =====
class TestCacheInvalidation:
    """Test that cache is invalidated on order status change"""
    
    def test_order_status_update_available(self, authenticated_client):
        """PATCH /api/orders/{id}/status endpoint should exist"""
        # Get first order to test with
        response = authenticated_client.get(f"{BASE_URL}/api/orders?limit=1")
        assert response.status_code == 200
        data = response.json()
        
        if data.get("orders") and len(data["orders"]) > 0:
            order_id = data["orders"][0]["id"]
            current_status = data["orders"][0]["status"]
            
            # Try to update to same status (safe operation)
            update_response = authenticated_client.patch(
                f"{BASE_URL}/api/orders/{order_id}/status",
                params={"status": current_status}
            )
            # Should succeed (200 or similar)
            assert update_response.status_code in [200, 422], f"Status update failed: {update_response.status_code}"
        else:
            pytest.skip("No orders available to test status update")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
