"""MongoDB Index Manager — Performance Optimization
Creates indexes on startup for all critical collections.
"""
import logging
from motor.motor_asyncio import AsyncIOMotorDatabase

logger = logging.getLogger(__name__)

# Index definitions: collection -> list of (keys, options)
INDEX_DEFINITIONS = {
    "orders": [
        ({"tracking_id": 1}, {"unique": True, "sparse": True, "name": "idx_orders_tracking_id"}),
        ({"status": 1}, {"name": "idx_orders_status"}),
        ({"created_at": -1}, {"name": "idx_orders_created_at"}),
        ({"user_id": 1, "status": 1}, {"name": "idx_orders_user_status"}),
        ({"recipient.phone": 1}, {"sparse": True, "name": "idx_orders_recipient_phone"}),
        ({"delivery_partner": 1, "status": 1}, {"sparse": True, "name": "idx_orders_driver_status"}),
    ],
    "users": [
        ({"email": 1}, {"unique": True, "name": "idx_users_email"}),
        ({"phone": 1}, {"sparse": True, "name": "idx_users_phone"}),
        ({"role": 1}, {"name": "idx_users_role"}),
    ],
    "sessions": [
        ({"user_id": 1}, {"name": "idx_sessions_user_id"}),
        ({"expires_at": 1}, {"expireAfterSeconds": 0, "name": "idx_sessions_ttl"}),
        ({"session_token": 1}, {"unique": True, "sparse": True, "name": "idx_sessions_token"}),
    ],
    "returns": [
        ({"status": 1}, {"name": "idx_returns_status"}),
        ({"created_at": -1}, {"name": "idx_returns_created_at"}),
        ({"tracking_id": 1}, {"sparse": True, "name": "idx_returns_tracking_id"}),
    ],
    "tracking_events": [
        ({"order_id": 1, "timestamp": -1}, {"name": "idx_tracking_order_ts"}),
    ],
    "audit_logs": [
        ({"timestamp": -1}, {"name": "idx_audit_ts"}),
        ({"user_id": 1}, {"sparse": True, "name": "idx_audit_user"}),
    ],
    "customers": [
        ({"phone": 1}, {"sparse": True, "name": "idx_customers_phone"}),
    ],
    "warehouse_zones": [
        ({"name": 1}, {"name": "idx_wh_zones_name"}),
    ],
    "warehouse_depots": [
        ({"name": 1}, {"name": "idx_wh_depots_name"}),
    ],
    "whatsapp_messages": [
        ({"timestamp": -1}, {"name": "idx_wa_msgs_ts"}),
    ],
    "ai_usage": [
        ({"timestamp": -1}, {"name": "idx_ai_usage_ts"}),
    ],
}


async def ensure_indexes(db: AsyncIOMotorDatabase):
    """Create all indexes. Safe to call repeatedly (idempotent)."""
    created = 0
    skipped = 0
    for collection_name, indexes in INDEX_DEFINITIONS.items():
        col = db[collection_name]
        existing = set()
        async for idx in col.list_indexes():
            existing.add(idx["name"])

        for keys, options in indexes:
            name = options.get("name", "")
            if name in existing:
                skipped += 1
                continue
            try:
                await col.create_index(list(keys.items()), **options)
                created += 1
            except Exception as e:
                logger.warning(f"Index {name} on {collection_name}: {e}")
                skipped += 1

    logger.info(f"MongoDB indexes: {created} created, {skipped} skipped (already exist)")
    return {"created": created, "skipped": skipped}
