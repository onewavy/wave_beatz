from flask import request, jsonify, send_from_directory
import os
import re
import secrets
import sqlite3
import requests
from datetime import datetime, timedelta


# ==========================================
# ECOCASH CONFIGURATION
# ==========================================

ECOCASH_BASE_URL = os.environ.get(
    "ECOCASH_BASE_URL", ""
).rstrip("/")

ECOCASH_USERNAME = os.environ.get(
    "ECOCASH_USERNAME", ""
)

ECOCASH_PASSWORD = os.environ.get(
    "ECOCASH_PASSWORD", ""
)

ECOCASH_MERCHANT_CODE = os.environ.get(
    "ECOCASH_MERCHANT_CODE", ""
)

ECOCASH_MERCHANT_PIN = os.environ.get(
    "ECOCASH_MERCHANT_PIN", ""
)

ECOCASH_MERCHANT_NUMBER = os.environ.get(
    "ECOCASH_MERCHANT_NUMBER", ""
)

# Sandbox terminal ID from EcoCash Playground
ECOCASH_TERMINAL_ID = os.environ.get(
    "ECOCASH_TERMINAL_ID", "UAT00003"
)

ECOCASH_COUNTRY_CODE = os.environ.get(
    "ECOCASH_COUNTRY_CODE", "ZW"
)

ECOCASH_CURRENCY = os.environ.get(
    "ECOCASH_CURRENCY", "USD"
)

ECOCASH_LOCATION = os.environ.get(
    "ECOCASH_LOCATION", "Harare"
)

# Playground merchant information
ECOCASH_SUPER_MERCHANT_NAME = os.environ.get(
    "ECOCASH_SUPER_MERCHANT_NAME", "ECOCASH"
)

ECOCASH_MERCHANT_NAME = os.environ.get(
    "ECOCASH_MERCHANT_NAME", "UAT STORE 3"
)


# ==========================================
# LICENSE PRICES
# ==========================================

LICENSE_PRICES = {
    "basic": 7.89,
    "premium": 15.40,
    "exclusive": 24.99,
}

LICENSE_NAMES = {
    "basic": "BASIC LEASE",
    "premium": "PREMIUM LEASE",
    "exclusive": "EXCLUSIVE",
}


# ==========================================
# HELPERS
# ==========================================

def normalize_phone(phone):
    """
    Accept:
      0771234567
      771234567
      263771234567
      00263771234567
      +263771234567

    Return:
      263771234567
    """

    phone = str(phone or "").strip()

    phone = re.sub(r"[^\d+]", "", phone)

    if phone.startswith("+263"):
        phone = phone[1:]

    elif phone.startswith("00263"):
        phone = phone[2:]

    elif phone.startswith("0"):
        phone = "263" + phone[1:]

    elif phone.startswith("263"):
        pass

    elif re.fullmatch(r"7\d{8}", phone):
        phone = "263" + phone

    if not re.fullmatch(r"2637\d{8}", phone):
        return None

    return phone


def valid_email(email):
    email = str(email or "").strip()

    return bool(
        re.fullmatch(
            r"[^@\s]+@[^@\s]+\.[^@\s]+",
            email
        )
    )


def ecocash_configured():
    """
    Check the credentials required to contact EcoCash.

    terminalID has a sandbox default of UAT00003.
    """

    required = {
        "ECOCASH_BASE_URL": ECOCASH_BASE_URL,
        "ECOCASH_USERNAME": ECOCASH_USERNAME,
        "ECOCASH_PASSWORD": ECOCASH_PASSWORD,
        "ECOCASH_MERCHANT_CODE": ECOCASH_MERCHANT_CODE,
        "ECOCASH_MERCHANT_PIN": ECOCASH_MERCHANT_PIN,
        "ECOCASH_MERCHANT_NUMBER": ECOCASH_MERCHANT_NUMBER,
        "ECOCASH_TERMINAL_ID": ECOCASH_TERMINAL_ID,
        "ECOCASH_COUNTRY_CODE": ECOCASH_COUNTRY_CODE,
        "ECOCASH_CURRENCY": ECOCASH_CURRENCY,
        "ECOCASH_LOCATION": ECOCASH_LOCATION,
        "ECOCASH_MERCHANT_NAME": ECOCASH_MERCHANT_NAME,
    }

    missing = [
        key
        for key, value in required.items()
        if not str(value).strip()
    ]

    return missing


def extract_status(data):
    """
    Try several possible EcoCash response locations
    because sandbox/API responses can differ.
    """

    if not isinstance(data, dict):
        return ""

    possible = [
        data.get("transactionOperationStatus"),
        data.get("status"),
        data.get("paymentStatus"),
        data.get("ecocash_status"),
    ]

    transaction = data.get("transactionOperationStatus")

    if isinstance(transaction, dict):
        possible.extend([
            transaction.get("status"),
            transaction.get("code"),
            transaction.get("description"),
        ])

    for value in possible:
        if value:
            return str(value).strip().upper()

    return ""


def ecocash_charge(
    client_correlator,
    reference_code,
    phone,
    amount,
    beat_title
):
    """
    Send payment request to EcoCash.
    """

    missing = ecocash_configured()

    if missing:
        return {
            "success": False,
            "error": "EcoCash configuration is incomplete.",
            "missing": missing,
        }

    payload = {
        "clientCorrelator": client_correlator,
        "referenceCode": reference_code,

        # Sandbox payment request
        "tranType": "MER",
        "endUserId": phone,

        "remarks": f"WAVE BEATZ - {beat_title}",

        "transactionOperationStatus": "Charged",

        "paymentAmount": {
            "charginginformation": {
                "amount": amount,
                "currency": ECOCASH_CURRENCY,
                "description": f"WAVE BEATZ - {beat_title}",
            },

            "chargeMetaData": {
                "channel": "WEB",
                "purchaseCategoryCode": "Music License",
                "onBeHalfOf": "DJ WAVY",
            },
        },

        # EcoCash merchant information
        "merchantCode": ECOCASH_MERCHANT_CODE,
        "merchantPin": ECOCASH_MERCHANT_PIN,
        "merchantNumber": ECOCASH_MERCHANT_NUMBER,

        "countryCode": ECOCASH_COUNTRY_CODE,

        # Required by the sandbox
        "terminalID": ECOCASH_TERMINAL_ID,

        "location": ECOCASH_LOCATION,

        # Required by the sandbox
        "superMerchantName": ECOCASH_SUPER_MERCHANT_NAME,
        "merchantName": ECOCASH_MERCHANT_NAME,
    }

    url = ECOCASH_BASE_URL + "/transactions/amount/"

    try:

        response = requests.post(
            url,
            json=payload,
            auth=(
                ECOCASH_USERNAME,
                ECOCASH_PASSWORD
            ),
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            timeout=45,
        )

        try:
            data = response.json()
        except ValueError:
            data = {
                "raw_response": response.text
            }

        if response.status_code != 200:

            return {
                "success": False,
                "error": "EcoCash charge request failed.",
                "http_status": response.status_code,

                # Keep sandbox debugging information for now.
                "details": data,
            }

        return {
            "success": True,
            "http_status": response.status_code,
            "data": data,
        }

    except requests.RequestException as exc:

        return {
            "success": False,
            "error": "Could not connect to EcoCash.",
            "details": str(exc),
        }


def ecocash_lookup(
    phone,
    client_correlator
):
    """
    Look up an EcoCash transaction.
    """

    missing = ecocash_configured()

    if missing:
        return {
            "success": False,
            "error": "EcoCash configuration is incomplete.",
            "missing": missing,
        }

    url = (
        ECOCASH_BASE_URL
        + "/"
        + phone
        + "/transactions/amount/"
        + client_correlator
    )

    try:

        response = requests.get(
            url,
            auth=(
                ECOCASH_USERNAME,
                ECOCASH_PASSWORD
            ),
            headers={
                "Accept": "application/json",
            },
            timeout=45,
        )

        try:
            data = response.json()
        except ValueError:
            data = {
                "raw_response": response.text
            }

        if response.status_code != 200:

            return {
                "success": False,
                "error": "EcoCash transaction lookup failed.",
                "http_status": response.status_code,
                "details": data,
            }

        return {
            "success": True,
            "http_status": response.status_code,
            "data": data,
        }

    except requests.RequestException as exc:

        return {
            "success": False,
            "error": "Could not connect to EcoCash.",
            "details": str(exc),
        }


# ==========================================
# REGISTER ECOCASH ROUTES
# ==========================================

def register_ecocash_routes(
    app,
    get_db,
    audio_dir,
    slugify
):

    # ======================================
    # LICENSE AVAILABILITY
    # ======================================

    @app.route(
        "/api/ecocash/license-availability/<int:beat_id>",
        methods=["GET"]
    )
    def license_availability(beat_id):

        db = get_db()

        beat = db.execute(
            """
            SELECT id
            FROM beats
            WHERE id = ?
            """,
            (beat_id,)
        ).fetchone()

        if not beat:
            db.close()

            return jsonify({
                "success": False,
                "error": "Beat not found.",
            }), 404

        paid_orders = db.execute(
            """
            SELECT license_type
            FROM orders
            WHERE beat_id = ?
              AND payment_status = 'PAID'
              AND license_type IN ('premium', 'exclusive')
            """,
            (beat_id,)
        ).fetchall()

        paid_types = {
            row["license_type"]
            for row in paid_orders
        }

        exclusive_sold = "exclusive" in paid_types
        premium_sold = (
            "premium" in paid_types
            or exclusive_sold
        )

        # Basic disappears once Premium or Exclusive
        # has been successfully purchased.
        basic_available = not (
            premium_sold
            or exclusive_sold
        )

        premium_available = not (
            premium_sold
            or exclusive_sold
        )

        exclusive_available = not exclusive_sold

        db.close()

        return jsonify({
            "success": True,
            "beat_id": beat_id,
            "basic": {
                "available": basic_available,
                "sold": not basic_available,
            },
            "premium": {
                "available": premium_available,
                "sold": not premium_available,
            },
            "exclusive": {
                "available": exclusive_available,
                "sold": not exclusive_available,
            },
        })



    # ======================================
    # CREATE ECOCASH ORDER
    # ======================================

    @app.route(
        "/api/ecocash/create-order",
        methods=["POST"]
    )
    def create_ecocash_order():

        data = request.get_json(
            silent=True
        ) or {}

        beat_id = data.get("beat_id")
        license_type = str(
            data.get("license_type", "")
        ).strip().lower()

        artist_name = str(
            data.get("artist_name", "")
        ).strip()

        buyer_email = str(
            data.get("buyer_email", "")
        ).strip()

        buyer_phone = normalize_phone(
            data.get("buyer_phone")
        )

        buyer_message = str(
            data.get("buyer_message", "")
        ).strip()

        # ----------------------------------
        # Validate license
        # ----------------------------------

        if license_type not in LICENSE_PRICES:

            return jsonify({
                "success": False,
                "error": "Invalid license type.",
            }), 400

        # ----------------------------------
        # Validate artist
        # ----------------------------------

        if not artist_name:

            return jsonify({
                "success": False,
                "error": "Artist name is required.",
            }), 400

        # ----------------------------------
        # Validate email
        # ----------------------------------

        if not valid_email(buyer_email):

            return jsonify({
                "success": False,
                "error": "A valid buyer email is required.",
            }), 400

        # ----------------------------------
        # Validate phone
        # ----------------------------------

        if not buyer_phone:

            return jsonify({
                "success": False,
                "error": (
                    "Enter a valid Zimbabwe EcoCash "
                    "mobile number."
                ),
            }), 400

        # ----------------------------------
        # Validate beat ID
        # ----------------------------------

        try:
            beat_id = int(beat_id)
        except (TypeError, ValueError):

            return jsonify({
                "success": False,
                "error": "Invalid beat ID.",
            }), 400

        db = get_db()

        beat = db.execute(
            """
            SELECT *
            FROM beats
            WHERE id = ?
            """,
            (beat_id,)
        ).fetchone()

        if not beat:

            db.close()

            return jsonify({
                "success": False,
                "error": "Beat not found.",
            }), 404

        beat_title = beat["title"]

        # ----------------------------------
        # CHECK LICENSE SALE STATUS
        # ----------------------------------

        paid_license = db.execute(
            """
            SELECT license_type
            FROM orders
            WHERE beat_id = ?
              AND payment_status = 'PAID'
              AND license_type IN ('premium', 'exclusive')
            """,
            (beat_id,)
        ).fetchall()

        paid_license_types = {
            row["license_type"]
            for row in paid_license
        }

        exclusive_sold = (
            "exclusive" in paid_license_types
        )

        premium_sold = (
            "premium" in paid_license_types
            or exclusive_sold
        )

        # Basic disappears after a successful
        # Premium or Exclusive purchase.
        if license_type == "basic" and premium_sold:

            db.close()

            return jsonify({
                "success": False,
                "error": (
                    "Basic Lease is no longer available "
                    "for this beat."
                ),
                "license_sold": True,
            }), 409

        # Premium becomes unavailable once Premium
        # or Exclusive has already been purchased.
        if license_type == "premium" and premium_sold:

            db.close()

            return jsonify({
                "success": False,
                "error": (
                    "Premium Lease has already been sold "
                    "for this beat."
                ),
                "license_sold": True,
            }), 409

        # Exclusive becomes unavailable after it is sold.
        if license_type == "exclusive" and exclusive_sold:

            db.close()

            return jsonify({
                "success": False,
                "error": (
                    "Exclusive rights have already been "
                    "sold for this beat."
                ),
                "license_sold": True,
            }), 409

        amount = LICENSE_PRICES[
            license_type
        ]

        # ----------------------------------
        # Generate unique references
        # ----------------------------------

        random_part = secrets.token_hex(4).upper()

        client_correlator = (
            f"WB{beat_id}"
            f"{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
            f"{random_part}"
        )

        reference_code = (
            f"WB-{beat_id}-"
            f"{datetime.utcnow().strftime('%H%M%S')}-"
            f"{random_part}"
        )

        # ----------------------------------
        # Create pending order
        # ----------------------------------

        cursor = db.execute(
            """
            INSERT INTO orders (
                beat_id,
                license_type,
                artist_name,
                buyer_email,
                buyer_phone,
                buyer_message,
                amount,
                currency,
                client_correlator,
                reference_code,
                payment_status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                beat_id,
                license_type,
                artist_name,
                buyer_email,
                buyer_phone,
                buyer_message,
                amount,
                ECOCASH_CURRENCY,
                client_correlator,
                reference_code,
                "PENDING",
            )
        )

        order_id = cursor.lastrowid

        db.commit()
        db.close()

        # ----------------------------------
        # Send EcoCash payment request
        # ----------------------------------

        payment = ecocash_charge(
            client_correlator=client_correlator,
            reference_code=reference_code,
            phone=buyer_phone,
            amount=amount,
            beat_title=beat_title,
        )

        if not payment.get("success"):

            db = get_db()

            db.execute(
                """
                UPDATE orders
                SET payment_status = ?
                WHERE id = ?
                """,
                (
                    "FAILED",
                    order_id,
                )
            )

            db.commit()
            db.close()

            return jsonify({
                "success": False,
                "error": payment.get(
                    "error",
                    "EcoCash payment request failed."
                ),
                "order_id": order_id,
                "http_status": payment.get(
                    "http_status"
                ),
                "details": payment.get(
                    "details"
                ),
            }), 502

        response_data = payment.get(
            "data",
            {}
        )

        status = extract_status(
            response_data
        )

        # ----------------------------------
        # Save EcoCash status/reference
        # ----------------------------------

        ecocash_transaction_id = None
        ecocash_server_reference = None

        if isinstance(response_data, dict):

            ecocash_transaction_id = (
                response_data.get(
                    "transactionId"
                )
                or response_data.get(
                    "transactionID"
                )
                or response_data.get(
                    "transaction_id"
                )
            )

            ecocash_server_reference = (
                response_data.get(
                    "serverReferenceCode"
                )
                or response_data.get(
                    "serverReference"
                )
                or response_data.get(
                    "referenceCode"
                )
            )

        db = get_db()

        db.execute(
            """
            UPDATE orders
            SET
                ecocash_transaction_id = ?,
                ecocash_server_reference = ?,
                ecocash_status = ?,
                payment_status = ?
            WHERE id = ?
            """,
            (
                ecocash_transaction_id,
                ecocash_server_reference,
                status or "PENDING",
                status or "PENDING",
                order_id,
            )
        )

        db.commit()
        db.close()

        return jsonify({
            "success": True,
            "order_id": order_id,
            "beat_id": beat_id,
            "license_type": license_type,
            "license_name": LICENSE_NAMES[
                license_type
            ],
            "amount": amount,
            "currency": ECOCASH_CURRENCY,
            "client_correlator": client_correlator,
            "reference_code": reference_code,
            "ecocash_status": status or "PENDING",
            "payment_status": status or "PENDING",
        })


    # ======================================
    # CHECK ORDER / PAYMENT STATUS
    # ======================================

    @app.route(
        "/api/ecocash/order/<int:order_id>",
        methods=["GET"]
    )
    def ecocash_order_status(order_id):

        db = get_db()

        order = db.execute(
            """
            SELECT *
            FROM orders
            WHERE id = ?
            """,
            (order_id,)
        ).fetchone()

        if not order:

            db.close()

            return jsonify({
                "success": False,
                "error": "Order not found.",
            }), 404

        phone = order["buyer_phone"]
        client_correlator = order[
            "client_correlator"
        ]

        # ----------------------------------
        # Ask EcoCash for latest status
        # ----------------------------------

        lookup = ecocash_lookup(
            phone,
            client_correlator
        )

        if lookup.get("success"):

            response_data = lookup.get(
                "data",
                {}
            )

            status = extract_status(
                response_data
            )

            if status:

                ecocash_transaction_id = (
                    response_data.get(
                        "transactionId"
                    )
                    if isinstance(
                        response_data,
                        dict
                    )
                    else None
                )

                ecocash_server_reference = (
                    response_data.get(
                        "serverReferenceCode"
                    )
                    if isinstance(
                        response_data,
                        dict
                    )
                    else None
                )

                paid_statuses = {
                    "COMPLETED",
                    "SUCCESS",
                    "CHARGED",
                }

                failed_statuses = {
                    "FAILED",
                    "FAILURE",
                    "DECLINED",
                    "REJECTED",
                    "CANCELLED",
                    "CANCELED",
                }

                if status in paid_statuses:

                    download_token = (
                        order["download_token"]
                    )

                    if not download_token:

                        download_token = (
                            secrets.token_urlsafe(48)
                        )

                    expires = (
                        datetime.utcnow()
                        + timedelta(days=30)
                    )

                    db.execute(
                        """
                        UPDATE orders
                        SET
                            ecocash_transaction_id = ?,
                            ecocash_server_reference = ?,
                            ecocash_status = ?,
                            payment_status = ?,
                            download_token = ?,
                            download_expires_at = ?,
                            paid_at = COALESCE(
                                paid_at,
                                CURRENT_TIMESTAMP
                            )
                        WHERE id = ?
                        """,
                        (
                            ecocash_transaction_id,
                            ecocash_server_reference,
                            status,
                            "PAID",
                            download_token,
                            expires.strftime(
                                "%Y-%m-%d %H:%M:%S"
                            ),
                            order_id,
                        )
                    )

                    db.commit()

                    result = {
                        "success": True,
                        "order_id": order_id,
                        "payment_status": "PAID",
                        "ecocash_status": status,
                        "download_ready": True,
                        "download_url": (
                            f"/license/download/"
                            f"{download_token}"
                        ),
                    }

                    db.close()

                    return jsonify(result)

                elif status in failed_statuses:

                    db.execute(
                        """
                        UPDATE orders
                        SET
                            ecocash_status = ?,
                            payment_status = ?
                        WHERE id = ?
                        """,
                        (
                            status,
                            "FAILED",
                            order_id,
                        )
                    )

                    db.commit()

        # ----------------------------------
        # Return current local order status
        # ----------------------------------

        db = get_db()

        order = db.execute(
            """
            SELECT *
            FROM orders
            WHERE id = ?
            """,
            (order_id,)
        ).fetchone()

        result = {
            "success": True,
            "order_id": order_id,
            "payment_status": order[
                "payment_status"
            ],
            "ecocash_status": order[
                "ecocash_status"
            ],
            "download_ready": (
                order["payment_status"]
                == "PAID"
                and bool(
                    order["download_token"]
                )
            ),
        }

        if result["download_ready"]:

            result["download_url"] = (
                f"/license/download/"
                f"{order['download_token']}"
            )

        db.close()

        return jsonify(result)


    # ======================================
    # PROTECTED LICENSE DOWNLOAD
    # ======================================

    @app.route(
        "/license/download/<token>",
        methods=["GET"]
    )
    def download_license(token):

        if not token:

            return jsonify({
                "success": False,
                "error": "Invalid download token.",
            }), 400

        db = get_db()

        order = db.execute(
            """
            SELECT *
            FROM orders
            WHERE download_token = ?
            """,
            (token,)
        ).fetchone()

        if not order:

            db.close()

            return jsonify({
                "success": False,
                "error": "Download link not found.",
            }), 404

        # ----------------------------------
        # Payment check
        # ----------------------------------

        if order["payment_status"] != "PAID":

            db.close()

            return jsonify({
                "success": False,
                "error": "Payment has not been completed.",
            }), 403

        # ----------------------------------
        # Expiry check
        # ----------------------------------

        expires_at = order[
            "download_expires_at"
        ]

        if expires_at:

            try:

                expiry = datetime.strptime(
                    expires_at,
                    "%Y-%m-%d %H:%M:%S"
                )

                if datetime.utcnow() > expiry:

                    db.close()

                    return jsonify({
                        "success": False,
                        "error": "Download link has expired.",
                    }), 410

            except ValueError:
                pass

        # ----------------------------------
        # Get beat
        # ----------------------------------

        beat = db.execute(
            """
            SELECT *
            FROM beats
            WHERE id = ?
            """,
            (order["beat_id"],)
        ).fetchone()

        db.close()

        if not beat:

            return jsonify({
                "success": False,
                "error": "Beat no longer exists.",
            }), 404

        audio_file = beat[
            "audio_file"
        ]

        if not audio_file:

            return jsonify({
                "success": False,
                "error": "Audio file is unavailable.",
            }), 404

        filename = os.path.basename(
            audio_file
        )

        file_path = os.path.join(
            audio_dir,
            filename
        )

        if not os.path.isfile(file_path):

            return jsonify({
                "success": False,
                "error": "Audio file not found.",
            }), 404

        safe_title = slugify(
            beat["title"]
        ) or "wave-beatz"

        license_slug = slugify(
            LICENSE_NAMES.get(
                order["license_type"],
                "LICENSE"
            )
        )

        download_name = (
            f"{safe_title}-"
            f"{license_slug}.mp3"
        )

        return send_from_directory(
            audio_dir,
            filename,
            as_attachment=True,
            download_name=download_name,
        )
