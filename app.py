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

# --- AYARLAR ---
st.set_page_config(page_title="Cntooturk Takip Sistemi", page_icon="🚌", layout="centered")

# --- CSS TASARIM ---
st.markdown("""
    <style>
        .block-container { padding-top: 0.5rem; padding-bottom: 1rem; }
        [data-testid="column"] { padding: 0px !important; margin: 0px !important; }
        
        .stButton button {
            height: 24px !important;
            min_height: 24px !important;
            width: 100% !important;
            padding: 0px !important;
            font-size: 11px !important;
            margin: 1px 0px !important;
            line-height: 22px !important;
            background-color: #2b2b2b; 
            color: #e0e0e0;
            border: 1px solid #444;
        }
        .stButton button:hover { border-color: #ff4b4b; color: #ff4b4b; }
        
        .stLinkButton a {
            height: 24px !important;
            min_height: 24px !important;
            width: 100% !important;
            font-size: 11px !important;
            padding: 0px !important;
            margin: 1px 0px !important;
            display: flex; justify-content: center; align-items: center;
            line-height: 22px !important;
            background-color: #2b2b2b;
            color: #e0e0e0 !important;
            border: 1px solid #444;
        }

        .metric-card {
            background-color: #1e1e1e;
            border: 1px solid #333;
            border-radius: 8px;
            padding: 10px 5px;
            text-align: center;
            margin: 0px 2px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        }
        .metric-title {
            color: #aaaaaa;
            font-size: 11px;
            text-transform: uppercase;
            font-weight: bold;
            margin-bottom: 2px;
        }
        .metric-value {
            color: #ffffff;
            font-size: 24px;
            font-weight: 800;
            margin: 0;
            line-height: 1.2;
        }

        .info-box {
            background-color: #262730;
            border-left: 5px solid #00bc8c;
            padding: 10px;
            margin-bottom: 10px;
            color: white;
            border-radius: 4px;
        }

        .address-card {
            background-color: #262730;
            border-left: 5px solid #ff4b4b;
            padding: 12px;
            margin: 15px 0px;
            border-radius: 4px;
            color: #e0e0e0;
            font-size: 14px;
            font-weight: 500;
            display: flex; align-items: center;
        }

        .table-header {
            font-size: 11px;
            font-weight: bold;
            color: #ff4b4b;
            margin-bottom: 4px;
            text-align: center;
            display: block;
        }

        hr { margin: 2px 0px !important; border-top: 1px solid #333; }
        p { margin: 0px !important; font-size: 13px; color: #ccc; }
    </style>
""", unsafe_allow_html=True)

API_URL = "https://bursakartapi.abys-web.com/api/static/realtimedata"
HEADERS = {
    'Content-Type': 'application/json',
    'Origin': 'https://www.bursakart.com.tr',
    'Referer': 'https://www.bursakart.com.tr/',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
}

# --- HAT LİSTESİ ---
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
    "38D2", "38G", "40H", "43A", "43D", "43H", "43HB", "60B", "60K",
    "B1", "B1B", "B2", "B2A", "B2C", "B2D", "B2K", "B3", "B3K", "B4", "B5", "B6", 
    "B7", "B8", "B9", "B10", "B10K", "B12", "B13", "B15", "B15C", "B16A", "B16B", 
    "B17", "B17A", "B17B", "B20A", "B20B", "B20C", "B20D", "B20G", "B22", "B22K", 
    "B24", "B25", "B27", "B29", "B30", "B31", "B31A", "B32", "B32A", "B33", "B33A", 
    "B33G", "B33H", "B33K", "B33M", "B34", "B34U", "B35", "B35K1", "B35K2", "B35M", 
    "B36", "B36A", "B36C", "B36M", "B36U", "B37", "B38", "B39", "B39K", "B40", 
    "B41B", "B41C", "B42A", "B43", "B44B", "B46", 
    "91", "91G", "92", "92B", "93", "93E", "94", "95", "95A", "95B", "96", "97", 
    "97A", "97B", "97F", "97G", "98", "98E", "99", "101", "102", "103", "103A", 
    "104", "105", "111A", "111B", "112", "112A", "113", "113A", "114", "114A", 
    "115", "116", "116C", "117", "118A", "119", "119A", "120", "130", "131", 
    "132", "132İ", "133", "134", "134F", "135", "135H", "136", "137", "139", 
    "140", "401", "501", "601", "601U", "610", "610H", "611", "612", "612T", 
    "613", "614", "615", "616", "616H", "617", "617H", "618", "619", "620", 
    "620K", "621", "622", "623", "630", "631", "632", "642", "675", "741M", 
    "755B", "772", "801", "811", "811D", "812S", "812T", "813C", "813D", "813H", 
    "814", "815", "816", "817", "817TK", "818", "818H", "820", "901", "903", 
    "911A", "912", "913", "914", "914A", "991", "992", "D1", "D1A", "D1B", 
    "D2", "D2A", "D2B", "D3", "D4", "D4A", "D5", "D6", "D6A", "D7", "D7A", 
    "D8", "D8A", "D9", "D10", "D11", "D11A", "D11B", "D12", "D12A", "D12E", 
    "D12H", "D12R", "D12Y", "D13", "D13A", "D14", "D14A", "D15", "D16", "D16A", 
    "D16B", "D17", "D17B", "D18", "D19", "D20", "D21", "D22", "D23", "D24", 
    "D24E", "D25", "D26", "E2", "E12", "E13", "F1", "F3", "G1", "G2", "G3", 
    "G4S", "G4T", "G5", "G6", "G7", "G8", "H1", "H2", "H3", "H3B", "H3D", "H4", 
    "S1", "S2"
]

def get_turkey_time():
    tz = pytz.timezone('Europe/Istanbul')
    return datetime.now(tz).strftime('%H:%M:%S')

def get_address(lat, lon):
    try:
        geolocator = Nominatim(user_agent="cntooturk_v81_percent21_5", timeout=10)
        loc = geolocator.reverse(f"{lat},{lon}")
        if loc:
            address = loc.raw.get('address', {})
            road = address.get('road', '') 
            
            mahalle = ""
            for key in ['neighbourhood', 'quarter', 'suburb', 'residential', 'village']:
                if address.get(key):
                    mahalle = address.get(key)
                    break
            
            if not mahalle:
                mahalle = address.get('town') or address.get('city_district') or address.get('district') or ""

            if road and mahalle: return f"{road}, {mahalle}"
            elif road: return road
            elif mahalle: return mahalle
            return loc.address.split(",")[0]
    except:
        return "Konum Bilgisi Alınamadı"
    return "Adres aranıyor..."

def plaka_duzenle(plaka_ham):
    try:
        p = plaka_ham.upper().replace(" ", "")
        match = re.match(r"(\d+)([A-Z]+)(\d+)", p)
        if match: return f"{match.group(1)} {match.group(2)} {match.group(3)}"
        return p
    except: return plaka_ham

def veri_cek(keyword, genis_sorgu=True):
    try:
        if genis_sorgu:
            payload = {"keyword": keyword, "take": 500, "limit": 500}
        else:
            payload = {"keyword": keyword}
            
        r = requests.post(API_URL, headers=HEADERS, json=payload, timeout=5, verify=False)
        if r.status_code == 200:
            return r.json().get("result", [])
    except: return []
    return []

def google_maps_link(lat, lon):
    return f"https://www.google.com/maps?q={lat},{lon}"

def yandex_maps_link(lat, lon):
    return f"https://yandex.com.tr/harita/?text={lat},{lon}"

# --- SESSION STATE ---
if 'secilen_plaka' not in st.session_state:
    st.session_state.secilen_plaka = None
if 'takip_modu' not in st.session_state:
    st.session_state.takip_modu = False
if 'aktif_arama' not in st.session_state:
    st.session_state.aktif_arama = None
if 'hat_ham_veri' not in st.session_state:
    st.session_state.hat_ham_veri = []

# --- CALLBACK ---
def arac_secildi_callback():
    secim = st.session_state.selectbox_secimi
    if secim and secim != "Seçiniz...":
        ham_veri = st.session_state.hat_ham_veri
        hedef_arac = next((x for x in ham_veri if x['plaka'] == secim), None)
        if hedef_arac:
            hedef_arac['hatkodu'] = st.session_state.aktif_arama
            st.session_state.secilen_plaka = hedef_arac
            st.session_state.takip_modu = True
            time.sleep(1)

# --- ARAYÜZ ---
st.title("🚌 Cntooturk Takip Sistemi")
st.caption(f"🕒 {get_turkey_time()} | ⚡ 20 Sn")

# GİRİŞ KUTUSU
if not st.session_state.takip_modu:
    col_input, col_btn = st.columns([3, 1])
    with col_input:
        giris_text = st.text_input("Giriş:", placeholder="Örn: 16M10171 veya B5", key="giris_input")
    with col_btn:
        st.write("") 
        st.write("") 
        btn_baslat = st.button("SORGULA", type="primary")

    if btn_baslat and giris_text:
        st.session_state.aktif_arama = giris_text.upper().strip()
        st.session_state.takip_modu = False 
        st.session_state.secilen_plaka = None
        st.session_state.hat_ham_veri = []

# --- LİSTELEME MODU ---
if st.session_state.aktif_arama and not st.session_state.takip_modu:
    giris = st.session_state.aktif_arama
    
    # 3 (BOŞ ARAÇLAR)
    if giris == "3" or giris == "0":
        st.subheader("💤 Boş / Servis Dışı")
        veriler = []
        with st.spinner("Taranıyor..."):
            for k in ["HAT SEÇİLMEMİŞ", "SERVİS DIŞI"]:
                res = veri_cek(k, genis_sorgu=True)
                if res: veriler.extend(res)
        
        temiz_veriler = []
        goru_plakalar = set()
        for v in veriler:
            if v['plaka'] not in goru_plakalar:
                temiz_veriler.append(v)
                goru_plakalar.add(v['plaka'])
        
        st.session_state.hat_ham_veri = temiz_veriler
        
        if temiz_veriler:
            st.markdown(f'<p style="margin-bottom: 5px; font-weight:bold;">Toplam {len(temiz_veriler)} araç listeleniyor:</p>', unsafe_allow_html=True)
            
            c1, c2, c3, c4, c5 = st.columns([2.2, 1.1, 1.1, 1.2, 1.8])
            c1.markdown("<span class='table-header'>PLAKA</span>", unsafe_allow_html=True)
            c2.markdown("<span class='table-header'>HIZ</span>", unsafe_allow_html=True)
            c3.markdown("<span class='table-header'>YOLCU</span>", unsafe_allow_html=True)
            c4.markdown("<span class='table-header'>KONUM</span>", unsafe_allow_html=True)
            c5.markdown("<span class='table-header'>İZLE</span>", unsafe_allow_html=True)
            st.divider()

            for i, bus in enumerate(temiz_veriler):
                c1, c2, c3, c4, c5 = st.columns([2.2, 1.1, 1.1, 1.2, 1.8])
                c1.write(f"**{bus['plaka']}**")
                c2.write(f"{bus['hiz']}")
                
                # Yolcu kalibrasyon %21.5
                h_yolcu = bus.get('gunlukYolcu', 0) or 0
                k_yolcu = int(h_yolcu * 1.22)
                c3.write(f"{k_yolcu}")
                
                maps = google_maps_link(bus['enlem'], bus['boylam'])
                c4.link_button("📍", maps)
                
                if c5.button("▶️", key=f"btn_{bus['plaka']}_{i}", type="primary"):
                    bus['hatkodu'] = "SERVİS DIŞI"
                    st.session_state.secilen_plaka = bus
                    st.session_state.takip_modu = True
                    st.rerun()
                st.divider()

    # PLAKA SORGUSU
    elif len(giris) > 4 and giris[0].isdigit():
        hedef = plaka_duzenle(giris)
        with st.status("🔍 Araç aranıyor...", expanded=True) as status:
            bulunan = None
            
            # 1. HASSAS ARAMA
            status.write(f"📡 '{hedef}' aranıyor...")
            res = veri_cek(hedef, genis_sorgu=False)
            if res:
                bulunan = res[0]
                bulunan['hatkodu'] = bulunan.get('hatkodu', 'ÖZEL')
            
            # 2. GENİŞ ARAMA
            if not bulunan:
                status.write("🌍 Araç hatlarda aranıyor...")
                with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
                    future_to_hat = {executor.submit(veri_cek, hat, True): hat for hat in TUM_HATLAR}
                    for future in concurrent.futures.as_completed(future_to_hat):
                        data = future.result()
                        for bus in data:
                            if bus.get("plaka", "").replace(" ","") == hedef.replace(" ",""):
                                bulunan = bus
                                bulunan['hatkodu'] = future_to_hat[future]
                                executor.shutdown(wait=False)
                                break
                        if bulunan: break
            
            if not bulunan:
                status.write("Hat Seçilmemiş Araçlar Aranıyor")
                for k in ["HAT SEÇİLMEMİŞ", "SERVİS DIŞI"]:
                    res = veri_cek(k, genis_sorgu=True)
                    for bus in res:
                        if bus.get("plaka", "").replace(" ","") == hedef.replace(" ",""):
                            bulunan = bus
                            bulunan['hatkodu'] = "SERVİS DIŞI"
                            break
                    if bulunan: break

            if bulunan:
                status.update(label="✅ Bulundu!, veriler getiriliyor.", state="complete", expanded=False)
                st.session_state.secilen_plaka = bulunan
                st.session_state.takip_modu = True
                time.sleep(1)
                st.rerun()
            else:
                status.update(label="❌ Bulunamadı.", state="error", expanded=True)
                st.error(f"{hedef} bulunamadı. Araç cihazı uykuda veya şartel kapatılmış.")

    # HAT SORGUSU
    else:
        st.subheader(f"📊 Hat: {giris}")
        with st.spinner("Veriler yükleniyor..."):
            data = veri_cek(giris, genis_sorgu=True)
            
            temiz_data = []
            goru_plaka = set()
            for d in data:
                if d['plaka'] not in goru_plaka:
                    temiz_data.append(d)
                    goru_plaka.add(d['plaka'])
            
            st.session_state.hat_ham_veri = temiz_data
        
        if temiz_data:
            ham_toplam = sum(b.get('gunlukYolcu', 0) for b in temiz_data)
            kalibre_toplam = int(ham_toplam * 1.215)
            
            c_toplam, c_arac = st.columns(2)
            c_toplam.markdown(f"""
                <div class="metric-card">
                    <div class="metric-title">TOPLAM YOLCU</div>
                    <div class="metric-value">{kalibre_toplam}</div>
                </div>
            """, unsafe_allow_html=True)
            c_arac.markdown(f"""
                <div class="metric-card">
                    <div class="metric-title">AKTİF ARAÇ</div>
                    <div class="metric-value">{len(temiz_data)}</div>
                </div>
            """, unsafe_allow_html=True)
            
            st.markdown("---")
            
            c1, c2, c3, c4, c5 = st.columns([2.2, 1.1, 1.1, 1.2, 1.8])
            c1.markdown("<span class='table-header'>PLAKA</span>", unsafe_allow_html=True)
            c2.markdown("<span class='table-header'>HIZ</span>", unsafe_allow_html=True)
            c3.markdown("<span class='table-header'>YOLCU</span>", unsafe_allow_html=True)
            c4.markdown("<span class='table-header'>KONUM</span>", unsafe_allow_html=True)
            c5.markdown("<span class='table-header'>İZLE</span>", unsafe_allow_html=True)
            st.divider()

            for i, bus in enumerate(temiz_data):
                c1, c2, c3, c4, c5 = st.columns([2.2, 1.1, 1.1, 1.2, 1.8])
                c1.write(f"**{bus['plaka']}**")
                c2.write(f"{bus['hiz']}")
                
                h_yolcu = bus.get('gunlukYolcu', 0) or 0
                k_yolcu = int(h_yolcu * 1.215)
                c3.write(f"{k_yolcu}")
                
                maps = google_maps_link(bus['enlem'], bus['boylam'])
                c4.link_button("📍", maps)
                
                if c5.button("▶️", key=f"btn_{bus['plaka']}_{i}", type="primary"):
                    bus['hatkodu'] = giris
                    st.session_state.secilen_plaka = bus
                    st.session_state.takip_modu = True
                    st.rerun()
                st.divider()

            plaka_listesi = [b['plaka'] for b in temiz_data]
            st.selectbox("Veya listeden seç:", ["Seçiniz..."] + plaka_listesi, key="selectbox_secimi", on_change=arac_secildi_callback)

        else:
            st.warning("Hat verisi alınamadı.")

# --- 2. MOD: CANLI TAKİP ---
if st.session_state.takip_modu and st.session_state.secilen_plaka:
    
    arama_terimi = st.session_state.aktif_arama
    is_plaka = len(arama_terimi) > 4 and arama_terimi[0].isdigit()
    
    if is_plaka:
        if st.button("🏠 Ana Menüye Dön"):
            st.session_state.takip_modu = False
            st.session_state.secilen_plaka = None
            st.session_state.aktif_arama = None
            st.session_state.hat_ham_veri = []
            st.rerun()
    else:
        if st.button("⬅️ Listeye Geri Dön"):
            st.session_state.takip_modu = False
            st.session_state.secilen_plaka = None
            st.rerun()

    eski_veri = st.session_state.secilen_plaka
    hedef_plaka = eski_veri['plaka']
    hedef_hat = eski_veri.get('hatkodu') or st.session_state.aktif_arama

    # VERİ GÜNCELLEME (ÖNCE PLAKA, SONRA HAT)
    taze_veri = None
    
    res_plaka = veri_cek(plaka_duzenle(hedef_plaka), genis_sorgu=False)
    if res_plaka:
        for r in res_plaka:
            if r['plaka'] == hedef_plaka:
                taze_veri = r
                break
    
    if not taze_veri and hedef_hat and hedef_hat != "ÖZEL":
        hat_verisi = veri_cek(hedef_hat, genis_sorgu=True)
        taze_veri = next((x for x in hat_verisi if x['plaka'] == hedef_plaka), None)

    if taze_veri:
        taze_veri['hatkodu'] = taze_veri.get('hatkodu') or hedef_hat
        arac = taze_veri
        st.session_state.secilen_plaka = taze_veri
    else:
        arac = eski_veri
        st.toast("⚠️ Veri güncellenemedi.")

    st.markdown("---")
    
    st.markdown(f"""
        <div class='info-box'>
            <h3 style='margin:0; text-align:center;'>🔴 {arac['plaka']}</h3>
            <p style='text-align:center; color:#ccc; margin-top:5px;'>CANLI TAKİP MODU</p>
        </div>
    """, unsafe_allow_html=True)

    surucu = arac.get('surucu') or "Belirtilmemiş"
    st.markdown(f"""
        <div style='background-color:#1e1e1e; padding:8px; border-radius:4px; text-align:center; border:1px solid #333; margin-bottom:15px;'>
            <span style='color:#888; font-size:12px;'>👮 SÜRÜCÜ</span><br>
            <span style='color:#fff; font-weight:bold; font-size:16px;'>{surucu}</span>
        </div>
    """, unsafe_allow_html=True)

    hat_no = arac.get('hatkodu') or "---"
    hiz = f"{arac.get('hiz')} km/s"
    
    ham_anlik = arac.get('seferYolcu')
    ham_toplam = arac.get('gunlukYolcu', 0) or 0
    kalibre_toplam = int(ham_toplam * 1.215) # %21.5 Kalibrasyon

    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(f"""<div class="metric-card"><div class="metric-title">HAT</div><div class="metric-value" style="color:#ff4b4b;">{hat_no}</div></div>""", unsafe_allow_html=True)
    c2.markdown(f"""<div class="metric-card"><div class="metric-title">HIZ</div><div class="metric-value">{hiz}</div></div>""", unsafe_allow_html=True)
    c3.markdown(f"""<div class="metric-card"><div class="metric-title">ANLIK</div><div class="metric-value" style="color:#00bc8c;">{ham_anlik}</div></div>""", unsafe_allow_html=True)
    c4.markdown(f"""<div class="metric-card"><div class="metric-title">TOPLAM</div><div class="metric-value">{kalibre_toplam}</div></div>""", unsafe_allow_html=True)

    lat = float(arac['enlem'])
    lon = float(arac['boylam'])
    adres = get_address(lat, lon)
    
    st.markdown(f"""
        <div class="address-card">
            <span style='font-size:20px; margin-right:10px;'>📍</span>
            <span>{adres}</span>
        </div>
    """, unsafe_allow_html=True)

    col_g, col_y = st.columns(2)
    col_g.link_button("🗺️ Google Haritalar", google_maps_link(lat, lon), use_container_width=True)
    col_y.link_button("🧭 Yandex Navigasyon", yandex_maps_link(lat, lon), use_container_width=True)

    m = folium.Map(location=[lat, lon], zoom_start=15)
    folium.Marker(
        [lat, lon],
        tooltip=f"{arac['plaka']}",
        popup=f"Hız: {arac['hiz']}",
        icon=folium.Icon(color="red", icon="bus", prefix="fa")
    ).add_to(m)
    st_folium(m, width=700, height=350)

# --- GLOBAL REFRESH ---
if st.session_state.aktif_arama:
    time.sleep(20)
    st.rerun()


