from models import Restaurant, MenuItem, DeliveryZone, OpeningHour
from typing import List
from datetime import datetime

def build_dynamic_prompt(
    restaurant: Restaurant,
    menu: List[MenuItem],
    zones: List[DeliveryZone],
    hours: List[OpeningHour]
) -> str:
    """Construit le system prompt dynamiquement selon le restaurant"""
    
    # Format menu par catégorie
    pizzas = [item for item in menu if item.category == "pizza"]
    boissons = [item for item in menu if item.category == "boisson"]
    desserts = [item for item in menu if item.category == "dessert"]
    
    menu_text = "MENU:\n\nPIZZAS:\n"
    for pizza in pizzas:
        if pizza.sizes.senior and pizza.sizes.mega:
            menu_text += f"- {pizza.name}: Senior {pizza.sizes.senior}€, Mega {pizza.sizes.mega}€\n"
    
    if boissons:
        menu_text += "\nBOISSONS:\n"
        for b in boissons:
            price = b.sizes.unique or b.sizes.senior or b.sizes.mega
            menu_text += f"- {b.name}: {price}€\n"
    
    if desserts:
        menu_text += "\nDESSERTS:\n"
        for d in desserts:
            price = d.sizes.unique or d.sizes.senior or d.sizes.mega
            menu_text += f"- {d.name}: {price}€\n"
    
    # Format zones de livraison
    zones_text = "ZONES DE LIVRAISON:\n"
    for zone in zones:
        zones_text += f"- {zone.city} ({zone.postal_code}): Minimum {zone.min_order_amount}€\n"
    
    # Format horaires
    current_day = datetime.now().weekday()
    today_hours = [h for h in hours if h.day_of_week == current_day and not h.is_closed]
    
    hours_text = "HORAIRES:\n"
    if today_hours:
        for h in today_hours:
            hours_text += f"Aujourd'hui: {h.open_time.strftime('%H:%M')}-{h.close_time.strftime('%H:%M')}\n"
    else:
        hours_text += "Fermé aujourd'hui\n"
    
    # Instructions custom
    custom = restaurant.custom_prompt or "Être chaleureux et efficace."
    
    # Prompt complet
    prompt = f"""Tu es Léo, agent vocal pour {restaurant.name}.

{menu_text}

{zones_text}

{hours_text}

RÈGLES:
1. TOUJOURS demander la TAILLE (senior ou mega)
2. Confirmer chaque pizza ajoutée
3. Vérifier ville et rue pour livraisons
4. Phrases COURTES (<15 mots)
5. Récapituler à la fin
6. Annoncer délai: 20min (emporter) ou 30min (livraison)

{custom}

Réponds en français, naturel et concis."""

    return prompt