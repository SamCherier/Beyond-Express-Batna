"""
Initialize subscription plans in database
Run this once to seed the 4 Beyond Express plans
"""
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone
import os
import asyncio

# Plans data based on Beyond Express specifications
PLANS_DATA = [
    {
        "plan_type": "free",
        "name_fr": "BEYOND FREE",
        "name_ar": "بيوند المجاني",
        "name_en": "BEYOND FREE",
        "description_fr": "1 mois gratuit pour les débutants",
        "description_ar": "شهر مجاني للمبتدئين",
        "description_en": "1 free month for beginners",
        "target_audience_fr": "Les débutants",
        "target_audience_ar": "المبتدئين الذين لديهم أقل من 100 طلب شهريًا",
        "features": {
            "max_orders_per_month": 100,
            "max_delivery_companies": 1,
            "max_connected_pages": 1,
            "max_stock_items": None,
            "preparations_included": 0,
            "pickups_per_week": 0,
            "stock_management": False,
            "whatsapp_auto_confirmation": False,
            "ai_content_generator": False,
            "ai_generator_uses": 0,
            "advanced_analytics": False,
            "pro_dashboard": False,
            "unlimited_delivery_companies": False,
            "package_tracking": False,
            "detailed_reports": False,
            "dedicated_account_manager": False,
            "preferred_partner_rates": False,
            "daily_pickup": False
        },
        "pricing": {
            "monthly_price": 0.0,  # Free for first month
            "quarterly_price": None,
            "biannual_price": None,
            "annual_price": None,
            "onboarding_fee": None,
            "currency": "DZD"
        },
        "is_active": True,
        "display_order": 1
    },
    {
        "plan_type": "starter",
        "name_fr": "BEYOND STARTER",
        "name_ar": "بيوند المبتدئ",
        "name_en": "BEYOND STARTER",
        "description_fr": "Pour commerçants en phase de croissance",
        "description_ar": "خطة متكاملة للتجار الصاعدين",
        "description_en": "Complete plan for growing merchants",
        "target_audience_fr": "Commerçants en phase de croissance",
        "target_audience_ar": "خطة متكاملة للتجار الصاعدين",
        "features": {
            "max_orders_per_month": 500,
            "max_delivery_companies": 3,
            "max_connected_pages": 3,
            "max_stock_items": None,
            "preparations_included": 50,
            "pickups_per_week": 1,
            "stock_management": True,
            "whatsapp_auto_confirmation": True,
            "ai_content_generator": True,
            "ai_generator_uses": 2,
            "advanced_analytics": True,
            "pro_dashboard": False,
            "unlimited_delivery_companies": False,
            "package_tracking": False,
            "detailed_reports": False,
            "dedicated_account_manager": False,
            "preferred_partner_rates": False,
            "daily_pickup": False
        },
        "pricing": {
            "monthly_price": 12000.0,
            "quarterly_price": 6600.0,
            "biannual_price": 12000.0,
            "annual_price": 22000.0,
            "onboarding_fee": None,
            "currency": "DZD"
        },
        "is_active": True,
        "display_order": 2
    },
    {
        "plan_type": "pro",
        "name_fr": "BEYOND PRO",
        "name_ar": "بيوند المحترف",
        "name_en": "BEYOND PRO",
        "description_fr": "Solution tout-en-un pour e-commerces ambitieux",
        "description_ar": "أقوى خطة للتوسع",
        "description_en": "All-in-one solution for ambitious e-commerce",
        "target_audience_fr": "E-commerces ambitieux",
        "target_audience_ar": "أقوى خطة للتوسع",
        "features": {
            "max_orders_per_month": 1000,
            "max_delivery_companies": 999,  # Unlimited (represented as 999)
            "max_connected_pages": 10,
            "max_stock_items": 1000,
            "preparations_included": 200,
            "pickups_per_week": 3,
            "stock_management": True,
            "whatsapp_auto_confirmation": True,
            "ai_content_generator": True,
            "ai_generator_uses": 999,  # Unlimited
            "advanced_analytics": True,
            "pro_dashboard": True,
            "unlimited_delivery_companies": True,
            "package_tracking": True,
            "detailed_reports": True,
            "dedicated_account_manager": False,
            "preferred_partner_rates": False,
            "daily_pickup": False
        },
        "pricing": {
            "monthly_price": 25000.0,
            "quarterly_price": 20000.0,
            "biannual_price": 39000.0,
            "annual_price": 72000.0,
            "onboarding_fee": None,
            "currency": "DZD"
        },
        "is_active": True,
        "display_order": 3
    },
    {
        "plan_type": "business",
        "name_fr": "BEYOND BUSINESS",
        "name_ar": "بيوند للأعمال",
        "name_en": "BEYOND BUSINESS",
        "description_fr": "Pour grandes boutiques et marques établies",
        "description_ar": "تخزين وتسيير احترافي",
        "description_en": "For large shops and established brands",
        "target_audience_fr": "Grandes boutiques et marques",
        "target_audience_ar": "تخزين وتسيير احترافي",
        "features": {
            "max_orders_per_month": 9999,  # Virtually unlimited
            "max_delivery_companies": 999,
            "max_connected_pages": 999,
            "max_stock_items": 3000,
            "preparations_included": 500,
            "pickups_per_week": 7,  # Daily
            "stock_management": True,
            "whatsapp_auto_confirmation": True,
            "ai_content_generator": True,
            "ai_generator_uses": 999,
            "advanced_analytics": True,
            "pro_dashboard": True,
            "unlimited_delivery_companies": True,
            "package_tracking": True,
            "detailed_reports": True,
            "dedicated_account_manager": True,
            "preferred_partner_rates": True,
            "daily_pickup": True
        },
        "pricing": {
            "monthly_price": 50000.0,
            "quarterly_price": 140000.0,  # 3 months recommended
            "biannual_price": None,
            "annual_price": None,
            "onboarding_fee": 5000.0,
            "currency": "DZD"
        },
        "is_active": True,
        "display_order": 4
    }
]

async def seed_plans():
    """Initialize plans in MongoDB"""
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
    db_name = os.environ.get('DB_NAME', 'beyond_express_db')
    
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    plans_collection = db["plans"]
    
    # Check if plans already exist
    existing_count = await plans_collection.count_documents({})
    if existing_count > 0:
        print(f"⚠️  Plans already exist ({existing_count} found). Skipping seed.")
        return
    
    # Insert all plans
    for plan_data in PLANS_DATA:
        plan_data["created_at"] = datetime.now(timezone.utc)
        plan_data["updated_at"] = datetime.now(timezone.utc)
        
        await plans_collection.insert_one(plan_data)
        print(f"✅ Created plan: {plan_data['name_fr']} ({plan_data['plan_type']})")
    
    print(f"\n🎉 Successfully seeded {len(PLANS_DATA)} plans!")
    client.close()

if __name__ == "__main__":
    asyncio.run(seed_plans())
