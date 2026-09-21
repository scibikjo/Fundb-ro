import os
import datetime
import json
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from supabase import create_client, Client

# ---------------------------------------------------------
# 1. STREAMLIT CONFIG
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
        # Beispieldaten
        return pd.DataFrame([
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
                "bild_base64": "https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=500&auto=format&fit=crop&q=60"
            },
            {
                "id": 2,
                "titel": "Blaue Strickjacke",
                "kategorie": "Kleidung",
                "fundort": "Turnhalle",
                "raum": "Halle 2",
                "datum": "2026-09-21",
                "status": "Offen",
                "kontakt": "Hausmeister",
                "uploader": "Maria (10a)",
                "bild_base64": "https://images.unsplash.com/photo-1434389677669-e08b4cac3105?w=500&auto=format&fit=crop&q=60"
            }
        ])

df_items = load_data()

# ---------------------------------------------------------
# 3. SIDEBAR (PROFILE & ADMIN DELETION)
# ---------------------------------------------------------
with st.sidebar:
    st.markdown("### ⚙️ Konto & Admin")
    user_account_name = st.text_input("Dein Name / Klasse (Account)", value="Johann (8b)")
    
    st.divider()
    admin_pw_input = st.text_input("Admin-Passwort zum Löschen", type="password")
    ADMIN_PW = st.secrets.get("ADMIN_PASSWORD", "admin123")
    is_admin = (admin_pw_input == ADMIN_PW)
    
    if is_admin:
        st.success("🔓 Admin-Löschrechte aktiv!")
        st.divider()
        st.markdown("### 🗑️ Eintrag löschen")
        if not df_items.empty:
            delete_id = st.selectbox("Fundstück wählen:", df_items["id"].tolist(), format_func=lambda x: f"{x}: {df_items[df_items['id']==x]['titel'].values[0]}")
            if st.button("🗑️ Endgültig Löschen", type="primary", use_container_width=True):
                if supabase:
                    supabase.table("fundstuecke").delete().eq("id", int(delete_id)).execute()
                else:
                    df_items = df_items[df_items["id"] != delete_id]
                    df_items.to_csv("fundbuero_db.csv", index=False)
                st.success("Erfolgreich gelöscht!")
                st.rerun()
    else:
        st.caption("🔒 Nur Admins können Einträge löschen.")

# Daten in JSON umwandeln für JavaScript
items_json = df_items.to_json(orient="records")

# ---------------------------------------------------------
# 4. VOLLSTÄNDIGES HTML / JS FRONTEND
# ---------------------------------------------------------
html_code = f"""
<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>FundSpot – Schul-Fundbüro</title>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        :root {{
            --primary: #1b5e20;
            --primary-light: #2e7d32;
            --primary-bg: #e8f5e9;
            --bg-main: #f4f7f5;
            --card-bg: #ffffff;
            --text-main: #111827;
            --text-muted: #6b7280;
            --border: #e5e7eb;
            --radius-lg: 24px;
            --radius-md: 16px;
            --shadow-sm: 0 4px 12px rgba(0,0,0,0.03);
            --shadow-hover: 0 12px 28px rgba(46, 125, 50, 0.12);
        }}

        * {{ box-sizing: border-box; margin: 0; padding: 0; font-family: 'Plus Jakarta Sans', sans-serif; }}
        body {{ background-color: var(--bg-main); color: var(--text-main); padding: 16px; min-height: 100vh; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}

        /* Header */
        .app-header {{
            background: var(--card-bg); border-radius: var(--radius-lg); padding: 16px 28px;
            display: flex; justify-content: space-between; align-items: center;
            box-shadow: var(--shadow-sm); border: 1px solid var(--border); margin-bottom: 24px;
        }}
        .brand-logo {{ display: flex; align-items: center; gap: 12px; font-weight: 800; font-size: 1.4rem; color: var(--primary); }}
        .brand-icon {{ background: var(--primary); color: white; width: 42px; height: 42px; border-radius: 12px; display: flex; align-items: center; justify-content: center; font-size: 1.2rem; }}
        .nav-links {{ display: flex; gap: 8px; }}
        .nav-btn {{
            background: transparent; border: none; padding: 10px 18px; border-radius: var(--radius-md);
            font-weight: 600; color: var(--text-muted); cursor: pointer; transition: all 0.2s;
            display: flex; align-items: center; gap: 8px;
        }}
        .nav-btn:hover, .nav-btn.active {{ background: var(--primary-bg); color: var(--primary); }}

        /* Hero */
        .hero-card {{
            background: linear-gradient(135deg, var(--primary) 0%, var(--primary-light) 100%);
            border-radius: var(--radius-lg); padding: 36px; color: white;
            box-shadow: 0 12px 30px rgba(27, 94, 32, 0.2); margin-bottom: 28px;
        }}
        .hero-card h1 {{ font-size: 2rem; font-weight: 800; margin-bottom: 8px; }}
        .hero-card p {{ color: #e8f5e9; font-size: 1.05rem; }}

        /* Filters */
        .filter-bar {{ display: grid; grid-template-columns: 2fr 1fr 1fr; gap: 16px; margin-bottom: 28px; }}
        .input-group {{
            background: white; border: 1px solid var(--border); border-radius: var(--radius-md);
            padding: 12px 18px; display: flex; align-items: center; gap: 10px; box-shadow: var(--shadow-sm);
        }}
        .input-group input, .input-group select {{ border: none; outline: none; width: 100%; font-size: 0.95rem; background: transparent; }}

        /* Grid */
        .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 24px; }}
        .item-card {{
            background: white; border-radius: var(--radius-lg); border: 1px solid var(--border);
            padding: 18px; box-shadow: var(--shadow-sm); transition: all 0.25s ease; cursor: pointer;
            display: flex; flex-direction: column; gap: 12px;
        }}
        .item-card:hover {{ transform: translateY(-6px); box-shadow: var(--shadow-hover); border-color: #a5d6a7; }}
        .item-img {{ width: 100%; height: 180px; border-radius: var(--radius-md); object-fit: cover; background: #f1f5f9; }}
        .badge-status {{ padding: 4px 12px; border-radius: 12px; font-size: 0.78rem; font-weight: 700; width: fit-content; }}
        .badge-offen {{ background: var(--primary-bg); color: var(--primary); }}
        .badge-abgeholt {{ background: #ffebee; color: #c62828; }}
        .uploader-tag {{ background: #f1f5f9; color: #475569; padding: 4px 10px; border-radius: 10px; font-size: 0.8rem; font-weight: 600; width: fit-content; }}
        .card-title {{ font-size: 1.15rem; font-weight: 700; }}
        .card-loc {{ color: var(--text-muted); font-size: 0.88rem; }}

        .screen {{ display: none; }}
        .screen.active {{ display: block; }}

        /* Form & Detail */
        .form-card {{
            background: white; border-radius: var(--radius-lg); padding: 32px;
            border: 1px solid var(--border); max-width: 650px; margin: 0 auto; box-shadow: var(--shadow-sm);
        }}
        .btn-primary {{
            background: var(--primary); color: white; border: none; padding: 14px 24px;
            border-radius: var(--radius-md); font-weight: 700; font-size: 1rem; cursor: pointer;
            width: 100%; transition: background 0.2s;
        }}
        .btn-primary:hover {{ background: var(--primary-light); }}
        .back-btn {{ background: #e2e8f0; border: none; padding: 8px 16px; border-radius: var(--radius-md); font-weight: 600; cursor: pointer; margin-bottom: 20px; }}
    </style>
</head>
<body>

<div class="container">
    <header class="app-header">
        <div class="brand-logo">
            <div class="brand-icon"><i class="fa-solid fa-leaf"></i></div>
            <span>FundSpot</span>
        </div>
        <nav class="nav-links">
            <button class="nav-btn active" id="btn-home" onclick="switchScreen('home')"><i class="fa-solid fa-compass"></i> Entdecken</button>
        </nav>
    </header>

    <!-- MAIN SCREEN -->
    <main id="screen-home" class="screen active">
        <div class="hero-card">
            <h1>Gefundenes wiederentdecken</h1>
            <p>Willkommen zurück, <b>{user_account_name}</b>! Durchsuche das digitale Fundbüro.</p>
        </div>

        <div class="filter-bar">
            <div class="input-group">
                <i class="fa-solid fa-magnifying-glass" style="color: var(--text-muted);"></i>
                <input type="text" id="searchInput" placeholder="Suchen nach Jacke, Tasche..." oninput="filterItems()">
            </div>
            <div class="input-group">
                <select id="catSelect" onchange="filterItems()">
                    <option value="Alle">Alle Kategorien</option>
                    <option value="Kleidung">Kleidung</option>
                    <option value="Elektronik">Elektronik</option>
                    <option value="Bücher & Hefte">Bücher & Hefte</option>
                    <option value="Sonstiges">Sonstiges</option>
                </select>
            </div>
            <div class="input-group">
                <select id="statusSelect" onchange="filterItems()">
                    <option value="Alle">Alle Status</option>
                    <option value="Offen">Offen</option>
                    <option value="Abgeholt">Abgeholt</option>
                </select>
            </div>
        </div>

        <div class="grid" id="itemsGrid"></div>
    </main>

    <!-- DETAIL SCREEN -->
    <main id="screen-detail" class="screen">
        <button class="back-btn" onclick="switchScreen('home')"><i class="fa-solid fa-arrow-left"></i> Zurück</button>
        <div class="form-card" id="detailContent"></div>
    </main>
</div>

<script>
    let items = {items_json};

    function renderItems(filtered) {{
        const grid = document.getElementById("itemsGrid");
        grid.innerHTML = "";

        if(!filtered || filtered.length === 0) {{
            grid.innerHTML = "<p style='color: var(--text-muted); grid-column: 1/-1;'>Keine Fundstücke gefunden.</p>";
            return;
        }}

        filtered.forEach(item => {{
            const card = document.createElement("div");
            card.className = "item-card";
            card.onclick = () => openDetail(item.id);
            
            const badgeClass = item.status === "Offen" ? "badge-offen" : "badge-abgeholt";
            const img = (item.bild_base64 && item.bild_base64.length > 10) ? item.bild_base64 : "https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=500&auto=format&fit=crop&q=60";
            
            card.innerHTML = `
                <img src="${{img}}" class="item-img" alt="${{item.titel}}">
                <div class="badge-status ${{badgeClass}}">${{item.status}}</div>
                <div class="card-title">${{item.titel}}</div>
                <div class="uploader-tag">👤 von ${{item.uploader || 'Anonym'}}</div>
                <div class="card-loc">📍 ${{item.fundort}} (Raum ${{item.raum || '-'}})</div>
            `;
            grid.appendChild(card);
        }});
    }}

    function filterItems() {{
        const q = document.getElementById("searchInput").value.toLowerCase();
        const cat = document.getElementById("catSelect").value;
        const status = document.getElementById("statusSelect").value;

        const res = items.filter(i => {{
            const matchQ = (i.titel && i.titel.toLowerCase().includes(q)) || (i.fundort && i.fundort.toLowerCase().includes(q));
            const matchCat = (cat === "Alle" || i.kategorie === cat);
            const matchStatus = (status === "Alle" || i.status === status);
            return matchQ && matchCat && matchStatus;
        }});

        renderItems(res);
    }}

    function openDetail(id) {{
        const item = items.find(i => i.id == id);
        if(!item) return;

        const img = (item.bild_base64 && item.bild_base64.length > 10) ? item.bild_base64 : "https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=500&auto=format&fit=crop&q=60";
        const badgeClass = item.status === "Offen" ? "badge-offen" : "badge-abgeholt";

        const detailBox = document.getElementById("detailContent");
        detailBox.innerHTML = `
            <img src="${{img}}" style="width: 100%; height: 260px; object-fit: cover; border-radius: var(--radius-md); margin-bottom: 20px;">
            <h2 style="margin-bottom: 12px;">${{item.titel}}</h2>
            <p style="margin: 8px 0;"><strong>Status:</strong> <span class="badge-status ${{badgeClass}}">${{item.status}}</span></p>
            <p style="margin: 8px 0;"><strong>Hochgeladen von:</strong> ${{item.uploader || 'Anonym'}}</p>
            <p style="margin: 8px 0;"><strong>Kategorie:</strong> ${{item.kategorie}}</p>
            <p style="margin: 8px 0;"><strong>Fundort:</strong> ${{item.fundort}} (Raum ${{item.raum || '-'}})</p>
            <p style="margin: 8px 0;"><strong>Abgabeort / Kontakt:</strong> ${{item.kontakt || 'Sekretariat'}}</p>
            <p style="margin: 8px 0; color: var(--text-muted); font-size: 0.85rem;"><strong>Funddatum:</strong> ${{item.datum}}</p>
        `;
        switchScreen('detail');
    }}

    function switchScreen(name) {{
        document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
        document.getElementById('screen-' + name).classList.add('active');
    }}

    // Erstes Laden
    renderItems(items);
</script>

</body>
</html>
"""

# Rendern des vollständigen HTML-Designs
components.html(html_code, height=750, scrolling=True)

# ---------------------------------------------------------
# 5. STREAMLIT FORMULAR FÜR HOCHLADEN
# ---------------------------------------------------------
st.divider()
st.markdown("### ➕ Neues Fundstück eintragen")

with st.form("upload_form", clear_on_submit=True):
    titel = st.text_input("Bezeichnung des Kleidungsstücks / Gegenstands *", placeholder="z. B. Schwarze North Face Jacke")
    col1, col2 = st.columns(2)
    with col1:
        uploader_input = st.text_input("Dein Name / Klasse (Uploader) *", value=user_account_name)
        kategorie = st.selectbox("Kategorie", ["Kleidung", "Elektronik", "Bücher & Hefte", "Sonstiges"])
    with col2:
        fundort = st.text_input("Fundort *", placeholder="z. B. Pausenhof")
        raum = st.text_input("Raum / Bereich", placeholder="z. B. B-Trakt")
        
    kontakt = st.text_input("Abgabeort / Kontakt", placeholder="z. B. Sekretariat")
    uploaded_file = st.file_uploader("Foto hinzufügen", type=["jpg", "png", "jpeg"])
    
    img_data_url = ""
    if uploaded_file is not None:
        import base64
        base64_encoded = base64.b64encode(uploaded_file.getvalue()).decode('utf-8')
        img_data_url = f"data:image/jpeg;base64,{base64_encoded}"

    if st.form_submit_button("💾 Fundstück veröffentlichen", type="primary", use_container_width=True):
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
            
            st.success(f"🎉 Fundstück veröffentlicht als {uploader_input}!")
            st.rerun()
