from flask import Flask, render_template, request, jsonify, redirect, send_from_directory
from dotenv import load_dotenv
import sqlite3
import os
import re
import base64
import requests
from werkzeug.utils import secure_filename

# ==========================================
# WAVE BEATZ - DJ WAVY
# Flask Backend
# ==========================================

load_dotenv()

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

from seo_routes import register_seo_routes

app = Flask(
    __name__,
    template_folder="templates",
    static_folder="static"
)

# ==========================================
# STAGE 8 — CUSTOMER ACCOUNT SESSIONS
# ==========================================

app.secret_key = os.getenv(
    "WAVE_BEATZ_SECRET_KEY",
    "wave-beatz-development-secret-change-later"
)

app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

# ==========================================
# PATHS
# ==========================================

DB_PATH = os.path.join(
    BASE_DIR,
    "database",
    "wave_beatz.db"
)

IMAGE_DIR = os.path.join(
    BASE_DIR,
    "static",
    "images"
)

AUDIO_DIR = os.path.join(
    BASE_DIR,
    "static",
    "audio"
)

os.makedirs(
    os.path.dirname(DB_PATH),
    exist_ok=True
)

os.makedirs(
    IMAGE_DIR,
    exist_ok=True
)

os.makedirs(
    AUDIO_DIR,
    exist_ok=True
)


# ==========================================
# FILE SETTINGS
# ==========================================

ALLOWED_AUDIO_EXTENSIONS = {
    "mp3",
    "wav",
    "m4a",
    "ogg"
}

ALLOWED_IMAGE_EXTENSIONS = {
    "jpg",
    "jpeg",
    "png",
    "webp"
}


def allowed_file(filename, allowed_extensions):

    return (
        "." in filename
        and filename.rsplit(
            ".",
            1
        )[1].lower()
        in allowed_extensions
    )


# ==========================================
# DATABASE
# ==========================================

def get_db():

    conn = sqlite3.connect(DB_PATH)

    conn.row_factory = sqlite3.Row

    return conn


def init_db():

    conn = get_db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS beats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            genre TEXT,
            bpm INTEGER,
            mood TEXT,
            audio_file TEXT,
            artwork_file TEXT,
            created_at TIMESTAMP
                DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # --------------------------------------
    # STAGE 5 DATABASE COLUMNS
    # --------------------------------------

    columns = conn.execute(
        "PRAGMA table_info(beats)"
    ).fetchall()

    column_names = {
        column["name"]
        for column in columns
    }

    if "featured" not in column_names:

        conn.execute("""
            ALTER TABLE beats
            ADD COLUMN featured
            INTEGER NOT NULL DEFAULT 0
        """)

    if "dj_wavy_pick" not in column_names:

        conn.execute("""
            ALTER TABLE beats
            ADD COLUMN dj_wavy_pick
            INTEGER NOT NULL DEFAULT 0
        """)

    # --------------------------------------
    # STAGE 8A — CUSTOMER ACCOUNTS
    # --------------------------------------

    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            phone TEXT,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()

    conn.close()


# ==========================================
# HELPERS
# ==========================================

def slugify(text):

    text = text.lower().strip()

    text = re.sub(
        r"[^a-z0-9]+",
        "-",
        text
    )

    return text.strip("-")


def unique_filename(directory, filename):

    base, extension = os.path.splitext(
        filename
    )

    candidate = filename

    counter = 2

    while os.path.exists(
        os.path.join(
            directory,
            candidate
        )
    ):

        candidate = (
            f"{base}-{counter}"
            f"{extension}"
        )

        counter += 1

    return candidate


# ==========================================
# PUBLIC WEBSITE
# ==========================================

@app.route("/")
def home():

    conn = get_db()

    # --------------------------------------
    # MAIN CATALOGUE
    # --------------------------------------

    beats = conn.execute("""
        SELECT *
        FROM beats
        ORDER BY id DESC
    """).fetchall()

    # --------------------------------------
    # FEATURED BEATS
    # --------------------------------------

    featured_beats = conn.execute("""
        SELECT *
        FROM beats
        WHERE featured = 1
        ORDER BY id DESC
        LIMIT 6
    """).fetchall()

    # --------------------------------------
    # NEW DROPS
    # --------------------------------------

    new_drops = conn.execute("""
        SELECT *
        FROM beats
        ORDER BY id DESC
        LIMIT 6
    """).fetchall()

    # --------------------------------------
    # DJ WAVY PICKS
    # --------------------------------------

    dj_wavy_picks = conn.execute("""
        SELECT *
        FROM beats
        WHERE dj_wavy_pick = 1
        ORDER BY id DESC
        LIMIT 6
    """).fetchall()

    conn.close()

    return render_template(
        "index.html",
        beats=beats,
        current_genre=None,
        featured_beats=featured_beats,
        new_drops=new_drops,
        dj_wavy_picks=dj_wavy_picks
    )


# ==========================================
# INDIVIDUAL BEAT PAGE
# ==========================================

@app.route("/beat/<int:beat_id>")
def beat_detail(beat_id):

    conn = get_db()

    beat = conn.execute(
        """
        SELECT *
        FROM beats
        WHERE id = ?
        """,
        (beat_id,)
    ).fetchone()

    if not beat:

        conn.close()

        return (
            render_template(
                "beat-not-found.html"
            ),
            404
        )

    related_beats = conn.execute(
        """
        SELECT *
        FROM beats
        WHERE genre = ?
        AND id != ?
        ORDER BY id DESC
        LIMIT 6
        """,
        (
            beat["genre"],
            beat["id"]
        )
    ).fetchall()

    # If there are no beats from the same genre,
    # show other recent beats instead.
    if not related_beats:
        related_beats = conn.execute(
            """
            SELECT *
            FROM beats
            WHERE id != ?
            ORDER BY id DESC
            LIMIT 6
            """,
            (
                beat["id"],
            )
        ).fetchall()

    conn.close()

    return render_template(
        "beat.html",
        beat=beat,
        related_beats=related_beats
    )


# ==========================================
# LICENSE STORE
# ==========================================

@app.route("/licenses")
def license_store():

    conn = get_db()

    beats = conn.execute(
        "SELECT * FROM beats ORDER BY id DESC"
    ).fetchall()

    selected_beat_id = request.args.get(
        "beat_id",
        type=int
    )

    selected_license = request.args.get(
        "license",
        default=""
    ).lower()

    if selected_license not in (
        "basic",
        "premium",
        "exclusive"
    ):
        selected_license = ""

    selected_beat = None

    if selected_beat_id:

        selected_beat = conn.execute(
            "SELECT * FROM beats WHERE id = ?",
            (selected_beat_id,)
        ).fetchone()

    conn.close()

    if selected_beat and selected_license:
        return redirect(
            f"/beat/{selected_beat['id']}#license-{selected_license}"
        )

    return render_template(
        "licenses.html",
        beats=beats,
        selected_beat=selected_beat,
        selected_license=selected_license
    )


# ==========================================
# INDIVIDUAL BEAT DOWNLOAD
# ==========================================

@app.route(
    "/beat/<int:beat_id>/download"
)
def download_beat(beat_id):

    conn = get_db()

    beat = conn.execute(
        """
        SELECT *
        FROM beats
        WHERE id = ?
        """,
        (beat_id,)
    ).fetchone()

    conn.close()

    if not beat:

        return jsonify({
            "success": False,
            "error":
                "Beat not found."
        }), 404

    audio_file = beat["audio_file"]

    if not audio_file:

        return jsonify({
            "success": False,
            "error":
                "Audio file not available."
        }), 404

    filename = os.path.basename(
        audio_file
    )

    file_path = os.path.join(
        AUDIO_DIR,
        filename
    )

    if not os.path.isfile(file_path):

        return jsonify({
            "success": False,
            "error":
                "Audio file not found."
        }), 404

    download_name = (
        slugify(beat["title"])
        or "wave-beatz"
    )

    extension = os.path.splitext(
        filename
    )[1].lower()

    download_name += extension

    return send_from_directory(
        AUDIO_DIR,
        filename,
        as_attachment=True,
        download_name=download_name
    )


# ==========================================
# GENRE PAGE HELPER
# ==========================================

def genre_page(genre_name):

    conn = get_db()

    beats = conn.execute(
        """
        SELECT *
        FROM beats
        WHERE LOWER(genre) = LOWER(?)
        ORDER BY id DESC
        """,
        (genre_name,)
    ).fetchall()

    conn.close()

    return render_template(
        "index.html",
        beats=beats,
        current_genre=genre_name,
        featured_beats=[],
        new_drops=[],
        dj_wavy_picks=[]
    )


# ==========================================
# GENRE PAGES
# ==========================================

@app.route("/trap")
def trap():

    return genre_page("TRAP")


@app.route("/afrobeat")
def afrobeat():

    return genre_page("AFROBEAT")


@app.route("/hip-hop")
def hip_hop():

    return genre_page("HIP-HOP")


@app.route("/dancehall")
def dancehall():

    return genre_page("DANCEHALL")


@app.route("/rnb")
def rnb():

    return genre_page("R&B")


# ==========================================
# ADMIN PAGE
# ==========================================

@app.route("/admin")
def admin():

    return render_template(
        "admin.html"
    )


# ==========================================
# BEAT API
# ==========================================

@app.route("/api/beats")
def get_beats():

    conn = get_db()

    beats = conn.execute("""
        SELECT *
        FROM beats
        ORDER BY id DESC
    """).fetchall()

    conn.close()

    return jsonify([
        dict(beat)
        for beat in beats
    ])


# ==========================================
# ADD NEW BEAT
# ==========================================

@app.route(
    "/api/add-beat",
    methods=["POST"]
)
def add_beat():

    title = request.form.get(
        "title",
        ""
    ).strip()

    genre = request.form.get(
        "genre",
        ""
    ).strip()

    mood = request.form.get(
        "mood",
        ""
    ).strip()

    bpm = request.form.get(
        "bpm",
        ""
    ).strip()

    audio_file = request.files.get(
        "audio"
    )

    artwork_file = request.files.get(
        "artwork"
    )

    # --------------------------------------
    # BASIC VALIDATION
    # --------------------------------------

    if not title:

        return jsonify({
            "success": False,
            "error":
                "Beat title is required."
        }), 400

    if not audio_file:

        return jsonify({
            "success": False,
            "error":
                "MP3/audio file is required."
        }), 400

    if not allowed_file(
        audio_file.filename,
        ALLOWED_AUDIO_EXTENSIONS
    ):

        return jsonify({
            "success": False,
            "error":
                "Unsupported audio format. "
                "Use MP3, WAV, M4A or OGG."
        }), 400

    # --------------------------------------
    # BPM VALIDATION
    # --------------------------------------

    bpm_value = None

    if bpm:

        try:

            bpm_value = int(bpm)

        except ValueError:

            return jsonify({
                "success": False,
                "error":
                    "BPM must be a number."
            }), 400

    # --------------------------------------
    # CREATE AUDIO FILENAME
    # --------------------------------------

    base_name = slugify(title)

    if not base_name:

        base_name = "beat"

    audio_extension = os.path.splitext(
        secure_filename(
            audio_file.filename
        )
    )[1].lower()

    audio_filename = (
        base_name +
        audio_extension
    )

    audio_filename = unique_filename(
        AUDIO_DIR,
        audio_filename
    )

    audio_path = os.path.join(
        AUDIO_DIR,
        audio_filename
    )

    # --------------------------------------
    # SAVE AUDIO
    # --------------------------------------

    audio_file.save(
        audio_path
    )

    # --------------------------------------
    # SAVE ARTWORK
    # --------------------------------------

    artwork_filename = ""

    if (
        artwork_file
        and artwork_file.filename
    ):

        if not allowed_file(
            artwork_file.filename,
            ALLOWED_IMAGE_EXTENSIONS
        ):

            if os.path.exists(
                audio_path
            ):

                os.remove(
                    audio_path
                )

            return jsonify({
                "success": False,
                "error":
                    "Unsupported artwork format."
            }), 400

        artwork_extension = (
            os.path.splitext(
                secure_filename(
                    artwork_file.filename
                )
            )[1].lower()
        )

        artwork_filename = (
            base_name +
            artwork_extension
        )

        artwork_filename = unique_filename(
            IMAGE_DIR,
            artwork_filename
        )

        artwork_path = os.path.join(
            IMAGE_DIR,
            artwork_filename
        )

        artwork_file.save(
            artwork_path
        )

    # --------------------------------------
    # SAVE TO DATABASE
    # --------------------------------------

    conn = get_db()

    cursor = conn.execute(
        """
        INSERT INTO beats (
            title,
            genre,
            bpm,
            mood,
            audio_file,
            artwork_file,
            featured,
            dj_wavy_pick
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            title,
            genre,
            bpm_value,
            mood,
            "audio/" + audio_filename,
            artwork_filename,
            0,
            0
        )
    )

    conn.commit()

    beat_id = cursor.lastrowid

    conn.close()

    # --------------------------------------
    # SUCCESS
    # --------------------------------------

    return jsonify({
        "success": True,
        "message":
            "Beat added successfully.",
        "beat_id":
            beat_id,
        "title":
            title,
        "audio_file":
            "audio/" + audio_filename,
        "artwork_file":
            artwork_filename
    })


# ==========================================
# AI COVER GENERATOR
# ==========================================

@app.route(
    "/api/generate-cover",
    methods=["POST"]
)
def generate_cover():

    api_key = os.environ.get(
        "OPENAI_API_KEY"
    )

    if not api_key:

        return jsonify({
            "success": False,
            "error":
                "OPENAI_API_KEY is not configured."
        }), 500

    data = request.get_json(
        silent=True
    ) or {}

    title = data.get(
        "title",
        ""
    ).strip()

    genre = data.get(
        "genre",
        ""
    ).strip()

    mood = data.get(
        "mood",
        ""
    ).strip()

    bpm = data.get(
        "bpm",
        ""
    )

    if not title:

        return jsonify({
            "success": False,
            "error":
                "Beat title is required."
        }), 400

    prompt = f"""
Create premium professional square
music cover artwork for a beat.

Beat title:
{title}

Genre:
{genre or "Modern urban music"}

Mood:
{mood or "Atmospheric and stylish"}

BPM:
{bpm or "Not specified"}

Brand:
DJ WAVY / WAVE BEATZ

Create completely original artwork
for a professional beat marketplace.

The artwork should visually match
the beat title, genre and mood.

Use a dark cinematic music aesthetic.

Use modern urban influences and,
where appropriate, African-inspired
visual elements.

Use dramatic lighting.

Use deep shadows.

Use premium composition.

Use strong depth.

Use high contrast.

Use tasteful gold, black and neutral
accents.

Make the artwork look professional
and suitable for an official music
brand.

Display the beat title prominently.

Display DJ WAVY as smaller branding.

Do NOT use another artist's logo.

Do NOT use another company's logo.

Do NOT imitate a specific living artist.

Do NOT create a website screenshot.

Do NOT create a phone mockup.

Do NOT create a CD mockup.

Do NOT create a vinyl mockup.

Do NOT create a poster mockup.

Create clean square album artwork.
"""

    try:

        response = requests.post(
            "https://api.openai.com/v1/images/generations",
            headers={
                "Authorization":
                    f"Bearer {api_key}",
                "Content-Type":
                    "application/json"
            },
            json={
                "model":
                    "gpt-image-2",
                "prompt":
                    prompt,
                "size":
                    "1024x1024",
                "quality":
                    "low",
                "output_format":
                    "webp",
                "output_compression":
                    70
            },
            timeout=180
        )

        if response.status_code != 200:

            try:

                error_data = (
                    response.json()
                )

            except Exception:

                error_data = (
                    response.text
                )

            return jsonify({
                "success": False,
                "error":
                    f"Image API error: "
                    f"{error_data}"
            }), response.status_code

        result = response.json()

        image_data = (
            result["data"][0]["b64_json"]
        )

        filename = slugify(title)

        if not filename:

            filename = "beat-cover"

        image_path = os.path.join(
            IMAGE_DIR,
            f"{filename}.webp"
        )

        with open(
            image_path,
            "wb"
        ) as image_file:

            image_file.write(
                base64.b64decode(
                    image_data
                )
            )

        return jsonify({
            "success": True,
            "filename":
                f"{filename}.webp",
            "url":
                f"/static/images/"
                f"{filename}.webp"
        })

    except Exception as error:

        return jsonify({
            "success": False,
            "error": str(error)
        }), 500


# ==========================================
# START SERVER
# ==========================================


# ==========================================
# STAGE 8 — CUSTOMER ACCOUNT ROUTES
# ==========================================

from account_routes import register_account_routes

register_account_routes(
    app,
    get_db
)


# ==========================================
# STAGE 7 — ECOCASH PAYMENT ROUTES
# ==========================================

from ecocash_routes import register_ecocash_routes

register_ecocash_routes(
    app,
    get_db,
    AUDIO_DIR,
    slugify
)


register_seo_routes(app, get_db)


# ==========================================
# START FLASK SERVER
# ==========================================

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=8080,
        debug=False
    )
