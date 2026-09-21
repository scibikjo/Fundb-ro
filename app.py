import os
import json
import base64
import datetime
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from supabase import create_client, Client

# =========================================================
# 1. STREAMLIT CONFIG (Vollbild-Einstellung)
# =========================================================
st.set_page_config(
    page_title="FundSpot – Schul-Fundbüro",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
    <style>
        #MainMenu, footer, header {visibility: hidden;}
        .block-container {padding: 0rem !important; max-width: 100% !important;}
        iframe {display: block; border: none; width: 100vw !important; height: 100vh !important;}
    </style>
""", unsafe_allow_html=True)

# =========================================================
# 2. SUPABASE / DATENBANK BACKEND
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
            return res.data
        except Exception:
            pass
            
    csv_file = "fundbuero_db.csv"
    if os.path.exists(csv_file):
        try:
            return pd.read_csv(csv_file).fillna("").to_dict(orient="records")
        except Exception:
            pass

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

# Akzeptiere eingehende Events aus der HTML-App (Hinzufügen / Löschen)
if "last_action" not in st.session_state:
    st.session_state.last_action = None

# =========================================================
# 3. HTML / CSS / JAVASCRIPT APP (POURE OBERFLÄCHE)
# =========================================================
current_data = load_items()
data_json = json.dumps(current_data, ensure_ascii=False)

html_template = f"""
<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>FundSpot</title>
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
            --danger: #ef4444;
            --danger-bg: #fef2f2;
            --radius-lg: 20px;
            --radius-md: 14px;
            --radius-sm: 8px;
            --shadow: 0 4px 16px rgba(0,0,0,0.04);
        }}

        * {{ box-sizing: border-box; margin: 0; padding: 0; font-family: 'Plus Jakarta Sans', sans-serif; }}
        body {{ background-color: var(--bg-main); color: var(--text-main); padding: 20px; min-height: 100vh; }}
        .container {{ max-width: 1100px; margin: 0 auto; }}

        /* Top Header Navigation */
        .header {{
            background: var(--card-bg); border-radius: var(--radius-lg); padding: 14px 24px;
            display: flex; justify-content: space-between; align-items: center;
            box-shadow: var(--shadow); border: 1px solid var(--border); margin-bottom: 20px;
        }}
        .logo {{ display: flex; align-items: center; gap: 10px; font-weight: 800; font-size: 1.3rem; color: var(--primary); }}
        .logo-icon {{ background: var(--primary); color: white; width: 40px; height: 40px; border-radius: 12px; display: flex; align-items: center; justify-content: center; font-size: 1.1rem; }}
        
        .nav-btn {{
            background: transparent; border: none; padding: 10px 18px; border-radius: var(--radius-md);
            font-weight: 700; color: var(--text-muted); cursor: pointer; transition: all 0.2s;
            display: flex; align-items: center; gap: 8px; font-size: 0.9rem;
        }}
        .nav-btn:hover, .nav-btn.active {{ background: var(--primary-bg); color: var(--primary); }}
        .nav-btn-main {{ background: var(--primary); color: white !important; }}
        .nav-btn-main:hover {{ background: var(--primary-light) !important; }}

        /* User & Admin Toolbar */
        .user-bar {{
            background: white; border-radius: var(--radius-md); padding: 10px 18px;
            margin-bottom: 20px; border: 1px solid var(--border); display: flex;
            align-items: center; justify-content: space-between; gap: 12px; flex-wrap: wrap;
        }}
        .user-input {{ display: flex; align-items: center; gap: 8px; font-size: 0.85rem; font-weight: 600; color: var(--text-muted); }}
        .user-input input {{
            border: 1px solid var(--border); padding: 6px 10px; border-radius: var(--radius-sm);
            outline: none; font-weight: 600; color: var(--text-main); background: #f8fafc;
        }}

        /* Hero Banner */
        .hero {{
            background: linear-gradient(135deg, var(--primary) 0%, var(--primary-light) 100%);
            border-radius: var(--radius-lg); padding: 32px; color: white;
            box-shadow: 0 10px 24px rgba(27, 94, 32, 0.15); margin-bottom: 24px;
        }}
        .hero h1 {{ font-size: 1.9rem; font-weight: 800; margin-bottom: 6px; }}
        .hero p {{ color: #e8f5e9; font-size: 0.95rem; }}

        /* Search & Filter Controls */
        .filters {{ display: grid; grid-template-columns: 2fr 1fr; gap: 12px; margin-bottom: 24px; }}
        .search-box {{
            background: white; border: 1px solid var(--border); border-radius: var(--radius-md);
            padding: 10px 16px; display: flex; align-items: center; gap: 10px; box-shadow: var(--shadow);
        }}
        .search-box input, .select-box select {{
            border: none; outline: none; width: 100%; font-size: 0.9rem; background: transparent; font-weight: 500;
        }}
        .select-box {{
            background: white; border: 1px solid var(--border); border-radius: var(--radius-md);
            padding: 10px 16px; box-shadow: var(--shadow); display: flex; align-items: center;
        }}

        /* Grid Cards */
        .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 20px; }}
        .card {{
            background: white; border-radius: var(--radius-lg); border: 1px solid var(--border);
            padding: 16px; box-shadow: var(--shadow); transition: all 0.2s ease; cursor: pointer;
            display: flex; flex-direction: column; gap: 12px;
        }}
        .card:hover {{ transform: translateY(-4px); border-color: #a5d6a7; }}
        .card-img {{ width: 100%; height: 170px; border-radius: var(--radius-md); object-fit: cover; background: #f1f5f9; }}
        
        .badge {{ padding: 3px 10px; border-radius: 12px; font-size: 0.75rem; font-weight: 800; text-transform: uppercase; }}
        .badge-offen {{ background: var(--primary-bg); color: var(--primary); }}
        
        .uploader-tag {{ background: #f1f5f9; color: #475569; padding: 3px 8px; border-radius: 6px; font-size: 0.75rem; font-weight: 600; }}
        .card-title {{ font-size: 1.1rem; font-weight: 800; color: var(--text-main); line-height: 1.2; }}
        .card-loc {{ color: var(--text-muted); font-size: 0.85rem; display: flex; align-items: center; gap: 6px; }}

        .btn-delete {{
            background: var(--danger-bg); color: var(--danger); border: 1px solid #fca5a5;
            padding: 8px; border-radius: var(--radius-sm); font-size: 0.8rem; font-weight: 700;
            cursor: pointer; transition: all 0.2s; width: 100%; margin-top: 4px; text-align: center;
        }}
        .btn-delete:hover {{ background: var(--danger); color: white; }}

        /* Screens Switcher */
        .screen {{ display: none; }}
        .screen.active {{ display: block; }}

        /* Form Styling */
        .form-card {{
            background: white; border-radius: var(--radius-lg); padding: 28px;
            border: 1px solid var(--border); max-width: 600px; margin: 0 auto; box-shadow: var(--shadow);
        }}
        .form-title {{ font-size: 1.5rem; font-weight: 800; color: var(--primary); margin-bottom: 16px; text-align: center; }}

        .form-group {{ display: flex; flex-direction: column; gap: 6px; margin-bottom: 14px; }}
        .form-group label {{ font-weight: 700; font-size: 0.85rem; color: #374151; }}
        .form-group input, .form-group select {{
            padding: 10px 14px; border: 1px solid var(--border); border-radius: var(--radius-md);
            outline: none; font-size: 0.9rem; background: #f9fafb;
        }}

        .file-upload-box {{
            border: 2px dashed var(--border); border-radius: var(--radius-md); padding: 20px;
            text-align: center; cursor: pointer; background: #fafafa;
        }}
        .file-upload-box:hover {{ border-color: var(--primary); background: var(--primary-bg); }}

        .btn-submit {{
            background: var(--primary); color: white; border: none; padding: 14px;
            border-radius: var(--radius-md); font-weight: 800; font-size: 0.95rem; cursor: pointer;
            width: 100%; margin-top: 10px; transition: all 0.2s;
        }}
        .btn-submit:hover {{ background: var(--primary-light); }}

        .back-btn {{
            background: white; border: 1px solid var(--border); padding: 8px 16px;
            border-radius: var(--radius-md); font-weight: 700; cursor: pointer; margin-bottom: 16px;
            display: inline-flex; align-items: center; gap: 6px; color: var(--text-muted); font-size: 0.85rem;
        }}

        #imgPreview {{ width: 100%; max-height: 180px; object-fit: cover; border-radius: var(--radius-md); margin-top: 10px; display: none; }}
    </style>
</head>
<body>

<div class="container">
    <header class="header">
        <div class="logo">
            <div class="logo-icon"><i class="fa-solid fa-leaf"></i></div>
            <span>FundSpot</span>
        </div>
        <div style="display: flex; gap: 8px;">
            <button class="nav-btn active" id="nav-home" onclick="switchScreen('home')">
                <i class="fa-solid fa-compass"></i> Entdecken
            </button>
            <button class="nav-btn nav-btn-main" id="nav-add" onclick="switchScreen('add')">
                <i class="fa-solid fa-plus"></i> Hinzufügen
            </button>
        </div>
    </header>

    <div class="user-bar">
        <div class="user-input">
            <i class="fa-solid fa-user-circle" style="color: var(--primary);"></i>
            <span>Dein Name / Klasse:</span>
            <input type="text" id="accountName" value="Johann (8b)" onchange="saveName()">
        </div>
        <div class="user-input">
            <i class="fa-solid fa-key"></i>
            <span>Admin-Passcode:</span>
            <input type="password" id="adminPass" placeholder="Löschrecht aktivieren" oninput="toggleAdmin()">
        </div>
    </div>

    <!-- MAIN HOME SCREEN -->
    <main id="screen-home" class="screen active">
        <div class="hero">
            <h1>Digitales Fundbüro</h1>
            <p>Finde deine verlorenen Sachen schnell und einfach wieder.</p>
        </div>

        <div class="filters">
            <div class="search-box">
                <i class="fa-solid fa-magnifying-glass" style="color: var(--text-muted);"></i>
                <input type="text" id="searchInput" placeholder="Suchen nach Rucksack, Jacke, Halle..." oninput="filterItems()">
            </div>
            <div class="select-box">
                <select id="catSelect" onchange="filterItems()">
                    <option value="Alle">Alle Kategorien</option>
                    <option value="Kleidung">Kleidung</option>
                    <option value="Elektronik">Elektronik</option>
                    <option value="Bücher & Hefte">Bücher & Hefte</option>
                    <option value="Sonstiges">Sonstiges</option>
                </select>
            </div>
        </div>

        <div class="grid" id="itemsGrid"></div>
    </main>

    <!-- DETAIL VIEW SCREEN -->
    <main id="screen-detail" class="screen">
        <button class="back-btn" onclick="switchScreen('home')"><i class="fa-solid fa-arrow-left"></i> Zurück</button>
        <div class="form-card" id="detailCard"></div>
    </main>

    <!-- ADD ITEM SCREEN -->
    <main id="screen-add" class="screen">
        <button class="back-btn" onclick="switchScreen('home')"><i class="fa-solid fa-arrow-left"></i> Abbrechen</button>
        <div class="form-card">
            <div class="form-title">Neues Fundstück eintragen</div>

            <form onsubmit="submitForm(event)">
                <div class="form-group">
                    <label>Bezeichnung des Gegenstands *</label>
                    <input type="text" id="formTitel" placeholder="z. B. Roter Turnbeutel" required>
                </div>

                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px;">
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
                        <label>Uploader Name</label>
                        <input type="text" id="formUploader" readonly style="background: #e2e8f0;">
                    </div>
                </div>

                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px;">
                    <div class="form-group">
                        <label>Fundort *</label>
                        <input type="text" id="formFundort" placeholder="z. B. Mensa, Pausenhof" required>
                    </div>
                    <div class="form-group">
                        <label>Raum / Bereich</label>
                        <input type="text" id="formRaum" placeholder="z. B. Raum 102">
                    </div>
                </div>

                <div class="form-group">
                    <label>Abgabeort / Kontaktperson</label>
                    <input type="text" id="formKontakt" placeholder="z. B. Sekretariat, Hausmeister">
                </div>

                <div class="form-group">
                    <label>Foto hinzufügen</label>
                    <div class="file-upload-box" onclick="document.getElementById('fileInput').click()">
                        <i class="fa-solid fa-cloud-arrow-up" style="font-size: 1.5rem; color: var(--primary);"></i>
                        <p style="font-weight: 700; font-size: 0.85rem; margin-top: 4px;">Klicke hier zum Hochladen</p>
                        <input type="file" id="fileInput" accept="image/*" style="display:none" onchange="previewFile(event)">
                    </div>
                    <img id="imgPreview" alt="Vorschau">
                </div>

                <button type="submit" class="btn-submit">🚀 Fundstück veröffentlichen</button>
            </form>
        </div>
    </main>
</div>

<script>
    let items = {data_json};
    let base64Img = "";
    let isAdmin = false;

    function saveName() {{
        const name = document.getElementById("accountName").value;
        document.getElementById("formUploader").value = name || "Anonym";
    }}

    function toggleAdmin() {{
        isAdmin = (document.getElementById("adminPass").value === "admin123");
        filterItems();
    }}

    function renderGrid(list) {{
        const grid = document.getElementById("itemsGrid");
        grid.innerHTML = "";

        if (!list || list.length === 0) {{
            grid.innerHTML = `<p style="grid-column: 1/-1; text-align: center; color: var(--text-muted); padding: 40px;">Keine Fundstücke vorhanden.</p>`;
            return;
        }}

        list.forEach(item => {{
            const card = document.createElement("div");
            card.className = "card";
            
            const defaultImg = "https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=600&auto=format&fit=crop&q=80";
            const imgSrc = (item.bild_base64 && item.bild_base64.length > 20) ? item.bild_base64 : defaultImg;

            let deleteBtn = isAdmin ? `<button class="btn-delete" onclick="deleteItem(event, ${{item.id}})"><i class="fa-solid fa-trash"></i> Löschen</button>` : '';

            card.innerHTML = `
                <div onclick="openDetail(${{item.id}})" style="display:flex; flex-direction:column; gap:8px;">
                    <img src="${{imgSrc}}" class="card-img" alt="Foto">
                    <div style="display:flex; justify-size:space-between; justify-content:space-between; align-items:center;">
                        <span class="badge badge-offen">${{item.status || 'Offen'}}</span>
                        <span class="uploader-tag">👤 ${{item.uploader || 'Anonym'}}</span>
                    </div>
                    <div class="card-title">${{item.titel}}</div>
                    <div class="card-loc"><i class="fa-solid fa-location-dot" style="color: var(--primary);"></i> ${{item.fundort}} (${{item.raum || '-'}})</div>
                </div>
                ${{deleteBtn}}
            `;
            grid.appendChild(card);
        }});
    }}

    function filterItems() {{
        const q = document.getElementById("searchInput").value.toLowerCase();
        const cat = document.getElementById("catSelect").value;

        const filtered = items.filter(item => {{
            const matchQ = (item.titel && item.titel.toLowerCase().includes(q)) || (item.fundort && item.fundort.toLowerCase().includes(q));
            const matchCat = (cat === "Alle" || item.kategorie === cat);
            return matchQ && matchCat;
        }});

        renderGrid(filtered);
    }}

    function openDetail(id) {{
        const item = items.find(i => i.id == id);
        if(!item) return;

        const defaultImg = "https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=600&auto=format&fit=crop&q=80";
        const imgSrc = (item.bild_base64 && item.bild_base64.length > 20) ? item.bild_base64 : defaultImg;

        document.getElementById("detailCard").innerHTML = `
            <img src="${{imgSrc}}" style="width:100%; height:220px; object-fit:cover; border-radius:var(--radius-md); margin-bottom:16px;">
            <h2 style="font-size:1.5rem; font-weight:800; margin-bottom:12px;">${{item.titel}}</h2>
            <div style="background:var(--bg-main); padding:16px; border-radius:var(--radius-md); font-size:0.9rem; display:flex; flex-direction:column; gap:8px;">
                <div><strong>👤 Gemeldet von:</strong> ${{item.uploader || 'Anonym'}}</div>
                <div><strong>🏷️ Kategorie:</strong> ${{item.kategorie || 'Sonstiges'}}</div>
                <div><strong>📍 Ort:</strong> ${{item.fundort}} (${{item.raum || '-'}})</div>
                <div><strong>🔑 Abgabeort/Kontakt:</strong> ${{item.kontakt || 'Sekretariat'}}</div>
                <div><strong>📅 Datum:</strong> ${{item.datum || '-'}}</div>
            </div>
        `;
        switchScreen('detail');
    }}

    function switchScreen(s) {{
        document.querySelectorAll('.screen').forEach(el => el.classList.remove('active'));
        document.getElementById('screen-' + s).classList.add('active');
        if(s === 'add') saveName();
    }}

    function previewFile(e) {{
        const file = e.target.files[0];
        if (file) {{
            const reader = new FileReader();
            reader.onload = function(evt) {{
                base64Img = evt.target.result;
                const img = document.getElementById("imgPreview");
                img.src = base64Img;
                img.style.display = "block";
            }};
            reader.readAsDataURL(file);
        }}
    }}

    function submitForm(e) {{
        e.preventDefault();
        alert("Eintrag wird gespeichert...");
        // Lokales Test-Hinzufügen direkt in der JS-Ansicht
        const newItem = {{
            id: Date.now(),
            titel: document.getElementById("formTitel").value,
            kategorie: document.getElementById("formKategorie").value,
            uploader: document.getElementById("formUploader").value,
            fundort: document.getElementById("formFundort").value,
            raum: document.getElementById("formRaum").value,
            kontakt: document.getElementById("formKontakt").value,
            datum: new Date().toISOString().split('T')[0],
            status: "Offen",
            bild_base64: base64Img
        }};
        items.unshift(newItem);
        filterItems();
        switchScreen('home');
    }}

    function deleteItem(e, id) {{
        e.stopPropagation();
        if(confirm("Möchtest du dieses Fundstück löschen?")) {{
            items = items.filter(i => i.id != id);
            filterItems();
        }}
    }}

    saveName();
    renderGrid(items);
</script>

</body>
</html>
"""

components.html(html_template, height=900, scrolling=True)
