import streamlit as st
import pandas as pd
import pydeck as pdk
import sqlite3
import os
from src.cities import CITIES

st.set_page_config(page_title="Urban Traffic Analytics", page_icon="🚦", layout="wide")

st.title("🚦 Urban Traffic Analytics Dashboard")
st.markdown("Türkiye geneli 81 ilin gerçek zamanlı trafik sıkışıklık yüzdesi.")

@st.cache_data(ttl=60)
def load_data():
    db_path = "data/traffic_history.db"
    if not os.path.exists(db_path):
        return None
    
    conn = sqlite3.connect(db_path)
    df = pd.read_sql_query("SELECT * FROM traffic_data", conn)
    conn.close()
    
    df['lat'] = df['province_name'].map(lambda x: CITIES.get(x, {}).get('lat', 39.0))
    df['lon'] = df['province_name'].map(lambda x: CITIES.get(x, {}).get('lon', 35.0))
    
    # Trafik yüzdesine göre renk ataması (Yeşilden Kırmızıya)
    df['color_r'] = (df['congestion_level'] * 2.55).astype(int)
    df['color_g'] = ((100 - df['congestion_level']) * 2.55).astype(int)
    
    return df

df = load_data()

if df is None or df.empty:
    st.error("[SYSTEM ERROR] Veritabanı bulunamadı. Lütfen fetcher'ı çalıştırın.")
else:
    st.sidebar.header("🕹️ Zaman Makinesi")
    timestamps = sorted(df['timestamp'].unique(), reverse=True)
    
    if not timestamps:
        st.warning("Veri bekleniyor...")
    else:
        selected_time = st.sidebar.selectbox("Geçmişe Git (Zaman Damgası)", timestamps)
        filtered_df = df[df['timestamp'] == selected_time]
        
        # Ortalama sıkışıklığı hesapla
        avg_congestion = int(filtered_df['congestion_level'].mean())
        max_city = filtered_df.loc[filtered_df['congestion_level'].idxmax()]['province_name']
        max_value = filtered_df['congestion_level'].max()
        
        col1, col2, col3 = st.columns(3)
        col1.metric(label="Seçilen An", value=selected_time.split(" ")[1])
        col2.metric(label="Türkiye Ortalaması", value=f"% {avg_congestion}")
        col3.metric(label="En Tıkalı Şehir", value=f"{max_city} (%{max_value})")
        
        st.markdown("---")
        
        # Birbirine girmeyen, şehir bazlı keskin noktalar (Scatterplot)
        layer = pdk.Layer(
            "ScatterplotLayer",
            data=filtered_df,
            get_position=["lon", "lat"],
            get_radius=18000, # Nokta boyutu
            get_fill_color="[color_r, color_g, 0, 200]",
            pickable=True,
            auto_highlight=True
        )

        view_state = pdk.ViewState(
            latitude=39.0, longitude=35.0, zoom=4.8, min_zoom=4.5, max_zoom=8, pitch=30, bearing=0
        )

        st.pydeck_chart(pdk.Deck(
            map_provider="carto", map_style="dark", layers=[layer],
            initial_view_state=view_state,
            tooltip={"text": "{province_name}\nTrafik Sıkışıklığı: %{congestion_level}"}
        ))