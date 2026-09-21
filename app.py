import os
import json
import base64
import datetime
import pandas as pd
import streamlit as st
from PIL import Image
from supabase import create_client, Client

# Optional: Google Gemini KI für automatische Bildeinschätzung
try:
    import google.generativeai as genai
    HAS_GEMINI = True
except ImportError:
    HAS_GEMINI = False

# =========================================================
# 1. STREAMLIT CONFIG & DESIGN (HTML-Look & Feel)
# =========================================================
st.set_page_config(
    page_title="FundSpot – Schul-Fundbüro",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS für den modernen HTML/App-Look
st.markdown("""
    <style>
        #MainMenu, footer, header {visibility: hidden;}
        .block-container {padding-top: 1.5rem !important; padding-bottom: 3rem !important; max-width: 1100px;}
        
        /* Globale Stile */
        body { background-color: #f4f7f5; }
        
        /* Banner Header */
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

        /* Card Styling */
        div[data-testid="stVerticalBlockBorderWrapper"] {
            background-color: white !important;
            border-radius: 18px !important;
            border: 1px solid #e5e7eb !important;
            box-shadow: 0 4px 16px rgba(0,0,0,0.04) !important;
            padding: 16px !important;
        }
        
        /* Badges */
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
        
        .user-tag {
            background-color: #f1f5f9; color: #475569;
            padding: 4px 10px; border-radius: 8px;
            font-weight: 600; font-size: 0.8rem;
        }
        
        /* Buttons Schön gestalten */
        .stButton>button {
            border-radius: 12px !important;
            font-weight: 700 !important;
            transition: all 0.2s !important;
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
            if claimer:
                item["beansprucht_von"] = claimer
            break
            
    if supabase:
        try:
            supabase.table("fundstuecke").update({
                "status": status,
                "beansprucht_von": claimer
            }).eq("id", item_id).execute()
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
# 3. KI-ANALSYE (GEMINI / VISION)
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
            Gib ein einfaches JSON-Objekt zurück mit folgenden Keys:
            - titel: Kurzer prägnanter deutscher Name (z.B. "Roter Nike Rucksack")
            - kategorie: Eine der folgenden ("Kleidung", "Elektronik", "Bücher & Hefte", "Sonstiges")
            """
            res = model.generate_content([prompt, img])
            text = res.text.replace("```json", "").replace("```", "").strip()
            return json.loads(text)
        except Exception:
            pass
    
    # Fallback, falls kein Key vorhanden ist
    return {"titel": "Neues Fundstück", "kategorie": "Sonstiges"}

# =========================================================
# 4. SESSION STATE & NAVIGATION
# =========================================================
if "current_user" not in st.session_state:
    st.session_state.current_user = "Johann (8b)"
if "is_admin" not in st.session_state:
    st.session_state.is_admin = False
if "tab" not in st.session_state:
    st.session_state.tab = "entdecken"

# =========================================================
# 5. HEADER & NUTZER-LEISTE
# =========================================================
st.markdown("""
    <div class="hero-banner">
        <h1>🌱 FundSpot</h1>
        <p>Das digitale Schul-Fundbüro – Fundstücke eintragen, KI-Erkennung nutzen & Wiederfinden</p>
    </div>
""", unsafe_allow_html=True)

col_u1, col_u2, col_u3 = st.columns([2, 2, 1])
with col_u1:
    st.session_state.current_user = st.text_input("👤 Dein Name / Klasse:", value=st.session_state.current_user)
with col_u2:
    passcode = st.text_input("🔑 Admin-Passcode:", type="password", placeholder="Optional für Admin-Rechte")
    st.session_state.is_admin = (passcode == "admin123")
with col_u3:
    st.write("")
    st.write("")
    if st.session_state.is_admin:
        st.success("Admin aktiv")

st.divider()

# Tab Navigation Buttons
col_b1, col_b2 = st.columns(2)
with col_b1:
    if st.button("🔍 Entdecken & Suchen", use_container_width=True, type="primary" if st.session_state.tab == "entdecken" else "secondary"):
        st.session_state.tab = "entdecken"
        st.rerun()
with col_b2:
    if st.button("➕ Neues Fundstück hochladen", use_container_width=True, type="primary" if st.session_state.tab == "hochladen" else "secondary"):
        st.session_state.tab = "hochladen"
        st.rerun()

st.write("")

# =========================================================
# TAB 1: ENTDECKEN & GEGENSTÄNDE (MIT BEANSPRUCHEN & LÖSCHEN)
# =========================================================
if st.session_state.tab == "entdecken":
    
    # Such- und Filterleiste
    c1, c2 = st.columns([3, 1])
    with c1:
        search = st.text_input("🔎 Suche nach Gegenstand, Ort...", placeholder="z. B. Jacke, Mensa, Nike")
    with c2:
        category = st.selectbox("Kategorie Filter", ["Alle", "Kleidung", "Elektronik", "Bücher & Hefte", "Sonstiges"])

    all_items = load_items()
    
    # Filtern
    filtered = []
    for item in all_items:
        match_search = search.lower() in str(item.get("titel", "")).lower() or search.lower() in str(item.get("fundort", "")).lower()
        match_cat = (category == "Alle") or (item.get("kategorie") == category)
        if match_search and match_cat:
            filtered.append(item)

    if not filtered:
        st.info("Keine Fundstücke gefunden.")
    else:
        # Karten im Grid anzeigen (3 Spalten)
        cols = st.columns(3)
        for idx, item in enumerate(filtered):
            with cols[idx % 3]:
                with st.container(border=True):
                    # Bild anzeigen
                    img_src = item.get("bild_base64", "")
                    if img_src and img_src.startswith("data:image"):
                        st.image(img_src, use_container_width=True)
                    elif img_src and img_src.startswith("http"):
                        st.image(img_src, use_container_width=True)
                    else:
                        st.image("https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=600&auto=format&fit=crop&q=80", use_container_width=True)

                    # Titel & Meta
                    st.subheader(item.get("titel", "Unbenannt"))
                    
                    # Status Badge
                    status = item.get("status", "Offen")
                    if status == "Beansprucht":
                        st.markdown(f'<span class="badge-beansprucht">Markiert von {item.get("beansprucht_von", "Jemandem")}</span>', unsafe_allow_html=True)
                    else:
                        st.markdown('<span class="badge-offen">Offen</span>', unsafe_allow_html=True)
                        
                    st.write(f"📍 **Ort:** {item.get('fundort', '-')} ({item.get('raum', '-')})")
                    st.write(f"🔑 **Abgabe bei:** {item.get('kontakt', 'Sekretariat')}")
                    st.markdown(f'<span class="user-tag">👤 Hochgeladen von: {item.get("uploader", "Anonym")}</span>', unsafe_allow_html=True)
                    
                    st.write("")
                    
                    # --- ACTION BUTTON 1: "Das gehört mir!" ---
                    if status == "Offen":
                        if st.button(f"🙋‍♂️ Das gehört mir!", key=f"claim_{item['id']}", use_container_width=True):
                            update_item_status(item["id"], "Beansprucht", st.session_state.current_user)
                            st.toast("✅ Super! Es wurde als beansprucht markiert.")
                            st.rerun()
                    elif status == "Beansprucht":
                        if item.get("beansprucht_von") == st.session_state.current_user or st.session_state.is_admin:
                            if st.button("🔄 Wieder als 'Offen' freigeben", key=f"unclaim_{item['id']}", use_container_width=True):
                                update_item_status(item["id"], "Offen", "")
                                st.rerun()

                    # --- ACTION BUTTON 2: LÖSCHEN (Ersteller ODER Admin) ---
                    is_owner = (item.get("uploader") == st.session_state.current_user)
                    if is_owner or st.session_state.is_admin:
                        if st.button(f"🗑️ Löschen", key=f"del_{item['id']}", type="secondary", use_container_width=True):
                            delete_item(item["id"])
                            st.toast("Eintrag erfolgreich gelöscht!")
                            st.rerun()

# =========================================================
# TAB 2: HOCHLADEN (MIT KI-ERKENNUNG)
# =========================================================
elif st.session_state.tab == "hochladen":
    st.subheader("📸 Neues Fundstück mit KI-Erkennung eintragen")
    
    with st.container(border=True):
        uploaded_file = st.file_uploader("1. Foto des Fundstücks auswählen", type=["jpg", "jpeg", "png", "webp"])
        
        ai_titel = ""
        ai_kat = "Sonstiges"
        b64_image_str = ""
        
        if uploaded_file is not None:
            # Bild anzeigen
            st.image(uploaded_file, caption="Vorschau", width=300)
            
            # Base64 String erstellen
            bytes_data = uploaded_file.getvalue()
            b64_image_str = f"data:image/jpeg;base64,{base64.b64encode(bytes_data).decode()}"
            
            # KI-Analyse durchführen
            with st.spinner("🤖 KI analysiert das Foto..."):
                ai_res = analyze_image_with_ai(uploaded_file)
                ai_titel = ai_res.get("titel", "")
                ai_kat = ai_res.get("kategorie", "Sonstiges")
                st.success("KI hat das Bild erkannt! Du kannst die Daten unten anpassen.")

        # Formular mit KI-Vorschlägen
        with st.form("add_form"):
            titel = st.text_input("Gegenstand / Bezeichnung *", value=ai_titel, placeholder="z. B. Grüner Nike Rucksack")
            
            c_kat, c_ort = st.columns(2)
            with c_kat:
                kategorien = ["Sonstiges", "Kleidung", "Elektronik", "Bücher & Hefte"]
                kat_index = kategorien.index(ai_kat) if ai_kat in kategorien else 0
                kategorie = st.selectbox("Kategorie", kategorien, index=kat_index)
            with c_ort:
                fundort = st.text_input("Fundort *", placeholder="z. B. Mensa, Pausenhof")

            c_raum, c_kontakt = st.columns(2)
            with c_raum:
                raum = st.text_input("Raum / Bereich", placeholder="z. B. EG oder Raum 102")
            with c_kontakt:
                kontakt = st.text_input("Wo abgegeben? / Kontakt", placeholder="z. B. Sekretariat, Hausmeister")

            submit = st.form_submit_button("🚀 Fundstück veröffentlichen", use_container_width=True, type="primary")

            if submit:
                if not titel or not fundort:
                    st.error("Bitte fülle mindestens den Titel und den Fundort aus.")
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
                    st.session_state.tab = "entdecken"
                    st.rerun()
