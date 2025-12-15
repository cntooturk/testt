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

# --- AYARLAR ---
st.set_page_config(page_title="CNTOOTURK Live", page_icon="🚌", layout="centered")

API_URL = "https://bursakartapi.abys-web.com/api/static/realtimedata"
HEADERS = {
    'Content-Type': 'application/json',
    'Origin': 'https://www.bursakart.com.tr',
    'Referer': 'https://www.bursakart.com.tr/',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
}

# --- HAT LİSTESİ (Özet) ---
TUM_HATLAR = [
    "1A", "1C", "B5", "93", "97", "14L2", "6F", "B24", "38", "97G",
    "HAT SEÇİLMEMİŞ", "SERVİS DIŞI"
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
    try:
        r = requests.post(API_URL, headers=HEADERS, json={"keyword": keyword}, timeout=5)
        if r.status_code == 200:
            return r.json().get("result", [])
    except:
        return []
    return []

def google_maps_link(lat, lon):
    return f"https://www.google.com/maps/search/?api=1&query={lat},{lon}"

# --- ARAYÜZ ---
st.title("🚌 CNTOOTURK LIVE v40")
st.caption(f"Sistem Saati: {get_turkey_time()}")
st.markdown("---")

# --- SESSION STATE (Hafıza) ---
# Burası sayfa yenilense bile verilerin kaybolmamasını sağlar
if 'secilen_plaka' not in st.session_state:
    st.session_state.secilen_plaka = None
if 'takip_modu' not in st.session_state:
    st.session_state.takip_modu = False
if 'aktif_arama' not in st.session_state:
    st.session_state.aktif_arama = None  # Sorgu metnini burada tutacağız

# GİRİŞ ALANI
col_input, col_btn = st.columns([3, 1])
with col_input:
    # Value kısmını session'dan alıyoruz ki yenilenince silinmesin
    giris_text = st.text_input("Giriş (Plaka, Hat veya 3):", placeholder="Örn: 16M10171", key="giris_input")
with col_btn:
    st.write("") 
    st.write("") 
    btn_baslat = st.button("SORGULA", type="primary")

# Butona basılınca hafızaya kaydet
if btn_baslat and giris_text:
    st.session_state.aktif_arama = giris_text.upper().strip()
    st.session_state.takip_modu = False # Yeni aramada takibi sıfırla
    st.session_state.secilen_plaka = None # Seçimi sıfırla

# --- ARAMA MANTIĞI (Hafızadaki veriye göre çalışır) ---
if st.session_state.aktif_arama:
    giris = st.session_state.aktif_arama
    
    # 1. SENARYO: BOŞ ARAÇLAR (3)
    if giris == "3" or giris == "0":
        st.subheader("💤 Boş / Servis Dışı Araçlar")
        veriler = []
        # Spinner sadece ilk yüklemede görünsün diye kontrol
        if not st.session_state.secilen_plaka:
            with st.spinner("Taranıyor..."):
                for k in ["HAT SEÇİLMEMİŞ", "SERVİS DIŞI"]:
                    res = veri_cek(k)
                    if res: veriler.extend(res)
        else:
             # Takip modundaysak spinner göstermeden arka planda çek
             for k in ["HAT SEÇİLMEMİŞ", "SERVİS DIŞI"]:
                    res = veri_cek(k)
                    if res: veriler.extend(res)
        
        if veriler:
            if not st.session_state.secilen_plaka:
                st.info(f"Toplam {len(veriler)} araç boşta.")
            
            plaka_listesi = [v["plaka"] for v in veriler]
            
            # Seçim kutusu
            # Eğer bir seçim yapıldıysa kutuda o seçili kalsın
            index_val = 0
            if st.session_state.secilen_plaka and st.session_state.secilen_plaka['plaka'] in plaka_listesi:
                index_val = plaka_listesi.index(st.session_state.secilen_plaka['plaka']) + 1

            secim = st.selectbox("İzlemek için seç:", ["Seçiniz..."] + plaka_listesi, index=index_val)
            
            if secim and secim != "Seçiniz...":
                # Eğer yeni bir seçim yapıldıysa veya takip devam ediyorsa
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
            res = veri_cek(hedef)
            if res:
                bulunan = res[0]
                bulunan['hatkodu'] = bulunan.get('hatkodu', 'ÖZEL')
            
            if not bulunan:
                with st.status("Sistem taranıyor...", expanded=True) as status:
                    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
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
                st.error(f"❌ {hedef} bulunamadı.")

    # 3. SENARYO: HAT SORGUSU
    else:
        # Eğer takip modu aktif DEĞİLSE listeyi göster
        if not st.session_state.takip_modu:
            st.subheader(f"📊 Hat: {giris}")
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
                
                # Seçim Kutusu
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
        
        # Eğer takip modu AKTİFSE ve Hat modundaysak, geri dönme butonu koy
        else:
            if st.button("⬅️ Listeye Dön"):
                st.session_state.takip_modu = False
                st.session_state.secilen_plaka = None
                st.rerun()

# --- 4. CANLI TAKİP VE OTO-YENİLEME BÖLÜMÜ ---
if st.session_state.takip_modu and st.session_state.secilen_plaka:
    
    # VERİYİ TAZELE
    eski_veri = st.session_state.secilen_plaka
    hedef_plaka = eski_veri['plaka']
    hedef_hat = eski_veri.get('hatkodu') or eski_veri.get('bulunan_hat') or "HAT SEÇİLMEMİŞ"
    
    taze_veri = None
    
    # 1. Önce bildiğimiz hatta bakalım
    if hedef_hat:
        res = veri_cek(hedef_hat)
        taze_veri = next((x for x in res if x['plaka'] == hedef_plaka), None)
    
    # 2. Bulamazsak direkt plakaya soralım
    if not taze_veri:
        res = veri_cek(plaka_duzenle(hedef_plaka))
        if res: taze_veri = res[0]

    if taze_veri:
        taze_veri['hatkodu'] = taze_veri.get('hatkodu') or hedef_hat
        arac = taze_veri
        st.session_state.secilen_plaka = taze_veri
    else:
        arac = eski_veri
        st.warning("⚠️ Araçtan sinyal alınamıyor (Son Konum).")

    # --- GÖRSELLEŞTİRME ---
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
