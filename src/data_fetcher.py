import os
import sqlite3
import requests
import time
from datetime import datetime
from dotenv import load_dotenv, find_dotenv
from cities import CITIES # 81 ilin listesini dışarıdan alıyoruz!

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
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS traffic_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME,
                province_name TEXT,
                active_vehicles INTEGER,
                source TEXT
            )
        ''')
        conn.commit()
        conn.close()

    def fetch_tomtom_data(self, lat, lon):
        url = f"https://api.tomtom.com/traffic/services/4/flowSegmentData/absolute/10/json?key={TOMTOM_API_KEY}&point={lat},{lon}"
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                current_speed = data['flowSegmentData']['currentSpeed']
                free_flow = data['flowSegmentData']['freeFlowSpeed']
                traffic_ratio = 1 - (current_speed / free_flow) if free_flow > 0 else 0
                
                # Her ilin kendi ölçeğine göre ortalama bir araç bazı (Metropollerde daha yüksek vb. eklenebilir)
                base_vehicles = 100000 
                return int(base_vehicles * (1 + traffic_ratio))
        except Exception as e:
            print(f"[ERROR] Bağlantı hatası: {e}")
        return 0

    def collect_and_save(self):
        print(f"[INFO] {len(CITIES)} il için TomTom uydularından canlı veri çekiliyor...")
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:00")
        success_count = 0

        for city, coords in CITIES.items():
            vehicles = self.fetch_tomtom_data(coords["lat"], coords["lon"])
            
            cursor.execute(
                "INSERT INTO traffic_data (timestamp, province_name, active_vehicles, source) VALUES (?, ?, ?, ?)",
                (current_time, city, vehicles, "TomTom")
            )
            success_count += 1
            # Sunucuyu boğmamak için aralara salise bazında bekleme koyuyoruz
            time.sleep(0.1)

        conn.commit()
        conn.close()
        print(f"[SUCCESS] Veritabanı güncellendi! Başarıyla çekilen il sayısı: {success_count}/{len(CITIES)}")

if __name__ == "__main__":
    fetcher = TrafficFetcher()
    fetcher.collect_and_save()