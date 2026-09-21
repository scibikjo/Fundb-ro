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
# 1. PAGE CONFIG & MODERNES STYLING (CUSTOM CSS)
# ---------------------------------------------------------
st.set_page_config(
    page_title="Schul-Fundbüro", 
    page_icon="🔍", 
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    /* Hauptlayout & Farben */
    .stApp {
        background: linear-gradient(135deg, #f5f7fa 0%, #e4e8f0 100%);
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    /* Titel-Styling */
    .main-title {
        font-size: 2.2rem;
        font-weight: 800;
        color: #1e293b;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        color: #64748b;
        font-size: 1rem;
        margin-bottom: 1.5rem;
    }

    /* Karten-Design für Fundstücke */
    div[data-testid="stVerticalBlock"] > div[style*="border"] {
        background-color: #ffffff !important;
        border-radius: 16px !important;
        border: 1px solid #e2e8f0 !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.03) !important;
        transition: all 0.25s ease-in-out !important;
        padding: 18px !important;
    }
    div[data-testid="stVerticalBlock"] > div[style*="border"]:hover {
        transform: translateY(-5px);
        box-shadow: 0 12px 24px rgba(0, 0, 0, 0.08) !important;
        border-color: #cbd5e1 !important;
    }

    /* Status-Badges */
    .badge {
        padding: 6px 12px;
        border-radius: 20px;
        font-weight: 700;
        font-size: 0.78rem;
        letter-spacing: 0.5px;
        text-transform: uppercase;
        display: inline-block;
    }
    .badge-offen {
        background-color: #dcfce7;
        color: #15803d;
        border: 1px solid #bbf7d0;
    }
    .badge-abgeholt {
        background-color: #fee2e2;
        color: #b91c1c;
        border: 1px solid #fecaca;
    }

    /* Tabs Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        background-color: transparent;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 10px !important;
        padding: 10px 20px !important;
        background-color: #ffffff !important;
        border: 1px solid #e2e8f0 !important;
        font-weight: 600 !important;
        color: #475569 !important;
    }
    .stTabs [aria-selected="true"] {
        background-color: #2563eb !important;
        color: #ffffff !important;
        border-color: #2563eb !important;
        box-shadow: 0 4px 10px rgba(37, 99, 235, 0.25) !important;
    }

    /* Input-Felder abrunden */
    .stTextInput > div > div > input, .stSelectbox > div > div {
        border-radius: 10px !important;
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
# 3. LABELS & KI-MODELL
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
            return None, f"Fehler beim Laden: {e}"
    else:
        return None, f"Datei '{model_path}' fehlt auf GitHub!"

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
# 4. BENUTZEROBERFLÄCHE & STATE MANAGEMENT
# ---------------------------------------------------------
st.markdown('<div class="main-title">🔍 Digitales Schul-Fundbüro</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Verlorene Gegenstände finden, eintragen und verwalten.</div>', unsafe_allow_html=True)

if "selected_item_id" not in st.session_state:
    st.session_state.selected_item_id = None
if "upload_key" not in st.session_state:
    st.session_state.upload_key = 0
if "success_msg" not in st.session_state:
    st.session_state.success_msg = None

df_items = load_data()
model, model_error = load_keras_model()

# --- SIDEBAR (STATUS & ADMIN-LOGIN) ---
with st.sidebar:
    st.header("🔑 Admin & Status")
    
    # Passwort-Abfrage für Owner/Admin
    admin_pw_input = st.text_input("Admin-Passwort (zum Löschen)", type="password")
    ADMIN_PW = st.secrets.get("ADMIN_PASSWORD", "admin123")
    is_admin = (admin_pw_input == ADMIN_PW)
    
    if is_admin:
        st.success("🔓 Admin-Modus aktiv: Löschen freigeschaltet!")
    else:
        st.caption("ℹ️ Als Schülerschaft/Lehrkraft hast du Vollzugriff auf das Eintragen und als 'Abgeholt' markieren.")
        
    st.divider()
    
    st.subheader("System Status")
    if supabase:
        st.success("☁️ Cloud-Datenbank verbunden")
    else:
        st.warning("⚠️ CSV-Lokalmodus")
        
    if model_error:
        st.error(f"⚠️ {model_error}")
    else:
        st.success("🤖 KI-Erkennung aktiv")

tab_home, tab_add, tab_detail = st.tabs(["📋 Übersicht & Suche", "➕ Etwas melden", "🔎 Details & Status"])

# --- TAB 1: DASHBOARD ---
with tab_home:
    if st.session_state.success_msg:
        st.success(st.session_state.success_msg)
        st.session_state.success_msg = None
    
    col_search, col_cat, col_status = st.columns([2, 1, 1])
    with col_search:
        search_query = st.text_input("🔍 Suchbegriff", placeholder="Suchen nach Titel, Ort...")
    with col_cat:
        filter_cat = st.selectbox("Kategorie", ["Alle"] + CATEGORIES)
    with col_status:
        filter_status = st.selectbox("Status", ["Alle", "Offen", "Abgeholt"])
    
    filtered_df = df_items.copy()
    if not filtered_df.empty:
        if search_query:
            filtered_df = filtered_df[
                filtered_df["titel"].str.contains(search_query, case=False, na=False) |
                filtered_df["fundort"].str.contains(search_query, case=False, na=False)
            ]
        if filter_cat != "Alle":
            filtered_df = filtered_df[filtered_df["kategorie"] == filter_cat]
        if filter_status != "Alle":
            filtered_df = filtered_df[filtered_df["status"] == filter_status]
        
    if filtered_df.empty:
        st.info("Keine Fundstücke vorhanden.")
    else:
        cols = st.columns(3)
        for idx, row in filtered_df.reset_index(drop=True).iterrows():
            with cols[idx % 3]:
                with st.container(border=True):
                    if pd.notna(row["bild_base64"]) and str(row["bild_base64"]).startswith("data:image"):
                        st.image(row["bild_base64"], use_container_width=True)
                    
                    st.subheader(row["titel"])
                    
                    status_class = "badge-offen" if row["status"] == "Offen" else "badge-abgeholt"
                    st.markdown(f'<span class="badge {status_class}">{row["status"]}</span>', unsafe_allow_html=True)
                    st.write("")
                    
                    st.markdown(f"**🏷️ Kategorie:** {row['kategorie']}")
                    st.markdown(f"**📍 Ort:** {row['fundort']} *(Raum: {row['raum']})*")
                    st.markdown(f"**📅 Datum:** {row['datum']}")
                    
                    if st.button("🔎 Details ansehen", key=f"btn_{row['id']}", use_container_width=True):
                        st.session_state.selected_item_id = int(row["id"])
                        st.rerun()

# --- TAB 2: GEGENSTAND MELDEN ---
with tab_add:
    st.subheader("Gefundenen Gegenstand eintragen")
    
    uploaded_file = st.file_uploader(
        "Foto des Gegenstands hochladen", 
        type=["jpg", "jpeg", "png"], 
        key=f"uploader_{st.session_state.upload_key}"
    )
    
    auto_category = CATEGORIES[0]
    img_data_url = ""
    
    if uploaded_file is not None:
        file_bytes = uploaded_file.getvalue()
        predicted_cat, conf = predict_category(file_bytes, model)
        if predicted_cat:
            auto_category = predicted_cat
            st.info(f"🤖 KI-Vorschlag: **{auto_category}** ({conf*100:.1f}% Sicherheit)")
        
        st.image(file_bytes, caption="Vorschau", width=200)
        base64_encoded = base64.b64encode(file_bytes).decode('utf-8')
        img_data_url = f"data:image/jpeg;base64,{base64_encoded}"

    with st.form("add_item_form", clear_on_submit=True):
        titel = st.text_input("Gegenstand / Titel *", placeholder="z.B. Blaue Nike Sportjacke")
        kategorie_index = CATEGORIES.index(auto_category) if auto_category in CATEGORIES else 0
        kategorie = st.selectbox("Kategorie", CATEGORIES, index=kategorie_index)
        fundort = st.text_input("Fundort *", placeholder="z.B. Sporthalle / Mensa")
        raum = st.text_input("Raumnummer / Genauere Angabe", placeholder="z.B. Umkleide 2")
        kontakt = st.text_input("Abgabeort / Finder", placeholder="z.B. Abgegeben im Sekretariat")
        
        submitted = st.form_submit_button("💾 Fundstück eintragen", type="primary", use_container_width=True)
        
        if submitted:
            if not titel or not fundort:
                st.error("Bitte mindestens **Titel** und **Fundort** ausfüllen.")
            else:
                with st.spinner("Fundstück wird gespeichert..."):
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
                    st.session_state.success_msg = f"✅ Erfolgreich gespeichert: **'{titel}'** wurde eingetragen."
                    st.rerun()

# --- TAB 3: DETAILS & STATUS ÄNDERN ---
with tab_detail:
    st.subheader("Detailansicht & Statusänderung")
    
    if df_items.empty:
        st.info("Es sind aktuell keine Fundstücke in der Datenbank.")
    else:
        all_ids = df_items["id"].tolist()
        
        default_index = 0
        if st.session_state.selected_item_id in all_ids:
            default_index = all_ids.index(st.session_state.selected_item_id)
            
        selected_id = st.selectbox(
            "Fundstück wählen", 
            options=all_ids,
            index=default_index,
            format_func=lambda x: f"ID {x}: {df_items.loc[df_items['id'] == x, 'titel'].values[0]} [{df_items.loc[df_items['id'] == x, 'status'].values[0]}]"
        )
        
        item_data = df_items[df_items["id"] == selected_id].iloc[0]
        
        col_img, col_info = st.columns([1, 1])
        with col_img:
            if pd.notna(item_data["bild_base64"]) and str(item_data["bild_base64"]).startswith("data:image"):
                st.image(item_data["bild_base64"], use_container_width=True)
            else:
                st.info("Kein Bild vorhanden.")
        
        with col_info:
            st.title(item_data["titel"])
            
            status_class = "badge-offen" if item_data["status"] == "Offen" else "badge-abgeholt"
            st.markdown(f'<span class="badge {status_class}">{item_data["status"]}</span>', unsafe_allow_html=True)
            st.write("")
            
            st.markdown(f"**🏷️ Kategorie:** {item_data['kategorie']}")
            st.markdown(f"**📍 Fundort:** {item_data['fundort']} *(Raum: {item_data['raum']})*")
            st.markdown(f"**📅 Gefunden am:** {item_data['datum']}")
            st.markdown(f"**👤 Kontakt / Aufbewahrung:** {item_data['kontakt']}")
            
            st.divider()
            
            # --- STATUS ÄNDERN (FÜR JEDEN) ---
            if item_data["status"] == "Offen":
                if st.button("🙋‍♂️ Das gehört mir! (Als abgeholt markieren)", use_container_width=True, type="primary"):
                    if supabase:
                        supabase.table("fundstuecke").update({"status": "Abgeholt"}).eq("id", selected_id).execute()
                    else:
                        df_items.loc[df_items["id"] == selected_id, "status"] = "Abgeholt"
                        df_items.to_csv("fundbuero_db.csv", index=False)
                    st.success("Gegenstand erfolgreich als 'Abgeholt' markiert!")
                    st.rerun()
            else:
                st.info("Dieser Gegenstand wurde bereits abgeholt.")

            # --- LÖSCHEN (NUR FÜR ADMINS) ---
            st.write("")
            if is_admin:
                if st.button("🗑️ Eintrag unwiderruflich löschen", use_container_width=True):
                    if supabase:
                        supabase.table("fundstuecke").delete().eq("id", selected_id).execute()
                    else:
                        df_items = df_items[df_items["id"] != selected_id]
                        df_items.to_csv("fundbuero_db.csv", index=False)
                    st.session_state.selected_item_id = None
                    st.success("Eintrag gelöscht!")
                    st.rerun()
            else:
                st.caption("🔒 *Nur der Owner/Admin kann Fundstücke komplett löschen (Passwort-Eingabe in der Sidebar erforderlich).*")
