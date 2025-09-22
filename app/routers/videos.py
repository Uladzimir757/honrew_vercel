# Файл: app/routers/videos.py
import os
import uuid
import math
import logging
import boto3
from botocore.exceptions import ClientError
from datetime import datetime, timezone
from flask import (Blueprint, request, session, g, render_template,
                   redirect, url_for, jsonify, abort)

from app.config import settings
from app.moderation import check_text_for_stop_words
from app.utils import send_email_notification
from app.decorators import login_required

videos_bp = Blueprint('videos', __name__)

@videos_bp.route("/video/<int:video_id>")
def view_video_page(video_id: int):
    query_video = """
        SELECT v.*, u.email as author_email, u.id as author_id
        FROM videos v JOIN users u ON v.user_id = u.id
        WHERE v.id = %s
    """
    video_data = g.db.fetch_one(query_video, (video_id,))

    if not video_data:
        return redirect(url_for('pages.home', lang=session.get('lang')))
    
    is_owner = g.user and g.user["id"] == video_data["author_id"]
    is_admin = g.user and g.user.get("is_admin")
    is_published = video_data["status"] == 'published'

    if not is_published and not is_owner and not is_admin:
        return redirect(url_for('pages.home', lang=session.get('lang')))
    
    likes_count_result = g.db.fetch_one("SELECT COUNT(*) AS total FROM likes WHERE video_id = %s", (video_id,))
    likes_count = likes_count_result['total'] if likes_count_result else 0
    
    query_comments = """
        SELECT c.*, u.id as author_id, u.email as author_email
        FROM comments c JOIN users u ON c.user_id = u.id
        WHERE c.video_id = %s AND c.status = 'published'
        ORDER BY c.created_at DESC
    """
    video_comments = g.db.fetch_all(query_comments, (video_id,))

    user_has_liked = False
    if g.user:
        like = g.db.fetch_one("SELECT 1 FROM likes WHERE video_id = %s AND user_id = %s", (video_id, g.user["id"]))
        user_has_liked = bool(like)
        
    base_media_url = f"{settings.R2_PUBLIC_URL}/{settings.S3_BUCKET_NAME}" 
    media_url = f"{base_media_url}/{video_data['filename']}" 
    preview_url = f"{base_media_url}/{video_data['preview_filename']}" if video_data.get('preview_filename') else None

    query_reply = """
        SELECT cr.*, u.email as company_email
        FROM company_replies cr JOIN users u ON cr.user_id = u.id
        WHERE cr.video_id = %s
    """
    reply_data = g.db.fetch_one(query_reply, (video_id,))

    can_reply = g.user and g.user.get("user_type") == 'company' and not reply_data

    return render_template("video_view.html",
        video=video_data, likes_count=likes_count, comments=video_comments,
        user_has_liked=user_has_liked, title=f"{video_data['title']} - HonestReviews",
        description=video_data.get('description', '')[:155],
        media_url=media_url, preview_url=preview_url,
        company_reply=reply_data, can_reply=can_reply
    )

@videos_bp.route("/video/<int:video_id>/reply", methods=['POST'])
@login_required
def handle_company_reply(video_id: int):
    content = request.form.get('content')
    lang = session.get('lang', 'en')

    if g.user["user_type"] != 'company':
        abort(403)

    existing_reply = g.db.fetch_one("SELECT id FROM company_replies WHERE video_id = %s", (video_id,))
    if existing_reply:
        return "A reply for this review already exists.", 400

    query = "INSERT INTO company_replies (content, video_id, user_id) VALUES (%s, %s, %s)"
    g.db.execute(query, (content, video_id, g.user["id"]))

    session["flash"] = {"category": "success", "message": g.tr["company_reply_success"]}
    return redirect(url_for('videos.view_video_page', video_id=video_id, lang=lang))

@videos_bp.route("/api/video/<int:video_id>/like", methods=['POST'])
@login_required
def api_handle_like(video_id: int):
    existing_like = g.db.fetch_one("SELECT 1 FROM likes WHERE video_id = %s AND user_id = %s", (video_id, g.user["id"]))
    lang = session.get('lang', 'en')
    
    if existing_like:
        g.db.execute("DELETE FROM likes WHERE video_id = %s AND user_id = %s", (video_id, g.user["id"]))
        user_has_liked = False
    else:
        g.db.execute("INSERT INTO likes (video_id, user_id) VALUES (%s, %s)", (video_id, g.user["id"]))
        user_has_liked = True
        
        video_author_info_query = "SELECT u.email, v.title FROM videos v JOIN users u ON v.user_id = u.id WHERE v.id = %s"
        video_author_info = g.db.fetch_one(video_author_info_query, (video_id,))
        
        if video_author_info and video_author_info["email"] != g.user["email"]:
            video_link = url_for('videos.view_video_page', video_id=video_id, lang=lang, _external=True)
            send_email_notification(
                recipients=[video_author_info["email"]], 
                subject_key="email_new_like_subject",
                body_key="email_new_like_body",
                template_vars={ "liker_email": g.user["email"], "video_title": video_author_info["title"], "video_link": video_link }
            )
            
    likes_count_result = g.db.fetch_one("SELECT COUNT(*) AS total FROM likes WHERE video_id = %s", (video_id,))
    likes_count = likes_count_result['total'] if likes_count_result else 0
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
    
    insert_query = "INSERT INTO comments (content, video_id, user_id, status) VALUES (%s, %s, %s, 'pending_review')"
    g.db.execute(insert_query, (text_to_check, video_id, g.user["id"]))
            
    return jsonify({"status": "success", "message": "Comment submitted for review."})

@videos_bp.route("/live")
def live_page():
    page = request.args.get('page', 1, type=int)
    offset = (page - 1) * settings.ITEMS_PER_PAGE

    count_query = "SELECT COUNT(*) AS total FROM videos WHERE status = 'published'"
    count_result = g.db.fetch_one(count_query)
    total_items = count_result['total'] if count_result else 0
    total_pages = math.ceil(total_items / settings.ITEMS_PER_PAGE) if total_items > 0 else 0

    select_query = """
        SELECT v.*, u.email as author_email, u.id as user_id
        FROM videos v JOIN users u ON v.user_id = u.id
        WHERE v.status = 'published'
        ORDER BY v.created_at DESC
        LIMIT %s OFFSET %s
    """
    result_videos = g.db.fetch_all(select_query, (settings.ITEMS_PER_PAGE, offset))

    return render_template("live.html", videos=result_videos, current_page=page, total_pages=total_pages)

@videos_bp.route("/category/<category_name>")
def category_page(category_name: str):
    page = request.args.get('page', 1, type=int)
    offset = (page - 1) * settings.ITEMS_PER_PAGE
    
    count_query = "SELECT COUNT(*) AS total FROM videos WHERE category = %s AND status = 'published'"
    count_result = g.db.fetch_one(count_query, (category_name,))
    total_items = count_result['total'] if count_result else 0
    total_pages = math.ceil(total_items / settings.ITEMS_PER_PAGE) if total_items > 0 else 0

    select_query = """
        SELECT v.*, u.email as author_email FROM videos v JOIN users u ON v.user_id = u.id
        WHERE v.category = %s AND v.status = 'published'
        ORDER BY v.id DESC LIMIT %s OFFSET %s
    """
    result_videos = g.db.fetch_all(select_query, (category_name, settings.ITEMS_PER_PAGE, offset))
    
    return render_template("category.html",
        videos=result_videos, current_page=page, total_pages=total_pages,
        category_name=category_name, 
        category_title=g.tr.get(f"nav_{category_name.replace('-', '_')}", category_name)
    )

@videos_bp.route("/upload", methods=['GET', 'POST'])
@login_required
def handle_upload():
    if request.method == 'GET':
        category_name = request.args.get('category')
        return render_template("upload.html", selected_category=category_name)

    if request.method == 'POST':
        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "message": "Invalid JSON payload"}), 400

        what = data.get('what')
        where = data.get('where')
        title = data.get('title')
        description = data.get('description')
        category = data.get('category')
        rating = data.get('rating')
        object_name = data.get('objectName') 
        media_type = data.get('mediaType', 'video')

        if not all([what, where, title, description, category, rating, object_name]):
            return jsonify({"status": "error", "message": "Missing required fields"}), 400

        try:
            query = """
                INSERT INTO videos (title, description, category, filename, user_id, what, "where", media_type, rating, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'pending_review')
            """
            params = (title, description, category, object_name, g.user["id"], what, where, media_type, rating)
            g.db.execute(query, params)
            
            session["flash"] = {"category": "success", "message": g.tr["upload_success_message"]}
            return jsonify({"status": "success", "redirectUrl": url_for('pages.home', lang=g.lang)})

        except Exception as e:
            logging.error(f"Database error during upload: {e}")
            return jsonify({"status": "error", "message": "Failed to save review details."}), 500

@videos_bp.route("/api/generate-upload-url", methods=["POST"])
@login_required
def generate_upload_url():
    try:
        data = request.get_json()
        filename = data.get("filename")
        content_type = data.get("contentType")

        if not filename or not content_type:
            return jsonify({"error": "Filename and contentType are required"}), 400

        file_extension = ""
        if '.' in filename:
            file_extension = filename.rsplit('.', 1)[1].lower()

        folder = 'images' if 'image' in content_type else 'videos'
        object_name = f"{folder}/{uuid.uuid4()}.{file_extension}"

        s3_client = boto3.client(
            's3', endpoint_url=settings.S3_ENDPOINT_URL,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name="auto"
        )

        presigned_url = s3_client.generate_presigned_url(
            'put_object',
            Params={'Bucket': settings.S3_BUCKET_NAME, 'Key': object_name, 'ContentType': content_type},
            ExpiresIn=600
        )

        return jsonify({"url": presigned_url, "objectName": object_name})

    except ClientError as e:
        logging.error(f"Error generating presigned URL: {e}")
        return jsonify({"error": "Could not generate upload URL"}), 500
    except Exception as e:
        logging.error(f"An unexpected error occurred in generate_upload_url: {e}")
        return jsonify({"error": "An internal server error occurred"}), 500

@videos_bp.route('/video/edit/<int:video_id>', methods=['GET', 'POST'])
@login_required
def edit_video(video_id):
    video = g.db.fetch_one("SELECT * FROM videos WHERE id = %s", (video_id,))
    if not video or (video['user_id'] != g.user['id'] and not g.user.get('is_admin')):
        abort(403)
        
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        what = request.form.get('what')
        where = request.form.get('where')
        category = request.form.get('category')
        
        query = """
            UPDATE videos SET title = %s, description = %s, what = %s, "where" = %s, category = %s 
            WHERE id = %s
        """
        g.db.execute(query, (title, description, what, where, category, video_id))
        session["flash"] = {"category": "success", "message": g.tr["edit_success_message"]}
        return redirect(url_for('videos.view_video_page', video_id=video_id, lang=g.lang))
        
    return render_template('edit_video.html', video=video)

@videos_bp.route("/video/delete/<int:video_id>", methods=['POST'])
@login_required
def delete_video(video_id: int):
    lang = session.get('lang', 'en')
    video_data = g.db.fetch_one("SELECT * FROM videos WHERE id = %s", (video_id,))

    if not video_data or (video_data["user_id"] != g.user["id"] and not g.user.get("is_admin")):
        abort(403)

    try:
        # Здесь должна быть логика удаления файла из R2
        # s3_client = boto3.client(...)
        # s3_client.delete_object(Bucket=settings.S3_BUCKET_NAME, Key=video_data["filename"])
        pass # Пока заглушка
    except Exception as e:
        logging.error(f"Ошибка удаления файла из R2: {e}, filename: {video_data.get('filename')}")
    
    g.db.execute("DELETE FROM videos WHERE id = %s", (video_id,))
    session["flash"] = {"category": "success", "message": g.tr["video_deleted_success"]}

    referer = request.headers.get("referer")
    if referer and "/admin/" in referer:
        return redirect(referer)
    return redirect(url_for('users.profile_page', lang=lang))