import pandas as pd
import os

class TrafficDataPipeline:
    def __init__(self):
        self.raw_data_path = "data/raw/tuik_vehicle_stats.csv"
        self.processed_data_path = "data/processed/clean_vehicle_stats.csv"

    def process_data(self):
        print("[INFO] Starting data pipeline for REAL data...")
        
        if not os.path.exists(self.raw_data_path):
            print(f"[ERROR] Real data not found at {self.raw_data_path}!")
            return
            
        df = pd.read_csv(self.raw_data_path)
        df = df.dropna()
        
        os.makedirs("data/processed", exist_ok=True)
        df.to_csv(self.processed_data_path, index=False)
        
        print(f"[INFO] Real data successfully cleaned and saved to {self.processed_data_path}")

if __name__ == "__main__":
    pipeline = TrafficDataPipeline()
    pipeline.process_data()