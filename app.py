import base64
import datetime
import os
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from PIL import Image
from supabase import Client, create_client

# Hugging Face Transformers Integration
try:
    from transformers import BlipForConditionalGeneration, BlipProcessor

    HAS_HF = True
except ImportError:
    HAS_HF = False

# Übersetzungsdienst für Deutsch
try:
    from deep_translator import GoogleTranslator

    HAS_TRANSLATOR = True
except ImportError:
    HAS_TRANSLATOR = False

# =========================================================
# 1. STREAMLIT CONFIG & EXTENDED CSS (BACKGROUND & CARDS)
# =========================================================
st.set_page_config(
    page_title="FundSpot – Schul-Fundbüro & Mini-Game",
    page_icon="🎒",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

        /* Eleganter, moderner Hintergrund mit feinem Subtil-Muster */
        html, body, [class*="css"], .stApp {
            font-family: 'Plus Jakarta Sans', sans-serif !important;
            background-color: #f1f5f9 !important;
            background-image: 
                radial-gradient(at 0% 0%, rgba(13, 148, 136, 0.08) 0px, transparent 50%),
                radial-gradient(at 100% 100%, rgba(5, 150, 105, 0.06) 0px, transparent 50%),
                radial-gradient(#cbd5e1 0.8px, transparent 0.8px) !important;
            background-size: 100% 100%, 100% 100%, 20px 20px !important;
            background-attachment: fixed !important;
            color: #0f172a !important;
        }

        #MainMenu, footer, header { visibility: hidden !important; }
        
        .block-container {
            padding-top: 2rem !important;
            padding-bottom: 4rem !important;
            max-width: 1200px !important;
        }

        /* Hero Banner */
        .hero-banner {
            background: linear-gradient(135deg, #0f766e 0%, #0d9488 50%, #059669 100%);
            border-radius: 24px;
            padding: 32px 40px;
            color: #ffffff;
            box-shadow: 0 12px 30px -10px rgba(13, 148, 136, 0.4);
            margin-bottom: 24px;
        }
        .hero-banner h1 { 
            font-weight: 800; 
            font-size: 2.4rem; 
            margin: 0; 
            color: #ffffff !important;
        }
        .hero-banner p { 
            color: #ccfbf1; 
            font-size: 1.05rem; 
            margin-top: 6px; 
            margin-bottom: 0;
        }

        /* Karten mit Hover-Animation & Zoom-Effekt */
        .fund-card-container {
            background: #ffffff;
            border-radius: 20px;
            border: 1px solid #e2e8f0;
            overflow: hidden;
            box-shadow: 0 4px 12px rgba(0,0,0,0.03);
            transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
            margin-bottom: 12px;
        }

        .fund-card-container:hover {
            transform: translateY(-6px) scale(1.01);
            box-shadow: 0 16px 28px -8px rgba(15, 23, 42, 0.12);
            border-color: #cbd5e1;
        }

        .fund-card-details {
            padding: 16px 18px;
            background: #ffffff;
        }

        .fund-card-title {
            font-size: 1.15rem;
            font-weight: 700;
            color: #0f172a;
            margin-top: 6px;
            margin-bottom: 10px;
        }

        /* Badges */
        .badge {
            display: inline-block;
            padding: 4px 10px;
            border-radius: 9999px;
            font-size: 0.75rem;
            font-weight: 700;
            margin-right: 4px;
            margin-bottom: 6px;
        }
        .badge-kategorie { background-color: #e0f2fe; color: #0369a1; }
        .badge-ort { background-color: #fef3c7; color: #b45309; }
        .badge-claimed { background-color: #fef2f2; color: #991b1b; }
        .badge-open { background-color: #f0fdf4; color: #166534; }

        /* Custom Input & Form Styling */
        div[data-baseweb="input"] > div { border-radius: 14px !important; }
        div[data-baseweb="select"] > div { border-radius: 14px !important; }
        .stButton>button { border-radius: 12px !important; font-weight: 600 !important; }

        .upload-section {
            background-color: #ffffff;
            border-radius: 20px;
            padding: 24px;
            border: 1px solid #e2e8f0;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.03);
        }
    </style>
""",
    unsafe_allow_html=True,
)


# =========================================================
# 2. SUPABASE / CSV BACKEND
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
            res = (
                supabase.table("fundstuecke")
                .select("*")
                .order("id", desc=True)
                .execute()
            )
            if res.data:
                return res.data
        except Exception:
            pass

    csv_file = "fundbuero_db.csv"
    if os.path.exists(csv_file):
        try:
            df = pd.read_csv(csv_file).fillna("")
            return df.to_dict(orient="records")
        except Exception:
            pass

    default_data = [
        {
            "id": 1,
            "titel": "Grüner Nike Rucksack",
            "kategorie": "Kleidung & Taschen",
            "fundort": "Mensa",
            "raum": "EG",
            "datum": "2026-09-20",
            "status": "Offen",
            "kontakt": "Sekretariat",
            "uploader": "Johann (8b)",
            "beansprucht_von": "",
            "bild_base64": "https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=600&auto=format&fit=crop&q=80",
        }
    ]
    pd.DataFrame(default_data).to_csv(csv_file, index=False)
    return default_data


def save_items(items):
    csv_file = "fundbuero_db.csv"
    pd.DataFrame(items).to_csv(csv_file, index=False)


def delete_item(item_id):
    items = load_items()
    items = [i for i in items if str(i["id"]) != str(item_id)]

    if supabase:
        try:
            supabase.table("fundstuecke").delete().eq("id", item_id).execute()
        except Exception:
            pass
    save_items(items)


def update_item_claim(item_id, claimer_info):
    items = load_items()
    for item in items:
        if str(item["id"]) == str(item_id):
            item["status"] = "Beansprucht"
            item["beansprucht_von"] = claimer_info
            break

    if supabase:
        try:
            supabase.table("fundstuecke").update(
                {"status": "Beansprucht", "beansprucht_von": claimer_info}
            ).eq("id", item_id).execute()
        except Exception:
            pass
    save_items(items)


def add_new_item(item_dict):
    items = load_items()
    items.insert(0, item_dict)

    if supabase:
        try:
            supabase.table("fundstuecke").insert(item_dict).execute()
        except Exception:
            pass
    save_items(items)


# =========================================================
# 3. HUGGING FACE KI-MODELL & ÜBERSETZUNG (DEUTSCH)
# =========================================================
@st.cache_resource
def load_hf_model():
    processor = BlipProcessor.from_pretrained(
        "Salesforce/blip-image-captioning-base"
    )
    model = BlipForConditionalGeneration.from_pretrained(
        "Salesforce/blip-image-captioning-base"
    )
    return processor, model


def translate_to_german(text_en):
    if HAS_TRANSLATOR:
        try:
            translated = GoogleTranslator(source="en", target="de").translate(
                text_en
            )
            return translated
        except Exception:
            pass
    return text_en


def analyze_image_with_hf(image_file):
    if not HAS_HF:
        return (
            None,
            "Die Pakete 'transformers' und 'torch' fehlen in deiner requirements.txt.",
        )

    try:
        processor, model = load_hf_model()

        raw_image = Image.open(image_file).convert("RGB")

        inputs = processor(raw_image, return_tensors="pt")
        out = model.generate(**inputs, max_new_tokens=50)
        description_en = processor.decode(out[0], skip_special_tokens=True)

        description_de = translate_to_german(description_en)

        desc_lower = description_en.lower()

        kategorie = "Sonstiges"
        if any(
            w in desc_lower
            for w in [
                "jacket",
                "coat",
                "shirt",
                "pants",
                "sweater",
                "hoodie",
                "shoe",
                "sneaker",
                "hat",
                "cap",
                "glove",
                "scarf",
                "clothes",
                "bag",
                "backpack",
            ]
        ):
            kategorie = "Kleidung & Taschen"
        elif any(
            w in desc_lower
            for w in [
                "phone",
                "laptop",
                "tablet",
                "headphone",
                "earphone",
                "calculator",
                "cable",
                "charger",
                "electronic",
            ]
        ):
            kategorie = "Elektronik"
        elif any(
            w in desc_lower
            for w in [
                "book",
                "notebook",
                "paper",
                "binder",
                "pencil",
                "pen",
                "case",
            ]
        ):
            kategorie = "Bücher & Schreibwaren"

        return {
            "beschreibung": description_de,
            "kategorie": kategorie,
        }, None

    except Exception as e:
        return (
            None,
            f"Fehler bei der Hugging Face Modell-Analyse: {str(e)}",
        )


# =========================================================
# 4. SESSION STATE & OWNER / ADMIN RECHTE
# =========================================================
if "current_user" not in st.session_state:
    st.session_state.current_user = "Schüler / Finder"
if "tab" not in st.session_state:
    st.session_state.tab = "entdecken"
if "is_owner" not in st.session_state:
    st.session_state.is_owner = False

if "f_titel" not in st.session_state:
    st.session_state.f_titel = ""
if "f_kategorie" not in st.session_state:
    st.session_state.f_kategorie = "Sonstiges"
if "f_ort" not in st.session_state:
    st.session_state.f_ort = ""

OWNER_PASSWORD = st.secrets.get("OWNER_PASSWORD", "admin123")

# =========================================================
# 5. OBERFLÄCHE
# =========================================================

# Hero Banner
st.markdown(
    """
    <div class="hero-banner">
        <div style="display: flex; align-items: center; justify-content: space-between;">
            <div>
                <h1>🎒 FundSpot</h1>
                <p>Das digitale Schul-Fundbüro mit KI-Bilderkennung & Pause-Game</p>
            </div>
            <div style="font-size: 3.5rem; opacity: 0.9;">🔍</div>
        </div>
    </div>
""",
    unsafe_allow_html=True,
)

# User-Eingabe & Owner Mode Toggle
top_col1, top_col2 = st.columns([2, 1])
with top_col1:
    st.session_state.current_user = st.text_input(
        "👤 Dein Name / Klasse:", value=st.session_state.current_user
    )
with top_col2:
    pwd_input = st.text_input(
        "🔑 Owner / Admin Passwort:", type="password", placeholder="admin123"
    )
    if pwd_input == OWNER_PASSWORD:
        st.session_state.is_owner = True
        st.caption("✅ Owner-Rechte aktiv (Löschen erlaubt)")
    else:
        st.session_state.is_owner = False
        if pwd_input:
            st.caption("❌ Falsches Passwort")

st.write("")
nav_c1, nav_c2, nav_c3 = st.columns(3)
with nav_c1:
    if st.button(
        "🔍 Fundstücke durchsuchen",
        use_container_width=True,
        type="primary"
        if st.session_state.tab == "entdecken"
        else "secondary",
    ):
        st.session_state.tab = "entdecken"
        st.rerun()
with nav_c2:
    if st.button(
        "➕ Fundstück hochladen (KI)",
        use_container_width=True,
        type="primary"
        if st.session_state.tab == "hochladen"
        else "secondary",
    ):
        st.session_state.tab = "hochladen"
        st.rerun()
with nav_c3:
    if st.button(
        "🎮 Mini-Game (Battle Royale)",
        use_container_width=True,
        type="primary" if st.session_state.tab == "game" else "secondary",
    ):
        st.session_state.tab = "game"
        st.rerun()

st.write("")

# TAB 1: ENTDECKEN (MIT HOVER, DETAIL-VIEW & CLAIM-FUNKTION)
if st.session_state.tab == "entdecken":
    items = load_items()
    cols = st.columns(3)

    for idx, item in enumerate(items):
        with cols[idx % 3]:
            img_src = (
                item.get("bild_base64")
                or "https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=600&auto=format&fit=crop&q=80"
            )
            is_claimed = item.get("status") == "Beansprucht"
            status_badge = (
                '<span class="badge badge-claimed">⚠️ Beansprucht</span>'
                if is_claimed
                else '<span class="badge badge-open">✅ Offen</span>'
            )

            # HTML Card Rendering mit Hover
            st.markdown(
                f"""
                <div class="fund-card-container">
                    <div style="height: 200px; overflow: hidden; background: #e2e8f0;">
                        <img src="{img_src}" style="width: 100%; height: 100%; object-fit: cover;">
                    </div>
                    <div class="fund-card-details">
                        {status_badge}
                        <span class="badge badge-kategorie">🏷️ {item.get('kategorie')}</span>
                        <span class="badge badge-ort">📍 {item.get('fundort')}</span>
                        <div class="fund-card-title">{item.get('titel', 'Unbenannt')}</div>
                        <div style="font-size: 0.85rem; color: #64748b; line-height: 1.5;">
                            <b>Raum:</b> {item.get('raum')}<br>
                            <b>Finder:</b> {item.get('uploader')}<br>
                            <b>Datum:</b> {item.get('datum')}
                        </div>
                    </div>
                </div>
            """,
                unsafe_allow_html=True,
            )

            # Interaktions-Buttons
            btn_col1, btn_col2 = st.columns(2)

            # Button 1: Details / Bild vergrößern & Eigentum beanspruchen
            with btn_col1:
                with st.popover("🔎 Details / Eigentum"):
                    st.image(
                        img_src,
                        caption=item.get("titel"),
                        use_container_width=True,
                    )
                    st.markdown(f"### {item.get('titel')}")
                    st.write(
                        f"📍 **Fundort:** {item.get('fundort')} (Raum:"
                        f" {item.get('raum')})"
                    )
                    st.write(f"🏢 **Abholen bei:** {item.get('kontakt')}")
                    st.write(f"👤 **Eingetragen von:** {item.get('uploader')}")
                    st.write(f"📅 **Datum:** {item.get('datum')}")

                    if is_claimed:
                        st.warning(
                            "Dieses Fundstück wurde bereits beansprucht von:"
                            f" **{item.get('beansprucht_von')}**"
                        )
                    else:
                        st.divider()
                        st.markdown("#### 🙋 Das gehört mir!")
                        claimer_name = st.text_input(
                            "Dein Name / Klasse zum Abholen:",
                            key=f"claimer_{item['id']}",
                        )
                        if st.button(
                            "Gegenstand als 'Meins' markieren",
                            key=f"claim_btn_{item['id']}",
                            type="primary",
                        ):
                            if claimer_name.strip():
                                update_item_claim(item["id"], claimer_name)
                                st.success(
                                    "Vielen Dank! Der Gegenstand wurde für dich"
                                    " reserviert."
                                )
                                st.rerun()
                            else:
                                st.error("Bitte gib deinen Namen ein.")

            # Button 2: Löschen (Nur für den Owner sichtbar)
            with btn_col2:
                if st.session_state.is_owner:
                    if st.button(
                        "🗑️ Löschen",
                        key=f"del_{item['id']}",
                        use_container_width=True,
                    ):
                        delete_item(item["id"])
                        st.toast("Eintrag gelöscht!")
                        st.rerun()

# TAB 2: HOCHLADEN
elif st.session_state.tab == "hochladen":
    st.markdown('<div class="upload-section">', unsafe_allow_html=True)
    st.subheader("📸 Neues Fundstück eintragen")

    uploaded_file = st.file_uploader(
        "1. Wähle ein Foto aus", type=["jpg", "jpeg", "png", "webp"]
    )

    b64_img = ""
    if uploaded_file:
        st.image(uploaded_file, caption="Vorschau", width=220)
        b64_img = f"data:image/jpeg;base64,{base64.b64encode(uploaded_file.getvalue()).decode()}"

        if st.button(
            "🤗 Foto mit Hugging Face KI analysieren (auf Deutsch)",
            type="primary",
            use_container_width=True,
        ):
            with st.spinner(
                "Hugging Face KI analysiert das Bild und übersetzt die"
                " Auswertung..."
            ):
                ai_data, error_msg = analyze_image_with_hf(uploaded_file)

                if error_msg:
                    st.error(f"❌ {error_msg}")
                elif ai_data:
                    st.session_state.f_titel = ai_data.get(
                        "beschreibung", ""
                    ).capitalize()
                    st.session_state.f_kategorie = ai_data.get(
                        "kategorie", "Sonstiges"
                    )
                    st.success(
                        "✅ Das Bild wurde erfolgreich analysiert und ins"
                        " Deutsche übersetzt!"
                    )
                    st.rerun()

    st.markdown(
        '<hr style="border: 0; height: 1px; background: #e2e8f0; margin: 25px'
        ' 0;">',
        unsafe_allow_html=True,
    )
    st.write("### 2. Formular überprüfen & Veröffentlichen")

    titel_val = st.text_input(
        "Gegenstand / Beschreibung *", value=st.session_state.f_titel
    )

    kategorien = [
        "Sonstiges",
        "Kleidung & Taschen",
        "Elektronik",
        "Bücher & Schreibwaren",
    ]
    kat_idx = (
        kategorien.index(st.session_state.f_kategorie)
        if st.session_state.f_kategorie in kategorien
        else 0
    )
    kat_val = st.selectbox("Kategorie", kategorien, index=kat_idx)

    ort_val = st.text_input("Fundort *", value=st.session_state.f_ort)
    raum_val = st.text_input(
        "Raum / Bereich", placeholder="z. B. Sporthalle, Mensa, EG"
    )
    kontakt_val = st.text_input("Abgabeort / Kontakt", value="Sekretariat")

    if st.button(
        "🚀 Fundstück veröffentlichen", type="primary", use_container_width=True
    ):
        if not titel_val or not ort_val:
            st.error(
                "Bitte gib mindestens einen Titel/Gegenstand und den Ort ein."
            )
        else:
            new_entry = {
                "id": int(datetime.datetime.now().timestamp()),
                "titel": titel_val,
                "kategorie": kat_val,
                "fundort": ort_val,
                "raum": raum_val if raum_val else "-",
                "datum": str(datetime.date.today()),
                "status": "Offen",
                "kontakt": kontakt_val,
                "uploader": st.session_state.current_user,
                "beansprucht_von": "",
                "bild_base64": b64_img,
            }
            add_new_item(new_entry)
            st.toast("🎉 Fundstück erfolgreich eingetragen!")
            st.session_state.f_titel = ""
            st.session_state.f_ort = ""
            st.session_state.tab = "entdecken"
            st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

# TAB 3: BATTLE ROYALE MINI-GAME
elif st.session_state.tab == "game":
    st.subheader("🎮 Battle Royale 2D – Pausenspiel")
    st.caption(
        "Verstecktes Owner-Menü unten rechts im Spiel nutzen. Passwort:"
        " **`owner123`**"
    )

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
                overflow: hidden;
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
                width: 100%;
            }

            /* Vollbild-Modus Styles */
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
                border-radius: 0;
                border: none;
                background: #0f1115;
            }

            canvas { 
                display: block; 
                background-color: #16181d; 
                max-width: 100%;
                max-height: 100%;
            }
            
            .fullscreen-btn {
                position: absolute;
                top: 10px;
                right: 10px;
                background: rgba(26, 29, 36, 0.85);
                border: 1px solid #2e3440;
                color: #fff;
                padding: 6px 12px;
                border-radius: 8px;
                cursor: pointer;
                font-size: 0.85rem;
                font-weight: bold;
                z-index: 40;
                transition: background 0.2s;
            }
            .fullscreen-btn:hover { background: #0d9488; }

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
            <button class="fullscreen-btn" id="fsBtn">⛶ Vollbild</button>
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
            const container = document.getElementById('gameContainer');
            const fsBtn = document.getElementById('fsBtn');

            const WIDTH = 900, HEIGHT = 500, PLAYER_SIZE = 28, PLAYER_SPEED = 3.5;
            const keys = {};

            window.addEventListener('keydown', e => keys[e.code] = true);
            window.addEventListener('keyup', e => keys[e.code] = false);

            // Vollbild-Funktionalität
            function toggleFullscreen() {
                if (!document.fullscreenElement && !document.webkitFullscreenElement) {
                    if (container.requestFullscreen) {
                        container.requestFullscreen();
                    } else if (container.webkitRequestFullscreen) {
                        container.webkitRequestFullscreen();
                    }
                } else {
                    if (document.exitFullscreen) {
                        document.exitFullscreen();
                    } else if (document.webkitExitFullscreen) {
                        document.webkitExitFullscreen();
                    }
                }
            }

            fsBtn.addEventListener('click', toggleFullscreen);

            function updateFullscreenBtn() {
                if (document.fullscreenElement || document.webkitFullscreenElement) {
                    fsBtn.innerText = "❌ Beenden";
                } else {
                    fsBtn.innerText = "⛶ Vollbild";
                }
            }

            document.addEventListener('fullscreenchange', updateFullscreenBtn);
            document.addEventListener('webkitfullscreenchange', updateFullscreenBtn);

            function distance(x1, y1, x2, y2) { return Math.hypot(x2 - x1, y2 - y1); }
            function vecNormalize(vx, vy) {
                const len = Math.hypot(vx, vy);
                return len === 0 ? { x: 0, y: 0 } : { x: vx / len, y: vy / len };
            }

            let bullets = [];

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
                handleInput(nowMs) {
                    if (!this.alive) return;
                    let dx = 0, dy = 0;
                    if (keys[this.controls.up]) dy -= 1;
                    if (keys[this.controls.down]) dy += 1;
                    if (keys[this.controls.left]) dx -= 1;
                    if (keys[this.controls.right]) dx += 1;

                    const norm = vecNormalize(dx, dy);
                    if (norm.x !== 0 || norm.y !== 0) {
                        this.aimDir = norm;
                    }
                    this.x = Math.max(15, Math.min(WIDTH - 15, this.x + norm.x * PLAYER_SPEED));
                    this.y = Math.max(15, Math.min(HEIGHT - 15, this.y + norm.y * PLAYER_SPEED));

                    let closest = null, minDist = Infinity;
                    players.forEach(p => {
                        if (p !== this && p.alive) {
                            const d = distance(this.x, this.y, p.x, p.y);
                            if (d < minDist) { minDist = d; closest = p; }
                        }
                    });

                    if (keys[this.controls.shoot]) {
                        this.weapon.tryShoot(nowMs, this, closest);
                    }
                }
                takeDamage(amount) {
                    if (this.godMode || !this.alive) return;
                    if (this.shield > 0) {
                        this.shield -= amount;
                        if (this.shield < 0) {
                            this.health += this.shield;
                            this.shield = 0;
                        }
                    } else {
                        this.health -= amount;
                    }
                    if (this.health <= 0) {
                        this.health = 0;
                        this.alive = false;
                    }
                }
                draw() {
                    if (!this.alive) return;
                    ctx.fillStyle = this.color;
                    ctx.beginPath(); ctx.arc(this.x, this.y, PLAYER_SIZE / 2, 0, Math.PI * 2); ctx.fill();

                    // Ausrichtung anzeigen
                    ctx.strokeStyle = '#fff';
                    ctx.lineWidth = 3;
                    ctx.beginPath();
                    ctx.moveTo(this.x, this.y);
                    ctx.lineTo(this.x + this.aimDir.x * 20, this.y + this.aimDir.y * 20);
                    ctx.stroke();

                    // Statusleiste
                    ctx.fillStyle = '#ff4444';
                    ctx.fillRect(this.x - 20, this.y - 25, 40 * (this.health / 300), 4);
                    ctx.fillStyle = '#00aaff';
                    ctx.fillRect(this.x - 20, this.y - 20, 40 * (this.shield / 200), 4);
                }
            }

            const players = [
                new Player(1, 100, HEIGHT / 2, '#0d9488', { up: 'KeyW', down: 'KeyS', left: 'KeyA', right: 'KeyD', shoot: 'Space' }),
                new Player(2, WIDTH - 100, HEIGHT / 2, '#e11d48', { up: 'ArrowUp', down: 'ArrowDown', left: 'ArrowLeft', right: 'ArrowRight', shoot: 'Enter' })
            ];

            // Owner Menü & Logik
            const secretBtn = document.getElementById('openSecretBtn');
            const passModal = document.getElementById('passwordModal');
            const passInput = document.getElementById('ownerPassInput');
            const submitPassBtn = document.getElementById('submitPassBtn');
            const closePassBtn = document.getElementById('closePassBtn');
            const ownerDash = document.getElementById('ownerDashboard');

            secretBtn.addEventListener('click', () => passModal.classList.add('active'));
            closePassBtn.addEventListener('click', () => passModal.classList.remove('active'));

            submitPassBtn.addEventListener('click', () => {
                if (passInput.value === 'owner123') {
                    passModal.classList.remove('active');
                    ownerDash.style.display = 'block';
                } else {
                    alert('Falsches Passwort!');
                }
            });

            window.ownerGodMode = function(pId) {
                const p = players.find(x => x.id === pId);
                if (p) { p.godMode = true; p.health = 300; p.shield = 200; alert('God Mode für P' + pId + ' aktiviert!'); }
            };

            window.ownerGiveWeapon = function(pId, type) {
                const p = players.find(x => x.id === pId);
                if (p) {
                    if (type === 'Minigun') p.weapon = new Minigun();
                    if (type === 'RocketLauncher') p.weapon = new RocketLauncher();
                    alert(type + ' für P' + pId + ' ausgerüstet!');
                }
            };

            window.ownerNukeEnemies = function(pId) {
                players.forEach(p => { if (p.id !== pId) p.takeDamage(9999); });
            };

            // Game Loop
            function gameLoop(time) {
                ctx.clearRect(0, 0, WIDTH, HEIGHT);

                // Grid zeichnen
                ctx.strokeStyle = '#1f232d';
                ctx.lineWidth = 1;
                for (let x = 0; x < WIDTH; x += 40) { ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, HEIGHT); ctx.stroke(); }
                for (let y = 0; y < HEIGHT; y += 40) { ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(WIDTH, y); ctx.stroke(); }

                players.forEach(p => {
                    p.handleInput(time);
                    p.draw();
                });

                bullets.forEach(b => {
                    b.update();
                    b.draw();
                    players.forEach(p => {
                        if (p.id !== b.ownerId && p.alive && distance(b.x, b.y, p.x, p.y) < PLAYER_SIZE / 2 + b.size / 2) {
                            p.takeDamage(b.damage);
                            b.alive = false;
                        }
                    });
                });

                bullets = bullets.filter(b => b.alive);

                requestAnimationFrame(gameLoop);
            }

            requestAnimationFrame(gameLoop);
        </script>
    </body>
    </html>
    """

    components.html(game_html, height=560)
