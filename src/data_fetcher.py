import os
import sqlite3
import requests
import time
from datetime import datetime
from dotenv import load_dotenv, find_dotenv
from cities import CITIES 

load_dotenv(find_dotenv())
TOMTOM_API_KEY = os.getenv("TOMTOM_API_KEY")

class TrafficFetcher:
    def __init__(self):
        self.db_path = "data/traffic_history.db"
        self.setup_database()

    def setup_database(self):
        os.makedirs("data", exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        # Tabloyu 'congestion_level' (Sıkışıklık Yüzdesi) olarak güncelledik
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

    def fetch_tomtom_data(self, city_name, lat, lon):
        url = f"https://api.tomtom.com/traffic/services/4/flowSegmentData/absolute/10/json?key={TOMTOM_API_KEY}&point={lat},{lon}"
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                current_speed = data['flowSegmentData']['currentSpeed']
                free_flow = data['flowSegmentData']['freeFlowSpeed']
                
                # Sadece saf bir yüzde hesabı: Yol yüzde kaç kilitli? (0-100 arası)
                if free_flow > 0:
                    congestion = int(((free_flow - current_speed) / free_flow) * 100)
                    return max(0, congestion)
        except Exception as e:
            print(f"[ERROR] {city_name} için bağlantı hatası: {e}")
        return 0

    def collect_and_save(self):
        print(f"[INFO] 81 il için SAF TomTom trafik sıkışıklık verisi çekiliyor...")
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:00")
        success_count = 0

        for city, coords in CITIES.items():
            congestion = self.fetch_tomtom_data(city, coords["lat"], coords["lon"])
            
            cursor.execute(
                "INSERT INTO traffic_data (timestamp, province_name, congestion_level, source) VALUES (?, ?, ?, ?)",
                (current_time, city, congestion, "TomTom")
            )
            success_count += 1
            time.sleep(0.1)

        conn.commit()
        conn.close()
        print(f"[SUCCESS] Temiz veri güncellendi! {success_count}/81")

if __name__ == "__main__":
    fetcher = TrafficFetcher()
    fetcher.collect_and_save()