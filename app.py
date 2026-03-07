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
            margin: 4px 0px !important;
            line-height: 24px !important;
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
            margin: 4px 0px !important;
            display: flex; justify-content: center; align-items: center;
            line-height: 24px !important;
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
        
        .note-card {
            background-color: #3e2a00;
            border-left: 5px solid #ffc107;
            color: #e0e0e0;
            padding: 12px;
            margin-top: 20px;
            margin-bottom: 10px;
            border-radius: 4px;
            font-size: 12px;
            line-height: 1.5;
        }
        
        .oho-note {
            background-color: #1a2a3a;
            border-left: 5px solid #3498db;
            color: #e0e0e0;
            padding: 12px;
            margin-bottom: 15px;
            border-radius: 4px;
            font-size: 12px;
            line-height: 1.5;
        }
        
        .type-summary-card {
            background-color: #1e1e1e;
            border: 1px solid #444;
            border-left: 4px solid #f39c12;
            padding: 12px;
            border-radius: 5px;
            margin-bottom: 15px;
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
        
        .stTabs [data-baseweb="tab-list"] {
            gap: 10px;
        }
        .stTabs [data-baseweb="tab"] {
            height: 40px;
            white-space: pre-wrap;
            background-color: #1e1e1e;
            border-radius: 4px 4px 0px 0px;
            padding: 10px 20px;
        }
        .stTabs [aria-selected="true"] {
            background-color: #ff4b4b !important;
            color: white !important;
        }
    </style>
""", unsafe_allow_html=True)

API_URL = "https://bursakartapi.abys-web.com/api/static/realtimedata"
HEADERS = {
    'Content-Type': 'application/json',
    'Origin': 'https://www.bursakart.com.tr',
    'Referer': 'https://www.bursakart.com.tr/',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
}

# --- HAT LİSTELERİ ---
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

OHO_BATI = ["1C", "1T", "1TG", "1TK", "2B", "2BT", "2E", "B2", "B3", "B4", "B5", "6F", "6FD", "6E", "6A", "6K1", "B8", "8L", "9D", "9M", "9PA", "B9", "B10", "B10K", "B12", "B13", "14L", "14L2", "14N", "14F", "B16A", "B16B", "B17", "B17B", "B17A", "B20A", "B20B", "B20C", "B20D", "B24", "B25", "B27", "B29", "B31", "B31A", "B32", "B32A", "B33", "B33H", "B33A", "B33K", "B34", "B34U", "B35K1", "B35K2", "35H", "B36", "B36M", "B36C", "B36A", "B36U", "B38", "B39", "B39K", "B40", "40H", "B41B", "B41C", "B42A", "B43", "43A", "B44B", "B46", "97A", "H2"]
OHO_DOGU = ["19B", "19D", "19İ", "D1B", "20", "20A", "21", "23", "23A", "24B", "24D", "27A", "28A"]

# --- OTOBÜS TİPLERİ LİSTESİ ---
SIRKET_HATLARI = ["6E", "6A", "97A"]
OTOBUS_12M_HATLARI = ["1T", "1TG", "1TK", "6F", "6FD", "6K1", "8L", "9D", "B24", "B25", "B40", "40H", "B41B", "B41C", "B42A", "43A", "B44B", "H2"]
DOGU_MIKROBUS_HATLARI = ["19D", "24D", "27A", "28A"]

def get_turkey_time():
    tz = pytz.timezone('Europe/Istanbul')
    return datetime.now(tz).strftime('%H:%M:%S')

def get_address(lat, lon):
    try:
        geolocator = Nominatim(user_agent="cntooturk_bursa_panel", timeout=5)
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
        return "Adres bilgisi bekleniyor..."
    return "Adres bilgisi bekleniyor..."

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
            payload = {"keyword": keyword, "take": 2000, "limit": 2000}
        else:
            payload = {"keyword": keyword}
            
        for _ in range(2):
            try:
                r = requests.post(API_URL, headers=HEADERS, json=payload, timeout=8, verify=False)
                if r.status_code == 200:
                    data = r.json().get("result", [])
                    if data: return data
            except:
                time.sleep(1)
                continue
                
        return []
    except: return []

def oho_hat_verisi_getir(hat):
    res = veri_cek(hat, genis_sorgu=True)
    goru_plaka = set()
    temiz = []
    for b in res:
        if b['plaka'] not in goru_plaka:
            temiz.append(b)
            goru_plaka.add(b['plaka'])
    
    ham_yolcu = sum(int(float(b.get('gunlukYolcu', 0) or 0)) for b in temiz)
    k_yolcu = int(ham_yolcu * 1.11)
    return {"hat": hat, "arac": len(temiz), "yolcu": k_yolcu}

# --- ENTEGRE HAT BİRLEŞTİRİCİ (ÇOKLU HAT DESTEĞİ) ---
def hatlari_birlestir(veri_listesi, hatlar_listesi, yeni_isim):
    birlesecekler = [x for x in veri_listesi if x['hat'] in hatlar_listesi]
    
    if birlesecekler:
        toplam_arac = sum(x['arac'] for x in birlesecekler)
        toplam_yolcu = sum(x['yolcu'] for x in birlesecekler)
        
        # Alt Kırılımları Yolcu Sayısına Göre Büyükten Küçüğe Sırala
        sub_hatlar = sorted(birlesecekler, key=lambda x: x['yolcu'], reverse=True)
        
        veri_listesi = [x for x in veri_listesi if x['hat'] not in hatlar_listesi]
        
        veri_listesi.append({
            "hat": yeni_isim, 
            "arac": toplam_arac, 
            "yolcu": toplam_yolcu,
            "is_merged": True,
            "sub_hatlar": sub_hatlar
        })
        
    return veri_listesi

def google_maps_link(lat, lon):
    return f"https://www.google.com/maps?q={lat},{lon}"

def yandex_maps_link(lat, lon):
    return f"https://yandex.com.tr/harita/?text={lat},{lon}"

if 'secilen_plaka' not in st.session_state:
    st.session_state.secilen_plaka = None
if 'takip_modu' not in st.session_state:
    st.session_state.takip_modu = False
if 'aktif_arama' not in st.session_state:
    st.session_state.aktif_arama = None
if 'hat_ham_veri' not in st.session_state:
    st.session_state.hat_ham_veri = []
if 'oho_data' not in st.session_state:
    st.session_state.oho_data = None
if 'show_switch_toast' not in st.session_state:
    st.session_state.show_switch_toast = False

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

st.title("🚌 Cntooturk Takip Sistemi")
st.caption(f"🕒 {get_turkey_time()} | ⚡ 20 Sn Güncelleme | 🚀 v105")

# KISAYOL TIKLANDIĞINDA ÇIKAN UYARI MESAJI
if st.session_state.show_switch_toast:
    hat_adi = st.session_state.show_switch_toast
    st.toast(f"✅ {hat_adi} başarıyla arandı! Lütfen yukarıdan '📍 CANLI TAKİP' sekmesine tıklayın.", icon="🚌")
    st.session_state.show_switch_toast = False

tab_canli, tab_oho = st.tabs(["📍 CANLI TAKİP", "📊 ÖHO HAT VERİLERİ"])

# ==========================================
# 1. SEKME: MEVCUT CANLI TAKİP SİSTEMİ
# ==========================================
with tab_canli:
    if not st.session_state.takip_modu:
        col_input, col_btn = st.columns([3, 1])
        with col_input:
            # Kısayol tıklandığında input kutusu otomatik dolsun diye value eklendi
            giris_text = st.text_input("Giriş:", 
                                       value=st.session_state.get('giris_input', ''), 
                                       placeholder="Örn: 16M10171 veya B5", 
                                       key="giris_kutu")
        with col_btn:
            st.write("") 
            st.write("") 
            btn_baslat = st.button("SORGULA", type="primary")

        if btn_baslat and giris_text:
            giris_temiz = giris_text.replace("i", "İ").replace("ı", "I").upper().strip()
            st.session_state.aktif_arama = giris_temiz
            st.session_state.giris_input = giris_temiz
            st.session_state.takip_modu = False 
            st.session_state.secilen_plaka = None
            st.session_state.hat_ham_veri = []

    if st.session_state.aktif_arama and not st.session_state.takip_modu:
        giris = st.session_state.aktif_arama
        
        if giris == "3" or giris == "0":
            st.subheader("💤 Boş / Servis Dışı")
            veriler = []
            with st.spinner("Taranıyor..."):
                for k in ["HAT SEÇİLMEMİŞ", "SERVİS DIŞI", "0", "3"]:
                    res = veri_cek(k, genis_sorgu=True)
                    if res: veriler.extend(res)
            
            temiz_veriler = []
            goru_plakalar = set()
            for v in veriler:
                if v['plaka'] not in goru_plakalar:
                    temiz_veriler.append(v)
                    goru_plakalar.add(v['plaka'])
            
            temiz_veriler = sorted(temiz_veriler, key=lambda x: int(float(x.get('gunlukYolcu', 0) or 0)), reverse=True)
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
                    
                    h_hiz = float(bus.get('hiz', 0) or 0)
                    k_hiz = int(h_hiz * 1.40)
                    c2.write(f"{k_hiz}")
                    
                    h_yolcu = bus.get('gunlukYolcu', 0) or 0
                    k_yolcu = int(h_yolcu * 1.11)
                    c3.write(f"{k_yolcu}")
                    
                    maps = google_maps_link(bus['enlem'], bus['boylam'])
                    c4.link_button("📍", maps)
                    
                    if c5.button("▶️", key=f"btn_{bus['plaka']}_{i}", type="primary"):
                        bus['hatkodu'] = "SERVİS DIŞI"
                        st.session_state.secilen_plaka = bus
                        st.session_state.takip_modu = True
                        st.rerun()
                    st.divider()

        elif len(giris) > 4 and giris[0].isdigit():
            hedef = plaka_duzenle(giris)
            with st.status("🔍 Araç aranıyor...", expanded=True) as status:
                bulunan = None
                
                status.write(f"📡 '{hedef}' aranıyor...")
                res = veri_cek(hedef, genis_sorgu=False)
                if not res:
                    res = veri_cek(hedef.replace(" ", ""), genis_sorgu=False)
                    
                if res:
                    for b in res:
                        if b.get("plaka", "").replace(" ", "") == hedef.replace(" ", ""):
                            bulunan = b
                            hk = bulunan.get('hatkodu')
                            if not hk or str(hk).strip() == "" or str(hk) == "0":
                                bulunan['hatkodu'] = 'SERVİS DIŞI'
                            else:
                                bulunan['hatkodu'] = hk
                            break
                
                if not bulunan:
                    status.write("🌍 Tüm hatlar taranıyor...")
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
                    status.write("💤 Boş araçlara bakılıyor...")
                    for k in ["HAT SEÇİLMEMİŞ", "SERVİS DIŞI", "0", "3"]:
                        res = veri_cek(k, genis_sorgu=True)
                        for bus in res:
                            if bus.get("plaka", "").replace(" ","") == hedef.replace(" ",""):
                                bulunan = bus
                                bulunan['hatkodu'] = "SERVİS DIŞI"
                                break
                        if bulunan: break

                if bulunan:
                    status.update(label="✅ Bulundu!", state="complete", expanded=False)
                    st.session_state.secilen_plaka = bulunan
                    st.session_state.takip_modu = True
                    time.sleep(1)
                    st.rerun()
                else:
                    status.update(label="❌ Bulunamadı", state="error", expanded=True)
                    st.error(f"❌ {hedef} bulunamadı. Araç cihazı uykuda veya şartel kapatılmış olabilir.")

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
                
                temiz_data = sorted(temiz_data, key=lambda x: int(float(x.get('gunlukYolcu', 0) or 0)), reverse=True)
                st.session_state.hat_ham_veri = temiz_data
            
            if temiz_data:
                ham_toplam = sum(int(float(b.get('gunlukYolcu', 0) or 0)) for b in temiz_data)
                kalibre_toplam = int(ham_toplam * 1.11)
                
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
                
                st.markdown("""
                    <div class="note-card">
                        ⚠️ <b>SİSTEM NOTU:</b><br>
                        Yolcu verileri merkezi sistemden (BURULAŞ/ABYS) kaynaklı olarak 
                        2-3 dakika gecikmeli yansıyabilmektedir.
                    </div>
                """, unsafe_allow_html=True)
                
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
                    
                    h_hiz = float(bus.get('hiz', 0) or 0)
                    k_hiz = int(h_hiz * 1.40)
                    c2.write(f"{k_hiz}")
                    
                    h_yolcu = bus.get('gunlukYolcu', 0) or 0
                    k_yolcu = int(h_yolcu * 1.11)
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

    if st.session_state.takip_modu and st.session_state.secilen_plaka:
        
        arama_terimi = st.session_state.aktif_arama
        is_plaka = len(arama_terimi) > 4 and arama_terimi[0].isdigit()
        
        if is_plaka:
            if st.button("🏠 Ana Menüye Dön"):
                st.session_state.takip_modu = False
                st.session_state.secilen_plaka = None
                st.session_state.aktif_arama = None
                st.session_state.giris_input = ""
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
            st.toast("⚠️ Bağlantı bekleniyor (Yenileniyor...)")

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
        
        h_hiz_canli = float(arac.get('hiz', 0) or 0)
        k_hiz_canli = int(h_hiz_canli * 1.40)
        hiz = f"{k_hiz_canli} km/s"
        
        ham_anlik = arac.get('seferYolcu')
        ham_toplam = arac.get('gunlukYolcu', 0) or 0
        kalibre_toplam = int(ham_toplam * 1.11)

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
        
        st.markdown("""
            <div class="note-card">
                ⚠️ <b>SİSTEM NOTU:</b><br>
                Yolcu verileri merkezi sistemden kaynaklı 2-3 dk gecikmeli gelebilir.
            </div>
        """, unsafe_allow_html=True)

        col_g, col_y = st.columns(2)
        col_g.link_button("🗺️ Google Haritalar", google_maps_link(lat, lon), use_container_width=True)
        col_y.link_button("🧭 Yandex Navigasyon", yandex_maps_link(lat, lon), use_container_width=True)

        m = folium.Map(location=[lat, lon], zoom_start=15)
        folium.Marker(
            [lat, lon],
            tooltip=f"{arac['plaka']}",
            popup=f"Hız: {k_hiz_canli}", 
            icon=folium.Icon(color="red", icon="bus", prefix="fa")
        ).add_to(m)
        st_folium(m, width=700, height=350)

# ==========================================
# 2. SEKME: YENİ ÖHO İSTATİSTİK SİSTEMİ
# ==========================================
with tab_oho:
    st.markdown("<h3 style='text-align: center; color: #ff4b4b; margin-bottom: 5px;'>📊 ÖHO Filo Verileri</h3>", unsafe_allow_html=True)
    
    st.markdown("""
        <div class="oho-note">
            ℹ️ <b>BİLGİLENDİRME:</b><br>
            Bu veriler anlık olarak hat numarası açık olan araçlardan çekilmektedir. 
            Yolcu verilerinde gecikmeler yaşanmaktadır.
        </div>
    """, unsafe_allow_html=True)

    if st.button("🔄 Tüm Verileri Yükle / Güncelle", use_container_width=True, type="primary"):
        with st.spinner("Tüm ÖHO Hatları (Batı ve Doğu) taranıyor, bu işlem birkaç saniye sürebilir..."):
            bati_veriler = []
            dogu_veriler = []
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
                future_bati = {executor.submit(oho_hat_verisi_getir, hat): hat for hat in OHO_BATI}
                for future in concurrent.futures.as_completed(future_bati):
                    bati_veriler.append(future.result())
                    
            with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
                future_dogu = {executor.submit(oho_hat_verisi_getir, hat): hat for hat in OHO_DOGU}
                for future in concurrent.futures.as_completed(future_dogu):
                    dogu_veriler.append(future.result())
            
            # --- KATEGORİ HESAPLAMALARI ---
            s_yolcu = sum(v['yolcu'] for v in bati_veriler if v['hat'] in SIRKET_HATLARI)
            o_12m_yolcu = sum(v['yolcu'] for v in bati_veriler if v['hat'] in OTOBUS_12M_HATLARI)
            m_yolcu = sum(v['yolcu'] for v in bati_veriler if v['hat'] not in SIRKET_HATLARI and v['hat'] not in OTOBUS_12M_HATLARI)
            
            dogu_m_yolcu = sum(v['yolcu'] for v in dogu_veriler if v['hat'] in DOGU_MIKROBUS_HATLARI)
            dogu_o_yolcu = sum(v['yolcu'] for v in dogu_veriler if v['hat'] not in DOGU_MIKROBUS_HATLARI)
            
            # --- ENTEGRE HATLARI BİRLEŞTİRME ---
            bati_veriler = hatlari_birlestir(bati_veriler, ["6F", "6FD"], "6F & 6FD")
            bati_veriler = hatlari_birlestir(bati_veriler, ["B32", "B32A"], "B32 & B32A")
            bati_veriler = hatlari_birlestir(bati_veriler, ["1T", "1TG", "1TK"], "1T & 1TG & 1TK")
            bati_veriler = hatlari_birlestir(bati_veriler, ["B39", "B39K"], "B39 & B39K")
            bati_veriler = hatlari_birlestir(bati_veriler, ["B31", "B31A"], "B31 & B31A")
            bati_veriler = hatlari_birlestir(bati_veriler, ["B35K1", "B35K2"], "B35K1 & B35K2")
            
            # YOLCU SAYISINA GÖRE SIRALAMA
            bati_veriler = sorted(bati_veriler, key=lambda x: x['yolcu'], reverse=True)
            dogu_veriler = sorted(dogu_veriler, key=lambda x: x['yolcu'], reverse=True)
            
            st.session_state.oho_data = {
                "bati": bati_veriler,
                "dogu": dogu_veriler,
                "bati_toplam_yolcu": sum(v['yolcu'] for v in bati_veriler),
                "dogu_toplam_yolcu": sum(v['yolcu'] for v in dogu_veriler),
                "bati_toplam_arac": sum(v['arac'] for v in bati_veriler),
                "dogu_toplam_arac": sum(v['arac'] for v in dogu_veriler),
                "sirket_yolcu": s_yolcu,
                "otobus_12m_yolcu": o_12m_yolcu,
                "otobus_toplam": s_yolcu + o_12m_yolcu,
                "mikrobus_toplam": m_yolcu,
                "dogu_otobus_toplam": dogu_o_yolcu,
                "dogu_mikrobus_toplam": dogu_m_yolcu
            }
            st.success("Veriler başarıyla çekildi ve entegre hatlar birleştirildi!")

    if st.session_state.oho_data:
        data = st.session_state.oho_data
        
        # --- FARK HESAPLAMALARI VE HTML DİZİLİMLERİ ---
        fark_bati = abs(data['otobus_toplam'] - data['mikrobus_toplam'])
        if data['otobus_toplam'] > data['mikrobus_toplam']:
            bati_fark_html = f"<div style='color:#00bc8c; font-size:12px; margin-top:8px; border-top: 1px dashed #555; padding-top: 6px;'>🟢 <b>Otobüsler</b>, mikrobüslerden <b>{fark_bati}</b> yolcu fazla.</div>"
        elif data['mikrobus_toplam'] > data['otobus_toplam']:
            bati_fark_html = f"<div style='color:#00bc8c; font-size:12px; margin-top:8px; border-top: 1px dashed #555; padding-top: 6px;'>🟢 <b>Mikrobüsler</b>, otobüslerden <b>{fark_bati}</b> yolcu fazla.</div>"
        else:
            bati_fark_html = f"<div style='color:#00bc8c; font-size:12px; margin-top:8px; border-top: 1px dashed #555; padding-top: 6px;'>🟢 Otobüs ve Mikrobüs yolcu sayıları eşit.</div>"

        fark_dogu = abs(data['dogu_otobus_toplam'] - data['dogu_mikrobus_toplam'])
        if data['dogu_otobus_toplam'] > data['dogu_mikrobus_toplam']:
            dogu_fark_html = f"<div style='color:#00bc8c; font-size:12px; margin-top:8px; border-top: 1px dashed #555; padding-top: 6px;'>🟢 <b>Otobüsler</b>, mikrobüslerden <b>{fark_dogu}</b> yolcu fazla.</div>"
        elif data['dogu_mikrobus_toplam'] > data['dogu_otobus_toplam']:
            dogu_fark_html = f"<div style='color:#00bc8c; font-size:12px; margin-top:8px; border-top: 1px dashed #555; padding-top: 6px;'>🟢 <b>Mikrobüsler</b>, otobüslerden <b>{fark_dogu}</b> yolcu fazla.</div>"
        else:
            dogu_fark_html = f"<div style='color:#00bc8c; font-size:12px; margin-top:8px; border-top: 1px dashed #555; padding-top: 6px;'>🟢 Otobüs ve Mikrobüs yolcu sayıları eşit.</div>"

        
        cb1, cd1 = st.columns(2)
        cb1.markdown(f"""
            <div class="metric-card" style="border-left: 5px solid #00bc8c;">
                <div class="metric-title">ÖHO BATI TOPLAM YOLCU</div>
                <div class="metric-value">{data['bati_toplam_yolcu']}</div>
                <div style="font-size:11px; color:#aaa; margin-top:5px;">Aktif Araç: {data['bati_toplam_arac']}</div>
            </div>
        """, unsafe_allow_html=True)
        
        cd1.markdown(f"""
            <div class="metric-card" style="border-left: 5px solid #ff4b4b;">
                <div class="metric-title">ÖHO DOĞU TOPLAM YOLCU</div>
                <div class="metric-value">{data['dogu_toplam_yolcu']}</div>
                <div style="font-size:11px; color:#aaa; margin-top:5px;">Aktif Araç: {data['dogu_toplam_arac']}</div>
            </div>
        """, unsafe_allow_html=True)
        
        st.write("")
        
        with st.expander("📂 ÖHO BATI HATLARI DETAYLARI", expanded=False):
            
            st.markdown(f"""
                <div class="type-summary-card">
                    <div style="color:#fff; font-size:16px; font-weight:bold; margin-bottom:5px;">🚌 OTOBÜS HATLARI: <span style="color:#f39c12;">{data['otobus_toplam']}</span> Yolcu</div>
                    <div style="color:#aaa; font-size:12px; margin-left:25px; margin-bottom:3px;">• Şirket Araçları (6E, 6A, 97A): <span style="color:#fff;">{data['sirket_yolcu']}</span></div>
                    <div style="color:#aaa; font-size:12px; margin-left:25px; margin-bottom:8px;">• 12 Metre Araçlar: <span style="color:#fff;">{data['otobus_12m_yolcu']}</span></div>
                    <div style="color:#fff; font-size:16px; font-weight:bold;">🚐 MİKROBÜS HATLARI: <span style="color:#f39c12;">{data['mikrobus_toplam']}</span> Yolcu</div>
                    {bati_fark_html}
                </div>
            """, unsafe_allow_html=True)
            
            c1, c2, c3, c4 = st.columns([1.5, 1.0, 1.0, 1.2])
            c1.markdown("<span class='table-header' style='text-align:left;'>HAT NUMARASI</span>", unsafe_allow_html=True)
            c2.markdown("<span class='table-header' style='text-align:left;'>AKTİF ARAÇ</span>", unsafe_allow_html=True)
            c3.markdown("<span class='table-header' style='text-align:left;'>YOLCU</span>", unsafe_allow_html=True)
            c4.markdown("<span class='table-header' style='text-align:center;'>İŞLEM</span>", unsafe_allow_html=True)
            st.divider()
            
            for b in data['bati']:
                if b['arac'] > 0 or b['yolcu'] > 0: 
                    c1, c2, c3, c4 = st.columns([1.5, 1.0, 1.0, 1.2])
                    
                    c1.markdown(f"<div style='font-size:15px; font-weight:bold; height:32px; display:flex; align-items:center;'>{b['hat']}</div>", unsafe_allow_html=True)
                    c2.markdown(f"<div style='font-size:15px; height:32px; display:flex; align-items:center;'>{b['arac']}</div>", unsafe_allow_html=True)
                    # YOLCU SAYISI KIRMIZI VE KALIN YAPILDI
                    c3.markdown(f"<div style='font-size:15px; font-weight:bold; color:#ff4b4b; height:32px; display:flex; align-items:center;'>{b['yolcu']}</div>", unsafe_allow_html=True)
                    
                    if not b.get('is_merged'):
                        if c4.button("Detay ➡", key=f"detay_b_{b['hat']}", use_container_width=True):
                            st.session_state.aktif_arama = b['hat']
                            st.session_state.giris_input = b['hat']
                            st.session_state.takip_modu = False
                            st.session_state.secilen_plaka = None
                            st.session_state.hat_ham_veri = []
                            st.session_state.show_switch_toast = b['hat']
                            st.rerun()
                    else:
                        c4.write("")

                    if b.get('is_merged'):
                        for sub in b['sub_hatlar']:
                            if sub['arac'] > 0 or sub['yolcu'] > 0:
                                sc1, sc2, sc3, sc4 = st.columns([1.5, 1.0, 1.0, 1.2])
                                sc1.markdown(f"<div style='font-size:14px; font-weight:bold; color:#ff4b4b; padding-left:15px; height:32px; display:flex; align-items:center;'>↳ {sub['hat']}</div>", unsafe_allow_html=True)
                                sc2.markdown(f"<div style='font-size:14px; font-weight:bold; color:#ff4b4b; height:32px; display:flex; align-items:center;'>{sub['arac']}</div>", unsafe_allow_html=True)
                                sc3.markdown(f"<div style='font-size:14px; font-weight:bold; color:#ff4b4b; height:32px; display:flex; align-items:center;'>{sub['yolcu']}</div>", unsafe_allow_html=True)
                                
                                if sc4.button("Detay ➡", key=f"detay_b_sub_{sub['hat']}", use_container_width=True):
                                    st.session_state.aktif_arama = sub['hat']
                                    st.session_state.giris_input = sub['hat']
                                    st.session_state.takip_modu = False
                                    st.session_state.secilen_plaka = None
                                    st.session_state.hat_ham_veri = []
                                    st.session_state.show_switch_toast = sub['hat']
                                    st.rerun()
                    st.divider()

        with st.expander("📂 ÖHO DOĞU HATLARI DETAYLARI", expanded=False):
            
            st.markdown(f"""
                <div class="type-summary-card">
                    <div style="color:#fff; font-size:16px; font-weight:bold; margin-bottom:5px;">🚌 OTOBÜS HATLARI: <span style="color:#f39c12;">{data['dogu_otobus_toplam']}</span> Yolcu</div>
                    <div style="color:#fff; font-size:16px; font-weight:bold;">🚐 MİKROBÜS HATLARI: <span style="color:#f39c12;">{data['dogu_mikrobus_toplam']}</span> Yolcu</div>
                    {dogu_fark_html}
                </div>
            """, unsafe_allow_html=True)
            
            c1, c2, c3, c4 = st.columns([1.5, 1.0, 1.0, 1.2])
            c1.markdown("<span class='table-header' style='text-align:left;'>HAT NUMARASI</span>", unsafe_allow_html=True)
            c2.markdown("<span class='table-header' style='text-align:left;'>AKTİF ARAÇ</span>", unsafe_allow_html=True)
            c3.markdown("<span class='table-header' style='text-align:left;'>YOLCU</span>", unsafe_allow_html=True)
            c4.markdown("<span class='table-header' style='text-align:center;'>İŞLEM</span>", unsafe_allow_html=True)
            st.divider()
            
            for d in data['dogu']:
                if d['arac'] > 0 or d['yolcu'] > 0: 
                    c1, c2, c3, c4 = st.columns([1.5, 1.0, 1.0, 1.2])
                    
                    c1.markdown(f"<div style='font-size:15px; font-weight:bold; height:32px; display:flex; align-items:center;'>{d['hat']}</div>", unsafe_allow_html=True)
                    c2.markdown(f"<div style='font-size:15px; height:32px; display:flex; align-items:center;'>{d['arac']}</div>", unsafe_allow_html=True)
                    # YOLCU SAYISI KIRMIZI VE KALIN YAPILDI
                    c3.markdown(f"<div style='font-size:15px; font-weight:bold; color:#ff4b4b; height:32px; display:flex; align-items:center;'>{d['yolcu']}</div>", unsafe_allow_html=True)
                    
                    if not d.get('is_merged'):
                        if c4.button("Detay ➡", key=f"detay_d_{d['hat']}", use_container_width=True):
                            st.session_state.aktif_arama = d['hat']
                            st.session_state.giris_input = d['hat']
                            st.session_state.takip_modu = False
                            st.session_state.secilen_plaka = None
                            st.session_state.hat_ham_veri = []
                            st.session_state.show_switch_toast = d['hat']
                            st.rerun()
                    else:
                        c4.write("")

                    if d.get('is_merged'):
                        for sub in d['sub_hatlar']:
                            if sub['arac'] > 0 or sub['yolcu'] > 0:
                                sc1, sc2, sc3, sc4 = st.columns([1.5, 1.0, 1.0, 1.2])
                                sc1.markdown(f"<div style='font-size:14px; font-weight:bold; color:#ff4b4b; padding-left:15px; height:32px; display:flex; align-items:center;'>↳ {sub['hat']}</div>", unsafe_allow_html=True)
                                sc2.markdown(f"<div style='font-size:14px; font-weight:bold; color:#ff4b4b; height:32px; display:flex; align-items:center;'>{sub['arac']}</div>", unsafe_allow_html=True)
                                sc3.markdown(f"<div style='font-size:14px; font-weight:bold; color:#ff4b4b; height:32px; display:flex; align-items:center;'>{sub['yolcu']}</div>", unsafe_allow_html=True)
                                
                                if sc4.button("Detay ➡", key=f"detay_d_sub_{sub['hat']}", use_container_width=True):
                                    st.session_state.aktif_arama = sub['hat']
                                    st.session_state.giris_input = sub['hat']
                                    st.session_state.takip_modu = False
                                    st.session_state.secilen_plaka = None
                                    st.session_state.hat_ham_veri = []
                                    st.session_state.show_switch_toast = sub['hat']
                                    st.rerun()
                    st.divider()

# --- GLOBAL REFRESH ---
if st.session_state.aktif_arama:
    time.sleep(20)
    st.rerun()
