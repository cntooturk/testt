import streamlit as st
import requests
import pandas as pd
import folium
from streamlit_folium import st_folium
import time
import re
import concurrent.futures
from geopy.geocoders import Nominatim
from datetime import datetime
import pytz 
import urllib3

# SSL Uyarılarını Gizle (Bulut sunucuda hata vermemesi için)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- AYARLAR ---
st.set_page_config(page_title="CNTOOTURK Live", page_icon="🚌", layout="centered")

API_URL = "https://bursakartapi.abys-web.com/api/static/realtimedata"
HEADERS = {
    'Content-Type': 'application/json',
    'Origin': 'https://www.bursakart.com.tr',
    'Referer': 'https://www.bursakart.com.tr/',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
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

def get_turkey_time():
    tz = pytz.timezone('Europe/Istanbul')
    return datetime.now(tz).strftime('%H:%M:%S')

def plaka_duzenle(plaka_ham):
    try:
        p = plaka_ham.upper().replace(" ", "")
        match = re.match(r"(\d+)([A-Z]+)(\d+)", p)
        if match: return f"{match.group(1)} {match.group(2)} {match.group(3)}"
        return p
    except:
        return plaka_ham

def veri_cek(keyword):
    """
    Bulut ortamında çalışması için optimize edilmiştir.
    Verify=False -> SSL hatalarını yok sayar.
    Timeout=10 -> Yavaş internete tolerans tanır.
    """
    try:
        r = requests.post(API_URL, headers=HEADERS, json={"keyword": keyword}, timeout=10, verify=False)
        if r.status_code == 200:
            return r.json().get("result", [])
    except Exception as e:
        return []
    return []

def google_maps_link(lat, lon):
    return f"https://www.google.com/maps/search/?api=1&query={lat},{lon}"

# --- ARAYÜZ ---
st.title("🚌 CNTOOTURK LIVE v41")
st.caption(f"Sistem Saati: {get_turkey_time()}")
st.markdown("---")

# --- SESSION STATE (Hafıza) ---
if 'secilen_plaka' not in st.session_state:
    st.session_state.secilen_plaka = None
if 'takip_modu' not in st.session_state:
    st.session_state.takip_modu = False
if 'aktif_arama' not in st.session_state:
    st.session_state.aktif_arama = None

# GİRİŞ ALANI
col_input, col_btn = st.columns([3, 1])
with col_input:
    giris_text = st.text_input("Giriş (Plaka, Hat veya 3):", placeholder="Örn: 16M10171", key="giris_input")
with col_btn:
    st.write("") 
    st.write("") 
    btn_baslat = st.button("SORGULA", type="primary")

if btn_baslat and giris_text:
    st.session_state.aktif_arama = giris_text.upper().strip()
    st.session_state.takip_modu = False 
    st.session_state.secilen_plaka = None

# --- ARAMA MANTIĞI ---
if st.session_state.aktif_arama:
    giris = st.session_state.aktif_arama
    
    # 1. SENARYO: BOŞ ARAÇLAR (3)
    if giris == "3" or giris == "0":
        st.subheader("💤 Boş / Servis Dışı Araçlar")
        veriler = []
        if not st.session_state.secilen_plaka:
            with st.spinner("Taranıyor (Bulut Modu)..."):
                for k in ["HAT SEÇİLMEMİŞ", "SERVİS DIŞI"]:
                    res = veri_cek(k)
                    if res: veriler.extend(res)
        else:
             for k in ["HAT SEÇİLMEMİŞ", "SERVİS DIŞI"]:
                    res = veri_cek(k)
                    if res: veriler.extend(res)
        
        if veriler:
            if not st.session_state.secilen_plaka:
                st.info(f"Toplam {len(veriler)} araç boşta.")
            
            plaka_listesi = [v["plaka"] for v in veriler]
            index_val = 0
            if st.session_state.secilen_plaka and st.session_state.secilen_plaka['plaka'] in plaka_listesi:
                index_val = plaka_listesi.index(st.session_state.secilen_plaka['plaka'])

            secim = st.selectbox("İzlemek için seç:", ["Seçiniz..."] + plaka_listesi, index=index_val if st.session_state.secilen_plaka else 0)
            
            if secim and secim != "Seçiniz...":
                if not st.session_state.secilen_plaka or st.session_state.secilen_plaka['plaka'] != secim:
                    secilen_arac = next((x for x in veriler if x["plaka"] == secim), None)
                    st.session_state.secilen_plaka = secilen_arac
                    st.session_state.takip_modu = True
                    st.rerun()

    # 2. SENARYO: PLAKA SORGUSU (16M...)
    elif len(giris) > 4 and giris[0].isdigit():
        hedef = plaka_duzenle(giris)
        
        if not st.session_state.takip_modu:
            bulunan = None
            # Adım 1: Direkt Sorgu
            res = veri_cek(hedef)
            if res:
                bulunan = res[0]
                bulunan['hatkodu'] = bulunan.get('hatkodu', 'ÖZEL')
            
            # Adım 2: Threading ile Tarama (MOTOR SAYISI 4'E DÜŞÜRÜLDÜ)
            if not bulunan:
                with st.status("Detaylı sistem taraması yapılıyor (Bu işlem 20-30 sn sürebilir)...", expanded=True) as status:
                    # Cloud sunucusunu yormamak için workers sayısını azalttık
                    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
                        future_to_hat = {executor.submit(veri_cek, hat): hat for hat in TUM_HATLAR}
                        for future in concurrent.futures.as_completed(future_to_hat):
                            data = future.result()
                            for bus in data:
                                if bus.get("plaka", "").replace(" ","") == hedef.replace(" ",""):
                                    bulunan = bus
                                    bulunan['hatkodu'] = future_to_hat[future]
                                    executor.shutdown(wait=False)
                                    break
                            if bulunan: break
                    status.update(label="Tarama bitti.", state="complete", expanded=False)

            if bulunan:
                st.session_state.secilen_plaka = bulunan
                st.session_state.takip_modu = True
                st.rerun()
            else:
                st.error(f"❌ {hedef} bulunamadı. Araç kontak kapatmış veya servis dışı olabilir.")

    # 3. SENARYO: HAT SORGUSU
    else:
        if not st.session_state.takip_modu:
            st.subheader(f"📊 Hat: {giris}")
            with st.spinner("Veriler çekiliyor..."):
                data = veri_cek(giris)
            
            if data:
                toplam = sum(b.get('gunlukYolcu', 0) for b in data)
                st.metric("Toplam Taşınan Yolcu", f"{toplam}", delta=f"{len(data)} Aktif Araç")
                
                tablo_data = []
                for b in data:
                    maps_url = google_maps_link(b['enlem'], b['boylam'])
                    tablo_data.append({
                        "PLAKA": b['plaka'],
                        "HIZ": f"{b['hiz']} km/s",
                        "YOLCU": b['gunlukYolcu'],
                        "KONUM": maps_url
                    })
                
                st.dataframe(pd.DataFrame(tablo_data), 
                             column_config={"KONUM": st.column_config.LinkColumn("Konum", display_text="📍 Harita")},
                             hide_index=True, use_container_width=True)
                
                plaka_listesi = [b['plaka'] for b in data]
                plaka_secim = st.selectbox("Canlı izlemek için araç seç:", ["Seçiniz..."] + plaka_listesi)
                
                if plaka_secim and plaka_secim != "Seçiniz...":
                    hedef_arac = next((x for x in data if x['plaka'] == plaka_secim), None)
                    if hedef_arac:
                        hedef_arac['hatkodu'] = giris 
                        st.session_state.secilen_plaka = hedef_arac
                        st.session_state.takip_modu = True
                        st.rerun()
            else:
                st.warning("Bu hatta aktif araç yok.")
        else:
            if st.button("⬅️ Listeye Dön"):
                st.session_state.takip_modu = False
                st.session_state.secilen_plaka = None
                st.rerun()

# --- 4. CANLI TAKİP ---
if st.session_state.takip_modu and st.session_state.secilen_plaka:
    
    # VERİ TAZELEME
    eski_veri = st.session_state.secilen_plaka
    hedef_plaka = eski_veri['plaka']
    hedef_hat = eski_veri.get('hatkodu') or eski_veri.get('bulunan_hat') or "HAT SEÇİLMEMİŞ"
    
    taze_veri = None
    
    # 1. Önce Hatta Bak
    if hedef_hat:
        res = veri_cek(hedef_hat)
        taze_veri = next((x for x in res if x['plaka'] == hedef_plaka), None)
    
    # 2. Bulamazsa Plakaya Bak
    if not taze_veri:
        res = veri_cek(plaka_duzenle(hedef_plaka))
        if res: taze_veri = res[0]

    if taze_veri:
        taze_veri['hatkodu'] = taze_veri.get('hatkodu') or hedef_hat
        arac = taze_veri
        st.session_state.secilen_plaka = taze_veri
    else:
        arac = eski_veri
        st.toast("⚠️ Veri güncellenemedi, eski konum gösteriliyor.")

    # --- EKRAN ---
    st.markdown("---")
    st.subheader(f"🔴 CANLI İZLEME: {arac['plaka']}")
    
    c1, c2, c3, c4 = st.columns(4)
    surucu_adi = arac.get('surucu')
    if not surucu_adi or surucu_adi.strip() == "": surucu_adi = "Belirtilmemiş"

    c1.info(f"👮 **SÜRÜCÜ**\n\n{surucu_adi}")
    c2.metric("🚀 ANLIK HIZ", f"{arac.get('hiz')} km/s")
    c3.metric("🎫 ANLIK YOLCU", f"{arac.get('seferYolcu')}")
    c4.metric("💰 TOPLAM YOLCU", f"{arac.get('gunlukYolcu')}")
    
    st.write(f"🚌 **Hat:** {arac.get('hatkodu')} | 🕒 **Son Güncelleme:** {get_turkey_time()}")

    g_maps = google_maps_link(arac['enlem'], arac['boylam'])
    st.link_button("📍 Google Haritalar'da Git", g_maps, use_container_width=True)
    
    lat = float(arac['enlem'])
    lon = float(arac['boylam'])
    
    m = folium.Map(location=[lat, lon], zoom_start=15)
    folium.Marker(
        [lat, lon],
        tooltip=f"{arac['plaka']}",
        popup=f"Hız: {arac['hiz']} km/s",
        icon=folium.Icon(color="red", icon="bus", prefix="fa")
    ).add_to(m)
    
    st_folium(m, width=700, height=350)
    
    # OTOMATİK YENİLEME (20 sn)
    time.sleep(20)
    st.rerun()
