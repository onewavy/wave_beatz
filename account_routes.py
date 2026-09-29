from flask import render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
import re


# ==========================================
# WAVE BEATZ — STAGE 8
# CUSTOMER ACCOUNT + ORDERS
# ==========================================

def register_account_routes(app, get_db):

    # --------------------------------------
    # REGISTER
    # --------------------------------------

    @app.route("/register", methods=["GET", "POST"])
    def register():

        if request.method == "POST":

            name = request.form.get(
                "name",
                ""
            ).strip()

            email = request.form.get(
                "email",
                ""
            ).strip().lower()

            phone = request.form.get(
                "phone",
                ""
            ).strip()

            password = request.form.get(
                "password",
                ""
            )

            confirm_password = request.form.get(
                "confirm_password",
                ""
            )

            # ------------------------------
            # Validation
            # ------------------------------

            if not name:
                flash(
                    "Please enter your name.",
                    "error"
                )
                return redirect(
                    url_for("register")
                )

            if not email or not re.match(
                r"^[^@\s]+@[^@\s]+\.[^@\s]+$",
                email
            ):
                flash(
                    "Please enter a valid email address.",
                    "error"
                )
                return redirect(
                    url_for("register")
                )

            if len(password) < 8:
                flash(
                    "Password must be at least 8 characters.",
                    "error"
                )
                return redirect(
                    url_for("register")
                )

            if password != confirm_password:
                flash(
                    "Passwords do not match.",
                    "error"
                )
                return redirect(
                    url_for("register")
                )

            db = get_db()

            existing_user = db.execute(
                """
                SELECT id
                FROM users
                WHERE email = ?
                """,
                (email,)
            ).fetchone()

            if existing_user:

                db.close()

                flash(
                    "An account with that email already exists.",
                    "error"
                )

                return redirect(
                    url_for("login")
                )

            password_hash = generate_password_hash(
                password
            )

            cursor = db.execute(
                """
                INSERT INTO users (
                    name,
                    email,
                    phone,
                    password_hash
                )
                VALUES (?, ?, ?, ?)
                """,
                (
                    name,
                    email,
                    phone,
                    password_hash
                )
            )

            user_id = cursor.lastrowid

            db.commit()
            db.close()

            session.clear()

            session["user_id"] = user_id
            session["user_name"] = name
            session["user_email"] = email

            flash(
                "Your WAVE BEATZ account has been created.",
                "success"
            )

            return redirect(
                url_for("account")
            )

        return render_template(
            "register.html"
        )


    # --------------------------------------
    # LOGIN
    # --------------------------------------

    @app.route("/login", methods=["GET", "POST"])
    def login():

        next_url = request.args.get("next", "").strip()

        if request.method == "POST":

            next_url = request.form.get("next", "").strip()

            email = request.form.get(
                "email",
                ""
            ).strip().lower()

            password = request.form.get(
                "password",
                ""
            )

            if not email or not password:

                flash(
                    "Please enter your email and password.",
                    "error"
                )

                return redirect(
                    url_for("login", next=next_url)
                )

            db = get_db()

            user = db.execute(
                """
                SELECT *
                FROM users
                WHERE email = ?
                """,
                (email,)
            ).fetchone()

            db.close()

            if not user or not check_password_hash(
                user["password_hash"],
                password
            ):

                flash(
                    "Invalid email or password.",
                    "error"
                )

                return redirect(
                    url_for("login", next=next_url)
                )

            session.clear()

            session["user_id"] = user["id"]
            session["user_name"] = user["name"]
            session["user_email"] = user["email"]

            flash(
                "Welcome back, " + user["name"] + ".",
                "success"
            )

            if next_url.startswith("/") and not next_url.startswith("//"):
                return redirect(next_url)

            return redirect(
                url_for("account")
            )

        return render_template(
            "login.html"
        )


    # --------------------------------------
    # LOGOUT
    # --------------------------------------

    @app.route("/logout")
    def logout():

        session.clear()

        flash(
            "You have been logged out.",
            "success"
        )

        return redirect(
            url_for("login")
        )


    # --------------------------------------
    # ACCOUNT + CUSTOMER ORDERS
    # --------------------------------------

    @app.route("/account")
    def account():

        if "user_id" not in session:

            flash(
                "Please log in to view your account.",
                "error"
            )

            return redirect(
                url_for("login")
            )

        db = get_db()

        # ----------------------------------
        # Load customer account
        # ----------------------------------

        user = db.execute(
            """
            SELECT id, name, email, phone, created_at
            FROM users
            WHERE id = ?
            """,
            (session["user_id"],)
        ).fetchone()

        if not user:

            db.close()

            session.clear()

            flash(
                "Your account could not be found.",
                "error"
            )

            return redirect(
                url_for("login")
            )

        # ----------------------------------
        # Load customer orders
        #
        # Existing orders are connected
        # using the buyer email.
        # ----------------------------------

        orders = db.execute(
            """
            SELECT
                orders.id,
                orders.beat_id,
                orders.license_type,
                orders.artist_name,
                orders.buyer_email,
                orders.amount,
                orders.currency,
                orders.payment_status,
                orders.ecocash_status,
                orders.download_token,
                orders.download_expires_at,
                orders.created_at,
                orders.paid_at,

                beats.title AS beat_title,
                beats.genre AS beat_genre,
                beats.bpm AS beat_bpm,
                beats.artwork_file AS beat_artwork

            FROM orders

            LEFT JOIN beats
                ON beats.id = orders.beat_id

            WHERE LOWER(orders.buyer_email) = LOWER(?)

            ORDER BY
                COALESCE(
                    orders.paid_at,
                    orders.created_at
                ) DESC
            """,
            (user["email"],)
        ).fetchall()

        db.close()

        # ----------------------------------
        # Prepare safe dashboard statistics
        # ----------------------------------

        total_orders = len(orders)

        paid_orders = sum(
            1
            for order in orders
            if str(
                order["payment_status"] or ""
            ).upper() == "PAID"
        )

        pending_orders = sum(
            1
            for order in orders
            if str(
                order["payment_status"] or ""
            ).upper() == "PENDING"
        )

        return render_template(
            "account.html",
            user=user,
            orders=orders,
            total_orders=total_orders,
            paid_orders=paid_orders,
            pending_orders=pending_orders
        )
