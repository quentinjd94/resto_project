from database import db
from datetime import datetime
import json

def get_menu(restaurant_id: str) -> dict:
    """Retourne le menu du restaurant"""
    menu = db.get_menu(restaurant_id)
    
    # Grouper par catégorie
    categories = {}
    for item in menu:
        cat = item.category
        if cat not in categories:
            categories[cat] = []
        
        categories[cat].append({
            "name": item.name,
            "price": item.sizes.unique or item.sizes.senior,
            "description": item.description or ""
        })
    
    return {"categories": categories}

def check_delivery_zone(restaurant_id: str, city: str) -> dict:
    """Vérifie si la ville est dans la zone"""
    zones = db.get_delivery_zones(restaurant_id)
    
    city_lower = city.lower().strip()
    for zone in zones:
        if zone.city.lower() == city_lower:
            return {
                "delivers": True,
                "min_order": zone.min_order_amount,
                "delivery_fee": zone.delivery_fee,
                "estimated_time": zone.estimated_time_minutes
            }
    
    return {
        "delivers": False,
        "message": f"Désolé, on ne livre pas à {city}. Vous pouvez commander à emporter !"
    }

def get_time() -> dict:
    """Retourne l'heure actuelle et les horaires"""
    now = datetime.now()
    current_time = now.strftime("%H:%M")
    day_of_week = now.weekday()
    
    # Horaires (12h-22h tous les jours pour Mama's Secret)
    is_open = 12 <= now.hour < 22
    
    return {
        "current_time": current_time,
        "day": day_of_week,
        "is_open": is_open,
        "opens_at": "12:00",
        "closes_at": "22:00"
    }

def save_order(restaurant_id: str, order_data: dict) -> dict:
    """Sauvegarde la commande"""
    try:
        order_id = db.create_order(
            restaurant_id=restaurant_id,
            customer_name=order_data.get('customer_name'),
            customer_phone=order_data.get('customer_phone'),
            order_type=order_data.get('order_type'),
            items=json.dumps(order_data.get('items')),
            total_amount=order_data.get('total'),
            delivery_address=order_data.get('delivery_address'),
            delivery_city=order_data.get('delivery_city'),
            delivery_instructions=order_data.get('delivery_instructions')
        )
        
        return {
            "success": True,
            "order_id": order_id,
            "message": "Commande enregistrée !"
        }
    except Exception as e:
        print(f"❌ Save order error: {e}")
        return {
            "success": False,
            "message": "Erreur lors de l'enregistrement"
        }

# Mapping des functions
FUNCTIONS_MAP = {
    "get_menu": get_menu,
    "check_delivery_zone": check_delivery_zone,
    "get_time": get_time,
    "save_order": save_order
}
