import streamlit as st
import requests
import pandas as pd
import folium
from streamlit_folium import st_folium
import time
import re
import concurrent.futures
from datetime import datetime
import pytz 
import urllib3
from geopy.geocoders import Nominatim

# SSL Hata Gizleme
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- AYARLAR VE ULTRA KOMPAKT CSS ---
st.set_page_config(page_title="CNTOOTURK Live", page_icon="🚌", layout="centered")

st.markdown("""
    <style>
        .block-container { padding-top: 0.5rem; padding-bottom: 1rem; }
        [data-testid="column"] { padding: 0px !important; margin: 0px !important; }
        .stButton button {
            height: 28px !important;
            padding-top: 0px !important;
            padding-bottom: 0px !important;
            font-size: 12px !important;
            margin-top: 2px !important;
            width: 100%;
        }
        hr { margin: 0px 0px !important; border-top: 1px solid #eee; }
        p, .stMarkdown {
            font-size: 13px !important;
            margin-bottom: 0px !important;
            margin-top: 0px !important;
            padding-top: 2px !important; 
        }
        .stLinkButton { height: 28px !important; margin-top: 2px !important; }
        .stLinkButton a { padding-top: 2px !important; padding-bottom: 2px !important; }
    </style>
""", unsafe_allow_html=True)

API_URL = "https://bursakartapi.abys-web.com/api/static/realtimedata"
HEADERS = {
    'Content-Type': 'application/json',
    'Origin': 'https://www.bursakart.com.tr',
    'Referer': 'https://www.bursakart.com.tr/',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
}

# --- AKILLI SIRALANMIŞ HAT LİSTESİ ---
TUM_HATLAR = [
    # 1. GRUP: 1-60 ARASI
    "1A", "1C", "1D", "1GY", "1H", "1K", "1M", "1MB", "1SY", "1T", "1TG", "1TK", 
    "2B", "2BT", "2C", "2E", "2G1", "2G2", "2GH", "2GK", "2GM", "2GY", "2K", "2KÇ", 
    "2M", "2MU", "2U", "3C", "3G", "3İ", "3MU", "3P", "4A", "4B", "4G", "4İ", 
    "5A", "5B", "5E", "5G", "6A", "6E", "6F", "6F1", "6F2", "6FD", "6K1", "7A", 
    "7B", "7C", "7S", "8L", "9D", "9M", "9PA", "14F", "14L", "14L2", "14L3", "14N", 
    "14U", "15", "15A", "15B", "15D", "15H", "16A", "16İ", "16S", "17A", "17B", 
    "17C", "17D", "17E", "17F", "17H", "17M", "17S", "17Y", "18", "18B", "18İ", 
    "18Y", "19A", "19B", "19C", "19D", "19E", "19İ", "20", "20A", "21", "21C", 
    "21CK", "22C", "23", "23A", "24B", "24D", "25", "25A", "25B", "25D", "27A", 
    "28", "28A", "29A", "30", "31A", "35B", "35C", "35E1", "35E2", "35G", "35H", 
    "35R", "35S", "35SE", "35U", "36", "36A", "37", "38", "38B", "38B2", "38D", 
    "38D2", "38G", "40H", "43A", "43D", "43H", "43HB", "60B", "60K",

    # 2. GRUP: B SERİSİ
    "B1", "B1B", "B2", "B2A", "B2C", "B2D", "B2K", "B3", "B3K", "B4", "B5", "B6", 
    "B7", "B8", "B9", "B10", "B10K", "B12", "B13", "B15", "B15C", "B16A", "B16B", 
    "B17", "B17A", "B17B", "B20A", "B20B", "B20C", "B20D", "B20G", "B22", "B22K", 
    "B24", "B25", "B27", "B29", "B30", "B31", "B31A", "B32", "B32A", "B33", "B33A", 
    "B33G", "B33H", "B33K", "B33M", "B34", "B34U", "B35", "B35K1", "B35K2", "B35M", 
    "B36", "B36A", "B36C", "B36M", "B36U", "B37", "B38", "B39", "B39K", "B40", 
    "B41B", "B41C", "B42A", "B43", "B44B", "B46", 

    # 3. GRUP: DİĞERLERİ
    "91", "91G", "92", "92B", "93", "93E", "94", "95", "95A", "95B", "96", "97", 
    "97A", "97B", "97F", "97G", "98", "98E", "99", "101", "102", "103", "103A", 
    "104", "105", "111A", "111B", "112", "112A", "113", "113A", "114", "114A", 
    "115", "116", "116C", "117", "118A", "119", "119A", "120", "130", "131", 
    "132", "132İ", "133", "134", "134F", "135", "135H", "136", "137", "139", 
    "140", "401", "501", "601", "601U", "610", "610H", "611", "612", "612T", 
    "613", "614", "61
