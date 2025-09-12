# Файл: app/routers/auth.py
import secrets
from datetime import datetime, timedelta, timezone
from flask import (Blueprint, request, session, redirect, url_for, 
                   render_template, g)

from app.security import get_password_hash, verify_password
from app.utils import send_email_notification

auth_bp = Blueprint('auth', __name__)

@auth_bp.route("/register", methods=['GET', 'POST'])
def handle_registration():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        user_type = request.form.get('user_type')
        consent = request.form.get('consent')

        if not consent:
            session["flash"] = {"category": "error", "message": g.tr["error_consent_required"]}
            return redirect(url_for('auth.handle_registration', lang=session.get('lang')))
        if password != confirm_password:
            session["flash"] = {"category": "error", "message": g.tr["error_passwords_mismatch"]}
            return redirect(url_for('auth.handle_registration', lang=session.get('lang')))
        if len(password) < 8 or not any(char.isdigit() for char in password) or not any(char.isupper() for char in password):
            session["flash"] = {"category": "error", "message": g.tr["error_password_too_weak"]}
            return redirect(url_for('auth.handle_registration', lang=session.get('lang')))

        existing_user = g.db.fetch_one("SELECT id FROM users WHERE email = ?1", (email,))
        if existing_user:
            session["flash"] = {"category": "error", "message": g.tr["error_user_exists"]}
            return redirect(url_for('auth.handle_registration', lang=session.get('lang')))

        hashed_password = get_password_hash(password)
        verification_token = secrets.token_urlsafe(32)

        query = """
            INSERT INTO users (email, hashed_password, verification_token, user_type, is_admin, is_verified) 
            VALUES (?1, ?2, ?3, ?4, 0, 0)
        """
        g.db.execute(query, (email, hashed_password, verification_token, user_type))

        verification_link = url_for('auth.verify_email', token=verification_token, lang=session.get('lang'), _external=True)
        send_email_notification(
            recipients=[email], subject_key="email_verification_subject",
            body_key="email_verification_body",
            template_vars={"verification_link": verification_link}
        )
        
        session["flash"] = {"category": "success", "message": g.tr["registration_check_email"]}
        return redirect(url_for('auth.handle_login', lang=session.get('lang')))

    return render_template("register.html")

@auth_bp.route("/verify/<token>")
def verify_email(token: str):
    query = "UPDATE users SET is_verified = 1, verification_token = NULL WHERE verification_token = ?1"
    result = g.db.execute(query, (token,))
    
    changes = result.get('meta', {}).get('changes', 0)
    if changes > 0:
        session["flash"] = {"category": "success", "message": g.tr["verification_success"]}
    return redirect(url_for('auth.handle_login', lang=session.get('lang')))

@auth_bp.route("/login", methods=['GET', 'POST'])
def handle_login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user_data = g.db.fetch_one("SELECT * FROM users WHERE email = ?1", (email,))
        
        if not user_data or not verify_password(password, user_data['hashed_password']):
            session["flash"] = {"category": "error", "message": g.tr["error_login_failed"]}
            return redirect(url_for('auth.handle_login', lang=session.get('lang')))
        
        if not user_data['is_verified']:
            session["flash"] = {"category": "error", "message": g.tr["error_not_verified"]}
            return redirect(url_for('auth.handle_login', lang=session.get('lang')))

        session["user"] = {"email": user_data['email'], "id": user_data['id']}
        session["flash"] = {"category": "success", "message": g.tr["login_success_message"]}
        
        if user_data.get('is_admin'):
            return redirect(url_for('admin.admin_dashboard'))
        return redirect(url_for('pages.read_root'))

    return render_template("login.html")

@auth_bp.route("/logout")
def handle_logout():
    lang = session.get('lang', 'en')
    session.clear()
    session["lang"] = lang
    session["flash"] = {"category": "success", "message": g.tr.get("logout_success_message", "You have been logged out.")}
    return redirect(url_for('pages.read_root', lang=lang))

@auth_bp.route("/forgot-password", methods=['GET', 'POST'])
def handle_forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        user = g.db.fetch_one("SELECT * FROM users WHERE email = ?1", (email,))
        
        if user:
            token = secrets.token_urlsafe(32)
            expires = datetime.now(timezone.utc) + timedelta(hours=1)
            
            g.db.execute(
                "UPDATE users SET password_reset_token = ?1, password_reset_expires = ?2 WHERE id = ?3",
                (token, expires.isoformat(), user['id'])
            )
            
            reset_link = url_for('auth.reset_password_page', token=token, lang=session.get('lang'), _external=True)
            send_email_notification(
                recipients=[email], subject_key="email_reset_subject",
                body_key="email_reset_body",
                template_vars={"reset_link": reset_link}
            )
                
        session["flash"] = {"category": "success", "message": g.tr["reset_email_sent"]}
        return redirect(url_for('auth.handle_forgot_password', lang=session.get('lang')))

    return render_template("forgot_password.html")

@auth_bp.route("/reset-password/<token>", methods=['GET', 'POST'])
def reset_password_page(token: str):
    now_utc_iso = datetime.now(timezone.utc).isoformat()
    user = g.db.fetch_one(
        "SELECT * FROM users WHERE password_reset_token = ?1 AND password_reset_expires > ?2", 
        (token, now_utc_iso)
    )

    if not user:
        session["flash"] = {"category": "error", "message": g.tr["error_invalid_token"]}
        return redirect(url_for('auth.handle_login', lang=session.get('lang')))
        
    if request.method == 'POST':
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if password != confirm_password:
            session["flash"] = {"category": "error", "message": g.tr["error_passwords_mismatch"]}
            return redirect(url_for('auth.reset_password_page', token=token, lang=session.get('lang')))
            
        if len(password) < 8 or not any(char.isdigit() for char in password) or not any(char.isupper() for char in password):
            session["flash"] = {"category": "error", "message": g.tr["error_password_too_weak"]}
            return redirect(url_for('auth.reset_password_page', token=token, lang=session.get('lang')))

        hashed_password = get_password_hash(password)
        g.db.execute(
            "UPDATE users SET hashed_password = ?1, password_reset_token = NULL, password_reset_expires = NULL WHERE id = ?2",
            (hashed_password, user['id'])
        )
        
        session["flash"] = {"category": "success", "message": g.tr["password_reset_success"]}
        return redirect(url_for('auth.handle_login', lang=session.get('lang')))

    return render_template("reset_password.html", token=token)