from flask import Response
from datetime import datetime
from xml.sax.saxutils import escape
import os


# ==========================================
# WAVE BEATZ SEO CONFIGURATION
# ==========================================

# Use the real public domain when available.
# Falls back to the local Flask server for testing.
SITE_URL = os.getenv(
    "SITE_URL",
    "http://127.0.0.1:8080"
).rstrip("/")


def register_seo_routes(app, get_db):

    # ==========================================
    # ROBOTS.TXT
    # ==========================================

    # Make the configured public site URL available
    # to all active templates.
    @app.context_processor
    def inject_site_url():
        return {
            "site_url": SITE_URL
        }

    @app.route("/robots.txt")
    def robots_txt():

        content = (
            "User-agent: *\n"
            "Allow: /\n"
            "Disallow: /admin\n"
            "Disallow: /api/\n"
            f"Sitemap: {SITE_URL}/sitemap.xml\n"
        )

        return Response(
            content,
            status=200,
            mimetype="text/plain"
        )

    # ==========================================
    # SITEMAP.XML
    # ==========================================

    @app.route("/sitemap.xml")
    def sitemap_xml():

        db = get_db()

        beats = db.execute(
            """
            SELECT id
            FROM beats
            ORDER BY id DESC
            """
        ).fetchall()

        db.close()

        today = datetime.utcnow().strftime("%Y-%m-%d")

        pages = [
            {
                "url": SITE_URL + "/",
                "priority": "1.0"
            },
            {
                "url": SITE_URL + "/trap",
                "priority": "0.8"
            },
            {
                "url": SITE_URL + "/afrobeat",
                "priority": "0.8"
            },
            {
                "url": SITE_URL + "/hip-hop",
                "priority": "0.8"
            },
            {
                "url": SITE_URL + "/dancehall",
                "priority": "0.8"
            },
            {
                "url": SITE_URL + "/rnb",
                "priority": "0.8"
            }
        ]

        # ==========================================
        # BEAT PAGES
        # ==========================================

        for beat in beats:

            pages.append(
                {
                    "url": f'{SITE_URL}/beat/{beat["id"]}',
                    "priority": "0.9"
                }
            )

        # ==========================================
        # BUILD XML
        # ==========================================

        xml = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        ]

        for page in pages:

            safe_url = escape(page["url"])

            xml.append("    <url>")

            xml.append(
                f"        <loc>{safe_url}</loc>"
            )

            xml.append(
                f"        <lastmod>{today}</lastmod>"
            )

            xml.append(
                "        <changefreq>weekly</changefreq>"
            )

            xml.append(
                f'        <priority>{page["priority"]}</priority>'
            )

            xml.append("    </url>")

        xml.append("</urlset>")

        return Response(
            "\n".join(xml),
            status=200,
            mimetype="application/xml"
        )
