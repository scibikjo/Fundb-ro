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
# 1. PAGE CONFIG & DESIGN SYSTEM
# ---------------------------------------------------------
st.set_page_config(
    page_title="FundSpot – Schul-Fundbüro", 
    page_icon="🌱", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Modernes Styling
st.markdown("""
<style>
    .stApp {
        background-color: #f8faf9 !important;
        color: #1e293b !important;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }

    /* Header & Brand Logo */
    .brand-header {
        display: flex;
        align-items: center;
        gap: 12px;
        background: #ffffff;
        padding: 16px 28px;
        border-radius: 20px;
        box-shadow: 0 4px 16px rgba(0,0,0,0.04);
        margin-bottom: 24px;
        border: 1px solid #e2e8f0;
    }
    .brand-logo {
        background: #2e7d32;
        color: white;
        font-weight: 900;
        font-size: 1.4rem;
        padding: 8px 14px;
        border-radius: 14px;
    }
    .brand-title {
        font-size: 1.5rem;
        font-weight: 800;
        color: #0f291e;
        margin: 0;
    }

    /* Hero Banner */
    .hero-card {
        background: linear-gradient(135deg, #1b5e20 0%, #2e7d32 100%);
        border-radius: 24px;
        padding: 32px;
        color: #ffffff !important;
        box-shadow: 0 10px 25px rgba(46, 125, 50, 0.2);
        margin-bottom: 28px;
    }
    .hero-card h1 {
        color: #ffffff !important;
        font-size: 2.2rem !important;
        margin: 0 0 8px 0 !important;
    }
    .hero-card p {
        color: #e8f5e9 !important;
        font-size: 1.05rem;
        margin: 0;
    }

    /* Cards */
    div[data-testid="stVerticalBlock"] > div[style*="border"] {
        background-color: #ffffff !important;
        border-radius: 20px !important;
        border: 1px solid #e2e8f0 !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.03) !important;
        transition: all 0.2s ease !important;
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
        padding: 4px 12px;
        border-radius: 12px;
        font-size: 0.8rem;
        font-weight: 700;
        display: inline-block;
    }
    .badge-abgeholt {
        background-color: #ffebee;
        color: #c62828;
        padding: 4px 12px;
        border-radius: 12px;
        font-size: 0.8rem;
        font-weight: 700;
        display: inline-block;
    }
    .uploader-chip {
        background-color: #f1f5f9;
        color: #475569;
        padding: 4px 10px;
        border-radius: 10px;
        font-size: 0.8rem;
        font-weight: 600;
        display: inline-block;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 2. SUPABASE / DATENBANK & KI MODELL
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
    return None, "Kein Modell vorhanden"

def predict_category(image_bytes, model):
    if model is None:
        return None, 0.0
    img = Image.open(io.BytesIO(image_bytes)).convert('RGB').resize((224, 224))
    img_array = (np.expand_dims(np.array(img, dtype=np.float32), axis=0) / 127.5) - 1.0
    try:
        predictions = model(img_array, training=False).numpy()
    except Exception:
        predictions = model.predict(img_array)
    idx = np.argmax(predictions[0])
    return (CATEGORIES[idx] if idx < len(CATEGORIES) else CATEGORIES[0]), float(predictions[0][idx])

# ---------------------------------------------------------
# 3. SESSION STATE & ROUTING
# ---------------------------------------------------------
if "current_screen" not in st.session_state:
    st.session_state.current_screen = "home"
if "selected_item_id" not in st.session_state:
    st.session_state.selected_item_id = None
if "upload_key" not in st.session_state:
    st.session_state.upload_key = 0

df_items = load_data()
model, _ = load_keras_model()

# --- SIDEBAR (NAVIGATION & ACCOUNT) ---
with st.sidebar:
    st.markdown("### 🌱 FundSpot Menü")
    
    if st.button("🏠 Hauptseite (Entdecken)", use_container_width=True):
        st.session_state.current_screen = "home"
        st.rerun()
        
    if st.button("➕ Kleidungsstück hochladen", use_container_width=True, type="primary"):
        st.session_state.current_screen = "upload"
        st.rerun()
        
    if st.button("👤 Mein Konto & Fundstücke", use_container_width=True):
        st.session_state.current_screen = "account"
        st.rerun()

    st.divider()
    st.markdown("### ⚙️ Profil & Admin")
    user_account_name = st.text_input("Dein Name / Klasse", value="Johann")
    admin_pw_input = st.text_input("Admin-Passwort", type="password")
    ADMIN_PW = st.secrets.get("ADMIN_PASSWORD", "admin123")
    is_admin = (admin_pw_input == ADMIN_PW)
    if is_admin:
        st.success("🔓 Admin-Rechte aktiv")

# --- HEADER BAR ---
st.markdown("""
<div class="brand-header">
    <div class="brand-logo">🌱</div>
    <div class="brand-title">FundSpot – Schul-Fundbüro</div>
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 4. SCREEN 1: HAUPTSEITE (HOME)
# ---------------------------------------------------------
if st.session_state.current_screen == "home":
    st.markdown("""
    <div class="hero-card">
        <h1>Gefundenes wiederentdecken.</h1>
        <p>Suche nach verlorenen Gegenständen an deiner Schule oder trage gefundene Sachen ein.</p>
    </div>
    """, unsafe_allow_html=True)

    c1, c2, c3 = st.columns([2, 1, 1])
    with c1:
        search_q = st.text_input("🔍 Suchbegriff", placeholder="z. B. Jacke, Sportbeutel...")
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
        st.info("Keine Fundstücke gefunden.")
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
                    st.markdown(f'<span class="uploader-chip">👤 {row.get("uploader", "Anonym")}</span>', unsafe_allow_html=True)
                    st.caption(f"📍 {row['fundort']} (Raum {row['raum']})")
                    
                    if st.button("🔎 Kleidungsstück anschauen", key=f"btn_{row['id']}", use_container_width=True):
                        st.session_state.selected_item_id = row['id']
                        st.session_state.current_screen = "detail"
                        st.rerun()

# ---------------------------------------------------------
# 5. SCREEN 2: DETAILANSICHT
# ---------------------------------------------------------
elif st.session_state.current_screen == "detail":
    if st.button("⬅️ Zurück zur Hauptseite"):
        st.session_state.current_screen = "home"
        st.rerun()
        
    item_rows = df_items[df_items["id"] == st.session_state.selected_item_id]
    if item_rows.empty:
        st.error("Gegenstand nicht gefunden.")
    else:
        item = item_rows.iloc[0]
        st.markdown(f"## 🔎 {item['titel']}")
        
        col_left, col_right = st.columns([1, 1])
        with col_left:
            if pd.notna(item["bild_base64"]) and str(item["bild_base64"]).startswith("data:image"):
                st.image(item["bild_base64"], use_container_width=True)
            else:
                st.info("Kein Foto vorhanden.")
                
        with col_right:
            status_class = "badge-offen" if item["status"] == "Offen" else "badge-abgeholt"
            st.markdown(f'<span class="{status_class}" style="font-size: 1rem;">Status: {item["status"]}</span>', unsafe_allow_html=True)
            st.write("")
            st.markdown(f"**👤 Hochgeladen von:** {item.get('uploader', 'Anonym')}")
            st.markdown(f"**🏷️ Kategorie:** {item['kategorie']}")
            st.markdown(f"**📍 Fundort:** {item['fundort']} (Raum: {item['raum']})")
            st.markdown(f"**📅 Funddatum:** {item['datum']}")
            st.markdown(f"**📦 Abgabeort / Kontakt:** {item['kontakt']}")
            
            st.divider()
            if item["status"] == "Offen":
                if st.button("🙋‍♂️ Das gehört mir! (Als abgeholt markieren)", use_container_width=True, type="primary"):
                    if supabase:
                        supabase.table("fundstuecke").update({"status": "Abgeholt"}).eq("id", int(item["id"])).execute()
                    else:
                        df_items.loc[df_items["id"] == item["id"], "status"] = "Abgeholt"
                        df_items.to_csv("fundbuero_db.csv", index=False)
                    st.success("Erfolgreich als abgeholt markiert!")
                    st.rerun()

            if is_admin:
                if st.button("🗑️ Eintrag löschen (Admin)", use_container_width=True):
                    if supabase:
                        supabase.table("fundstuecke").delete().eq("id", int(item["id"])).execute()
                    else:
                        df_items_new = df_items[df_items["id"] != item["id"]]
                        df_items_new.to_csv("fundbuero_db.csv", index=False)
                    st.session_state.current_screen = "home"
                    st.rerun()

# ---------------------------------------------------------
# 6. SCREEN 3: HOCHLADEN
# ---------------------------------------------------------
elif st.session_state.current_screen == "upload":
    st.subheader("➕ Neues Fundstück eintragen")
    
    uploaded_file = st.file_uploader(
        "Foto vom Kleidungsstück hochladen", 
        type=["jpg", "jpeg", "png"], 
        key=f"upl_{st.session_state.upload_key}"
    )
    
    auto_cat = CATEGORIES[0]
    img_data_url = ""
    
    if uploaded_file is not None:
        file_bytes = uploaded_file.getvalue()
        pred_cat, conf = predict_category(file_bytes, model)
        if pred_cat:
            auto_cat = pred_cat
            st.info(f"🤖 KI-Vorschlag: **{auto_cat}** ({conf*100:.1f}% Sicher)")
        st.image(file_bytes, caption="Vorschau", width=200)
        img_data_url = f"data:image/jpeg;base64,{base64.b64encode(file_bytes).decode('utf-8')}"

    with st.form("add_form", clear_on_submit=True):
        titel = st.text_input("Bezeichnung *", placeholder="z. B. Rote Adidas Jacke")
        col1, col2 = st.columns(2)
        with col1:
            uploader_input = st.text_input("Dein Name / Klasse *", value=user_account_name)
            kategorie = st.selectbox("Kategorie", CATEGORIES, index=(CATEGORIES.index(auto_cat) if auto_cat in CATEGORIES else 0))
        with col2:
            fundort = st.text_input("Fundort *", placeholder="z. B. Pausenhof")
            raum = st.text_input("Raum", placeholder="z. B. B12")
        kontakt = st.text_input("Abgabeort / Kontakt", placeholder="z. B. Sekretariat")
        
        if st.form_submit_button("💾 Veröffentlichen", type="primary", use_container_width=True):
            if not titel or not fundort or not uploader_input:
                st.error("Bitte Titel, Fundort und deinen Namen eingeben!")
            else:
                new_row = {
                    "titel": titel, "kategorie": kategorie, "fundort": fundort,
                    "raum": raum, "datum": datetime.date.today().strftime("%Y-%m-%d"),
                    "status": "Offen", "kontakt": kontakt, "uploader": uploader_input,
                    "bild_base64": img_data_url
                }
                if supabase:
                    supabase.table("fundstuecke").insert(new_row).execute()
                else:
                    new_row["id"] = len(df_items) + 1
                    pd.concat([df_items, pd.DataFrame([new_row])], ignore_index=True).to_csv("fundbuero_db.csv", index=False)
                
                st.session_state.upload_key += 1
                st.session_state.current_screen = "home"
                st.rerun()

# ---------------------------------------------------------
# 7. SCREEN 4: KONTO / MEINE FUNDSTÜCKE
# ---------------------------------------------------------
elif st.session_state.current_screen == "account":
    st.subheader(f"👤 Konto von {user_account_name}")
    my_items = df_items[df_items["uploader"] == user_account_name]
    
    if my_items.empty:
        st.info("Du hast bisher noch keine Fundstücke hochgeladen.")
    else:
        st.write(f"Du hast bisher **{len(my_items)}** Gegenstände hochgeladen:")
        st.dataframe(my_items[["titel", "kategorie", "fundort", "datum", "status"]], use_container_width=True)
