import streamlit as st
import pandas as pd
import pydeck as pdk
import os

# Tüm ekranı kaplayan gerçek bir dashboard görünümü
st.set_page_config(page_title="Urban Traffic Analytics", page_icon="🚦", layout="wide")

st.title("🚦 Urban Traffic Analytics Dashboard")
st.markdown("Türkiye geneli saatlik trafik yoğunluğu analiz ve simülasyon platformu.")

@st.cache_data
def load_data():
    file_path = "data/processed/hourly_traffic_simulation.csv"
    if not os.path.exists(file_path):
        return None
    
    df = pd.read_csv(file_path)
    
    coords = {
        "Istanbul": {"lat": 41.0082, "lon": 28.9784},
        "Ankara": {"lat": 39.9334, "lon": 32.8597},
        "Izmir": {"lat": 38.4192, "lon": 27.1287},
        "Bursa": {"lat": 40.1826, "lon": 29.0669},
        "Antalya": {"lat": 36.8969, "lon": 30.7133}
    }
    
    df['lat'] = df['province_name'].map(lambda x: coords.get(x, {}).get('lat', 39.0))
    df['lon'] = df['province_name'].map(lambda x: coords.get(x, {}).get('lon', 35.0))
    
    return df

df = load_data()

if df is None:
    st.error("[SYSTEM ERROR] Data not found! Please run `python src/simulator.py` first.")
else:
    # Sol Menü (Kontrolcü)
    st.sidebar.header("🕹️ Kontrol Paneli")
    selected_hour = st.sidebar.slider("Günün Saatini Kaydır", min_value=0, max_value=23, value=8, step=1)
    
    filtered_df = df[df['hour'] == selected_hour]
    total_traffic = filtered_df['active_vehicles'].sum()
    max_city = filtered_df.loc[filtered_df['active_vehicles'].idxmax()]['province_name']
    
    # Şık Metrik Kutucukları (Dashboard Tasarımı)
    col1, col2, col3 = st.columns(3)
    col1.metric(label="Seçilen Saat", value=f"{selected_hour:02d}:00")
    col2.metric(label="Toplam Aktif Araç", value=f"{total_traffic:,}")
    col3.metric(label="En Yoğun Şehir", value=max_city)
    
    st.markdown("---")
    
    # Silindirler (ColumnLayer) yerine Organik Isı Haritası (HeatmapLayer)
    layer = pdk.Layer(
        "HeatmapLayer",
        data=filtered_df,
        opacity=0.8,
        get_position=["lon", "lat"],
        get_weight="active_vehicles",
        radiusPixels=60, # Yayılım büyüklüğü
    )

    # Türkiye sınırlarına kamerayı kilitleme
    view_state = pdk.ViewState(
        latitude=39.0, 
        longitude=35.0, 
        zoom=5, 
        min_zoom=4.5,  # Uzaydan bakmayı engeller (Türkiye dışına çıkılamaz)
        max_zoom=8,    # Mahalle arasına kadar inmeyi engeller
        pitch=30,      # Daha estetik, hafif eğimli bir 3D açı
        bearing=0
    )

    st.pydeck_chart(pdk.Deck(
        map_provider="carto",
        map_style="dark",
        layers=[layer],
        initial_view_state=view_state,
    ))