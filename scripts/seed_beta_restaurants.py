import sys
sys.path.append('/workspace/pizza-agent')

from database import db
from models import Restaurant, MenuItem, MenuItemSize, DeliveryZone, OpeningHour
import uuid
from datetime import time

def seed_restaurant_1():
    """Macadam Pizza - Sucy-en-Brie"""
    
    restaurant_id = str(uuid.uuid4())
    
    # Restaurant
    restaurant = Restaurant(
        id=restaurant_id,
        name="Macadam Pizza",
        twilio_phone="+33123456789",  # À remplacer par vrai numéro
        owner_phone="+33612345678",
        email="contact@macadam-pizza.fr",
        address="123 Avenue de la Gare",
        city="Sucy-en-Brie",
        custom_prompt="Toujours proposer une boisson. Insister sur les desserts maison."
    )
    db.add_restaurant(restaurant)
    print(f"✅ Added: {restaurant.name}")
    
    # Menu - Pizzas
    pizzas = [
        {"name": "Margherita", "senior": 10.50, "mega": 14.50},
        {"name": "Reine", "senior": 11.50, "mega": 15.50},
        {"name": "4 Fromages", "senior": 12.00, "mega": 16.00},
        {"name": "Chorizo", "senior": 12.50, "mega": 16.50},
        {"name": "Orientale", "senior": 12.50, "mega": 16.50},
        {"name": "Calzone", "senior": 13.00, "mega": 17.00},
    ]
    
    for pizza in pizzas:
        item = MenuItem(
            id=str(uuid.uuid4()),
            restaurant_id=restaurant_id,
            name=pizza["name"],
            category="pizza",
            sizes=MenuItemSize(senior=pizza["senior"], mega=pizza["mega"]),
            description=f"Pizza {pizza['name']}"
        )
        db.add_menu_item(item)
    
    # Menu - Boissons
    boissons = [
        {"name": "Coca-Cola 33cl", "price": 2.50},
        {"name": "Coca-Cola 1.5L", "price": 4.50},
        {"name": "Orangina 33cl", "price": 2.50},
        {"name": "Eau 50cl", "price": 1.50},
    ]
    
    for boisson in boissons:
        item = MenuItem(
            id=str(uuid.uuid4()),
            restaurant_id=restaurant_id,
            name=boisson["name"],
            category="boisson",
            sizes=MenuItemSize(unique=boisson["price"]),
            description=boisson["name"]
        )
        db.add_menu_item(item)
    
    # Menu - Desserts
    desserts = [
        {"name": "Tiramisu maison", "price": 5.00},
        {"name": "Panna cotta", "price": 4.50},
    ]
    
    for dessert in desserts:
        item = MenuItem(
            id=str(uuid.uuid4()),
            restaurant_id=restaurant_id,
            name=dessert["name"],
            category="dessert",
            sizes=MenuItemSize(unique=dessert["price"]),
            description=dessert["name"]
        )
        db.add_menu_item(item)
    
    # Zones de livraison
    zones = [
        {
            "city": "Sucy-en-Brie",
            "postal_code": "94370",
            "streets": [
                "Avenue de la Gare", "Rue Victor Hugo", "Avenue du Général de Gaulle",
                "Rue de la République", "Avenue du Maréchal Foch"
            ],
            "min_order": 18.00
        },
        {
            "city": "Boissy-Saint-Léger",
            "postal_code": "94470",
            "streets": [
                "Avenue du Général Leclerc", "Rue Jean Jaurès", "Avenue de Paris"
            ],
            "min_order": 18.00
        }
    ]
    
    for zone_data in zones:
        zone = DeliveryZone(
            id=str(uuid.uuid4()),
            restaurant_id=restaurant_id,
            city=zone_data["city"],
            postal_code=zone_data["postal_code"],
            streets=zone_data["streets"],
            min_order_amount=zone_data["min_order"],
            delivery_fee=0.0
        )
        db.add_delivery_zone(zone)
    
    # Horaires (Lundi à Dimanche)
    hours = [
        # Lundi à Jeudi (0-3)
        *[(day, "11:00", "14:00") for day in range(4)],
        *[(day, "18:00", "22:00") for day in range(4)],
        # Vendredi-Samedi (4-5)
        *[(day, "11:00", "14:00") for day in range(4, 6)],
        *[(day, "18:00", "23:00") for day in range(4, 6)],
        # Dimanche (6)
        (6, "18:00", "22:00")
    ]
    
    for day, open_time, close_time in hours:
        hour = OpeningHour(
            id=str(uuid.uuid4()),
            restaurant_id=restaurant_id,
            day_of_week=day,
            open_time=time.fromisoformat(open_time),
            close_time=time.fromisoformat(close_time),
            is_closed=False
        )
        db.add_opening_hour(hour)
    
    print(f"   ✓ Menu: {len(pizzas)} pizzas, {len(boissons)} boissons, {len(desserts)} desserts")
    print(f"   ✓ Zones: {len(zones)} zones de livraison")
    print(f"   ✓ Horaires configurés")

def seed_restaurant_2():
    """Pizza Express - Créteil"""
    
    restaurant_id = str(uuid.uuid4())
    
    restaurant = Restaurant(
        id=restaurant_id,
        name="Pizza Express Créteil",
        twilio_phone="+33198765432",  # À remplacer
        owner_phone="+33687654321",
        email="contact@pizza-express.fr",
        address="45 Avenue du Général de Gaulle",
        city="Créteil",
        custom_prompt="Mettre en avant nos pizzas signature. Toujours demander si le client souhaite ajouter des suppléments."
    )
    db.add_restaurant(restaurant)
    print(f"✅ Added: {restaurant.name}")
    
    # Menu simplifié
    pizzas = [
        {"name": "Margherita", "senior": 9.90, "mega": 13.90},
        {"name": "Pepperoni", "senior": 11.90, "mega": 15.90},
        {"name": "Végétarienne", "senior": 11.50, "mega": 15.50},
        {"name": "4 Saisons", "senior": 12.50, "mega": 16.50},
    ]
    
    for pizza in pizzas:
        item = MenuItem(
            id=str(uuid.uuid4()),
            restaurant_id=restaurant_id,
            name=pizza["name"],
            category="pizza",
            sizes=MenuItemSize(senior=pizza["senior"], mega=pizza["mega"])
        )
        db.add_menu_item(item)
    
    # Zone de livraison
    zone = DeliveryZone(
        id=str(uuid.uuid4()),
        restaurant_id=restaurant_id,
        city="Créteil",
        postal_code="94000",
        streets=["Avenue du Général de Gaulle", "Rue de Paris", "Boulevard Kennedy"],
        min_order_amount=15.00,
        delivery_fee=0.0
    )
    db.add_delivery_zone(zone)
    
    # Horaires (tous les jours 11h-14h et 18h-22h)
    for day in range(7):
        for slot in [("11:00", "14:00"), ("18:00", "22:00")]:
            hour = OpeningHour(
                id=str(uuid.uuid4()),
                restaurant_id=restaurant_id,
                day_of_week=day,
                open_time=time.fromisoformat(slot[0]),
                close_time=time.fromisoformat(slot[1])
            )
            db.add_opening_hour(hour)
    
    print(f"   ✓ Menu: {len(pizzas)} pizzas")

def seed_restaurant_3():
    """Bella Napoli - Maisons-Alfort"""
    
    restaurant_id = str(uuid.uuid4())
    
    restaurant = Restaurant(
        id=restaurant_id,
        name="Bella Napoli",
        twilio_phone="+33134567890",  # À remplacer
        owner_phone="+33645678901",
        email="contact@bella-napoli.fr",
        address="78 Rue Jean Jaurès",
        city="Maisons-Alfort",
        custom_prompt="Style italien authentique. Toujours mentionner que nos pizzas sont préparées avec des ingrédients italiens."
    )
    db.add_restaurant(restaurant)
    print(f"✅ Added: {restaurant.name}")
    
    # Menu
    pizzas = [
        {"name": "Napoletana", "senior": 11.00, "mega": 15.00},
        {"name": "Diavola", "senior": 12.00, "mega": 16.00},
        {"name": "Prosciutto", "senior": 12.50, "mega": 16.50},
    ]
    
    for pizza in pizzas:
        item = MenuItem(
            id=str(uuid.uuid4()),
            restaurant_id=restaurant_id,
            name=pizza["name"],
            category="pizza",
            sizes=MenuItemSize(senior=pizza["senior"], mega=pizza["mega"])
        )
        db.add_menu_item(item)
    
    # Zone
    zone = DeliveryZone(
        id=str(uuid.uuid4()),
        restaurant_id=restaurant_id,
        city="Maisons-Alfort",
        postal_code="94700",
        streets=["Rue Jean Jaurès", "Avenue du Général Leclerc"],
        min_order_amount=20.00
    )
    db.add_delivery_zone(zone)
    
    # Horaires
    for day in range(7):
        for slot in [("11:30", "14:00"), ("18:30", "22:30")]:
            hour = OpeningHour(
                id=str(uuid.uuid4()),
                restaurant_id=restaurant_id,
                day_of_week=day,
                open_time=time.fromisoformat(slot[0]),
                close_time=time.fromisoformat(slot[1])
            )
            db.add_opening_hour(hour)
    
    print(f"   ✓ Menu: {len(pizzas)} pizzas")

def seed_restaurant_4():
    """Pizza Roma - Vitry-sur-Seine"""
    
    restaurant_id = str(uuid.uuid4())
    
    restaurant = Restaurant(
        id=restaurant_id,
        name="Pizza Roma",
        twilio_phone="+33145678901",  # À remplacer
        owner_phone="+33656789012",
        email="contact@pizza-roma.fr",
        address="12 Place de la Mairie",
        city="Vitry-sur-Seine",
        custom_prompt="Restaurant familial. Toujours être chaleureux et proposer nos formules du jour."
    )
    db.add_restaurant(restaurant)
    print(f"✅ Added: {restaurant.name}")
    
    # Menu
    pizzas = [
        {"name": "Regina", "senior": 10.50, "mega": 14.50},
        {"name": "Sicilienne", "senior": 11.50, "mega": 15.50},
        {"name": "Campagnarde", "senior": 12.00, "mega": 16.00},
    ]
    
    for pizza in pizzas:
        item = MenuItem(
            id=str(uuid.uuid4()),
            restaurant_id=restaurant_id,
            name=pizza["name"],
            category="pizza",
            sizes=MenuItemSize(senior=pizza["senior"], mega=pizza["mega"])
        )
        db.add_menu_item(item)
    
    # Zone
    zone = DeliveryZone(
        id=str(uuid.uuid4()),
        restaurant_id=restaurant_id,
        city="Vitry-sur-Seine",
        postal_code="94400",
        streets=["Place de la Mairie", "Rue de Paris", "Avenue Paul Vaillant-Couturier"],
        min_order_amount=18.00
    )
    db.add_delivery_zone(zone)
    
    # Horaires
    for day in range(7):
        if day == 0:  # Fermé le lundi
            continue
        for slot in [("11:00", "14:00"), ("18:00", "22:00")]:
            hour = OpeningHour(
                id=str(uuid.uuid4()),
                restaurant_id=restaurant_id,
                day_of_week=day,
                open_time=time.fromisoformat(slot[0]),
                close_time=time.fromisoformat(slot[1])
            )
            db.add_opening_hour(hour)
    
    print(f"   ✓ Menu: {len(pizzas)} pizzas")

def seed_restaurant_5():
    """L'Authentique - Ivry-sur-Seine"""
    
    restaurant_id = str(uuid.uuid4())
    
    restaurant = Restaurant(
        id=restaurant_id,
        name="L'Authentique Pizza",
        twilio_phone="+33156789012",  # À remplacer
        owner_phone="+33667890123",
        email="contact@authentique-pizza.fr",
        address="34 Avenue de la République",
        city="Ivry-sur-Seine",
        custom_prompt="Pizzas artisanales au feu de bois. Toujours mentionner notre cuisson au feu de bois."
    )
    db.add_restaurant(restaurant)
    print(f"✅ Added: {restaurant.name}")
    
    # Menu
    pizzas = [
        {"name": "Classique", "senior": 10.00, "mega": 14.00},
        {"name": "Savoyarde", "senior": 12.00, "mega": 16.00},
        {"name": "Méditerranéenne", "senior": 11.50, "mega": 15.50},
        {"name": "Chef", "senior": 13.00, "mega": 17.00},
    ]
    
    for pizza in pizzas:
        item = MenuItem(
            id=str(uuid.uuid4()),
            restaurant_id=restaurant_id,
            name=pizza["name"],
            category="pizza",
            sizes=MenuItemSize(senior=pizza["senior"], mega=pizza["mega"])
        )
        db.add_menu_item(item)
    
    # Zone
    zone = DeliveryZone(
        id=str(uuid.uuid4()),
        restaurant_id=restaurant_id,
        city="Ivry-sur-Seine",
        postal_code="94200",
        streets=["Avenue de la République", "Rue Raspail", "Boulevard Maxime Gorki"],
        min_order_amount=18.00
    )
    db.add_delivery_zone(zone)
    
    # Horaires
    for day in range(7):
        for slot in [("11:30", "14:00"), ("18:30", "22:30")]:
            hour = OpeningHour(
                id=str(uuid.uuid4()),
                restaurant_id=restaurant_id,
                day_of_week=day,
                open_time=time.fromisoformat(slot[0]),
                close_time=time.fromisoformat(slot[1])
            )
            db.add_opening_hour(hour)
    
    print(f"   ✓ Menu: {len(pizzas)} pizzas")

if __name__ == "__main__":
    print("🌱 Seeding 5 beta restaurants...\n")
    
    seed_restaurant_1()
    print()
    seed_restaurant_2()
    print()
    seed_restaurant_3()
    print()
    seed_restaurant_4()
    print()
    seed_restaurant_5()
    
    print("\n🎉 All 5 beta restaurants seeded successfully!")
    print("\n📊 Summary:")
    print("   • Macadam Pizza (Sucy-en-Brie)")
    print("   • Pizza Express (Créteil)")
    print("   • Bella Napoli (Maisons-Alfort)")
    print("   • Pizza Roma (Vitry-sur-Seine)")
    print("   • L'Authentique (Ivry-sur-Seine)")
