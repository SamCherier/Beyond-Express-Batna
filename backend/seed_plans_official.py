"""
Seed Script - Official Pricing Plans
Insert 4 subscription plans into MongoDB
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone
import os
import uuid

# MongoDB connection
mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
db_name = os.environ.get('DB_NAME', 'beyond_express_db')

async def seed_plans():
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    # Clear existing plans
    await db.plans.delete_many({})
    print("🗑️  Anciens plans supprimés")
    
    now = datetime.now(timezone.utc)
    
    # Plan 1: BEYOND Free (7-day trial)
    free_plan = {
        "id": str(uuid.uuid4()),
        "plan_type": "free",
        "name_fr": "BEYOND Free",
        "name_ar": "بيوند مجاني",
        "name_en": "BEYOND Free",
        "description_fr": "Essai gratuit de 7 jours",
        "description_ar": "تجربة مجانية لمدة 7 أيام",
        "description_en": "7-day free trial",
        "target_audience_fr": "Essai gratuit",
        "target_audience_ar": "تجربة مجانية",
        "target_audience_en": "Free Trial",
        "category": "trial",
        "is_active": True,
        "display_order": 1,
        "features": {
            "max_orders_per_month": 50,  # Total during trial
            "max_delivery_companies": 1,
            "unlimited_delivery_companies": False,
            "max_connected_pages": 1,
            "stock_management": False,
            "whatsapp_auto_confirmation": False,
            "ai_content_generator": False,
            "ai_generator_uses": 0,
            "advanced_analytics": False,
            "pro_dashboard": False,
            "package_tracking": True,
            "detailed_reports": False,
            "dedicated_account_manager": False,
            "preferred_partner_rates": False,
            "daily_pickup": False,
            "preparations_included": 0,
            "pickups_per_week": 0
        },
        "pricing": {
            "monthly_price": 0,
            "quarterly_price": 0,
            "biannual_price": 0,
            "annual_price": 0,
            "trial_days": 7
        },
        "support_level": "Support limité",
        "created_at": now,
        "updated_at": now
    }
    
    # Plan 2: BEYOND Beginner (NEW)
    beginner_plan = {
        "id": str(uuid.uuid4()),
        "plan_type": "beginner",
        "name_fr": "BEYOND Beginner",
        "name_ar": "بيوند المبتدئ",
        "name_en": "BEYOND Beginner",
        "description_fr": "Pour nouveaux vendeurs",
        "description_ar": "للبائعين الجدد",
        "description_en": "For new sellers",
        "target_audience_fr": "Nouveaux vendeurs",
        "target_audience_ar": "البائعون الجدد",
        "target_audience_en": "New sellers",
        "category": "basic",
        "is_active": True,
        "display_order": 2,
        "features": {
            "max_orders_per_month": 100,
            "max_delivery_companies": 1,
            "unlimited_delivery_companies": False,
            "max_connected_pages": 1,
            "stock_management": True,
            "whatsapp_auto_confirmation": False,
            "ai_content_generator": False,
            "ai_generator_uses": 0,
            "advanced_analytics": False,
            "pro_dashboard": False,  # Dashboard simplifié
            "package_tracking": True,
            "detailed_reports": False,
            "dedicated_account_manager": False,
            "preferred_partner_rates": False,
            "daily_pickup": False,
            "preparations_included": 50,
            "pickups_per_week": 2
        },
        "pricing": {
            "monthly_price": 1500,
            "quarterly_price": 0,  # Monthly only
            "biannual_price": 0,
            "annual_price": 0,
            "trial_days": 0
        },
        "support_level": "Support standard",
        "created_at": now,
        "updated_at": now
    }
    
    # Plan 3: BEYOND Starter (Growth)
    starter_plan = {
        "id": str(uuid.uuid4()),
        "plan_type": "starter",
        "name_fr": "BEYOND Starter",
        "name_ar": "بيوند المبتدئ",
        "name_en": "BEYOND Starter",
        "description_fr": "Plan croissance",
        "description_ar": "خطة النمو",
        "description_en": "Growth plan",
        "target_audience_fr": "Croissance",
        "target_audience_ar": "النمو",
        "target_audience_en": "Growth",
        "category": "growth",
        "is_active": True,
        "display_order": 3,
        "features": {
            "max_orders_per_month": 500,
            "max_delivery_companies": 3,
            "unlimited_delivery_companies": False,
            "max_connected_pages": 2,
            "stock_management": True,
            "whatsapp_auto_confirmation": True,
            "ai_content_generator": True,
            "ai_generator_uses": 2,  # 2 AI tools
            "advanced_analytics": False,
            "pro_dashboard": False,
            "package_tracking": True,
            "detailed_reports": False,
            "dedicated_account_manager": False,
            "preferred_partner_rates": False,
            "daily_pickup": False,
            "preparations_included": 200,
            "pickups_per_week": 4
        },
        "pricing": {
            "monthly_price": 2500,
            "quarterly_price": 7000,   # 3 months
            "biannual_price": 13000,   # 6 months
            "annual_price": 25000,     # 12 months
            "trial_days": 0
        },
        "support_level": "Support prioritaire",
        "created_at": now,
        "updated_at": now
    }
    
    # Plan 4: BEYOND Pro (Ultimate)
    pro_plan = {
        "id": str(uuid.uuid4()),
        "plan_type": "pro",
        "name_fr": "BEYOND Pro",
        "name_ar": "بيوند برو",
        "name_en": "BEYOND Pro",
        "description_fr": "Plan ultime",
        "description_ar": "الخطة النهائية",
        "description_en": "Ultimate plan",
        "target_audience_fr": "Entreprises",
        "target_audience_ar": "الشركات",
        "target_audience_en": "Businesses",
        "category": "premium",
        "is_active": True,
        "display_order": 4,
        "features": {
            "max_orders_per_month": -1,  # Unlimited
            "max_delivery_companies": -1,  # Unlimited
            "unlimited_delivery_companies": True,
            "max_connected_pages": -1,
            "stock_management": True,
            "whatsapp_auto_confirmation": True,
            "ai_content_generator": True,
            "ai_generator_uses": -1,  # Unlimited
            "advanced_analytics": True,
            "pro_dashboard": True,
            "package_tracking": True,
            "detailed_reports": True,
            "dedicated_account_manager": True,
            "preferred_partner_rates": True,
            "daily_pickup": True,
            "preparations_included": -1,
            "pickups_per_week": 7
        },
        "pricing": {
            "monthly_price": 7000,
            "quarterly_price": 20000,   # 3 months
            "biannual_price": 40000,    # 6 months
            "annual_price": 75000,      # 12 months
            "trial_days": 0
        },
        "support_level": "Assistance personnalisée",
        "created_at": now,
        "updated_at": now
    }
    
    # Insert all plans
    plans = [free_plan, beginner_plan, starter_plan, pro_plan]
    await db.plans.insert_many(plans)
    
    print(f"✅ {len(plans)} plans insérés avec succès:")
    print(f"   1. BEYOND Free (Essai 7 jours)")
    print(f"   2. BEYOND Beginner (1,500 DA/mois)")
    print(f"   3. BEYOND Starter (2,500 DA/mois)")
    print(f"   4. BEYOND Pro (7,000 DA/mois)")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(seed_plans())
