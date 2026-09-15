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
# 1. PAGE CONFIG & CUSTOM CSS (MODERNES DESIGN)
# ---------------------------------------------------------
st.set_page_config(page_title="Schul-Fundbüro", page_icon="🔍", layout="wide")

st.markdown("""
<style>
    /* Haupt-Hintergrund & Schrift */
    .stApp {
        background-color: #f8f9fa;
    }
    
    /* Karten-Design für Fundstücke */
    div[data-testid="stVerticalBlock"] > div[style*="border"] {
        background-color: #ffffff;
        border-radius: 12px !important;
        border: 1px solid #e9ecef !important;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.04);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
        padding: 16px;
    }
    div[data-testid="stVerticalBlock"] > div[style*="border"]:hover {
        transform: translateY(-4px);
        box-shadow: 0 10px 15px rgba(0, 0, 0, 0.08);
    }
    
    /* Status Badges */
    .badge-offen {
        background-color: #d1e7dd;
        color: #0f5132;
        padding: 4px 10px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.85rem;
        display: inline-block;
    }
    .badge-abgeholt {
        background-color: #f8d7da;
        color: #842029;
        padding: 4px 10px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.85rem;
        display: inline-block;
    }
    
    /* Tab Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        padding: 8px 16px;
        background-color: #ffffff;
        border: 1px solid #dee2e6;
    }
    .stTabs [aria-selected="true"] {
        background-color: #0d6efd !important;
        color: white !important;
    }
    
    /* Buttons verfeinern */
    .stButton > button {
        border-radius: 8px !important;
        font-weight: 500;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 2. SUPABASE DATENBANK-VERBINDUNG
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
# 4. BENUTZEROBERFLÄCHE (UI & STATE)
# ---------------------------------------------------------
st.title("🔍 Digitales Schul-Fundbüro")

# State Management
if "selected_item_id" not in st.session_state:
    st.session_state.selected_item_id = None
if "upload_key" not in st.session_state:
    st.session_state.upload_key = 0
if "success_msg" not in st.session_state:
    st.session_state.success_msg = None

df_items = load_data()
model, model_error = load_keras_model()

with st.sidebar:
    st.header("⚙️ System-Status")
    if supabase:
        st.success("☁️ Supabase Cloud-DB aktiv")
    else:
        st.warning("⚠️ Lokaler CSV-Modus")
        
    if model_error:
        st.error(f"⚠️ {model_error}")
    else:
        st.success("🤖 KI-Modell bereit")
    
    st.divider()
    st.markdown("**Verfügbare Kategorien:**")
    for cat in CATEGORIES:
        st.markdown(f"- `{cat}`")

tab_home, tab_add, tab_detail = st.tabs(["📋 Dashboard", "➕ Etwas gefunden", "🔎 Detailansicht"])

# --- TAB 1: DASHBOARD ---
with tab_home:
    st.header("Aktuelle Fundstücke")
    
    # Erfolgsmeldung anzeigen, wenn gerade ein Item hochgeladen wurde
    if st.session_state.success_msg:
        st.success(st.session_state.success_msg)
        st.session_state.success_msg = None
    
    col_search, col_cat, col_status = st.columns([2, 1, 1])
    with col_search:
        search_query = st.text_input("🔍 Suchbegriff", placeholder="z.B. Jacke, Turnhalle...")
    with col_cat:
        filter_cat = st.selectbox("Kategorie Filter", ["Alle"] + CATEGORIES)
    with col_status:
        filter_status = st.selectbox("Status Filter", ["Alle", "Offen", "Abgeholt"])
    
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
        st.info("Keine passenden Fundstücke vorhanden.")
    else:
        cols = st.columns(3)
        for idx, row in filtered_df.reset_index(drop=True).iterrows():
            with cols[idx % 3]:
                with st.container(border=True):
                    if pd.notna(row["bild_base64"]) and str(row["bild_base64"]).startswith("data:image"):
                        st.image(row["bild_base64"], use_container_width=True)
                    
                    st.subheader(row["titel"])
                    
                    status_class = "badge-offen" if row["status"] == "Offen" else "badge-abgeholt"
                    st.markdown(f'<span class="{status_class}">{row["status"]}</span>', unsafe_allow_html=True)
                    st.write("")
                    
                    st.markdown(f"**🏷️ Kategorie:** {row['kategorie']}")
                    st.markdown(f"**📍 Fundort:** {row['fundort']} (Raum: {row['raum']})")
                    st.markdown(f"**📅 Datum:** {row['datum']}")
                    
                    if st.button("🔎 Details ansehen", key=f"btn_{row['id']}", use_container_width=True):
                        st.session_state.selected_item_id = int(row["id"])
                        st.rerun()

# --- TAB 2: FORMULAR "ETWAS GEFUNDEN" ---
with tab_add:
    st.header("Neues Fundstück eintragen")
    
    # Dynamic Key setzt den Uploader nach dem Speichern zurück
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
            st.info(f"🤖 KI-Klassifizierung: **{auto_category}** ({conf*100:.1f}% Sicherheit)")
        
        st.image(file_bytes, caption="Vorschau", width=220)
        base64_encoded = base64.b64encode(file_bytes).decode('utf-8')
        img_data_url = f"data:image/jpeg;base64,{base64_encoded}"

    with st.form("add_item_form", clear_on_submit=True):
        titel = st.text_input("Titel / Gegenstand *", placeholder="z.B. Blaue Nike Sportjacke")
        kategorie_index = CATEGORIES.index(auto_category) if auto_category in CATEGORIES else 0
        kategorie = st.selectbox("Kategorie", CATEGORIES, index=kategorie_index)
        fundort = st.text_input("Fundort *", placeholder="z.B. Haupteingang / Mensa")
        raum = st.text_input("Raumnummer / Bereich", placeholder="z.B. Raum 102")
        kontakt = st.text_input("Finder / Abgabeort", placeholder="z.B. Hausmeister / Sekretariat")
        
        # Visueller Submit Button
        submitted = st.form_submit_button("💾 Fundstück jetzt speichern", type="primary", use_container_width=True)
        
        if submitted:
            if not titel or not fundort:
                st.error("Bitte füllen Sie mindestens die Felder **Titel** und **Fundort** aus.")
            else:
                with st.spinner("Fundstück wird in der Datenbank gespeichert..."):
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
                    
                    # Verhindert Mehrfach-Uploads durch Reset des Uploader-Keys
                    st.session_state.upload_key += 1
                    st.session_state.success_msg = f"✅ Success! **'{titel}'** wurde erfolgreich im Fundbüro eingetragen."
                    st.rerun()

# --- TAB 3: DETAILANSICHT & VERWALTUNG ---
with tab_detail:
    st.header("Gegenstand-Details & Verwaltung")
    
    if df_items.empty:
        st.info("Derzeit gibt es keine eingetragenen Fundstücke.")
    else:
        all_ids = df_items["id"].tolist()
        
        default_index = 0
        if st.session_state.selected_item_id in all_ids:
            default_index = all_ids.index(st.session_state.selected_item_id)
            
        selected_id = st.selectbox(
            "Fundstück zur Detailansicht auswählen", 
            options=all_ids,
            index=default_index,
            format_func=lambda x: f"ID {x}: {df_items.loc[df_items['id'] == x, 'titel'].values[0]} [{df_items.loc[df_items['id'] == x, 'status'].values[0]}]"
        )
        
        item_data = df_items[df_items["id"] == selected_id].iloc[0]
        
        col_img, col_info = st.columns([1, 1])
        with col_img:
            if pd.notna(item_data["bild_base64"]) and str(item_data["bild_base64"]).startswith("data:image"):
                st.image(item_data["bild_base64"], use_container_width=True)
        
        with col_info:
            st.title(item_data["titel"])
            
            status_class = "badge-offen" if item_data["status"] == "Offen" else "badge-abgeholt"
            st.markdown(f'<span class="{status_class}">{item_data["status"]}</span>', unsafe_allow_html=True)
            st.write("")
            
            st.markdown(f"**🏷️ Kategorie:** {item_data['kategorie']}")
            st.markdown(f"**📍 Fundort:** {item_data['fundort']} (Raum: {item_data['raum']})")
            st.markdown(f"**📅 Gefunden am:** {item_data['datum']}")
            st.markdown(f"**👤 Kontakt / Abgabeort:** {item_data['kontakt']}")
            
            st.divider()
            
            col_action1, col_action2 = st.columns(2)
            
            with col_action1:
                if item_data["status"] == "Offen":
                    if st.button("🙋‍♂️ Das gehört mir! (Abgeholt)", use_container_width=True):
                        if supabase:
                            supabase.table("fundstuecke").update({"status": "Abgeholt"}).eq("id", selected_id).execute()
                        else:
                            df_items.loc[df_items["id"] == selected_id, "status"] = "Abgeholt"
                            df_items.to_csv("fundbuero_db.csv", index=False)
                        st.success("Gegenstand wurde als 'Abgeholt' markiert.")
                        st.rerun()
                else:
                    st.info("Bereits als abgeholt markiert.")

            with col_action2:
                if st.button("🗑️ Eintrag löschen", type="primary", use_container_width=True):
                    if supabase:
                        supabase.table("fundstuecke").delete().eq("id", selected_id).execute()
                    else:
                        df_items = df_items[df_items["id"] != selected_id]
                        df_items.to_csv("fundbuero_db.csv", index=False)
                    st.session_state.selected_item_id = None
                    st.success("Eintrag aus Datenbank gelöscht.")
                    st.rerun()
