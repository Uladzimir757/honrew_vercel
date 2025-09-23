# Файл: app/routers/admin.py
import math
import logging
from flask import (Blueprint, request, session, g, render_template, 
                   redirect, url_for)

from app.config import settings
from app.utils import send_email_notification
from app.decorators import admin_required

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route("/")
@admin_required
def admin_dashboard():
    total_users = g.db.fetch_one("SELECT COUNT(*) AS total FROM users")['total']
    total_reviews = g.db.fetch_one("SELECT COUNT(*) AS total FROM videos")['total']
    total_likes = g.db.fetch_one("SELECT COUNT(*) AS total FROM likes")['total']
    # ИЗМЕНЕНИЕ: Считаем только комментарии, ожидающие проверки
    pending_comments = g.db.fetch_one("SELECT COUNT(*) AS total FROM comments WHERE status = 'pending_review'")['total']
    
    stats = {
        "users": total_users, "reviews": total_reviews, 
        "likes": total_likes, "comments": pending_comments
    }
    return render_template("admin/dashboard.html", stats=stats)


@admin_bp.route("/reviews")
@admin_required
def admin_reviews_list():
    q = request.args.get('q', '')
    status = request.args.get('status', 'all')
    page = request.args.get('page', 1, type=int)

    offset = (page - 1) * settings.ITEMS_PER_PAGE
    search_term = f"%{q}%" if q else "%"
    
    where_clauses = ["(v.what LIKE %s OR v.where LIKE %s OR u.email LIKE %s)"]
    params = [search_term, search_term, search_term]

    if status != "all":
        where_clauses.append("v.status = %s")
        params.append(status)
    
    where_sql = " AND ".join(where_clauses)
    
    count_query = f"SELECT COUNT(*) AS total FROM videos v JOIN users u ON v.user_id = u.id WHERE {where_sql}"
    total_items = g.db.fetch_one(count_query, tuple(params))['total']
    total_pages = math.ceil(total_items / settings.ITEMS_PER_PAGE) if total_items > 0 else 0
    
    params.extend([settings.ITEMS_PER_PAGE, offset])
    select_query = f"""
        SELECT v.*, u.email as author_email FROM videos v JOIN users u ON v.user_id = u.id
        WHERE {where_sql} ORDER BY v.id DESC LIMIT %s OFFSET %s
    """
    result_reviews = g.db.fetch_all(select_query, tuple(params))
    
    return render_template("admin/reviews.html", 
        reviews=result_reviews, current_page=page, total_pages=total_pages,
        query=q, current_status=status
    )

def _handle_review_status_change(video_id: int, new_status: str):
    g.db.execute("UPDATE videos SET status = %s WHERE id = %s", (new_status, video_id))
    
    video_author_query = "SELECT v.title, u.email FROM videos v JOIN users u ON v.user_id = u.id WHERE v.id = %s"
    video_author_data = g.db.fetch_one(video_author_query, (video_id,))
    lang = session.get('lang', 'en')

    if video_author_data:
        subject_key = "email_review_approved_subject" if new_status == 'published' else "email_review_rejected_subject"
        body_key = "email_review_approved_body" if new_status == 'published' else "email_review_rejected_body"
        
        video_link = url_for('videos.view_video_page', video_id=video_id, lang=lang, _external=True)
        send_email_notification(
            recipients=[video_author_data["email"]],
            subject_key=subject_key, body_key=body_key,
            template_vars={"video_title": video_author_data["title"], "video_link": video_link}
        )
    else:
        logging.warning(f"Could not find author or review for video_id: {video_id} on status change.")

    message = g.tr["admin_review_approved"] if new_status == 'published' else g.tr["admin_review_rejected"]
    session["flash"] = {"category": "success", "message": message}
    return redirect(request.headers.get("referer", url_for('admin.admin_reviews_list')))


@admin_bp.route("/reviews/<int:video_id>/approve", methods=['POST'])
@admin_required
def approve_review(video_id: int):
    return _handle_review_status_change(video_id, 'published')


@admin_bp.route("/reviews/<int:video_id>/reject", methods=['POST'])
@admin_required
def reject_review(video_id: int):
    return _handle_review_status_change(video_id, 'rejected')


@admin_bp.route("/users")
@admin_required
def admin_users_list():
    q = request.args.get('q', '')
    page = request.args.get('page', 1, type=int)

    offset = (page - 1) * settings.ITEMS_PER_PAGE
    search_term = f"%{q}%" if q else "%"

    count_query = "SELECT COUNT(*) AS total FROM users WHERE email LIKE %s"
    total_items = g.db.fetch_one(count_query, (search_term,))['total']
    total_pages = math.ceil(total_items / settings.ITEMS_PER_PAGE) if total_items > 0 else 0
    
    select_query = "SELECT * FROM users WHERE email LIKE %s ORDER BY id LIMIT %s OFFSET %s"
    result_users = g.db.fetch_all(select_query, (search_term, settings.ITEMS_PER_PAGE, offset))
    
    return render_template("admin/users.html", 
        users=result_users, current_page=page, total_pages=total_pages, query=q
    )


@admin_bp.route("/users/<int:user_id>/delete", methods=['POST'])
@admin_required
def admin_delete_user(user_id: int):
    lang = session.get('lang', 'en')

    if user_id == g.user["id"]:
        session["flash"] = {"category": "error", "message": g.tr.get("admin_cannot_delete_self")}
        return redirect(url_for('admin.admin_users_list', lang=lang))
        
    g.db.execute("DELETE FROM users WHERE id = %s", (user_id,))
    session["flash"] = {"category": "success", "message": g.tr.get("admin_user_deleted_success")}
    return redirect(url_for('admin.admin_users_list', lang=lang))

# --- НОВЫЙ КОД ДЛЯ МОДЕРАЦИИ КОММЕНТАРИЕВ ---

@admin_bp.route("/comments")
@admin_required
def admin_comments_list():
    """Отображает список комментариев, ожидающих модерации."""
    query = """
        SELECT c.*, u.email as author_email, v.title as video_title
        FROM comments c
        JOIN users u ON c.user_id = u.id
        JOIN videos v ON c.video_id = v.id
        WHERE c.status = 'pending_review' 
        ORDER BY c.created_at DESC
    """
    comments = g.db.fetch_all(query)
    return render_template("admin/comments.html", comments=comments)

def _handle_comment_status_change(comment_id: int, new_status: str):
    """Общая функция для одобрения/отклонения комментариев."""
    g.db.execute("UPDATE comments SET status = %s WHERE id = %s", (new_status, comment_id))
    
    # Отправка email только при одобрении
    if new_status == 'published':
        comment_info_query = """
            SELECT c.content, u.email, v.id as video_id, v.title as video_title
            FROM comments c
            JOIN users u ON c.user_id = u.id
            JOIN videos v ON c.video_id = v.id
            WHERE c.id = %s
        """
        comment_info = g.db.fetch_one(comment_info_query, (comment_id,))
        lang = session.get('lang', 'en')

        if comment_info:
            video_link = url_for('videos.view_video_page', video_id=comment_info["video_id"], lang=lang, _external=True)
            send_email_notification(
                recipients=[comment_info["email"]],
                subject_key="email_comment_approved_subject", 
                body_key="email_comment_approved_body",
                template_vars={
                    "video_title": comment_info["video_title"],
                    "comment_content": comment_info["content"],
                    "video_link": video_link
                })
            
    message = g.tr.get("admin_comment_approved") if new_status == 'published' else g.tr.get("admin_comment_rejected")
    session["flash"] = {"category": "success", "message": message}
    return redirect(url_for('admin.admin_comments_list'))

@admin_bp.route("/comments/<int:comment_id>/approve", methods=['POST'])
@admin_required
def approve_comment(comment_id: int):
    return _handle_comment_status_change(comment_id, 'published')

@admin_bp.route("/comments/<int:comment_id>/reject", methods=['POST'])
@admin_required
def reject_comment(comment_id: int):
    return _handle_comment_status_change(comment_id, 'rejected')

# --- КОНЕЦ НОВОГО КОДА ---

@admin_bp.route("/complaints")
@admin_required
def admin_complaints_list():
    query = """
        SELECT c.*, u.email as reporter_email, cm.video_id
        FROM complaints c
        LEFT JOIN users u ON c.user_id = u.id
        LEFT JOIN comments cm ON c.content_id = cm.id AND c.content_type = 'comment'
        WHERE c.status = 'pending' ORDER BY c.id DESC
    """
    results = g.db.fetch_all(query)
    return render_template("admin/complaints.html", complaints=results)


@admin_bp.route("/complaints/<int:complaint_id>/resolve", methods=['POST'])
@admin_required
def resolve_complaint(complaint_id: int):
    lang = session.get('lang', 'en')
    g.db.execute("UPDATE complaints SET status = 'resolved' WHERE id = %s", (complaint_id,))
    session["flash"] = {"category": "success", "message": g.tr.get("complaint_resolved_success")}
    return redirect(url_for('admin.admin_complaints_list', lang=lang))

