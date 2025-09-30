# Файл: app/routers/admin.py
import math
import logging
from flask import (Blueprint, request, session, g, render_template,
                   redirect, url_for)

from app.config import settings
from app.utils import send_email_notification
from app.decorators import admin_required

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.before_request
@admin_required
def before_request():
    """Защищает все маршруты в этом блюпринте"""
    pass

@admin_bp.route("/")
def dashboard():
    total_users = g.db.fetch_one("SELECT COUNT(*) AS total FROM users")['total']
    # ИЗМЕНЕНО: videos -> reviews
    total_reviews = g.db.fetch_one("SELECT COUNT(*) AS total FROM reviews")['total']
    total_likes = g.db.fetch_one("SELECT COUNT(*) AS total FROM likes")['total']
    pending_comments = g.db.fetch_one("SELECT COUNT(*) AS total FROM comments WHERE status = 'pending_review'")['total']
    
    stats = {
        "users": total_users, "reviews": total_reviews, 
        "likes": total_likes, "comments": pending_comments
    }
    return render_template("admin/dashboard.html", stats=stats)


@admin_bp.route("/reviews")
def admin_reviews_list():
    q = request.args.get('q', '')
    status = request.args.get('status', 'all')
    page = request.args.get('page', 1, type=int)

    offset = (page - 1) * settings.ITEMS_PER_PAGE
    search_term = f"%{q}%" if q else "%"
    
    # ИЗМЕНЕНО: v -> r, videos -> reviews
    where_clauses = ["(r.what LIKE %s OR r.where LIKE %s OR u.email LIKE %s)"]
    params = [search_term, search_term, search_term]

    if status != "all":
        where_clauses.append("r.status = %s")
        params.append(status)
    
    where_sql = " AND ".join(where_clauses)
    
    count_query = f"SELECT COUNT(*) AS total FROM reviews r JOIN users u ON r.user_id = u.id WHERE {where_sql}"
    total_items = g.db.fetch_one(count_query, tuple(params))['total']
    total_pages = math.ceil(total_items / settings.ITEMS_PER_PAGE) if total_items > 0 else 0
    
    params.extend([settings.ITEMS_PER_PAGE, offset])
    select_query = f"""
        SELECT r.*, u.email as author_email FROM reviews r JOIN users u ON r.user_id = u.id
        WHERE {where_sql} ORDER BY r.id DESC LIMIT %s OFFSET %s
    """
    result_reviews = g.db.fetch_all(select_query, tuple(params))
    
    return render_template("admin/reviews.html", 
        reviews=result_reviews, current_page=page, total_pages=total_pages,
        query=q, current_status=status
    )

def _handle_review_status_change(review_id: int, new_status: str):
    # ИЗМЕНЕНО: videos -> reviews
    g.db.execute("UPDATE reviews SET status = %s WHERE id = %s", (new_status, review_id))
    
    review_author_query = "SELECT r.title, u.email FROM reviews r JOIN users u ON r.user_id = u.id WHERE r.id = %s"
    review_author_data = g.db.fetch_one(review_author_query, (review_id,))
    lang = session.get('lang', 'en')

    if review_author_data:
        subject_key = "email_review_approved_subject" if new_status == 'published' else "email_review_rejected_subject"
        body_key = "email_review_approved_body" if new_status == 'published' else "email_review_rejected_body"
        
        # ИЗМЕНЕНО: videos.view_video_page -> reviews.view_review_page, video_id -> review_id
        review_link = url_for('reviews.view_review_page', review_id=review_id, lang=lang, _external=True)
        send_email_notification(
            recipients=[review_author_data["email"]],
            subject_key=subject_key, body_key=body_key,
            template_vars={"review_title": review_author_data["title"], "review_link": review_link}
        )
    else:
        logging.warning(f"Could not find author or review for review_id: {review_id} on status change.")

    message = g.tr["admin_review_approved"] if new_status == 'published' else g.tr["admin_review_rejected"]
    session["flash"] = {"category": "success", "message": message}
    return redirect(request.headers.get("referer", url_for('admin.admin_reviews_list')))


@admin_bp.route("/reviews/<int:review_id>/approve", methods=['POST'])
def approve_review(review_id: int):
    return _handle_review_status_change(review_id, 'published')


@admin_bp.route("/reviews/<int:review_id>/reject", methods=['POST'])
def reject_review(review_id: int):
    return _handle_review_status_change(review_id, 'rejected')


@admin_bp.route("/users")
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
def admin_delete_user(user_id: int):
    lang = session.get('lang', 'en')

    if user_id == g.user["id"]:
        session["flash"] = {"category": "error", "message": g.tr.get("admin_cannot_delete_self")}
        return redirect(url_for('admin.admin_users_list', lang=lang))
        
    g.db.execute("DELETE FROM users WHERE id = %s", (user_id,))
    session["flash"] = {"category": "success", "message": g.tr.get("admin_user_deleted_success")}
    return redirect(url_for('admin.admin_users_list', lang=lang))


@admin_bp.route("/comments")
def admin_comments_list():
    """Отображает список комментариев, ожидающих модерации."""
    # ИЗМЕНЕНО: v -> r, videos -> reviews, video_id -> review_id, video_title -> review_title
    query = """
        SELECT c.*, u.email as author_email, r.title as review_title, r.id as review_id
        FROM comments c
        JOIN users u ON c.user_id = u.id
        JOIN reviews r ON c.review_id = r.id
        WHERE c.status = 'pending_review' 
        ORDER BY c.created_at DESC
    """
    comments = g.db.fetch_all(query)
    return render_template("admin/comments.html", comments=comments)

def _handle_comment_status_change(comment_id: int, new_status: str):
    """Общая функция для одобрения/отклонения комментариев."""
    g.db.execute("UPDATE comments SET status = %s WHERE id = %s", (new_status, comment_id))
    
    if new_status == 'published':
        comment_info_query = """
            SELECT c.content, u.email, r.id as review_id, r.title as review_title
            FROM comments c
            JOIN users u ON c.user_id = u.id
            JOIN reviews r ON c.review_id = r.id
            WHERE c.id = %s
        """
        comment_info = g.db.fetch_one(comment_info_query, (comment_id,))
        lang = session.get('lang', 'en')

        if comment_info:
            review_link = url_for('reviews.view_review_page', review_id=comment_info["review_id"], lang=lang, _external=True)
            send_email_notification(
                recipients=[comment_info["email"]],
                subject_key="email_comment_approved_subject", 
                body_key="email_comment_approved_body",
                template_vars={
                    "review_title": comment_info["review_title"],
                    "comment_content": comment_info["content"],
                    "review_link": review_link
                })
            
    message = g.tr.get("admin_comment_approved") if new_status == 'published' else g.tr.get("admin_comment_rejected")
    session["flash"] = {"category": "success", "message": message}
    return redirect(url_for('admin.admin_comments_list'))

@admin_bp.route("/comments/<int:comment_id>/approve", methods=['POST'])
def approve_comment(comment_id: int):
    return _handle_comment_status_change(comment_id, 'published')

@admin_bp.route("/comments/<int:comment_id>/reject", methods=['POST'])
def reject_comment(comment_id: int):
    return _handle_comment_status_change(comment_id, 'rejected')

@admin_bp.route("/complaints")
def admin_complaints_list():
    query = """
        SELECT c.*, u.email as reporter_email, 
               r.id as review_id
        FROM complaints c
        LEFT JOIN users u ON c.user_id = u.id
        LEFT JOIN comments cm ON c.content_id = cm.id AND c.content_type = 'comment'
        LEFT JOIN reviews r ON cm.review_id = r.id OR (c.content_type = 'review' AND c.content_id = r.id)
        WHERE c.status = 'pending' ORDER BY c.id DESC
    """
    results = g.db.fetch_all(query)
    return render_template("admin/complaints.html", complaints=results)


@admin_bp.route("/complaints/<int:complaint_id>/handle", methods=['POST'])
def handle_complaint(complaint_id: int):
    action = request.form.get('action')
    complaint = g.db.fetch_one("SELECT * FROM complaints WHERE id = %s", (complaint_id,))

    if not complaint:
        session["flash"] = {"category": "error", "message": g.tr.get("complaint_not_found")}
        return redirect(url_for('admin.admin_complaints_list'))

    if action == 'delete_content':
        content_type = complaint['content_type']
        content_id = complaint['content_id']
        
        if content_type == 'review':
            g.db.execute("UPDATE reviews SET status = 'rejected' WHERE id = %s", (content_id,))
            message = g.tr.get("admin_review_rejected_and_complaint_resolved")
        elif content_type == 'comment':
            g.db.execute("DELETE FROM comments WHERE id = %s", (content_id,))
            message = g.tr.get("admin_comment_deleted_and_complaint_resolved")
        else:
            message = g.tr.get("complaint_resolved_success")
            
        g.db.execute("UPDATE complaints SET status = 'resolved' WHERE id = %s", (complaint_id,))
        session["flash"] = {"category": "success", "message": message}

    elif action == 'dismiss':
        g.db.execute("UPDATE complaints SET status = 'resolved' WHERE id = %s", (complaint_id,))
        session["flash"] = {"category": "info", "message": g.tr.get("complaint_dismissed")}
    
    else:
        session["flash"] = {"category": "error", "message": "Invalid action"}

    return redirect(url_for('admin.admin_complaints_list'))


# --- НОВЫЙ БЛОК ДЛЯ УПРАВЛЕНИЯ КАТЕГОРИЯМИ ---
@admin_bp.route('/categories', methods=['GET', 'POST'])
def manage_categories():
    if request.method == 'POST':
        name = request.form.get('name')
        slug = request.form.get('slug')
        parent_id = request.form.get('parent_id')

        if not name or not slug:
            session['flash'] = {'category': 'error', 'message': 'Название и слаг обязательны'}
            return redirect(url_for('admin.manage_categories'))

        try:
            if parent_id:
                query = "INSERT INTO subcategories (name, slug, category_id) VALUES (%s, %s, %s)"
                g.db.execute(query, (name, slug, int(parent_id)))
                session['flash'] = {'category': 'success', 'message': 'Подкатегория успешно добавлена'}
            else:
                query = "INSERT INTO categories (name, slug) VALUES (%s, %s)"
                g.db.execute(query, (name, slug))
                session['flash'] = {'category': 'success', 'message': 'Категория успешно добавлена'}
        except Exception as e:
            session['flash'] = {'category': 'error', 'message': f'Ошибка при добавлении: {e}'}

        return redirect(url_for('admin.manage_categories'))

    main_categories = g.db.fetch_all("SELECT * FROM categories ORDER BY name")
    subcategories_flat = g.db.fetch_all("SELECT * FROM subcategories ORDER BY name")
    
    categories_tree = {cat['id']: {'data': cat, 'subcategories': []} for cat in main_categories}
    for subcat in subcategories_flat:
        parent_id = subcat['category_id']
        if parent_id in categories_tree:
            categories_tree[parent_id]['subcategories'].append(subcat)

    return render_template('admin/categories.html', 
                           categories_tree=categories_tree.values(),
                           main_categories=main_categories)