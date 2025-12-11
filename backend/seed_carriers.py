"""
Seed Carrier Definitions
Inserts carrier definitions with logos into MongoDB
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone
import os
from uuid import uuid4

# MongoDB connection
mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
db_name = os.environ.get('DB_NAME', 'beyond_express_db')

CARRIERS = [
    {
        "carrier_type": "yalidine",
        "name": "Yalidine",
        "logo_url": "https://yalidine.com/assets/images/logo.png",
        "required_fields": ["api_key", "center_id"],
        "api_endpoints": {
            "test": "https://api.yalidine.app/v1/auth/user",
            "create": "https://api.yalidine.app/v1/parcels"
        },
        "description": "Service de livraison rapide en Algérie",
        "is_active": True
    },
    {
        "carrier_type": "dhd",
        "name": "DHD Express",
        "logo_url": "https://www.dhd.dz/logo.png",
        "required_fields": ["api_key"],
        "api_endpoints": {
            "test": "https://api.dhd.dz/v1/test",
            "create": "https://api.dhd.dz/v1/orders"
        },
        "description": "DHD Express - Livraison nationale",
        "is_active": True
    },
    {
        "carrier_type": "zr_express",
        "name": "ZR Express",
        "logo_url": "https://zrexpress.dz/logo.png",
        "required_fields": ["api_key", "api_token"],
        "api_endpoints": {
            "test": "https://api.zrexpress.dz/v1/auth",
            "create": "https://api.zrexpress.dz/v1/shipments"
        },
        "description": "ZR Express - Solutions logistiques",
        "is_active": True
    },
    {
        "carrier_type": "maystro",
        "name": "Maystro Delivery",
        "logo_url": "https://maystro.dz/logo.png",
        "required_fields": ["api_key"],
        "api_endpoints": {
            "test": "https://api.maystro.dz/v1/ping",
            "create": "https://api.maystro.dz/v1/deliveries"
        },
        "description": "Maystro - Livraison express",
        "is_active": True
    },
    {
        "carrier_type": "guepex",
        "name": "Guepex",
        "logo_url": "https://guepex.dz/logo.png",
        "required_fields": ["api_key", "user_id"],
        "api_endpoints": {
            "test": "https://api.guepex.dz/v1/status",
            "create": "https://api.guepex.dz/v1/parcels"
        },
        "description": "Guepex - Service de colis",
        "is_active": True
    },
    {
        "carrier_type": "nord_ouest",
        "name": "Nord et Ouest",
        "logo_url": "https://nordouest.dz/logo.png",
        "required_fields": ["api_key"],
        "api_endpoints": {
            "test": "https://api.nordouest.dz/v1/test",
            "create": "https://api.nordouest.dz/v1/orders"
        },
        "description": "Nord et Ouest - Couverture nationale",
        "is_active": True
    },
    {
        "carrier_type": "pajo",
        "name": "Pajo Delivery",
        "logo_url": "https://pajo.dz/logo.png",
        "required_fields": ["api_key", "api_secret"],
        "api_endpoints": {
            "test": "https://api.pajo.dz/v1/auth",
            "create": "https://api.pajo.dz/v1/shipments"
        },
        "description": "Pajo - Livraison rapide",
        "is_active": True
    }
]

async def seed_carriers():
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    # Clear existing carriers (optional)
    # await db.carrier_definitions.delete_many({})
    # print("🗑️  Cleared existing carriers")
    
    now = datetime.now(timezone.utc)
    created_count = 0
    updated_count = 0
    
    for carrier in CARRIERS:
        # Check if carrier exists
        existing = await db.carrier_definitions.find_one({"carrier_type": carrier["carrier_type"]})
        
        if existing:
            # Update existing
            await db.carrier_definitions.update_one(
                {"carrier_type": carrier["carrier_type"]},
                {"$set": {
                    **carrier,
                    "updated_at": now
                }}
            )
            updated_count += 1
            print(f"✅ Updated: {carrier['name']}")
        else:
            # Create new
            carrier_doc = {
                "id": str(uuid4()),
                **carrier,
                "created_at": now,
                "updated_at": now
            }
            await db.carrier_definitions.insert_one(carrier_doc)
            created_count += 1
            print(f"✨ Created: {carrier['name']}")
    
    print(f"\n📊 Summary:")
    print(f"   ✨ Created: {created_count}")
    print(f"   ✅ Updated: {updated_count}")
    print(f"   📦 Total: {created_count + updated_count} carriers in database")
    
    # Verify
    total = await db.carrier_definitions.count_documents({})
    print(f"\n✅ Verification: {total} carriers in carrier_definitions collection")
    
    client.close()

if __name__ == "__main__":
    print("🚀 Starting Carrier Definitions seed...")
    asyncio.run(seed_carriers())
    print("✅ Carrier Definitions seed complete!")
