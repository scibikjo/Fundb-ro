import os
import io
import datetime
import base64
import pandas as pd
import numpy as np
from PIL import Image
import streamlit as st
import tensorflow as tf
from supabase import create_client, Client

# ---------------------------------------------------------
# 1. PAGE CONFIG & DESIGN INSPIRIERUNG VON DESIGN.JPG
# ---------------------------------------------------------
st.set_page_config(
    page_title="Schul-Fundbüro", 
    page_icon="🌱", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# UI Styling nach Vorlage (Grüner Hintergrund, abgerundete weiße & grüne Karten)
st.markdown("""
<style>
    /* Haupt-Hintergrund */
    .stApp {
        background-color: #f2f5f3 !important;
        color: #1e293b !important;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }

    /* Top-Bar Navigation / Header */
    .app-header {
        background: #ffffff;
        padding: 16px 24px;
        border-radius: 24px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.03);
        margin-bottom: 24px;
        border: 1px solid #e5e7eb;
    }
    
    .app-title {
        font-size: 1.6rem;
        font-weight: 800;
        color: #0f291e;
        margin: 0;
    }

    /* Hero Banner (Grün wie in der Vorlage) */
    .green-card {
        background: linear-gradient(135deg, #2e7d32 0%, #1b5e20 100%);
        border-radius: 28px;
        padding: 28px;
        color: #ffffff !important;
        box-shadow: 0 12px 28px rgba(46, 125, 50, 0.2);
        margin-bottom: 24px;
    }
    .green-card h2 {
        color: #ffffff !important;
        font-size: 1.8rem !important;
        margin-top: 0 !important;
    }
    .green-card p {
        color: #e8f5e9 !important;
        font-size: 1rem;
        margin-bottom: 0;
    }

    /* Produkt-Karten Design */
    div[data-testid="stVerticalBlock"] > div[style*="border"] {
        background-color: #ffffff !important;
        border-radius: 24px !important;
        border: 1px solid #e5e7eb !important;
        box-shadow: 0 6px 18px rgba(0, 0, 0, 0.03) !important;
        transition: all 0.25s ease !important;
        padding: 18px !important;
    }
    div[data-testid="stVerticalBlock"] > div[style*="border"]:hover {
        transform: translateY(-5px);
        box-shadow: 0 14px 28px rgba(46, 125, 50, 0.12) !important;
        border-color: #a5d6a7 !important;
    }

    /* Badges & Uploader Chips */
    .badge-offen {
        background-color: #e8f5e9;
        color: #1b5e20;
        padding: 5px 12px;
        border-radius: 16px;
        font-size: 0.78rem;
        font-weight: 700;
        display: inline-block;
    }
    .badge-abgeholt {
        background-color: #ffebee;
        color: #c62828;
        padding: 5px 12px;
        border-radius: 16px;
        font-size: 0.78rem;
        font-weight: 700;
        display: inline-block;
    }
    .uploader-chip {
        background-color: #f1f5f9;
        color: #475569;
        padding: 4px 10px;
        border-radius: 12px;
        font-size: 0.8rem;
        font-weight: 600;
        display: inline-block;
        margin-top: 6px;
    }

    /* Tabs Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 12px;
        margin-bottom: 20px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 20px !important;
        padding: 10px 24px !important;
        background-color: #ffffff !important;
        border: 1px solid #e5e7eb !important;
        color: #334155 !important;
        font-weight: 600;
    }
    .stTabs [aria-selected="true"] {
        background-color: #1b5e20 !important;
        color: #ffffff !important;
        border-color: #1b5e20 !important;
        box-shadow: 0 4px 12px rgba(27, 94, 32, 0.25);
    }

    /* Input-Felder & Knöpfe */
    .stTextInput input, .stSelectbox select {
        border-radius: 14px !important;
        border: 1px solid #cbd5e1 !important;
    }
    .stButton > button {
        border-radius: 16px !important;
        font-weight: 600 !important;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 2. SUPABASE DATENBANK
# ---------------------------------------------------------
@st.cache_resource
def init_supabase():
    url = st.secrets.get("SUPABASE_URL")
    key = st.secrets.get("SUPABASE_KEY")
    if url and key:
        return create_client(url, key)
    return None

supabase: Client = init_supabase()

def load_data():
    if supabase:
        response = supabase.table("fundstuecke").select("*").execute()
        return pd.DataFrame(response.data)
    else:
        DB_FILE = "fundbuero_db.csv"
        if os.path.exists(DB_FILE):
            df = pd.read_csv(DB_FILE)
            if "uploader" not in df.columns:
                df["uploader"] = "Anonym"
            return df
        return pd.DataFrame(columns=[
            "id", "titel", "kategorie", "fundort", "raum", 
            "datum", "status", "kontakt", "uploader", "bild_base64"
        ])

# ---------------------------------------------------------
# 3. KI-MODELL & LABELS
# ---------------------------------------------------------
def load_labels():
    labels_path = "labels.txt"
    if os.path.exists(labels_path):
        with open(labels_path, "r", encoding="utf-8") as f:
            labels = [line.strip().split(" ", 1)[-1] for line in f.readlines() if line.strip()]
            if labels:
                return labels
    return ["Kleidung", "Elektronik", "Bücher & Hefte", "Sonstiges"]

CATEGORIES = load_labels()

class FixedDepthwiseConv2D(tf.keras.layers.DepthwiseConv2D):
    def __init__(self, *args, **kwargs):
        kwargs.pop('groups', None)
        super().__init__(*args, **kwargs)

@st.cache_resource
def load_keras_model():
    model_path = "keras_model.h5"
    if os.path.exists(model_path):
        try:
            custom_objects = {'DepthwiseConv2D': FixedDepthwiseConv2D}
            model = tf.keras.models.load_model(model_path, custom_objects=custom_objects, compile=False)
            return model, None
        except Exception as e:
            return None, f"Fehler: {e}"
    else:
        return None, "Keras-Modell fehlt"

def predict_category(image_bytes, model):
    if model is None:
        return None, 0.0
    
    img = Image.open(io.BytesIO(image_bytes)).convert('RGB')
    img = img.resize((224, 224))
    
    img_array = np.array(img, dtype=np.float32)
    img_array = np.expand_dims(img_array, axis=0)
    img_array = (img_array / 127.5) - 1.0
    
    try:
        predictions = model(img_array, training=False).numpy()
    except Exception:
        predictions = model.predict(img_array)
        
    predicted_class_index = np.argmax(predictions[0])
    confidence = float(predictions[0][predicted_class_index])
    
    if predicted_class_index < len(CATEGORIES):
        return CATEGORIES[predicted_class_index], confidence
    return CATEGORIES[0], confidence

# ---------------------------------------------------------
# 4. INITIALISIERUNG
# ---------------------------------------------------------
if "upload_key" not in st.session_state:
    st.session_state.upload_key = 0
if "success_msg" not in st.session_state:
    st.session_state.success_msg = None

df_items = load_data()
model, model_error = load_keras_model()

# --- HEADER / APP BAR ---
st.markdown("""
<div class="app-header">
    <div class="app-title">🌱 Schul-Fundbüro App</div>
</div>
""", unsafe_allow_html=True)

# --- SIDEBAR (ADMIN / ACCOUNT) ---
with st.sidebar:
    st.header("⚙️ Einstellungen")
    user_account_name = st.text_input("Dein Name / Account", value="Schüler / Lehrer")
    admin_pw_input = st.text_input("Admin-Passwort", type="password")
    ADMIN_PW = st.secrets.get("ADMIN_PASSWORD", "admin123")
    is_admin = (admin_pw_input == ADMIN_PW)
    
    if is_admin:
        st.success("🔓 Admin-Rechte aktiv")
    st.divider()
    st.caption("⚡ Cloud-DB: " + ("🟢 Online" if supabase else "🔴 Lokaler Modus"))

# --- DIALOG POPUP FÜR DIREKTE DETAILANSICHT ---
@st.dialog("🔎 Details zum Fundstück")
def show_detail_dialog(item_data):
    col1, col2 = st.columns([1, 1])
    with col1:
        if pd.notna(item_data["bild_base64"]) and str(item_data["bild_base64"]).startswith("data:image"):
            st.image(item_data["bild_base64"], use_container_width=True)
        else:
            st.info("Kein Bild vorhanden.")
            
    with col2:
        st.subheader(item_data["titel"])
        status_class = "badge-offen" if item_data["status"] == "Offen" else "badge-abgeholt"
        st.markdown(f'<span class="{status_class}">{item_data["status"]}</span>', unsafe_allow_html=True)
        
        uploader_name = item_data.get("uploader", "Anonym")
        st.markdown(f'<div class="uploader-chip">👤 Hochgeladen von: {uploader_name}</div>', unsafe_allow_html=True)
        st.write("")
        
        st.write(f"**🏷️ Kategorie:** {item_data['kategorie']}")
        st.write(f"**📍 Fundort:** {item_data['fundort']} (Raum: {item_data['raum']})")
        st.write(f"**📅 Datum:** {item_data['datum']}")
        st.write(f"**📦 Abgabeort/Kontakt:** {item_data['kontakt']}")
    
    st.divider()
    
    if item_data["status"] == "Offen":
        if st.button("🙋‍♂️ Das gehört mir! (Als abgeholt markieren)", use_container_width=True, type="primary"):
            if supabase:
                supabase.table("fundstuecke").update({"status": "Abgeholt"}).eq("id", int(item_data["id"])).execute()
            else:
                df_items.loc[df_items["id"] == item_data["id"], "status"] = "Abgeholt"
                df_items.to_csv("fundbuero_db.csv", index=False)
            st.success("Als 'Abgeholt' markiert!")
            st.rerun()

    if is_admin:
        if st.button("🗑️ Eintrag löschen", use_container_width=True):
            if supabase:
                supabase.table("fundstuecke").delete().eq("id", int(item_data["id"])).execute()
            else:
                df_items_new = df_items[df_items["id"] != item_data["id"]]
                df_items_new.to_csv("fundbuero_db.csv", index=False)
            st.success("Gelöscht!")
            st.rerun()

# ---------------------------------------------------------
# 5. HAUPTNAVIGATION
# ---------------------------------------------------------
tab_home, tab_add = st.tabs(["🏠 Entdecken", "➕ Kleidungsstück hochladen"])

# --- TAB 1: ENTDECKEN / ÜBERSICHT ---
with tab_home:
    st.markdown("""
    <div class="green-card">
        <h2>Verlorene Sachen suchen & finden</h2>
        <p>Wähle eine Kategorie oder tippe in die Suche, um gefundene Gegenstände zu durchsuchen.</p>
    </div>
    """, unsafe_allow_html=True)

    if st.session_state.success_msg:
        st.success(st.session_state.success_msg)
        st.session_state.success_msg = None

    # Such- und Filterleiste
    c1, c2, c3 = st.columns([2, 1, 1])
    with c1:
        search_q = st.text_input("🔍 Suchbegriff", placeholder="z. B. Jacke, Pullover...")
    with c2:
        filter_c = st.selectbox("Kategorie", ["Alle"] + CATEGORIES)
    with c3:
        filter_s = st.selectbox("Status", ["Alle", "Offen", "Abgeholt"])

    filtered_df = df_items.copy()
    if not filtered_df.empty:
        if search_q:
            filtered_df = filtered_df[
                filtered_df["titel"].str.contains(search_q, case=False, na=False) |
                filtered_df["fundort"].str.contains(search_q, case=False, na=False)
            ]
        if filter_c != "Alle":
            filtered_df = filtered_df[filtered_df["kategorie"] == filter_c]
        if filter_s != "Alle":
            filtered_df = filtered_df[filtered_df["status"] == filter_s]

    if filtered_df.empty:
        st.info("Keine passenden Fundstücke gefunden.")
    else:
        cols = st.columns(3)
        for idx, row in filtered_df.reset_index(drop=True).iterrows():
            with cols[idx % 3]:
                with st.container(border=True):
                    if pd.notna(row["bild_base64"]) and str(row["bild_base64"]).startswith("data:image"):
                        st.image(row["bild_base64"], use_container_width=True)
                    
                    st.subheader(row["titel"])
                    
                    badge_class = "badge-offen" if row["status"] == "Offen" else "badge-abgeholt"
                    st.markdown(f'<span class="{badge_class}">{row["status"]}</span>', unsafe_allow_html=True)
                    
                    uploader_name = row.get("uploader", "Anonym")
                    st.markdown(f'<br><span class="uploader-chip">👤 von {uploader_name}</span>', unsafe_allow_html=True)
                    st.write("")
                    
                    st.caption(f"📍 {row['fundort']} (Raum {row['raum']})")
                    
                    if st.button("🔎 Details öffnen", key=f"btn_{row['id']}", use_container_width=True):
                        show_detail_dialog(row)

# --- TAB 2: GEGENSTAND/KLEIDUNG HOCHLADEN ---
with tab_add:
    st.subheader("Neues Fundstück im System eintragen")
    
    uploaded_file = st.file_uploader(
        "Foto vom Kleidungsstück hochladen", 
        type=["jpg", "jpeg", "png"], 
        key=f"uploader_{st.session_state.upload_key}"
    )
    
    auto_cat = CATEGORIES[0]
    img_data_url = ""
    
    if uploaded_file is not None:
        file_bytes = uploaded_file.getvalue()
        pred_cat, conf = predict_category(file_bytes, model)
        if pred_cat:
            auto_cat = pred_cat
            st.info(f"🤖 KI erkennt automatisch: **{auto_cat}** ({conf*100:.1f}% Sicher)")
        
        st.image(file_bytes, caption="Vorschau", width=180)
        base64_encoded = base64.b64encode(file_bytes).decode('utf-8')
        img_data_url = f"data:image/jpeg;base64,{base64_encoded}"

    with st.form("add_form", clear_on_submit=True):
        titel = st.text_input("Bezeichnung / Kleidungsstück *", placeholder="z. B. Blaue Nike Jacke")
        
        col_form1, col_form2 = st.columns(2)
        with col_form1:
            uploader_input = st.text_input("Dein Name / Klasse (Account) *", value=user_account_name)
            cat_idx = CATEGORIES.index(auto_cat) if auto_cat in CATEGORIES else 0
            kategorie = st.selectbox("Kategorie", CATEGORIES, index=cat_idx)
        with col_form2:
            fundort = st.text_input("Fundort *", placeholder="z. B. Turnhalle")
            raum = st.text_input("Raum / Platz", placeholder="z. B. Umkleide 2")
            
        kontakt = st.text_input("Abgabeort / Kontakt", placeholder="z. B. Hausmeister / Seki")
        
        submitted = st.form_submit_button("💾 Fundstück jetzt veröffentlichen", type="primary", use_container_width=True)
        
        if submitted:
            if not titel or not fundort or not uploader_input:
                st.error("Bitte Titel, Fundort und deinen Namen eingeben!")
            else:
                today_str = datetime.date.today().strftime("%Y-%m-%d")
                new_row = {
                    "titel": titel,
                    "kategorie": kategorie,
                    "fundort": fundort,
                    "raum": raum,
                    "datum": today_str,
                    "status": "Offen",
                    "kontakt": kontakt,
                    "uploader": uploader_input,
                    "bild_base64": img_data_url
                }
                
                if supabase:
                    supabase.table("fundstuecke").insert(new_row).execute()
                else:
                    new_row["id"] = len(df_items) + 1
                    df_items = pd.concat([df_items, pd.DataFrame([new_row])], ignore_index=True)
                    df_items.to_csv("fundbuero_db.csv", index=False)
                
                st.session_state.upload_key += 1
                st.session_state.success_msg = f"🎉 Erfolgreich hinzugefügt! '{titel}' ist jetzt online."
                st.rerun()import os
import io
import datetime
import base64
import pandas as pd
import numpy as np
from PIL import Image
import streamlit as st
import tensorflow as tf
from supabase import create_client, Client

# ---------------------------------------------------------
# 1. PAGE CONFIG & MODERNES GREEN/LIGHT DESIGN (WIE BILD)
# ---------------------------------------------------------
st.set_page_config(
    page_title="Schul-Fundbüro", 
    page_icon="🌱", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Frisches Grün-Weiß Styling für beste Lesbarkeit
st.markdown("""
<style>
    /* Haupt-Hintergrund */
    .stApp {
        background-color: #f4f7f4 !important;
        color: #1e293b !important;
        font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
    }

    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #ffffff !important;
        border-right: 1px solid #e2e8f0 !important;
    }

    /* Überschriften */
    h1, h2, h3, h4, h5, h6 {
        color: #0f291e !important;
        font-weight: 700 !important;
    }

    /* Grüne Hero-Header Karte */
    .hero-header {
        background: linear-gradient(135deg, #2e7d32 0%, #1b5e20 100%);
        color: #ffffff !important;
        padding: 24px;
        border-radius: 20px;
        margin-bottom: 24px;
        box-shadow: 0 10px 20px rgba(46, 125, 50, 0.15);
    }
    .hero-header h1 {
        color: #ffffff !important;
        margin: 0;
        font-size: 2.2rem;
    }
    .hero-header p {
        color: #e8f5e9 !important;
        margin-top: 6px;
        font-size: 1rem;
    }

    /* Karten-Design (Heller Hintergrund, perfekt lesbarer dunkler Text) */
    div[data-testid="stVerticalBlock"] > div[style*="border"] {
        background-color: #ffffff !important;
        border-radius: 20px !important;
        border: 1px solid #e2e8f0 !important;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.04) !important;
        transition: transform 0.2s ease, box-shadow 0.2s ease !important;
        padding: 16px !important;
    }
    div[data-testid="stVerticalBlock"] > div[style*="border"]:hover {
        transform: translateY(-4px);
        box-shadow: 0 12px 24px rgba(46, 125, 50, 0.12) !important;
        border-color: #a5d6a7 !important;
    }

    /* Badges */
    .badge-offen {
        background-color: #e8f5e9;
        color: #1b5e20;
        padding: 6px 14px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 700;
        display: inline-block;
        border: 1px solid #a5d6a7;
    }
    .badge-abgeholt {
        background-color: #ffebee;
        color: #c62828;
        padding: 6px 14px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 700;
        display: inline-block;
        border: 1px solid #ffcdd2;
    }

    /* Tabs Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: transparent;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 12px !important;
        padding: 10px 20px !important;
        background-color: #ffffff !important;
        border: 1px solid #e2e8f0 !important;
        color: #475569 !important;
        font-weight: 600;
    }
    .stTabs [aria-selected="true"] {
        background-color: #2e7d32 !important;
        color: #ffffff !important;
        border-color: #2e7d32 !important;
        box-shadow: 0 4px 12px rgba(46, 125, 50, 0.25);
    }

    /* Input-Felder & Buttons */
    .stTextInput > div > div > input, .stSelectbox > div > div {
        background-color: #ffffff !important;
        color: #0f291e !important;
        border-radius: 12px !important;
        border: 1px solid #cbd5e1 !important;
    }
    .stButton > button {
        border-radius: 12px !important;
        font-weight: 600 !important;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 2. SUPABASE DATENBANK
# ---------------------------------------------------------
@st.cache_resource
def init_supabase():
    url = st.secrets.get("SUPABASE_URL")
    key = st.secrets.get("SUPABASE_KEY")
    if url and key:
        return create_client(url, key)
    return None

supabase: Client = init_supabase()

def load_data():
    if supabase:
        response = supabase.table("fundstuecke").select("*").execute()
        return pd.DataFrame(response.data)
    else:
        DB_FILE = "fundbuero_db.csv"
        if os.path.exists(DB_FILE):
            return pd.read_csv(DB_FILE)
        return pd.DataFrame(columns=[
            "id", "titel", "kategorie", "fundort", "raum", 
            "datum", "status", "kontakt", "bild_base64"
        ])

# ---------------------------------------------------------
# 3. KI-MODELL & LABELS
# ---------------------------------------------------------
def load_labels():
    labels_path = "labels.txt"
    if os.path.exists(labels_path):
        with open(labels_path, "r", encoding="utf-8") as f:
            labels = [line.strip().split(" ", 1)[-1] for line in f.readlines() if line.strip()]
            if labels:
                return labels
    return ["Elektronik", "Kleidung", "Bücher & Hefte", "Sonstiges"]

CATEGORIES = load_labels()

class FixedDepthwiseConv2D(tf.keras.layers.DepthwiseConv2D):
    def __init__(self, *args, **kwargs):
        kwargs.pop('groups', None)
        super().__init__(*args, **kwargs)

@st.cache_resource
def load_keras_model():
    model_path = "keras_model.h5"
    if os.path.exists(model_path):
        try:
            custom_objects = {'DepthwiseConv2D': FixedDepthwiseConv2D}
            model = tf.keras.models.load_model(model_path, custom_objects=custom_objects, compile=False)
            return model, None
        except Exception as e:
            return None, f"Fehler: {e}"
    else:
        return None, "Keras-Modell fehlt"

def predict_category(image_bytes, model):
    if model is None:
        return None, 0.0
    
    img = Image.open(io.BytesIO(image_bytes)).convert('RGB')
    img = img.resize((224, 224))
    
    img_array = np.array(img, dtype=np.float32)
    img_array = np.expand_dims(img_array, axis=0)
    img_array = (img_array / 127.5) - 1.0
    
    try:
        predictions = model(img_array, training=False).numpy()
    except Exception:
        predictions = model.predict(img_array)
        
    predicted_class_index = np.argmax(predictions[0])
    confidence = float(predictions[0][predicted_class_index])
    
    if predicted_class_index < len(CATEGORIES):
        return CATEGORIES[predicted_class_index], confidence
    return CATEGORIES[0], confidence

# ---------------------------------------------------------
# 4. BENUTZEROBERFLÄCHE & STATE
# ---------------------------------------------------------
st.markdown("""
<div class="hero-header">
    <h1>🌱 Schul-Fundbüro</h1>
    <p>Gegenstände schnell wiederfinden, eintragen und verwalten</p>
</div>
""", unsafe_allow_html=True)

if "active_dialog_item" not in st.session_state:
    st.session_state.active_dialog_item = None
if "upload_key" not in st.session_state:
    st.session_state.upload_key = 0
if "success_msg" not in st.session_state:
    st.session_state.success_msg = None

df_items = load_data()
model, model_error = load_keras_model()

# --- SIDEBAR ---
with st.sidebar:
    st.header("🔑 Admin & Status")
    admin_pw_input = st.text_input("Admin-Passwort", type="password")
    ADMIN_PW = st.secrets.get("ADMIN_PASSWORD", "admin123")
    is_admin = (admin_pw_input == ADMIN_PW)
    
    if is_admin:
        st.success("🔓 Owner-Modus aktiv: Löschen erlaubt")
    else:
        st.info("🔒 Normaler Modus (Eintragen & Beanspruchen freigeschaltet)")
        
    st.divider()
    st.caption("⚡ Cloud-DB Status: " + ("🟢 Aktiv" if supabase else "🔴 Offline"))
    st.caption("🤖 KI Status: " + ("🟢 Aktiv" if not model_error else "🔴 Offline"))

# --- DIALOG-FENSTER FÜR DIREKTE DETAILANSICHT ---
@st.dialog("🔎 Details zum Fundstück")
def show_detail_dialog(item_data):
    col1, col2 = st.columns([1, 1])
    with col1:
        if pd.notna(item_data["bild_base64"]) and str(item_data["bild_base64"]).startswith("data:image"):
            st.image(item_data["bild_base64"], use_container_width=True)
        else:
            st.info("Kein Foto vorhanden.")
            
    with col2:
        st.subheader(item_data["titel"])
        status_class = "badge-offen" if item_data["status"] == "Offen" else "badge-abgeholt"
        st.markdown(f'<span class="{status_class}">{item_data["status"]}</span>', unsafe_allow_html=True)
        st.write("")
        
        st.write(f"**🏷️ Kategorie:** {item_data['kategorie']}")
        st.write(f"**📍 Fundort:** {item_data['fundort']} (Raum: {item_data['raum']})")
        st.write(f"**📅 Gefunden am:** {item_data['datum']}")
        st.write(f"**👤 Kontakt:** {item_data['kontakt']}")
    
    st.divider()
    
    # Action Buttons direkt im Dialog
    if item_data["status"] == "Offen":
        if st.button("🙋‍♂️ Das gehört mir! (Als abgeholt markieren)", use_container_width=True, type="primary"):
            if supabase:
                supabase.table("fundstuecke").update({"status": "Abgeholt"}).eq("id", int(item_data["id"])).execute()
            else:
                df_items.loc[df_items["id"] == item_data["id"], "status"] = "Abgeholt"
                df_items.to_csv("fundbuero_db.csv", index=False)
            st.success("Gegenstand wurde als 'Abgeholt' markiert!")
            st.rerun()

    if is_admin:
        if st.button("🗑️ Eintrag löschen (Owner Only)", use_container_width=True):
            if supabase:
                supabase.table("fundstuecke").delete().eq("id", int(item_data["id"])).execute()
            else:
                df_items_new = df_items[df_items["id"] != item_data["id"]]
                df_items_new.to_csv("fundbuero_db.csv", index=False)
            st.success("Eintrag gelöscht!")
            st.rerun()

tab_home, tab_add = st.tabs(["📋 Fundstücke Übersicht", "➕ Neues Fundstück eintragen"])

# --- TAB 1: ÜBERSICHT ---
with tab_home:
    if st.session_state.success_msg:
        st.success(st.session_state.success_msg)
        st.session_state.success_msg = None

    c1, c2, c3 = st.columns([2, 1, 1])
    with c1:
        search_q = st.text_input("🔍 Suchbegriff", placeholder="Suchen nach Name, Ort...")
    with c2:
        filter_c = st.selectbox("Kategorie", ["Alle"] + CATEGORIES)
    with c3:
        filter_s = st.selectbox("Status", ["Alle", "Offen", "Abgeholt"])

    filtered_df = df_items.copy()
    if not filtered_df.empty:
        if search_q:
            filtered_df = filtered_df[
                filtered_df["titel"].str.contains(search_q, case=False, na=False) |
                filtered_df["fundort"].str.contains(search_q, case=False, na=False)
            ]
        if filter_c != "Alle":
            filtered_df = filtered_df[filtered_df["kategorie"] == filter_c]
        if filter_s != "Alle":
            filtered_df = filtered_df[filtered_df["status"] == filter_s]

    if filtered_df.empty:
        st.info("Keine passenden Gegenstände vorhanden.")
    else:
        cols = st.columns(3)
        for idx, row in filtered_df.reset_index(drop=True).iterrows():
            with cols[idx % 3]:
                with st.container(border=True):
                    if pd.notna(row["bild_base64"]) and str(row["bild_base64"]).startswith("data:image"):
                        st.image(row["bild_base64"], use_container_width=True)
                    
                    st.subheader(row["titel"])
                    
                    badge_class = "badge-offen" if row["status"] == "Offen" else "badge-abgeholt"
                    st.markdown(f'<span class="{badge_class}">{row["status"]}</span>', unsafe_allow_html=True)
                    st.write("")
                    
                    st.write(f"**🏷️ Kategorie:** {row['kategorie']}")
                    st.write(f"**📍 Ort:** {row['fundort']} *(Raum: {row['raum']})*")
                    st.write(f"**📅 Datum:** {row['datum']}")
                    
                    # DIREKTES ÖFFNEN PER POPUP/DIALOG
                    if st.button("🔎 Details öffnen", key=f"btn_{row['id']}", use_container_width=True):
                        show_detail_dialog(row)

# --- TAB 2: GEGENSTAND EINTRAGEN ---
with tab_add:
    st.subheader("Neues Fundstück im System registrieren")
    
    uploaded_file = st.file_uploader(
        "Bild hochladen", 
        type=["jpg", "jpeg", "png"], 
        key=f"uploader_{st.session_state.upload_key}"
    )
    
    auto_cat = CATEGORIES[0]
    img_data_url = ""
    
    if uploaded_file is not None:
        file_bytes = uploaded_file.getvalue()
        pred_cat, conf = predict_category(file_bytes, model)
        if pred_cat:
            auto_cat = pred_cat
            st.info(f"🤖 KI-Erkennung schlägt vor: **{auto_cat}** ({conf*100:.1f}%)")
        
        st.image(file_bytes, caption="Vorschau", width=200)
        base64_encoded = base64.b64encode(file_bytes).decode('utf-8')
        img_data_url = f"data:image/jpeg;base64,{base64_encoded}"

    with st.form("add_form", clear_on_submit=True):
        titel = st.text_input("Bezeichnung *", placeholder="z.B. Schwarzer Rucksack")
        cat_idx = CATEGORIES.index(auto_cat) if auto_cat in CATEGORIES else 0
        kategorie = st.selectbox("Kategorie", CATEGORIES, index=cat_idx)
        fundort = st.text_input("Fundort *", placeholder="z.B. Pausenhof")
        raum = st.text_input("Raumnummer / Details", placeholder="z.B. Nahe Basketballplatz")
        kontakt = st.text_input("Abgabeort", placeholder="z.B. Hausmeister")
        
        submitted = st.form_submit_button("💾 Fundstück jetzt Speichern", type="primary", use_container_width=True)
        
        if submitted:
            if not titel or not fundort:
                st.error("Bitte mindestens Titel und Fundort ausfüllen!")
            else:
                today_str = datetime.date.today().strftime("%Y-%m-%d")
                new_row = {
                    "titel": titel,
                    "kategorie": kategorie,
                    "fundort": fundort,
                    "raum": raum,
                    "datum": today_str,
                    "status": "Offen",
                    "kontakt": kontakt,
                    "bild_base64": img_data_url
                }
                
                if supabase:
                    supabase.table("fundstuecke").insert(new_row).execute()
                else:
                    new_row["id"] = len(df_items) + 1
                    df_items = pd.concat([df_items, pd.DataFrame([new_row])], ignore_index=True)
                    df_items.to_csv("fundbuero_db.csv", index=False)
                
                st.session_state.upload_key += 1
                st.session_state.success_msg = f"🎉 Erfolgreich gespeichert! '{titel}' ist jetzt online."
                st.rerun()
