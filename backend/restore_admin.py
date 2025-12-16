import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
import sys
from datetime import datetime, timezone

# Add backend to path to import auth_utils
sys.path.insert(0, '/app/backend')
from auth_utils import hash_password

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
    
    # Delete ALL existing accounts with this email (clean slate)
    delete_result = await db.users.delete_many({"email": admin_email})
    if delete_result.deleted_count > 0:
        print(f"✅ {delete_result.deleted_count} ancien(s) compte(s) supprimé(s): {admin_email}")
    
    # Hash password using the SAME function as the backend
    print(f"🔐 Hashing du mot de passe...")
    hashed_password = hash_password(admin_password)
    print(f"✅ Hash créé: {hashed_password[:50]}...")
    
    # Create new admin account with ALL required fields
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
        "email_verified": True,
        "picture": None,
        "phone": None
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
    print(f"🗄️  MongoDB ID: {result.inserted_id}")
    print("="*70)
    
    # Verify the account was created
    verification = await db.users.find_one({"email": admin_email}, {"_id": 0, "password": 0})
    if verification:
        print("\n✅ VÉRIFICATION : Compte trouvé dans la base de données")
        print(f"   Role: {verification.get('role')}")
        print(f"   Plan: {verification.get('subscription_plan')}")
        print(f"   Active: {verification.get('is_active')}")
    else:
        print("\n❌ ERREUR : Compte non trouvé après insertion!")
    
    print("\n🎉 Vous pouvez maintenant vous connecter avec ces identifiants !")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(restore_admin())
