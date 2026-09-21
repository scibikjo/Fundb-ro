import os
import json
import base64
import datetime
import pandas as pd
import streamlit as st
from PIL import Image
from supabase import create_client, Client

# Optional: Google Gemini KI für die automatische Formular-Befüllung
try:
    import google.generativeai as genai
    HAS_GEMINI = True
except ImportError:
    HAS_GEMINI = False

# =========================================================
# 1. STREAMLIT CONFIG & CUSTOM HTML/CSS DESIGN
# =========================================================
st.set_page_config(
    page_title="FundSpot – Schul-Fundbüro",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Hier wird das komplette HTML/CSS-Design deiner HTML-Vorlage injiziert
st.markdown("""
    <style>
        /* Import der Schriftart aus dem HTML-Design */
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
        
        html, body, [class*="css"] {
            font-family: 'Plus Jakarta Sans', sans-serif !important;
            background-color: #f4f7f5 !important;
            color: #111827;
        }

        #MainMenu, footer, header {visibility: hidden;}
        .block-container {padding-top: 1.5rem !important; padding-bottom: 3rem !important; max-width: 1100px;}
        
        /* Hero Banner aus HTML */
        .hero-banner {
            background: linear-gradient(135deg, #1b5e20 0%, #2e7d32 100%);
            border-radius: 20px;
            padding: 28px 32px;
            color: white;
            box-shadow: 0 10px 24px rgba(27, 94, 32, 0.15);
            margin-bottom: 24px;
        }
        .hero-banner h1 { font-weight: 800; font-size: 2.2rem; margin: 0; color: white; }
        .hero-banner p { color: #e8f5e9; font-size: 1rem; margin-top: 6px; margin-bottom: 0; }

        /* Container & Karten im HTML-Look */
        div[data-testid="stVerticalBlockBorderWrapper"] {
            background-color: #ffffff !important;
            border-radius: 20px !important;
            border: 1px solid #e5e7eb !important;
            box-shadow: 0 4px 16px rgba(0,0,0,0.04) !important;
            padding: 18px !important;
            transition: all 0.2s ease;
        }
        
        /* HTML Badges */
        .badge-offen {
            background-color: #e8f5e9; color: #1b5e20;
            padding: 4px 12px; border-radius: 12px;
            font-weight: 800; font-size: 0.75rem; text-transform: uppercase;
            display: inline-block;
        }
        .badge-beansprucht {
            background-color: #fef3c7; color: #d97706;
            padding: 4px 12px; border-radius: 12px;
            font-weight: 800; font-size: 0.75rem; text-transform: uppercase;
            display: inline-block;
        }
        .uploader-tag {
            background-color: #f1f5f9; color: #475569;
            padding: 4px 10px; border-radius: 8px;
            font-weight: 600; font-size: 0.8rem;
            display: inline-block;
        }

        /* Buttons wie im HTML Styled */
        .stButton>button {
            border-radius: 14px !important;
            font-weight: 700 !important;
            border: none !important;
            transition: all 0.2s !important;
        }
        
        /* Input Felder stylen */
        .stTextInput>div>div>input, .stSelectbox>div>div>div {
            border-radius: 12px !important;
            border: 1px solid #e5e7eb !important;
            background-color: #f9fafb !important;
        }
    </style>
""", unsafe_allow_html=True)

# =========================================================
# 2. SUPABASE & SPEICHER-BACKEND
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
        },
        {
            "id": 2,
            "titel": "Blaue Adidas Strickjacke",
            "kategorie": "Kleidung",
            "fundort": "Turnhalle",
            "raum": "Halle 2",
            "datum": "2026-09-21",
            "status": "Offen",
            "kontakt": "Hausmeister",
            "uploader": "Maria (10a)",
            "beansprucht_von": "",
            "bild_base64": "https://images.unsplash.com/photo-1434389677669-e08b4cac3105?w=600&auto=format&fit=crop&q=80"
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
# 3. KI-ANALSYE (AUTOMATISCHES AUSFÜLLEN)
# =========================================================
def analyze_image_with_ai(image_file):
    gemini_key = st.secrets.get("GEMINI_API_KEY")
    if HAS_GEMINI and gemini_key:
        try:
            genai.configure(api_key=gemini_key)
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            img = Image.open(image_file)
            prompt = """
            Analysiere dieses Fundstück-Bild für ein Schul-Fundbüro.
            Gib ein valides JSON-Objekt zurück mit folgenden Werten:
            - titel: Prägnanter deutscher Name (z.B. "Grüner Nike Rucksack")
            - kategorie: Exakt eine dieser ("Kleidung", "Elektronik", "Bücher & Hefte", "Sonstiges")
            - vermuteter_ort: Ein möglicher Ort in der Schule wo man das verliert (z.B. "Pausenhof", "Turnhalle", "Klassenzimmer", "Unbekannt")
            """
            res = model.generate_content([prompt, img])
            text = res.text.replace("```json", "").replace("```", "").strip()
            return json.loads(text)
        except Exception:
            pass
    
    return {"titel": "", "kategorie": "Sonstiges", "vermuteter_ort": ""}

# =========================================================
# 4. SESSION STATE & NAVIGATION
# =========================================================
if "current_user" not in st.session_state:
    st.session_state.current_user = "Johann (8b)"
if "is_admin" not in st.session_state:
    st.session_state.is_admin = False
if "tab" not in st.session_state:
    st.session_state.tab = "entdecken"

# Session States für KI-ausgefüllte Felder
if "ai_title" not in st.session_state:
    st.session_state.ai_title = ""
if "ai_category" not in st.session_state:
    st.session_state.ai_category = "Sonstiges"
if "ai_ort" not in st.session_state:
    st.session_state.ai_ort = ""

# =========================================================
# 5. HEADER & NUTZER-LEISTE
# =========================================================
st.markdown("""
    <div class="hero-banner">
        <h1>🌱 FundSpot</h1>
        <p>Das digitale Schul-Fundbüro – Entdecken, Automatisch Erkennen & Wiederfinden</p>
    </div>
""", unsafe_allow_html=True)

col_u1, col_u2, col_u3 = st.columns([2, 2, 1])
with col_u1:
    st.session_state.current_user = st.text_input("👤 Dein Name / Klasse:", value=st.session_state.current_user)
with col_u2:
    passcode = st.text_input("🔑 Admin-Passcode:", type="password", placeholder="Für globale Löschrechte")
    st.session_state.is_admin = (passcode == "admin123")
with col_u3:
    st.write("")
    st.write("")
    if st.session_state.is_admin:
        st.success("Admin aktiv")

st.divider()

# Navigation Tabs im HTML-Stil
col_b1, col_b2 = st.columns(2)
with col_b1:
    if st.button("🔍 Entdecken & Suchen", use_container_width=True, type="primary" if st.session_state.tab == "entdecken" else "secondary"):
        st.session_state.tab = "entdecken"
        st.rerun()
with col_b2:
    if st.button("➕ Fundstück hochladen", use_container_width=True, type="primary" if st.session_state.tab == "hochladen" else "secondary"):
        st.session_state.tab = "hochladen"
        st.rerun()

st.write("")

# =========================================================
# TAB 1: ENTDECKEN (KARTEN IM HTML-LOOK + BUTTONS)
# =========================================================
if st.session_state.tab == "entdecken":
    
    c1, c2 = st.columns([3, 1])
    with c1:
        search = st.text_input("🔎 Suche...", placeholder="Rucksack, Jacke, Mensa, Halle...")
    with c2:
        category = st.selectbox("Kategorie Filter", ["Alle", "Kleidung", "Elektronik", "Bücher & Hefte", "Sonstiges"])

    all_items = load_items()
    
    filtered = []
    for item in all_items:
        match_search = search.lower() in str(item.get("titel", "")).lower() or search.lower() in str(item.get("fundort", "")).lower()
        match_cat = (category == "Alle") or (item.get("kategorie") == category)
        if match_search and match_cat:
            filtered.append(item)

    if not filtered:
        st.info("Keine Fundstücke gefunden.")
    else:
        # Karten-Grid (3 Spalten)
        cols = st.columns(3)
        for idx, item in enumerate(filtered):
            with cols[idx % 3]:
                with st.container(border=True):
                    # Bildanzeige
                    img_src = item.get("bild_base64", "")
                    if img_src and (img_src.startswith("data:image") or img_src.startswith("http")):
                        st.image(img_src, use_container_width=True)
                    else:
                        st.image("https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=600&auto=format&fit=crop&q=80", use_container_width=True)

                    # Karten-Inhalt
                    st.subheader(item.get("titel", "Unbenannt"))
                    
                    # Status Badge
                    status = item.get("status", "Offen")
                    if status == "Beansprucht":
                        st.markdown(f'<span class="badge-beansprucht">Markiert von {item.get("beansprucht_von", "Jemandem")}</span>', unsafe_allow_html=True)
                    else:
                        st.markdown('<span class="badge-offen">Offen</span>', unsafe_allow_html=True)
                        
                    st.write(f"📍 **Ort:** {item.get('fundort', '-')} ({item.get('raum', '-')})")
                    st.write(f"🔑 **Abgabe bei:** {item.get('kontakt', 'Sekretariat')}")
                    st.markdown(f'<span class="uploader-tag">👤 Hochgeladen von: {item.get("uploader", "Anonym")}</span>', unsafe_allow_html=True)
                    
                    st.write("")
                    
                    # 1. BUTTON: "Das gehört mir!"
                    if status == "Offen":
                        if st.button("🙋‍♂️ Das gehört mir!", key=f"claim_{item['id']}", use_container_width=True):
                            update_item_status(item["id"], "Beansprucht", st.session_state.current_user)
                            st.toast("✅ Als beansprucht markiert!")
                            st.rerun()
                    elif status == "Beansprucht":
                        if item.get("beansprucht_von") == st.session_state.current_user or st.session_state.is_admin:
                            if st.button("🔄 Wieder als 'Offen' freigeben", key=f"unclaim_{item['id']}", use_container_width=True):
                                update_item_status(item["id"], "Offen", "")
                                st.rerun()

                    # 2. BUTTON: LÖSCHEN (Ersteller ODER Admin)
                    is_owner = (item.get("uploader") == st.session_state.current_user)
                    if is_owner or st.session_state.is_admin:
                        if st.button("🗑️ Löschen", key=f"del_{item['id']}", type="secondary", use_container_width=True):
                            delete_item(item["id"])
                            st.toast("Eintrag gelöscht!")
                            st.rerun()

# =========================================================
# TAB 2: HOCHLADEN (MIT KI-ERKENNUNG & VORAUSFÜLLUNG)
# =========================================================
elif st.session_state.tab == "hochladen":
    st.subheader("📸 Neues Fundstück eintragen")
    
    with st.container(border=True):
        uploaded_file = st.file_uploader("1. Wähle ein Foto aus", type=["jpg", "jpeg", "png", "webp"])
        
        b64_image_str = ""
        
        if uploaded_file is not None:
            st.image(uploaded_file, caption="Hochgeladenes Foto", width=250)
            
            bytes_data = uploaded_file.getvalue()
            b64_image_str = f"data:image/jpeg;base64,{base64.b64encode(bytes_data).decode()}"
            
            # KI-Erkennung ausführen
            if st.button("🤖 Foto von KI analysieren lassen", use_container_width=True):
                with st.spinner("KI liest Gegenstand, Kategorie & Ort aus..."):
                    ai_data = analyze_image_with_ai(uploaded_file)
                    st.session_state.ai_title = ai_data.get("titel", "")
                    st.session_state.ai_category = ai_data.get("kategorie", "Sonstiges")
                    st.session_state.ai_ort = ai_data.get("vermuteter_ort", "")
                    st.success("✅ KI hat das Formular für dich ausgefüllt!")

        st.divider()
        st.write("### 2. Details überprüfen & Veröffentlichen")

        # Formular nimmt automatisch die Werte der KI an
        with st.form("add_form"):
            titel = st.text_input("Gegenstand / Bezeichnung *", value=st.session_state.ai_title, placeholder="z. B. Roter Nike Rucksack")
            
            c_kat, c_ort = st.columns(2)
            with c_kat:
                kategorien = ["Sonstiges", "Kleidung", "Elektronik", "Bücher & Hefte"]
                idx = kategorien.index(st.session_state.ai_category) if st.session_state.ai_category in kategorien else 0
                kategorie = st.selectbox("Kategorie", kategorien, index=idx)
            with c_ort:
                fundort = st.text_input("Fundort *", value=st.session_state.ai_ort, placeholder="z. B. Mensa, Turnhalle")

            c_raum, c_kontakt = st.columns(2)
            with c_raum:
                raum = st.text_input("Raum / Bereich", placeholder="z. B. EG oder Raum 102")
            with c_kontakt:
                kontakt = st.text_input("Abgabeort / Kontakt", placeholder="z. B. Sekretariat")

            submit = st.form_submit_button("🚀 Fundstück hochladen", use_container_width=True, type="primary")

            if submit:
                if not titel or not fundort:
                    st.error("Bitte gib mindestens einen Titel und den Fundort an.")
                else:
                    new_entry = {
                        "id": int(datetime.datetime.now().timestamp()),
                        "titel": titel,
                        "kategorie": kategorie,
                        "fundort": fundort,
                        "raum": raum if raum else "-",
                        "datum": str(datetime.date.today()),
                        "status": "Offen",
                        "kontakt": kontakt if kontakt else "Sekretariat",
                        "uploader": st.session_state.current_user,
                        "beansprucht_von": "",
                        "bild_base64": b64_image_str
                    }
                    add_new_item(new_entry)
                    st.toast("🎉 Fundstück erfolgreich eingetragen!")
                    
                    # Session zurücksetzen & wechseln
                    st.session_state.ai_title = ""
                    st.session_state.ai_category = "Sonstiges"
                    st.session_state.ai_ort = ""
                    st.session_state.tab = "entdecken"
                    st.rerun()
