import os
import io
import datetime
import base64
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from supabase import create_client, Client

# ---------------------------------------------------------
# 1. PAGE CONFIG
# ---------------------------------------------------------
st.set_page_config(
    page_title="FundSpot – Schul-Fundbüro",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------------------------------------------------
# 2. SUPABASE / DATENBANK
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

df_items = load_data()

# ---------------------------------------------------------
# 3. SIDEBAR (ACCOUNT & ADMIN)
# ---------------------------------------------------------
with st.sidebar:
    st.markdown("### ⚙️ Profil & Verwaltung")
    user_account_name = st.text_input("Dein Name / Klasse (Account)", value="Johann")
    
    st.divider()
    admin_pw_input = st.text_input("Admin-Passwort (zum Löschen)", type="password")
    ADMIN_PW = st.secrets.get("ADMIN_PASSWORD", "admin123")
    is_admin = (admin_pw_input == ADMIN_PW)
    
    if is_admin:
        st.success("🔓 Admin-Löschrechte aktiv!")
    else:
        st.caption("🔒 Nur Admin kann Fundstücke löschen.")

    st.divider()
    st.caption("⚡ Status: " + ("🟢 Cloud-DB Aktiv" if supabase else "🔴 Lokaler Modus"))

# ---------------------------------------------------------
# 4. ADMIN-LÖSCHEN & STATUS-AKTIONEN (DIALOG)
# ---------------------------------------------------------
@st.dialog("⚙️ Fundstück verwalten")
def item_manage_dialog(item_row):
    st.subheader(item_row["titel"])
    st.write(f"**Hochgeladen von:** {item_row.get('uploader', 'Anonym')}")
    st.write(f"**Fundort:** {item_row['fundort']} (Raum: {item_row['raum']})")
    st.write(f"**Status:** {item_row['status']}")
    st.divider()
    
    if item_row["status"] == "Offen":
        if st.button("🙋‍♂️ Als 'Abgeholt' markieren", use_container_width=True, type="primary"):
            if supabase:
                supabase.table("fundstuecke").update({"status": "Abgeholt"}).eq("id", int(item_row["id"])).execute()
            else:
                df_items.loc[df_items["id"] == item_row["id"], "status"] = "Abgeholt"
                df_items.to_csv("fundbuero_db.csv", index=False)
            st.success("Status auf 'Abgeholt' geändert!")
            st.rerun()

    if is_admin:
        if st.button("🗑️ Eintrag endgültig löschen", use_container_width=True):
            if supabase:
                supabase.table("fundstuecke").delete().eq("id", int(item_row["id"])).execute()
            else:
                df_new = df_items[df_items["id"] != item_row["id"]]
                df_new.to_csv("fundbuero_db.csv", index=False)
            st.success("Fundstück gelöscht!")
            st.rerun()

# Schnellzugriff für Admin über Sidebar
if is_admin and not df_items.empty:
    with st.sidebar:
        st.divider()
        st.markdown("### 🗑️ Quick-Delete (Admin)")
        delete_id = st.selectbox("Eintrag zum Löschen wählen:", df_items["id"].tolist(), format_func=lambda x: f"{x}: {df_items[df_items['id']==x]['titel'].values[0]}")
        if st.button(" Selected Item Löschen", type="primary"):
            if supabase:
                supabase.table("fundstuecke").delete().eq("id", int(delete_id)).execute()
            else:
                df_new = df_items[df_items["id"] != delete_id]
                df_new.to_csv("fundbuero_db.csv", index=False)
            st.success("Gelöscht!")
            st.rerun()

# ---------------------------------------------------------
# 5. HTML GENERIERUNG MIT DYNAMISCHEN DATEN
# ---------------------------------------------------------
items_html = ""
if df_items.empty:
    items_html = "<p style='color: #6b7280; grid-column: 1/-1;'>Noch keine Fundstücke in der Datenbank.</p>"
else:
    for _, row in df_items.iterrows():
        img_src = row['bild_base64'] if (pd.notna(row['bild_base64']) and str(row['bild_base64']).startswith("data:image")) else "https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=500&auto=format&fit=crop&q=60"
        status_color = "#e8f5e9; color: #1b5e20;" if row['status'] == 'Offen' else "#ffebee; color: #c62828;"
        
        items_html += f"""
        <div class="item-card">
            <img src="{img_src}" class="item-img" alt="{row['titel']}">
            <div style="background: {status_color}" class="badge-status">{row['status']}</div>
            <div class="card-title">{row['titel']}</div>
            <div class="uploader-tag">👤 von {row.get('uploader', 'Anonym')}</div>
            <div class="card-loc">📍 {row['fundort']} (Raum {row['raum']})</div>
        </div>
        """

html_code = f"""
<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        :root {{
            --primary: #1b5e20;
            --primary-light: #2e7d32;
            --primary-bg: #e8f5e9;
            --bg-main: #f8faf9;
            --card-bg: #ffffff;
            --text-main: #111827;
            --border: #e2e8f0;
            --radius-lg: 24px;
            --radius-md: 16px;
        }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; font-family: 'Plus Jakarta Sans', sans-serif; }}
        body {{ background-color: var(--bg-main); color: var(--text-main); padding: 12px; }}
        
        .brand-header {{
            background: var(--card-bg); border-radius: var(--radius-lg); padding: 16px 28px;
            display: flex; align-items: center; gap: 12px; border: 1px solid var(--border); margin-bottom: 20px;
        }}
        .brand-logo {{ background: var(--primary); color: white; width: 40px; height: 40px; border-radius: 12px; display: flex; align-items: center; justify-content: center; font-size: 1.2rem; }}
        .brand-title {{ font-size: 1.4rem; font-weight: 800; color: var(--primary); }}
        
        .hero-card {{
            background: linear-gradient(135deg, var(--primary) 0%, var(--primary-light) 100%);
            border-radius: var(--radius-lg); padding: 28px; color: white; margin-bottom: 24px;
        }}
        .hero-card h1 {{ font-size: 1.8rem; font-weight: 800; margin-bottom: 6px; }}
        
        .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 20px; }}
        .item-card {{
            background: white; border-radius: var(--radius-lg); border: 1px solid var(--border);
            padding: 16px; display: flex; flex-direction: column; gap: 10px;
        }}
        .item-img {{ width: 100%; height: 160px; border-radius: var(--radius-md); object-fit: cover; }}
        .badge-status {{ padding: 4px 12px; border-radius: 10px; font-size: 0.75rem; font-weight: 700; width: fit-content; }}
        .uploader-tag {{ background: #f1f5f9; color: #475569; padding: 4px 10px; border-radius: 8px; font-size: 0.8rem; font-weight: 600; width: fit-content; }}
        .card-title {{ font-size: 1.1rem; font-weight: 700; }}
        .card-loc {{ color: #6b7280; font-size: 0.85rem; }}
    </style>
</head>
<body>
    <div class="brand-header">
        <div class="brand-logo"><i class="fa-solid fa-leaf"></i></div>
        <div class="brand-title">FundSpot – Schul-Fundbüro</div>
    </div>

    <div class="hero-card">
        <h1>Gefundenes wiederentdecken</h1>
        <p>Hallo <b>{user_account_name}</b>! Hier sind alle aktuellen Fundstücke deiner Schule.</p>
    </div>

    <div class="grid">
        {items_html}
    </div>
</body>
</html>
"""

# HTML View anzeigen
components.html(html_code, height=650, scrolling=True)

# ---------------------------------------------------------
# 6. FORMULAR FÜR NEUES FUNDSTÜCK (MIT ACCOUNT-NAME)
# ---------------------------------------------------------
st.divider()
st.subheader("➕ Neues Fundstück hochladen")

with st.form("upload_form", clear_on_submit=True):
    titel = st.text_input("Bezeichnung des Fundstücks *", placeholder="z. B. Rote Nike Sportjacke")
    col1, col2 = st.columns(2)
    with col1:
        uploader_input = st.text_input("Hochgeladen von (Account) *", value=user_account_name)
        kategorie = st.selectbox("Kategorie", ["Kleidung", "Elektronik", "Bücher & Hefte", "Sonstiges"])
    with col2:
        fundort = st.text_input("Fundort *", placeholder="z. B. Pausenhof")
        raum = st.text_input("Raum", placeholder="z. B. B12")
        
    kontakt = st.text_input("Abgabeort / Kontakt", placeholder="z. B. Hausmeister / Seki")
    
    uploaded_file = st.file_uploader("Foto hochladen (optional)", type=["jpg", "png", "jpeg"])
    img_data_url = ""
    if uploaded_file is not None:
        base64_encoded = base64.b64encode(uploaded_file.getvalue()).decode('utf-8')
        img_data_url = f"data:image/jpeg;base64,{base64_encoded}"

    if st.form_submit_button("💾 Fundstück jetzt veröffentlichen", type="primary", use_container_width=True):
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
                df_items = pd.concat([df_items, pd.DataFrame([new_row])], ignore_index=True)
                df_items.to_csv("fundbuero_db.csv", index=False)
            
            st.success(f"🎉 Erfolgreich hinzugefügt als {uploader_input}!")
            st.rerun()
