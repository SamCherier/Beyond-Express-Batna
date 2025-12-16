import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from datetime import datetime, timezone
from passlib.context import CryptContext

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def restore_admin():
    """Restore admin account with specific credentials"""
    
    # Get MongoDB connection
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
    db_name = os.environ.get('DB_NAME', 'logistics_db')
    
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    print("🔧 Connexion à MongoDB...")
    
    # Admin credentials
    admin_email = "cherier.sam@beyondexpress-batna.com"
    admin_password = "admin123456"
    
    # Delete existing account if exists
    existing = await db.users.find_one({"email": admin_email})
    if existing:
        await db.users.delete_one({"email": admin_email})
        print(f"✅ Ancien compte supprimé: {admin_email}")
    
    # Hash password
    hashed_password = pwd_context.hash(admin_password)
    
    # Create new admin account
    admin_user = {
        "id": "admin_restored_" + datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S"),
        "email": admin_email,
        "password": hashed_password,
        "name": "Sam Cherier",
        "role": "admin",
        "subscription_plan": "BUSINESS",
        "subscription_status": "active",
        "subscription_id": "business_lifetime",
        "ai_message_limit": 999999,
        "ai_messages_used": 0,
        "permissions": {
            "whatsapp_notifications": True,
            "whatsapp_auto_confirmation": True,
            "bulk_import": True,
            "api_access": True,
            "financial_management": True,
            "driver_management": True,
            "advanced_analytics": True,
            "custom_integrations": True,
            "priority_support": True
        },
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "is_active": True,
        "email_verified": True
    }
    
    # Insert into database
    result = await db.users.insert_one(admin_user)
    
    print("\n" + "="*70)
    print("✅ COMPTE ADMIN RESTAURÉ AVEC SUCCÈS !")
    print("="*70)
    print(f"📧 Email: {admin_email}")
    print(f"🔑 Password: {admin_password}")
    print(f"👤 Role: admin")
    print(f"💎 Plan: BUSINESS")
    print(f"🆔 ID: {admin_user['id']}")
    print("="*70)
    print("\n🎉 Vous pouvez maintenant vous connecter !")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(restore_admin())
