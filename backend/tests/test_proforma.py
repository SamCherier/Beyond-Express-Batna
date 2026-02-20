"""
Proforma Invoice API Tests
Tests the proforma generation endpoint for Beyond Express logistics platform.
Features: Invoice generation with auto-increment reference (BEY-XXXX), totals calculation.
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://cargo-command-18.preview.emergentagent.com')


class TestProformaAPI:
    """Test proforma invoice generation API"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={
                "email": "final_admin@qa.com",
                "password": "Final123!"
            }
        )
        assert response.status_code == 200, f"Login failed: {response.text}"
        return response.json()["access_token"]
    
    @pytest.fixture(scope="class")
    def auth_headers(self, auth_token):
        """Get headers with auth token"""
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {auth_token}"
        }
    
    def test_proforma_generate_success(self, auth_headers):
        """Test successful proforma generation with valid order IDs"""
        order_ids = [
            "9cd313ff-5c5c-424f-b868-3499a7e6918d",
            "7b0c93bb-80cb-40b5-883b-60e9c176f529"
        ]
        
        response = requests.post(
            f"{BASE_URL}/api/invoices/proforma/generate",
            headers=auth_headers,
            json={
                "order_ids": order_ids,
                "lieu": "Batna"
            }
        )
        
        assert response.status_code == 200, f"Proforma generation failed: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "id" in data, "Response must have id"
        assert "reference" in data, "Response must have reference"
        assert "date" in data, "Response must have date"
        assert "lieu" in data, "Response must have lieu"
        assert "client" in data, "Response must have client"
        assert "items" in data, "Response must have items"
        assert "totals" in data, "Response must have totals"
        assert "order_count" in data, "Response must have order_count"
        
        # Verify reference format BEY-XXXX
        ref = data["reference"]
        assert ref.startswith("BEY-"), f"Reference must start with BEY-, got {ref}"
        assert len(ref) == 8, f"Reference must be 8 chars (BEY-XXXX), got {ref}"
        
        # Verify order count matches
        assert data["order_count"] == len(order_ids), "Order count mismatch"
        assert len(data["items"]) == len(order_ids), "Items count mismatch"
        
        print(f"✅ Proforma generated: {ref}")
    
    def test_proforma_reference_auto_increment(self, auth_headers):
        """Test that proforma reference auto-increments"""
        order_ids = ["9cd313ff-5c5c-424f-b868-3499a7e6918d"]
        
        # Generate first proforma
        response1 = requests.post(
            f"{BASE_URL}/api/invoices/proforma/generate",
            headers=auth_headers,
            json={"order_ids": order_ids, "lieu": "Alger"}
        )
        assert response1.status_code == 200
        ref1 = response1.json()["reference"]
        num1 = int(ref1.split("-")[1])
        
        # Generate second proforma
        response2 = requests.post(
            f"{BASE_URL}/api/invoices/proforma/generate",
            headers=auth_headers,
            json={"order_ids": order_ids, "lieu": "Oran"}
        )
        assert response2.status_code == 200
        ref2 = response2.json()["reference"]
        num2 = int(ref2.split("-")[1])
        
        # Verify increment
        assert num2 == num1 + 1, f"Reference should increment: {ref1} -> {ref2}"
        print(f"✅ Reference auto-increment working: {ref1} -> {ref2}")
    
    def test_proforma_totals_calculation(self, auth_headers):
        """Test totals calculation: prestation = 15% of shipping"""
        order_ids = [
            "9cd313ff-5c5c-424f-b868-3499a7e6918d",
            "7b0c93bb-80cb-40b5-883b-60e9c176f529"
        ]
        
        response = requests.post(
            f"{BASE_URL}/api/invoices/proforma/generate",
            headers=auth_headers,
            json={"order_ids": order_ids, "lieu": "Batna"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify totals structure
        totals = data["totals"]
        assert "montant" in totals, "Totals must have montant"
        assert "livraison" in totals, "Totals must have livraison"
        assert "prestation" in totals, "Totals must have prestation"
        assert "net" in totals, "Totals must have net"
        
        # Verify prestation is 15% of livraison
        expected_prestation = round(totals["livraison"] * 0.15, 2)
        assert totals["prestation"] == expected_prestation, \
            f"Prestation should be 15% of livraison: {expected_prestation}, got {totals['prestation']}"
        
        # Verify net = montant - livraison - prestation
        expected_net = round(totals["montant"] - totals["livraison"] - totals["prestation"], 2)
        assert abs(totals["net"] - expected_net) < 0.1, \
            f"Net calculation incorrect: expected {expected_net}, got {totals['net']}"
        
        print(f"✅ Totals calculation correct: montant={totals['montant']}, livraison={totals['livraison']}, prestation={totals['prestation']}, net={totals['net']}")
    
    def test_proforma_item_fields(self, auth_headers):
        """Test that each item has all required 11 fields"""
        order_ids = ["9cd313ff-5c5c-424f-b868-3499a7e6918d"]
        
        response = requests.post(
            f"{BASE_URL}/api/invoices/proforma/generate",
            headers=auth_headers,
            json={"order_ids": order_ids, "lieu": "Batna"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        required_fields = [
            "reference", "article", "destinataire", "telephone",
            "wilaya", "commune", "poids", "montant",
            "tarif_livraison", "tarif_prestation", "net"
        ]
        
        for item in data["items"]:
            for field in required_fields:
                assert field in item, f"Item missing field: {field}"
        
        print(f"✅ All 11 item fields present: {required_fields}")
    
    def test_proforma_no_orders_error(self, auth_headers):
        """Test error when no order_ids provided"""
        response = requests.post(
            f"{BASE_URL}/api/invoices/proforma/generate",
            headers=auth_headers,
            json={"order_ids": [], "lieu": "Batna"}
        )
        
        assert response.status_code == 400, "Empty order_ids should return 400"
        print("✅ Empty order_ids returns 400")
    
    def test_proforma_invalid_orders_error(self, auth_headers):
        """Test error when invalid order_ids provided"""
        response = requests.post(
            f"{BASE_URL}/api/invoices/proforma/generate",
            headers=auth_headers,
            json={
                "order_ids": ["nonexistent-order-id-12345"],
                "lieu": "Batna"
            }
        )
        
        assert response.status_code == 404, "Invalid order_ids should return 404"
        print("✅ Invalid order_ids returns 404")
    
    def test_proforma_unauthenticated(self):
        """Test that unauthenticated requests are rejected"""
        response = requests.post(
            f"{BASE_URL}/api/invoices/proforma/generate",
            json={
                "order_ids": ["9cd313ff-5c5c-424f-b868-3499a7e6918d"],
                "lieu": "Batna"
            }
        )
        
        assert response.status_code == 401, "Unauthenticated should return 401"
        print("✅ Unauthenticated returns 401")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
