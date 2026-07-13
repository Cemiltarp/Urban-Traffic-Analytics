import os
import sqlite3
import requests
import time
from datetime import datetime
from dotenv import load_dotenv, find_dotenv
from cities import CITIES 

load_dotenv(find_dotenv())
TOMTOM_API_KEY = os.getenv("TOMTOM_API_KEY")

# 9 Radar atılacak metropoller listesi
BIG_CITIES = [
    "Istanbul", "Ankara", "Izmir", "Bursa", "Antalya", 
    "Adana", "Konya", "Gaziantep", "Kocaeli", "Mersin"
]

class TrafficFetcher:
    def __init__(self):
        self.db_path = "data/traffic_history.db"
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

    def fetch_tomtom_data(self, city_name, base_lat, base_lon):
        step = 0.04 # Yaklaşık 4.5 - 5 km mesafe adımı
        
        # MÜHENDİSLİK OPTİMİZASYONU: Şehrin çapına göre radar sayısını belirliyoruz
        if city_name in BIG_CITIES:
            # 9 Nokta (3x3 Dev Ağ) - Metropoller için
            grid_points = [
                (0, 0), (step, 0), (-step, 0),
                (0, step), (0, -step),
                (step, step), (-step, -step),
                (step, -step), (-step, step)
            ]
        else:
            # 5 Nokta (Artı Şeklinde Ağ) - Küçük ve orta şehirler için
            grid_points = [
                (0, 0), (step, 0), (-step, 0),
                (0, step), (0, -step)
            ]
            
        total_current = 0
        total_free = 0
        valid_points = 0

        for d_lat, d_lon in grid_points:
            target_lat = base_lat + d_lat
            target_lon = base_lon + d_lon
            url = f"https://api.tomtom.com/traffic/services/4/flowSegmentData/absolute/10/json?key={TOMTOM_API_KEY}&point={target_lat},{target_lon}"
            
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
                
                # API kotasını korumak için kısa uyku
                time.sleep(0.1) 
            except Exception:
                continue

        if valid_points > 0 and total_free > 0:
            congestion = int(((total_free - total_current) / total_free) * 100)
            return max(0, min(100, congestion))
        return 0

    def collect_and_save(self):
        print(f"[INFO] Dinamik Tarama Ağı başlatıldı. Büyük şehirlere 9, diğerlerine 5 radar atılıyor...")
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:00")
        success_count = 0

        for city, coords in CITIES.items():
            print(f"> {city} taranıyor...")
            congestion = self.fetch_tomtom_data(city, coords["lat"], coords["lon"])
            
            cursor.execute(
                "INSERT INTO traffic_data (timestamp, province_name, congestion_level, source) VALUES (?, ?, ?, ?)",
                (current_time, city, congestion, "TomTom-DynamicGrid")
            )
            success_count += 1
            
        conn.commit()
        conn.close()
        print(f"[SUCCESS] Optimize edilmiş gerçekçi veri tabanı güncellendi! Toplam il: {success_count}/81")

if __name__ == "__main__":
    fetcher = TrafficFetcher()
    fetcher.collect_and_save()