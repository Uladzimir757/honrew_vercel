# Файл: app/routers/users.py
import os
import uuid
import math
import secrets
from datetime import datetime, timezone
from flask import (Blueprint, request, session, g, render_template,
                   redirect, url_for)

from app.security import get_password_hash, verify_password
from app.config import settings
from app.utils import send_email_notification, logger
from app.decorators import login_required

users_bp = Blueprint('users', __name__)

@users_bp.route("/profile", methods=['GET'])
@login_required
def profile_page():
    query_videos = "SELECT * FROM videos WHERE user_id = %s ORDER BY id DESC"
    user_videos = g.db.fetch_all(query_videos, (g.user["id"],))

    return render_template("profile.html",
        db_user=g.user,
        videos=user_videos,
        background_image="index.jpg"
    )

@users_bp.route("/profile/update", methods=['POST'])
@login_required
def handle_profile_update():
    username = request.form.get('username')
    bio = request.form.get('bio', '')
    lang = session.get('lang', 'en')
    
    if username != g.user.get("username"):
        query_existing_user = "SELECT id FROM users WHERE username = %s AND id != %s"
        if g.db.fetch_one(query_existing_user, (username, g.user["id"])):
            session["flash"] = {"category": "error", "message": g.tr["profile_username_taken"]}
            return redirect(url_for('users.profile_page', lang=lang))

    query = "UPDATE users SET username = %s, bio = %s WHERE id = %s"
    g.db.execute(query, (username, bio, g.user["id"]))

    session["flash"] = {"category": "success", "message": g.tr["profile_info_updated"]}
    return redirect(url_for('users.profile_page', lang=lang))


@users_bp.route("/profile/avatar", methods=['POST'])
@login_required
def handle_avatar_upload():
    lang = session.get('lang', 'en')
    
    if 'avatar_file' not in request.files or not request.files['avatar_file'].filename:
        session["flash"] = {"category": "error", "message": g.tr["profile_avatar_error"]}
        return redirect(url_for('users.profile_page', lang=lang))
        
    avatar_file = request.files['avatar_file']

    if not avatar_file.content_type.startswith("image/"):
        session["flash"] = {"category": "error", "message": g.tr["profile_avatar_error"]}
        return redirect(url_for('users.profile_page', lang=lang))

    file_extension = os.path.splitext(avatar_file.filename)[1]
    unique_filename = f"avatars/{uuid.uuid4()}{file_extension}"
    
    file_content = avatar_file.read()

    try:
        g.r2.put(unique_filename, file_content, httpMetadata={'contentType': avatar_file.content_type})
    except Exception as e:
        logger.error(f"Ошибка загрузки аватара в R2: {e}")
        session["flash"] = {"category": "error", "message": g.tr["error_s3_upload_failed"]}
        return redirect(url_for('users.profile_page', lang=lang))
    
    if g.user["avatar_filename"]:
        try:
            g.r2.delete(g.user["avatar_filename"])
        except Exception as e:
             logger.warning(f"Ошибка удаления старого аватара из R2: {e}")

    g.db.execute("UPDATE users SET avatar_filename = %s WHERE id = %s", (unique_filename, g.user["id"]))
    
    session["flash"] = {"category": "success", "message": g.tr["profile_avatar_updated"]}
    return redirect(url_for('users.profile_page', lang=lang))


@users_bp.route("/profile/password", methods=['POST'])
@login_required
def handle_password_change():
    lang = session.get('lang', 'en')
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')

    if new_password != confirm_password:
        session["flash"] = {"category": "error", "message": g.tr["profile_password_mismatch"]}
        return redirect(url_for('users.profile_page', lang=lang))

    if not verify_password(current_password, g.user["hashed_password"]):
        session["flash"] = {"category": "error", "message": g.tr["profile_password_incorrect"]}
        return redirect(url_for('users.profile_page', lang=lang))

    hashed_password = get_password_hash(new_password)
    g.db.execute("UPDATE users SET hashed_password = %s WHERE id = %s", (hashed_password, g.user["id"]))
    
    session["flash"] = {"category": "success", "message": g.tr["profile_password_updated"]}
    return redirect(url_for('users.profile_page', lang=lang))

@users_bp.route("/profile/delete/request", methods=['POST'])
@login_required
def request_profile_deletion():
    lang = session.get('lang', 'en')
    token = secrets.token_urlsafe(32)
    expires = datetime.now(timezone.utc) + timedelta(hours=1)
    
    g.db.execute(
        "UPDATE users SET delete_token = %s, delete_token_expires = %s WHERE id = %s",
        (token, expires.isoformat(), g.user["id"])
    )
    
    delete_link = url_for('users.confirm_profile_deletion', token=token, lang=lang, _external=True)
    send_email_notification(
        request=request,
        recipients=[g.user["email"]],
        subject_key="email_delete_account_subject",
        body_key="email_delete_account_body",
        template_vars={"delete_link": delete_link}
    )
    
    session["flash"] = {"category": "success", "message": g.tr["delete_confirmation_sent"]}
    return redirect(url_for('users.profile_page', lang=lang))

@users_bp.route("/profile/delete/confirm/<token>")
def confirm_profile_deletion(token: str):
    lang = session.get('lang', 'en')
    now_utc_iso = datetime.now(timezone.utc).isoformat()
    query = "SELECT * FROM users WHERE delete_token = %s AND delete_token_expires > %s"
    user_to_delete = g.db.fetch_one(query, (token, now_utc_iso))

    if not user_to_delete:
        session["flash"] = {"category": "error", "message": g.tr["error_invalid_token"]}
        return redirect(url_for('pages.read_root', lang=lang))

    user_id_to_delete = user_to_delete["id"]

    try:
        user_videos = g.db.fetch_all("SELECT filename, preview_filename FROM videos WHERE user_id = %s", (user_id_to_delete,))
        for video in user_videos:
            if video["filename"]: g.r2.delete(video["filename"])
            if video["preview_filename"]: g.r2.delete(video["preview_filename"])
        if user_to_delete["avatar_filename"]:
            g.r2.delete(user_to_delete["avatar_filename"])
    except Exception as e:
        logger.error(f"Ошибка при удалении файлов пользователя {user_id_to_delete} из R2: {e}")

    g.db.execute("DELETE FROM users WHERE id = %s", (user_id_to_delete,))
    
    session.clear()
    session['lang'] = lang
    session["flash"] = {"category": "success", "message": g.tr["profile_deleted_success"]}
    return redirect(url_for('pages.read_root', lang=lang))

@users_bp.route("/user/<int:user_id>")
def user_profile_page(user_id: int):
    page = request.args.get('page', 1, type=int)
    profile_user = g.db.fetch_one("SELECT * FROM users WHERE id = %s", (user_id,))
    
    if not profile_user:
        return redirect(url_for('pages.read_root', lang=session.get('lang')))

    offset = (page - 1) * settings.ITEMS_PER_PAGE
    
    count_query = "SELECT COUNT(*) AS total FROM videos WHERE user_id = %s AND status = 'published'"
    total_items = g.db.fetch_one(count_query, (user_id,))['total']
    total_pages = math.ceil(total_items / settings.ITEMS_PER_PAGE) if total_items > 0 else 0

    query_videos = """
        SELECT v.*, u.email as author_email 
        FROM videos v JOIN users u ON v.user_id = u.id 
        WHERE v.user_id = %s AND v.status = 'published'
        ORDER BY v.id DESC LIMIT %s OFFSET %s
    """
    result_videos = g.db.fetch_all(query_videos, (user_id, settings.ITEMS_PER_PAGE, offset))
    
    return render_template("user_profile.html",
        videos=result_videos,
        profile_user=profile_user,
        current_page=page,
        total_pages=total_pages,
        background_image="index.jpg"
    )