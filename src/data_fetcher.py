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
        # ÇİFT CEPHANE SİSTEMİ: İki anahtarı da listeye alıyoruz
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

    # O anki aktif API anahtarını getirir
    def get_current_key(self):
        return self.api_keys[self.active_key_index]

    # Kota dolduğunda sistemi yedek hesaba geçirir
    def switch_key(self):
        if self.active_key_index < len(self.api_keys) - 1:
            self.active_key_index += 1
            print(f"\n[ALERT] 1. API Anahtarının kotası doldu! Şarjör değiştiriliyor... 2. Anahtara (Yedek) geçildi!")
            return True
        else:
            print(f"\n[CRITICAL] Tüm API hesaplarının kotası doldu! Lojistik destek kesildi.")
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
                    
                    if response.status_code == 200: # Başarılı atış
                        data = response.json()
                        current_speed = data['flowSegmentData']['currentSpeed']
                        free_flow = data['flowSegmentData']['freeFlowSpeed']
                        
                        if free_flow > 0:
                            total_current += current_speed
                            total_free += free_flow
                            valid_points += 1
                        success = True 
                        
                    elif response.status_code in [403, 429]: # Kota aşıldı hatası!
                        # Yedek anahtara geçmeyi dene
                        if not self.switch_key(): 
                            return 0 # Yedek de bittiyse şehri atla
                        # Yedek anahtara geçildiyse "while" döngüsü bu noktayı yeni anahtarla tekrar vurmayı dener
                        
                    else:
                        success = True # Farklı bir anlık sunucu hatasıysa döngüde takılmamak için atla
                        
                except Exception:
                    success = True 
                    
                time.sleep(0.1)

        if valid_points > 0 and total_free > 0:
            congestion = int(((total_free - total_current) / total_free) * 100)
            return max(0, min(100, congestion))
        return 0

    def collect_and_save(self):
        print(f"[INFO] Çoklu API Sistemi Devrede! Akıllı tarama başlatıldı...")
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
        print(f"[SUCCESS] Veri tabanı güncellendi! Toplam il: {success_count}/81\n")

if __name__ == "__main__":
    fetcher = TrafficFetcher()
    
    # Sistemin çift hesapla test atışı
    fetcher.collect_and_save()
    
    # Artık elimizde 5000 limit var! Zamanlayıcıyı daha özgürce kullanabiliriz.
    # Sabah, öğle, akşam üzeri ve gece yoklamaları.
    schedule.every().day.at("07:00").do(fetcher.collect_and_save)
    schedule.every().day.at("08:00").do(fetcher.collect_and_save)
    schedule.every().day.at("09:00").do(fetcher.collect_and_save)
    schedule.every().day.at("12:00").do(fetcher.collect_and_save)
    schedule.every().day.at("17:00").do(fetcher.collect_and_save)
    schedule.every().day.at("18:00").do(fetcher.collect_and_save)
    schedule.every().day.at("19:00").do(fetcher.collect_and_save)
    schedule.every().day.at("20:00").do(fetcher.collect_and_save)
    
    print("\n[SYSTEM] 🎯 Çift API'li Akıllı Zamanlayıcı Aktif!")
    print("[SYSTEM] Kotamız 5000'e çıktığı için günde 8 pik saatte geniş tarama yapılacaktır.")
    
    while True:
        schedule.run_pending()
        time.sleep(1)