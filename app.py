import streamlit as st
import pandas as pd
import pydeck as pdk
import os

st.set_page_config(page_title="Urban Traffic Analytics", page_icon="🚦", layout="wide")

st.title("🚦 Turkey Urban Traffic & Mobility Analytics")
st.markdown("Real-time simulation and analysis of vehicle density across provinces.")

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
    st.sidebar.header("Control Panel")
    selected_hour = st.sidebar.slider("Select Hour of the Day", min_value=0, max_value=23, value=8, step=1)
    
    filtered_df = df[df['hour'] == selected_hour]
    
    st.markdown(f"### Live Traffic Map - Time: {selected_hour:02d}:00")
    
    layer = pdk.Layer(
        "ColumnLayer",
        data=filtered_df,
        get_position=["lon", "lat"],
        get_elevation="active_vehicles",
        elevation_scale=0.04,
        radius=12000,
        get_fill_color=[255, 69, 0, 220],
        pickable=True,
        auto_highlight=True,
    )

    view_state = pdk.ViewState(
        latitude=39.0, 
        longitude=35.0, 
        zoom=5, 
        pitch=45,
        bearing=0
    )

    st.pydeck_chart(pdk.Deck(
        map_provider="carto",
        map_style="dark",
        layers=[layer],
        initial_view_state=view_state,
        tooltip={"text": "{province_name}\nActive Vehicles in Traffic: {active_vehicles}"}
    ))
    
    st.markdown("#### Traffic Overview")
    st.dataframe(
        filtered_df[['province_name', 'active_vehicles']].sort_values(by='active_vehicles', ascending=False), 
        use_container_width=True
    )