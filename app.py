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
# 1. PAGE CONFIG & DEEP MODERN CSS (RADIKALES DESIGN)
# ---------------------------------------------------------
st.set_page_config(
    page_title="Schul-Fundbüro Premium", 
    page_icon="🔍", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Injektion von direktem Custom CSS für das gesamte Theme
st.markdown("""
<style>
    /* Hintergrund & Hauptfarben */
    .stApp {
        background: #0f172a !important;
        color: #f8fafc !important;
    }

    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #1e293b !important;
        border-right: 1px solid #334155 !important;
    }

    /* Überschriften */
    h1, h2, h3, h4, h5, h6 {
        color: #ffffff !important;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }

    /* Custom Cards für Fundstücke */
    .card-container {
        background: #1e293b;
        border: 1px solid #334155;
        border-radius: 16px;
        padding: 16px;
        margin-bottom: 20px;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.3);
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    .card-container:hover {
        transform: translateY(-4px);
        border-color: #3b82f6;
    }

    .card-img {
        width: 100%;
        height: 200px;
        object-fit: cover;
        border-radius: 12px;
        margin-bottom: 12px;
    }

    /* Badges */
    .badge-offen {
        background-color: #065f46;
        color: #34d399;
        padding: 4px 12px;
        border-radius: 9999px;
        font-size: 0.8rem;
        font-weight: 700;
        display: inline-block;
        border: 1px solid #059669;
    }
    .badge-abgeholt {
        background-color: #881337;
        color: #fecdd3;
        padding: 4px 12px;
        border-radius: 9999px;
        font-size: 0.8rem;
        font-weight: 700;
        display: inline-block;
        border: 1px solid #be123c;
    }

    /* Streamlit Tabs Anpassen */
    .stTabs [data-baseweb="tab-list"] {
        gap: 12px;
        background-color: transparent;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 10px !important;
        padding: 12px 24px !important;
        background-color: #1e293b !important;
        border: 1px solid #334155 !important;
        color: #94a3b8 !important;
        font-weight: 600;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #2563eb, #1d4ed8) !important;
        color: #ffffff !important;
        border-color: #3b82f6 !important;
        box-shadow: 0 4px 14px rgba(37, 99, 235, 0.4);
    }

    /* Input-Felder & Buttons */
    .stTextInput > div > div > input, .stSelectbox > div > div {
        background-color: #1e293b !important;
        color: #ffffff !important;
        border-radius: 10px !important;
        border: 1px solid #334155 !important;
    }
    .stButton > button {
        border-radius: 10px !important;
        font-weight: 600 !important;
        transition: all 0.2s ease !important;
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
st.markdown("<h1 style='text-align: center; font-size: 2.8rem;'>🔍 Digitales Schul-Fundbüro</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #94a3b8; font-size: 1.1rem; margin-bottom: 2rem;'>Finden, Melden und Verwalten von Schulfundsachen</p>", unsafe_allow_html=True)

if "selected_item_id" not in st.session_state:
    st.session_state.selected_item_id = None
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
        st.success("🔓 Owner-Modus: Löschen aktiv")
    else:
        st.info("🔒 Normaler Modus (Eintragen & Beanspruchen freigeschaltet)")
        
    st.divider()
    st.caption("⚡ Cloud-DB Status: " + ("🟢 Aktiv" if supabase else "🔴 Offline"))
    st.caption("🤖 KI Status: " + ("🟢 Aktiv" if not model_error else "🔴 Offline"))

tab_home, tab_add, tab_detail = st.tabs(["📋 Fundstücke Übersicht", "➕ Neues Fundstück eintragen", "🔎 Detailansicht"])

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
        st.info("Keine passenden Gegenstände gefunden.")
    else:
        cols = st.columns(3)
        for idx, row in filtered_df.reset_index(drop=True).iterrows():
            with cols[idx % 3]:
                # Custom HTML Card für garantiertes Styling
                img_src = row["bild_base64"] if (pd.notna(row["bild_base64"]) and str(row["bild_base64"]).startswith("data:image")) else "https://via.placeholder.com/300x200?text=Kein+Bild"
                badge_class = "badge-offen" if row["status"] == "Offen" else "badge-abgeholt"
                
                card_html = f"""
                <div class="card-container">
                    <img src="{img_src}" class="card-img" />
                    <span class="{badge_class}">{row['status']}</span>
                    <h3 style="margin-top: 10px; margin-bottom: 5px;">{row['titel']}</h3>
                    <p style="color: #94a3b8; font-size: 0.9rem; margin-bottom: 4px;">🏷️ {row['kategorie']}</p>
                    <p style="color: #94a3b8; font-size: 0.9rem; margin-bottom: 4px;">📍 {row['fundort']} (Raum: {row['raum']})</p>
                    <p style="color: #64748b; font-size: 0.8rem;">📅 {row['datum']}</p>
                </div>
                """
                st.markdown(card_html, unsafe_allow_html=True)
                
                if st.button("🔎 Details öffnen", key=f"btn_{row['id']}", use_container_width=True):
                    st.session_state.selected_item_id = int(row["id"])
                    st.rerun()

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
                
                # Formular zurücksetzen & Feedback anzeigen
                st.session_state.upload_key += 1
                st.session_state.success_msg = f"🎉 Erfolgreich gespeichert! '{titel}' ist jetzt online."
                st.rerun()

# --- TAB 3: DETAILS & STATUS ---
with tab_detail:
    st.subheader("Gegenstand-Details")
    
    if df_items.empty:
        st.info("Keine Daten vorhanden.")
    else:
        all_ids = df_items["id"].tolist()
        def_idx = 0
        if st.session_state.selected_item_id in all_ids:
            def_idx = all_ids.index(st.session_state.selected_item_id)
            
        selected_id = st.selectbox(
            "Fundstück wählen", 
            options=all_ids,
            index=def_idx,
            format_func=lambda x: f"ID {x}: {df_items.loc[df_items['id'] == x, 'titel'].values[0]}"
        )
        
        item = df_items[df_items["id"] == selected_id].iloc[0]
        
        col_i1, col_i2 = st.columns([1, 1])
        with col_i1:
            if pd.notna(item["bild_base64"]) and str(item["bild_base64"]).startswith("data:image"):
                st.image(item["bild_base64"], use_container_width=True)
            else:
                st.info("Kein Foto verfügbar")
                
        with col_i2:
            st.title(item["titel"])
            st.markdown(f"**Status:** `{item['status']}`")
            st.markdown(f"**Kategorie:** {item['kategorie']}")
            st.markdown(f"**Ort:** {item['fundort']} (Raum: {item['raum']})")
            st.markdown(f"**Datum:** {item['datum']}")
            st.markdown(f"**Abgabeort:** {item['kontakt']}")
            
            st.divider()
            
            # Button für JEDEN
            if item["status"] == "Offen":
                if st.button("🙋‍♂️ Das gehört mir! (Als abgeholt markieren)", use_container_width=True, type="primary"):
                    if supabase:
                        supabase.table("fundstuecke").update({"status": "Abgeholt"}).eq("id", selected_id).execute()
                    else:
                        df_items.loc[df_items["id"] == selected_id, "status"] = "Abgeholt"
                        df_items.to_csv("fundbuero_db.csv", index=False)
                    st.success("Status auf 'Abgeholt' geändert.")
                    st.rerun()
            
            # Button NUR FÜR ADMIN
            if is_admin:
                if st.button("🗑️ Eintrag löschen (Owner Only)", use_container_width=True):
                    if supabase:
                        supabase.table("fundstuecke").delete().eq("id", selected_id).execute()
                    else:
                        df_items = df_items[df_items["id"] != selected_id]
                        df_items.to_csv("fundbuero_db.csv", index=False)
                    st.session_state.selected_item_id = None
                    st.success("Gelöscht!")
                    st.rerun()
