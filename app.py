import streamlit as st
import pandas as pd
import pydeck as pdk
import sqlite3
import os
from src.cities import CITIES # 81 ilin koordinatlarını buradan çekiyoruz

st.set_page_config(page_title="Urban Traffic Analytics", page_icon="🚦", layout="wide")

st.title("🚦 Urban Traffic Analytics Dashboard")
st.markdown("Türkiye geneli 81 ilin gerçek zamanlı trafik yoğunluğu analiz platformu.")

# Veritabanından veriyi çekme (ttl=60 ile her 1 dakikada bir önbelleği yeniler)
@st.cache_data(ttl=60)
def load_data():
    db_path = "data/traffic_history.db"
    if not os.path.exists(db_path):
        return None
    
    # SQLite veritabanına bağlanıp tüm tabloyu okuyoruz
    conn = sqlite3.connect(db_path)
    df = pd.read_sql_query("SELECT * FROM traffic_data", conn)
    conn.close()
    
    # Şehir isimlerini eşleştirerek koordinatları (lat, lon) DataFrame'e ekliyoruz
    df['lat'] = df['province_name'].map(lambda x: CITIES.get(x, {}).get('lat', 39.0))
    df['lon'] = df['province_name'].map(lambda x: CITIES.get(x, {}).get('lon', 35.0))
    
    return df

df = load_data()

if df is None or df.empty:
    st.error("[SYSTEM ERROR] Veritabanı bulunamadı veya boş! Lütfen `python src/data_fetcher.py` komutunu çalıştırın.")
else:
    st.sidebar.header("🕹️ Zaman Makinesi")
    
    # Veritabanındaki çekilmiş veri saatlerini al ve en yenisi en üstte olacak şekilde sırala
    timestamps = sorted(df['timestamp'].unique(), reverse=True)
    
    if not timestamps:
        st.warning("Henüz hiç trafik verisi kaydedilmemiş.")
    else:
        # Kullanıcıya daha önce kaydedilmiş saatleri seçtir (Geriye sarma özelliği)
        selected_time = st.sidebar.selectbox("Geçmişe Git (Zaman Damgası)", timestamps)
        
        # Seçilen saate göre veriyi filtrele
        filtered_df = df[df['timestamp'] == selected_time]
        total_traffic = filtered_df['active_vehicles'].sum()
        
        # En yoğun şehri bul
        max_city = "Bilinmiyor"
        if not filtered_df.empty:
            max_city = filtered_df.loc[filtered_df['active_vehicles'].idxmax()]['province_name']
        
        # Metrik Kutucukları
        col1, col2, col3 = st.columns(3)
        col1.metric(label="Seçilen An", value=selected_time.split(" ")[1]) # Sadece saati göster
        col2.metric(label="Toplam Aktif Araç", value=f"{total_traffic:,}")
        col3.metric(label="En Yoğun Şehir", value=max_city)
        
        st.markdown("---")
        
        # 81 ili kapsayan ısı haritası
        layer = pdk.Layer(
            "HeatmapLayer",
            data=filtered_df,
            opacity=0.8,
            get_position=["lon", "lat"],
            get_weight="active_vehicles",
            radiusPixels=45, # Tüm Türkiye'ye sığması için biraz küçülttük
        )

        view_state = pdk.ViewState(
            latitude=39.0, 
            longitude=35.0, 
            zoom=4.8, 
            min_zoom=4.5,
            max_zoom=8,
            pitch=30,
            bearing=0
        )

        st.pydeck_chart(pdk.Deck(
            map_provider="carto",
            map_style="dark",
            layers=[layer],
            initial_view_state=view_state,
        ))