import os
import base64
import datetime
import pandas as pd
import streamlit as st
from PIL import Image
from supabase import create_client, Client

# Hugging Face Transformers Integration
try:
    from transformers import BlipProcessor, BlipForConditionalGeneration
    HAS_HF = True
except ImportError:
    HAS_HF = False

# Übersetzungsdienst für Deutsch
try:
    from deep_translator import GoogleTranslator
    HAS_TRANSLATOR = True
except ImportError:
    HAS_TRANSLATOR = False

# =========================================================
# 1. STREAMLIT CONFIG & EXTENDED CSS (HOVER & CARDS)
# =========================================================
st.set_page_config(
    page_title="FundSpot – Schul-Fundbüro",
    page_icon="🎒",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

        html, body, [class*="css"], .stApp {
            font-family: 'Plus Jakarta Sans', sans-serif !important;
            background-color: #f1f5f9 !important;
            color: #0f172a !important;
        }

        #MainMenu, footer, header { visibility: hidden !important; }
        
        .block-container {
            padding-top: 2rem !important;
            padding-bottom: 4rem !important;
            max-width: 1200px !important;
        }

        /* Hero Banner */
        .hero-banner {
            background: linear-gradient(135deg, #0f766e 0%, #0d9488 50%, #059669 100%);
            border-radius: 24px;
            padding: 32px 40px;
            color: #ffffff;
            box-shadow: 0 12px 30px -10px rgba(13, 148, 136, 0.4);
            margin-bottom: 24px;
        }
        .hero-banner h1 { 
            font-weight: 800; 
            font-size: 2.4rem; 
            margin: 0; 
            color: #ffffff !important;
        }
        .hero-banner p { 
            color: #ccfbf1; 
            font-size: 1.05rem; 
            margin-top: 6px; 
            margin-bottom: 0;
        }

        /* Karten mit Hover-Animation & Zoom-Effekt */
        .fund-card-container {
            background: #ffffff;
            border-radius: 20px;
            border: 1px solid #e2e8f0;
            overflow: hidden;
            box-shadow: 0 4px 12px rgba(0,0,0,0.03);
            transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
            margin-bottom: 12px;
        }

        .fund-card-container:hover {
            transform: translateY(-6px) scale(1.01);
            box-shadow: 0 16px 28px -8px rgba(15, 23, 42, 0.12);
            border-color: #cbd5e1;
        }

        .fund-card-details {
            padding: 16px 18px;
            background: #ffffff;
        }

        .fund-card-title {
            font-size: 1.15rem;
            font-weight: 700;
            color: #0f172a;
            margin-top: 6px;
            margin-bottom: 10px;
        }

        /* Badges */
        .badge {
            display: inline-block;
            padding: 4px 10px;
            border-radius: 9999px;
            font-size: 0.75rem;
            font-weight: 700;
            margin-right: 4px;
            margin-bottom: 6px;
        }
        .badge-kategorie { background-color: #e0f2fe; color: #0369a1; }
        .badge-ort { background-color: #fef3c7; color: #b45309; }
        .badge-claimed { background-color: #fef2f2; color: #991b1b; }
        .badge-open { background-color: #f0fdf4; color: #166534; }

        /* Custom Input & Form Styling */
        div[data-baseweb="input"] > div { border-radius: 14px !important; }
        div[data-baseweb="select"] > div { border-radius: 14px !important; }
        .stButton>button { border-radius: 12px !important; font-weight: 600 !important; }

        .upload-section {
            background-color: #ffffff;
            border-radius: 20px;
            padding: 24px;
            border: 1px solid #e2e8f0;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.03);
        }
    </style>
""", unsafe_allow_html=True)

# =========================================================
# 2. SUPABASE / CSV BACKEND
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
            "kategorie": "Kleidung & Taschen",
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

def delete_item(item_id):
    items = load_items()
    items = [i for i in items if str(i["id"]) != str(item_id)]
    
    if supabase:
        try:
            supabase.table("fundstuecke").delete().eq("id", item_id).execute()
        except Exception:
            pass
    save_items(items)

def update_item_claim(item_id, claimer_info):
    items = load_items()
    for item in items:
        if str(item["id"]) == str(item_id):
            item["status"] = "Beansprucht"
            item["beansprucht_von"] = claimer_info
            break
            
    if supabase:
        try:
            supabase.table("fundstuecke").update({
                "status": "Beansprucht",
                "beansprucht_von": claimer_info
            }).eq("id", item_id).execute()
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
# 3. HUGGING FACE KI-MODELL & ÜBERSETZUNG (DEUTSCH)
# =========================================================
@st.cache_resource
def load_hf_model():
    """Lädt das vortrainierte BLIP-Modell von Hugging Face einmalig im Cache."""
    processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
    model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")
    return processor, model

def translate_to_german(text_en):
    """Übersetzt den englischen Text des Hugging Face Modells auf Deutsch."""
    if HAS_TRANSLATOR:
        try:
            translated = GoogleTranslator(source='en', target='de').translate(text_en)
            return translated
        except Exception:
            pass
    return text_en

def analyze_image_with_hf(image_file):
    if not HAS_HF:
        return None, "Die Pakete 'transformers' und 'torch' fehlen in deiner requirements.txt."

    try:
        processor, model = load_hf_model()
        
        raw_image = Image.open(image_file).convert('RGB')
        
        inputs = processor(raw_image, return_tensors="pt")
        out = model.generate(**inputs, max_new_tokens=50)
        description_en = processor.decode(out[0], skip_special_tokens=True)

        description_de = translate_to_german(description_en)

        desc_lower = description_en.lower()
        
        kategorie = "Sonstiges"
        if any(w in desc_lower for w in ["jacket", "coat", "shirt", "pants", "sweater", "hoodie", "shoe", "sneaker", "hat", "cap", "glove", "scarf", "clothes", "bag", "backpack"]):
            kategorie = "Kleidung & Taschen"
        elif any(w in desc_lower for w in ["phone", "laptop", "tablet", "headphone", "earphone", "calculator", "cable", "charger", "electronic"]):
            kategorie = "Elektronik"
        elif any(w in desc_lower for w in ["book", "notebook", "paper", "binder", "pencil", "pen", "case"]):
            kategorie = "Bücher & Schreibwaren"

        return {
            "beschreibung": description_de,
            "kategorie": kategorie
        }, None

    except Exception as e:
        return None, f"Fehler bei der Hugging Face Modell-Analyse: {str(e)}"

# =========================================================
# 4. SESSION STATE & OWNER / ADMIN RECHTE
# =========================================================
if "current_user" not in st.session_state:
    st.session_state.current_user = "Schüler / Finder"
if "tab" not in st.session_state:
    st.session_state.tab = "entdecken"
if "is_owner" not in st.session_state:
    st.session_state.is_owner = False

if "f_titel" not in st.session_state:
    st.session_state.f_titel = ""
if "f_kategorie" not in st.session_state:
    st.session_state.f_kategorie = "Sonstiges"
if "f_ort" not in st.session_state:
    st.session_state.f_ort = ""

OWNER_PASSWORD = st.secrets.get("OWNER_PASSWORD", "admin123")

# =========================================================
# 5. OBERFLÄCHE
# =========================================================

# Hero Banner
st.markdown("""
    <div class="hero-banner">
        <div style="display: flex; align-items: center; justify-content: space-between;">
            <div>
                <h1>🎒 FundSpot</h1>
                <p>Das digitale Schul-Fundbüro mit KI-Bilderkennung</p>
            </div>
            <div style="font-size: 3.5rem; opacity: 0.9;">🔍</div>
        </div>
    </div>
""", unsafe_allow_html=True)

# User-Eingabe & Owner Mode Toggle
top_col1, top_col2 = st.columns([2, 1])
with top_col1:
    st.session_state.current_user = st.text_input("👤 Dein Name / Klasse:", value=st.session_state.current_user)
with top_col2:
    pwd_input = st.text_input("🔑 Owner / Admin Passwort:", type="password", placeholder="admin123")
    if pwd_input == OWNER_PASSWORD:
        st.session_state.is_owner = True
        st.caption("✅ Owner-Rechte aktiv (Löschen erlaubt)")
    else:
        st.session_state.is_owner = False
        if pwd_input:
            st.caption("❌ Falsches Passwort")

st.write("")
nav_c1, nav_c2 = st.columns(2)
with nav_c1:
    if st.button("🔍 Fundstücke durchsuchen", use_container_width=True, type="primary" if st.session_state.tab == "entdecken" else "secondary"):
        st.session_state.tab = "entdecken"
        st.rerun()
with nav_c2:
    if st.button("➕ Fundstück hochladen (Hugging Face KI)", use_container_width=True, type="primary" if st.session_state.tab == "hochladen" else "secondary"):
        st.session_state.tab = "hochladen"
        st.rerun()

st.write("")

# TAB 1: ENTDECKEN (MIT HOVER, DETAIL-VIEW & CLAIM-FUNKTION)
if st.session_state.tab == "entdecken":
    items = load_items()
    cols = st.columns(3)
    
    for idx, item in enumerate(items):
        with cols[idx % 3]:
            img_src = item.get("bild_base64") or "https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=600&auto=format&fit=crop&q=80"
            is_claimed = item.get("status") == "Beansprucht"
            status_badge = '<span class="badge badge-claimed">⚠️ Beansprucht</span>' if is_claimed else '<span class="badge badge-open">✅ Offen</span>'
            
            # HTML Card Rendering mit Hover
            st.markdown(f"""
                <div class="fund-card-container">
                    <div style="height: 200px; overflow: hidden; background: #e2e8f0;">
                        <img src="{img_src}" style="width: 100%; height: 100%; object-fit: cover;">
                    </div>
                    <div class="fund-card-details">
                        {status_badge}
                        <span class="badge badge-kategorie">🏷️ {item.get('kategorie')}</span>
                        <span class="badge badge-ort">📍 {item.get('fundort')}</span>
                        <div class="fund-card-title">{item.get('titel', 'Unbenannt')}</div>
                        <div style="font-size: 0.85rem; color: #64748b; line-height: 1.5;">
                            <b>Raum:</b> {item.get('raum')}<br>
                            <b>Finder:</b> {item.get('uploader')}<br>
                            <b>Datum:</b> {item.get('datum')}
                        </div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
            # Interaktions-Buttons
            btn_col1, btn_col2 = st.columns(2)
            
            # Button 1: Details / Bild vergrößern & Eigentum beanspruchen
            with btn_col1:
                with st.popover("🔎 Details / Eigentum"):
                    st.image(img_src, caption=item.get("titel"), use_container_width=True)
                    st.markdown(f"### {item.get('titel')}")
                    st.write(f"📍 **Fundort:** {item.get('fundort')} (Raum: {item.get('raum')})")
                    st.write(f"🏢 **Abholen bei:** {item.get('kontakt')}")
                    st.write(f"👤 **Eingetragen von:** {item.get('uploader')}")
                    st.write(f"📅 **Datum:** {item.get('datum')}")
                    
                    if is_claimed:
                        st.warning(f"Dieses Fundstück wurde bereits beansprucht von: **{item.get('beansprucht_von')}**")
                    else:
                        st.divider()
                        st.markdown("#### 🙋 Das gehört mir!")
                        claimer_name = st.text_input("Dein Name / Klasse zum Abholen:", key=f"claimer_{item['id']}")
                        if st.button("Gegenstand als 'Meins' markieren", key=f"claim_btn_{item['id']}", type="primary"):
                            if claimer_name.strip():
                                update_item_claim(item["id"], claimer_name)
                                st.success("Vielen Dank! Der Gegenstand wurde für dich reserviert.")
                                st.rerun()
                            else:
                                st.error("Bitte gib deinen Namen ein.")

            # Button 2: Löschen (Nur für den Owner sichtbar)
            with btn_col2:
                if st.session_state.is_owner:
                    if st.button("🗑️ Löschen", key=f"del_{item['id']}", use_container_width=True):
                        delete_item(item["id"])
                        st.toast("Eintrag gelöscht!")
                        st.rerun()

# TAB 2: HOCHLADEN
elif st.session_state.tab == "hochladen":
    st.markdown('<div class="upload-section">', unsafe_allow_html=True)
    st.subheader("📸 Neues Fundstück eintragen")
    
    uploaded_file = st.file_uploader("1. Wähle ein Foto aus", type=["jpg", "jpeg", "png", "webp"])
    
    b64_img = ""
    if uploaded_file:
        st.image(uploaded_file, caption="Vorschau", width=220)
        b64_img = f"data:image/jpeg;base64,{base64.b64encode(uploaded_file.getvalue()).decode()}"
        
        if st.button("🤗 Foto mit Hugging Face KI analysieren (auf Deutsch)", type="primary", use_container_width=True):
            with st.spinner("Hugging Face KI analysiert das Bild und übersetzt die Auswertung..."):
                ai_data, error_msg = analyze_image_with_hf(uploaded_file)
                
                if error_msg:
                    st.error(f"❌ {error_msg}")
                elif ai_data:
                    st.session_state.f_titel = ai_data.get("beschreibung", "").capitalize()
                    st.session_state.f_kategorie = ai_data.get("kategorie", "Sonstiges")
                    st.success("✅ Das Bild wurde erfolgreich analysiert und ins Deutsche übersetzt!")
                    st.rerun()

    st.markdown('<hr style="border: 0; height: 1px; background: #e2e8f0; margin: 25px 0;">', unsafe_allow_html=True)
    st.write("### 2. Formular überprüfen & Veröffentlichen")

    titel_val = st.text_input("Gegenstand / Beschreibung *", value=st.session_state.f_titel)
    
    kategorien = ["Sonstiges", "Kleidung & Taschen", "Elektronik", "Bücher & Schreibwaren"]
    kat_idx = kategorien.index(st.session_state.f_kategorie) if st.session_state.f_kategorie in kategorien else 0
    kat_val = st.selectbox("Kategorie", kategorien, index=kat_idx)
    
    ort_val = st.text_input("Fundort *", value=st.session_state.f_ort)
    raum_val = st.text_input("Raum / Bereich", placeholder="z. B. Sporthalle, Mensa, EG")
    kontakt_val = st.text_input("Abgabeort / Kontakt", value="Sekretariat")

    if st.button("🚀 Fundstück veröffentlichen", type="primary", use_container_width=True):
        if not titel_val or not ort_val:
            st.error("Bitte gib mindestens einen Titel/Gegenstand und den Ort ein.")
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
            st.toast("🎉 Fundstück erfolgreich eingetragen!")
            st.session_state.f_titel = ""
            st.session_state.f_ort = ""
            st.session_state.tab = "entdecken"
            st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)
