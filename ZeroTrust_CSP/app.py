from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import pyotp
import qrcode
import os
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
import re

app = Flask(__name__)
app.secret_key = "change_this_to_any_random_secret_key"

DATABASE = "users.db"
QR_FOLDER = "static/qr_codes"

if not os.path.exists(QR_FOLDER):
    os.makedirs(QR_FOLDER)


def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            totp_secret TEXT NOT NULL,
            failed_attempts INTEGER DEFAULT 0,
            lock_until TEXT DEFAULT NULL
        )
    """)
    conn.commit()
    conn.close()


def get_user_by_username(username):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    conn.close()
    return user


def get_user_by_email(email):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
    user = cursor.fetchone()
    conn.close()
    return user


def create_user(username, email, password_hash, totp_secret):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO users (username, email, password_hash, totp_secret)
        VALUES (?, ?, ?, ?)
    """, (username, email, password_hash, totp_secret))
    conn.commit()
    conn.close()


def update_failed_attempts(username, attempts, lock_until=None):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE users
        SET failed_attempts = ?, lock_until = ?
        WHERE username = ?
    """, (attempts, lock_until, username))
    conn.commit()
    conn.close()


def reset_failed_attempts(username):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE users
        SET failed_attempts = 0, lock_until = NULL
        WHERE username = ?
    """, (username,))
    conn.commit()
    conn.close()


def is_strong_password(password):
    if len(password) < 8:
        return False
    if not re.search(r"[A-Z]", password):
        return False
    if not re.search(r"[a-z]", password):
        return False
    if not re.search(r"[0-9]", password):
        return False
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False
    return True


def is_account_locked(user):
    lock_until = user[6]
    if lock_until:
        lock_time = datetime.fromisoformat(lock_until)
        if datetime.now() < lock_time:
            return True, lock_time
    return False, None


@app.route("/")
def home():
    return redirect(url_for("login"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"].strip()
        email = request.form["email"].strip()
        password = request.form["password"]

        if get_user_by_username(username):
            flash("Username already exists.", "danger")
            return redirect(url_for("register"))

        if get_user_by_email(email):
            flash("Email already exists.", "danger")
            return redirect(url_for("register"))

        if not is_strong_password(password):
            flash("Password must be at least 8 characters long and include uppercase, lowercase, number, and special character.", "danger")
            return redirect(url_for("register"))

        password_hash = generate_password_hash(password)
        totp_secret = pyotp.random_base32()

        create_user(username, email, password_hash, totp_secret)

        totp = pyotp.TOTP(totp_secret)
        uri = totp.provisioning_uri(name=email, issuer_name="SecureAuthProject")

        qr_path = os.path.join(QR_FOLDER, f"{username}.png")
        img = qrcode.make(uri)
        img.save(qr_path)

        session["setup_user"] = username
        flash("Registration successful. Now set up 2FA.", "success")
        return redirect(url_for("setup_2fa"))

    return render_template("register.html")


@app.route("/setup_2fa")
def setup_2fa():
    username = session.get("setup_user")
    if not username:
        return redirect(url_for("register"))

    qr_file = f"qr_codes/{username}.png"
    return render_template("setup_2fa.html", qr_file=qr_file, username=username)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]

        user = get_user_by_username(username)

        if not user:
            flash("Invalid username or password.", "danger")
            return redirect(url_for("login"))

        locked, lock_time = is_account_locked(user)
        if locked:
            flash(f"Account is locked. Try again after {lock_time.strftime('%H:%M:%S')}", "danger")
            return redirect(url_for("login"))

        password_hash = user[3]
        failed_attempts = user[5]

        if check_password_hash(password_hash, password):
            reset_failed_attempts(username)
            session["temp_user"] = username
            return redirect(url_for("verify_otp"))
        else:
            failed_attempts += 1

            if failed_attempts >= 3:
                lock_until = (datetime.now() + timedelta(minutes=2)).isoformat()
                update_failed_attempts(username, failed_attempts, lock_until)
                flash("Too many failed attempts. Account locked for 2 minutes.", "danger")
            else:
                update_failed_attempts(username, failed_attempts)
                flash(f"Wrong password. Attempt {failed_attempts} of 3.", "danger")

            return redirect(url_for("login"))

    return render_template("login.html")


@app.route("/verify_otp", methods=["GET", "POST"])
def verify_otp():
    username = session.get("temp_user")
    if not username:
        return redirect(url_for("login"))

    user = get_user_by_username(username)
    if not user:
        return redirect(url_for("login"))

    totp_secret = user[4]
    totp = pyotp.TOTP(totp_secret)

    if request.method == "POST":
        otp = request.form["otp"].strip()

        if totp.verify(otp):
            session["user"] = username
            session.pop("temp_user", None)
            flash("Login successful with 2FA.", "success")
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid OTP.", "danger")
            return redirect(url_for("verify_otp"))

    return render_template("verify_otp.html")


@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect(url_for("login"))

    return render_template("dashboard.html", username=session["user"])


@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully.", "success")
    return redirect(url_for("login"))


if __name__ == "__main__":
    init_db()
    app.run(debug=True)