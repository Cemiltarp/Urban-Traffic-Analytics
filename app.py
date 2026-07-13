import streamlit as st
import pandas as pd
import pydeck as pdk
import sqlite3
import os
from src.cities import CITIES
from streamlit_autorefresh import st_autorefresh

# Configure page layout
st.set_page_config(page_title="Türkiye Urban Traffic Analytics", page_icon="🚦", layout="wide")

# Auto-refresh page every 60 seconds (60000 ms)
st_autorefresh(interval=60000, limit=None, key="traffic_refresh")

st.title("🚦 Türkiye Urban Traffic Analysis Dashboard")
st.markdown("Historical traffic analysis calculated for each of Türkiye's 81 provinces based on their respective capacities.")

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
    
    # Dynamic Color and Radius Algorithm based on congestion thresholds
    def get_congestion_color(congestion):
        if congestion < 20:
            return [0, 255, 0, 160]      # Free Flow: Transparent Green
        elif congestion < 40:
            return [255, 215, 0, 200]    # Moderate: Bright Yellow
        elif congestion < 60:
            return [255, 140, 0, 220]    # Heavy: Orange
        else:
            return [255, 0, 0, 255]      # Severe: Solid Red
            
    df['color'] = df['congestion_level'].apply(get_congestion_color)
    # Increase scatterplot radius as congestion increases
    df['radius'] = df['congestion_level'].apply(lambda x: 10000 + (x * 450)) 
    
    return df

df = load_data()

if df is None or df.empty:
    st.error("[SYSTEM ERROR] Database not found. Please run the data fetcher in the background.")
else:
    st.sidebar.header("⏱️ Time Filter & Controls")
    timestamps = sorted(df['timestamp'].unique(), reverse=True)
    selected_time = st.sidebar.selectbox("Select Timestamp:", timestamps)
    
    filtered_df = df[df['timestamp'] == selected_time]
    
    # --- TOP METRICS PANEL ---
    avg_congestion = int(filtered_df['congestion_level'].mean())
    max_city = filtered_df.loc[filtered_df['congestion_level'].idxmax()]['province_name']
    max_value = filtered_df['congestion_level'].max()
    
    # Critical threshold counter (>50% congestion)
    critical_cities = len(filtered_df[filtered_df['congestion_level'] >= 50])
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric(label="Selected Time", value=selected_time.split(" ")[1])
    col2.metric(label="National Average", value=f"{avg_congestion}%")
    col3.metric(label="Most Congested", value=f"{max_city} ({max_value}%)")
    col4.metric(
        label="Critical Regions (>50%)", 
        value=f"{critical_cities} Cities", 
        delta="-High Volume" if critical_cities > 0 else "Normal", 
        delta_color="inverse"
    )
    
    st.markdown("---")
    
    # --- SPLIT LAYOUT (Left: Map, Right: Charts) ---
    map_col, chart_col = st.columns([2, 1]) 
    
    with map_col:
        st.subheader("🗺️ Live Traffic Map")
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
            tooltip={"text": "{province_name}\nCongestion Level: {congestion_level}%"}
        ))
        
    with chart_col:
        st.subheader("📊 Top 5 Congested Cities")
        # Bar chart for the top 5 most congested cities
        top_5 = filtered_df.nlargest(5, 'congestion_level')[['province_name', 'congestion_level']]
        top_5.set_index('province_name', inplace=True)
        st.bar_chart(top_5, color="#ff4b4b") 
        
        st.markdown("<br>", unsafe_allow_html=True) 
        
        st.subheader("📈 Daily Traffic Trend")
        # Line chart showing the selected city's congestion trend throughout the day
        default_city_index = sorted(df['province_name'].unique()).index(max_city)
        selected_city = st.selectbox("Select City for Trend Analysis:", sorted(df['province_name'].unique()), index=default_city_index)
        
        city_data = df[df['province_name'] == selected_city][['timestamp', 'congestion_level']].sort_values('timestamp')
        # Extract HH:MM format for the x-axis
        city_data['Time'] = city_data['timestamp'].apply(lambda x: x.split(" ")[1][:5]) 
        city_data.set_index('Time', inplace=True)
        
        st.line_chart(city_data['congestion_level'], color="#00ff00")