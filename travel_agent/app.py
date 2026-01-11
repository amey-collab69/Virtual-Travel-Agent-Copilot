"""
TravelEase - Streamlit Travel Agent Application
Deploy on Streamlit Cloud for free!
"""
import streamlit as st
import sqlite3
import hashlib
import math
import requests
from datetime import datetime, timedelta
import os

# Page config
st.set_page_config(
    page_title="TravelEase - Your Travel Companion",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for MakeMyTrip-style UI
st.markdown("""
<style>
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Main container */
    .main {
        padding: 0 !important;
    }
    
    /* Header */
    .header {
        background: linear-gradient(135deg, #0770E3 0%, #0052CC 100%);
        padding: 15px 50px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin: -80px -80px 20px -80px;
    }
    
    .logo {
        font-size: 28px;
        font-weight: bold;
        color: white;
        text-decoration: none;
    }
    
    /* Search card */
    .search-card {
        background: white;
        border-radius: 20px;
        padding: 30px;
        box-shadow: 0 10px 40px rgba(0,0,0,0.1);
        margin: -30px 20px 30px 20px;
    }
    
    /* City display */
    .city-name {
        font-size: 32px;
        font-weight: bold;
        color: #1a1a2e;
        margin: 0;
    }
    
    .airport-code {
        font-size: 12px;
        color: #666;
    }
    
    /* Buttons */
    .stButton > button {
        border-radius: 25px !important;
        font-weight: bold !important;
    }
    
    /* Cards */
    .result-card {
        background: white;
        border-radius: 15px;
        padding: 20px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.08);
        margin: 10px 0;
    }
    
    /* Price */
    .price {
        font-size: 24px;
        font-weight: bold;
        color: #0770E3;
    }
    
    .price-small {
        font-size: 14px;
        color: #666;
    }
    
    /* Package cards */
    .package-card {
        background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%);
        border-radius: 15px;
        padding: 25px;
        text-align: center;
        border: 2px solid #e0e0e0;
        transition: all 0.3s ease;
    }
    
    .package-card:hover {
        border-color: #0770E3;
        transform: translateY(-5px);
    }
    
    /* Hero section */
    .hero {
        background: linear-gradient(135deg, #0770E3 0%, #0052CC 100%);
        padding: 40px;
        border-radius: 0 0 30px 30px;
        margin: -80px -80px 30px -80px;
    }
    
    /* Trip type buttons */
    .trip-type {
        display: inline-block;
        padding: 8px 20px;
        border-radius: 20px;
        margin-right: 10px;
        cursor: pointer;
    }
    
    .trip-type.active {
        background: white;
        color: #0770E3;
    }
    
    .trip-type.inactive {
        background: transparent;
        color: white;
        border: 1px solid white;
    }
    
    /* Metric styling */
    [data-testid="stMetricValue"] {
        font-size: 28px !important;
        color: #0770E3 !important;
    }
    
    /* Input styling */
    .stTextInput > div > div > input {
        border-radius: 10px !important;
    }
    
    .stSelectbox > div > div {
        border-radius: 10px !important;
    }
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 10px;
        padding: 10px 20px;
    }
</style>
""", unsafe_allow_html=True)


# ============== DATABASE ==============
def get_database():
    conn = sqlite3.connect('travel_agent.db', check_same_thread=False)
    cursor = conn.cursor()
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        phone TEXT,
        password TEXT NOT NULL,
        points INTEGER DEFAULT 100,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS bookings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        booking_type TEXT,
        origin TEXT,
        destination TEXT,
        travelers INTEGER,
        total_cost REAL,
        status TEXT DEFAULT 'confirmed',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS locations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE,
        lat REAL,
        lng REAL,
        country TEXT,
        region TEXT,
        airport_code TEXT
    )''')
    
    # Add airport_code column if it doesn't exist (migration for old databases)
    try:
        cursor.execute("ALTER TABLE locations ADD COLUMN airport_code TEXT")
        conn.commit()
    except:
        pass  # Column already exists
    
    # Seed locations - delete old and insert fresh
    cursor.execute("DELETE FROM locations")
    locations = [
        ("Mumbai", 19.0760, 72.8777, "India", "south_asia", "BOM"),
        ("Delhi", 28.6139, 77.2090, "India", "south_asia", "DEL"),
        ("Bangalore", 12.9716, 77.5946, "India", "south_asia", "BLR"),
        ("Chennai", 13.0827, 80.2707, "India", "south_asia", "MAA"),
        ("Kolkata", 22.5726, 88.3639, "India", "south_asia", "CCU"),
        ("Hyderabad", 17.3850, 78.4867, "India", "south_asia", "HYD"),
        ("Pune", 18.5204, 73.8567, "India", "south_asia", "PNQ"),
        ("Jaipur", 26.9124, 75.7873, "India", "south_asia", "JAI"),
        ("Goa", 15.2993, 74.1240, "India", "south_asia", "GOI"),
        ("Agra", 27.1767, 78.0081, "India", "south_asia", "AGR"),
        ("Varanasi", 25.3176, 82.9739, "India", "south_asia", "VNS"),
        ("Udaipur", 24.5854, 73.7125, "India", "south_asia", "UDR"),
        ("Manali", 32.2396, 77.1887, "India", "south_asia", "KUU"),
        ("Shimla", 31.1048, 77.1734, "India", "south_asia", "SLV"),
        ("Rishikesh", 30.0869, 78.2676, "India", "south_asia", "DED"),
        ("Paris", 48.8566, 2.3522, "France", "western_europe", "CDG"),
        ("London", 51.5074, -0.1278, "UK", "western_europe", "LHR"),
        ("New York", 40.7128, -74.0060, "USA", "north_america", "JFK"),
        ("Tokyo", 35.6762, 139.6503, "Japan", "east_asia", "NRT"),
        ("Dubai", 25.2048, 55.2708, "UAE", "middle_east", "DXB"),
        ("Singapore", 1.3521, 103.8198, "Singapore", "southeast_asia", "SIN"),
        ("Bangkok", 13.7563, 100.5018, "Thailand", "southeast_asia", "BKK"),
        ("Bali", -8.4095, 115.1889, "Indonesia", "southeast_asia", "DPS"),
        ("Sydney", -33.8688, 151.2093, "Australia", "australia", "SYD"),
    ]
    cursor.executemany("INSERT OR IGNORE INTO locations (name, lat, lng, country, region, airport_code) VALUES (?, ?, ?, ?, ?, ?)", locations)
    conn.commit()
    
    return conn


def get_user(conn, email, password):
    cursor = conn.cursor()
    pwd_hash = hashlib.sha256(password.encode()).hexdigest()
    cursor.execute("SELECT * FROM users WHERE email=? AND password=?", (email, pwd_hash))
    return cursor.fetchone()


def create_user(conn, name, email, phone, password):
    cursor = conn.cursor()
    pwd_hash = hashlib.sha256(password.encode()).hexdigest()
    try:
        cursor.execute("INSERT INTO users (name, email, phone, password) VALUES (?, ?, ?, ?)", 
                      (name, email, phone, pwd_hash))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False


def get_location(conn, name):
    cursor = conn.cursor()
    cursor.execute("SELECT name, lat, lng, country, region, COALESCE(airport_code, '') as airport_code FROM locations WHERE LOWER(name) LIKE ?", (f"%{name.lower()}%",))
    return cursor.fetchone()


def get_all_locations(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM locations ORDER BY name")
    return [row[0] for row in cursor.fetchall()]


def add_booking(conn, user_id, booking_type, origin, dest, travelers, cost):
    cursor = conn.cursor()
    cursor.execute("INSERT INTO bookings (user_id, booking_type, origin, destination, travelers, total_cost) VALUES (?, ?, ?, ?, ?, ?)",
                  (user_id, booking_type, origin, dest, travelers, cost))
    conn.commit()


def get_user_bookings(conn, user_id):
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM bookings WHERE user_id=? ORDER BY created_at DESC", (user_id,))
    return cursor.fetchall()


def update_points(conn, user_id, points):
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET points = points + ? WHERE id = ?", (points, user_id))
    conn.commit()


def get_all_users(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, email, phone, points, created_at FROM users ORDER BY created_at DESC")
    return cursor.fetchall()


def get_all_bookings(conn):
    cursor = conn.cursor()
    cursor.execute("""SELECT b.id, u.name, b.booking_type, b.origin, b.destination, 
                   b.travelers, b.total_cost, b.status, b.created_at FROM bookings b 
                   JOIN users u ON b.user_id = u.id ORDER BY b.created_at DESC""")
    return cursor.fetchall()


def get_stats(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM bookings")
    total_bookings = cursor.fetchone()[0]
    cursor.execute("SELECT COALESCE(SUM(total_cost), 0) FROM bookings")
    total_revenue = cursor.fetchone()[0]
    return {"total_users": total_users, "total_bookings": total_bookings, "total_revenue": total_revenue}


# ============== LOCATION SERVICE ==============
def geocode(conn, query):
    loc = get_location(conn, query)
    if loc:
        return {"name": str(loc[0]), "lat": float(loc[1]), "lng": float(loc[2]), "country": str(loc[3]), "code": str(loc[5]) if len(loc) > 5 and loc[5] else ""}
    
    try:
        url = "https://nominatim.openstreetmap.org/search"
        headers = {"User-Agent": "TravelEase/1.0"}
        params = {"q": query, "format": "json", "limit": 1}
        response = requests.get(url, params=params, headers=headers, timeout=10)
        data = response.json()
        if data:
            result = data[0]
            parts = result.get("display_name", "").split(", ")
            return {"name": query.title(), "lat": float(result["lat"]), "lng": float(result["lon"]), 
                   "country": parts[-1] if parts else "Unknown", "code": ""}
    except:
        pass
    return None


def calculate_distance(lat1, lng1, lat2, lng2):
    R = 6371
    lat1_rad, lat2_rad = math.radians(lat1), math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lng = math.radians(lng2 - lng1)
    a = math.sin(delta_lat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lng/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))


def get_route_info(conn, origin, dest):
    origin_loc = geocode(conn, origin)
    dest_loc = geocode(conn, dest)
    if not origin_loc or not dest_loc:
        return None
    direct_distance = calculate_distance(origin_loc["lat"], origin_loc["lng"], dest_loc["lat"], dest_loc["lng"])
    road_distance = direct_distance * 1.3
    return {"origin": origin_loc, "destination": dest_loc, "distance_km": round(road_distance, 1), 
            "flight_hours": round(direct_distance / 800 + 1.5, 1)}


# ============== PRICING ENGINE ==============
def calculate_prices(distance, origin_country, dest_country, adults, children, nights):
    cost_index = {"south_asia": 1.0, "southeast_asia": 1.2, "east_asia": 2.5, "middle_east": 2.0, 
                  "western_europe": 3.5, "north_america": 3.0, "australia": 3.2}
    base_prices = {"flight_per_km": 5, "train_per_km": 0.8, "bus_per_km": 0.5, "cab_per_km": 12,
                   "hotel_budget": 800, "hotel_mid": 3000, "hotel_luxury": 12000}
    
    regions = {"south_asia": ["India", "Nepal", "Bangladesh", "Sri Lanka"], 
               "southeast_asia": ["Thailand", "Vietnam", "Indonesia", "Malaysia", "Singapore"],
               "east_asia": ["Japan", "South Korea"], "middle_east": ["UAE", "Saudi Arabia"], 
               "western_europe": ["UK", "France", "Germany", "Italy"],
               "north_america": ["USA", "Canada"], "australia": ["Australia", "New Zealand"]}
    
    def get_region(country):
        for region, countries in regions.items():
            if country in countries:
                return region
        return "south_asia"
    
    travelers = adults + children
    origin_region = get_region(origin_country)
    dest_region = get_region(dest_country)
    avg_index = (cost_index.get(origin_region, 1) + cost_index.get(dest_region, 1)) / 2
    is_international = origin_country != dest_country
    
    flight_base = base_prices["flight_per_km"] * distance * avg_index * (1.5 if is_international else 1)
    flight_economy = max(2000, min(int(flight_base * 0.8), 150000))
    flight_business = int(flight_economy * 2.5)
    
    train_prices, bus_prices = [], []
    if not is_international and distance < 2000:
        train_base = base_prices["train_per_km"] * distance * cost_index.get(origin_region, 1)
        train_prices = [{"type": "Sleeper", "price": max(200, int(train_base * 0.6))}, 
                       {"type": "AC 3-Tier", "price": max(400, int(train_base))},
                       {"type": "AC 2-Tier", "price": max(600, int(train_base * 1.5))}, 
                       {"type": "AC First", "price": max(1000, int(train_base * 2.5))}]
    if not is_international and distance < 1500:
        bus_base = base_prices["bus_per_km"] * distance * cost_index.get(origin_region, 1)
        bus_prices = [{"type": "Non-AC", "price": max(150, int(bus_base * 0.5))}, 
                     {"type": "AC Seater", "price": max(250, int(bus_base * 0.8))},
                     {"type": "AC Sleeper", "price": max(400, int(bus_base * 1.2))}, 
                     {"type": "Volvo", "price": max(600, int(bus_base * 1.8))}]
    
    cab_base = base_prices["cab_per_km"] * distance * cost_index.get(dest_region, 1)
    cab_prices = [{"type": "Sedan", "price": max(500, int(cab_base * 0.8))}, 
                 {"type": "SUV", "price": max(800, int(cab_base * 1.2))},
                 {"type": "Luxury", "price": max(1500, int(cab_base * 2))}]
    
    dest_index = cost_index.get(dest_region, 1)
    hotels = {"budget": int(base_prices["hotel_budget"] * dest_index), 
              "mid_range": int(base_prices["hotel_mid"] * dest_index), 
              "luxury": int(base_prices["hotel_luxury"] * dest_index)}
    
    rooms = max(1, (travelers + 1) // 2)
    packages = []
    
    cheapest = bus_prices[0]["price"] if bus_prices else (train_prices[0]["price"] if train_prices else flight_economy)
    budget_total = (cheapest * travelers * 2) + (hotels["budget"] * nights * rooms) + (500 * (nights + 1) * travelers)
    packages.append({"name": "💰 Budget", "total": budget_total, "per_person": budget_total // travelers, "color": "#10B981"})
    
    mid_transport = train_prices[1]["price"] if len(train_prices) > 1 else flight_economy
    comfort_total = (mid_transport * travelers * 2) + (hotels["mid_range"] * nights * rooms) + (1500 * (nights + 1) * travelers)
    packages.append({"name": "⭐ Comfort", "total": comfort_total, "per_person": comfort_total // travelers, "color": "#0770E3"})
    
    premium_total = (flight_business * travelers * 2) + (hotels["luxury"] * nights * rooms) + (4000 * (nights + 1) * travelers)
    packages.append({"name": "👑 Premium", "total": premium_total, "per_person": premium_total // travelers, "color": "#FF6B00"})
    
    return {"flights": [{"type": "Economy", "price": flight_economy}, {"type": "Business", "price": flight_business}],
            "trains": train_prices, "buses": bus_prices, "cabs": cab_prices, "hotels": hotels, "packages": packages}


# ============== SESSION STATE ==============
if 'user' not in st.session_state:
    st.session_state.user = None
if 'page' not in st.session_state:
    st.session_state.page = 'home'
if 'search_results' not in st.session_state:
    st.session_state.search_results = None


# ============== MAIN APP ==============
def main():
    conn = get_database()
    locations = get_all_locations(conn)
    
    # Header
    col1, col2, col3 = st.columns([2, 6, 2])
    with col1:
        if st.button("✈️ TravelEase", type="primary", use_container_width=True):
            st.session_state.page = 'home'
            st.session_state.search_results = None
            st.rerun()
    
    with col3:
        if st.session_state.user:
            user_col1, user_col2 = st.columns(2)
            with user_col1:
                if st.button(f"👤 {st.session_state.user[1].split()[0]}", use_container_width=True):
                    st.session_state.page = 'profile'
                    st.rerun()
            with user_col2:
                if st.button("Logout", use_container_width=True):
                    st.session_state.user = None
                    st.rerun()
        else:
            if st.button("🔐 Login / Signup", type="secondary", use_container_width=True):
                st.session_state.page = 'login'
                st.rerun()
    
    st.markdown("---")
    
    # Navigation tabs
    tabs = st.tabs(["✈️ Flights", "🏨 Hotels", "🚂 Trains", "🚌 Buses", "🚕 Cabs", "🏖️ Holidays", "🛡️ Admin"])
    
    with tabs[0]:  # Flights
        show_search_form(conn, locations, "flights")
    
    with tabs[1]:  # Hotels
        show_search_form(conn, locations, "hotels")
    
    with tabs[2]:  # Trains
        show_search_form(conn, locations, "trains")
    
    with tabs[3]:  # Buses
        show_search_form(conn, locations, "buses")
    
    with tabs[4]:  # Cabs
        show_search_form(conn, locations, "cabs")
    
    with tabs[5]:  # Holidays
        show_search_form(conn, locations, "holidays")
    
    with tabs[6]:  # Admin
        show_admin_panel(conn)
    
    # Show login modal
    if st.session_state.page == 'login':
        show_login_form(conn)
    
    # Show profile
    if st.session_state.page == 'profile' and st.session_state.user:
        show_profile(conn)


def show_search_form(conn, locations, tab_type):
    st.markdown("### 🌍 Search Your Perfect Trip")
    
    # Trip type
    col1, col2, col3 = st.columns([2, 2, 4])
    with col1:
        trip_type = st.radio("Trip Type", ["One Way", "Round Trip"], horizontal=True, label_visibility="collapsed", key=f"trip_type_{tab_type}")
    with col3:
        if trip_type == "One Way":
            st.info("📢 Book a round trip to save more!")
    
    # Search fields
    col1, col2, col3, col4 = st.columns([3, 3, 2, 2])
    
    with col1:
        st.markdown("**FROM**")
        origin = st.selectbox("Origin", locations, index=1, label_visibility="collapsed", key=f"from_{tab_type}")
        origin_loc = get_location(conn, origin)
        if origin_loc:
            st.caption(f"[{origin_loc[5] if len(origin_loc) > 5 else ''}] {origin_loc[3]}")
    
    with col2:
        st.markdown("**TO**")
        dest = st.selectbox("Destination", locations, index=0, label_visibility="collapsed", key=f"to_{tab_type}")
        dest_loc = get_location(conn, dest)
        if dest_loc:
            st.caption(f"[{dest_loc[5] if len(dest_loc) > 5 else ''}] {dest_loc[3]}")
    
    with col3:
        st.markdown("**DEPARTURE**")
        dep_date = st.date_input("Departure", datetime.now() + timedelta(days=7), label_visibility="collapsed", key=f"dep_{tab_type}")
    
    with col4:
        if trip_type == "Round Trip":
            st.markdown("**RETURN**")
            ret_date = st.date_input("Return", datetime.now() + timedelta(days=14), label_visibility="collapsed", key=f"ret_{tab_type}")
        else:
            st.markdown("**RETURN**")
            st.caption("Book round trip\nto save more")
    
    # Travelers
    st.markdown("---")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        adults = st.number_input("👨 Adults (12+ yrs)", min_value=1, max_value=9, value=1, key=f"adults_{tab_type}")
    with col2:
        children = st.number_input("👶 Children (2-12 yrs)", min_value=0, max_value=6, value=0, key=f"children_{tab_type}")
    with col3:
        nights = st.number_input("🌙 Nights", min_value=1, max_value=30, value=3, key=f"nights_{tab_type}")
    with col4:
        travel_class = st.selectbox("Class", ["Economy", "Business"], key=f"class_{tab_type}")
    
    # Special fares
    st.markdown("**Special Fares (Optional)**")
    fare_cols = st.columns(6)
    fares = ["Regular", "Student", "Senior Citizen", "Armed Forces", "Doctors", "Defence"]
    selected_fare = fare_cols[0].radio("", fares, label_visibility="collapsed", key=f"fare_{tab_type}")
    
    # Search button
    st.markdown("---")
    if st.button("🔍 SEARCH", type="primary", use_container_width=True, key=f"search_{tab_type}"):
        with st.spinner("Searching best deals..."):
            route = get_route_info(conn, origin, dest)
            if route:
                prices = calculate_prices(route["distance_km"], route["origin"]["country"],
                                         route["destination"]["country"], adults, children, nights)
                st.session_state.search_results = {"route": route, "prices": prices, 
                                                   "adults": adults, "children": children, "nights": nights}
                st.rerun()
            else:
                st.error("Could not find route. Please try different cities.")
    
    # Show results
    if st.session_state.search_results:
        show_results(conn, st.session_state.search_results, tab_type)


def show_results(conn, data, tab_type):
    route = data["route"]
    prices = data["prices"]
    travelers = data["adults"] + data["children"]
    nights = data["nights"]
    
    st.markdown("---")
    
    # Route header
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); 
                padding: 25px; border-radius: 15px; margin: 20px 0;">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <span style="font-size: 32px; font-weight: bold; color: white;">{route['origin']['name']}</span>
                <span style="color: #888; font-size: 14px;"> [{route['origin'].get('code', '')}]</span>
            </div>
            <div style="color: #00D4AA; font-size: 16px;">
                ✈️ {route['distance_km']:,.0f} km ✈️
            </div>
            <div>
                <span style="font-size: 32px; font-weight: bold; color: white;">{route['destination']['name']}</span>
                <span style="color: #888; font-size: 14px;"> [{route['destination'].get('code', '')}]</span>
            </div>
            <div style="color: white;">
                👥 {travelers} Travelers | 🌙 {nights} Nights
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Transport options
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if prices["flights"]:
            st.markdown("### ✈️ Flights")
            for flight in prices["flights"]:
                st.markdown(f"""
                <div style="background: white; padding: 15px; border-radius: 10px; margin: 10px 0; 
                            box-shadow: 0 2px 10px rgba(0,0,0,0.05);">
                    <div style="display: flex; justify-content: space-between;">
                        <span>{flight['type']}</span>
                        <span style="font-weight: bold; color: #0770E3;">₹{flight['price']:,}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
    
    with col2:
        if prices["trains"]:
            st.markdown("### 🚂 Trains")
            for train in prices["trains"]:
                st.markdown(f"""
                <div style="background: white; padding: 12px; border-radius: 10px; margin: 8px 0;
                            box-shadow: 0 2px 10px rgba(0,0,0,0.05);">
                    <div style="display: flex; justify-content: space-between;">
                        <span style="font-size: 14px;">{train['type']}</span>
                        <span style="font-weight: bold; color: #0770E3;">₹{train['price']:,}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        elif prices["buses"]:
            st.markdown("### 🚌 Buses")
            for bus in prices["buses"]:
                st.markdown(f"""
                <div style="background: white; padding: 12px; border-radius: 10px; margin: 8px 0;
                            box-shadow: 0 2px 10px rgba(0,0,0,0.05);">
                    <div style="display: flex; justify-content: space-between;">
                        <span style="font-size: 14px;">{bus['type']}</span>
                        <span style="font-weight: bold; color: #0770E3;">₹{bus['price']:,}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("### 🚕 Local Cabs")
        for cab in prices["cabs"]:
            st.markdown(f"""
            <div style="background: white; padding: 12px; border-radius: 10px; margin: 8px 0;
                        box-shadow: 0 2px 10px rgba(0,0,0,0.05);">
                <div style="display: flex; justify-content: space-between;">
                    <span style="font-size: 14px;">{cab['type']}</span>
                    <span style="font-weight: bold; color: #0770E3;">₹{cab['price']:,}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    # Packages
    st.markdown("---")
    st.markdown("### 🎁 Complete Packages")
    
    pkg_cols = st.columns(3)
    for i, pkg in enumerate(prices["packages"]):
        with pkg_cols[i]:
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%); 
                        padding: 25px; border-radius: 15px; text-align: center;
                        border: 2px solid #e0e0e0; margin: 10px 0;">
                <h3 style="margin: 0;">{pkg['name']}</h3>
                <p style="font-size: 36px; font-weight: bold; color: {pkg['color']}; margin: 15px 0;">
                    ₹{pkg['total']:,}
                </p>
                <p style="color: #666; font-size: 14px;">₹{pkg['per_person']:,} per person</p>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button(f"Book {pkg['name']}", key=f"book_{tab_type}_{i}", use_container_width=True):
                if st.session_state.user:
                    add_booking(conn, st.session_state.user[0], "package", 
                               route['origin']['name'], route['destination']['name'], 
                               travelers, pkg['total'])
                    points = int(pkg['total'] / 100)
                    update_points(conn, st.session_state.user[0], points)
                    st.success(f"🎉 Booked! You earned {points} reward points!")
                    st.balloons()
                else:
                    st.warning("Please login to book")
                    st.session_state.page = 'login'
                    st.rerun()
    
    # Hotels
    st.markdown("---")
    st.markdown("### 🏨 Hotels")
    
    hotel_cols = st.columns(3)
    hotel_types = [("Budget", "budget", "⭐⭐"), ("Mid-Range", "mid_range", "⭐⭐⭐"), ("Luxury", "luxury", "⭐⭐⭐⭐⭐")]
    
    for i, (name, key, stars) in enumerate(hotel_types):
        with hotel_cols[i]:
            price = prices["hotels"][key]
            st.markdown(f"""
            <div style="background: white; padding: 20px; border-radius: 15px; text-align: center;
                        box-shadow: 0 4px 15px rgba(0,0,0,0.08);">
                <h4>{name}</h4>
                <p style="color: #FF6B00;">{stars}</p>
                <p style="font-size: 24px; font-weight: bold; color: #0770E3;">₹{price:,}/night</p>
                <p style="color: #666; font-size: 12px;">Total: ₹{price * nights:,} for {nights} nights</p>
            </div>
            """, unsafe_allow_html=True)


def show_login_form(conn):
    st.markdown("---")
    st.markdown("### 🔐 Login / Sign Up")
    
    tab1, tab2 = st.tabs(["Login", "Sign Up"])
    
    with tab1:
        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            
            if st.form_submit_button("Login", type="primary", use_container_width=True):
                user = get_user(conn, email, password)
                if user:
                    st.session_state.user = user
                    st.session_state.page = 'home'
                    st.success(f"Welcome back, {user[1].split()[0]}!")
                    st.rerun()
                else:
                    st.error("Invalid email or password")
    
    with tab2:
        with st.form("signup_form"):
            name = st.text_input("Full Name")
            email = st.text_input("Email", key="signup_email")
            phone = st.text_input("Phone")
            password = st.text_input("Password", type="password", key="signup_pwd")
            
            if st.form_submit_button("Sign Up", type="primary", use_container_width=True):
                if name and email and password:
                    if create_user(conn, name, email, phone, password):
                        st.success("Account created! Please login.")
                    else:
                        st.error("Email already exists")
                else:
                    st.error("Please fill all required fields")
    
    if st.button("← Back to Home"):
        st.session_state.page = 'home'
        st.rerun()


def show_profile(conn):
    st.markdown("---")
    user = st.session_state.user
    
    st.markdown(f"### 👤 Welcome, {user[1]}!")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("🎁 Reward Points", user[5])
    with col2:
        st.metric("📧 Email", user[2])
    with col3:
        st.metric("📞 Phone", user[3] or "Not provided")
    
    st.markdown("---")
    st.markdown("### 📋 My Bookings")
    
    bookings = get_user_bookings(conn, user[0])
    if bookings:
        for b in bookings:
            col1, col2, col3 = st.columns([4, 2, 2])
            with col1:
                st.markdown(f"**{b[3]} → {b[4]}**")
            with col2:
                st.markdown(f"👥 {b[5]} travelers")
            with col3:
                st.markdown(f"**₹{b[6]:,.0f}**")
            st.markdown("---")
    else:
        st.info("No bookings yet. Start planning your trip!")
    
    if st.button("← Back to Home"):
        st.session_state.page = 'home'
        st.rerun()


def show_admin_panel(conn):
    st.markdown("### 🛡️ Admin Dashboard")
    
    password = st.text_input("Admin Password", type="password", key="admin_pwd")
    
    if password == "admin123":
        stats = get_stats(conn)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("👥 Total Users", stats["total_users"])
        with col2:
            st.metric("📋 Total Bookings", stats["total_bookings"])
        with col3:
            st.metric("💰 Total Revenue", f"₹{stats['total_revenue']:,.0f}")
        
        st.markdown("---")
        
        # Users
        st.markdown("### 👥 All Users")
        users = get_all_users(conn)
        if users:
            for u in users:
                col1, col2, col3, col4 = st.columns([3, 3, 2, 2])
                with col1:
                    st.write(f"**{u[1]}**")
                with col2:
                    st.write(u[2])
                with col3:
                    st.write(f"📞 {u[3] or 'N/A'}")
                with col4:
                    st.write(f"🎁 {u[4]} pts")
        
        st.markdown("---")
        
        # Bookings
        st.markdown("### 📋 All Bookings")
        bookings = get_all_bookings(conn)
        if bookings:
            for b in bookings:
                col1, col2, col3, col4 = st.columns([2, 3, 2, 2])
                with col1:
                    st.write(f"**{b[1]}**")
                with col2:
                    st.write(f"{b[3]} → {b[4]}")
                with col3:
                    st.write(f"👥 {b[5]}")
                with col4:
                    st.write(f"**₹{b[6]:,.0f}**")
    elif password:
        st.error("Invalid admin password. Default: admin123")


if __name__ == "__main__":
    main()
