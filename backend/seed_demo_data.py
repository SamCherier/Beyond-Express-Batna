"""
Data Seeding Script - Demo Investisseurs
Génère 15 commandes réalistes avec noms et adresses algériennes
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
from pathlib import Path
from datetime import datetime, timedelta, timezone
import random
import secrets

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Données réalistes algériennes
NOMS_ALGERIENS = [
    "Mohamed Amrani", "Sarah Benali", "Karim Boudiaf", "Amina Cherif",
    "Yacine Djamel", "Leila Mansour", "Rachid Moussa", "Fatima Kaci",
    "Sofiane Belkacem", "Nadia Hamidi", "Mehdi Slimani", "Samira Benahmed",
    "Farid Zidane", "Yasmine Touati", "Omar Benmohamed"
]

TELEPHONES = [
    "0555123456", "0661234567", "0770234567", "0551345678", "0662456789",
    "0771567890", "0552678901", "0663789012", "0772890123", "0553901234",
    "0664012345", "0773123456", "0554234567", "0665345678", "0774456789"
]

ADRESSES = [
    "12 Rue Didouche Mourad, Alger Centre",
    "45 Boulevard de la Liberté, Oran",
    "78 Avenue 1er Novembre, Sétif",
    "23 Rue Larbi Ben M'hidi, Constantine",
    "56 Boulevard Mohamed V, Batna",
    "89 Rue Emir Abdelkader, Annaba",
    "34 Avenue de l'ALN, Blida",
    "67 Rue Hassiba Ben Bouali, Tizi Ouzou",
    "90 Boulevard Zighoud Youcef, Béjaïa",
    "12 Rue Abane Ramdane, Tlemcen",
    "45 Avenue Ahmed Zabana, Biskra",
    "78 Rue Krim Belkacem, Chlef",
    "23 Boulevard Boumediene, Skikda",
    "56 Rue Colonel Lotfi, Mostaganem",
    "89 Avenue Si El Haouès, El Oued"
]

WILAYAS = [
    "Alger", "Oran", "Sétif", "Constantine", "Batna",
    "Annaba", "Blida", "Tizi Ouzou", "Béjaïa", "Tlemcen",
    "Biskra", "Chlef", "Skikda", "Mostaganem", "El Oued"
]

COMMUNES = [
    "Centre", "Hay El Badr", "Cite Djamila", "Bab Ezzouar", "Bab El Oued",
    "Hussein Dey", "El Biar", "Kouba", "Bachdjerrah", "Bir Mourad Rais",
    "Cheraga", "Draria", "El Harrach", "Bordj El Kiffan", "Dar El Beida"
]

PRODUITS = [
    "Smartphone Samsung Galaxy", "Ordinateur Portable HP", "Tablette iPad",
    "Montre connectée Apple Watch", "Console PlayStation 5", "Écouteurs AirPods",
    "TV Samsung 55 pouces", "Appareil photo Canon", "Drone DJI Mini",
    "MacBook Pro 14 pouces", "Casque gaming Razer", "Clavier mécanique",
    "Souris gaming Logitech", "Enceinte Bluetooth JBL", "Chargeur sans fil"
]

STATUS_DISTRIBUTION = [
    ("delivered", 5),      # 5 Livré (Vert)
    ("in_transit", 3),     # 3 En cours de livraison (Bleu)
    ("returned", 2),       # 2 Retour au dépôt (Rouge)
    ("pending", 5)         # 5 En attente (Gris)
]

async def seed_orders():
    """Génère 15 commandes réalistes pour la démo"""
    mongo_url = os.environ['MONGO_URL']
    client = AsyncIOMotorClient(mongo_url)
    db = client[os.environ['DB_NAME']]
    
    print("🧹 Nettoyage des anciennes commandes...")
    result = await db.orders.delete_many({})
    print(f"   ✅ {result.deleted_count} commandes supprimées")
    print("")
    
    print("🌱 Génération de 15 commandes réalistes...")
    print("")
    
    # Get admin user
    admin = await db.users.find_one({"role": "admin"}, {"_id": 0})
    if not admin:
        print("❌ Utilisateur admin introuvable")
        return
    
    # Get organization
    org = await db.organizations.find_one({}, {"_id": 0})
    if not org:
        print("❌ Organisation introuvable")
        return
    
    orders = []
    order_idx = 0
    
    # Generate orders with varied statuses
    for status, count in STATUS_DISTRIBUTION:
        for i in range(count):
            # Random dates over last 30 days
            days_ago = random.randint(1, 30)
            created_date = datetime.now(timezone.utc) - timedelta(days=days_ago)
            
            # Tracking ID
            tracking_id = f"BEX-{secrets.token_hex(6).upper()}"
            
            # Random data
            nom = NOMS_ALGERIENS[order_idx]
            tel = TELEPHONES[order_idx]
            adresse = ADRESSES[order_idx]
            wilaya = WILAYAS[order_idx]
            commune = random.choice(COMMUNES)
            produit = random.choice(PRODUITS)
            
            # COD amount (realistic prices)
            cod_amounts = [12500, 25000, 45000, 78000, 35000, 52000, 89000, 15000, 28000, 41000, 67000, 19000, 33000, 54000, 72000]
            cod_amount = cod_amounts[order_idx]
            
            # Shipping cost (realistic for Algeria)
            shipping_costs = {
                "Alger": 400, "Oran": 600, "Sétif": 700, "Constantine": 750,
                "Batna": 700, "Annaba": 800, "Blida": 500, "Tizi Ouzou": 650,
                "Béjaïa": 700, "Tlemcen": 850, "Biskra": 900, "Chlef": 650,
                "Skikda": 800, "Mostaganem": 750, "El Oued": 1000
            }
            shipping_cost = shipping_costs.get(wilaya, 600)
            
            net_to_merchant = cod_amount - shipping_cost
            
            # Delivery type
            delivery_type = random.choice(["Domicile", "Stop Desk"])
            
            # Payment status
            payment_status = "paid" if status == "delivered" else "unpaid"
            
            # Collected/Transferred dates for delivered orders
            collected_date = None
            transferred_date = None
            if status == "delivered":
                collected_date = (created_date + timedelta(days=random.randint(3, 5))).isoformat()
                transferred_date = (created_date + timedelta(days=random.randint(8, 12))).isoformat()
            
            order = {
                "id": secrets.token_hex(12),
                "tracking_id": tracking_id,
                "user_id": admin['id'],
                "status": status,
                "sender": {
                    "name": org['name'],
                    "phone": org['phone'],
                    "address": org['address'],
                    "wilaya": "Batna",
                    "commune": "Batna"
                },
                "recipient": {
                    "name": nom,
                    "phone": tel,
                    "address": adresse,
                    "wilaya": wilaya,
                    "commune": commune
                },
                "description": produit,
                "cod_amount": cod_amount,
                "shipping_cost": shipping_cost,
                "net_to_merchant": net_to_merchant,
                "delivery_type": delivery_type,
                "delivery_partner": "Yalidine",
                "pin_code": str(random.randint(1000, 9999)),
                "payment_status": payment_status,
                "collected_date": collected_date,
                "transferred_date": transferred_date,
                "created_at": created_date.isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            
            orders.append(order)
            
            # Display status emoji
            status_emoji = {
                "delivered": "✅",
                "in_transit": "🚚",
                "returned": "↩️",
                "pending": "🕒"
            }
            
            status_fr = {
                "delivered": "Livré",
                "in_transit": "En cours",
                "returned": "Retour",
                "pending": "En attente"
            }
            
            print(f"{status_emoji[status]} {status_fr[status]:12} | {nom:20} | {wilaya:15} | {cod_amount:,} DA | {tracking_id}")
            
            order_idx += 1
    
    # Insert all orders
    await db.orders.insert_many(orders)
    
    print("")
    print("✅ 15 commandes créées avec succès!")
    print("")
    print("📊 Résumé par statut:")
    print(f"   ✅ Livré:           5 commandes")
    print(f"   🚚 En cours:        3 commandes")
    print(f"   ↩️  Retour:          2 commandes")
    print(f"   🕒 En attente:      5 commandes")
    print("")
    print("🎯 Dashboard prêt pour la démo investisseurs!")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(seed_orders())
