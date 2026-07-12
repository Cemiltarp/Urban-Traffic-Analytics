import pandas as pd
import numpy as np
import os

class TrafficSimulator:
    def __init__(self):
        self.input_file = "data/processed/clean_vehicle_stats.csv"
        self.output_file = "data/processed/hourly_traffic_simulation.csv"
        
    def run_simulation(self):
        print("[INFO] Starting simulation...")
        if not os.path.exists(self.input_file):
            print(f"[ERROR] Clean data not found at {self.input_file}")
            return
            
        df = pd.read_csv(self.input_file)
        
        simulation_data = []
        
        for hour in range(24):
            for index, row in df.iterrows():
                base_traffic = row['estimated_active_traffic']
                province = row['province_name']
                
                # Saatlik yoğunluk katsayısı
                if 7 <= hour <= 9 or 17 <= hour <= 19:
                    multiplier = np.random.uniform(0.8, 1.0)
                elif 0 <= hour <= 5:
                    multiplier = np.random.uniform(0.05, 0.15)
                else:
                    multiplier = np.random.uniform(0.4, 0.7)
                    
                active_vehicles = int(base_traffic * multiplier)
                
                simulation_data.append({
                    'hour': hour,
                    'province_name': province,
                    'active_vehicles': active_vehicles
                })
                
        sim_df = pd.DataFrame(simulation_data)
        os.makedirs("data/processed", exist_ok=True)
        sim_df.to_csv(self.output_file, index=False)
        print(f"[INFO] Simulation complete. Data saved to {self.output_file}")

if __name__ == "__main__":
    sim = TrafficSimulator()
    sim.run_simulation()