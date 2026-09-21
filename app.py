import os
import json
import base64
import datetime
import pandas as pd
import streamlit as st
from PIL import Image
from supabase import create_client, Client

# Google Gemini KI Integration
try:
    import google.generativeai as genai
    HAS_GEMINI = True
except ImportError:
    HAS_GEMINI = False

# =========================================================
# 1. STREAMLIT CONFIG & DESIGN
# =========================================================
st.set_page_config(
    page_title="FundSpot – Das digitale Schul-Fundbüro",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');

        html, body, [class*="css"], .stApp {
            font-family: 'Plus Jakarta Sans', sans-serif !important;
            background-color: #f1f5f9 !important;
            color: #0f172a !important;
        }

        #MainMenu, footer, header { visibility: hidden !important; }
        .block-container {
            padding-top: 1.5rem !important;
            padding-bottom: 4rem !important;
            max-width: 1200px !important;
        }

        .hero-banner-html {
            background: linear-gradient(135deg, #166534 0%, #15803d 50%, #22c55e 100%);
            border-radius: 24px;
            padding: 32px;
            color: #ffffff;
            box-shadow: 0 10px 20px rgba(22, 101, 52, 0.15);
            margin-bottom: 24px;
        }
        .hero-banner-html h1 { font-weight: 800; font-size: 2.2rem; margin: 0; color: #ffffff !important; }
        .hero-banner-html p { color: #dcfce7; font-size: 1rem; margin-top: 6px; margin-bottom: 0; }

        .badge {
            padding: 4px 12px;
            border-radius: 9999px;
            font-weight: 700;
            font-size: 0.75rem;
            text-transform: uppercase;
            display: inline-block;
        }
        .badge-offen { background-color: #dcfce7; color: #15803d; }
        .badge-beansprucht { background-color: #fef3c7; color: #b45309; }
        .badge-kategorie { background-color: #f1f5f9; color: #475569; }

        div[data-baseweb="input"] > div { border-radius: 12px !important; }
        div[data-baseweb="select"] > div { border-radius: 12px !important; }
    </style>
""", unsafe_allow_html=True)

# =========================================================
# 2. SUPABASE / CSV SPEICHER
# =========================================================
@st.cache_resource
def get_supabase():
    url = st.secrets.get("SUPABASE_URL")
    key = st.secrets.get("SUPABASE_KEY")
    if url and key:
        try:
            return create_client(url, key)
        except Exception:
            return None
    return None

supabase: Client = get_supabase()

def load_items():
    if supabase:
        try:
            res = supabase.table("fundstuecke").select("*").order("id", desc=True).execute()
            if res.data:
                return res.data
        except Exception:
            pass
            
    csv_file = "fundbuero_db.csv"
    if os.path.exists(csv_file):
        try:
            df = pd.read_csv(csv_file).fillna("")
            return df.to_dict(orient="records")
        except Exception:
            pass

    default_data = [
        {
            "id": 1,
            "titel": "Grüner Nike Rucksack",
            "kategorie": "Sonstiges",
            "fundort": "Mensa",
            "raum": "EG",
            "datum": "2026-09-20",
            "status": "Offen",
            "kontakt": "Sekretariat",
            "uploader": "Johann (8b)",
            "beansprucht_von": "",
            "bild_base64": "https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=600&auto=format&fit=crop&q=80"
        }
    ]
    pd.DataFrame(default_data).to_csv(csv_file, index=False)
    return default_data

def save_items(items):
    csv_file = "fundbuero_db.csv"
    pd.DataFrame(items).to_csv(csv_file, index=False)

def update_item_status(item_id, status, claimer=""):
    items = load_items()
    for item in items:
        if str(item["id"]) == str(item_id):
            item["status"] = status
            item["beansprucht_von"] = claimer
            break
            
    if supabase:
        try:
            supabase.table("fundstuecke").update({"status": status, "beansprucht_von": claimer}).eq("id", item_id).execute()
        except Exception:
            pass
    save_items(items)

def delete_item(item_id):
    items = load_items()
    items = [i for i in items if str(i["id"]) != str(item_id)]
    
    if supabase:
        try:
            supabase.table("fundstuecke").delete().eq("id", item_id).execute()
        except Exception:
            pass
    save_items(items)

def add_new_item(item_dict):
    items = load_items()
    items.insert(0, item_dict)
    
    if supabase:
        try:
            supabase.table("fundstuecke").insert(item_dict).execute()
        except Exception:
            pass
    save_items(items)

# =========================================================
# 3. KI ANALYSE MIT FEHLERDIAGNOSE
# =========================================================
def analyze_image_with_ai(image_file):
    """Analysiert das Bild und gibt Fehler direkt zurück, falls etwas schiefgeht."""
    if not HAS_GEMINI:
        return None, "Das Paket 'google-generativeai' ist nicht installiert. Bitte 'pip install google-generativeai' ausführen."

    # API Key aus st.secrets oder Umgebungsvariablen laden
    gemini_key = st.secrets.get("GEMINI_API_KEY") or os.environ.get("GEMINI_API_KEY")
    if not gemini_key:
        return None, "Kein 'GEMINI_API_KEY' in den Secrets gefunden! Bitte trage deinen API-Key in `.streamlit/secrets.toml` ein."

    try:
        genai.configure(api_key=gemini_key)
        
        # Nutzen des stabilen Gemini 1.5 Flash Models
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        img = Image.open(image_file)
        
        prompt = """
        Du bist der Erkennungs-Assistent für ein Schul-Fundbüro.
        Analysiere das Bild und antworte AUSSCHLIESSLICH in diesem JSON-Format ohne Markdown oder Extra-Text:
        {
          "titel": "<Kurzer Gegenstandsname auf Deutsch>",
          "kategorie": "<Exakt eines aus: Kleidung | Elektronik | Bücher & Hefte | Sonstiges>",
          "vermuteter_ort": "<Möglicher Ort z.B. Turnhalle, Mensa, Pausenhof>"
        }
        """
        
        response = model.generate_content([prompt, img])
        
        # JSON säubern & parsen
        raw_text = response.text.strip()
        if "```json" in raw_text:
            raw_text = raw_text.split("```json")[1].split("```")[0].strip()
        elif "```" in raw_text:
            raw_text = raw_text.split("```")[1].split("```")[0].strip()
            
        data = json.loads(raw_text)
        return data, None

    except Exception as e:
        return None, f"Fehler bei der KI-Analyse: {str(e)}"

# =========================================================
# 4. SESSION STATE
# =========================================================
if "current_user" not in st.session_state:
    st.session_state.current_user = "Schüler / Finder"
if "is_admin" not in st.session_state:
    st.session_state.is_admin = False
if "tab" not in st.session_state:
    st.session_state.tab = "entdecken"

# Speicher für die Formularfelder
if "f_titel" not in st.session_state:
    st.session_state.f_titel = ""
if "f_kategorie" not in st.session_state:
    st.session_state.f_kategorie = "Sonstiges"
if "f_ort" not in st.session_state:
    st.session_state.f_ort = ""

# =========================================================
# 5. OBERFLÄCHE
# =========================================================
st.markdown("""
    <div class="hero-banner-html">
        <h1>🌱 FundSpot</h1>
        <p>Das digitale Schul-Fundbüro – Automatische KI-Erkennung</p>
    </div>
""", unsafe_allow_html=True)

col1, col2 = st.columns([3, 1])
with col1:
    st.session_state.current_user = st.text_input("👤 Dein Name / Klasse:", value=st.session_state.current_user)
with col2:
    passcode = st.text_input("🔑 Admin-Passcode:", type="password", placeholder="admin123")
    st.session_state.is_admin = (passcode == "admin123")

st.write("")
nav_c1, nav_c2 = st.columns(2)
with nav_c1:
    if st.button("🔍 Fundstücke durchsuchen", use_container_width=True, type="primary" if st.session_state.tab == "entdecken" else "secondary"):
        st.session_state.tab = "entdecken"
        st.rerun()
with nav_c2:
    if st.button("➕ Neues Fundstück eintragen", use_container_width=True, type="primary" if st.session_state.tab == "hochladen" else "secondary"):
        st.session_state.tab = "hochladen"
        st.rerun()

st.write("")

# TAB 1: ENTDECKEN
if st.session_state.tab == "entdecken":
    items = load_items()
    cols = st.columns(3)
    for idx, item in enumerate(items):
        with cols[idx % 3]:
            with st.container(border=True):
                img_src = item.get("bild_base64") or "https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=600&auto=format&fit=crop&q=80"
                st.image(img_src, use_container_width=True)
                st.subheader(item.get("titel", "Unbenannt"))
                st.write(f"📍 **Ort:** {item.get('fundort')} ({item.get('raum')})")
                st.write(f"👤 **Von:** {item.get('uploader')}")
                
                if item.get("uploader") == st.session_state.current_user or st.session_state.is_admin:
                    if st.button("🗑️ Löschen", key=f"del_{item['id']}", use_container_width=True):
                        delete_item(item["id"])
                        st.rerun()

# TAB 2: HOCHLADEN (MIT EXPLIZITER KI-DIAGNOSE)
elif st.session_state.tab == "hochladen":
    st.subheader("📸 Neues Fundstück eintragen")
    
    with st.container(border=True):
        uploaded_file = st.file_uploader("1. Wähle ein Foto aus", type=["jpg", "jpeg", "png", "webp"])
        
        b64_img = ""
        if uploaded_file:
            st.image(uploaded_file, caption="Vorschau", width=200)
            b64_img = f"data:image/jpeg;base64,{base64.b64encode(uploaded_file.getvalue()).decode()}"
            
            # KI-Button mit Diagnoseanzeige
            if st.button("🤖 Foto von KI analysieren & Felder befüllen", type="primary", use_container_width=True):
                with st.spinner("Gemini KI liest das Bild aus..."):
                    ai_data, error_msg = analyze_image_with_ai(uploaded_file)
                    
                    if error_msg:
                        st.error(f"❌ KI konnte nicht ausgeführt werden:\n{error_msg}")
                    elif ai_data:
                        st.session_state.f_titel = ai_data.get("titel", "")
                        st.session_state.f_kategorie = ai_data.get("kategorie", "Sonstiges")
                        st.session_state.f_ort = ai_data.get("vermuteter_ort", "")
                        st.success("✅ KI hat den Gegenstand erkannt und das Formular ausgefüllt!")
                        st.rerun()

        st.divider()
        st.write("### 2. Formular überprüfen")

        # Das eigentliche Formular nimmt direkt die Session State Werte an
        titel_val = st.text_input("Gegenstand / Titel *", value=st.session_state.f_titel)
        
        kategorien = ["Sonstiges", "Kleidung", "Elektronik", "Bücher & Hefte"]
        kat_idx = kategorien.index(st.session_state.f_kategorie) if st.session_state.f_kategorie in kategorien else 0
        kat_val = st.selectbox("Kategorie", kategorien, index=kat_idx)
        
        ort_val = st.text_input("Fundort *", value=st.session_state.f_ort)
        raum_val = st.text_input("Raum / Bereich")
        kontakt_val = st.text_input("Abgabeort / Kontakt", value="Sekretariat")

        if st.button("🚀 Fundstück speichern", type="primary", use_container_width=True):
            if not titel_val or not ort_val:
                st.error("Bitte gib mindestens einen Titel und den Ort ein.")
            else:
                new_entry = {
                    "id": int(datetime.datetime.now().timestamp()),
                    "titel": titel_val,
                    "kategorie": kat_val,
                    "fundort": ort_val,
                    "raum": raum_val if raum_val else "-",
                    "datum": str(datetime.date.today()),
                    "status": "Offen",
                    "kontakt": kontakt_val,
                    "uploader": st.session_state.current_user,
                    "beansprucht_von": "",
                    "bild_base64": b64_img
                }
                add_new_item(new_entry)
                st.toast("🎉 Fundstück gespeichert!")
                st.session_state.f_titel = ""
                st.session_state.f_ort = ""
                st.session_state.tab = "entdecken"
                st.rerun()
