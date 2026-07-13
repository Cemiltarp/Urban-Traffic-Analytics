import streamlit as st
import pandas as pd
import pydeck as pdk
import sqlite3
import os
from src.cities import CITIES
from streamlit_autorefresh import st_autorefresh

# Ekranı tam genişlikte (wide) kullanıyoruz ki paneller sığsın
st.set_page_config(page_title="Urban Traffic Analytics", page_icon="🚦", layout="wide")

# Sayfayı 60 saniyede bir otomatik yenile
st_autorefresh(interval=60000, limit=None, key="traffic_refresh")

st.title("🚦 Taktiksel Trafik Komuta Merkezi")
st.markdown("Türkiye geneli 81 ilin gerçek zamanlı ve tarihsel trafik sıkışıklık analizi.")

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
    
    # 1. YENİLİK: Taktiksel Renk ve Boyut Algoritması
    def get_tactical_color(congestion):
        if congestion < 20:
            return [0, 255, 0, 160]      # Akıcı: Şeffaf Yeşil
        elif congestion < 40:
            return [255, 215, 0, 200]    # Yoğun: Parlak Sarı
        elif congestion < 60:
            return [255, 140, 0, 220]    # Sıkışık: Turuncu
        else:
            return [255, 0, 0, 255]      # Kilitli: Koyu Kırmızı (Alarm)
            
    df['color'] = df['congestion_level'].apply(get_tactical_color)
    # Trafik arttıkça yarıçap (radius) büyür
    df['radius'] = df['congestion_level'].apply(lambda x: 10000 + (x * 450)) 
    
    return df

df = load_data()

if df is None or df.empty:
    st.error("[SYSTEM ERROR] Veritabanı bulunamadı. Lütfen arka planda toplayıcıyı (fetcher) çalıştırın.")
else:
    st.sidebar.header("🕹️ Zaman Makinesi & Filtreler")
    timestamps = sorted(df['timestamp'].unique(), reverse=True)
    selected_time = st.sidebar.selectbox("Geçmişe Git (Zaman Damgası)", timestamps)
    
    filtered_df = df[df['timestamp'] == selected_time]
    
    # --- ÜST METRİK PANELİ ---
    avg_congestion = int(filtered_df['congestion_level'].mean())
    max_city = filtered_df.loc[filtered_df['congestion_level'].idxmax()]['province_name']
    max_value = filtered_df['congestion_level'].max()
    
    # 2. YENİLİK: Kritik eşik (>%50) sayacı
    critical_cities = len(filtered_df[filtered_df['congestion_level'] >= 50])
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric(label="Seçilen An", value=selected_time.split(" ")[1])
    col2.metric(label="Türkiye Ortalaması", value=f"% {avg_congestion}")
    col3.metric(label="En Tıkalı Şehir", value=f"{max_city} (%{max_value})")
    col4.metric(
        label="Kritik Şehirler (>%50)", 
        value=f"{critical_cities} Şehir", 
        delta="-Acil Durum" if critical_cities > 0 else "Normal", 
        delta_color="inverse"
    )
    
    st.markdown("---")
    
    # --- 3. YENİLİK: BÖLÜNMÜŞ EKRAN (Sol: Harita, Sağ: Grafikler) ---
    map_col, chart_col = st.columns([2, 1]) # Harita 2 birim, grafikler 1 birim yer kaplar
    
    with map_col:
        st.subheader("🗺️ Canlı Taktik Harita")
        layer = pdk.Layer(
            "ScatterplotLayer",
            data=filtered_df,
            get_position=["lon", "lat"],
            get_radius="radius", 
            get_fill_color="color",
            pickable=True,
            auto_highlight=True
        )

        view_state = pdk.ViewState(
            latitude=39.0, longitude=35.0, zoom=4.8, pitch=35, bearing=0
        )

        st.pydeck_chart(pdk.Deck(
            map_provider="carto", map_style="dark", layers=[layer],
            initial_view_state=view_state,
            tooltip={"text": "{province_name}\nTrafik Sıkışıklığı: %{congestion_level}"}
        ))
        
    with chart_col:
        st.subheader("🔥 Kriz Bölgeleri (Top 5)")
        # En yoğun 5 şehri bulup bar grafiğine döküyoruz
        top_5 = filtered_df.nlargest(5, 'congestion_level')[['province_name', 'congestion_level']]
        top_5.set_index('province_name', inplace=True)
        st.bar_chart(top_5, color="#ff4b4b") # Kırmızı renkli barlar
        
        st.markdown("<br>", unsafe_allow_html=True) # Araya biraz boşluk
        
        st.subheader("📈 Trafik Nabzı (Günlük Trend)")
        # Kullanıcının seçtiği şehrin tüm günkü verilerini çizen çizgi grafik
        default_city_index = sorted(df['province_name'].unique()).index(max_city)
        selected_city = st.selectbox("Trendini Görmek İstediğin Şehri Seç:", sorted(df['province_name'].unique()), index=default_city_index)
        
        city_data = df[df['province_name'] == selected_city][['timestamp', 'congestion_level']].sort_values('timestamp')
        # Sadece saat ve dakikayı al (örn: 21:25)
        city_data['Saat'] = city_data['timestamp'].apply(lambda x: x.split(" ")[1][:5]) 
        city_data.set_index('Saat', inplace=True)
        
        st.line_chart(city_data['congestion_level'], color="#00ff00") # Yeşil renkli trend çizgisi