# Файл: app/routers/reviews.py
import os
import uuid
import math
import logging
import boto3
from botocore.exceptions import ClientError
from flask import (Blueprint, request, session, g, render_template,
                   redirect, url_for, jsonify, abort)

from app.config import settings
from app.moderation import check_text_for_stop_words
from app.utils import send_email_notification
from app.decorators import login_required

reviews_bp = Blueprint('reviews', __name__)

# --- Вспомогательная функция для удаления файлов из S3/R2 ---
def delete_s3_objects(filenames):
    if not filenames:
        return
    try:
        s3_client = boto3.client(
            's3',
            endpoint_url=settings.S3_ENDPOINT_URL,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name="auto"
        )
        objects_to_delete = [{'Key': filename} for filename in filenames]
        s3_client.delete_objects(
            Bucket=settings.S3_BUCKET_NAME,
            Delete={'Objects': objects_to_delete}
        )
        logging.info(f"Successfully deleted {len(filenames)} files from R2.")
    except Exception as e:
        logging.error(f"Ошибка удаления файлов из R2: {e}")

# --- Ваши существующие функции (без изменений) ---

@reviews_bp.route("/review/<int:review_id>")
def view_review_page(review_id: int):
    # Запрос основной информации об отзыве
    query_review = """
        SELECT r.*, u.email as author_email, u.id as author_id,
               sc.name as subcategory_name, sc.slug as subcategory_slug,
               c.name as category_name, c.slug as category_slug,
               sc.category_id as category_id
        FROM reviews r 
        JOIN users u ON r.user_id = u.id
        LEFT JOIN subcategories sc ON r.subcategory_id = sc.id
        LEFT JOIN categories c ON sc.category_id = c.id
        WHERE r.id = %s
    """
    review_data = g.db.fetch_one(query_review, (review_id,))

    if not review_data:
        return redirect(url_for('pages.home', lang=session.get('lang')))
    
    is_owner = g.user and g.user["id"] == review_data["author_id"]
    is_admin = g.user and g.user.get("is_admin")
    is_published = review_data["status"] == 'published'

    if not is_published and not is_owner and not is_admin:
        return redirect(url_for('pages.home', lang=session.get('lang')))

    # Запрос всех медиа-файлов для этого отзыва
    query_media = "SELECT id, filename, media_type FROM media_files WHERE review_id = %s ORDER BY id"
    media_files_data = g.db.fetch_all(query_media, (review_id,))
    
    base_media_url = f"{settings.R2_PUBLIC_URL}/{settings.S3_BUCKET_NAME}"
    media_items = [
        {"id": mf['id'], "url": f"{base_media_url}/{mf['filename']}", "type": mf['media_type']}
        for mf in media_files_data
    ]

    likes_count = g.db.fetch_one("SELECT COUNT(*) AS total FROM likes WHERE review_id = %s", (review_id,))['total']
    
    query_comments = """
        SELECT c.*, u.id as author_id, u.email as author_email
        FROM comments c JOIN users u ON c.user_id = u.id
        WHERE c.review_id = %s AND c.status = 'published'
        ORDER BY c.created_at DESC
    """
    review_comments = g.db.fetch_all(query_comments, (review_id,))

    user_has_liked = False
    if g.user:
        like = g.db.fetch_one("SELECT 1 FROM likes WHERE review_id = %s AND user_id = %s", (review_id, g.user["id"]))
        user_has_liked = bool(like)

    query_reply = """
        SELECT cr.*, u.email as company_email
        FROM company_replies cr JOIN users u ON cr.user_id = u.id
        WHERE cr.review_id = %s
    """
    reply_data = g.db.fetch_one(query_reply, (review_id,))

    can_reply = g.user and g.user.get("user_type") == 'company' and not reply_data

    return render_template("video_view.html",
        review=review_data, 
        media_items=media_items,
        likes_count=likes_count, 
        comments=review_comments,
        user_has_liked=user_has_liked, 
        title=f"{review_data['title']} - HonestReviews",
        description=review_data.get('description', '')[:155],
        company_reply=reply_data, 
        can_reply=can_reply
    )

@reviews_bp.route("/review/<int:review_id>/reply", methods=['POST'])
@login_required
def handle_company_reply(review_id: int):
    content = request.form.get('content')
    lang = session.get('lang', 'en')

    if g.user["user_type"] != 'company':
        abort(403)

    existing_reply = g.db.fetch_one("SELECT id FROM company_replies WHERE review_id = %s", (review_id,))
    if existing_reply:
        return "A reply for this review already exists.", 400

    query = "INSERT INTO company_replies (content, review_id, user_id) VALUES (%s, %s, %s)"
    g.db.execute(query, (content, review_id, g.user["id"]))

    session["flash"] = {"category": "success", "message": g.tr["company_reply_success"]}
    return redirect(url_for('reviews.view_review_page', review_id=review_id, lang=lang))

@reviews_bp.route("/api/review/<int:review_id>/like", methods=['POST'])
@login_required
def api_handle_like(review_id: int):
    existing_like = g.db.fetch_one("SELECT 1 FROM likes WHERE review_id = %s AND user_id = %s", (review_id, g.user["id"]))
    lang = session.get('lang', 'en')
    
    if existing_like:
        g.db.execute("DELETE FROM likes WHERE review_id = %s AND user_id = %s", (review_id, g.user["id"]))
        user_has_liked = False
    else:
        g.db.execute("INSERT INTO likes (review_id, user_id) VALUES (%s, %s)", (review_id, g.user["id"]))
        user_has_liked = True
        
        author_info_query = "SELECT u.email, r.title FROM reviews r JOIN users u ON r.user_id = u.id WHERE r.id = %s"
        author_info = g.db.fetch_one(author_info_query, (review_id,))
        
        if author_info and author_info["email"] != g.user["email"]:
            review_link = url_for('reviews.view_review_page', review_id=review_id, lang=lang, _external=True)
            send_email_notification(
                recipients=[author_info["email"]], 
                subject_key="email_new_like_subject",
                body_key="email_new_like_body",
                template_vars={ "liker_email": g.user["email"], "review_title": author_info["title"], "review_link": review_link }
            )
            
    likes_count = g.db.fetch_one("SELECT COUNT(*) AS total FROM likes WHERE review_id = %s", (review_id,))['total']
    return jsonify({"likes_count": likes_count, "user_has_liked": user_has_liked})



@reviews_bp.route("/api/review/<int:review_id>/comment", methods=['POST'])
@login_required
def api_handle_comment(review_id: int):
    content = request.form.get("content")
    if not content or not content.strip():
        return jsonify({"status": "error", "message": "Comment cannot be empty"}), 400
    
    status = 'published' if not check_text_for_stop_words(content, g.lang) else 'pending_review'
    
    # Добавляем комментарий и сразу получаем его ID
    query = "INSERT INTO comments (content, review_id, user_id, status) VALUES (%s, %s, %s, %s) RETURNING id"
    new_comment_id = g.db.fetch_one(query, (content.strip(), review_id, g.user["id"], status))['id']

    if status == 'published':
        # Если коммент опубликован, отправляем его данные обратно на фронтенд
        new_comment_data = {
            "id": new_comment_id,
            "content": content.strip(),
            "author_email": g.user["email"],
            "author_id": g.user["id"]
        }
        return jsonify({
            "status": "success", 
            "message": g.tr.get("comment_published_success"),
            "comment": new_comment_data
        })
    else:
        # Если коммент ушел на модерацию, просто сообщаем об этом
        return jsonify({
            "status": "moderation",
            "message": g.tr.get("review_moderation_pending")
        })

@reviews_bp.route("/live")
def live_page():
    page = request.args.get('page', 1, type=int)
    offset = (page - 1) * settings.ITEMS_PER_PAGE

    count_query = "SELECT COUNT(*) AS total FROM reviews WHERE status = 'published'"
    total_items = g.db.fetch_one(count_query)['total']
    total_pages = math.ceil(total_items / settings.ITEMS_PER_PAGE) if total_items > 0 else 0

    query = """
        SELECT r.id, r.title, r.description, r.rating, r.user_id, u.email as author_email,
               mf.filename, mf.media_type
        FROM reviews r
        JOIN users u ON r.user_id = u.id
        LEFT JOIN (
            SELECT DISTINCT ON (review_id) review_id, filename, media_type
            FROM media_files
            ORDER BY review_id, id
        ) AS mf ON r.id = mf.review_id
        WHERE r.status = 'published'
        ORDER BY r.created_at DESC
        LIMIT %s OFFSET %s
    """
    reviews = g.db.fetch_all(query, (settings.ITEMS_PER_PAGE, offset))
    return render_template("live.html", reviews=reviews, current_page=page, total_pages=total_pages)

@reviews_bp.route("/category/<category_slug>")
@reviews_bp.route("/category/<category_slug>/<subcategory_slug>")
def category_page(category_slug: str, subcategory_slug: str = None):
    page = request.args.get('page', 1, type=int)
    offset = (page - 1) * settings.ITEMS_PER_PAGE
    
    base_query = """
        FROM reviews r
        JOIN users u ON r.user_id = u.id
        JOIN subcategories sc ON r.subcategory_id = sc.id
        JOIN categories c ON sc.category_id = c.id
        WHERE r.status = 'published' AND c.slug = %s
    """
    params = [category_slug]
    
    if subcategory_slug:
        base_query += " AND sc.slug = %s"
        params.append(subcategory_slug)
        query = """
            SELECT sc.*, c.slug as category_slug FROM subcategories sc 
            JOIN categories c ON sc.category_id = c.id 
            WHERE sc.slug=%s AND c.slug=%s
        """
        current_category = g.db.fetch_one(query, (subcategory_slug, category_slug))
    else:
        current_category = g.db.fetch_one("SELECT * FROM categories WHERE slug=%s", (category_slug,))

    count_query = f"SELECT COUNT(r.id) AS total {base_query}"
    total_items = g.db.fetch_one(count_query, tuple(params))['total']
    total_pages = math.ceil(total_items / settings.ITEMS_PER_PAGE) if total_items > 0 else 0

    select_query = f"""
        SELECT r.id, r.title, r.what, r.where, r.rating, r.description, r.user_id, u.email as author_email,
               (SELECT mf.filename FROM media_files mf WHERE mf.review_id = r.id ORDER BY mf.id LIMIT 1) as filename,
               (SELECT mf.media_type FROM media_files mf WHERE mf.review_id = r.id ORDER BY mf.id LIMIT 1) as media_type
        {base_query}
        ORDER BY r.id DESC
        LIMIT %s OFFSET %s
    """
    params.extend([settings.ITEMS_PER_PAGE, offset])
    reviews = g.db.fetch_all(select_query, tuple(params))
    
    return render_template("category.html",
        reviews=reviews, current_page=page, total_pages=total_pages,
        category=current_category
    )

@reviews_bp.route("/upload", methods=['GET', 'POST'])
@login_required
def handle_upload():
    if request.method == 'GET':
        category_slug = request.args.get('category')
        selected_category_id = None
        if category_slug:
            cat_data = g.db.fetch_one("SELECT id FROM categories WHERE slug = %s", (category_slug,))
            if cat_data:
                selected_category_id = cat_data['id']
        return render_template("upload.html", selected_category_id=selected_category_id)

    if request.method == 'POST':
        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "message": "Invalid JSON payload"}), 400

        what = data.get('what')
        where = data.get('where')
        title = data.get('title')
        description = data.get('description')
        subcategory_id = data.get('subcategory_id')
        rating = data.get('rating')
        uploaded_files = data.get('objectNames')

        if not all([what, where, title, description, subcategory_id, rating, uploaded_files]):
            return jsonify({"status": "error", "message": "Missing required fields"}), 400
        
        if not isinstance(uploaded_files, list) or not uploaded_files:
            return jsonify({"status": "error", "message": "objectNames must be a non-empty list"}), 400

        text_to_check = f"{title} {what} {where} {description}"
        status = 'published' if not check_text_for_stop_words(text_to_check, g.lang) else 'pending_review'
        
        try:
            review_query = """
                INSERT INTO reviews (title, description, subcategory_id, user_id, what, "where", rating, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING id
            """
            review_params = (title, description, subcategory_id, g.user["id"], what, where, rating, status)
            new_review = g.db.fetch_one(review_query, review_params)
            new_review_id = new_review['id']

            for file_info in uploaded_files:
                object_name = file_info.get('objectName')
                media_type = file_info.get('mediaType', 'video')
                if not object_name:
                    continue
                
                media_query = "INSERT INTO media_files (review_id, filename, media_type) VALUES (%s, %s, %s)"
                g.db.execute(media_query, (new_review_id, object_name, media_type))
            
            if status == 'published':
                session["flash"] = {"category": "success", "message": g.tr.get("review_published_success")}
            else:
                session["flash"] = {"category": "info", "message": g.tr.get("review_moderation_pending")}

            return jsonify({"status": "success", "redirectUrl": url_for('pages.home', lang=g.lang)})

        except Exception as e:
            logging.error(f"Database error during multi-upload: {e}")
            g.db._connection.rollback()
            return jsonify({"status": "error", "message": "Failed to save review details."}), 500

@reviews_bp.route("/api/generate-upload-url", methods=["POST"])
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

# --- НОВАЯ, ПОЛНОЦЕННАЯ ФУНКЦИЯ РЕДАКТИРОВАНИЯ ---
@reviews_bp.route('/review/edit/<int:review_id>', methods=['GET', 'POST'])
@login_required
def edit_review(review_id):
    # Получаем полную информацию об отзыве, включая категорию и подкатегорию
    query = """
        SELECT r.*, sc.category_id 
        FROM reviews r 
        LEFT JOIN subcategories sc ON r.subcategory_id = sc.id
        WHERE r.id = %s
    """
    review = g.db.fetch_one(query, (review_id,))
    if not review or (review['user_id'] != g.user['id'] and not g.user.get('is_admin')):
        abort(403)

    if request.method == 'POST':
        # Получаем данные из обычной формы (не JSON)
        title = request.form.get('title')
        description = request.form.get('description')
        what = request.form.get('what')
        where = request.form.get('where')
        subcategory_id = request.form.get('subcategory_id')
        
        # Обновляем текстовые поля и категорию
        update_query = """
            UPDATE reviews SET title = %s, description = %s, what = %s, "where" = %s, subcategory_id = %s
            WHERE id = %s
        """
        g.db.execute(update_query, (title, description, what, where, subcategory_id, review_id))
        
        session["flash"] = {"category": "success", "message": g.tr["review_updated_success"]}
        return redirect(url_for('reviews.view_review_page', review_id=review_id, lang=g.lang))
    
    # Для GET-запроса: получаем медиа-файлы и категории для отображения в форме
    media_files = g.db.fetch_all("SELECT id, filename, media_type FROM media_files WHERE review_id = %s ORDER BY id", (review_id,))
    
    return render_template('edit_review.html', 
        review=review, 
        media_files=media_files,
        selected_category_id=review.get('category_id'),
        selected_subcategory_id=review.get('subcategory_id')
    )

@reviews_bp.route("/review/delete/<int:review_id>", methods=['POST'])
@login_required
def delete_review(review_id: int):
    lang = session.get('lang', 'en')
    review_data = g.db.fetch_one("SELECT id, user_id FROM reviews WHERE id = %s", (review_id,))

    if not review_data or (review_data["user_id"] != g.user["id"] and not g.user.get("is_admin")):
        abort(403)

    media_files_to_delete = g.db.fetch_all("SELECT filename FROM media_files WHERE review_id = %s", (review_id,))
    filenames = [mf['filename'] for mf in media_files_to_delete if mf.get('filename')]
    
    if filenames:
        delete_s3_objects(filenames)
    
    g.db.execute("DELETE FROM reviews WHERE id = %s", (review_id,))
    session["flash"] = {"category": "success", "message": g.tr["review_deleted_success"]}

    referer = request.headers.get("referer")
    if referer and "/admin/" in referer:
        return redirect(referer)
    return redirect(url_for('users.profile_page', lang=lang))

# Новый эндпоинт для удаления медиа-файла
@reviews_bp.route("/media/delete/<int:media_id>", methods=['POST'])
@login_required
def delete_media_file(media_id: int):
    media_file = g.db.fetch_one("SELECT mf.filename, r.user_id FROM media_files mf JOIN reviews r ON mf.review_id = r.id WHERE mf.id = %s", (media_id,))

    if not media_file or (media_file['user_id'] != g.user['id'] and not g.user.get('is_admin')):
        abort(403)

    if media_file.get("filename"):
        delete_s3_objects([media_file["filename"]])

    g.db.execute("DELETE FROM media_files WHERE id = %s", (media_id,))
    
    return jsonify({"status": "success", "message": "File deleted."})