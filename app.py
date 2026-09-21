import streamlit as st
import streamlit.components.v1 as components

# 1. Streamlit-Konfiguration für volle Breite
st.set_page_config(
    page_title="FundSpot – Schul-Fundbüro",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 2. Das vollständige HTML/CSS/JS-Design
html_code = """
<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>FundSpot – Schul-Fundbüro</title>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        :root {
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
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
            font-family: 'Plus Jakarta Sans', sans-serif;
        }

        body {
            background-color: var(--bg-main);
            color: var(--text-main);
            padding: 24px;
            min-height: 100vh;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
        }

        /* Header / Brand Bar */
        .app-header {
            background: var(--card-bg);
            border-radius: var(--radius-lg);
            padding: 16px 28px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            box-shadow: var(--shadow-sm);
            border: 1px solid var(--border);
            margin-bottom: 24px;
        }

        .brand-logo {
            display: flex;
            align-items: center;
            gap: 12px;
            font-weight: 800;
            font-size: 1.4rem;
            color: var(--primary);
        }

        .brand-icon {
            background: var(--primary);
            color: white;
            width: 42px;
            height: 42px;
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.2rem;
        }

        .nav-links {
            display: flex;
            gap: 8px;
        }

        .nav-btn {
            background: transparent;
            border: none;
            padding: 10px 18px;
            border-radius: var(--radius-md);
            font-weight: 600;
            color: var(--text-muted);
            cursor: pointer;
            transition: all 0.2s;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .nav-btn:hover, .nav-btn.active {
            background: var(--primary-bg);
            color: var(--primary);
        }

        /* Hero Banner */
        .hero-card {
            background: linear-gradient(135deg, var(--primary) 0%, var(--primary-light) 100%);
            border-radius: var(--radius-lg);
            padding: 36px;
            color: white;
            box-shadow: 0 12px 30px rgba(27, 94, 32, 0.2);
            margin-bottom: 28px;
        }

        .hero-card h1 {
            font-size: 2rem;
            font-weight: 800;
            margin-bottom: 8px;
        }

        .hero-card p {
            color: #e8f5e9;
            font-size: 1.05rem;
        }

        /* Filters */
        .filter-bar {
            display: grid;
            grid-template-columns: 2fr 1fr 1fr;
            gap: 16px;
            margin-bottom: 28px;
        }

        .input-group {
            background: white;
            border: 1px solid var(--border);
            border-radius: var(--radius-md);
            padding: 12px 18px;
            display: flex;
            align-items: center;
            gap: 10px;
            box-shadow: var(--shadow-sm);
        }

        .input-group input, .input-group select {
            border: none;
            outline: none;
            width: 100%;
            font-size: 0.95rem;
            background: transparent;
        }

        /* Grid & Cards */
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 24px;
        }

        .item-card {
            background: white;
            border-radius: var(--radius-lg);
            border: 1px solid var(--border);
            padding: 18px;
            box-shadow: var(--shadow-sm);
            transition: all 0.25s ease;
            cursor: pointer;
            display: flex;
            flex-direction: column;
            gap: 12px;
        }

        .item-card:hover {
            transform: translateY(-6px);
            box-shadow: var(--shadow-hover);
            border-color: #a5d6a7;
        }

        .item-img {
            width: 100%;
            height: 180px;
            border-radius: var(--radius-md);
            object-fit: cover;
            background: #f1f5f9;
        }

        .badge-status {
            background: var(--primary-bg);
            color: var(--primary);
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 0.78rem;
            font-weight: 700;
            display: inline-block;
            width: fit-content;
        }

        .uploader-tag {
            background: #f1f5f9;
            color: #475569;
            padding: 4px 10px;
            border-radius: 10px;
            font-size: 0.8rem;
            font-weight: 600;
            display: inline-block;
            width: fit-content;
        }

        .card-title {
            font-size: 1.15rem;
            font-weight: 700;
        }

        .card-loc {
            color: var(--text-muted);
            font-size: 0.88rem;
        }

        /* Screens */
        .screen {
            display: none;
        }

        .screen.active {
            display: block;
        }

        /* Forms & Buttons */
        .form-card {
            background: white;
            border-radius: var(--radius-lg);
            padding: 32px;
            border: 1px solid var(--border);
            max-width: 650px;
            margin: 0 auto;
            box-shadow: var(--shadow-sm);
        }

        .form-group {
            margin-bottom: 20px;
        }

        .form-group label {
            display: block;
            font-weight: 700;
            margin-bottom: 8px;
            font-size: 0.9rem;
        }

        .form-control {
            width: 100%;
            padding: 12px 16px;
            border-radius: var(--radius-md);
            border: 1px solid var(--border);
            font-size: 0.95rem;
            outline: none;
        }

        .btn-primary {
            background: var(--primary);
            color: white;
            border: none;
            padding: 14px 24px;
            border-radius: var(--radius-md);
            font-weight: 700;
            font-size: 1rem;
            cursor: pointer;
            width: 100%;
            transition: background 0.2s;
        }

        .btn-primary:hover {
            background: var(--primary-light);
        }

        .back-btn {
            background: #e2e8f0;
            border: none;
            padding: 8px 16px;
            border-radius: var(--radius-md);
            font-weight: 600;
            cursor: pointer;
            margin-bottom: 20px;
        }
    </style>
</head>
<body>

<div class="container">
    <!-- Navigation Header -->
    <header class="app-header">
        <div class="brand-logo">
            <div class="brand-icon"><i class="fa-solid fa-leaf"></i></div>
            <span>FundSpot</span>
        </div>
        <nav class="nav-links">
            <button class="nav-btn active" onclick="switchScreen('home')"><i class="fa-solid fa-compass"></i> Entdecken</button>
            <button class="nav-btn" onclick="switchScreen('upload')"><i class="fa-solid fa-plus"></i> Hochladen</button>
        </nav>
    </header>

    <!-- SCREEN 1: HOME -->
    <main id="screen-home" class="screen active">
        <div class="hero-card">
            <h1>Gefundenes wiederentdecken</h1>
            <p>Finde deine verlorenen Wertsachen oder hilf anderen, ihre Sachen wiederzubekommen.</p>
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
                    <option value="Bücher">Bücher & Hefte</option>
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

    <!-- SCREEN 2: DETAILANSICHT -->
    <main id="screen-detail" class="screen">
        <button class="back-btn" onclick="switchScreen('home')"><i class="fa-solid fa-arrow-left"></i> Zurück</button>
        <div class="form-card" id="detailContent"></div>
    </main>

    <!-- SCREEN 3: HOCHLADEN -->
    <main id="screen-upload" class="screen">
        <div class="form-card">
            <h2 style="margin-bottom: 20px;">➕ Fundstück eintragen</h2>
            <form onsubmit="handleUpload(event)">
                <div class="form-group">
                    <label>Bezeichnung / Titel *</label>
                    <input type="text" class="form-control" id="titleInput" placeholder="z. B. Blaue Nike Jacke" required>
                </div>
                <div class="form-group">
                    <label>Dein Name / Klasse *</label>
                    <input type="text" class="form-control" id="uploaderInput" placeholder="z. B. Johann (8b)" required>
                </div>
                <div class="form-group">
                    <label>Kategorie</label>
                    <select class="form-control" id="categoryInput">
                        <option value="Kleidung">Kleidung</option>
                        <option value="Elektronik">Elektronik</option>
                        <option value="Bücher & Hefte">Bücher & Hefte</option>
                        <option value="Sonstiges">Sonstiges</option>
                    </select>
                </div>
                <div class="form-group">
                    <label>Fundort *</label>
                    <input type="text" class="form-control" id="locInput" placeholder="z. B. Turnhalle" required>
                </div>
                <div class="form-group">
                    <label>Abgabeort / Kontakt</label>
                    <input type="text" class="form-control" id="contactInput" placeholder="z. B. Hausmeister">
                </div>
                <button type="submit" class="btn-primary">💾 Fundstück veröffentlichen</button>
            </form>
        </div>
    </main>
</div>

<script>
    // Beispieldaten
    let items = [
        {
            id: 1,
            titel: "Grüner Nike Rucksack",
            kategorie: "Sonstiges",
            fundort: "Mensa",
            uploader: "Johann",
            status: "Offen",
            datum: "2026-09-20",
            img: "https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=500&auto=format&fit=crop&q=60"
        },
        {
            id: 2,
            titel: "Blaue Strickjacke",
            kategorie: "Kleidung",
            fundort: "Turnhalle",
            uploader: "Maria",
            status: "Offen",
            datum: "2026-09-21",
            img: "https://images.unsplash.com/photo-1434389677669-e08b4cac3105?w=500&auto=format&fit=crop&q=60"
        }
    ];

    function renderItems(filtered) {
        const grid = document.getElementById("itemsGrid");
        grid.innerHTML = "";

        if(filtered.length === 0) {
            grid.innerHTML = "<p style='color: var(--text-muted); grid-column: 1/-1;'>Keine Fundstücke gefunden.</p>";
            return;
        }

        filtered.forEach(item => {
            const card = document.createElement("div");
            card.className = "item-card";
            card.onclick = () => openDetail(item.id);
            card.innerHTML = `
                <img src="${item.img}" class="item-img" alt="${item.titel}">
                <div class="badge-status">${item.status}</div>
                <div class="card-title">${item.titel}</div>
                <div class="uploader-tag">👤 von ${item.uploader}</div>
                <div class="card-loc">📍 ${item.fundort}</div>
            `;
            grid.appendChild(card);
        });
    }

    function filterItems() {
        const q = document.getElementById("searchInput").value.toLowerCase();
        const cat = document.getElementById("catSelect").value;
        const status = document.getElementById("statusSelect").value;

        const res = items.filter(i => {
            const matchQ = i.titel.toLowerCase().includes(q) || i.fundort.toLowerCase().includes(q);
            const matchCat = (cat === "Alle" || i.kategorie === cat);
            const matchStatus = (status === "Alle" || i.status === status);
            return matchQ && matchCat && matchStatus;
        });

        renderItems(res);
    }

    function openDetail(id) {
        const item = items.find(i => i.id === id);
        if(!item) return;

        const detailBox = document.getElementById("detailContent");
        detailBox.innerHTML = `
            <img src="${item.img}" style="width: 100%; height: 260px; object-fit: cover; border-radius: var(--radius-md); margin-bottom: 20px;">
            <h2>${item.titel}</h2>
            <p style="margin: 10px 0;"><strong>Status:</strong> <span class="badge-status">${item.status}</span></p>
            <p style="margin: 6px 0;"><strong>Hochgeladen von:</strong> ${item.uploader}</p>
            <p style="margin: 6px 0;"><strong>Kategorie:</strong> ${item.kategorie}</p>
            <p style="margin: 6px 0;"><strong>Fundort:</strong> ${item.fundort}</p>
            <p style="margin: 6px 0;"><strong>Datum:</strong> ${item.datum}</p>
            <button class="btn-primary" style="margin-top: 20px;" onclick="markCollected(${item.id})">🙋‍♂️ Das gehört mir!</button>
        `;
        switchScreen('detail');
    }

    function markCollected(id) {
        const item = items.find(i => i.id === id);
        if(item) {
            item.status = "Abgeholt";
            alert("Erfolgreich als abgeholt markiert!");
            filterItems();
            switchScreen('home');
        }
    }

    function handleUpload(e) {
        e.preventDefault();
        const newObj = {
            id: Date.now(),
            titel: document.getElementById("titleInput").value,
            uploader: document.getElementById("uploaderInput").value,
            kategorie: document.getElementById("categoryInput").value,
            fundort: document.getElementById("locInput").value,
            status: "Offen",
            datum: new Date().toISOString().split('T')[0],
            img: "https://images.unsplash.com/photo-1523381210434-271e8be1f52b?w=500&auto=format&fit=crop&q=60"
        };

        items.unshift(newObj);
        filterItems();
        e.target.reset();
        switchScreen('home');
    }

    function switchScreen(name) {
        document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
        document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
        
        document.getElementById('screen-' + name).classList.add('active');
    }

    // Erstes Rendering
    renderItems(items);
</script>

</body>
</html>
"""

# 3. HTML in Streamlit einbetten
components.html(html_code, height=900, scrolling=True)
