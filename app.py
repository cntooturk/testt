import streamlit as st
import requests
import pandas as pd
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
import re

# --- AYARLAR ---
st.set_page_config(page_title="CNTOOTURK Takip", page_icon="🚌", layout="centered")

API_URL = "https://bursakartapi.abys-web.com/api/static/realtimedata"
HEADERS = {
    'Content-Type': 'application/json',
    'Origin': 'https://www.bursakart.com.tr',
    'Referer': 'https://www.bursakart.com.tr/',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
}

# --- HAT LİSTESİ (Hız için) ---
TUM_HATLAR = [
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
    "38D2", "38G", "40H", "43A", "43D", "43H", "43HB", "60B", "60K", "91", "91G", 
    "92", "92B", "93", "93E", "94", "95", "95A", "95B", "96", "97", "97A", "97B", 
    "97F", "97G", "98", "98E", "99", "101", "102", "103", "103A", "104", "105", 
    "111A", "111B", "112", "112A", "113", "113A", "114", "114A", "115", "116", 
    "116C", "117", "118A", "119", "119A", "120", "130", "131", "132", "132İ", 
    "133", "134", "134F", "135", "135H", "136", "137", "139", "140", "401", "501", 
    "601", "601U", "610", "610H", "611", "612", "612T", "613", "614", "615", "616", 
    "616H", "617", "617H", "618", "619", "620", "620K", "621", "622", "623", "630", 
    "631", "632", "642", "675", "741M", "755B", "772", "801", "811", "811D", "812S", 
    "812T", "813C", "813D", "813H", "814", "815", "816", "817", "817TK", "818", 
    "818H", "820", "901", "903", "911A", "912", "913", "914", "914A", "991", "992", 
    "B1", "B1B", "B2", "B2A", "B2C", "B2D", "B2K", "B3", "B3K", "B4", "B5", "B6", 
    "B7", "B8", "B9", "B10", "B10K", "B12", "B13", "B15", "B15C", "B16A", "B16B", 
    "B17", "B17A", "B17B", "B20A", "B20B", "B20C", "B20D", "B20G", "B22", "B22K", 
    "B24", "B25", "B27", "B29", "B30", "B31", "B31A", "B32", "B32A", "B33", "B33A", 
    "B33G", "B33H", "B33K", "B33M", "B34", "B34U", "B35", "B35K1", "B35K2", "B35M", 
    "B36", "B36A", "B36C", "B36M", "B36U", "B37", "B38", "B39", "B39K", "B40", 
    "B41B", "B41C", "B42A", "B43", "B44B", "B46", "D1", "D1A", "D1B", "D2", "D2A", 
    "D2B", "D3", "D4", "D4A", "D5", "D6", "D6A", "D7", "D7A", "D8", "D8A", "D9", 
    "D10", "D11", "D11A", "D11B", "D12", "D12A", "D12E", "D12H", "D12R", "D12Y", 
    "D13", "D13A", "D14", "D14A", "D15", "D16", "D16A", "D16B", "D17", "D17B", 
    "D18", "D19", "D20", "D21", "D22", "D23", "D24", "D24E", "D25", "D26", "E2", 
    "E12", "E13", "F1", "F3", "G1", "G2", "G3", "G4S", "G4T", "G5", "G6", "G7", 
    "G8", "H1", "H2", "H3", "H3B", "H3D", "H4", "S1", "S2"
]

@st.cache_resource
def get_geolocator():
    return Nominatim(user_agent="cntooturk_web_v36", timeout=5)

def plaka_duzenle(plaka_ham):
    p = plaka_ham.upper().replace(" ", "")
    match = re.match(r"(\d+)([A-Z]+)(\d+)", p)
    if match: return f"{match.group(1)} {match.group(2)} {match.group(3)}"
    return p

def veri_cek(keyword):
    try:
        r = requests.post(API_URL, headers=HEADERS, json={"keyword": keyword}, timeout=4)
        if r.status_code == 200:
            return r.json().get("result", [])
    except:
        return []
    return []

# --- ARAYÜZ ---
st.title("🚌 CNTOOTURK AKILLI PANEL")
st.markdown("**Plaka** (16M10171) veya **Hat Kodu** (B5) veya **3** (Boş Araçlar) giriniz.")

# Form Kullanarak "Enter" Tuşunu Aktif Ediyoruz
with st.form(key='arama_formu'):
    giris = st.text_input("Giriş Yapınız:", placeholder="Örn: 16M10171, B5, 3")
    btn_ara = st.form_submit_button("SORGULA 🔍")

# --- DURUM YÖNETİMİ ---
# Kullanıcı arama yaptığında sonuçları hafızada tutalım ki harita kapanmasın
if "sonuc_data" not in st.session_state:
    st.session_state["sonuc_data"] = None
if "arama_turu" not in st.session_state:
    st.session_state["arama_turu"] = None
if "hedef_plaka" not in st.session_state:
    st.session_state["hedef_plaka"] = None

# Arama Butonuna Basıldığında İşlemler
if btn_ara and giris:
    giris = giris.upper().strip()
    
    # 1. SENARYO: BOŞ ARAÇLAR (3)
    if giris == "3" or giris == "0":
        st.session_state["arama_turu"] = "BOS"
        with st.spinner("Boş araçlar taranıyor..."):
            bostakiler = []
            for k in ["HAT SEÇİLMEMİŞ", "SERVİS DIŞI"]:
                data = veri_cek(k)
                if data: bostakiler.extend(data)
            st.session_state["sonuc_data"] = bostakiler

    # 2. SENARYO: PLAKA SORGUSU (16M...)
    elif len(giris) > 4 and giris[0].isdigit():
        st.session_state["arama_turu"] = "PLAKA"
        hedef = plaka_duzenle(giris)
        st.session_state["hedef_plaka"] = hedef
        
        with st.spinner(f"🔍 '{hedef}' tüm hatlarda aranıyor..."):
            bulunan = None
            # Hızlı Tarama (Boşuna hepsine bakmasın diye önce olası listelere bakabiliriz ama burada full scan yapıyoruz)
            # Web tarafında uzun sürmemesi için önce servislere bakıyoruz
            for hat in ["HAT SEÇİLMEMİŞ", "SERVİS DIŞI"] + TUM_HATLAR:
                data = veri_cek(hat)
                for bus in data:
                    if bus.get("plaka", "").replace(" ", "") == hedef.replace(" ", ""):
                        bus['bulunan_hat'] = hat
                        bulunan = bus
                        break
                if bulunan: break
            
            st.session_state["sonuc_data"] = bulunan # Tek bir obje döner

    # 3. SENARYO: HAT SORGUSU (B5...)
    else:
        st.session_state["arama_turu"] = "HAT"
        with st.spinner(f"📡 '{giris}' hattı verileri çekiliyor..."):
            data = veri_cek(giris)
            st.session_state["sonuc_data"] = data

# --- SONUÇLARI GÖSTERME KISMI ---
if st.session_state["sonuc_data"] is not None:
    data = st.session_state["sonuc_data"]
    
    # --- PLAKA GÖSTERİMİ ---
    if st.session_state["arama_turu"] == "PLAKA":
        if data: # Araç bulunduysa
            bus = data
            st.success(f"✅ BULUNDU! Çalıştığı Hat: **{bus.get('hatkodu') or bus.get('bulunan_hat')}**")
            
            # Kart Bilgileri
            c1, c2, c3 = st.columns(3)
            c1.metric("Hız", f"{bus.get('hiz')} km/s")
            c2.metric("Anlık Yolcu", f"{bus.get('seferYolcu')}")
            c3.metric("Günlük Ciro", f"{bus.get('gunlukYolcu')}")
            
            st.info(f"👮 Sürücü: **{bus.get('surucu') or 'Belirtilmemiş'}**")
            st.write(f"📍 Konum: {bus.get('enlem')}, {bus.get('boylam')}")
            
            # HARİTA
            m = folium.Map(location=[float(bus['enlem']), float(bus['boylam'])], zoom_start=15)
            folium.Marker(
                [float(bus['enlem']), float(bus['boylam'])],
                tooltip=f"{bus['plaka']}",
                popup=f"Hız: {bus['hiz']}",
                icon=folium.Icon(color="red", icon="bus", prefix="fa")
            ).add_to(m)
            st_folium(m, width=700, height=350)
        else:
            st.error(f"❌ '{st.session_state['hedef_plaka']}' bulunamadı. Kontak kapalı olabilir.")

    # --- HAT GÖSTERİMİ ---
    elif st.session_state["arama_turu"] == "HAT":
        if data:
            # Toplam Yolcu
            toplam_yolcu = sum(b.get('gunlukYolcu', 0) for b in data)
            st.metric("BU HATTAKİ TOPLAM YOLCU", f"{toplam_yolcu} Kişi", delta=f"{len(data)} Aktif Araç")
            
            # Tablo Hazırla
            tablo = []
            for b in data:
                tablo.append({
                    "PLAKA": b.get("plaka"),
                    "SÜRÜCÜ": b.get("surucu"),
                    "HIZ (km/s)": b.get("hiz"),
                    "GÜNLÜK YOLCU": b.get("gunlukYolcu"),
                    "ANLIK YOLCU": b.get("seferYolcu")
                })
            
            st.table(pd.DataFrame(tablo))
            
            # --- DETAYLI SORGULAMA KUTUSU ---
            st.markdown("---")
            st.subheader("🚌 Detaylı Takip")
            
            plaka_listesi = [b.get("plaka") for b in data]
            secilen_plaka = st.selectbox("Haritada izlemek için araç seçin:", ["Seçiniz..."] + plaka_listesi)
            
            if secilen_plaka and secilen_plaka != "Seçiniz...":
                # Seçilen aracı listeden bul
                secilen_bus = next((item for item in data if item["plaka"] == secilen_plaka), None)
                if secilen_bus:
                    lat = float(secilen_bus['enlem'])
                    lon = float(secilen_bus['boylam'])
                    
                    st.write(f"📍 **{secilen_plaka} Konumu:**")
                    m = folium.Map(location=[lat, lon], zoom_start=15)
                    folium.Marker(
                        [lat, lon],
                        tooltip=secilen_plaka,
                        icon=folium.Icon(color="blue", icon="bus", prefix="fa")
                    ).add_to(m)
                    st_folium(m, width=700, height=300)
        else:
            st.warning("Bu hatta şu an aktif araç yok.")

    # --- BOŞ ARAÇ GÖSTERİMİ ---
    elif st.session_state["arama_turu"] == "BOS":
        st.metric("Toplam Boş/Servis Dışı Araç", f"{len(data)}")
        if data:
            tablo = [{"PLAKA": b.get("plaka"), "DURUM": "SERVİS DIŞI"} for b in data]
            st.dataframe(pd.DataFrame(tablo), use_container_width=True)
            
            # Detaylı Sorgu (Boş araçlar için de harita bakmak istersen)
            plaka_listesi = [b.get("plaka") for b in data]
            secilen_plaka = st.selectbox("Konumuna bakmak için seçin:", ["Seçiniz..."] + plaka_listesi)
            
            if secilen_plaka and secilen_plaka != "Seçiniz...":
                secilen_bus = next((item for item in data if item["plaka"] == secilen_plaka), None)
                if secilen_bus:
                    lat = float(secilen_bus['enlem'])
                    lon = float(secilen_bus['boylam'])
                    m = folium.Map(location=[lat, lon], zoom_start=15)
                    folium.Marker(
                        [lat, lon],
                        tooltip=secilen_plaka,
                        icon=folium.Icon(color="gray", icon="bed", prefix="fa")
                    ).add_to(m)
                    st_folium(m, width=700, height=300)
        else:
            st.info("Şu an boşta araç yok.")
