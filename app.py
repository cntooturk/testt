import streamlit as st
import requests
import pandas as pd
import folium
from streamlit_folium import st_folium
import time
import re
import concurrent.futures

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
# Buraya senin uzun listenin tamamı gelecek. Kodun kısalığı için özet geçiyorum.
# GitHub'a atarken önceki koddaki uzun listeyi buraya yapıştırabilirsin.
TUM_HATLAR = [
    "1A", "1C", "B5", "93", "97", "14L2", "6F", "B24", "38", "97G",
    "HAT SEÇİLMEMİŞ", "SERVİS DIŞI" # Bunları da ekledik
]

def plaka_duzenle(plaka_ham):
    """ 16m10171 -> 16 M 10171 """
    p = plaka_ham.upper().replace(" ", "")
    match = re.match(r"(\d+)([A-Z]+)(\d+)", p)
    if match: return f"{match.group(1)} {match.group(2)} {match.group(3)}"
    return p

def veri_cek(keyword):
    """API'den veri çeker"""
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
st.title("🚌 CNTOOTURK LIVE")
st.markdown("---")

# Session State (Verileri hafızada tutmak için)
if 'secilen_plaka' not in st.session_state:
    st.session_state.secilen_plaka = None

# GİRİŞ ALANI
col_input, col_btn = st.columns([3, 1])
with col_input:
    giris = st.text_input("Plaka, Hat veya 3:", placeholder="Örn: 16M10171 veya B5")
with col_btn:
    st.write("") # Boşluk
    st.write("") 
    btn_baslat = st.button("SORGULA", type="primary")

# --- ANA MANTIK ---
if giris:
    giris = giris.upper().strip()
    
    # 1. SENARYO: BOŞ ARAÇLAR (3)
    if giris == "3" or giris == "0":
        st.subheader("💤 Boş / Servis Dışı Araçlar")
        veriler = []
        for k in ["HAT SEÇİLMEMİŞ", "SERVİS DIŞI"]:
            res = veri_cek(k)
            if res: veriler.extend(res)
        
        if veriler:
            st.info(f"Toplam {len(veriler)} araç boşta.")
            # Seçim Kutusu
            plaka_listesi = [v["plaka"] for v in veriler]
            secim = st.selectbox("Haritada izlemek için araç seç:", ["Seçiniz..."] + plaka_listesi)
            if secim and secim != "Seçiniz...":
                # Seçilen aracı bul ve panele gönder
                secilen_arac = next((x for x in veriler if x["plaka"] == secim), None)
                st.session_state.secilen_plaka = secilen_arac

    # 2. SENARYO: PLAKA SORGUSU (16M...)
    elif len(giris) > 4 and giris[0].isdigit():
        hedef = plaka_duzenle(giris)
        
        # Önce Hızlı "Nokta Atışı" Sorgu (Dönüp durmayı engeller)
        bulunan = None
        # Direkt API'ye plakayı soruyoruz (En hızlı yöntem)
        res = veri_cek(hedef)
        if res:
            bulunan = res[0]
            bulunan['hatkodu'] = bulunan.get('hatkodu', 'ÖZEL')
        
        # Eğer direkt bulamazsa hatları tara (Yedek plan)
        if not bulunan:
            with st.status("Detaylı tarama yapılıyor...", expanded=True) as status:
                # Threading ile çok hızlı tarama
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
                status.update(label="Tarama tamamlandı!", state="complete", expanded=False)

        if bulunan:
            st.session_state.secilen_plaka = bulunan
        else:
            st.error(f"❌ {hedef} bulunamadı. Kontak kapalı olabilir.")

    # 3. SENARYO: HAT SORGUSU (B5...)
    else:
        st.subheader(f"📊 Hat: {giris}")
        data = veri_cek(giris)
        
        if data:
            # Toplam Yolcu
            toplam = sum(b.get('gunlukYolcu', 0) for b in data)
            st.metric("Toplam Taşınan Yolcu", f"{toplam}", delta=f"{len(data)} Aktif Araç")
            
            # --- TABLO HAZIRLIĞI (Şoförsüz, Linkli) ---
            tablo_data = []
            for b in data:
                # Google Maps Linki Oluştur
                maps_url = google_maps_link(b['enlem'], b['boylam'])
                tablo_data.append({
                    "PLAKA": b['plaka'],
                    "HIZ": f"{b['hiz']} km/s",
                    "YOLCU": b['gunlukYolcu'],
                    "KONUM": maps_url  # Link burada
                })
            
            df = pd.DataFrame(tablo_data)
            
            # Tabloyu Gelişmiş Göster (Link butonu ile)
            st.dataframe(
                df,
                column_config={
                    "KONUM": st.column_config.LinkColumn(
                        "Canlı Konum",
                        help="Google Haritalar'da aç",
                        validate="^https://",
                        display_text="📍 Haritada Aç"
                    )
                },
                hide_index=True,
                use_container_width=True
            )
            
            # --- HIZLI YÖNLENDİRME ---
            st.markdown("### 👇 Hızlı Takip")
            plaka_secim = st.selectbox("Canlı izlemek istediğin aracı seç:", 
                                     ["Seçiniz..."] + [b['plaka'] for b in data])
            
            if plaka_secim and plaka_secim != "Seçiniz...":
                # Seçilen aracı datadan çekip session'a atıyoruz
                hedef_arac = next((x for x in data if x['plaka'] == plaka_secim), None)
                if hedef_arac:
                    # Hat bilgisini de ekleyelim ki eksik kalmasın
                    hedef_arac['hatkodu'] = giris 
                    st.session_state.secilen_plaka = hedef_arac
        else:
            st.warning("Bu hatta aktif araç yok.")

# --- 4. VE EN ÖNEMLİ KISIM: CANLI TAKİP PANELİ ---
# Eğer yukarıdaki işlemlerden birinde bir araç seçildiyse (session dolduysa) burası çalışır.
if st.session_state.secilen_plaka:
    arac = st.session_state.secilen_plaka
    
    st.markdown("---")
    st.subheader(f"🔴 CANLI İZLEME: {arac['plaka']}")
    
    # OTO YENİLEME KUTUSU
    oto_yenile = st.checkbox("🔄 Otomatik Yenile (20 saniye)", value=False)
    
    # Eğer oto yenileme açıksa veriyi TAZELE
    if oto_yenile:
        time.sleep(20) # 20 saniye bekle
        st.rerun() # Sayfayı yenile (Bu, veriyi API'den tekrar çeker)
        
        # Not: Sayfa yenilenince 'giris' değişkeni tekrar çalışır ve veriyi taze çeker.
        # Bu döngü, checkbox açık olduğu sürece devam eder.

    # KOKPİT BİLGİLERİ
    c1, c2, c3, c4 = st.columns(4)
    c1.info(f"**HAT:** {arac.get('hatkodu')}")
    c2.metric("Hız", f"{arac.get('hiz')} km/s")
    c3.metric("Yolcu", f"{arac.get('seferYolcu')}")
    c4.metric("Ciro", f"{arac.get('gunlukYolcu')}")
    
    # GOOGLE MAPS BUTONU (AYRI KUTU)
    g_maps = google_maps_link(arac['enlem'], arac['boylam'])
    st.link_button("📍 Google Haritalar'da Git", g_maps, use_container_width=True)
    
    # CANLI HARİTA (Kırmızı Noktalı)
    lat = float(arac['enlem'])
    lon = float(arac['boylam'])
    
    m = folium.Map(location=[lat, lon], zoom_start=15)
    
    # Kırmızı İkon
    folium.Marker(
        [lat, lon],
        tooltip=f"{arac['plaka']}",
        popup=f"Hız: {arac['hiz']} km/s",
        icon=folium.Icon(color="red", icon="bus", prefix="fa")
    ).add_to(m)
    
    st_folium(m, width=700, height=350)
    
    st.caption(f"Son Veri: {datetime.now().strftime('%H:%M:%S')}")
