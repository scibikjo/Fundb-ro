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
# 1. STREAMLIT CONFIG & ADVANCED HTML/CSS INJECTION
# =========================================================
st.set_page_config(
    page_title="FundSpot – Das digitale Schul-Fundbüro",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Injektion von über 150 Zeilen Custom-HTML/CSS zur vollständigen Umgestaltung
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');

        /* Globale HTML-Resetting & Body-Styling */
        html, body, [class*="css"], .stApp {
            font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif !important;
            background-color: #f1f5f9 !important;
            color: #0f172a !important;
        }

        #MainMenu, footer, header { visibility: hidden !important; }
        .block-container {
            padding-top: 1.5rem !important;
            padding-bottom: 4rem !important;
            max-width: 1200px !important;
        }

        /* Top HTML Bar / Navigation Header */
        .app-header {
            background: #ffffff;
            border-bottom: 1px solid #e2e8f0;
            padding: 16px 24px;
            border-radius: 16px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 24px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        }

        /* Hero Banner Container */
        .hero-banner-html {
            background: linear-gradient(135deg, #166534 0%, #15803d 50%, #22c55e 100%);
            border-radius: 24px;
            padding: 40px;
            color: #ffffff;
            box-shadow: 0 20px 25px -5px rgba(22, 101, 52, 0.2), 0 8px 10px -6px rgba(22, 101, 52, 0.2);
            margin-bottom: 32px;
            position: relative;
            overflow: hidden;
        }
        .hero-banner-html h1 {
            font-weight: 800;
            font-size: 2.5rem;
            margin: 0;
            letter-spacing: -0.025em;
            color: #ffffff !important;
        }
        .hero-banner-html p {
            color: #dcfce7;
            font-size: 1.1rem;
            margin-top: 8px;
            margin-bottom: 0;
            max-width: 600px;
        }

        /* HTML-Cards (Modern Dashboard View) */
        .custom-card {
            background-color: #ffffff;
            border-radius: 20px;
            border: 1px solid #e2e8f0;
            padding: 20px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
            transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
            margin-bottom: 20px;
        }
        .custom-card:hover {
            transform: translateY(-4px);
            box-shadow: 0 12px 20px -3px rgba(0, 0, 0, 0.08);
            border-color: #cbd5e1;
        }

        /* HTML Custom Badges */
        .badge {
            padding: 6px 14px;
            border-radius: 9999px;
            font-weight: 700;
            font-size: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            display: inline-block;
        }
        .badge-offen { background-color: #dcfce7; color: #15803d; }
        .badge-beansprucht { background-color: #fef3c7; color: #b45309; }
        .badge-kategorie { background-color: #f1f5f9; color: #475569; font-weight: 600; }

        /* HTML Uploader Info Tag */
        .uploader-info {
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 0.85rem;
            color: #64748b;
            margin-top: 12px;
        }

        /* Streamlit Input Override (Fügt HTML-Formular-Stil ein) */
        div[data-baseweb="input"] > div {
            border-radius: 12px !important;
            border: 1px solid #cbd5e1 !important;
            background-color: #ffffff !important;
        }
        div[data-baseweb="select"] > div {
            border-radius: 12px !important;
            border: 1px solid #cbd5e1 !important;
        }
        
        /* HTML AI Banner Badge */
        .ai-status-box {
            background-color: #eff6ff;
            border: 1px solid #bfdbfe;
            border-radius: 12px;
            padding: 12px 16px;
            color: #1e40af;
            font-size: 0.9rem;
            font-weight: 500;
            margin-bottom: 16px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
    </style>
""", unsafe_allow_html=True)

# =========================================================
# 2. SUPABASE & DATABASE BACKEND
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
# 3. DIRECT KI ANALYSER (AUTOMATISCH BEIM HOCHLADEN)
# =========================================================
def analyze_image_with_ai(image_file):
    """
    Diese Funktion analysiert ein Bild direkt beim Hochladen, ohne dass ein
    Button geklickt werden muss, und gibt ein strukturiertes JSON zurück.
    """
    gemini_key = st.secrets.get("GEMINI_API_KEY")
    if not gemini_key:
        # Fallback falls kein Key konfiguriert ist
        return {"titel": "Hochgeladenes Objekt", "kategorie": "Sonstiges", "vermuteter_ort": "Schulgelände"}

    try:
        genai.configure(api_key=gemini_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        img = Image.open(image_file)
        prompt = """
        Du bist die KI für ein Schul-Fundbüro. Analysiere das Bild und antworte AUSSCHLIESSLICH mit einem JSON-Objekt.
        
        Format:
        {
          "titel": "<Kurze deutsche Beschreibung, max 4 Worte, z.B. Roter Nike Rucksack>",
          "kategorie": "<Exakt eine Kategorie: Kleidung OR Elektronik OR Bücher & Hefte OR Sonstiges>",
          "vermuteter_ort": "<Vermuteter Schulort, z.B. Turnhalle, Mensa, Klassenzimmer, Pausenhof>"
        }
        """
        res = model.generate_content([prompt, img])
        clean_text = res.text.replace("```json", "").replace("```", "").strip()
        return json.loads(clean_text)
    except Exception as e:
        # Bei Fehlern wird ein sinnvoller Standardwert gesetzt
        return {"titel": "Erkanntes Fundstück", "kategorie": "Sonstiges", "vermuteter_ort": "Unbekannt"}

# =========================================================
# 4. SESSION STATE & NAVIGATION MANAGEMENT
# =========================================================
if "current_user" not in st.session_state:
    st.session_state.current_user = "Schüler / Finder"
if "is_admin" not in st.session_state:
    st.session_state.is_admin = False
if "tab" not in st.session_state:
    st.session_state.tab = "entdecken"
if "last_uploaded_file_name" not in st.session_state:
    st.session_state.last_uploaded_file_name = ""

# Formularspeicher für automatische KI-Befüllung
if "form_title" not in st.session_state:
    st.session_state.form_title = ""
if "form_category" not in st.session_state:
    st.session_state.form_category = "Sonstiges"
if "form_ort" not in st.session_state:
    st.session_state.form_ort = ""

# =========================================================
# 5. HTML BANNER & HEADER
# =========================================================
st.markdown("""
    <div class="hero-banner-html">
        <h1>🌱 FundSpot</h1>
        <p>Das digitale Schul-Fundbüro – Fundstücke automatisch per KI analysieren & blitzschnell wiederfinden.</p>
    </div>
""", unsafe_allow_html=True)

# Admin & Benutzerleiste
col_u1, col_u2 = st.columns([3, 1])
with col_u1:
    st.session_state.current_user = st.text_input("👤 Dein Name / Klasse:", value=st.session_state.current_user)
with col_u2:
    passcode = st.text_input("🔑 Admin-Schlüssel:", type="password", placeholder="Löschrechte freischalten")
    st.session_state.is_admin = (passcode == "admin123")

# Navigation Tabs im modernisierten HTML-Design
st.write("")
col_nav1, col_nav2 = st.columns(2)
with col_nav1:
    if st.button("🔍 Fundstücke durchsuchen", use_container_width=True, type="primary" if st.session_state.tab == "entdecken" else "secondary"):
        st.session_state.tab = "entdecken"
        st.rerun()
with col_nav2:
    if st.button("➕ Neues Fundstück eintragen", use_container_width=True, type="primary" if st.session_state.tab == "hochladen" else "secondary"):
        st.session_state.tab = "hochladen"
        st.rerun()

st.write("")

# =========================================================
# TAB 1: ENTDECKEN (HTML-KARTEN DURCHSUCHEN)
# =========================================================
if st.session_state.tab == "entdecken":
    
    col_s1, col_s2 = st.columns([3, 1])
    with col_s1:
        search_query = st.text_input("🔎 Suchbegriff eingeben...", placeholder="Z. B. Rucksack, Jacke, Mensa...")
    with col_s2:
        category_filter = st.selectbox("Kategorie Filter", ["Alle", "Kleidung", "Elektronik", "Bücher & Hefte", "Sonstiges"])

    items = load_items()
    
    # Filter-Logik
    filtered_items = []
    for item in items:
        matches_search = search_query.lower() in str(item.get("titel", "")).lower() or search_query.lower() in str(item.get("fundort", "")).lower()
        matches_cat = (category_filter == "Alle") or (item.get("kategorie") == category_filter)
        if matches_search and matches_cat:
            filtered_items.append(item)

    if not filtered_items:
        st.info("Keine passenden Fundstücke gefunden.")
    else:
        # Karten-Grid (3 Spalten Layout)
        cols = st.columns(3)
        for idx, item in enumerate(filtered_items):
            with cols[idx % 3]:
                with st.container(border=True):
                    # Bildverarbeitung (Base64 oder URL)
                    img_data = item.get("bild_base64", "")
                    if img_data and (img_data.startswith("data:image") or img_data.startswith("http")):
                        st.image(img_data, use_container_width=True)
                    else:
                        st.image("https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=600&auto=format&fit=crop&q=80", use_container_width=True)

                    # HTML-Inhalte der Karte
                    st.subheader(item.get("titel", "Fundstück"))
                    
                    status = item.get("status", "Offen")
                    if status == "Beansprucht":
                        st.markdown(f'<span class="badge badge-beansprucht">Markiert von {item.get("beansprucht_von", "Jemandem")}</span>', unsafe_allow_html=True)
                    else:
                        st.markdown('<span class="badge badge-offen">Offen</span>', unsafe_allow_html=True)
                    
                    st.markdown(f'<span class="badge badge-kategorie">{item.get("kategorie", "Sonstiges")}</span>', unsafe_allow_html=True)
                    
                    st.write(f"📍 **Ort:** {item.get('fundort', '-')} ({item.get('raum', '-')})")
                    st.write(f"🔑 **Abgabe bei:** {item.get('kontakt', 'Sekretariat')}")
                    
                    st.markdown(f'''
                        <div class="uploader-info">
                            👤 Hochgeladen von: <b>{item.get("uploader", "Anonym")}</b>
                        </div>
                    ''', unsafe_allow_html=True)
                    
                    st.write("")
                    
                    # Interaktive Buttons (Anfordern / Löschen)
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

                    # Löschen für Ersteller oder Admins
                    if item.get("uploader") == st.session_state.current_user or st.session_state.is_admin:
                        if st.button("🗑️ Löschen", key=f"del_{item['id']}", type="secondary", use_container_width=True):
                            delete_item(item["id"])
                            st.toast("Fundstück gelöscht.")
                            st.rerun()

# =========================================================
# TAB 2: HOCHLADEN (SOFORTIGE KI-ERKENNUNG)
# =========================================================
elif st.session_state.tab == "hochladen":
    st.subheader("📸 Neues Fundstück eintragen")
    
    with st.container(border=True):
        uploaded_file = st.file_uploader("1. Foto auswählen", type=["jpg", "jpeg", "png", "webp"])
        
        b64_image_str = ""
        
        # Sobald eine neue Datei ausgewählt wird, läuft die KI AUTOMATISCH ab
        if uploaded_file is not None:
            
            # Prüfen, ob das Bild neu hochgeladen wurde
            if uploaded_file.name != st.session_state.last_uploaded_file_name:
                st.session_state.last_uploaded_file_name = uploaded_file.name
                
                with st.spinner("🤖 KI analysiert das Bild automatisch..."):
                    ai_res = analyze_image_with_ai(uploaded_file)
                    
                    # Werte direkt in die Formular-Variablen schreiben
                    st.session_state.form_title = ai_res.get("titel", "")
                    st.session_state.form_category = ai_res.get("kategorie", "Sonstiges")
                    st.session_state.form_ort = ai_res.get("vermuteter_ort", "")
                    st.rerun()

            st.image(uploaded_file, caption="Ausgewähltes Foto", width=220)
            
            # Base64 Konvertierung
            bytes_data = uploaded_file.getvalue()
            b64_image_str = f"data:image/jpeg;base64,{base64.b64encode(bytes_data).decode()}"

            if st.session_state.form_title:
                st.markdown(f"""
                    <div class="ai-status-box">
                        ⚡ <b>KI-Erkennung aktiv:</b> Die Felder wurden automatisch ausgefüllt! Du kannst sie bei Bedarf anpassen.
                    </div>
                """, unsafe_allow_html=True)

        st.divider()
        st.write("### 2. Details überprüfen & Veröffentlichen")

        # Das Formular wird mit den Daten der automatischen KI-Erkennung vorausgefüllt
        with st.form("upload_form"):
            titel = st.text_input("Gegenstand / Bezeichnung *", value=st.session_state.form_title, placeholder="z. B. Grüner Nike Rucksack")
            
            col_k, col_o = st.columns(2)
            with col_k:
                kategorien = ["Sonstiges", "Kleidung", "Elektronik", "Bücher & Hefte"]
                cat_idx = kategorien.index(st.session_state.form_category) if st.session_state.form_category in kategorien else 0
                kategorie = st.selectbox("Kategorie", kategorien, index=cat_idx)
            with col_o:
                fundort = st.text_input("Fundort *", value=st.session_state.form_ort, placeholder="z. B. Turnhalle, Mensa")

            col_r, col_c = st.columns(2)
            with col_r:
                raum = st.text_input("Raum / Bereich", placeholder="z. B. EG oder Raum 102")
            with col_c:
                kontakt = st.text_input("Abgabeort / Kontakt", placeholder="z. B. Sekretariat / Hausmeister")

            submit_button = st.form_submit_button("🚀 Fundstück veröffentlichen", use_container_width=True, type="primary")

            if submit_button:
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
                    st.toast("🎉 Fundstück erfolgreich veröffentlicht!")
                    
                    # Formular zurücksetzen & zur Übersicht springen
                    st.session_state.form_title = ""
                    st.session_state.form_category = "Sonstiges"
                    st.session_state.form_ort = ""
                    st.session_state.last_uploaded_file_name = ""
                    st.session_state.tab = "entdecken"
                    st.rerun()
