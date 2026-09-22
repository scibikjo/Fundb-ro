import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
from datetime import date

# ==========================================
# SEITEN-KONFIGURATION
# ==========================================
st.set_page_config(
    page_title="Digitales Fundbüro & Mini-Game",
    page_icon="🎒",
    layout="wide"
)

# Initialisierung des Session-States für Fundstücke
if "items" not in st.get_variable("session_state", st.session_state):
    st.session_state["items"] = [
        {
            "id": 101,
            "titel": "Schwarzer Haustürschlüssel",
            "kategorie": "Schlüssel",
            "ort": "Hauptbahnhof / Gleis 3",
            "datum": "2026-09-20",
            "status": "Gefunden",
            "beschreibung": "Schlüsselbund mit einem blauen Anhänger und 3 Schlüsseln."
        },
        {
            "id": 102,
            "titel": "Roter Damen-Regenschirm",
            "kategorie": "Kleidung & Accessoires",
            "ort": "Mensa / Innenstadt",
            "datum": "2026-09-21",
            "status": "Gefunden",
            "beschreibung": "Knirps-Schirm, rot gestreift, Griff leicht verkratzt."
        },
        {
            "id": 103,
            "titel": "Apple AirPods Pro Hülle",
            "kategorie": "Elektronik",
            "ort": "Stadtpark Bank",
            "datum": "2026-09-22",
            "status": "Verloren gemeldet",
            "beschreibung": "Ladecase ohne Ohrhörer, hat einen kleinen Sticker auf der Rückseite."
        }
    ]

# Navigation über Tabs
tab1, tab2 = st.tabs(["🎒 Digitales Fundbüro", "🎮 Mini-Game (Battle Royale)"])


# ==========================================
# TAB 1: DAS PERFEKTE FUNDBÜRO
# ==========================================
with tab1:
    st.title("🎒 Digitales Fundbüro")
    st.markdown("Willkommen! Hier kannst du nach verlorenen Gegenständen suchen oder gefundene/verlorene Sachen eintragen.")
    
    st.divider()

    # --- Unter-Tabs im Fundbüro ---
    f_tab1, f_tab2, f_tab3 = st.tabs(["🔍 Suche & Übersicht", "➕ Gegenstand melden", "⚙️ Admin / Verwaltung"])

    # 1. SUCHE UND ÜBERSICHT
    with f_tab1:
        st.subheader("Gefundene & Verlorene Gegenstände")
        
        col_s1, col_s2, col_s3 = st.columns([2, 1, 1])
        with col_s1:
            search_query = st.text_input("🔎 Suchbegriff eingeben", placeholder="z. B. Schlüssel, Rucksack...")
        with col_s2:
            kat_filter = st.selectbox("Kategorie-Filter", ["Alle", "Schlüssel", "Elektronik", "Kleidung & Accessoires", "Taschen & Rucksäcke", "Sonstiges"])
        with col_s3:
            status_filter = st.selectbox("Status-Filter", ["Alle", "Gefunden", "Verloren gemeldet"])

        # Filter-Logik
        filtered_items = st.session_state["items"]

        if search_query:
            filtered_items = [
                item for item in filtered_items 
                if search_query.lower() in item["titel"].lower() or search_query.lower() in item["beschreibung"].lower()
            ]

        if kat_filter != "Alle":
            filtered_items = [item for item in filtered_items if item["kategorie"] == kat_filter]

        if status_filter != "Alle":
            filtered_items = [item for item in filtered_items if item["status"] == status_filter]

        st.caption(f"{len(filtered_items)} Eintrag/Einträge gefunden.")

        # Kacheln anzeigen
        if filtered_items:
            for item in filtered_items:
                status_color = "🟢" if item["status"] == "Gefunden" else "🟠"
                with st.expander(f"{status_color} **{item['titel']}** — *{item['kategorie']}* ({item['datum']})"):
                    st.write(f"**Status:** {item['status']}")
                    st.write(f"**Ort:** {item['ort']}")
                    st.write(f"**Beschreibung:** {item['beschreibung']}")
                    st.caption(f"Referenz-ID: #{item['id']}")
        else:
            st.info("Keine passenden Einträge gefunden.")

    # 2. GEGENSTAND MELDEN FORMULAR
    with f_tab2:
        st.subheader("Neuen Gegenstand eintragen")
        st.write("Hast du etwas gefunden oder vermisst du etwas? Trage es hier ein.")

        with st.form("add_item_form", clear_on_submit=True):
            col_f1, col_f2 = st.columns(2)
            
            with col_f1:
                title = st.text_input("Titel / Gegenstand*", placeholder="z. B. Schwarzer Ledergürtel")
                kategorie = st.selectbox("Kategorie*", ["Schlüssel", "Elektronik", "Kleidung & Accessoires", "Taschen & Rucksäcke", "Sonstiges"])
                status = st.radio("Meldungsart*", ["Gefunden", "Verloren gemeldet"])

            with col_f2:
                ort = st.text_input("Ort*", placeholder="z. B. Buslinie 4, Haltestelle Markt")
                datum = st.date_input("Datum*", value=date.today())
                beschreibung = st.text_area("Genauere Beschreibung", placeholder="Besondere Merkmale, Marken, Zustand...")

            submitted = st.form_submit_button("Eintrag abschicken 🚀")

            if submitted:
                if title and ort:
                    new_id = max([i["id"] for i in st.session_state["items"]], default=100) + 1
                    st.session_state["items"].append({
                        "id": new_id,
                        "titel": title,
                        "kategorie": kategorie,
                        "ort": ort,
                        "datum": str(datum),
                        "status": status,
                        "beschreibung": beschreibung if beschreibung else "Keine Zusatzbeschreibung."
                    })
                    st.success(f"Vielen Dank! '{title}' wurde erfolgreich aufgenommen (ID #{new_id}).")
                else:
                    st.error("Bitte fülle mindestens den Titel und den Ort aus!")

    # 3. ADMIN / TABELLENANSICHT
    with f_tab3:
        st.subheader("⚙️ Datensatz-Verwaltung")
        df = pd.DataFrame(st.session_state["items"])
        
        st.dataframe(df, use_container_width=True)
        
        st.markdown("---")
        st.write("Eintrag löschen")
        del_id = st.number_input("Gib die ID des zu löschenden Eintrags ein:", min_value=101, step=1)
        if st.button("Eintrag unwiderruflich entfernen"):
            initial_count = len(st.session_state["items"])
            st.session_state["items"] = [item for item in st.session_state["items"] if item["id"] != del_id]
            if len(st.session_state["items"]) < initial_count:
                st.success(f"Eintrag #{del_id} wurde gelöscht.")
                st.rerun()
            else:
                st.warning(f"Kein Eintrag mit ID #{del_id} gefunden.")


# ==========================================
# TAB 2: BATTLE ROYALE 2D GAME
# ==========================================
with tab2:
    st.title("🎮 Battle Royale 2D")
    st.caption("Verstecktes Admin-Menü im Spiel? Nutze den **Owner Area** Button im Spiel. Passwort: **`owner123`**")

    # HTML5/JS Game Canvas Code
    game_html = """
    <!DOCTYPE html>
    <html lang="de">
    <head>
        <meta charset="UTF-8">
        <style>
            * { box-sizing: border-box; margin: 0; padding: 0; user-select: none; }
            body {
                background: #0f1115;
                color: #ececec;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                padding: 10px;
            }
            .game-container {
                position: relative;
                border-radius: 12px;
                box-shadow: 0 10px 30px rgba(0, 0, 0, 0.7);
                overflow: hidden;
                background: #16181d;
                border: 1px solid #2a2d37;
            }
            canvas { display: block; background-color: #16181d; }
            
            .modal-overlay {
                position: fixed; top: 0; left: 0; width: 100%; height: 100%;
                background: rgba(0, 0, 0, 0.85); backdrop-filter: blur(5px);
                display: flex; align-items: center; justify-content: center;
                z-index: 100; opacity: 0; pointer-events: none; transition: opacity 0.3s;
            }
            .modal-overlay.active { opacity: 1; pointer-events: auto; }
            .modal-card {
                background: #1e222b; border: 1px solid #323846; border-radius: 12px;
                padding: 20px; width: 300px; text-align: center;
            }
            .modal-card input {
                width: 100%; padding: 8px; margin: 10px 0; border-radius: 6px;
                border: 1px solid #3a4150; background: #12141a; color: #fff; text-align: center;
            }
            .btn {
                background: #2b68e0; color: white; border: none; padding: 8px 15px;
                border-radius: 6px; cursor: pointer; font-weight: bold; width: 100%; margin-top: 5px;
            }
            .secret-trigger {
                position: absolute; bottom: 10px; right: 10px;
                background: #1a1d24; border: 1px solid #2e3440; color: #888;
                padding: 6px 10px; border-radius: 15px; cursor: pointer; font-size: 0.8rem;
            }
            .owner-dashboard {
                position: absolute; bottom: 10px; left: 10px;
                background: rgba(22, 24, 29, 0.95); border: 1px solid #5aacff;
                padding: 10px; border-radius: 8px; display: none; width: 220px; z-index: 50;
            }
            .dash-btn {
                background: #252a34; border: 1px solid #3a4150; color: #eee;
                padding: 5px; margin: 3px 0; width: 100%; border-radius: 4px; cursor: pointer; font-size: 0.75rem;
            }
        </style>
    </head>
    <body>
        <div class="game-container">
            <canvas id="gameCanvas" width="900" height="550"></canvas>
            <button class="secret-trigger" id="openSecretBtn">🔒 Owner Area</button>
            
            <div class="owner-dashboard" id="ownerDashboard">
                <h4 style="color: #5aacff; margin-bottom: 5px;">⚡ Owner Controls</h4>
                <button class="dash-btn" onclick="ownerGodMode(1)">P1: Unendlich Leben/Schild</button>
                <button class="dash-btn" onclick="ownerGiveWeapon(1, 'Minigun')">P1: Minigun geben</button>
                <button class="dash-btn" onclick="ownerGiveWeapon(1, 'RocketLauncher')">P1: Raketenwerfer geben</button>
                <button class="dash-btn" onclick="ownerNukeEnemies(1)">P1: Gegner vernichten</button>
            </div>
        </div>

        <div class="modal-overlay" id="passwordModal">
            <div class="modal-card">
                <h3 style="color: #5aacff;">Owner Passwort</h3>
                <input type="password" id="ownerPassInput" placeholder="Passwort...">
                <button class="btn" id="submitPassBtn">Freischalten</button>
                <button class="btn" id="closePassBtn" style="background:#e02b2b; margin-top:5px;">Abbrechen</button>
            </div>
        </div>

        <script>
            const canvas = document.getElementById('gameCanvas');
            const ctx = canvas.getContext('2d');
            const WIDTH = 900, HEIGHT = 550, PLAYER_SIZE = 28, PLAYER_SPEED = 3.5;
            const keys = {};

            window.addEventListener('keydown', e => keys[e.code] = true);
            window.addEventListener('keyup', e => keys[e.code] = false);

            function distance(x1, y1, x2, y2) { return Math.hypot(x2 - x1, y2 - y1); }
            function vecNormalize(vx, vy) {
                const len = Math.hypot(vx, vy);
                return len === 0 ? { x: 0, y: 0 } : { x: vx / len, y: vy / len };
            }

            class Weapon {
                constructor(name, cooldownMs, bulletSpeed, bulletDamage, bulletSize, bulletColor) {
                    this.name = name; this.cooldownMs = cooldownMs; this.bulletSpeed = bulletSpeed;
                    this.bulletDamage = bulletDamage; this.bulletSize = bulletSize; this.bulletColor = bulletColor;
                    this.lastShotMs = 0;
                }
                tryShoot(nowMs, player, targetPlayer) {
                    if (nowMs - this.lastShotMs >= this.cooldownMs) {
                        this.shoot(player, targetPlayer);
                        this.lastShotMs = nowMs;
                    }
                }
                shoot(player, targetPlayer) {
                    let dir = player.aimDir;
                    if (targetPlayer && targetPlayer.alive) dir = vecNormalize(targetPlayer.x - player.x, targetPlayer.y - player.y);
                    bullets.push(new Bullet(player.x, player.y, dir.x, dir.y, this.bulletSpeed, this.bulletSize, this.bulletColor, player.id, this.bulletDamage));
                }
            }

            class Minigun extends Weapon {
                constructor() { super("Minigun", 50, 10.0, 5, 4, '#ffc864'); }
            }
            class RocketLauncher extends Weapon {
                constructor() { super("Raketenwerfer", 1500, 12.0, 100, 10, '#ff3232'); }
            }

            class Bullet {
                constructor(x, y, dirx, diry, speed, size, color, ownerId, damage) {
                    this.x = x; this.y = y; this.vx = dirx * speed; this.vy = diry * speed;
                    this.size = size; this.color = color; this.ownerId = ownerId; this.damage = damage; this.alive = true;
                }
                update() {
                    this.x += this.vx; this.y += this.vy;
                    if (this.x < 0 || this.x > WIDTH || this.y < 0 || this.y > HEIGHT) this.alive = false;
                }
                draw() {
                    ctx.fillStyle = this.color;
                    ctx.beginPath(); ctx.arc(this.x, this.y, this.size / 2, 0, Math.PI * 2); ctx.fill();
                }
            }

            class Player {
                constructor(id, x, y, color, controls) {
                    this.id = id; this.x = x; this.y = y; this.color = color; this.controls = controls;
                    this.health = 300; this.shield = 200; this.aimDir = { x: 1, y: 0 };
                    this.weapon = new Weapon("Pistole", 250, 7.0, 12, 6, '#ffdc5a');
                    this.alive = true; this.godMode = false;
                }
                handleInput() {
                    if (!this.alive) return;
                    let dx = 0, dy = 0;
                    if (keys[this.controls.up]) dy -= 1;
                    if (keys[this.controls.down]) dy += 1;
                    if (keys[this.controls.left]) dx -= 1;
                    if (keys[this.controls.right]) dx += 1;

                    const norm = vecNormalize(dx, dy);
                    this.x = Math.max(15, Math.min(WIDTH - 15, this.x + norm.x * PLAYER_SPEED));
                    this.y = Math.max(15, Math.min(HEIGHT - 15, this.y + norm.y * PLAYER_SPEED));

                    let closest = null, minDist = Infinity;
                    players.forEach(p => {
                        if (p !== this && p.alive) {
                            const d = distance(this.x, this.y, p.x, p.y);
                            if (d < minDist) { minDist = d; closest = p; }
                        }
                    });

                    if (closest) {
                        this.aimDir = vecNormalize(closest.x - this.x, closest.y - this.y);
                        this.weapon.tryShoot(Date.now(), this, closest);
                    } else if (dx !== 0 || dy !== 0) {
                        this.aimDir = norm;
                    }
                }
                takeDamage(dmg) {
                    if (this.godMode) return;
                    if (this.shield > 0) {
                        const abs = Math.min(dmg, this.shield);
                        this.shield -= abs; dmg -= abs;
                    }
                    if (dmg > 0) this.health = Math.max(0, this.health - dmg);
                    if (this.health <= 0) this.alive = false;
                }
                draw() {
                    if (!this.alive) return;
                    ctx.fillStyle = this.color;
                    ctx.beginPath(); ctx.arc(this.x, this.y, PLAYER_SIZE / 2, 0, Math.PI * 2); ctx.fill();
                    if (this.shield > 0) {
                        ctx.strokeStyle = '#64c8ff'; ctx.lineWidth = 2;
                        ctx.beginPath(); ctx.arc(this.x, this.y, PLAYER_SIZE / 2 + 3, 0, Math.PI * 2); ctx.stroke();
                    }
                }
            }

            let players = [], bullets = [];
            function initGame() {
                players = [
                    new Player(1, 80, HEIGHT / 2, '#5aacff', { up: 'KeyW', down: 'KeyS', left: 'KeyA', right: 'KeyD' }),
                    new Player(2, WIDTH - 80, HEIGHT / 2, '#ff785a', { up: 'ArrowUp', down: 'ArrowDown', left: 'ArrowLeft', right: 'ArrowRight' }),
                    new Player(3, WIDTH / 2, HEIGHT - 80, '#96ff96', { up: 'KeyI', down: 'KeyK', left: 'KeyJ', right: 'KeyL' })
                ];
                bullets = [];
            }

            function gameLoop() {
                ctx.clearRect(0, 0, WIDTH, HEIGHT);
                players.forEach(p => p.handleInput());
                bullets.forEach(b => {
                    b.update();
                    players.forEach(p => {
                        if (p.alive && b.alive && b.ownerId !== p.id && distance(b.x, b.y, p.x, p.y) < 18) {
                            p.takeDamage(b.damage); b.alive = false;
                        }
                    });
                });
                bullets = bullets.filter(b => b.alive);
                bullets.forEach(b => b.draw());
                players.forEach(p => p.draw());
                requestAnimationFrame(gameLoop);
            }

            // Owner Secret Logic
            const modal = document.getElementById('passwordModal');
            document.getElementById('openSecretBtn').onclick = () => modal.classList.add('active');
            document.getElementById('closePassBtn').onclick = () => modal.classList.remove('active');
            document.getElementById('submitPassBtn').onclick = () => {
                if (document.getElementById('ownerPassInput').value === 'owner123') {
                    modal.classList.remove('active');
                    document.getElementById('ownerDashboard').style.display = 'block';
                    document.getElementById('openSecretBtn').style.display = 'none';
                } else { alert('Falsches Passwort!'); }
            };

            window.ownerGodMode = id => { const p = players.find(x => x.id === id); if(p) { p.godMode = true; p.health = 300; p.shield = 200; } };
            window.ownerGiveWeapon = (id, type) => { const p = players.find(x => x.id === id); if(p && type === 'Minigun') p.weapon = new Minigun(); if(p && type === 'RocketLauncher') p.weapon = new RocketLauncher(); };
            window.ownerNukeEnemies = id => players.forEach(p => { if(p.id !== id) { p.health = 0; p.alive = false; } });

            initGame();
            gameLoop();
        </script>
    </body>
    </html>
    """

    components.html(game_html, height=620)
