import pandas as pd
import sqlite3
import uuid

def generate_id():
    return str(uuid.uuid4())[:8]

# Lire l'Excel
df = pd.read_excel('menu_grouped.xlsx')

# Connexion DB
conn = sqlite3.connect('pizza.db')
cursor = conn.cursor()

# Créer les tables
cursor.executescript("""
CREATE TABLE IF NOT EXISTS restaurants (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    address TEXT NOT NULL,
    city TEXT NOT NULL,
    postal_code TEXT NOT NULL,
    phone TEXT NOT NULL,
    owner_name TEXT,
    owner_phone TEXT,
    owner_email TEXT,
    custom_prompt TEXT,
    is_active INTEGER DEFAULT 1,
    assistant_id TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS menu_items (
    id TEXT PRIMARY KEY,
    restaurant_id TEXT NOT NULL,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    ingredients TEXT,
    description TEXT,
    tags TEXT,
    price_unique REAL,
    is_available INTEGER DEFAULT 1,
    display_order INTEGER DEFAULT 0,
    FOREIGN KEY (restaurant_id) REFERENCES restaurants(id)
);

CREATE TABLE IF NOT EXISTS delivery_zones (
    id TEXT PRIMARY KEY,
    restaurant_id TEXT NOT NULL,
    city TEXT NOT NULL,
    postal_code TEXT NOT NULL,
    min_order_amount REAL DEFAULT 15.0,
    delivery_fee REAL DEFAULT 0.0,
    estimated_time_minutes INTEGER DEFAULT 30,
    is_active INTEGER DEFAULT 1,
    FOREIGN KEY (restaurant_id) REFERENCES restaurants(id)
);

CREATE TABLE IF NOT EXISTS opening_hours (
    id TEXT PRIMARY KEY,
    restaurant_id TEXT NOT NULL,
    day_of_week INTEGER NOT NULL,
    open_time TEXT NOT NULL,
    close_time TEXT NOT NULL,
    is_closed INTEGER DEFAULT 0,
    FOREIGN KEY (restaurant_id) REFERENCES restaurants(id)
);

CREATE TABLE IF NOT EXISTS orders (
    id TEXT PRIMARY KEY,
    restaurant_id TEXT NOT NULL,
    call_sid TEXT,
    customer_phone TEXT,
    customer_name TEXT,
    order_type TEXT NOT NULL,
    items TEXT NOT NULL,
    total_amount REAL NOT NULL,
    delivery_address TEXT,
    delivery_city TEXT,
    delivery_instructions TEXT,
    status TEXT DEFAULT 'pending',
    estimated_time_minutes INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (restaurant_id) REFERENCES restaurants(id)
);
""")

# Insérer le restaurant
resto_id = "resto_mamas"
cursor.execute("""
    INSERT OR REPLACE INTO restaurants 
    (id, name, address, city, postal_code, phone, assistant_id, is_active)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
""", (
    resto_id,
    "Mama's Secret",
    "64 Rue Emile Zola",
    "Fresnes",
    "94260",
    "+33100000000",  # À remplacer
    "TON_ASSISTANT_ID_ICI",  # À remplacer
    1
))

print("✅ Restaurant créé")

# Insérer les horaires (tous les jours 12h-22h)
for day in range(7):
    cursor.execute("""
        INSERT OR REPLACE INTO opening_hours 
        (id, restaurant_id, day_of_week, open_time, close_time)
        VALUES (?, ?, ?, ?, ?)
    """, (
        f"hours_{day}",
        resto_id,
        day,
        "12:00",
        "22:00"
    ))

print("✅ Horaires créés")

# Zones de livraison par défaut (Fresnes + alentours)
zones = [
    ("Fresnes", "94260", 15.0),
    ("L'Haÿ-les-Roses", "94240", 20.0),
    ("Rungis", "94150", 20.0),
    ("Chevilly-Larue", "94550", 20.0)
]

for city, postal, min_order in zones:
    cursor.execute("""
        INSERT OR REPLACE INTO delivery_zones 
        (id, restaurant_id, city, postal_code, min_order_amount)
        VALUES (?, ?, ?, ?, ?)
    """, (
        generate_id(),
        resto_id,
        city,
        postal,
        min_order
    ))

print(f"✅ {len(zones)} zones de livraison créées")

# Parser le menu depuis Excel
print("\n📋 Parsing menu...")

for idx, row in df.iterrows():
    # Adapter selon les colonnes de ton Excel
    # Supposons: Catégorie | Nom | Prix | Description
    
    category = str(row.get('Catégorie', row.get('Category', 'autre'))).strip().lower()
    name = str(row.get('Nom', row.get('Name', row.get('Produit', '')))).strip()
    price = float(row.get('Prix', row.get('Price', 0)))
    description = str(row.get('Description', '')).strip() if pd.notna(row.get('Description')) else ''
    
    if not name or name == 'nan':
        continue
    
    # Tags automatiques selon catégorie
    tags = []
    if 'poke' in category:
        tags = ['healthy', 'fresh', 'customizable']
    elif 'sushi' in category:
        tags = ['japanese', 'fresh', 'seafood']
    elif 'boisson' in category or 'drink' in category:
        tags = ['beverage']
    
    cursor.execute("""
        INSERT INTO menu_items 
        (id, restaurant_id, name, category, description, tags, price_unique, display_order)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        generate_id(),
        resto_id,
        name,
        category,
        description,
        ','.join(tags),
        price,
        idx
    ))
    
    print(f"  ✓ {name} - {price}€")

conn.commit()
conn.close()

print(f"\n🎉 DB créée avec succès!")
print(f"📍 Restaurant: Mama's Secret")
print(f"🗄️  Fichier: pizza.db")
