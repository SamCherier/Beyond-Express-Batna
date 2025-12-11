"""
Seed Pricing Table with initial data
Populates shipping costs for all 58 wilayas of Algeria
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone
import os
from uuid import uuid4

# MongoDB connection
mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
db_name = os.environ.get('DB_NAME', 'beyond_express_db')

# Wilayas of Algeria with example pricing
WILAYAS_PRICING = {
    # Format: "Wilaya": {"home": price_home, "desk": price_desk}
    "Alger": {"home": 400, "desk": 350},
    "Oran": {"home": 500, "desk": 450},
    "Constantine": {"home": 500, "desk": 450},
    "Batna": {"home": 450, "desk": 400},
    "Blida": {"home": 450, "desk": 400},
    "Béjaïa": {"home": 500, "desk": 450},
    "Sétif": {"home": 500, "desk": 450},
    "Annaba": {"home": 550, "desk": 500},
    "Tizi Ouzou": {"home": 500, "desk": 450},
    "Tlemcen": {"home": 600, "desk": 550},
    "Biskra": {"home": 500, "desk": 450},
    "Bordj Bou Arreridj": {"home": 500, "desk": 450},
    "Bouira": {"home": 500, "desk": 450},
    "Boumerdès": {"home": 450, "desk": 400},
    "Chlef": {"home": 500, "desk": 450},
    "Djelfa": {"home": 550, "desk": 500},
    "El Oued": {"home": 600, "desk": 550},
    "Guelma": {"home": 550, "desk": 500},
    "Jijel": {"home": 550, "desk": 500},
    "Khenchela": {"home": 550, "desk": 500},
    "Laghouat": {"home": 600, "desk": 550},
    "M'Sila": {"home": 550, "desk": 500},
    "Mascara": {"home": 550, "desk": 500},
    "Médéa": {"home": 500, "desk": 450},
    "Mostaganem": {"home": 550, "desk": 500},
    "Oum El Bouaghi": {"home": 550, "desk": 500},
    "Ouargla": {"home": 700, "desk": 650},
    "Relizane": {"home": 550, "desk": 500},
    "Saïda": {"home": 600, "desk": 550},
    "Skikda": {"home": 550, "desk": 500},
    "Sidi Bel Abbès": {"home": 550, "desk": 500},
    "Souk Ahras": {"home": 600, "desk": 550},
    "Tamanrasset": {"home": 1000, "desk": 950},
    "Tébessa": {"home": 600, "desk": 550},
    "Tiaret": {"home": 600, "desk": 550},
    "Tipaza": {"home": 450, "desk": 400},
    "Tissemsilt": {"home": 600, "desk": 550},
    "El Bayadh": {"home": 700, "desk": 650},
    "Illizi": {"home": 1000, "desk": 950},
    "Khemis Miliana": {"home": 500, "desk": 450},
    "Mila": {"home": 550, "desk": 500},
    "Aïn Defla": {"home": 500, "desk": 450},
    "Naâma": {"home": 700, "desk": 650},
    "Aïn Témouchent": {"home": 550, "desk": 500},
    "Ghardaïa": {"home": 700, "desk": 650},
    "El Tarf": {"home": 600, "desk": 550},
    "Tindouf": {"home": 1000, "desk": 950},
    "El M'Ghair": {"home": 700, "desk": 650},
    "El Menia": {"home": 700, "desk": 650},
    "Ouled Djellal": {"home": 650, "desk": 600},
    "Bordj Badji Mokhtar": {"home": 1200, "desk": 1150},
    "Béni Abbès": {"home": 900, "desk": 850},
    "Timimoun": {"home": 900, "desk": 850},
    "Touggourt": {"home": 650, "desk": 600},
    "Djanet": {"home": 1200, "desk": 1150},
    "In Salah": {"home": 1000, "desk": 950},
    "In Guezzam": {"home": 1200, "desk": 1150},
}

async def seed_pricing():
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    # Clear existing pricing (optional - comment out if you want to keep existing data)
    # await db.pricing_table.delete_many({})
    # print("🗑️  Cleared existing pricing data")
    
    now = datetime.now(timezone.utc)
    documents = []
    
    for wilaya, prices in WILAYAS_PRICING.items():
        # Home delivery
        documents.append({
            "id": str(uuid4()),
            "wilaya": wilaya,
            "delivery_type": "home",
            "price": float(prices["home"]),
            "created_at": now,
            "updated_at": now
        })
        
        # Desk delivery
        documents.append({
            "id": str(uuid4()),
            "wilaya": wilaya,
            "delivery_type": "desk",
            "price": float(prices["desk"]),
            "created_at": now,
            "updated_at": now
        })
    
    # Insert all pricing entries
    if documents:
        # Check which ones already exist
        existing_count = 0
        new_documents = []
        
        for doc in documents:
            existing = await db.pricing_table.find_one({
                "wilaya": doc["wilaya"],
                "delivery_type": doc["delivery_type"]
            })
            if not existing:
                new_documents.append(doc)
            else:
                existing_count += 1
        
        if new_documents:
            await db.pricing_table.insert_many(new_documents)
            print(f"✅ Pricing table seeded: {len(new_documents)} entries created")
        
        if existing_count > 0:
            print(f"ℹ️  Skipped {existing_count} existing entries")
        
        print(f"\n📊 Total pricing entries in database:")
        total = await db.pricing_table.count_documents({})
        print(f"   {total} pricing entries")
        
        # Show sample
        print(f"\n📋 Sample pricing (first 5):")
        samples = await db.pricing_table.find({}, {"_id": 0}).limit(5).to_list(5)
        for sample in samples:
            print(f"   {sample['wilaya']} - {sample['delivery_type']}: {sample['price']} DZD")
    
    client.close()

if __name__ == "__main__":
    print("🚀 Starting Pricing Table seed...")
    asyncio.run(seed_pricing())
    print("✅ Pricing Table seed complete!")
