# 🚦 Urban Traffic Analytics System

![Python](https://img.shields.io/badge/Python-3.8%2B-blue?style=for-the-badge&logo=python)
![Streamlit](https://img.shields.io/badge/Streamlit-1.20%2B-FF4B4B?style=for-the-badge&logo=streamlit)
![SQLite](https://img.shields.io/badge/SQLite-Database-003B57?style=for-the-badge&logo=sqlite)
![TomTom](https://img.shields.io/badge/TomTom-Traffic_API-black?style=for-the-badge)

A highly scalable, real-time traffic congestion analytics dashboard monitoring 81 provinces in Turkey. This system leverages dynamic spatial grid sampling and a dual-API failover architecture to provide resilient and continuous data fetching.

The calculations are based on the province's capacity. 

<img width="1827" height="420" alt="image" src="https://github.com/user-attachments/assets/aea1f10d-0538-4068-8c59-32b6fedc8ac2" />
<img width="1811" height="948" alt="image" src="https://github.com/user-attachments/assets/48eef6ea-a3ae-4937-9cbf-b4174e3d88e9" />

##  Key Features

* **Dual-API Failover Mechanism:** Built-in load balancing utilizing multiple TomTom API keys to bypass daily quota limitations. The system automatically switches to a backup API key when a `429 Too Many Requests` error is encountered.
* **Dynamic Spatial Grid Sampling:** Uses 3x3 grids for metropolitan areas and 5-point cross-grids for smaller cities, optimizing API requests while ensuring zero error margin in congestion accuracy.
* **Automated Cron-Jobs (Scheduler):** An autonomous backend worker wakes up during specific peak traffic hours (e.g., 08:00, 17:00, 18:00) to fetch, process, and store data without manual intervention.
* **Tactical Command Dashboard:** A live-updating UI built with Streamlit and PyDeck, featuring dynamic node sizing, color-coded threshold alerts, and real-time line charts for trend analysis.

## 🛠️ Architecture & Tech Stack

* **Frontend:** Streamlit, PyDeck (Carto Dark Map), Pandas
* **Backend:** Python, Requests, Schedule (Cron Job Simulator)
* **Database:** SQLite (Historical Data Storage)
* **External APIs:** TomTom Flow Segment Data API

## ⚙️ Installation & Usage

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/Cemiltarp/urban-traffic-analytics.git](https://github.com/Cemiltarp/urban-traffic-analytics.git)
   cd urban-traffic-analytics

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```
3. **Configure Environment Variables**:
Create a .env file in the root directory and add your TomTom API keys:

```bash
TOMTOM_API_KEY_1=your_primary_api_key_here
TOMTOM_API_KEY_2=your_backup_api_key_here
```
4. **Run the Autonomous Fetcher (Backend)**:
```bash

python src/data_fetcher.py
```
5. **Launch the Dashboard (Frontend)**:
```bash
streamlit run app.py
```

**Developed by Said Cemil Tarpıcı**
