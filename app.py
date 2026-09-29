import streamlit as st
import streamlit.components.v1 as components

# Streamlit Konfiguration
st.set_page_config(page_title="Streamlit App & Game", layout="wide")

# Session State Initialisierung für Tab-Routing
if "tab" not in st.session_state:
    st.session_state.tab = "game"

# Tab-Navigation (Beispiel)
st.title("🎮 Dashboard & Mini-Game")
col1, col2, col3 = st.columns(3)
with col1:
    if st.button("Home / Tab 1"):
        st.session_state.tab = "home"
with col2:
    if st.button("Stats / Tab 2"):
        st.session_state.tab = "stats"
with col3:
    if st.button("Mini-Game / Tab 3"):
        st.session_state.tab = "game"

st.divider()

# TAB ROUTING
if st.session_state.tab == "home":
    st.subheader("Willkommen auf der Hauptseite")
    st.write("Hier sind die normalen Inhalte von Tab 1.")

elif st.session_state.tab == "stats":
    st.subheader("Statistiken")
    st.write("Hier sind die Inhalte von Tab 2.")

# TAB 3: BATTLE ROYALE MINI-GAME (inkl. Vollbildmodus)
elif st.session_state.tab == "game":
    st.subheader("🎮 Battle Royale 2D – Pausenspiel")
    st.caption("Verstecktes Owner-Menü unten rechts im Spiel nutzen. Passwort: **`owner123`**")

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
                border-radius: 16px;
            }
            .game-container {
                position: relative;
                border-radius: 12px;
                box-shadow: 0 10px 30px rgba(0, 0, 0, 0.7);
                overflow: hidden;
                background: #16181d;
                border: 1px solid #2a2d37;
                display: flex;
                justify-content: center;
                align-items: center;
            }
            /* Styling für den echten Vollbildmodus */
            .game-container:fullscreen {
                width: 100vw !important;
                height: 100vh !important;
                border-radius: 0;
                border: none;
                background: #0f1115;
            }
            .game-container:-webkit-full-screen {
                width: 100vw !important;
                height: 100vh !important;
            }
            
            canvas { display: block; background-color: #16181d; max-width: 100%; max-height: 100%; }
            
            /* Vollbild Button oben links */
            .fullscreen-btn {
                position: absolute; top: 10px; left: 10px;
                background: rgba(26, 29, 36, 0.8); border: 1px solid #2e3440; color: #fff;
                padding: 6px 12px; border-radius: 8px; cursor: pointer; font-size: 0.85rem;
                z-index: 40; backdrop-filter: blur(4px); transition: all 0.2s;
            }
            .fullscreen-btn:hover { background: #0d9488; border-color: #0d9488; }

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
                background: #0d9488; color: white; border: none; padding: 8px 15px;
                border-radius: 6px; cursor: pointer; font-weight: bold; width: 100%; margin-top: 5px;
            }
            .secret-trigger {
                position: absolute; bottom: 10px; right: 10px;
                background: #1a1d24; border: 1px solid #2e3440; color: #888;
                padding: 6px 10px; border-radius: 15px; cursor: pointer; font-size: 0.8rem;
                z-index: 40;
            }
            .owner-dashboard {
                position: absolute; bottom: 10px; left: 10px;
                background: rgba(22, 24, 29, 0.95); border: 1px solid #0d9488;
                padding: 10px; border-radius: 8px; display: none; width: 220px; z-index: 50;
            }
            .dash-btn {
                background: #252a34; border: 1px solid #3a4150; color: #eee;
                padding: 5px; margin: 3px 0; width: 100%; border-radius: 4px; cursor: pointer; font-size: 0.75rem;
            }
        </style>
    </head>
    <body>
        <div class="game-container" id="gameContainer">
            <button class="fullscreen-btn" id="fullscreenBtn">⛶ Vollbild</button>
            <canvas id="gameCanvas" width="900" height="500"></canvas>
            <button class="secret-trigger" id="openSecretBtn">🔒 Owner Area</button>
            
            <div class="owner-dashboard" id="ownerDashboard">
                <h4 style="color: #0d9488; margin-bottom: 5px;">⚡ Owner Controls</h4>
                <button class="dash-btn" onclick="ownerGodMode(1)">P1: Unendlich Leben/Schild</button>
                <button class="dash-btn" onclick="ownerGiveWeapon(1, 'Minigun')">P1: Minigun geben</button>
                <button class="dash-btn" onclick="ownerGiveWeapon(1, 'RocketLauncher')">P1: Raketenwerfer geben</button>
                <button class="dash-btn" onclick="ownerNukeEnemies(1)">P1: Gegner vernichten</button>
            </div>
        </div>

        <div class="modal-overlay" id="passwordModal">
            <div class="modal-card">
                <h3 style="color: #0d9488;">Owner Passwort</h3>
                <input type="password" id="ownerPassInput" placeholder="Passwort...">
                <button class="btn" id="submitPassBtn">Freischalten</button>
                <button class="btn" id="closePassBtn" style="background:#e02b2b; margin-top:5px;">Abbrechen</button>
            </div>
        </div>

        <script>
            const canvas = document.getElementById('gameCanvas');
            const ctx = canvas.getContext('2d');
            const gameContainer = document.getElementById('gameContainer');
            const fullscreenBtn = document.getElementById('fullscreenBtn');

            const WIDTH = 900, HEIGHT = 500, PLAYER_SIZE = 28, PLAYER_SPEED = 3.5;
            const keys = {};

            // Vollbild-Logik
            fullscreenBtn.addEventListener('click', toggleFullscreen);

            function toggleFullscreen() {
                if (!document.fullscreenElement && !document.webkitFullscreenElement) {
                    if (gameContainer.requestFullscreen) {
                        gameContainer.requestFullscreen();
                    } else if (gameContainer.webkitRequestFullscreen) {
                        gameContainer.webkitRequestFullscreen();
                    }
                } else {
                    if (document.exitFullscreen) {
                        document.exitFullscreen();
                    } else if (document.webkitExitFullscreen) {
                        document.webkitExitFullscreen();
                    }
                }
            }

            document.addEventListener('fullscreenchange', updateFullscreenBtn);
            document.addEventListener('webkitfullscreenchange', updateFullscreenBtn);

            function updateFullscreenBtn() {
                if (document.fullscreenElement || document.webkitFullscreenElement) {
                    fullscreenBtn.textContent = '❌ Vollbild Beenden';
                } else {
                    fullscreenBtn.textContent = '⛶ Vollbild';
                }
            }

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
                        ctx.strokeStyle = '#0d9488'; ctx.lineWidth = 2;
                        ctx.beginPath(); ctx.arc(this.x, this.y, PLAYER_SIZE / 2 + 3, 0, Math.PI * 2); ctx.stroke();
                    }
                }
            }

            let players = [], bullets = [];
            function initGame() {
                players = [
                    new Player(1, 80, HEIGHT / 2, '#0d9488', { up: 'KeyW', down: 'KeyS', left: 'KeyA', right: 'KeyD' }),
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

    components.html(game_html, height=560)
