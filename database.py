import sqlite3
import json
from typing import List, Optional
from datetime import datetime, time
import uuid

from models import (
    Restaurant, MenuItem, DeliveryZone, OpeningHour,
    Order, OrderItem, DeliveryAddress, SMSLog, OrderType, OrderStatus
)

class Database:
    def __init__(self, db_path: str = "data/pizza_agent.db"):
        self.db_path = db_path
        self.init_db()
    
    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Permet d'accéder aux colonnes par nom
        return conn
    
    def init_db(self):
        """Créer toutes les tables"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # RESTAURANTS
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS restaurants (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                twilio_phone TEXT UNIQUE NOT NULL,
                owner_phone TEXT NOT NULL,
                email TEXT,
                address TEXT NOT NULL,
                city TEXT NOT NULL,
                custom_prompt TEXT,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # MENU ITEMS
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS menu_items (
                id TEXT PRIMARY KEY,
                restaurant_id TEXT NOT NULL,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                sizes TEXT NOT NULL,
                description TEXT,
                available BOOLEAN DEFAULT 1,
                FOREIGN KEY (restaurant_id) REFERENCES restaurants(id)
            )
        """)
        
        # DELIVERY ZONES
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS delivery_zones (
                id TEXT PRIMARY KEY,
                restaurant_id TEXT NOT NULL,
                city TEXT NOT NULL,
                postal_code TEXT NOT NULL,
                streets TEXT NOT NULL,
                min_order_amount REAL NOT NULL,
                delivery_fee REAL DEFAULT 0,
                FOREIGN KEY (restaurant_id) REFERENCES restaurants(id)
            )
        """)
        
        # OPENING HOURS
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS opening_hours (
                id TEXT PRIMARY KEY,
                restaurant_id TEXT NOT NULL,
                day_of_week INTEGER NOT NULL,
                open_time TEXT NOT NULL,
                close_time TEXT NOT NULL,
                is_closed BOOLEAN DEFAULT 0,
                FOREIGN KEY (restaurant_id) REFERENCES restaurants(id)
            )
        """)
        
        # ORDERS
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id TEXT PRIMARY KEY,
                restaurant_id TEXT NOT NULL,
                call_sid TEXT NOT NULL,
                customer_phone TEXT NOT NULL,
                customer_name TEXT,
                order_type TEXT NOT NULL,
                items TEXT NOT NULL,
                total_amount REAL NOT NULL,
                delivery_address TEXT,
                status TEXT DEFAULT 'in_progress',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                conversation_transcript TEXT,
                FOREIGN KEY (restaurant_id) REFERENCES restaurants(id)
            )
        """)
        
        # SMS LOGS
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sms_logs (
                id TEXT PRIMARY KEY,
                order_id TEXT NOT NULL,
                recipient TEXT NOT NULL,
                message TEXT NOT NULL,
                status TEXT NOT NULL,
                sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (order_id) REFERENCES orders(id)
            )
        """)
        
        conn.commit()
        conn.close()
        print("✅ Database initialized")

    def create_order(self, restaurant_id: str, customer_name: str, customer_phone: str,
                   order_type: str, items: str, total_amount: float,
                   delivery_address: str = None, delivery_city: str = None,
                   delivery_instructions: str = None, call_sid: str = None) -> str:
      """Crée une nouvelle commande"""
      import uuid
      order_id = str(uuid.uuid4())[:8]
    
      conn = self.get_connection()
      cursor = conn.cursor()
    
      cursor.execute("""
          INSERT INTO orders 
          (id, restaurant_id, call_sid, customer_phone, customer_name, 
           order_type, items, total_amount, delivery_address, delivery_city, 
           delivery_instructions, status, created_at)
          VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', datetime('now'))
      """, (
          order_id, restaurant_id, call_sid, customer_phone, customer_name,
          order_type, items, total_amount, delivery_address, delivery_city,
          delivery_instructions
      ))
    
      conn.commit()
      conn.close()
    
      return order_id
    
    # ===== RESTAURANTS =====
    
    def add_restaurant(self, restaurant: Restaurant):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO restaurants 
            (id, name, twilio_phone, owner_phone, email, address, city, custom_prompt, is_active, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            restaurant.id, restaurant.name, restaurant.twilio_phone,
            restaurant.owner_phone, restaurant.email, restaurant.address,
            restaurant.city, restaurant.custom_prompt, restaurant.is_active,
            restaurant.created_at
        ))
        
        conn.commit()
        conn.close()
    
    def get_restaurant_by_phone(self, twilio_phone: str) -> Optional[Restaurant]:
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM restaurants WHERE twilio_phone = ? AND is_active = 1", (twilio_phone,))
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
        
        return Restaurant(
            id=row['id'],
            name=row['name'],
            twilio_phone=row['twilio_phone'],
            owner_phone=row['owner_phone'],
            email=row['email'],
            address=row['address'],
            city=row['city'],
            custom_prompt=row['custom_prompt'],
            is_active=bool(row['is_active']),
            created_at=datetime.fromisoformat(row['created_at'])
        )
    
    # ===== MENU =====
    
    def add_menu_item(self, item: MenuItem):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO menu_items (id, restaurant_id, name, category, sizes, description, available)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            item.id, item.restaurant_id, item.name, item.category,
            json.dumps(item.sizes.dict()), item.description, item.available
        ))
        
        conn.commit()
        conn.close()
    
    def get_menu(self, restaurant_id: str) -> List[MenuItem]:
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM menu_items WHERE restaurant_id = ? AND available = 1", (restaurant_id,))
        rows = cursor.fetchall()
        conn.close()
        
        menu = []
        for row in rows:
            sizes_dict = json.loads(row['sizes'])
            menu.append(MenuItem(
                id=row['id'],
                restaurant_id=row['restaurant_id'],
                name=row['name'],
                category=row['category'],
                sizes=sizes_dict,
                description=row['description'],
                available=bool(row['available'])
            ))
        
        return menu
    
    # ===== DELIVERY ZONES =====
    
    def add_delivery_zone(self, zone: DeliveryZone):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO delivery_zones (id, restaurant_id, city, postal_code, streets, min_order_amount, delivery_fee)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            zone.id, zone.restaurant_id, zone.city, zone.postal_code,
            json.dumps(zone.streets), zone.min_order_amount, zone.delivery_fee
        ))
        
        conn.commit()
        conn.close()
    
    def get_delivery_zones(self, restaurant_id: str) -> List[DeliveryZone]:
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM delivery_zones WHERE restaurant_id = ?", (restaurant_id,))
        rows = cursor.fetchall()
        conn.close()
        
        zones = []
        for row in rows:
            zones.append(DeliveryZone(
                id=row['id'],
                restaurant_id=row['restaurant_id'],
                city=row['city'],
                postal_code=row['postal_code'],
                streets=json.loads(row['streets']),
                min_order_amount=row['min_order_amount'],
                delivery_fee=row['delivery_fee']
            ))
        
        return zones
    
    # ===== OPENING HOURS =====
    
    def add_opening_hour(self, hour: OpeningHour):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO opening_hours (id, restaurant_id, day_of_week, open_time, close_time, is_closed)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            hour.id, hour.restaurant_id, hour.day_of_week,
            hour.open_time.isoformat(), hour.close_time.isoformat(), hour.is_closed
        ))
        
        conn.commit()
        conn.close()
    
    def get_opening_hours(self, restaurant_id: str) -> List[OpeningHour]:
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM opening_hours WHERE restaurant_id = ?", (restaurant_id,))
        rows = cursor.fetchall()
        conn.close()
        
        hours = []
        for row in rows:
            hours.append(OpeningHour(
                id=row['id'],
                restaurant_id=row['restaurant_id'],
                day_of_week=row['day_of_week'],
                open_time=time.fromisoformat(row['open_time']),
                close_time=time.fromisoformat(row['close_time']),
                is_closed=bool(row['is_closed'])
            ))
        
        return hours
    
    # ===== ORDERS =====
    
    def create_order(self, order: Order):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO orders 
            (id, restaurant_id, call_sid, customer_phone, customer_name, order_type, items, total_amount, delivery_address, status, created_at, conversation_transcript)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            order.id, order.restaurant_id, order.call_sid, order.customer_phone,
            order.customer_name, order.order_type.value,
            json.dumps([item.dict() for item in order.items]),
            order.total_amount,
            json.dumps(order.delivery_address.dict()) if order.delivery_address else None,
            order.status.value, order.created_at,
            json.dumps(order.conversation_transcript) if order.conversation_transcript else None
        ))
        
        conn.commit()
        conn.close()
    
    # ===== SMS LOGS =====
    
    def log_sms(self, log: SMSLog):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO sms_logs (id, order_id, recipient, message, status, sent_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (log.id, log.order_id, log.recipient, log.message, log.status, log.sent_at))
        
        conn.commit()
        conn.close()

# Instance globale
db = Database()
