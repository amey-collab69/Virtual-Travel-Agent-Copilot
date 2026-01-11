"""
TravelEase - Complete Python Travel Agent Application
Modern UI with CustomTkinter, SQLite Database, Google Maps Integration
"""
import customtkinter as ctk
from tkinter import messagebox
import tkinter as tk
import sqlite3
import math
import requests
import hashlib
from datetime import datetime, timedelta
import os

# Set appearance
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

# ============== DATABASE SETUP ==============
class Database:
    def __init__(self):
        self.conn = sqlite3.connect('travel_agent.db', check_same_thread=False)
        self.create_tables()
        self.seed_data()
    
    def create_tables(self):
        cursor = self.conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, email TEXT UNIQUE NOT NULL,
            phone TEXT, password TEXT NOT NULL, points INTEGER DEFAULT 100, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, booking_type TEXT, origin TEXT, destination TEXT,
            travelers INTEGER, total_cost REAL, status TEXT DEFAULT 'confirmed', created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id))''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS locations (
            id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE, lat REAL, lng REAL, country TEXT, region TEXT, airport_code TEXT)''')
        self.conn.commit()
    
    def seed_data(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM locations")
        if cursor.fetchone()[0] == 0:
            locations = [
                ("Mumbai", 19.0760, 72.8777, "India", "south_asia", "BOM"), ("Delhi", 28.6139, 77.2090, "India", "south_asia", "DEL"),
                ("Bangalore", 12.9716, 77.5946, "India", "south_asia", "BLR"), ("Chennai", 13.0827, 80.2707, "India", "south_asia", "MAA"),
                ("Kolkata", 22.5726, 88.3639, "India", "south_asia", "CCU"), ("Hyderabad", 17.3850, 78.4867, "India", "south_asia", "HYD"),
                ("Pune", 18.5204, 73.8567, "India", "south_asia", "PNQ"), ("Jaipur", 26.9124, 75.7873, "India", "south_asia", "JAI"),
                ("Goa", 15.2993, 74.1240, "India", "south_asia", "GOI"), ("Agra", 27.1767, 78.0081, "India", "south_asia", "AGR"),
                ("Varanasi", 25.3176, 82.9739, "India", "south_asia", "VNS"), ("Udaipur", 24.5854, 73.7125, "India", "south_asia", "UDR"),
                ("Manali", 32.2396, 77.1887, "India", "south_asia", "KUU"), ("Shimla", 31.1048, 77.1734, "India", "south_asia", "SLV"),
                ("Rishikesh", 30.0869, 78.2676, "India", "south_asia", "DED"), ("Darjeeling", 27.0410, 88.2663, "India", "south_asia", "IXB"),
                ("Ooty", 11.4102, 76.6950, "India", "south_asia", "CJB"), ("Ahmedabad", 23.0225, 72.5714, "India", "south_asia", "AMD"),
                ("Lucknow", 26.8467, 80.9462, "India", "south_asia", "LKO"), ("Kochi", 9.9312, 76.2673, "India", "south_asia", "COK"),
                ("Amritsar", 31.6340, 74.8723, "India", "south_asia", "ATQ"), ("Srinagar", 34.0837, 74.7973, "India", "south_asia", "SXR"),
                ("Paris", 48.8566, 2.3522, "France", "western_europe", "CDG"), ("London", 51.5074, -0.1278, "UK", "western_europe", "LHR"),
                ("New York", 40.7128, -74.0060, "USA", "north_america", "JFK"), ("Tokyo", 35.6762, 139.6503, "Japan", "east_asia", "NRT"),
                ("Dubai", 25.2048, 55.2708, "UAE", "middle_east", "DXB"), ("Singapore", 1.3521, 103.8198, "Singapore", "southeast_asia", "SIN"),
                ("Bangkok", 13.7563, 100.5018, "Thailand", "southeast_asia", "BKK"), ("Bali", -8.4095, 115.1889, "Indonesia", "southeast_asia", "DPS"),
                ("Sydney", -33.8688, 151.2093, "Australia", "australia", "SYD"), ("Rome", 41.9028, 12.4964, "Italy", "western_europe", "FCO"),
                ("Maldives", 3.2028, 73.2207, "Maldives", "south_asia", "MLE"), ("Phuket", 7.8804, 98.3923, "Thailand", "southeast_asia", "HKT"),
            ]
            cursor.executemany("INSERT OR IGNORE INTO locations (name, lat, lng, country, region, airport_code) VALUES (?, ?, ?, ?, ?, ?)", locations)
            self.conn.commit()
    
    def get_user(self, email, password):
        cursor = self.conn.cursor()
        pwd_hash = hashlib.sha256(password.encode()).hexdigest()
        cursor.execute("SELECT * FROM users WHERE email=? AND password=?", (email, pwd_hash))
        return cursor.fetchone()
    
    def create_user(self, name, email, phone, password):
        cursor = self.conn.cursor()
        pwd_hash = hashlib.sha256(password.encode()).hexdigest()
        try:
            cursor.execute("INSERT INTO users (name, email, phone, password) VALUES (?, ?, ?, ?)", (name, email, phone, pwd_hash))
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
    
    def get_location(self, name):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM locations WHERE LOWER(name) LIKE ?", (f"%{name.lower()}%",))
        return cursor.fetchone()
    
    def search_locations(self, query):
        cursor = self.conn.cursor()
        cursor.execute("SELECT name, country, airport_code FROM locations WHERE LOWER(name) LIKE ? OR LOWER(airport_code) LIKE ? ORDER BY name LIMIT 6", 
                      (f"{query.lower()}%", f"{query.lower()}%"))
        return cursor.fetchall()
    
    def add_booking(self, user_id, booking_type, origin, dest, travelers, cost):
        cursor = self.conn.cursor()
        cursor.execute("INSERT INTO bookings (user_id, booking_type, origin, destination, travelers, total_cost) VALUES (?, ?, ?, ?, ?, ?)",
                      (user_id, booking_type, origin, dest, travelers, cost))
        self.conn.commit()
    
    def get_user_bookings(self, user_id):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM bookings WHERE user_id=? ORDER BY created_at DESC", (user_id,))
        return cursor.fetchall()
    
    def update_points(self, user_id, points):
        cursor = self.conn.cursor()
        cursor.execute("UPDATE users SET points = points + ? WHERE id = ?", (points, user_id))
        self.conn.commit()
    
    def get_all_users(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, name, email, phone, points, created_at FROM users ORDER BY created_at DESC")
        return cursor.fetchall()
    
    def get_stats(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM bookings")
        total_bookings = cursor.fetchone()[0]
        cursor.execute("SELECT COALESCE(SUM(total_cost), 0) FROM bookings")
        total_revenue = cursor.fetchone()[0]
        return {"total_users": total_users, "total_bookings": total_bookings, "total_revenue": total_revenue}
    
    def delete_user(self, user_id):
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM bookings WHERE user_id = ?", (user_id,))
        cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
        self.conn.commit()


# ============== LOCATION SERVICE ==============
class LocationService:
    def __init__(self, db):
        self.db = db
    
    def geocode(self, query):
        loc = self.db.get_location(query)
        if loc:
            return {"name": loc[1], "lat": loc[2], "lng": loc[3], "country": loc[4], "code": loc[6] if len(loc) > 6 else ""}
        try:
            url = "https://nominatim.openstreetmap.org/search"
            response = requests.get(url, params={"q": query, "format": "json", "limit": 1}, headers={"User-Agent": "TravelEase/1.0"}, timeout=10)
            data = response.json()
            if data:
                parts = data[0].get("display_name", "").split(", ")
                return {"name": query.title(), "lat": float(data[0]["lat"]), "lng": float(data[0]["lon"]), "country": parts[-1] if parts else "Unknown", "code": ""}
        except:
            pass
        return None
    
    def calculate_distance(self, lat1, lng1, lat2, lng2):
        R = 6371
        lat1_rad, lat2_rad = math.radians(lat1), math.radians(lat2)
        delta_lat, delta_lng = math.radians(lat2 - lat1), math.radians(lng2 - lng1)
        a = math.sin(delta_lat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lng/2)**2
        return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    
    def get_route_info(self, origin, dest):
        origin_loc, dest_loc = self.geocode(origin), self.geocode(dest)
        if not origin_loc or not dest_loc:
            return None
        distance = self.calculate_distance(origin_loc["lat"], origin_loc["lng"], dest_loc["lat"], dest_loc["lng"]) * 1.3
        return {"origin": origin_loc, "destination": dest_loc, "distance_km": round(distance, 1)}


# ============== PRICING ENGINE ==============
class PricingEngine:
    def __init__(self):
        self.cost_index = {"south_asia": 1.0, "southeast_asia": 1.2, "east_asia": 2.5, "middle_east": 2.0, "western_europe": 3.5, "north_america": 3.0, "australia": 3.2}
    
    def get_region(self, country):
        regions = {"south_asia": ["India", "Nepal", "Bangladesh", "Sri Lanka", "Maldives"], "southeast_asia": ["Thailand", "Vietnam", "Indonesia", "Malaysia", "Singapore"],
                   "east_asia": ["Japan", "South Korea"], "middle_east": ["UAE", "Saudi Arabia"], "western_europe": ["UK", "France", "Germany", "Italy"],
                   "north_america": ["USA", "Canada"], "australia": ["Australia", "New Zealand"]}
        for region, countries in regions.items():
            if country in countries:
                return region
        return "south_asia"
    
    def calculate_prices(self, distance, origin_country, dest_country, adults, children, nights):
        travelers = adults + children
        avg_index = (self.cost_index.get(self.get_region(origin_country), 1) + self.cost_index.get(self.get_region(dest_country), 1)) / 2
        is_intl = origin_country != dest_country
        
        flight_base = 5 * distance * avg_index * (1.5 if is_intl else 1)
        flight_eco = max(2500, min(int(flight_base * 0.8), 150000))
        
        trains, buses, cabs = [], [], []
        if not is_intl and distance < 2000:
            train_base = 0.8 * distance * avg_index
            trains = [{"type": "Sleeper", "price": max(250, int(train_base * 0.6))}, {"type": "AC 3-Tier", "price": max(500, int(train_base))},
                     {"type": "AC 2-Tier", "price": max(800, int(train_base * 1.5))}, {"type": "AC First", "price": max(1200, int(train_base * 2.5))}]
        if not is_intl and distance < 1200:
            bus_base = 0.5 * distance * avg_index
            buses = [{"type": "Non-AC Seater", "price": max(200, int(bus_base * 0.5))}, {"type": "AC Seater", "price": max(350, int(bus_base * 0.8))},
                    {"type": "AC Sleeper", "price": max(500, int(bus_base * 1.2))}, {"type": "Volvo Multi-Axle", "price": max(700, int(bus_base * 1.8))}]
        
        cab_base = 14 * distance * self.cost_index.get(self.get_region(dest_country), 1)
        cabs = [{"type": "Sedan (Swift/Etios)", "price": max(800, int(cab_base * 0.7))}, {"type": "SUV (Innova/Ertiga)", "price": max(1200, int(cab_base))},
               {"type": "Luxury (BMW/Audi)", "price": max(3000, int(cab_base * 2.5))}]
        
        dest_idx = self.cost_index.get(self.get_region(dest_country), 1)
        hotels = {"budget": int(900 * dest_idx), "mid": int(3500 * dest_idx), "luxury": int(15000 * dest_idx)}
        
        rooms = max(1, (travelers + 1) // 2)
        packages = []
        cheap = buses[0]["price"] if buses else (trains[0]["price"] if trains else flight_eco)
        packages.append({"name": "💰 Budget Saver", "total": (cheap * travelers * 2) + (hotels["budget"] * nights * rooms) + (600 * nights * travelers), "color": "#10B981"})
        packages.append({"name": "⭐ Comfort Plus", "total": (flight_eco * travelers * 2) + (hotels["mid"] * nights * rooms) + (1800 * nights * travelers), "color": "#0770E3"})
        packages.append({"name": "👑 Premium Luxury", "total": (flight_eco * 2.5 * travelers * 2) + (hotels["luxury"] * nights * rooms) + (5000 * nights * travelers), "color": "#FF6B00"})
        for p in packages:
            p["per_person"] = int(p["total"] // travelers)
            p["total"] = int(p["total"])
        
        return {"flights": [{"type": "Economy", "price": flight_eco}, {"type": "Business", "price": int(flight_eco * 2.5)}],
                "trains": trains, "buses": buses, "cabs": cabs, "hotels": hotels, "packages": packages}


# ============== AUTOCOMPLETE DROPDOWN ==============
class AutocompleteEntry(ctk.CTkFrame):
    def __init__(self, parent, db, placeholder="", colors=None, font_size=24, **kwargs):
        super().__init__(parent, fg_color="transparent")
        self.db = db
        self.placeholder = placeholder
        self.colors = colors
        self.dropdown = None
        
        self.entry = ctk.CTkEntry(self, font=ctk.CTkFont(size=font_size, weight="bold"),
                                 fg_color="transparent", border_width=0, placeholder_text=placeholder,
                                 text_color=colors["text"], width=180)
        self.entry.pack(fill="x")
        self.entry.bind("<KeyRelease>", self.on_key)
        self.entry.bind("<FocusOut>", lambda e: self.after(200, self.hide_dropdown))
    
    def on_key(self, event):
        if event.keysym in ("Up", "Down", "Return", "Escape"):
            return
        query = self.entry.get().strip()
        if query:
            # Auto capitalize
            pos = self.entry.index(ctk.INSERT)
            self.entry.delete(0, "end")
            self.entry.insert(0, query.title())
            self.entry.icursor(pos)
        if len(query) >= 1:
            results = self.db.search_locations(query)
            if results:
                self.show_dropdown(results)
            else:
                self.hide_dropdown()
        else:
            self.hide_dropdown()
    
    def show_dropdown(self, results):
        self.hide_dropdown()
        self.dropdown = ctk.CTkToplevel(self)
        self.dropdown.wm_overrideredirect(True)
        self.dropdown.attributes("-topmost", True)
        x, y = self.entry.winfo_rootx(), self.entry.winfo_rooty() + self.entry.winfo_height()
        self.dropdown.geometry(f"280x{min(len(results)*45, 270)}+{x}+{y}")
        
        for name, country, code in results:
            btn = ctk.CTkButton(self.dropdown, text=f"{name} [{code}], {country}", anchor="w",
                               font=ctk.CTkFont(size=12), fg_color=self.colors["white"],
                               text_color=self.colors["text"], hover_color=self.colors["light_blue"],
                               corner_radius=0, height=45,
                               command=lambda n=name: self.select(n))
            btn.pack(fill="x")
    
    def select(self, name):
        self.entry.delete(0, "end")
        self.entry.insert(0, name)
        self.hide_dropdown()
    
    def hide_dropdown(self):
        if self.dropdown:
            self.dropdown.destroy()
            self.dropdown = None
    
    def get(self):
        return self.entry.get()
    
    def delete(self, start, end):
        self.entry.delete(start, end)
    
    def insert(self, idx, text):
        self.entry.insert(idx, text)


# ============== MAIN APPLICATION ==============
class TravelEaseApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("TravelEase - Your Travel Companion")
        self.geometry("1300x850")
        self.minsize(1100, 700)
        
        self.db = Database()
        self.location_service = LocationService(self.db)
        self.pricing = PricingEngine()
        self.current_user = None
        
        self.colors = {"primary": "#0770E3", "secondary": "#FF6B00", "accent": "#00A651",
                      "dark": "#1A1A2E", "light_blue": "#E8F4FD", "white": "#FFFFFF",
                      "gray": "#F5F5F5", "text": "#1A1A2E", "text_light": "#666666"}
        
        self.trip_type = ctk.StringVar(value="oneway")
        self.adults_var = ctk.IntVar(value=1)
        self.children_var = ctk.IntVar(value=0)
        self.nights_var = ctk.IntVar(value=3)
        self.dep_date = datetime.now() + timedelta(days=7)
        self.ret_date = None
        
        self.configure(fg_color=self.colors["gray"])
        self.build_ui()
    
    def build_ui(self):
        self.build_header()
        self.content = ctk.CTkScrollableFrame(self, fg_color=self.colors["gray"])
        self.content.pack(fill="both", expand=True)
        self.show_tab_search()  # Show default tab search
    
    def build_header(self):
        header = ctk.CTkFrame(self, fg_color=self.colors["white"], height=65, corner_radius=0)
        header.pack(fill="x")
        header.pack_propagate(False)
        
        # Logo
        logo = ctk.CTkButton(header, text="✈️ TravelEase", font=ctk.CTkFont(size=22, weight="bold"),
                            fg_color="transparent", text_color=self.colors["primary"],
                            hover_color=self.colors["light_blue"], command=self.show_home)
        logo.pack(side="left", padx=25)
        
        # Nav tabs
        self.nav_frame = ctk.CTkFrame(header, fg_color="transparent")
        self.nav_frame.pack(side="left", padx=20)
        self.tab_buttons = {}
        self.current_tab = "home"
        tabs = [("🏠 Home", "home"), ("✈️ Flights", "flights"), ("🏨 Hotels", "hotels"), ("🚂 Trains", "trains"),
               ("🚌 Buses", "buses"), ("🚕 Cabs", "cabs"), ("🏖️ Holidays", "holidays")]
        for text, tab in tabs:
            btn = ctk.CTkButton(self.nav_frame, text=text, font=ctk.CTkFont(size=11), 
                               fg_color=self.colors["light_blue"] if tab == "flights" else "transparent",
                               text_color=self.colors["primary"] if tab == "flights" else self.colors["text_light"], 
                               hover_color=self.colors["light_blue"],
                               width=75, corner_radius=10, command=lambda t=tab: self.switch_tab(t))
            btn.pack(side="left", padx=2)
            self.tab_buttons[tab] = btn
        
        # Right side
        right = ctk.CTkFrame(header, fg_color="transparent")
        right.pack(side="right", padx=25)
        
        ctk.CTkButton(right, text="🔐 Admin", font=ctk.CTkFont(size=11), fg_color="transparent",
                     text_color=self.colors["text_light"], hover_color=self.colors["light_blue"],
                     width=70, command=self.show_admin_login).pack(side="left", padx=5)
        ctk.CTkButton(right, text="💬 Support", font=ctk.CTkFont(size=11), fg_color="transparent",
                     text_color=self.colors["text_light"], hover_color=self.colors["light_blue"],
                     width=70, command=self.show_support).pack(side="left", padx=5)
        
        self.user_frame = ctk.CTkFrame(right, fg_color="transparent")
        self.user_frame.pack(side="left", padx=10)
        self.update_user_section()
    
    def switch_tab(self, tab):
        self.current_tab = tab
        # Update tab button styles
        for t, btn in self.tab_buttons.items():
            if t == tab:
                btn.configure(fg_color=self.colors["light_blue"], text_color=self.colors["primary"])
            else:
                btn.configure(fg_color="transparent", text_color=self.colors["text_light"])
        # Show appropriate search page
        self.show_tab_search()
    
    def update_user_section(self):
        for w in self.user_frame.winfo_children():
            w.destroy()
        if self.current_user:
            ctk.CTkButton(self.user_frame, text=f"👤 {self.current_user[1].split()[0]}",
                         font=ctk.CTkFont(size=12), fg_color=self.colors["accent"],
                         corner_radius=20, width=100, command=self.show_profile).pack(side="left", padx=3)
            ctk.CTkButton(self.user_frame, text="Logout", font=ctk.CTkFont(size=11),
                         fg_color=self.colors["dark"], corner_radius=20, width=70,
                         command=self.logout).pack(side="left", padx=3)
        else:
            ctk.CTkButton(self.user_frame, text="Login or Signup", font=ctk.CTkFont(size=12, weight="bold"),
                         fg_color=self.colors["secondary"], corner_radius=20, width=130,
                         command=self.show_login).pack()
    
    def clear_content(self):
        for w in self.content.winfo_children():
            w.destroy()
    
    def show_home(self):
        """Show main home page with all options"""
        self.current_tab = "home"
        # Update tab buttons if they exist
        if hasattr(self, 'tab_buttons'):
            for t, btn in self.tab_buttons.items():
                if t == "home":
                    btn.configure(fg_color=self.colors["light_blue"], text_color=self.colors["primary"])
                else:
                    btn.configure(fg_color="transparent", text_color=self.colors["text_light"])
        self.show_tab_search()
    
    def show_tab_search(self):
        """Show search page specific to selected tab"""
        self.clear_content()
        tab = self.current_tab
        
        # Handle Home tab - show everything
        if tab == "home":
            self.show_home_page()
            return
        
        # Tab titles and icons
        tab_info = {
            "flights": ("✈️", "Search Flights", "Find best flight deals"),
            "hotels": ("🏨", "Search Hotels", "Find perfect stay"),
            "trains": ("🚂", "Search Trains", "Book train tickets"),
            "buses": ("🚌", "Search Buses", "Book bus tickets"),
            "cabs": ("🚕", "Book Cabs", "Hire cabs for your trip"),
            "holidays": ("🏖️", "Holiday Packages", "Complete trip packages")
        }
        icon, title, subtitle = tab_info.get(tab, ("🔍", "Search", ""))
        
        # Hero section
        hero = ctk.CTkFrame(self.content, fg_color=self.colors["primary"], corner_radius=0, height=320)
        hero.pack(fill="x")
        hero.pack_propagate(False)
        
        # Search card
        card = ctk.CTkFrame(hero, fg_color=self.colors["white"], corner_radius=20)
        card.pack(padx=40, pady=25, fill="x")
        
        # Title
        title_row = ctk.CTkFrame(card, fg_color="transparent")
        title_row.pack(fill="x", padx=25, pady=(20, 15))
        ctk.CTkLabel(title_row, text=f"{icon} {title}", font=ctk.CTkFont(size=20, weight="bold"),
                    text_color=self.colors["text"]).pack(side="left")
        ctk.CTkLabel(title_row, text=subtitle, font=ctk.CTkFont(size=12),
                    text_color=self.colors["text_light"]).pack(side="left", padx=15)
        
        # Search fields based on tab
        fields = ctk.CTkFrame(card, fg_color="transparent")
        fields.pack(fill="x", padx=15, pady=10)
        
        if tab == "hotels":
            # Hotels: City, Check-in, Check-out, Rooms, Guests
            city_box = ctk.CTkFrame(fields, fg_color=self.colors["gray"], corner_radius=15)
            city_box.pack(side="left", fill="both", expand=True, padx=5)
            ctk.CTkLabel(city_box, text="CITY", font=ctk.CTkFont(size=10, weight="bold"),
                        text_color=self.colors["text_light"]).pack(anchor="w", padx=15, pady=(12, 0))
            self.hotel_city = AutocompleteEntry(city_box, self.db, "Mumbai", self.colors)
            self.hotel_city.pack(anchor="w", padx=15, pady=(0, 12))
            
            checkin_box = ctk.CTkFrame(fields, fg_color=self.colors["gray"], corner_radius=15)
            checkin_box.pack(side="left", fill="y", padx=5)
            ctk.CTkLabel(checkin_box, text="CHECK-IN", font=ctk.CTkFont(size=10, weight="bold"),
                        text_color=self.colors["text_light"]).pack(anchor="w", padx=15, pady=(12, 0))
            self.checkin_lbl = ctk.CTkLabel(checkin_box, text="15 Jan'26", font=ctk.CTkFont(size=18, weight="bold"),
                                           text_color=self.colors["text"])
            self.checkin_lbl.pack(anchor="w", padx=15, pady=(0, 12))
            
            checkout_box = ctk.CTkFrame(fields, fg_color=self.colors["gray"], corner_radius=15)
            checkout_box.pack(side="left", fill="y", padx=5)
            ctk.CTkLabel(checkout_box, text="CHECK-OUT", font=ctk.CTkFont(size=10, weight="bold"),
                        text_color=self.colors["text_light"]).pack(anchor="w", padx=15, pady=(12, 0))
            self.checkout_lbl = ctk.CTkLabel(checkout_box, text="18 Jan'26", font=ctk.CTkFont(size=18, weight="bold"),
                                            text_color=self.colors["text"])
            self.checkout_lbl.pack(anchor="w", padx=15, pady=(0, 12))
            
            rooms_box = ctk.CTkFrame(fields, fg_color=self.colors["gray"], corner_radius=15)
            rooms_box.pack(side="left", fill="y", padx=5)
            ctk.CTkLabel(rooms_box, text="ROOMS & GUESTS", font=ctk.CTkFont(size=10, weight="bold"),
                        text_color=self.colors["text_light"]).pack(anchor="w", padx=15, pady=(12, 0))
            ctk.CTkLabel(rooms_box, text="1 Room, 2 Guests", font=ctk.CTkFont(size=14, weight="bold"),
                        text_color=self.colors["text"]).pack(anchor="w", padx=15, pady=(0, 12))
        
        elif tab == "cabs":
            # Cabs: Pickup, Drop, Date, Time
            pickup_box = ctk.CTkFrame(fields, fg_color=self.colors["gray"], corner_radius=15)
            pickup_box.pack(side="left", fill="both", expand=True, padx=5)
            ctk.CTkLabel(pickup_box, text="PICKUP LOCATION", font=ctk.CTkFont(size=10, weight="bold"),
                        text_color=self.colors["text_light"]).pack(anchor="w", padx=15, pady=(12, 0))
            self.cab_pickup = AutocompleteEntry(pickup_box, self.db, "Delhi", self.colors)
            self.cab_pickup.pack(anchor="w", padx=15, pady=(0, 12))
            
            drop_box = ctk.CTkFrame(fields, fg_color=self.colors["gray"], corner_radius=15)
            drop_box.pack(side="left", fill="both", expand=True, padx=5)
            ctk.CTkLabel(drop_box, text="DROP LOCATION", font=ctk.CTkFont(size=10, weight="bold"),
                        text_color=self.colors["text_light"]).pack(anchor="w", padx=15, pady=(12, 0))
            self.cab_drop = AutocompleteEntry(drop_box, self.db, "Agra", self.colors)
            self.cab_drop.pack(anchor="w", padx=15, pady=(0, 12))
            
            date_box = ctk.CTkFrame(fields, fg_color=self.colors["gray"], corner_radius=15)
            date_box.pack(side="left", fill="y", padx=5)
            ctk.CTkLabel(date_box, text="PICKUP DATE", font=ctk.CTkFont(size=10, weight="bold"),
                        text_color=self.colors["text_light"]).pack(anchor="w", padx=15, pady=(12, 0))
            ctk.CTkLabel(date_box, text="15 Jan'26", font=ctk.CTkFont(size=18, weight="bold"),
                        text_color=self.colors["text"]).pack(anchor="w", padx=15, pady=(0, 12))
            
            time_box = ctk.CTkFrame(fields, fg_color=self.colors["gray"], corner_radius=15)
            time_box.pack(side="left", fill="y", padx=5)
            ctk.CTkLabel(time_box, text="PICKUP TIME", font=ctk.CTkFont(size=10, weight="bold"),
                        text_color=self.colors["text_light"]).pack(anchor="w", padx=15, pady=(12, 0))
            ctk.CTkLabel(time_box, text="10:00 AM", font=ctk.CTkFont(size=18, weight="bold"),
                        text_color=self.colors["text"]).pack(anchor="w", padx=15, pady=(0, 12))
        
        else:
            # Flights/Trains/Buses/Holidays: FROM, TO, Date, Travellers
            if tab in ["flights", "trains", "buses", "holidays"]:
                # Trip type for flights
                if tab == "flights":
                    trip_row = ctk.CTkFrame(card, fg_color="transparent")
                    trip_row.pack(fill="x", padx=25, pady=(0, 10))
                    ctk.CTkRadioButton(trip_row, text="One Way", variable=self.trip_type, value="oneway",
                                      font=ctk.CTkFont(size=12), fg_color=self.colors["primary"]).pack(side="left", padx=8)
                    ctk.CTkRadioButton(trip_row, text="Round Trip", variable=self.trip_type, value="round",
                                      font=ctk.CTkFont(size=12), fg_color=self.colors["primary"]).pack(side="left", padx=8)
                    fields.pack_forget()
                    fields = ctk.CTkFrame(card, fg_color="transparent")
                    fields.pack(fill="x", padx=15, pady=10)
            
            # FROM
            from_box = ctk.CTkFrame(fields, fg_color=self.colors["gray"], corner_radius=15)
            from_box.pack(side="left", fill="both", expand=True, padx=5)
            ctk.CTkLabel(from_box, text="FROM", font=ctk.CTkFont(size=10, weight="bold"),
                        text_color=self.colors["text_light"]).pack(anchor="w", padx=15, pady=(12, 0))
            self.tab_from = AutocompleteEntry(from_box, self.db, "Delhi", self.colors)
            self.tab_from.pack(anchor="w", padx=15, pady=(0, 12))
            
            # Swap
            ctk.CTkButton(fields, text="⇄", font=ctk.CTkFont(size=14), fg_color=self.colors["primary"],
                         width=35, height=35, corner_radius=18, command=self.swap_tab_cities).pack(side="left", padx=3)
            
            # TO
            to_box = ctk.CTkFrame(fields, fg_color=self.colors["gray"], corner_radius=15)
            to_box.pack(side="left", fill="both", expand=True, padx=5)
            ctk.CTkLabel(to_box, text="TO", font=ctk.CTkFont(size=10, weight="bold"),
                        text_color=self.colors["text_light"]).pack(anchor="w", padx=15, pady=(12, 0))
            self.tab_to = AutocompleteEntry(to_box, self.db, "Mumbai", self.colors)
            self.tab_to.pack(anchor="w", padx=15, pady=(0, 12))
            
            # Date
            date_box = ctk.CTkFrame(fields, fg_color=self.colors["gray"], corner_radius=15, cursor="hand2")
            date_box.pack(side="left", fill="y", padx=5)
            date_label = "DEPARTURE" if tab in ["flights", "trains", "buses"] else "TRAVEL DATE"
            ctk.CTkLabel(date_box, text=date_label, font=ctk.CTkFont(size=10, weight="bold"),
                        text_color=self.colors["text_light"]).pack(anchor="w", padx=15, pady=(12, 0))
            self.date_lbl = ctk.CTkLabel(date_box, text=self.dep_date.strftime("%d %b'%y"), 
                                        font=ctk.CTkFont(size=18, weight="bold"),
                                        text_color=self.colors["text"])
            self.date_lbl.pack(anchor="w", padx=15, pady=(0, 12))
            date_box.bind("<Button-1>", lambda e: self.pick_date())
            for child in date_box.winfo_children():
                child.bind("<Button-1>", lambda e: self.pick_date())
            
            # Travellers
            trav_box = ctk.CTkFrame(fields, fg_color=self.colors["gray"], corner_radius=15, cursor="hand2")
            trav_box.pack(side="left", fill="y", padx=5)
            ctk.CTkLabel(trav_box, text="TRAVELLERS", font=ctk.CTkFont(size=10, weight="bold"),
                        text_color=self.colors["text_light"]).pack(anchor="w", padx=15, pady=(12, 0))
            self.tab_trav_lbl = ctk.CTkLabel(trav_box, text=str(self.adults_var.get() + self.children_var.get()),
                                            font=ctk.CTkFont(size=18, weight="bold"), text_color=self.colors["text"])
            self.tab_trav_lbl.pack(anchor="w", padx=15, pady=(0, 12))
            trav_box.bind("<Button-1>", lambda e: self.pick_travellers())
            for child in trav_box.winfo_children():
                child.bind("<Button-1>", lambda e: self.pick_travellers())
        
        # Search button
        ctk.CTkButton(card, text=f"SEARCH {title.upper().split()[-1]}", font=ctk.CTkFont(size=14, weight="bold"),
                     fg_color=self.colors["secondary"], hover_color="#E55A00",
                     corner_radius=25, width=200, height=45, command=self.search_tab).pack(pady=18)
        
        # Popular routes section
        pop_frame = ctk.CTkFrame(self.content, fg_color="transparent")
        pop_frame.pack(fill="x", padx=40, pady=(10, 15))
        ctk.CTkLabel(pop_frame, text="🔥 Popular Routes", font=ctk.CTkFont(size=16, weight="bold"),
                    text_color=self.colors["text"]).pack(anchor="w", pady=(0, 12))
        
        routes_row = ctk.CTkFrame(pop_frame, fg_color="transparent")
        routes_row.pack(fill="x")
        
        popular = [("Delhi", "Mumbai", "₹4,299"), ("Mumbai", "Goa", "₹3,599"),
                  ("Bangalore", "Delhi", "₹5,199"), ("Delhi", "Dubai", "₹15,999"),
                  ("Chennai", "Hyderabad", "₹2,899"), ("Kolkata", "Delhi", "₹4,599")]
        
        for orig, dest, price in popular[:4]:
            c = ctk.CTkFrame(routes_row, fg_color=self.colors["white"], corner_radius=12, cursor="hand2")
            c.pack(side="left", fill="both", expand=True, padx=6)
            ctk.CTkLabel(c, text=f"{orig} → {dest}", font=ctk.CTkFont(size=13, weight="bold"),
                        text_color=self.colors["text"]).pack(pady=(15, 4))
            ctk.CTkLabel(c, text=f"Starting {price}", font=ctk.CTkFont(size=11),
                        text_color=self.colors["accent"]).pack(pady=(0, 15))
            c.bind("<Button-1>", lambda e, o=orig, d=dest: self.quick_tab_search(o, d))
        
        # Offers section
        offers_frame = ctk.CTkFrame(self.content, fg_color="transparent")
        offers_frame.pack(fill="x", padx=40, pady=15)
        ctk.CTkLabel(offers_frame, text="🎉 Exclusive Offers", font=ctk.CTkFont(size=16, weight="bold"),
                    text_color=self.colors["text"]).pack(anchor="w", pady=(0, 12))
        
        offers_row = ctk.CTkFrame(offers_frame, fg_color="transparent")
        offers_row.pack(fill="x")
        
        offers = [("🏖️ Goa Package", "3N/4D from ₹8,999", "GOA30", "30% OFF"),
                 ("🏔️ Manali Trip", "4N/5D from ₹12,999", "MANALI25", "25% OFF"),
                 ("✈️ Dubai Flights", "From ₹15,999", "FLY20", "20% OFF"),
                 ("🏨 Hotel Deals", "Flat ₹1000 Off", "HOTEL1K", "₹1000 OFF")]
        
        for title_txt, desc, code, off in offers:
            c = ctk.CTkFrame(offers_row, fg_color=self.colors["white"], corner_radius=12)
            c.pack(side="left", fill="both", expand=True, padx=6)
            ctk.CTkLabel(c, text=off, font=ctk.CTkFont(size=10, weight="bold"),
                        fg_color=self.colors["secondary"], text_color=self.colors["white"],
                        corner_radius=6).pack(anchor="ne", padx=8, pady=8)
            ctk.CTkLabel(c, text=title_txt, font=ctk.CTkFont(size=13, weight="bold"),
                        text_color=self.colors["text"]).pack(anchor="w", padx=12)
            ctk.CTkLabel(c, text=desc, font=ctk.CTkFont(size=11),
                        text_color=self.colors["primary"]).pack(anchor="w", padx=12, pady=2)
            ctk.CTkLabel(c, text=f"Code: {code}", font=ctk.CTkFont(size=10, weight="bold"),
                        text_color=self.colors["text_light"]).pack(anchor="w", padx=12, pady=(0, 12))
        
        # Results area
        self.tab_results = ctk.CTkFrame(self.content, fg_color="transparent")
        self.tab_results.pack(fill="both", expand=True, padx=40, pady=10)
    
    def quick_tab_search(self, orig, dest):
        """Quick search from popular routes"""
        if hasattr(self, 'tab_from') and hasattr(self, 'tab_to'):
            self.tab_from.delete(0, "end")
            self.tab_from.insert(0, orig)
            self.tab_to.delete(0, "end")
            self.tab_to.insert(0, dest)
            self.search_tab()
        elif hasattr(self, 'cab_pickup') and hasattr(self, 'cab_drop'):
            self.cab_pickup.delete(0, "end")
            self.cab_pickup.insert(0, orig)
            self.cab_drop.delete(0, "end")
            self.cab_drop.insert(0, dest)
            self.search_tab()
        elif hasattr(self, 'hotel_city'):
            self.hotel_city.delete(0, "end")
            self.hotel_city.insert(0, dest)
            self.search_tab()
    
    def show_home_page(self):
        """Show home page with all services"""
        self.clear_content()
        
        # Hero banner
        hero = ctk.CTkFrame(self.content, fg_color=self.colors["primary"], corner_radius=0, height=200)
        hero.pack(fill="x")
        hero.pack_propagate(False)
        
        hero_content = ctk.CTkFrame(hero, fg_color="transparent")
        hero_content.pack(expand=True)
        ctk.CTkLabel(hero_content, text="✈️ Welcome to TravelEase", font=ctk.CTkFont(size=32, weight="bold"),
                    text_color=self.colors["white"]).pack(pady=(30, 10))
        ctk.CTkLabel(hero_content, text="Book Flights, Hotels, Trains, Buses & Cabs - All in One Place!",
                    font=ctk.CTkFont(size=14), text_color=self.colors["white"]).pack()
        
        # Quick search bar
        search_bar = ctk.CTkFrame(hero_content, fg_color=self.colors["white"], corner_radius=25)
        search_bar.pack(pady=20)
        self.home_search = ctk.CTkEntry(search_bar, font=ctk.CTkFont(size=13), fg_color="transparent",
                                        border_width=0, width=400, height=45,
                                        placeholder_text="Where do you want to go? (e.g., Goa, Dubai, Manali)")
        self.home_search.pack(side="left", padx=20)
        ctk.CTkButton(search_bar, text="🔍 Search", font=ctk.CTkFont(size=12, weight="bold"),
                     fg_color=self.colors["secondary"], corner_radius=20, width=100, height=35,
                     command=self.home_quick_search).pack(side="right", padx=10, pady=5)
        
        # Services section
        services_frame = ctk.CTkFrame(self.content, fg_color="transparent")
        services_frame.pack(fill="x", padx=40, pady=25)
        ctk.CTkLabel(services_frame, text="🚀 Our Services", font=ctk.CTkFont(size=18, weight="bold"),
                    text_color=self.colors["text"]).pack(anchor="w", pady=(0, 15))
        
        services_row = ctk.CTkFrame(services_frame, fg_color="transparent")
        services_row.pack(fill="x")
        
        services = [("✈️", "Flights", "flights", "Book domestic & international flights"),
                   ("🏨", "Hotels", "hotels", "Find best hotels & resorts"),
                   ("🚂", "Trains", "trains", "Book train tickets easily"),
                   ("🚌", "Buses", "buses", "AC, Sleeper & Volvo buses"),
                   ("🚕", "Cabs", "cabs", "Local & outstation cabs"),
                   ("🏖️", "Holidays", "holidays", "Complete holiday packages")]
        
        for icon, name, tab, desc in services:
            c = ctk.CTkFrame(services_row, fg_color=self.colors["white"], corner_radius=15, cursor="hand2")
            c.pack(side="left", fill="both", expand=True, padx=6)
            ctk.CTkLabel(c, text=icon, font=ctk.CTkFont(size=28)).pack(pady=(18, 5))
            ctk.CTkLabel(c, text=name, font=ctk.CTkFont(size=14, weight="bold"),
                        text_color=self.colors["text"]).pack()
            ctk.CTkLabel(c, text=desc, font=ctk.CTkFont(size=10),
                        text_color=self.colors["text_light"], wraplength=100).pack(pady=(3, 18))
            c.bind("<Button-1>", lambda e, t=tab: self.switch_tab(t))
            for child in c.winfo_children():
                child.bind("<Button-1>", lambda e, t=tab: self.switch_tab(t))
        
        # Popular destinations
        dest_frame = ctk.CTkFrame(self.content, fg_color="transparent")
        dest_frame.pack(fill="x", padx=40, pady=15)
        ctk.CTkLabel(dest_frame, text="🌍 Popular Destinations", font=ctk.CTkFont(size=18, weight="bold"),
                    text_color=self.colors["text"]).pack(anchor="w", pady=(0, 15))
        
        dest_row = ctk.CTkFrame(dest_frame, fg_color="transparent")
        dest_row.pack(fill="x")
        
        destinations = [("Goa", "🏖️", "Beaches & Nightlife", "₹8,999"),
                       ("Manali", "🏔️", "Mountains & Snow", "₹12,999"),
                       ("Dubai", "🏙️", "Shopping & Luxury", "₹35,999"),
                       ("Jaipur", "🏰", "Heritage & Culture", "₹6,999"),
                       ("Kerala", "🌴", "Backwaters & Nature", "₹15,999")]
        
        for city, icon, desc, price in destinations:
            c = ctk.CTkFrame(dest_row, fg_color=self.colors["white"], corner_radius=15, cursor="hand2")
            c.pack(side="left", fill="both", expand=True, padx=6)
            ctk.CTkLabel(c, text=icon, font=ctk.CTkFont(size=24)).pack(pady=(15, 5))
            ctk.CTkLabel(c, text=city, font=ctk.CTkFont(size=14, weight="bold"),
                        text_color=self.colors["text"]).pack()
            ctk.CTkLabel(c, text=desc, font=ctk.CTkFont(size=10),
                        text_color=self.colors["text_light"]).pack()
            ctk.CTkLabel(c, text=f"From {price}", font=ctk.CTkFont(size=11, weight="bold"),
                        text_color=self.colors["accent"]).pack(pady=(5, 15))
            c.bind("<Button-1>", lambda e, ct=city: self.search_destination(ct))
            for child in c.winfo_children():
                child.bind("<Button-1>", lambda e, ct=city: self.search_destination(ct))
        
        # Popular routes
        routes_frame = ctk.CTkFrame(self.content, fg_color="transparent")
        routes_frame.pack(fill="x", padx=40, pady=15)
        ctk.CTkLabel(routes_frame, text="🔥 Popular Flight Routes", font=ctk.CTkFont(size=18, weight="bold"),
                    text_color=self.colors["text"]).pack(anchor="w", pady=(0, 15))
        
        routes_row = ctk.CTkFrame(routes_frame, fg_color="transparent")
        routes_row.pack(fill="x")
        
        routes = [("Delhi", "Mumbai", "₹4,299"), ("Mumbai", "Goa", "₹3,599"),
                 ("Bangalore", "Delhi", "₹5,199"), ("Chennai", "Kolkata", "₹4,899"),
                 ("Delhi", "Dubai", "₹15,999"), ("Mumbai", "Singapore", "₹18,999")]
        
        for orig, dest, price in routes:
            c = ctk.CTkFrame(routes_row, fg_color=self.colors["white"], corner_radius=12, cursor="hand2")
            c.pack(side="left", fill="both", expand=True, padx=5)
            ctk.CTkLabel(c, text=f"{orig} → {dest}", font=ctk.CTkFont(size=12, weight="bold"),
                        text_color=self.colors["text"]).pack(pady=(12, 3))
            ctk.CTkLabel(c, text=f"From {price}", font=ctk.CTkFont(size=11),
                        text_color=self.colors["accent"]).pack(pady=(0, 12))
            c.bind("<Button-1>", lambda e, o=orig, d=dest: self.search_route(o, d))
            for child in c.winfo_children():
                child.bind("<Button-1>", lambda e, o=orig, d=dest: self.search_route(o, d))
        
        # Offers
        offers_frame = ctk.CTkFrame(self.content, fg_color="transparent")
        offers_frame.pack(fill="x", padx=40, pady=15)
        ctk.CTkLabel(offers_frame, text="🎉 Today's Best Offers", font=ctk.CTkFont(size=18, weight="bold"),
                    text_color=self.colors["text"]).pack(anchor="w", pady=(0, 15))
        
        offers_row = ctk.CTkFrame(offers_frame, fg_color="transparent")
        offers_row.pack(fill="x")
        
        offers = [("✈️ Flight Sale", "Flat 20% OFF", "FLY20", self.colors["primary"]),
                 ("🏨 Hotel Deals", "₹1000 OFF", "HOTEL1K", self.colors["secondary"]),
                 ("🚂 Train Tickets", "No Booking Fee", "TRAIN0", self.colors["accent"]),
                 ("🏖️ Holiday Packages", "Up to 40% OFF", "HOLIDAY40", "#9333EA")]
        
        for title, offer, code, color in offers:
            c = ctk.CTkFrame(offers_row, fg_color=color, corner_radius=15, cursor="hand2")
            c.pack(side="left", fill="both", expand=True, padx=6)
            ctk.CTkLabel(c, text=title, font=ctk.CTkFont(size=13, weight="bold"),
                        text_color=self.colors["white"]).pack(pady=(15, 3))
            ctk.CTkLabel(c, text=offer, font=ctk.CTkFont(size=16, weight="bold"),
                        text_color=self.colors["white"]).pack()
            ctk.CTkLabel(c, text=f"Use Code: {code}", font=ctk.CTkFont(size=10),
                        text_color=self.colors["white"]).pack(pady=(3, 15))
    
    def home_quick_search(self):
        """Quick search from home page"""
        query = self.home_search.get().strip()
        if query:
            self.search_destination(query)
    
    def search_destination(self, city):
        """Search for a destination - go to holidays tab"""
        self.current_tab = "holidays"
        if hasattr(self, 'tab_buttons'):
            for t, btn in self.tab_buttons.items():
                btn.configure(fg_color=self.colors["light_blue"] if t == "holidays" else "transparent",
                             text_color=self.colors["primary"] if t == "holidays" else self.colors["text_light"])
        self.show_tab_search()
        if hasattr(self, 'tab_from'):
            self.tab_from.delete(0, "end")
            self.tab_from.insert(0, "Delhi")
        if hasattr(self, 'tab_to'):
            self.tab_to.delete(0, "end")
            self.tab_to.insert(0, city)
    
    def search_route(self, orig, dest):
        """Search for a route - go to flights tab"""
        self.current_tab = "flights"
        if hasattr(self, 'tab_buttons'):
            for t, btn in self.tab_buttons.items():
                btn.configure(fg_color=self.colors["light_blue"] if t == "flights" else "transparent",
                             text_color=self.colors["primary"] if t == "flights" else self.colors["text_light"])
        self.show_tab_search()
        if hasattr(self, 'tab_from'):
            self.tab_from.delete(0, "end")
            self.tab_from.insert(0, orig)
        if hasattr(self, 'tab_to'):
            self.tab_to.delete(0, "end")
            self.tab_to.insert(0, dest)
    
    def swap_tab_cities(self):
        if hasattr(self, 'tab_from') and hasattr(self, 'tab_to'):
            f, t = self.tab_from.get(), self.tab_to.get()
            self.tab_from.delete(0, "end")
            self.tab_to.delete(0, "end")
            self.tab_from.insert(0, t)
            self.tab_to.insert(0, f)
    
    def search_tab(self):
        """Search based on current tab"""
        tab = self.current_tab
        
        if tab == "hotels":
            city = self.hotel_city.get().strip()
            if not city:
                messagebox.showerror("Error", "Enter city name")
                return
            self.show_hotel_results(city)
        
        elif tab == "cabs":
            pickup = self.cab_pickup.get().strip()
            drop = self.cab_drop.get().strip()
            if not pickup or not drop:
                messagebox.showerror("Error", "Enter pickup and drop locations")
                return
            self.show_cab_results(pickup, drop)
        
        else:
            # Flights, Trains, Buses, Holidays
            orig = self.tab_from.get().strip()
            dest = self.tab_to.get().strip()
            if not orig or not dest:
                messagebox.showerror("Error", "Enter origin and destination")
                return
            
            route = self.location_service.get_route_info(orig, dest)
            if not route:
                messagebox.showerror("Error", f"Could not find: {orig} or {dest}")
                return
            
            prices = self.pricing.calculate_prices(route["distance_km"], route["origin"]["country"],
                                                   route["destination"]["country"], 
                                                   self.adults_var.get(), self.children_var.get(), 3)
            
            if tab == "flights":
                self.show_flight_results(route, prices)
            elif tab == "trains":
                self.show_train_results(route, prices)
            elif tab == "buses":
                self.show_bus_results(route, prices)
            else:
                self.show_results(route, prices, self.adults_var.get() + self.children_var.get(), 3)
        self.clear_content()
        
        # Hero with search
        hero = ctk.CTkFrame(self.content, fg_color=self.colors["primary"], corner_radius=0, height=380)
        hero.pack(fill="x")
        hero.pack_propagate(False)
        
        # Search card
        card = ctk.CTkFrame(hero, fg_color=self.colors["white"], corner_radius=20)
        card.pack(padx=40, pady=25, fill="x")
        
        # Trip type row
        trip_row = ctk.CTkFrame(card, fg_color="transparent")
        trip_row.pack(fill="x", padx=25, pady=(20, 10))
        
        ctk.CTkRadioButton(trip_row, text="One Way", variable=self.trip_type, value="oneway",
                          font=ctk.CTkFont(size=13), fg_color=self.colors["primary"]).pack(side="left", padx=10)
        ctk.CTkRadioButton(trip_row, text="Round Trip", variable=self.trip_type, value="round",
                          font=ctk.CTkFont(size=13), fg_color=self.colors["primary"]).pack(side="left", padx=10)
        ctk.CTkLabel(trip_row, text="📢 Book round trip to save more!",
                    font=ctk.CTkFont(size=12), text_color=self.colors["accent"]).pack(side="right", padx=15)
        
        # Main fields row
        fields = ctk.CTkFrame(card, fg_color="transparent")
        fields.pack(fill="x", padx=15, pady=10)
        
        # FROM
        from_box = ctk.CTkFrame(fields, fg_color=self.colors["gray"], corner_radius=15)
        from_box.pack(side="left", fill="both", expand=True, padx=5)
        ctk.CTkLabel(from_box, text="FROM", font=ctk.CTkFont(size=10, weight="bold"),
                    text_color=self.colors["text_light"]).pack(anchor="w", padx=15, pady=(12, 0))
        self.from_entry = AutocompleteEntry(from_box, self.db, "Delhi", self.colors)
        self.from_entry.pack(anchor="w", padx=15)
        self.from_label = ctk.CTkLabel(from_box, text="[DEL] Indira Gandhi Intl Airport",
                                       font=ctk.CTkFont(size=9), text_color=self.colors["text_light"])
        self.from_label.pack(anchor="w", padx=15, pady=(0, 12))
        
        # Swap
        ctk.CTkButton(fields, text="⇄", font=ctk.CTkFont(size=16), fg_color=self.colors["primary"],
                     width=40, height=40, corner_radius=20, command=self.swap_cities).pack(side="left", padx=5)
        
        # TO
        to_box = ctk.CTkFrame(fields, fg_color=self.colors["gray"], corner_radius=15)
        to_box.pack(side="left", fill="both", expand=True, padx=5)
        ctk.CTkLabel(to_box, text="TO", font=ctk.CTkFont(size=10, weight="bold"),
                    text_color=self.colors["text_light"]).pack(anchor="w", padx=15, pady=(12, 0))
        self.to_entry = AutocompleteEntry(to_box, self.db, "Mumbai", self.colors)
        self.to_entry.pack(anchor="w", padx=15)
        self.to_label = ctk.CTkLabel(to_box, text="[BOM] Chhatrapati Shivaji Intl Airport",
                                     font=ctk.CTkFont(size=9), text_color=self.colors["text_light"])
        self.to_label.pack(anchor="w", padx=15, pady=(0, 12))
        
        # Departure
        dep_box = ctk.CTkFrame(fields, fg_color=self.colors["gray"], corner_radius=15, cursor="hand2")
        dep_box.pack(side="left", fill="y", padx=5)
        ctk.CTkLabel(dep_box, text="DEPARTURE", font=ctk.CTkFont(size=10, weight="bold"),
                    text_color=self.colors["text_light"]).pack(anchor="w", padx=15, pady=(12, 0))
        self.dep_day_lbl = ctk.CTkLabel(dep_box, text=self.dep_date.strftime("%d"),
                                        font=ctk.CTkFont(size=26, weight="bold"), text_color=self.colors["text"])
        self.dep_day_lbl.pack(anchor="w", padx=15)
        self.dep_month_lbl = ctk.CTkLabel(dep_box, text=self.dep_date.strftime("%b'%y, %A"),
                                          font=ctk.CTkFont(size=9), text_color=self.colors["text_light"])
        self.dep_month_lbl.pack(anchor="w", padx=15, pady=(0, 12))
        dep_box.bind("<Button-1>", lambda e: self.pick_date("dep"))
        
        # Return
        ret_box = ctk.CTkFrame(fields, fg_color=self.colors["gray"], corner_radius=15, cursor="hand2")
        ret_box.pack(side="left", fill="y", padx=5)
        ctk.CTkLabel(ret_box, text="RETURN", font=ctk.CTkFont(size=10, weight="bold"),
                    text_color=self.colors["text_light"]).pack(anchor="w", padx=15, pady=(12, 0))
        self.ret_lbl = ctk.CTkLabel(ret_box, text="Book round trip\nto save more",
                                    font=ctk.CTkFont(size=10), text_color=self.colors["accent"])
        self.ret_lbl.pack(anchor="w", padx=15, pady=12)
        ret_box.bind("<Button-1>", lambda e: self.pick_date("ret"))

        
        # Travellers
        trav_box = ctk.CTkFrame(fields, fg_color=self.colors["gray"], corner_radius=15, cursor="hand2")
        trav_box.pack(side="left", fill="y", padx=5)
        ctk.CTkLabel(trav_box, text="TRAVELLERS & CLASS", font=ctk.CTkFont(size=10, weight="bold"),
                    text_color=self.colors["text_light"]).pack(anchor="w", padx=15, pady=(12, 0))
        self.trav_count_lbl = ctk.CTkLabel(trav_box, text="1",
                                           font=ctk.CTkFont(size=26, weight="bold"), text_color=self.colors["text"])
        self.trav_count_lbl.pack(anchor="w", padx=15)
        ctk.CTkLabel(trav_box, text="Traveller, Economy",
                    font=ctk.CTkFont(size=9), text_color=self.colors["text_light"]).pack(anchor="w", padx=15, pady=(0, 12))
        trav_box.bind("<Button-1>", lambda e: self.pick_travellers())
        
        # Special fares
        fares_row = ctk.CTkFrame(card, fg_color="transparent")
        fares_row.pack(fill="x", padx=25, pady=8)
        ctk.CTkLabel(fares_row, text="Special Fares:", font=ctk.CTkFont(size=11),
                    text_color=self.colors["text_light"]).pack(side="left")
        for fare in ["Regular", "Student", "Senior Citizen", "Armed Forces", "Doctor/Nurse"]:
            ctk.CTkButton(fares_row, text=fare, font=ctk.CTkFont(size=10), fg_color=self.colors["gray"],
                         text_color=self.colors["text"], hover_color=self.colors["light_blue"],
                         corner_radius=15, height=28, width=95).pack(side="left", padx=4)
        
        # Search button
        ctk.CTkButton(card, text="SEARCH", font=ctk.CTkFont(size=16, weight="bold"),
                     fg_color=self.colors["secondary"], hover_color="#E55A00",
                     corner_radius=25, width=220, height=50, command=self.search).pack(pady=18)
        
        # Popular routes
        pop_frame = ctk.CTkFrame(self.content, fg_color="transparent")
        pop_frame.pack(fill="x", padx=40, pady=20)
        ctk.CTkLabel(pop_frame, text="🔥 Popular Routes", font=ctk.CTkFont(size=18, weight="bold"),
                    text_color=self.colors["text"]).pack(anchor="w", pady=(0, 15))
        
        routes_row = ctk.CTkFrame(pop_frame, fg_color="transparent")
        routes_row.pack(fill="x")
        popular = [("Delhi", "Mumbai", "₹4,299"), ("Mumbai", "Goa", "₹3,599"),
                  ("Bangalore", "Delhi", "₹5,199"), ("Delhi", "Dubai", "₹15,999")]
        for orig, dest, price in popular:
            c = ctk.CTkFrame(routes_row, fg_color=self.colors["white"], corner_radius=15, cursor="hand2")
            c.pack(side="left", fill="both", expand=True, padx=8)
            ctk.CTkLabel(c, text=f"{orig} → {dest}", font=ctk.CTkFont(size=14, weight="bold"),
                        text_color=self.colors["text"]).pack(pady=(18, 5))
            ctk.CTkLabel(c, text=f"Starting {price}", font=ctk.CTkFont(size=12),
                        text_color=self.colors["accent"]).pack(pady=(0, 18))
            c.bind("<Button-1>", lambda e, o=orig, d=dest: self.quick_search(o, d))
        
        # Offers section
        offers_frame = ctk.CTkFrame(self.content, fg_color="transparent")
        offers_frame.pack(fill="x", padx=40, pady=20)
        ctk.CTkLabel(offers_frame, text="🎉 Exclusive Offers", font=ctk.CTkFont(size=18, weight="bold"),
                    text_color=self.colors["text"]).pack(anchor="w", pady=(0, 15))
        
        offers_row = ctk.CTkFrame(offers_frame, fg_color="transparent")
        offers_row.pack(fill="x")
        offers = [("🏖️ Goa Package", "3N/4D from ₹8,999", "GOA30", "30% OFF"),
                 ("🏔️ Manali Trip", "4N/5D from ₹12,999", "MANALI25", "25% OFF"),
                 ("✈️ Dubai Flights", "From ₹15,999", "FLY20", "20% OFF")]
        for title, desc, code, off in offers:
            c = ctk.CTkFrame(offers_row, fg_color=self.colors["white"], corner_radius=15)
            c.pack(side="left", fill="both", expand=True, padx=8)
            ctk.CTkLabel(c, text=off, font=ctk.CTkFont(size=11, weight="bold"),
                        fg_color=self.colors["secondary"], text_color=self.colors["white"],
                        corner_radius=8).pack(anchor="ne", padx=10, pady=10)
            ctk.CTkLabel(c, text=title, font=ctk.CTkFont(size=14, weight="bold"),
                        text_color=self.colors["text"]).pack(anchor="w", padx=15)
            ctk.CTkLabel(c, text=desc, font=ctk.CTkFont(size=12),
                        text_color=self.colors["primary"]).pack(anchor="w", padx=15, pady=3)
            ctk.CTkLabel(c, text=f"Code: {code}", font=ctk.CTkFont(size=11, weight="bold"),
                        text_color=self.colors["text_light"]).pack(anchor="w", padx=15, pady=(0, 15))
        
        # Results area
        self.results_frame = ctk.CTkFrame(self.content, fg_color="transparent")
        self.results_frame.pack(fill="both", expand=True, padx=40, pady=10)

    
    def swap_cities(self):
        f, t = self.from_entry.get(), self.to_entry.get()
        self.from_entry.delete(0, "end")
        self.to_entry.delete(0, "end")
        self.from_entry.insert(0, t)
        self.to_entry.insert(0, f)
    
    def pick_date(self, dtype):
        dlg = ctk.CTkToplevel(self)
        dlg.title("Select Date")
        dlg.geometry("320x220")
        dlg.transient(self)
        dlg.grab_set()
        
        ctk.CTkLabel(dlg, text=f"Select {'Departure' if dtype=='dep' else 'Return'} Date",
                    font=ctk.CTkFont(size=14, weight="bold")).pack(pady=20)
        
        row = ctk.CTkFrame(dlg, fg_color="transparent")
        row.pack(pady=10)
        day_var, mon_var, yr_var = ctk.StringVar(value="15"), ctk.StringVar(value="Jan"), ctk.StringVar(value="2026")
        ctk.CTkComboBox(row, values=[str(i) for i in range(1, 32)], variable=day_var, width=65).pack(side="left", padx=5)
        ctk.CTkComboBox(row, values=["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"],
                       variable=mon_var, width=75).pack(side="left", padx=5)
        ctk.CTkComboBox(row, values=["2026","2027"], variable=yr_var, width=75).pack(side="left", padx=5)
        
        def apply():
            txt = f"{day_var.get()} {mon_var.get()}'{yr_var.get()[-2:]}"
            if dtype == "dep":
                self.dep_day_lbl.configure(text=day_var.get())
                self.dep_month_lbl.configure(text=f"{mon_var.get()}'{yr_var.get()[-2:]}")
            else:
                self.ret_lbl.configure(text=txt)
                self.trip_type.set("round")
            dlg.destroy()
        
        ctk.CTkButton(dlg, text="Select", fg_color=self.colors["primary"], corner_radius=20,
                     width=120, command=apply).pack(pady=20)
    
    def pick_date(self):
        """Pick departure date"""
        dlg = ctk.CTkToplevel(self)
        dlg.title("Select Date")
        dlg.geometry("320x250")
        dlg.transient(self)
        dlg.grab_set()
        
        ctk.CTkLabel(dlg, text="📅 Select Departure Date", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=20)
        
        row = ctk.CTkFrame(dlg, fg_color="transparent")
        row.pack(pady=10)
        
        day_var = ctk.StringVar(value=str(self.dep_date.day))
        mon_var = ctk.StringVar(value=self.dep_date.strftime("%b"))
        yr_var = ctk.StringVar(value=str(self.dep_date.year))
        
        ctk.CTkLabel(row, text="Day:", font=ctk.CTkFont(size=11)).pack(side="left", padx=5)
        ctk.CTkComboBox(row, values=[str(i) for i in range(1, 32)], variable=day_var, width=60).pack(side="left", padx=5)
        ctk.CTkLabel(row, text="Month:", font=ctk.CTkFont(size=11)).pack(side="left", padx=5)
        ctk.CTkComboBox(row, values=["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"],
                       variable=mon_var, width=70).pack(side="left", padx=5)
        ctk.CTkLabel(row, text="Year:", font=ctk.CTkFont(size=11)).pack(side="left", padx=5)
        ctk.CTkComboBox(row, values=["2025","2026","2027"], variable=yr_var, width=70).pack(side="left", padx=5)
        
        def apply():
            months = {"Jan":1,"Feb":2,"Mar":3,"Apr":4,"May":5,"Jun":6,"Jul":7,"Aug":8,"Sep":9,"Oct":10,"Nov":11,"Dec":12}
            try:
                self.dep_date = datetime(int(yr_var.get()), months[mon_var.get()], int(day_var.get()))
                if hasattr(self, 'date_lbl'):
                    self.date_lbl.configure(text=self.dep_date.strftime("%d %b'%y"))
            except:
                pass
            dlg.destroy()
        
        ctk.CTkButton(dlg, text="Select Date", fg_color=self.colors["secondary"], corner_radius=20,
                     width=140, command=apply).pack(pady=25)
    
    def pick_travellers(self):
        dlg = ctk.CTkToplevel(self)
        dlg.title("Travellers")
        dlg.geometry("340x280")
        dlg.transient(self)
        dlg.grab_set()
        
        ctk.CTkLabel(dlg, text="Travellers & Class", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=20)
        
        # Adults
        a_row = ctk.CTkFrame(dlg, fg_color="transparent")
        a_row.pack(fill="x", padx=30, pady=8)
        ctk.CTkLabel(a_row, text="Adults (12+ yrs)", font=ctk.CTkFont(size=12)).pack(side="left")
        a_ctrl = ctk.CTkFrame(a_row, fg_color="transparent")
        a_ctrl.pack(side="right")
        ctk.CTkButton(a_ctrl, text="-", width=32, height=32, corner_radius=16, fg_color=self.colors["gray"],
                     text_color=self.colors["text"], command=lambda: self.adults_var.set(max(1, self.adults_var.get()-1))).pack(side="left", padx=5)
        ctk.CTkLabel(a_ctrl, textvariable=self.adults_var, font=ctk.CTkFont(size=14, weight="bold"), width=30).pack(side="left")
        ctk.CTkButton(a_ctrl, text="+", width=32, height=32, corner_radius=16, fg_color=self.colors["primary"],
                     command=lambda: self.adults_var.set(self.adults_var.get()+1)).pack(side="left", padx=5)
        
        # Children
        c_row = ctk.CTkFrame(dlg, fg_color="transparent")
        c_row.pack(fill="x", padx=30, pady=8)
        ctk.CTkLabel(c_row, text="Children (2-12 yrs)", font=ctk.CTkFont(size=12)).pack(side="left")
        c_ctrl = ctk.CTkFrame(c_row, fg_color="transparent")
        c_ctrl.pack(side="right")
        ctk.CTkButton(c_ctrl, text="-", width=32, height=32, corner_radius=16, fg_color=self.colors["gray"],
                     text_color=self.colors["text"], command=lambda: self.children_var.set(max(0, self.children_var.get()-1))).pack(side="left", padx=5)
        ctk.CTkLabel(c_ctrl, textvariable=self.children_var, font=ctk.CTkFont(size=14, weight="bold"), width=30).pack(side="left")
        ctk.CTkButton(c_ctrl, text="+", width=32, height=32, corner_radius=16, fg_color=self.colors["primary"],
                     command=lambda: self.children_var.set(self.children_var.get()+1)).pack(side="left", padx=5)
        
        def done():
            self.trav_count_lbl.configure(text=str(self.adults_var.get() + self.children_var.get()))
            dlg.destroy()
        
        ctk.CTkButton(dlg, text="Done", fg_color=self.colors["secondary"], corner_radius=20,
                     width=140, command=done).pack(pady=25)
    
    def quick_search(self, orig, dest):
        self.from_entry.delete(0, "end")
        self.from_entry.insert(0, orig)
        self.to_entry.delete(0, "end")
        self.to_entry.insert(0, dest)
        self.search()

    
    def search(self):
        orig, dest = self.from_entry.get().strip(), self.to_entry.get().strip()
        if not orig or not dest:
            messagebox.showerror("Error", "Enter origin and destination")
            return
        
        route = self.location_service.get_route_info(orig, dest)
        if not route:
            messagebox.showerror("Error", f"Could not find: {orig} or {dest}")
            return
        
        adults, children = self.adults_var.get(), self.children_var.get()
        nights = self.nights_var.get()
        prices = self.pricing.calculate_prices(route["distance_km"], route["origin"]["country"],
                                               route["destination"]["country"], adults, children, nights)
        self.show_results(route, prices, adults + children, nights)
    
    def show_results(self, route, prices, travelers, nights):
        for w in self.results_frame.winfo_children():
            w.destroy()
        
        # Route header
        hdr = ctk.CTkFrame(self.results_frame, fg_color=self.colors["dark"], corner_radius=20)
        hdr.pack(fill="x", pady=(0, 20))
        hdr_content = ctk.CTkFrame(hdr, fg_color="transparent")
        hdr_content.pack(fill="x", padx=30, pady=25)
        
        ctk.CTkLabel(hdr_content, text=route["origin"]["name"], font=ctk.CTkFont(size=28, weight="bold"),
                    text_color=self.colors["white"]).pack(side="left")
        ctk.CTkLabel(hdr_content, text=f"  [{route['origin'].get('code','')}]",
                    font=ctk.CTkFont(size=11), text_color=self.colors["text_light"]).pack(side="left")
        ctk.CTkLabel(hdr_content, text=f"   ✈️  {route['distance_km']:,.0f} km  ✈️   ",
                    font=ctk.CTkFont(size=13), text_color=self.colors["accent"]).pack(side="left")
        ctk.CTkLabel(hdr_content, text=route["destination"]["name"], font=ctk.CTkFont(size=28, weight="bold"),
                    text_color=self.colors["white"]).pack(side="left")
        ctk.CTkLabel(hdr_content, text=f"  [{route['destination'].get('code','')}]",
                    font=ctk.CTkFont(size=11), text_color=self.colors["text_light"]).pack(side="left")
        
        stats = ctk.CTkFrame(hdr_content, fg_color="transparent")
        stats.pack(side="right")
        ctk.CTkLabel(stats, text=f"👥 {travelers}", font=ctk.CTkFont(size=12),
                    text_color=self.colors["white"]).pack(side="left", padx=12)
        ctk.CTkLabel(stats, text=f"🌙 {nights} Nights", font=ctk.CTkFont(size=12),
                    text_color=self.colors["white"]).pack(side="left", padx=12)
        
        # Transport options row
        trans_row = ctk.CTkFrame(self.results_frame, fg_color="transparent")
        trans_row.pack(fill="x", pady=10)
        
        # Flights
        if prices["flights"]:
            fc = ctk.CTkFrame(trans_row, fg_color=self.colors["white"], corner_radius=15)
            fc.pack(side="left", fill="both", expand=True, padx=5)
            ctk.CTkLabel(fc, text="✈️ Flights", font=ctk.CTkFont(size=15, weight="bold"),
                        text_color=self.colors["text"]).pack(anchor="w", padx=18, pady=(15, 8))
            for f in prices["flights"]:
                r = ctk.CTkFrame(fc, fg_color=self.colors["gray"], corner_radius=10)
                r.pack(fill="x", padx=12, pady=4)
                ctk.CTkLabel(r, text=f["type"], font=ctk.CTkFont(size=11),
                            text_color=self.colors["text"]).pack(side="left", padx=12, pady=10)
                ctk.CTkLabel(r, text=f"₹{f['price']:,}", font=ctk.CTkFont(size=13, weight="bold"),
                            text_color=self.colors["primary"]).pack(side="right", padx=12, pady=10)
        
        # Trains
        if prices["trains"]:
            tc = ctk.CTkFrame(trans_row, fg_color=self.colors["white"], corner_radius=15)
            tc.pack(side="left", fill="both", expand=True, padx=5)
            ctk.CTkLabel(tc, text="🚂 Trains", font=ctk.CTkFont(size=15, weight="bold"),
                        text_color=self.colors["text"]).pack(anchor="w", padx=18, pady=(15, 8))
            for t in prices["trains"]:
                r = ctk.CTkFrame(tc, fg_color=self.colors["gray"], corner_radius=10)
                r.pack(fill="x", padx=12, pady=3)
                ctk.CTkLabel(r, text=t["type"], font=ctk.CTkFont(size=10),
                            text_color=self.colors["text"]).pack(side="left", padx=12, pady=8)
                ctk.CTkLabel(r, text=f"₹{t['price']:,}", font=ctk.CTkFont(size=12, weight="bold"),
                            text_color=self.colors["primary"]).pack(side="right", padx=12, pady=8)
        
        # Buses
        if prices["buses"]:
            bc = ctk.CTkFrame(trans_row, fg_color=self.colors["white"], corner_radius=15)
            bc.pack(side="left", fill="both", expand=True, padx=5)
            ctk.CTkLabel(bc, text="🚌 Buses", font=ctk.CTkFont(size=15, weight="bold"),
                        text_color=self.colors["text"]).pack(anchor="w", padx=18, pady=(15, 8))
            for b in prices["buses"]:
                r = ctk.CTkFrame(bc, fg_color=self.colors["gray"], corner_radius=10)
                r.pack(fill="x", padx=12, pady=3)
                ctk.CTkLabel(r, text=b["type"], font=ctk.CTkFont(size=10),
                            text_color=self.colors["text"]).pack(side="left", padx=12, pady=8)
                ctk.CTkLabel(r, text=f"₹{b['price']:,}", font=ctk.CTkFont(size=12, weight="bold"),
                            text_color=self.colors["primary"]).pack(side="right", padx=12, pady=8)
        
        # Cabs
        if prices["cabs"]:
            cc = ctk.CTkFrame(trans_row, fg_color=self.colors["white"], corner_radius=15)
            cc.pack(side="left", fill="both", expand=True, padx=5)
            ctk.CTkLabel(cc, text="🚕 Local Cabs", font=ctk.CTkFont(size=15, weight="bold"),
                        text_color=self.colors["text"]).pack(anchor="w", padx=18, pady=(15, 8))
            for c in prices["cabs"]:
                r = ctk.CTkFrame(cc, fg_color=self.colors["gray"], corner_radius=10)
                r.pack(fill="x", padx=12, pady=3)
                ctk.CTkLabel(r, text=c["type"], font=ctk.CTkFont(size=10),
                            text_color=self.colors["text"]).pack(side="left", padx=12, pady=8)
                ctk.CTkLabel(r, text=f"₹{c['price']:,}", font=ctk.CTkFont(size=12, weight="bold"),
                            text_color=self.colors["primary"]).pack(side="right", padx=12, pady=8)

        
        # Packages
        ctk.CTkLabel(self.results_frame, text="🎁 Complete Packages", font=ctk.CTkFont(size=18, weight="bold"),
                    text_color=self.colors["text"]).pack(anchor="w", pady=(20, 12))
        
        pkg_row = ctk.CTkFrame(self.results_frame, fg_color="transparent")
        pkg_row.pack(fill="x")
        
        for pkg in prices["packages"]:
            pc = ctk.CTkFrame(pkg_row, fg_color=self.colors["white"], corner_radius=15)
            pc.pack(side="left", fill="both", expand=True, padx=8)
            
            ctk.CTkLabel(pc, text=pkg["name"], font=ctk.CTkFont(size=16, weight="bold"),
                        text_color=self.colors["text"]).pack(pady=(20, 8))
            ctk.CTkLabel(pc, text=f"₹{pkg['total']:,}", font=ctk.CTkFont(size=30, weight="bold"),
                        text_color=pkg["color"]).pack()
            ctk.CTkLabel(pc, text=f"₹{pkg['per_person']:,}/person", font=ctk.CTkFont(size=11),
                        text_color=self.colors["text_light"]).pack(pady=(0, 5))
            ctk.CTkButton(pc, text="Book Now", font=ctk.CTkFont(size=12, weight="bold"),
                         fg_color=self.colors["secondary"], hover_color="#E55A00",
                         corner_radius=20, width=130, command=lambda p=pkg: self.book(p)).pack(pady=(10, 20))
        
        # Hotels
        ctk.CTkLabel(self.results_frame, text="🏨 Hotels", font=ctk.CTkFont(size=18, weight="bold"),
                    text_color=self.colors["text"]).pack(anchor="w", pady=(25, 12))
        
        htl_row = ctk.CTkFrame(self.results_frame, fg_color="transparent")
        htl_row.pack(fill="x")
        
        hotel_info = [("Budget", "budget", "⭐⭐", "Basic amenities"),
                     ("Mid-Range", "mid", "⭐⭐⭐", "Good amenities, restaurant"),
                     ("Luxury", "luxury", "⭐⭐⭐⭐⭐", "Premium, spa, pool")]
        for name, key, stars, desc in hotel_info:
            hc = ctk.CTkFrame(htl_row, fg_color=self.colors["white"], corner_radius=15)
            hc.pack(side="left", fill="both", expand=True, padx=8)
            ctk.CTkLabel(hc, text=f"{name} Hotels", font=ctk.CTkFont(size=14, weight="bold"),
                        text_color=self.colors["text"]).pack(anchor="w", padx=18, pady=(15, 3))
            ctk.CTkLabel(hc, text=stars, font=ctk.CTkFont(size=11),
                        text_color=self.colors["secondary"]).pack(anchor="w", padx=18)
            ctk.CTkLabel(hc, text=desc, font=ctk.CTkFont(size=10),
                        text_color=self.colors["text_light"]).pack(anchor="w", padx=18, pady=3)
            ctk.CTkLabel(hc, text=f"₹{prices['hotels'][key]:,}/night", font=ctk.CTkFont(size=16, weight="bold"),
                        text_color=self.colors["primary"]).pack(anchor="w", padx=18, pady=(5, 15))
    
    def show_flight_results(self, route, prices):
        """Show flight-specific results"""
        for w in self.tab_results.winfo_children():
            w.destroy()
        
        # Header
        hdr = ctk.CTkFrame(self.tab_results, fg_color=self.colors["dark"], corner_radius=15)
        hdr.pack(fill="x", pady=(0, 15))
        hdr_c = ctk.CTkFrame(hdr, fg_color="transparent")
        hdr_c.pack(fill="x", padx=25, pady=20)
        ctk.CTkLabel(hdr_c, text=f"✈️ Flights: {route['origin']['name']} → {route['destination']['name']}",
                    font=ctk.CTkFont(size=20, weight="bold"), text_color=self.colors["white"]).pack(side="left")
        ctk.CTkLabel(hdr_c, text=f"{route['distance_km']:,.0f} km", font=ctk.CTkFont(size=12),
                    text_color=self.colors["accent"]).pack(side="right")
        
        # Flight list
        ctk.CTkLabel(self.tab_results, text="Available Flights", font=ctk.CTkFont(size=16, weight="bold"),
                    text_color=self.colors["text"]).pack(anchor="w", pady=(10, 10))
        
        airlines = [("IndiGo", "6E-2145", "06:00", "08:15", prices["flights"][0]["price"]),
                   ("Air India", "AI-865", "08:30", "10:45", int(prices["flights"][0]["price"] * 1.1)),
                   ("SpiceJet", "SG-412", "10:00", "12:20", int(prices["flights"][0]["price"] * 0.95)),
                   ("Vistara", "UK-945", "14:00", "16:10", int(prices["flights"][0]["price"] * 1.2)),
                   ("IndiGo", "6E-6721", "18:30", "20:45", int(prices["flights"][0]["price"] * 1.05)),
                   ("Air India", "AI-502", "21:00", "23:15", prices["flights"][1]["price"])]
        
        for airline, flight_no, dep, arr, price in airlines:
            c = ctk.CTkFrame(self.tab_results, fg_color=self.colors["white"], corner_radius=12)
            c.pack(fill="x", pady=5)
            
            # Airline info
            left = ctk.CTkFrame(c, fg_color="transparent")
            left.pack(side="left", padx=20, pady=15)
            ctk.CTkLabel(left, text=airline, font=ctk.CTkFont(size=14, weight="bold"),
                        text_color=self.colors["text"]).pack(anchor="w")
            ctk.CTkLabel(left, text=flight_no, font=ctk.CTkFont(size=11),
                        text_color=self.colors["text_light"]).pack(anchor="w")
            
            # Time
            mid = ctk.CTkFrame(c, fg_color="transparent")
            mid.pack(side="left", expand=True, padx=20)
            ctk.CTkLabel(mid, text=f"{dep}  ✈️  {arr}", font=ctk.CTkFont(size=16, weight="bold"),
                        text_color=self.colors["text"]).pack()
            ctk.CTkLabel(mid, text="Non-stop • 2h 15m", font=ctk.CTkFont(size=10),
                        text_color=self.colors["text_light"]).pack()
            
            # Price & Book
            right = ctk.CTkFrame(c, fg_color="transparent")
            right.pack(side="right", padx=20, pady=15)
            ctk.CTkLabel(right, text=f"₹{price:,}", font=ctk.CTkFont(size=18, weight="bold"),
                        text_color=self.colors["primary"]).pack()
            ctk.CTkButton(right, text="Book", font=ctk.CTkFont(size=11, weight="bold"),
                         fg_color=self.colors["secondary"], corner_radius=15, width=80, height=30,
                         command=lambda p=price, a=airline: self.book_transport("Flight", a, p)).pack(pady=5)
    
    def show_train_results(self, route, prices):
        """Show train-specific results"""
        for w in self.tab_results.winfo_children():
            w.destroy()
        
        if not prices["trains"]:
            ctk.CTkLabel(self.tab_results, text="❌ No trains available for this route (international or too far)",
                        font=ctk.CTkFont(size=14), text_color=self.colors["text_light"]).pack(pady=50)
            return
        
        # Header
        hdr = ctk.CTkFrame(self.tab_results, fg_color=self.colors["dark"], corner_radius=15)
        hdr.pack(fill="x", pady=(0, 15))
        hdr_c = ctk.CTkFrame(hdr, fg_color="transparent")
        hdr_c.pack(fill="x", padx=25, pady=20)
        ctk.CTkLabel(hdr_c, text=f"🚂 Trains: {route['origin']['name']} → {route['destination']['name']}",
                    font=ctk.CTkFont(size=20, weight="bold"), text_color=self.colors["white"]).pack(side="left")
        
        ctk.CTkLabel(self.tab_results, text="Available Trains", font=ctk.CTkFont(size=16, weight="bold"),
                    text_color=self.colors["text"]).pack(anchor="w", pady=(10, 10))
        
        trains = [("Rajdhani Express", "12951", "16:25", "08:15", prices["trains"][3]["price"]),
                 ("Shatabdi Express", "12009", "06:00", "14:30", prices["trains"][2]["price"]),
                 ("Duronto Express", "12267", "23:00", "08:45", prices["trains"][2]["price"]),
                 ("Garib Rath", "12216", "17:30", "06:00", prices["trains"][1]["price"]),
                 ("Superfast Express", "12137", "22:15", "12:30", prices["trains"][0]["price"])]
        
        for name, num, dep, arr, price in trains:
            c = ctk.CTkFrame(self.tab_results, fg_color=self.colors["white"], corner_radius=12)
            c.pack(fill="x", pady=5)
            
            left = ctk.CTkFrame(c, fg_color="transparent")
            left.pack(side="left", padx=20, pady=15)
            ctk.CTkLabel(left, text=name, font=ctk.CTkFont(size=14, weight="bold"),
                        text_color=self.colors["text"]).pack(anchor="w")
            ctk.CTkLabel(left, text=f"Train #{num}", font=ctk.CTkFont(size=11),
                        text_color=self.colors["text_light"]).pack(anchor="w")
            
            mid = ctk.CTkFrame(c, fg_color="transparent")
            mid.pack(side="left", expand=True, padx=20)
            ctk.CTkLabel(mid, text=f"{dep}  🚂  {arr}", font=ctk.CTkFont(size=16, weight="bold"),
                        text_color=self.colors["text"]).pack()
            
            # Class options
            cls_row = ctk.CTkFrame(c, fg_color="transparent")
            cls_row.pack(side="left", padx=10)
            for cls, p in [("SL", prices["trains"][0]["price"]), ("3A", prices["trains"][1]["price"]), 
                          ("2A", prices["trains"][2]["price"]), ("1A", prices["trains"][3]["price"])]:
                ctk.CTkButton(cls_row, text=f"{cls}\n₹{p:,}", font=ctk.CTkFont(size=9),
                             fg_color=self.colors["gray"], text_color=self.colors["text"],
                             hover_color=self.colors["light_blue"], corner_radius=8, width=55, height=40,
                             command=lambda pr=p, n=name: self.book_transport("Train", n, pr)).pack(side="left", padx=2)
    
    def show_bus_results(self, route, prices):
        """Show bus-specific results"""
        for w in self.tab_results.winfo_children():
            w.destroy()
        
        if not prices["buses"]:
            ctk.CTkLabel(self.tab_results, text="❌ No buses available for this route (international or too far)",
                        font=ctk.CTkFont(size=14), text_color=self.colors["text_light"]).pack(pady=50)
            return
        
        hdr = ctk.CTkFrame(self.tab_results, fg_color=self.colors["dark"], corner_radius=15)
        hdr.pack(fill="x", pady=(0, 15))
        hdr_c = ctk.CTkFrame(hdr, fg_color="transparent")
        hdr_c.pack(fill="x", padx=25, pady=20)
        ctk.CTkLabel(hdr_c, text=f"🚌 Buses: {route['origin']['name']} → {route['destination']['name']}",
                    font=ctk.CTkFont(size=20, weight="bold"), text_color=self.colors["white"]).pack(side="left")
        
        ctk.CTkLabel(self.tab_results, text="Available Buses", font=ctk.CTkFont(size=16, weight="bold"),
                    text_color=self.colors["text"]).pack(anchor="w", pady=(10, 10))
        
        buses = [("VRL Travels", "Volvo Multi-Axle", "21:00", "06:30", prices["buses"][3]["price"], "⭐ 4.5"),
                ("SRS Travels", "AC Sleeper", "22:00", "07:00", prices["buses"][2]["price"], "⭐ 4.2"),
                ("Neeta Travels", "AC Seater", "20:30", "05:30", prices["buses"][1]["price"], "⭐ 4.0"),
                ("Orange Travels", "Non-AC Seater", "19:00", "04:00", prices["buses"][0]["price"], "⭐ 3.8"),
                ("Parveen Travels", "Volvo Multi-Axle", "23:00", "08:30", prices["buses"][3]["price"], "⭐ 4.3")]
        
        for operator, bus_type, dep, arr, price, rating in buses:
            c = ctk.CTkFrame(self.tab_results, fg_color=self.colors["white"], corner_radius=12)
            c.pack(fill="x", pady=5)
            
            left = ctk.CTkFrame(c, fg_color="transparent")
            left.pack(side="left", padx=20, pady=15)
            ctk.CTkLabel(left, text=operator, font=ctk.CTkFont(size=14, weight="bold"),
                        text_color=self.colors["text"]).pack(anchor="w")
            ctk.CTkLabel(left, text=f"{bus_type} • {rating}", font=ctk.CTkFont(size=11),
                        text_color=self.colors["text_light"]).pack(anchor="w")
            
            mid = ctk.CTkFrame(c, fg_color="transparent")
            mid.pack(side="left", expand=True, padx=20)
            ctk.CTkLabel(mid, text=f"{dep}  🚌  {arr}", font=ctk.CTkFont(size=16, weight="bold"),
                        text_color=self.colors["text"]).pack()
            
            right = ctk.CTkFrame(c, fg_color="transparent")
            right.pack(side="right", padx=20, pady=15)
            ctk.CTkLabel(right, text=f"₹{price:,}", font=ctk.CTkFont(size=18, weight="bold"),
                        text_color=self.colors["primary"]).pack()
            ctk.CTkButton(right, text="Book", font=ctk.CTkFont(size=11, weight="bold"),
                         fg_color=self.colors["secondary"], corner_radius=15, width=80, height=30,
                         command=lambda p=price, o=operator: self.book_transport("Bus", o, p)).pack(pady=5)
    
    def show_hotel_results(self, city):
        """Show hotel results for a city"""
        for w in self.tab_results.winfo_children():
            w.destroy()
        
        loc = self.location_service.geocode(city)
        if not loc:
            messagebox.showerror("Error", f"Could not find: {city}")
            return
        
        dest_idx = self.pricing.cost_index.get(self.pricing.get_region(loc["country"]), 1)
        
        hdr = ctk.CTkFrame(self.tab_results, fg_color=self.colors["dark"], corner_radius=15)
        hdr.pack(fill="x", pady=(0, 15))
        hdr_c = ctk.CTkFrame(hdr, fg_color="transparent")
        hdr_c.pack(fill="x", padx=25, pady=20)
        ctk.CTkLabel(hdr_c, text=f"🏨 Hotels in {city}", font=ctk.CTkFont(size=20, weight="bold"),
                    text_color=self.colors["white"]).pack(side="left")
        
        ctk.CTkLabel(self.tab_results, text="Available Hotels", font=ctk.CTkFont(size=16, weight="bold"),
                    text_color=self.colors["text"]).pack(anchor="w", pady=(10, 10))
        
        hotels = [("Taj Hotel", "⭐⭐⭐⭐⭐", "Luxury", int(15000 * dest_idx), "Pool, Spa, Restaurant"),
                 ("Marriott", "⭐⭐⭐⭐⭐", "Luxury", int(12000 * dest_idx), "Gym, Pool, Bar"),
                 ("Hyatt Regency", "⭐⭐⭐⭐", "Premium", int(8000 * dest_idx), "Restaurant, Gym"),
                 ("Lemon Tree", "⭐⭐⭐", "Mid-Range", int(3500 * dest_idx), "WiFi, Restaurant"),
                 ("OYO Rooms", "⭐⭐", "Budget", int(1200 * dest_idx), "AC, WiFi, TV"),
                 ("FabHotel", "⭐⭐", "Budget", int(900 * dest_idx), "AC, WiFi")]
        
        for name, stars, category, price, amenities in hotels:
            c = ctk.CTkFrame(self.tab_results, fg_color=self.colors["white"], corner_radius=12)
            c.pack(fill="x", pady=5)
            
            left = ctk.CTkFrame(c, fg_color="transparent")
            left.pack(side="left", padx=20, pady=15)
            ctk.CTkLabel(left, text=name, font=ctk.CTkFont(size=14, weight="bold"),
                        text_color=self.colors["text"]).pack(anchor="w")
            ctk.CTkLabel(left, text=f"{stars} • {category}", font=ctk.CTkFont(size=11),
                        text_color=self.colors["secondary"]).pack(anchor="w")
            ctk.CTkLabel(left, text=amenities, font=ctk.CTkFont(size=10),
                        text_color=self.colors["text_light"]).pack(anchor="w")
            
            right = ctk.CTkFrame(c, fg_color="transparent")
            right.pack(side="right", padx=20, pady=15)
            ctk.CTkLabel(right, text=f"₹{price:,}/night", font=ctk.CTkFont(size=18, weight="bold"),
                        text_color=self.colors["primary"]).pack()
            ctk.CTkButton(right, text="Book", font=ctk.CTkFont(size=11, weight="bold"),
                         fg_color=self.colors["secondary"], corner_radius=15, width=80, height=30,
                         command=lambda p=price, n=name: self.book_transport("Hotel", n, p)).pack(pady=5)
    
    def show_cab_results(self, pickup, drop):
        """Show cab results"""
        for w in self.tab_results.winfo_children():
            w.destroy()
        
        route = self.location_service.get_route_info(pickup, drop)
        if not route:
            messagebox.showerror("Error", f"Could not find route: {pickup} to {drop}")
            return
        
        prices = self.pricing.calculate_prices(route["distance_km"], route["origin"]["country"],
                                               route["destination"]["country"], 1, 0, 1)
        
        hdr = ctk.CTkFrame(self.tab_results, fg_color=self.colors["dark"], corner_radius=15)
        hdr.pack(fill="x", pady=(0, 15))
        hdr_c = ctk.CTkFrame(hdr, fg_color="transparent")
        hdr_c.pack(fill="x", padx=25, pady=20)
        ctk.CTkLabel(hdr_c, text=f"🚕 Cabs: {pickup} → {drop}", font=ctk.CTkFont(size=20, weight="bold"),
                    text_color=self.colors["white"]).pack(side="left")
        ctk.CTkLabel(hdr_c, text=f"{route['distance_km']:,.0f} km", font=ctk.CTkFont(size=12),
                    text_color=self.colors["accent"]).pack(side="right")
        
        ctk.CTkLabel(self.tab_results, text="Available Cabs", font=ctk.CTkFont(size=16, weight="bold"),
                    text_color=self.colors["text"]).pack(anchor="w", pady=(10, 10))
        
        cabs = [("Ola", "Mini", "Swift/WagonR", prices["cabs"][0]["price"], "4 Seater"),
               ("Uber", "Go", "Swift Dzire", int(prices["cabs"][0]["price"] * 1.1), "4 Seater"),
               ("Ola", "Prime Sedan", "Etios/Xcent", prices["cabs"][0]["price"], "4 Seater"),
               ("Uber", "Premier", "Honda City", int(prices["cabs"][1]["price"] * 0.9), "4 Seater"),
               ("Ola", "SUV", "Innova/Ertiga", prices["cabs"][1]["price"], "6 Seater"),
               ("Uber", "XL", "Innova Crysta", int(prices["cabs"][1]["price"] * 1.1), "6 Seater"),
               ("Ola", "Lux", "BMW/Audi", prices["cabs"][2]["price"], "4 Seater")]
        
        for provider, cab_type, car, price, capacity in cabs:
            c = ctk.CTkFrame(self.tab_results, fg_color=self.colors["white"], corner_radius=12)
            c.pack(fill="x", pady=5)
            
            left = ctk.CTkFrame(c, fg_color="transparent")
            left.pack(side="left", padx=20, pady=15)
            ctk.CTkLabel(left, text=f"{provider} {cab_type}", font=ctk.CTkFont(size=14, weight="bold"),
                        text_color=self.colors["text"]).pack(anchor="w")
            ctk.CTkLabel(left, text=f"{car} • {capacity}", font=ctk.CTkFont(size=11),
                        text_color=self.colors["text_light"]).pack(anchor="w")
            
            right = ctk.CTkFrame(c, fg_color="transparent")
            right.pack(side="right", padx=20, pady=15)
            ctk.CTkLabel(right, text=f"₹{price:,}", font=ctk.CTkFont(size=18, weight="bold"),
                        text_color=self.colors["primary"]).pack()
            ctk.CTkButton(right, text="Book", font=ctk.CTkFont(size=11, weight="bold"),
                         fg_color=self.colors["secondary"], corner_radius=15, width=80, height=30,
                         command=lambda p=price, t=f"{provider} {cab_type}": self.book_transport("Cab", t, p)).pack(pady=5)
    
    def book_transport(self, transport_type, name, price):
        """Book a specific transport/hotel"""
        if not self.current_user:
            messagebox.showinfo("Login Required", "Please login to book")
            self.show_login()
            return
        
        if messagebox.askyesno("Confirm Booking", f"Book {transport_type}: {name}?\n\nPrice: ₹{price:,}"):
            orig = self.tab_from.get() if hasattr(self, 'tab_from') else (self.cab_pickup.get() if hasattr(self, 'cab_pickup') else "")
            dest = self.tab_to.get() if hasattr(self, 'tab_to') else (self.cab_drop.get() if hasattr(self, 'cab_drop') else self.hotel_city.get() if hasattr(self, 'hotel_city') else "")
            
            self.db.add_booking(self.current_user[0], transport_type.lower(), orig, dest, 
                               self.adults_var.get() + self.children_var.get(), price)
            pts = int(price / 100)
            self.db.update_points(self.current_user[0], pts)
            messagebox.showinfo("Success", f"🎉 {transport_type} Booked!\nYou earned {pts} reward points!")
            self.update_user_section()
    
    def book(self, pkg):
        if not self.current_user:
            messagebox.showinfo("Login Required", "Please login to book")
            self.show_login()
            return
        if messagebox.askyesno("Confirm Booking", f"Book {pkg['name']}?\n\nTotal: ₹{pkg['total']:,}"):
            self.db.add_booking(self.current_user[0], "package", self.from_entry.get(),
                               self.to_entry.get(), self.adults_var.get() + self.children_var.get(), pkg['total'])
            pts = int(pkg['total'] / 100)
            self.db.update_points(self.current_user[0], pts)
            messagebox.showinfo("Success", f"🎉 Booking Confirmed!\nYou earned {pts} reward points!")
            self.update_user_section()

    
    def show_login(self):
        dlg = ctk.CTkToplevel(self)
        dlg.title("Login / Sign Up")
        dlg.geometry("400x520")
        dlg.transient(self)
        dlg.grab_set()
        
        hdr = ctk.CTkFrame(dlg, fg_color=self.colors["primary"], corner_radius=0, height=70)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        ctk.CTkLabel(hdr, text="✈️ TravelEase", font=ctk.CTkFont(size=22, weight="bold"),
                    text_color=self.colors["white"]).pack(pady=20)
        
        tab_row = ctk.CTkFrame(dlg, fg_color="transparent")
        tab_row.pack(fill="x", pady=15)
        self.auth_mode = ctk.StringVar(value="login")
        
        form = ctk.CTkFrame(dlg, fg_color="transparent")
        form.pack(fill="both", expand=True, padx=30)
        
        def update_form():
            for w in form.winfo_children():
                w.destroy()
            mode = self.auth_mode.get()
            
            if mode == "signup":
                ctk.CTkLabel(form, text="Full Name", font=ctk.CTkFont(size=11),
                            text_color=self.colors["text_light"]).pack(anchor="w", pady=(8, 3))
                self.name_entry = ctk.CTkEntry(form, font=ctk.CTkFont(size=12), corner_radius=10, height=40)
                self.name_entry.pack(fill="x")
                
                ctk.CTkLabel(form, text="Phone", font=ctk.CTkFont(size=11),
                            text_color=self.colors["text_light"]).pack(anchor="w", pady=(8, 3))
                self.phone_entry = ctk.CTkEntry(form, font=ctk.CTkFont(size=12), corner_radius=10, height=40)
                self.phone_entry.pack(fill="x")
            
            ctk.CTkLabel(form, text="Email", font=ctk.CTkFont(size=11),
                        text_color=self.colors["text_light"]).pack(anchor="w", pady=(8, 3))
            self.email_entry = ctk.CTkEntry(form, font=ctk.CTkFont(size=12), corner_radius=10, height=40)
            self.email_entry.pack(fill="x")
            
            ctk.CTkLabel(form, text="Password", font=ctk.CTkFont(size=11),
                        text_color=self.colors["text_light"]).pack(anchor="w", pady=(8, 3))
            pwd_row = ctk.CTkFrame(form, fg_color="transparent")
            pwd_row.pack(fill="x")
            self.pwd_entry = ctk.CTkEntry(pwd_row, font=ctk.CTkFont(size=12), corner_radius=10, height=40, show="•")
            self.pwd_entry.pack(side="left", fill="x", expand=True)
            
            self.show_pwd = False
            def toggle():
                self.show_pwd = not self.show_pwd
                self.pwd_entry.configure(show="" if self.show_pwd else "•")
                eye.configure(text="🙈" if self.show_pwd else "👁")
            eye = ctk.CTkButton(pwd_row, text="👁", width=40, height=40, corner_radius=10,
                               fg_color=self.colors["gray"], text_color=self.colors["text"],
                               hover_color=self.colors["light_blue"], command=toggle)
            eye.pack(side="right", padx=(8, 0))
            
            btn_txt = "Sign Up" if mode == "signup" else "Login"
            ctk.CTkButton(form, text=btn_txt, font=ctk.CTkFont(size=14, weight="bold"),
                         fg_color=self.colors["primary"], corner_radius=20, height=45,
                         command=lambda: self.process_auth(dlg)).pack(fill="x", pady=25)
        
        ctk.CTkRadioButton(tab_row, text="Login", variable=self.auth_mode, value="login",
                          font=ctk.CTkFont(size=13), command=update_form).pack(side="left", expand=True)
        ctk.CTkRadioButton(tab_row, text="Sign Up", variable=self.auth_mode, value="signup",
                          font=ctk.CTkFont(size=13), command=update_form).pack(side="left", expand=True)
        
        update_form()
    
    def process_auth(self, dlg):
        mode = self.auth_mode.get()
        email, pwd = self.email_entry.get().strip(), self.pwd_entry.get().strip()
        if not email or not pwd:
            messagebox.showerror("Error", "Fill all fields")
            return
        
        if mode == "signup":
            name, phone = self.name_entry.get().strip(), self.phone_entry.get().strip()
            if not name:
                messagebox.showerror("Error", "Enter name")
                return
            if self.db.create_user(name, email, phone, pwd):
                messagebox.showinfo("Success", "Account created! Please login.")
                self.auth_mode.set("login")
            else:
                messagebox.showerror("Error", "Email already exists")
        else:
            user = self.db.get_user(email, pwd)
            if user:
                self.current_user = user
                self.update_user_section()
                dlg.destroy()
                messagebox.showinfo("Welcome", f"Welcome back, {user[1].split()[0]}!")
            else:
                messagebox.showerror("Error", "Invalid email or password")

    
    def show_profile(self):
        self.clear_content()
        
        ctk.CTkLabel(self.content, text=f"👤 {self.current_user[1]}", font=ctk.CTkFont(size=26, weight="bold"),
                    text_color=self.colors["text"]).pack(pady=25)
        
        stats_row = ctk.CTkFrame(self.content, fg_color="transparent")
        stats_row.pack(fill="x", padx=40, pady=15)
        
        for lbl, val in [("🎁 Reward Points", self.current_user[5]), ("📧 Email", self.current_user[2]),
                        ("📞 Phone", self.current_user[3] or "Not set")]:
            c = ctk.CTkFrame(stats_row, fg_color=self.colors["white"], corner_radius=15)
            c.pack(side="left", fill="both", expand=True, padx=8)
            ctk.CTkLabel(c, text=lbl, font=ctk.CTkFont(size=11), text_color=self.colors["text_light"]).pack(pady=(18, 5))
            ctk.CTkLabel(c, text=str(val), font=ctk.CTkFont(size=16, weight="bold"),
                        text_color=self.colors["text"]).pack(pady=(0, 18))
        
        ctk.CTkLabel(self.content, text="📋 My Bookings", font=ctk.CTkFont(size=18, weight="bold"),
                    text_color=self.colors["text"]).pack(anchor="w", padx=40, pady=(25, 12))
        
        bookings = self.db.get_user_bookings(self.current_user[0])
        if bookings:
            for b in bookings:
                c = ctk.CTkFrame(self.content, fg_color=self.colors["white"], corner_radius=12)
                c.pack(fill="x", padx=40, pady=4)
                ctk.CTkLabel(c, text=f"{b[3]} → {b[4]}", font=ctk.CTkFont(size=13, weight="bold"),
                            text_color=self.colors["text"]).pack(side="left", padx=18, pady=12)
                ctk.CTkLabel(c, text=f"₹{b[6]:,.0f}", font=ctk.CTkFont(size=13, weight="bold"),
                            text_color=self.colors["primary"]).pack(side="right", padx=18, pady=12)
                ctk.CTkLabel(c, text=b[7].upper(), font=ctk.CTkFont(size=10),
                            text_color=self.colors["accent"]).pack(side="right", padx=10)
        else:
            ctk.CTkLabel(self.content, text="No bookings yet. Start planning your trip!",
                        font=ctk.CTkFont(size=12), text_color=self.colors["text_light"]).pack(pady=20)
        
        ctk.CTkButton(self.content, text="← Back to Home", fg_color=self.colors["dark"],
                     corner_radius=20, command=self.show_home).pack(pady=25)
    
    def logout(self):
        self.current_user = None
        self.update_user_section()
        messagebox.showinfo("Logged Out", "You have been logged out")
        self.show_home()
    
    def show_support(self):
        self.clear_content()
        
        ctk.CTkLabel(self.content, text="💬 Customer Support", font=ctk.CTkFont(size=26, weight="bold"),
                    text_color=self.colors["text"]).pack(pady=25)
        
        contact_row = ctk.CTkFrame(self.content, fg_color="transparent")
        contact_row.pack(fill="x", padx=40, pady=15)
        
        for icon, title, val, desc in [("📞", "Phone", "1800-123-4567", "24/7 Toll Free"),
                                       ("📧", "Email", "support@travelease.com", "Response in 24hrs"),
                                       ("💬", "Live Chat", "Available Now", "Instant support")]:
            c = ctk.CTkFrame(contact_row, fg_color=self.colors["white"], corner_radius=15)
            c.pack(side="left", fill="both", expand=True, padx=8)
            ctk.CTkLabel(c, text=f"{icon} {title}", font=ctk.CTkFont(size=13, weight="bold"),
                        text_color=self.colors["text"]).pack(pady=(20, 5))
            ctk.CTkLabel(c, text=val, font=ctk.CTkFont(size=16),
                        text_color=self.colors["primary"]).pack()
            ctk.CTkLabel(c, text=desc, font=ctk.CTkFont(size=10),
                        text_color=self.colors["text_light"]).pack(pady=(3, 20))
        
        ctk.CTkLabel(self.content, text="❓ FAQs", font=ctk.CTkFont(size=18, weight="bold"),
                    text_color=self.colors["text"]).pack(anchor="w", padx=40, pady=(25, 12))
        
        faqs = [("How to cancel booking?", "Go to My Bookings and click Cancel. Refund in 5-7 days."),
               ("Payment methods?", "Credit/Debit cards, UPI, Net Banking, Wallets accepted."),
               ("How to use promo codes?", "Enter code at checkout. Discount applied automatically.")]
        for q, a in faqs:
            c = ctk.CTkFrame(self.content, fg_color=self.colors["white"], corner_radius=12)
            c.pack(fill="x", padx=40, pady=4)
            ctk.CTkLabel(c, text=q, font=ctk.CTkFont(size=12, weight="bold"),
                        text_color=self.colors["text"]).pack(anchor="w", padx=18, pady=(12, 3))
            ctk.CTkLabel(c, text=a, font=ctk.CTkFont(size=11),
                        text_color=self.colors["text_light"], wraplength=700).pack(anchor="w", padx=18, pady=(0, 12))
        
        ctk.CTkButton(self.content, text="← Back to Home", fg_color=self.colors["dark"],
                     corner_radius=20, command=self.show_home).pack(pady=25)

    
    def show_admin_login(self):
        dlg = ctk.CTkToplevel(self)
        dlg.title("Admin Login")
        dlg.geometry("340x230")
        dlg.transient(self)
        dlg.grab_set()
        
        ctk.CTkLabel(dlg, text="🔐 Admin Access", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=25)
        
        pwd = ctk.CTkEntry(dlg, font=ctk.CTkFont(size=12), corner_radius=10, height=40,
                          show="•", placeholder_text="Admin Password")
        pwd.pack(fill="x", padx=30)
        
        def verify():
            if pwd.get() == "admin123":
                dlg.destroy()
                self.show_admin()
            else:
                messagebox.showerror("Error", "Invalid password")
        
        ctk.CTkButton(dlg, text="Login", fg_color=self.colors["primary"], corner_radius=20,
                     width=120, command=verify).pack(pady=20)
        ctk.CTkLabel(dlg, text="Default: admin123", font=ctk.CTkFont(size=10),
                    text_color=self.colors["text_light"]).pack()
    
    def show_admin(self):
        self.clear_content()
        
        ctk.CTkLabel(self.content, text="🛡️ Admin Dashboard", font=ctk.CTkFont(size=26, weight="bold"),
                    text_color=self.colors["text"]).pack(pady=25)
        
        stats = self.db.get_stats()
        stats_row = ctk.CTkFrame(self.content, fg_color="transparent")
        stats_row.pack(fill="x", padx=40, pady=15)
        
        for lbl, val, clr in [("👥 Total Users", stats["total_users"], self.colors["primary"]),
                             ("📋 Total Bookings", stats["total_bookings"], self.colors["secondary"]),
                             ("💰 Total Revenue", f"₹{stats['total_revenue']:,.0f}", self.colors["accent"])]:
            c = ctk.CTkFrame(stats_row, fg_color=self.colors["white"], corner_radius=15)
            c.pack(side="left", fill="both", expand=True, padx=8)
            ctk.CTkLabel(c, text=lbl, font=ctk.CTkFont(size=11), text_color=self.colors["text_light"]).pack(pady=(20, 5))
            ctk.CTkLabel(c, text=str(val), font=ctk.CTkFont(size=24, weight="bold"), text_color=clr).pack(pady=(0, 20))
        
        ctk.CTkLabel(self.content, text="👥 All Users", font=ctk.CTkFont(size=18, weight="bold"),
                    text_color=self.colors["text"]).pack(anchor="w", padx=40, pady=(25, 12))
        
        users = self.db.get_all_users()
        for u in users:
            c = ctk.CTkFrame(self.content, fg_color=self.colors["white"], corner_radius=12)
            c.pack(fill="x", padx=40, pady=3)
            ctk.CTkLabel(c, text=f"{u[1]}", font=ctk.CTkFont(size=12, weight="bold"),
                        text_color=self.colors["text"]).pack(side="left", padx=18, pady=10)
            ctk.CTkLabel(c, text=u[2], font=ctk.CTkFont(size=11),
                        text_color=self.colors["text_light"]).pack(side="left", padx=10)
            ctk.CTkLabel(c, text=f"{u[4]} pts", font=ctk.CTkFont(size=11, weight="bold"),
                        text_color=self.colors["primary"]).pack(side="right", padx=18)
            ctk.CTkButton(c, text="🗑️", width=35, height=30, corner_radius=8,
                         fg_color="#EF4444", hover_color="#DC2626",
                         command=lambda uid=u[0]: self.delete_user(uid)).pack(side="right", padx=5)
        
        ctk.CTkButton(self.content, text="← Back to Home", fg_color=self.colors["dark"],
                     corner_radius=20, command=self.show_home).pack(pady=25)
    
    def delete_user(self, uid):
        if messagebox.askyesno("Confirm", f"Delete user ID {uid} and all bookings?"):
            self.db.delete_user(uid)
            messagebox.showinfo("Deleted", "User deleted")
            self.show_admin()


# ============== RUN APP ==============
if __name__ == "__main__":
    app = TravelEaseApp()
    app.mainloop()
