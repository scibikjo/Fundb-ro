import os
import json
import datetime
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from supabase import create_client, Client

# =========================================================
# 1. STREAMLIT PAGE CONFIG (Maximaler Platz)
# =========================================================
st.set_page_config(
    page_title="FundSpot – Schul-Fundbüro",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Hide Streamlit Chrome (Header, Footer, Padding) for full-screen web app experience
st.markdown("""
    <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        .block-container {padding: 0rem !important; max-width: 100% !important;}
        iframe {display: block; border: none; width: 100vw !important; height: 100vh !important;}
    </style>
""", unsafe_allow_html=True)

# =========================================================
# 2. DATABASE / BACKEND LOGIC
# =========================================================
@st.cache_resource
def get_supabase_client():
    url = st.secrets.get("SUPABASE_URL")
    key = st.secrets.get("SUPABASE_KEY")
    if url and key:
        try:
            return create_client(url, key)
        except Exception:
            return None
    return None

supabase: Client = get_supabase_client()

def fetch_all_items():
    if supabase:
        try:
            res = supabase.table("fundstuecke").select("*").order("id", desc=True).execute()
            return res.data
        except Exception as e:
            st.error(f"Datenbankfehler: {e}")
            return []
    else:
        # Local CSV Fallback
        csv_file = "fundbuero_db.csv"
        if os.path.exists(csv_file):
            df = pd.read_csv(csv_file)
            return df.to_dict(orient="records")
        else:
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
                    "bild_base64": "https://images.unsplash.com/photo-1434389677669-e08b4cac3105?w=600&auto=format&fit=crop&q=80"
                }
            ]
            pd.DataFrame(default_data).to_csv(csv_file, index=False)
            return default_data

# Handle incoming actions from Frontend (Add / Delete)
query_params = st.query_params

if "action" in query_params:
    action = query_params["action"]
    
    if action == "add":
        try:
            payload = json.loads(query_params.get("payload", "{}"))
            payload["datum"] = datetime.date.today().strftime("%Y-%m-%d")
            payload["status"] = "Offen"
            
            if supabase:
                supabase.table("fundstuecke").insert(payload).execute()
            else:
                items = fetch_all_items()
                payload["id"] = max([i.get("id", 0) for i in items] + [0]) + 1
                items.insert(0, payload)
                pd.DataFrame(items).to_csv("fundbuero_db.csv", index=False)
        except Exception as e:
            st.error(f"Fehler beim Speichern: {e}")
            
        st.query_params.clear()
        st.rerun()

    elif action == "delete":
        item_id = query_params.get("id")
        if item_id:
            if supabase:
                supabase.table("fundstuecke").delete().eq("id", int(item_id)).execute()
            else:
                items = fetch_all_items()
                items = [i for i in items if str(i.get("id")) != str(item_id)]
                pd.DataFrame(items).to_csv("fundbuero_db.csv", index=False)
                
        st.query_params.clear()
        st.rerun()

# Load current data state
current_data = fetch_all_items()
data_json = json.dumps(current_data, ensure_ascii=False)

# =========================================================
# 3. FULL HTML / CSS / JAVASCRIPT FRONTEND (PURE DESIGN)
# =========================================================
html_template = f"""
<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>FundSpot – Digitales Schul-Fundbüro</title>
    <!-- Fonts & Icons -->
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    
    <style>
        :root {{
            --primary: #1b5e20;
            --primary-light: #2e7d32;
            --primary-bg: #e8f5e9;
            --accent: #4caf50;
            --bg-main: #f4f7f5;
            --card-bg: #ffffff;
            --text-main: #111827;
            --text-muted: #6b7280;
            --border: #e5e7eb;
            --danger: #ef4444;
            --danger-bg: #fef2f2;
            --radius-lg: 24px;
            --radius-md: 16px;
            --radius-sm: 10px;
            --shadow-sm: 0 4px 12px rgba(0,0,0,0.03);
            --shadow-md: 0 8px 24px rgba(0,0,0,0.06);
            --shadow-hover: 0 16px 32px rgba(46, 125, 50, 0.12);
        }}

        * {{ box-sizing: border-box; margin: 0; padding: 0; font-family: 'Plus Jakarta Sans', sans-serif; }}
        body {{ background-color: var(--bg-main); color: var(--text-main); padding: 24px; min-height: 100vh; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}

        /* Navigation Header */
        .app-header {{
            background: var(--card-bg);
            border-radius: var(--radius-lg);
            padding: 16px 28px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            box-shadow: var(--shadow-sm);
            border: 1px solid var(--border);
            margin-bottom: 24px;
        }}
        .brand-logo {{ display: flex; align-items: center; gap: 12px; font-weight: 800; font-size: 1.4rem; color: var(--primary); }}
        .brand-icon {{ background: var(--primary); color: white; width: 44px; height: 44px; border-radius: 14px; display: flex; align-items: center; justify-content: center; font-size: 1.25rem; }}
        
        .nav-actions {{ display: flex; align-items: center; gap: 12px; }}
        .nav-btn {{
            background: transparent; border: none; padding: 10px 20px; border-radius: var(--radius-md);
            font-weight: 700; color: var(--text-muted); cursor: pointer; transition: all 0.2s;
            display: flex; align-items: center; gap: 8px; font-size: 0.95rem;
        }}
        .nav-btn:hover, .nav-btn.active {{ background: var(--primary-bg); color: var(--primary); }}
        .nav-btn-primary {{ background: var(--primary); color: white !important; }}
        .nav-btn-primary:hover {{ background: var(--primary-light) !important; transform: translateY(-2px); }}

        /* Account & Admin Bar */
        .user-bar {{
            background: white; border-radius: var(--radius-md); padding: 12px 20px;
            margin-bottom: 24px; border: 1px solid var(--border); display: flex;
            align-items: center; justify-content: space-between; gap: 16px; flex-wrap: wrap;
        }}
        .user-field {{ display: flex; align-items: center; gap: 10px; font-size: 0.9rem; font-weight: 600; color: var(--text-muted); }}
        .user-field input {{
            border: 1px solid var(--border); padding: 6px 12px; border-radius: var(--radius-sm);
            outline: none; font-weight: 600; color: var(--text-main); background: #f8fafc;
        }}
        .user-field input:focus {{ border-color: var(--primary); background: white; }}

        /* Hero Header */
        .hero-card {{
            background: linear-gradient(135deg, var(--primary) 0%, var(--primary-light) 100%);
            border-radius: var(--radius-lg); padding: 40px; color: white;
            box-shadow: 0 12px 32px rgba(27, 94, 32, 0.2); margin-bottom: 28px;
            position: relative; overflow: hidden;
        }}
        .hero-card h1 {{ font-size: 2.2rem; font-weight: 800; margin-bottom: 10px; letter-spacing: -0.5px; }}
        .hero-card p {{ color: #e8f5e9; font-size: 1.1rem; max-width: 600px; line-height: 1.5; }}
        .hero-decoration {{ position: absolute; right: -20px; bottom: -30px; font-size: 15rem; color: rgba(255,255,255,0.06); pointer-events: none; }}

        /* Filter Controls */
        .filter-bar {{ display: grid; grid-template-columns: 2fr 1fr 1fr; gap: 16px; margin-bottom: 28px; }}
        .input-group {{
            background: white; border: 1px solid var(--border); border-radius: var(--radius-md);
            padding: 12px 18px; display: flex; align-items: center; gap: 12px; box-shadow: var(--shadow-sm);
            transition: all 0.2s;
        }}
        .input-group:focus-within {{ border-color: var(--primary); box-shadow: 0 0 0 3px rgba(46, 125, 50, 0.1); }}
        .input-group input, .input-group select {{ border: none; outline: none; width: 100%; font-size: 0.95rem; background: transparent; font-weight: 500; }}

        /* Item Grid & Cards */
        .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 24px; }}
        .item-card {{
            background: white; border-radius: var(--radius-lg); border: 1px solid var(--border);
            padding: 18px; box-shadow: var(--shadow-sm); transition: all 0.25s ease; cursor: pointer;
            display: flex; flex-direction: column; gap: 14px; position: relative; overflow: hidden;
        }}
        .item-card:hover {{ transform: translateY(-6px); box-shadow: var(--shadow-hover); border-color: #a5d6a7; }}
        .item-img {{ width: 100%; height: 190px; border-radius: var(--radius-md); object-fit: cover; background: #f1f5f9; }}
        
        .card-badges {{ display: flex; justify-content: space-between; align-items: center; }}
        .badge-status {{ padding: 4px 12px; border-radius: 20px; font-size: 0.75rem; font-weight: 800; text-transform: uppercase; letter-spacing: 0.5px; }}
        .badge-offen {{ background: var(--primary-bg); color: var(--primary); }}
        .badge-abgeholt {{ background: #ffebee; color: #c62828; }}
        
        .uploader-tag {{ background: #f1f5f9; color: #475569; padding: 4px 10px; border-radius: 8px; font-size: 0.8rem; font-weight: 600; display: inline-flex; align-items: center; gap: 6px; }}
        .card-title {{ font-size: 1.2rem; font-weight: 800; color: var(--text-main); line-height: 1.3; }}
        .card-loc {{ color: var(--text-muted); font-size: 0.9rem; display: flex; align-items: center; gap: 6px; }}

        .btn-delete-item {{
            background: var(--danger-bg); color: var(--danger); border: 1px solid #fca5a5;
            padding: 8px 14px; border-radius: var(--radius-sm); font-size: 0.85rem; font-weight: 700;
            cursor: pointer; transition: all 0.2s; display: flex; align-items: center; justify-content: center; gap: 6px; width: 100%; margin-top: 4px;
        }}
        .btn-delete-item:hover {{ background: var(--danger); color: white; }}

        /* View Screens */
        .screen {{ display: none; }}
        .screen.active {{ display: block; }}

        /* Form Container */
        .form-card {{
            background: white; border-radius: var(--radius-lg); padding: 36px;
            border: 1px solid var(--border); max-width: 680px; margin: 0 auto; box-shadow: var(--shadow-md);
        }}
        .form-header {{ margin-bottom: 24px; text-align: center; }}
        .form-header h2 {{ font-size: 1.8rem; font-weight: 800; color: var(--primary); margin-bottom: 6px; }}
        .form-header p {{ color: var(--text-muted); font-size: 0.95rem; }}

        .form-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 20px; }}
        .form-group {{ display: flex; flex-direction: column; gap: 8px; margin-bottom: 16px; }}
        .form-group.full {{ grid-column: 1 / -1; }}
        .form-group label {{ font-weight: 700; font-size: 0.88rem; color: #374151; }}
        .form-group input, .form-group select, .form-group textarea {{
            width: 100%; padding: 12px 16px; border: 1px solid var(--border); border-radius: var(--radius-md);
            outline: none; font-size: 0.95rem; font-weight: 500; background: #f9fafb; transition: all 0.2s;
        }}
        .form-group input:focus, .form-group select:focus {{ border-color: var(--primary); background: white; box-shadow: 0 0 0 3px rgba(46, 125, 50, 0.1); }}

        .file-upload-box {{
            border: 2px dashed var(--border); border-radius: var(--radius-md); padding: 24px;
            text-align: center; cursor: pointer; background: #fafafa; transition: all 0.2s;
        }}
        .file-upload-box:hover {{ border-color: var(--primary); background: var(--primary-bg); }}
        .file-upload-box i {{ font-size: 2rem; color: var(--primary); margin-bottom: 8px; }}

        .btn-submit {{
            background: var(--primary); color: white; border: none; padding: 16px 28px;
            border-radius: var(--radius-md); font-weight: 800; font-size: 1rem; cursor: pointer;
            width: 100%; transition: all 0.2s; box-shadow: 0 4px 12px rgba(27, 94, 32, 0.2);
        }}
        .btn-submit:hover {{ background: var(--primary-light); transform: translateY(-2px); }}

        .back-btn {{
            background: white; border: 1px solid var(--border); padding: 10px 20px;
            border-radius: var(--radius-md); font-weight: 700; cursor: pointer; margin-bottom: 24px;
            display: inline-flex; align-items: center; gap: 8px; color: var(--text-muted); transition: all 0.2s;
        }}
        .back-btn:hover {{ color: var(--primary); border-color: var(--primary); }}

        #imgPreview {{ width: 100%; max-height: 200px; object-fit: cover; border-radius: var(--radius-md); margin-top: 12px; display: none; }}
    </style>
</head>
<body>

<div class="container">
    <!-- Top Navigation Header -->
    <header class="app-header">
        <div class="brand-logo">
            <div class="brand-icon"><i class="fa-solid fa-leaf"></i></div>
            <span>FundSpot</span>
        </div>
        <div class="nav-actions">
            <button class="nav-btn active" id="nav-home" onclick="switchScreen('home')">
                <i class="fa-solid fa-compass"></i> Entdecken
            </button>
            <button class="nav-btn nav-btn-primary" id="nav-add" onclick="switchScreen('add')">
                <i class="fa-solid fa-plus"></i> Fundstück melden
            </button>
        </div>
    </header>

    <!-- Account & Admin Toolbar -->
    <div class="user-bar">
        <div class="user-field">
            <i class="fa-solid fa-user-circle" style="font-size: 1.2rem; color: var(--primary);"></i>
            <span>Dein Name / Klasse:</span>
            <input type="text" id="accountNameInput" value="Johann (8b)" onchange="updateAccountName()">
        </div>
        <div class="user-field">
            <i class="fa-solid fa-key" style="font-size: 1.1rem; color: var(--text-muted);"></i>
            <span>Admin-Passcode:</span>
            <input type="password" id="adminPassInput" placeholder="Passwort für Löschrechte" oninput="checkAdminRights()">
        </div>
    </div>

    <!-- MAIN DISCOVERY SCREEN -->
    <main id="screen-home" class="screen active">
        <div class="hero-card">
            <div class="hero-decoration"><i class="fa-solid fa-box-open"></i></div>
            <h1>Gefundenes wiederentdecken</h1>
            <p>Willkommen beim digitalen Fundbüro! Hier findest du alle verlorenen Gegenstände der Schule auf einen Blick.</p>
        </div>

        <div class="filter-bar">
            <div class="input-group">
                <i class="fa-solid fa-magnifying-glass" style="color: var(--text-muted);"></i>
                <input type="text" id="searchInput" placeholder="Suchen nach Jacke, Rucksack, Halle..." oninput="filterItems()">
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

    <!-- DETAIL VIEW SCREEN -->
    <main id="screen-detail" class="screen">
        <button class="back-btn" onclick="switchScreen('home')"><i class="fa-solid fa-arrow-left"></i> Zurück zur Übersicht</button>
        <div class="form-card" id="detailCard"></div>
    </main>

    <!-- ADD NEW ITEM SCREEN -->
    <main id="screen-add" class="screen">
        <button class="back-btn" onclick="switchScreen('home')"><i class="fa-solid fa-arrow-left"></i> Abbrechen</button>
        <div class="form-card">
            <div class="form-header">
                <h2>Neues Fundstück eintragen</h2>
                <p>Hilf mit, Gefundenes schnell wieder zu seinem Besitzer zu bringen.</p>
            </div>

            <form onsubmit="handleFormSubmit(event)">
                <div class="form-group full">
                    <label>Bezeichnung des Gegenstands *</label>
                    <input type="text" id="formTitel" placeholder="z. B. Grüner Nike Rucksack, Blaue Jacke" required>
                </div>

                <div class="form-grid">
                    <div class="form-group">
                        <label>Kategorie</label>
                        <select id="formKategorie">
                            <option value="Sonstiges">Sonstiges</option>
                            <option value="Kleidung">Kleidung</option>
                            <option value="Elektronik">Elektronik</option>
                            <option value="Bücher & Hefte">Bücher & Hefte</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Dein Name / Klasse *</label>
                        <input type="text" id="formUploader" required readonly style="background: #e2e8f0;">
                    </div>
                </div>

                <div class="form-grid">
                    <div class="form-group">
                        <label>Fundort *</label>
                        <input type="text" id="formFundort" placeholder="z. B. Mensa, Turnhalle" required>
                    </div>
                    <div class="form-group">
                        <label>Raum / Details</label>
                        <input type="text" id="formRaum" placeholder="z. B. Raum 102, Halle 2">
                    </div>
                </div>

                <div class="form-group full">
                    <label>Abgabeort / Kontaktperson</label>
                    <input type="text" id="formKontakt" placeholder="z. B. Hausmeister, Sekretariat, Herr Müller">
                </div>

                <div class="form-group full">
                    <label>Foto hinzufügen</label>
                    <div class="file-upload-box" onclick="document.getElementById('fileInput').click()">
                        <i class="fa-solid fa-cloud-arrow-up"></i>
                        <p style="font-weight: 700; color: var(--text-main);">Klicke hier, um ein Bild hochzuladen</p>
                        <p style="font-size: 0.8rem; color: var(--text-muted);">PNG, JPG oder JPEG</p>
                        <input type="file" id="fileInput" accept="image/*" style="display:none" onchange="handleFileSelect(event)">
                    </div>
                    <img id="imgPreview" alt="Vorschau">
                </div>

                <button type="submit" class="btn-submit">🚀 Fundstück veröffentlichen</button>
            </form>
        </div>
    </main>
</div>

<script>
    // Load dataset from Python Streamlit backend
    let items = {data_json};
    let base64Image = "";
    let isAdmin = false;
    const ADMIN_PW = "admin123";

    function updateAccountName() {{
        const name = document.getElementById("accountNameInput").value;
        document.getElementById("formUploader").value = name || "Anonym";
    }}

    function checkAdminRights() {{
        const pass = document.getElementById("adminPassInput").value;
        isAdmin = (pass === ADMIN_PW);
        filterItems(); // Re-render to show/hide delete buttons
    }}

    function renderItems(filteredList) {{
        const grid = document.getElementById("itemsGrid");
        grid.innerHTML = "";

        if (!filteredList || filteredList.length === 0) {{
            grid.innerHTML = `
                <div style="grid-column: 1/-1; text-align: center; padding: 48px; color: var(--text-muted);">
                    <i class="fa-solid fa-box-open" style="font-size: 3rem; margin-bottom: 12px; opacity: 0.5;"></i>
                    <p style="font-size: 1.1rem; font-weight: 600;">Keine Fundstücke gefunden.</p>
                </div>
            `;
            return;
        }}

        filteredList.forEach(item => {{
            const card = document.createElement("div");
            card.className = "item-card";
            
            const badgeClass = item.status === "Offen" ? "badge-offen" : "badge-abgeholt";
            const defaultImg = "https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=600&auto=format&fit=crop&q=80";
            const imgSrc = (item.bild_base64 && item.bild_base64.length > 20) ? item.bild_base64 : defaultImg;

            let deleteBtnHtml = "";
            if (isAdmin) {{
                deleteBtnHtml = `
                    <button class="btn-delete-item" onclick="deleteItem(event, ${{item.id}})">
                        <i class="fa-solid fa-trash"></i> Endgültig Löschen
                    </button>
                `;
            }}

            card.innerHTML = `
                <div onclick="openDetail(${{item.id}})" style="display:flex; flex-direction:column; gap:12px; cursor:pointer;">
                    <img src="${{imgSrc}}" class="item-img" alt="${{item.titel}}">
                    <div class="card-badges">
                        <span class="badge-status ${{badgeClass}}">${{item.status || 'Offen'}}</span>
                        <span class="uploader-tag"><i class="fa-solid fa-user"></i> ${{item.uploader || 'Anonym'}}</span>
                    </div>
                    <div class="card-title">${{item.titel}}</div>
                    <div class="card-loc"><i class="fa-solid fa-location-dot" style="color: var(--primary);"></i> ${{item.fundort}} (${{item.raum || 'Keine Raumangabe'}})</div>
                </div>
                ${{deleteBtnHtml}}
            `;
            grid.appendChild(card);
        }});
    }}

    function filterItems() {{
        const query = document.getElementById("searchInput").value.toLowerCase();
        const cat = document.getElementById("catSelect").value;
        const status = document.getElementById("statusSelect").value;

        const filtered = items.filter(item => {{
            const matchQuery = (item.titel && item.titel.toLowerCase().includes(query)) ||
                               (item.fundort && item.fundort.toLowerCase().includes(query)) ||
                               (item.uploader && item.uploader.toLowerCase().includes(query));
            const matchCat = (cat === "Alle" || item.kategorie === cat);
            const matchStatus = (status === "Alle" || item.status === status);
            return matchQuery && matchCat && matchStatus;
        }});

        renderItems(filtered);
    }}

    function openDetail(id) {{
        const item = items.find(i => i.id == id);
        if(!item) return;

        const defaultImg = "https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=600&auto=format&fit=crop&q=80";
        const imgSrc = (item.bild_base64 && item.bild_base64.length > 20) ? item.bild_base64 : defaultImg;
        const badgeClass = item.status === "Offen" ? "badge-offen" : "badge-abgeholt";

        const container = document.getElementById("detailCard");
        container.innerHTML = `
            <img src="${{imgSrc}}" style="width: 100%; height: 280px; object-fit: cover; border-radius: var(--radius-md); margin-bottom: 24px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
                <h2 style="font-size: 1.8rem; font-weight: 800;">${{item.titel}}</h2>
                <span class="badge-status ${{badgeClass}}" style="font-size: 0.85rem; padding: 6px 16px;">${{item.status || 'Offen'}}</span>
            </div>
            
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px; background: var(--bg-main); padding: 20px; border-radius: var(--radius-md); margin-bottom: 24px;">
                <div>
                    <span style="font-size: 0.8rem; color: var(--text-muted); font-weight: 700;">GEMELDET VON</span>
                    <p style="font-weight: 700; font-size: 1.05rem; margin-top: 2px;">👤 ${{item.uploader || 'Anonym'}}</p>
                </div>
                <div>
                    <span style="font-size: 0.8rem; color: var(--text-muted); font-weight: 700;">KATEGORIE</span>
                    <p style="font-weight: 700; font-size: 1.05rem; margin-top: 2px;">🏷️ ${{item.kategorie || 'Sonstiges'}}</p>
                </div>
                <div>
                    <span style="font-size: 0.8rem; color: var(--text-muted); font-weight: 700;">FUNDORT & RAUM</span>
                    <p style="font-weight: 700; font-size: 1.05rem; margin-top: 2px;">📍 ${{item.fundort}} (${{item.raum || '-'}})</p>
                </div>
                <div>
                    <span style="font-size: 0.8rem; color: var(--text-muted); font-weight: 700;">ABGABEORT / KONTAKT</span>
                    <p style="font-weight: 700; font-size: 1.05rem; margin-top: 2px;">🔑 ${{item.kontakt || 'Sekretariat'}}</p>
                </div>
            </div>
            <p style="color: var(--text-muted); font-size: 0.85rem; text-align: right;">Eingetragen am: ${{item.datum || 'Unbekannt'}}</p>
        `;

        switchScreen('detail');
    }}

    function switchScreen(name) {{
        document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
        document.getElementById('screen-' + name).classList.add('active');

        document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
        if(name === 'home') document.getElementById('nav-home').classList.add('active');
        if(name === 'add') updateAccountName();
    }}

    function handleFileSelect(event) {{
        const file = event.target.files[0];
        if (file) {{
            const reader = new FileReader();
            reader.onload = function(e) {{
                base64Image = e.target.result;
                const img = document.getElementById("imgPreview");
                img.src = base64Image;
                img.style.display = "block";
            }};
            reader.readAsDataURL(file);
        }}
    }}

    function handleFormSubmit(e) {{
        e.preventDefault();
        
        const payload = {{
            titel: document.getElementById("formTitel").value,
            kategorie: document.getElementById("formKategorie").value,
            uploader: document.getElementById("formUploader").value,
            fundort: document.getElementById("formFundort").value,
            raum: document.getElementById("formRaum").value,
            kontakt: document.getElementById("formKontakt").value,
            bild_base64: base64Image
        }};

        // Send via query params back to Streamlit python backend
        const url = window.location.pathname + '?action=add&payload=' + encodeURIComponent(JSON.stringify(payload));
        window.top.location.href = url;
    }}

    function deleteItem(event, id) {{
        event.stopPropagation();
        if(confirm("Möchtest du dieses Fundstück wirklich dauerhaft löschen?")) {{
            const url = window.location.pathname + '?action=delete&id=' + id;
            window.top.location.href = url;
        }}
    }}

    // Initial setup
    updateAccountName();
    renderItems(items);
</script>

</body>
</html>
"""

# Render Full Screen HTML App
components.html(html_template, height=900, scrolling=True)
