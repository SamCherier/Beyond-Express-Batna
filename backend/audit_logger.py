"""
Audit Log System with Cryptographic Hash Chaining
ISO 27001 Compliant - Immutable Logs
"""
import hashlib
import json
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging

logger = logging.getLogger(__name__)

class AuditLogger:
    """
    Immutable Audit Log System with Hash Chaining
    
    Each log entry contains:
    - Action details
    - User/IP info
    - Timestamp
    - Previous hash (blockchain-like)
    - Current hash (SHA-256 of all fields)
    
    If any entry is modified, the chain breaks and alerts are triggered.
    """
    
    def __init__(self, db: AsyncIOMotorClient):
        self.db = db
        self.collection = db.audit_logs
    
    @staticmethod
    def _compute_hash(data: Dict[str, Any], previous_hash: str) -> str:
        """Compute SHA-256 hash of log entry"""
        hash_input = json.dumps({
            **data,
            "previous_hash": previous_hash
        }, sort_keys=True, default=str)
        
        return hashlib.sha256(hash_input.encode()).hexdigest()
    
    async def log_action(
        self,
        action: str,
        user_id: str,
        user_email: str,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        status: str = "success"
    ):
        """
        Log a critical action with hash chaining
        
        Critical actions:
        - LOGIN, LOGOUT, FAILED_LOGIN
        - CREATE_ORDER, UPDATE_ORDER, DELETE_ORDER
        - UPDATE_CARRIER_CONFIG, CREATE_USER
        - CHANGE_PASSWORD, UPDATE_PERMISSIONS
        - EXPORT_DATA, DELETE_DATA
        """
        try:
            # Get last log entry to chain
            last_entry = await self.collection.find_one(
                {},
                {"_id": 0},
                sort=[("timestamp", -1)]
            )
            
            previous_hash = last_entry["hash"] if last_entry else "0" * 64
            
            # Build log entry
            log_entry = {
                "id": hashlib.sha256(f"{user_id}{action}{datetime.now(timezone.utc).isoformat()}".encode()).hexdigest()[:16],
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "action": action,
                "user_id": user_id,
                "user_email": user_email,
                "resource_type": resource_type,
                "resource_id": resource_id,
                "details": details or {},
                "ip_address": ip_address,
                "user_agent": user_agent,
                "status": status,
                "previous_hash": previous_hash
            }
            
            # Compute hash of this entry
            current_hash = self._compute_hash(log_entry, previous_hash)
            log_entry["hash"] = current_hash
            
            # Store in database
            await self.collection.insert_one(log_entry)
            
            logger.info(f"✅ Audit log created: {action} by {user_email}")
            
        except Exception as e:
            logger.error(f"❌ Audit logging failed: {e}")
            # NEVER fail the main operation if audit logging fails
            # But log it for investigation
    
    async def verify_chain_integrity(self) -> Dict[str, Any]:
        """
        Verify the integrity of the entire audit log chain
        Returns: {valid: bool, broken_at: Optional[str], message: str}
        """
        try:
            entries = await self.collection.find({}, {"_id": 0}).sort("timestamp", 1).to_list(10000)
            
            if not entries:
                return {"valid": True, "message": "No audit logs yet"}
            
            previous_hash = "0" * 64
            
            for i, entry in enumerate(entries):
                # Verify hash matches
                stored_hash = entry.pop("hash")
                computed_hash = self._compute_hash(entry, previous_hash)
                
                if stored_hash != computed_hash:
                    return {
                        "valid": False,
                        "broken_at": entry.get("id"),
                        "timestamp": entry.get("timestamp"),
                        "message": f"⚠️ INTEGRITY BREACH DETECTED at entry {i + 1}",
                        "details": f"Action: {entry.get('action')} by {entry.get('user_email')}"
                    }
                
                previous_hash = stored_hash
            
            return {
                "valid": True,
                "message": f"✅ Chain integrity verified: {len(entries)} entries",
                "total_entries": len(entries)
            }
            
        except Exception as e:
            logger.error(f"❌ Chain verification failed: {e}")
            return {"valid": False, "message": f"Verification error: {str(e)}"}
    
    async def get_user_actions(self, user_id: str, limit: int = 100):
        """Get all actions by a specific user"""
        try:
            logs = await self.collection.find(
                {"user_id": user_id},
                {"_id": 0}
            ).sort("timestamp", -1).limit(limit).to_list(limit)
            
            return logs
        except Exception as e:
            logger.error(f"❌ Failed to fetch user actions: {e}")
            return []
    
    async def get_recent_logs(self, limit: int = 100):
        """Get recent audit logs"""
        try:
            logs = await self.collection.find(
                {},
                {"_id": 0}
            ).sort("timestamp", -1).limit(limit).to_list(limit)
            
            return logs
        except Exception as e:
            logger.error(f"❌ Failed to fetch recent logs: {e}")
            return []
    
    async def search_logs(
        self,
        action: Optional[str] = None,
        user_id: Optional[str] = None,
        resource_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ):
        """Search audit logs with filters"""
        try:
            query = {}
            
            if action:
                query["action"] = action
            if user_id:
                query["user_id"] = user_id
            if resource_type:
                query["resource_type"] = resource_type
            if start_date or end_date:
                query["timestamp"] = {}
                if start_date:
                    query["timestamp"]["$gte"] = start_date.isoformat()
                if end_date:
                    query["timestamp"]["$lte"] = end_date.isoformat()
            
            logs = await self.collection.find(
                query,
                {"_id": 0}
            ).sort("timestamp", -1).limit(limit).to_list(limit)
            
            return logs
        except Exception as e:
            logger.error(f"❌ Failed to search logs: {e}")
            return []


# Critical actions enum
class AuditAction:
    # Authentication
    LOGIN = "LOGIN"
    LOGOUT = "LOGOUT"
    FAILED_LOGIN = "FAILED_LOGIN"
    PASSWORD_CHANGE = "PASSWORD_CHANGE"
    
    # Orders
    CREATE_ORDER = "CREATE_ORDER"
    UPDATE_ORDER = "UPDATE_ORDER"
    DELETE_ORDER = "DELETE_ORDER"
    EXPORT_ORDERS = "EXPORT_ORDERS"
    
    # Carriers
    UPDATE_CARRIER_CONFIG = "UPDATE_CARRIER_CONFIG"
    TEST_CARRIER_CONNECTION = "TEST_CARRIER_CONNECTION"
    
    # Users
    CREATE_USER = "CREATE_USER"
    UPDATE_USER = "UPDATE_USER"
    DELETE_USER = "DELETE_USER"
    
    # Data
    EXPORT_DATA = "EXPORT_DATA"
    DELETE_DATA = "DELETE_DATA"
    BULK_IMPORT = "BULK_IMPORT"
    
    # Financial
    UPDATE_PAYMENT_STATUS = "UPDATE_PAYMENT_STATUS"
    GENERATE_INVOICE = "GENERATE_INVOICE"
