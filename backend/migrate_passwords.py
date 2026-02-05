"""
Migration script: Bcrypt → Argon2id
Rehashes all user passwords to military-grade security standard
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from auth_utils import hash_password
import os
from dotenv import load_dotenv
from pathlib import Path

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Known passwords for demo accounts (for migration)
DEMO_ACCOUNTS = {
    "cherier.sam@beyondexpress-batna.com": "admin123456",
    "driver@beyond.com": "driver123",
    "merchant@beyond.com": "merchant123"
}

async def migrate_passwords():
    """Migrate all demo account passwords from bcrypt to Argon2id"""
    mongo_url = os.environ['MONGO_URL']
    client = AsyncIOMotorClient(mongo_url)
    db = client[os.environ['DB_NAME']]
    
    print("🔐 Starting password migration: Bcrypt → Argon2id...")
    print("")
    
    migrated = 0
    
    for email, password in DEMO_ACCOUNTS.items():
        try:
            user = await db.users.find_one({"email": email}, {"_id": 0})
            
            if not user:
                print(f"⚠️  User not found: {email}")
                continue
            
            # Hash with Argon2id
            new_hash = hash_password(password)
            
            # Update in database
            await db.users.update_one(
                {"email": email},
                {"$set": {"password": new_hash}}
            )
            
            print(f"✅ Migrated: {email}")
            print(f"   Old hash (bcrypt): {user['password'][:60]}...")
            print(f"   New hash (argon2): {new_hash[:60]}...")
            print("")
            migrated += 1
            
        except Exception as e:
            print(f"❌ Error migrating {email}: {e}")
            print("")
    
    print(f"🎉 Migration complete: {migrated}/{len(DEMO_ACCOUNTS)} accounts migrated")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(migrate_passwords())
