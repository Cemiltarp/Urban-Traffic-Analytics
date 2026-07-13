import os
import sqlite3
import requests
import time
import schedule
from datetime import datetime
from dotenv import load_dotenv, find_dotenv
from cities import CITIES 

load_dotenv(find_dotenv())

BIG_CITIES = [
    "Istanbul", "Ankara", "Izmir", "Bursa", "Antalya", 
    "Adana", "Konya", "Gaziantep", "Kocaeli", "Mersin"
]

class TrafficFetcher:
    def __init__(self):
        self.db_path = "data/traffic_history.db"
        # Store both API keys for failover mechanism
        self.api_keys = [
            os.getenv("TOMTOM_API_KEY_1"),
            os.getenv("TOMTOM_API_KEY_2")
        ]
        self.active_key_index = 0
        self.setup_database()

    def setup_database(self):
        os.makedirs("data", exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS traffic_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME,
                province_name TEXT,
                congestion_level INTEGER,
                source TEXT
            )
        ''')
        conn.commit()
        conn.close()

    # Retrieve the currently active API key
    def get_current_key(self):
        return self.api_keys[self.active_key_index]

    # Switch to the backup API key when quota is exceeded
    def switch_key(self):
        if self.active_key_index < len(self.api_keys) - 1:
            self.active_key_index += 1
            print(f"\n[ALERT] Quota limit reached for API Key 1. Switching to backup API Key (Key 2).")
            return True
        else:
            print(f"\n[CRITICAL] All API accounts have reached their daily quota limits.")
            return False

    def fetch_tomtom_data(self, city_name, base_lat, base_lon):
        step = 0.04 
        
        if city_name in BIG_CITIES:
            grid_points = [(0, 0), (step, 0), (-step, 0), (0, step), (0, -step), (step, step), (-step, -step), (step, -step), (-step, step)]
        else:
            grid_points = [(0, 0), (step, 0), (-step, 0), (0, step), (0, -step)]
            
        total_current = 0
        total_free = 0
        valid_points = 0

        for d_lat, d_lon in grid_points:
            target_lat = base_lat + d_lat
            target_lon = base_lon + d_lon
            
            success = False
            while not success:
                current_api_key = self.get_current_key()
                if not current_api_key:
                    return 0

                url = f"https://api.tomtom.com/traffic/services/4/flowSegmentData/absolute/10/json?key={current_api_key}&point={target_lat},{target_lon}"
                
                try:
                    response = requests.get(url, timeout=5)
                    
                    if response.status_code == 200: 
                        data = response.json()
                        current_speed = data['flowSegmentData']['currentSpeed']
                        free_flow = data['flowSegmentData']['freeFlowSpeed']
                        
                        if free_flow > 0:
                            total_current += current_speed
                            total_free += free_flow
                            valid_points += 1
                        success = True 
                        
                    elif response.status_code in [403, 429]: # Quota exceeded error
                        # Attempt failover to backup key
                        if not self.switch_key(): 
                            return 0 # Skip region if all quotas are exhausted
                        # Loop restarts and retries the same coordinates with the new key
                        
                    else:
                        success = True # Skip coordinate on other server errors to prevent infinite loops
                        
                except Exception:
                    success = True 
                    
                time.sleep(0.1)

        if valid_points > 0 and total_free > 0:
            congestion = int(((total_free - total_current) / total_free) * 100)
            return max(0, min(100, congestion))
        return 0

    def collect_and_save(self):
        print(f"[INFO] API Failover System Active. Fetching data...")
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:00")
        success_count = 0

        for city, coords in CITIES.items():
            congestion = self.fetch_tomtom_data(city, coords["lat"], coords["lon"])
            
            cursor.execute(
                "INSERT INTO traffic_data (timestamp, province_name, congestion_level, source) VALUES (?, ?, ?, ?)",
                (current_time, city, congestion, "TomTom-DualAPI")
            )
            success_count += 1
            
        conn.commit()
        conn.close()
        print(f"[SUCCESS] Database updated! Total provinces: {success_count}/81\n")

if __name__ == "__main__":
    fetcher = TrafficFetcher()
    
    # Initial data fetch upon startup
    fetcher.collect_and_save()
    
    # Schedule data collection during peak traffic hours
    schedule.every().day.at("07:00").do(fetcher.collect_and_save)
    schedule.every().day.at("08:00").do(fetcher.collect_and_save)
    schedule.every().day.at("09:00").do(fetcher.collect_and_save)
    schedule.every().day.at("12:00").do(fetcher.collect_and_save)
    schedule.every().day.at("17:00").do(fetcher.collect_and_save)
    schedule.every().day.at("18:00").do(fetcher.collect_and_save)
    schedule.every().day.at("19:00").do(fetcher.collect_and_save)
    schedule.every().day.at("20:00").do(fetcher.collect_and_save)
    
    print("[SYSTEM] Scheduler active. Scanning will be conducted during 8 peak hours.")
    
    while True:
        schedule.run_pending()
        time.sleep(1)