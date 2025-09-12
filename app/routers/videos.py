# Файл: app/routers/videos.py
import os
import uuid
import math
from datetime import datetime, timedelta, timezone
from flask import (Blueprint, request, session, g, render_template,
                   redirect, url_for, jsonify)

from app.config import settings
from app.moderation import check_text_for_stop_words
from app.utils import send_email_notification, logger
from app.decorators import login_required

videos_bp = Blueprint('videos', __name__)

@videos_bp.route("/video/<int:video_id>")
def view_video_page(video_id: int):
    query_video = """
        SELECT v.*, u.email as author_email, u.id as author_id
        FROM videos v JOIN users u ON v.user_id = u.id
        WHERE v.id = ?1
    """
    video_data = g.db.fetch_one(query_video, (video_id,))

    if not video_data:
        return redirect(url_for('pages.read_root', lang=session.get('lang')))
    
    is_owner = g.user and g.user["id"] == video_data["author_id"]
    is_admin = g.user and g.user.get("is_admin")
    is_published = video_data["status"] == 'published'

    if not is_published and not is_owner and not is_admin:
        return redirect(url_for('pages.read_root', lang=session.get('lang')))
        
    likes_count = g.db.fetch_val("SELECT COUNT(*) FROM likes WHERE video_id = ?1", (video_id,))
    
    query_comments = """
        SELECT c.*, u.id as author_id, u.email as author_email
        FROM comments c JOIN users u ON c.user_id = u.id
        WHERE c.video_id = ?1 AND c.status = 'published'
        ORDER BY c.created_at DESC
    """
    video_comments = g.db.fetch_all(query_comments, (video_id,))

    user_has_liked = False
    if g.user:
        like = g.db.fetch_one("SELECT 1 FROM likes WHERE video_id = ?1 AND user_id = ?2", (video_id, g.user["id"]))
        user_has_liked = bool(like)
        
    base_media_url = f"{settings.R2_PUBLIC_URL}/{settings.S3_BUCKET_NAME}" 
    media_url = f"{base_media_url}/{video_data['filename']}" 
    preview_url = f"{base_media_url}/{video_data['preview_filename']}" if video_data.get('preview_filename') else None

    query_reply = """
        SELECT cr.*, u.email as company_email
        FROM company_replies cr JOIN users u ON cr.user_id = u.id
        WHERE cr.video_id = ?1
    """
    reply_data = g.db.fetch_one(query_reply, (video_id,))

    can_reply = g.user and g.user.get("user_type") == 'company' and not reply_data

    return render_template("video_view.html",
        video=video_data, likes_count=likes_count, comments=video_comments,
        user_has_liked=user_has_liked, title=f"{video_data['title']} - HonestReviews",
        description=video_data.get('description', '')[:155], background_image="index.jpg",
        media_url=media_url, preview_url=preview_url,
        company_reply=reply_data, can_reply=can_reply
    )

@videos_bp.route("/video/<int:video_id>/reply", methods=['POST'])
@login_required
def handle_company_reply(video_id: int):
    content = request.form.get('content')
    lang = session.get('lang', 'en')

    if g.user["user_type"] != 'company':
        return "Only company users can reply.", 403

    existing_reply = g.db.fetch_one("SELECT id FROM company_replies WHERE video_id = ?1", (video_id,))
    if existing_reply:
        return "A reply for this review already exists.", 400

    query = "INSERT INTO company_replies (content, video_id, user_id) VALUES (?1, ?2, ?3)"
    g.db.execute(query, (content, video_id, g.user["id"]))

    session["flash"] = {"category": "success", "message": g.tr["company_reply_success"]}
    return redirect(url_for('videos.view_video_page', video_id=video_id, lang=lang))

@videos_bp.route("/api/video/<int:video_id>/like", methods=['POST'])
@login_required
def api_handle_like(video_id: int):
    existing_like = g.db.fetch_one("SELECT 1 FROM likes WHERE video_id = ?1 AND user_id = ?2", (video_id, g.user["id"]))
    lang = session.get('lang', 'en')
    
    if existing_like:
        g.db.execute("DELETE FROM likes WHERE video_id = ?1 AND user_id = ?2", (video_id, g.user["id"]))
        user_has_liked = False
    else:
        g.db.execute("INSERT INTO likes (video_id, user_id) VALUES (?1, ?2)", (video_id, g.user["id"]))
        user_has_liked = True
        
        video_author_info_query = "SELECT u.email, v.title FROM videos v JOIN users u ON v.user_id = u.id WHERE v.id = ?1"
        video_author_info = g.db.fetch_one(video_author_info_query, (video_id,))
        
        if video_author_info and video_author_info["email"] != g.user["email"]:
            video_link = url_for('videos.view_video_page', video_id=video_id, lang=lang, _external=True)
            send_email_notification(
                recipients=[video_author_info["email"]], subject_key="email_new_like_subject",
                body_key="email_new_like_body",
                template_vars={ "liker_email": g.user["email"], "video_title": video_author_info["title"], "video_link": video_link }
            )
            
    likes_count = g.db.fetch_val("SELECT COUNT(*) FROM likes WHERE video_id = ?1", (video_id,))
    return jsonify({"likes_count": likes_count, "user_has_liked": user_has_liked})

@videos_bp.route("/api/video/<int:video_id>/comment", methods=['POST'])
@login_required
def api_handle_comment(video_id: int):
    content = request.form.get("content")
    lang = session.get('lang', 'en')

    if not content or not content.strip():
        return jsonify({"error": "Comment cannot be empty"}), 400
    
    text_to_check = content.strip()
    if check_text_for_stop_words(text_to_check, lang):
        return jsonify({"error": g.tr["error_moderation_failed"]}), 400
    
    insert_query = """
        INSERT INTO comments (content, video_id, user_id, created_at, status) 
        VALUES (?1, ?2, ?3, ?4, 'pending_review')
    """
    created_at = datetime.now(timezone.utc).isoformat()
    g.db.execute(insert_query, (text_to_check, video_id, g.user["id"], created_at))
            
    return jsonify({"status": "success", "message": "Comment submitted for review."})

@videos_bp.route("/category/<category_name>")
def category_page(category_name: str):
    page = request.args.get('page', 1, type=int)
    offset = (page - 1) * settings.ITEMS_PER_PAGE
    
    count_query = "SELECT COUNT(*) FROM videos WHERE category = ?1 AND status = 'published'"
    total_items = g.db.fetch_val(count_query, (category_name,))
    total_pages = math.ceil(total_items / settings.ITEMS_PER_PAGE) if total_items > 0 else 0

    select_query = """
        SELECT v.*, u.email as author_email FROM videos v JOIN users u ON v.user_id = u.id
        WHERE v.category = ?1 AND v.status = 'published'
        ORDER BY v.id DESC LIMIT ?2 OFFSET ?3
    """
    result_videos = g.db.fetch_all(select_query, (category_name, settings.ITEMS_PER_PAGE, offset))
    
    return render_template("category.html",
        videos=result_videos, current_page=page, total_pages=total_pages,
        category_name=category_name, 
        category_title=g.tr.get(f"nav_{category_name.replace('-', '_')}", category_name),
        background_image=f"{category_name}.jpg"
    )

@videos_bp.route("/upload", methods=['GET', 'POST'])
@login_required
def handle_upload():
    lang = session.get('lang', 'en')
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        category = request.form.get('category')
        what = request.form.get('what')
        where = request.form.get('where')
        rating = request.form.get('rating', type=int)
        media_file = request.files.get('media_file')

        # ... (здесь должны быть ваши проверки на лимиты загрузки и т.д.) ...

        if not media_file or not media_file.filename:
            session["flash"] = {"category": "error", "message": "File is required."}
            return redirect(url_for('videos.handle_upload', lang=lang))

        preview_filename = None
        media_type = 'video' if media_file.content_type and media_file.content_type.startswith('video/') else 'image'
        unique_filename = f"{media_type}s/{uuid.uuid4()}{os.path.splitext(media_file.filename)[1]}"
        
        file_content = media_file.read()
        
        try:
            g.r2.put(unique_filename, file_content, httpMetadata={'contentType': media_file.content_type})
        except Exception as e:
            logger.error(f"Ошибка загрузки файла в R2 для {unique_filename}: {e}")
            session["flash"] = {"category": "error", "message": g.tr["error_s3_upload_failed"]}
            return redirect(url_for('videos.handle_upload', lang=lang))
        
        query_insert = """
            INSERT INTO videos (title, description, category, filename, preview_filename, user_id, what, "where", media_type, rating, created_at, status)
            VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8, ?9, ?10, ?11, 'pending_review')
        """
        params = (title, description, category, unique_filename, preview_filename, g.user["id"], what, where, media_type, rating, datetime.now(timezone.utc).isoformat())
        g.db.execute(query_insert, params)

        session["flash"] = {"category": "success", "message": g.tr["upload_success_message"]}
        return redirect(url_for('users.profile_page', lang=lang))

    category = request.args.get('category')
    return render_template("upload.html", selected_category=category, background_image="index.jpg")


@videos_bp.route("/video/delete/<int:video_id>", methods=['POST'])
@login_required
def delete_video(video_id: int):
    lang = session.get('lang', 'en')
    video_data = g.db.fetch_one("SELECT * FROM videos WHERE id = ?1", (video_id,))

    if not video_data or (video_data["user_id"] != g.user["id"] and not g.user.get("is_admin")):
        abort(403)

    try:
        if video_data.get("filename"): g.r2.delete(video_data["filename"])
        if video_data.get("preview_filename"): g.r2.delete(video_data["preview_filename"])
    except Exception as e:
        logger.error(f"Ошибка удаления файла из R2: {e}, filename: {video_data.get('filename')}")
    
    g.db.execute("DELETE FROM videos WHERE id = ?1", (video_id,))
    session["flash"] = {"category": "success", "message": g.tr["video_deleted_success"]}

    referer = request.headers.get("referer")
    if referer and "/admin/" in referer:
        return redirect(referer)
    return redirect(url_for('users.profile_page', lang=lang))