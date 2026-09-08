import os
import io
import datetime
import base64
import pandas as pd
import numpy as np
from PIL import Image
import streamlit as st
import tensorflow as tf

DB_FILE = "fundbuero_db.csv"

# ---------------------------------------------------------
# 1. LABELS / KATEGORIEN AUS LABELS.TXT LADEN
# ---------------------------------------------------------
def load_labels():
    labels_path = "labels.txt"
    if os.path.exists(labels_path):
        with open(labels_path, "r", encoding="utf-8") as f:
            # Entfernt Nummern wie "0 ", "1 " am Anfang der Zeilen
            labels = [line.strip().split(" ", 1)[-1] for line in f.readlines() if line.strip()]
            if labels:
                return labels
    # Fallback-Kategorien, falls labels.txt fehlt
    return ["Elektronik", "Kleidung", "Bücher & Hefte", "Sonstiges"]

CATEGORIES = load_labels()

# ---------------------------------------------------------
# 2. DATENBANK (LOKALE CSV-SPEICHERUNG)
# ---------------------------------------------------------
def load_data():
    if os.path.exists(DB_FILE):
        return pd.read_csv(DB_FILE)
    else:
        return pd.DataFrame(columns=[
            "id", "titel", "kategorie", "fundort", "raum", 
            "datum", "status", "kontakt", "bild_base64"
        ])

def save_data(df):
    df.to_csv(DB_FILE, index=False)

# ---------------------------------------------------------
# 3. KI-INTEGRATION (KERAS MOBILENETV2)
# ---------------------------------------------------------
@st.cache_resource
def load_keras_model():
    model_path = "keras_model.h5"
    if os.path.exists(model_path):
        try:
            return tf.keras.models.load_model(model_path, compile=False), None
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
    
    # Teachable Machine Standard-Skalierung (-1 bis 1)
    img_array = (img_array / 127.5) - 1.0
    
    predictions = model.predict(img_array)
    predicted_class_index = np.argmax(predictions[0])
    confidence = float(predictions[0][predicted_class_index])
    
    if predicted_class_index < len(CATEGORIES):
        return CATEGORIES[predicted_class_index], confidence
    return CATEGORIES[0], confidence

# ---------------------------------------------------------
# 4. BENUTZEROBERFLÄCHE (STREAMLIT UI)
# ---------------------------------------------------------
st.set_page_config(page_title="Schul-Fundbüro", page_icon="🔍", layout="wide")
st.title("🔍 Digitales Schul-Fundbüro")

df_items = load_data()
model, model_error = load_keras_model()

# Status in der Sidebar
with st.sidebar:
    st.header("KI-Status")
    if model_error:
        st.error(f"⚠️ {model_error}")
    else:
        st.success("✅ KI-Modell bereit!")
        st.write("**Gefundene Klassen:**")
        for cat in CATEGORIES:
            st.write(f"- {cat}")

tab_home, tab_add, tab_detail = st.tabs(["📋 Dashboard", "➕ Etwas gefunden", "🔎 Detailansicht"])

# --- TAB 1: DASHBOARD ---
with tab_home:
    st.header("Aktuelle Fundstücke")
    
    col_search, col_cat, col_status = st.columns([2, 1, 1])
    with col_search:
        search_query = st.text_input("Suchbegriff (Titel/Ort)", "")
    with col_cat:
        filter_cat = st.selectbox("Kategorie-Filter", ["Alle"] + CATEGORIES)
    with col_status:
        filter_status = st.selectbox("Status-Filter", ["Alle", "Offen", "Abgeholt"])
    
    filtered_df = df_items.copy()
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
        st.info("Keine Fundstücke gefunden.")
    else:
        cols = st.columns(3)
        for idx, row in filtered_df.reset_index(drop=True).iterrows():
            with cols[idx % 3]:
                with st.container(border=True):
                    if pd.notna(row["bild_base64"]) and str(row["bild_base64"]).startswith("data:image"):
                        st.image(row["bild_base64"], use_container_width=True)
                    st.subheader(row["titel"])
                    st.write(f"**Kategorie:** {row['kategorie']}")
                    st.write(f"**Fundort:** {row['fundort']} (Raum: {row['raum']})")
                    st.write(f"**Status:** {row['status']}")
                    st.write(f"**Datum:** {row['datum']}")

# --- TAB 2: FORMULAR "ETWAS GEFUNDEN" ---
with tab_add:
    st.header("Neues Fundstück eintragen")
    
    uploaded_file = st.file_uploader("Foto des Gegenstands hochladen", type=["jpg", "jpeg", "png"])
    
    auto_category = CATEGORIES[0]
    img_data_url = ""
    
    if uploaded_file is not None:
        file_bytes = uploaded_file.getvalue()
        
        predicted_cat, conf = predict_category(file_bytes, model)
        if predicted_cat:
            auto_category = predicted_cat
            st.success(f"🤖 KI-Vorschlag: **{auto_category}** ({conf*100:.1f}% Sicher)")
        else:
            st.warning("⚠️ KI konnte nicht genutzt werden. Bitte manuell wählen.")
            
        st.image(file_bytes, caption="Hochgeladenes Bild", width=200)
        
        base64_encoded = base64.b64encode(file_bytes).decode('utf-8')
        img_data_url = f"data:image/jpeg;base64,{base64_encoded}"

    with st.form("add_item_form"):
        titel = st.text_input("Titel / Gegenstand", placeholder="z.B. Blaue Trinkflasche")
        kategorie_index = CATEGORIES.index(auto_category) if auto_category in CATEGORIES else 0
        kategorie = st.selectbox("Kategorie", CATEGORIES, index=kategorie_index)
        fundort = st.text_input("Fundort", placeholder="z.B. Sporthalle")
        raum = st.text_input("Raumnummer / Bereich", placeholder="z.B. Umkleide 2")
        kontakt = st.text_input("Finder / Abgabeort", placeholder="z.B. Abgegeben im Sekretariat")
        
        submitted = st.form_submit_button("Fundstück speichern")
        
        if submitted:
            if not titel or not fundort:
                st.error("Bitte mindestens Titel und Fundort ausfüllen.")
            else:
                new_id = len(df_items) + 1
                today_str = datetime.date.today().strftime("%Y-%m-%d")
                
                new_row = {
                    "id": new_id,
                    "titel": titel,
                    "kategorie": kategorie,
                    "fundort": fundort,
                    "raum": raum,
                    "datum": today_str,
                    "status": "Offen",
                    "kontakt": kontakt,
                    "bild_base64": img_data_url
                }
                
                df_items = pd.concat([df_items, pd.DataFrame([new_row])], ignore_index=True)
                save_data(df_items)
                st.success("Fundstück erfolgreich eingetragen!")
                st.rerun()

# --- TAB 3: DETAILANSICHT ---
with tab_detail:
    st.header("Gegenstand-Details & Eigentum beanspruchen")
    
    offene_items = df_items[df_items["status"] == "Offen"]
    if offene_items.empty:
        st.info("Derzeit gibt es keine offenen Fundstücke.")
    else:
        selected_id = st.selectbox(
            "Fundstück auswählen", 
            options=offene_items["id"].tolist(),
            format_func=lambda x: f"ID {x}: {df_items.loc[df_items['id'] == x, 'titel'].values[0]}"
        )
        
        item_data = df_items[df_items["id"] == selected_id].iloc[0]
        
        col_img, col_info = st.columns([1, 1])
        with col_img:
            if pd.notna(item_data["bild_base64"]) and str(item_data["bild_base64"]).startswith("data:image"):
                st.image(item_data["bild_base64"], use_container_width=True)
        
        with col_info:
            st.title(item_data["titel"])
            st.write(f"**Status:** {item_data['status']}")
            st.write(f"**Kategorie:** {item_data['kategorie']}")
            st.write(f"**Fundort:** {item_data['fundort']} ({item_data['raum']})")
            st.write(f"**Gefunden am:** {item_data['datum']}")
            st.write(f"**Kontakt / Abgabeort:** {item_data['kontakt']}")
            
            st.divider()
            if st.button("Das gehört mir! (Als abgeholt markieren)"):
                df_items.loc[df_items["id"] == selected_id, "status"] = "Abgeholt"
                save_data(df_items)
                st.success("Der Gegenstand wurde als 'Abgeholt' markiert!")
                st.rerun()
