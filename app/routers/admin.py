# Файл: app/routers/admin.py
import math
from flask import (Blueprint, request, render_template, g, session,
                   redirect, url_for, jsonify, abort)
from app.decorators import admin_required
from app.config import settings

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/')
@admin_required
def manage_dashboard():
    stats_query = """
    SELECT
        (SELECT COUNT(*) FROM users) AS users,
        (SELECT COUNT(*) FROM reviews) AS reviews,
        (SELECT COUNT(*) FROM likes) AS likes,
        (SELECT COUNT(*) FROM comments WHERE status = 'pending_review') AS comments;
    """
    stats = g.db.fetch_one(stats_query)
    return render_template('admin/dashboard.html', stats=stats)

@admin_bp.route('/users')
@admin_required
def manage_users():
    page = request.args.get('page', 1, type=int)
    query = request.args.get('q', '')
    offset = (page - 1) * settings.ITEMS_PER_PAGE

    base_query = "FROM users WHERE email LIKE %s"
    search_term = f"%{query}%"
    
    count_query = f"SELECT COUNT(*) as total {base_query}"
    total_items = g.db.fetch_one(count_query, (search_term,))['total']
    total_pages = math.ceil(total_items / settings.ITEMS_PER_PAGE) if total_items > 0 else 0

    select_query = f"SELECT * {base_query} ORDER BY id DESC LIMIT %s OFFSET %s"
    users_list = g.db.fetch_all(select_query, (search_term, settings.ITEMS_PER_PAGE, offset))

    return render_template('admin/users.html', 
        users=users_list, 
        current_page=page, 
        total_pages=total_pages, 
        query=query
    )

@admin_bp.route('/users/delete/<int:user_id>', methods=['POST'])
@admin_required
def delete_user(user_id):
    if user_id == g.user['id']:
        session['flash'] = {'category': 'error', 'message': g.tr['admin_cannot_delete_self']}
        return redirect(url_for('admin.manage_users'))
    
    g.db.execute("DELETE FROM users WHERE id = %s", (user_id,))
    session['flash'] = {'category': 'success', 'message': g.tr['admin_user_deleted_success']}
    return redirect(url_for('admin.manage_users'))

@admin_bp.route('/reviews')
@admin_required
def manage_reviews():
    page = request.args.get('page', 1, type=int)
    query = request.args.get('q', '')
    status = request.args.get('status', 'all')
    offset = (page - 1) * settings.ITEMS_PER_PAGE

    base_query = """
        FROM reviews r 
        JOIN users u ON r.user_id = u.id 
        LEFT JOIN subcategories sc ON r.subcategory_id = sc.id
        LEFT JOIN categories c ON sc.category_id = c.id
        WHERE (r.what LIKE %s OR r.title LIKE %s OR u.email LIKE %s)
    """
    search_term = f"%{query}%"
    params = [search_term, search_term, search_term]

    if status != 'all':
        base_query += " AND r.status = %s"
        params.append(status)

    count_query = f"SELECT COUNT(r.id) as total {base_query}"
    total_items = g.db.fetch_one(count_query, tuple(params))['total']
    total_pages = math.ceil(total_items / settings.ITEMS_PER_PAGE) if total_items > 0 else 0
    
    select_query = f"""
        SELECT r.id, r.what, r.status, u.email as author_email, 
               c.name as category_name, sc.name as subcategory_name
        {base_query} ORDER BY r.id DESC LIMIT %s OFFSET %s
    """
    params.extend([settings.ITEMS_PER_PAGE, offset])
    reviews_list = g.db.fetch_all(select_query, tuple(params))

    return render_template('admin/reviews.html', 
        reviews=reviews_list, 
        current_page=page, 
        total_pages=total_pages, 
        query=query, 
        current_status=status
    )

@admin_bp.route('/reviews/approve/<int:review_id>', methods=['POST'])
@admin_required
def approve_review(review_id):
    g.db.execute("UPDATE reviews SET status = 'published' WHERE id = %s", (review_id,))
    session['flash'] = {'category': 'success', 'message': g.tr['admin_review_approved']}
    return redirect(request.referrer or url_for('admin.manage_reviews'))

@admin_bp.route('/reviews/reject/<int:review_id>', methods=['POST'])
@admin_required
def reject_review(review_id):
    g.db.execute("UPDATE reviews SET status = 'rejected' WHERE id = %s", (review_id,))
    session['flash'] = {'category': 'success', 'message': g.tr['admin_review_rejected']}
    return redirect(request.referrer or url_for('admin.manage_reviews'))

@admin_bp.route('/categories', methods=['GET', 'POST'])
@admin_required
def manage_categories():
    if request.method == 'POST':
        name = request.form.get('name')
        slug = request.form.get('slug')
        parent_id = request.form.get('parent_id')

        if parent_id: 
            g.db.execute("INSERT INTO subcategories (name, slug, category_id) VALUES (%s, %s, %s)",
                         (name, slug, int(parent_id)))
        else: 
            g.db.execute("INSERT INTO categories (name, slug) VALUES (%s, %s)", (name, slug))
        
        session['flash'] = {'category': 'success', 'message': 'Категория добавлена.'}
        return redirect(url_for('admin.manage_categories'))

    main_categories = g.db.fetch_all("SELECT id, name FROM categories ORDER BY name")
    
    categories_tree = []
    for cat in main_categories:
        subcategories = g.db.fetch_all(
            "SELECT id, name, slug FROM subcategories WHERE category_id = %s ORDER BY name", (cat['id'],)
        )
        categories_tree.append({'data': cat, 'subcategories': subcategories})

    return render_template('admin/categories.html',
                           categories_tree=categories_tree,
                           main_categories=main_categories)

@admin_bp.route('/categories/edit/<int:category_id>', methods=['GET', 'POST'])
@admin_required
def edit_category(category_id):
    # Сначала ищем в подкатегориях
    item = g.db.fetch_one("SELECT * FROM subcategories WHERE id = %s", (category_id,))
    is_subcategory = True
    if not item:
        # Если не нашли, ищем в основных категориях
        item = g.db.fetch_one("SELECT * FROM categories WHERE id = %s", (category_id,))
        is_subcategory = False

    if not item:
        abort(404)

    if request.method == 'POST':
        name = request.form.get('name')
        slug = request.form.get('slug')
        parent_id = request.form.get('parent_id')
        
        if is_subcategory:
            # Обновляем подкатегорию
            query = "UPDATE subcategories SET name = %s, slug = %s, category_id = %s WHERE id = %s"
            g.db.execute(query, (name, slug, int(parent_id) if parent_id else None, category_id))
        else:
            # Обновляем основную категорию
            query = "UPDATE categories SET name = %s, slug = %s WHERE id = %s"
            g.db.execute(query, (name, slug, category_id))
        
        session['flash'] = {'category': 'success', 'message': 'Категория успешно обновлена.'}
        return redirect(url_for('admin.manage_categories'))

    # Для GET-запроса получаем список всех основных категорий для выпадающего меню
    main_categories = g.db.fetch_all("SELECT id, name FROM categories ORDER BY name")
    return render_template('admin/edit_category.html', 
                           item=item, 
                           is_subcategory=is_subcategory,
                           main_categories=main_categories)

@admin_bp.route('/categories/delete/<int:category_id>', methods=['POST'])
@admin_required
def delete_category(category_id):
    g.db.execute("DELETE FROM subcategories WHERE id = %s", (category_id,))
    g.db.execute("DELETE FROM categories WHERE id = %s", (category_id,))
    
    session['flash'] = {'category': 'success', 'message': 'Категория удалена.'}
    return redirect(url_for('admin.manage_categories'))

@admin_bp.route('/complaints')
@admin_required
def manage_complaints():
    query = """
        SELECT 
            c.id, c.content_id, c.content_type, c.reason, u.email as reporter_email,
            CASE 
                WHEN c.content_type = 'comment' THEN cm.review_id
                ELSE NULL
            END as review_id
        FROM complaints c
        LEFT JOIN users u ON c.user_id = u.id
        LEFT JOIN comments cm ON c.content_type = 'comment' AND c.content_id = cm.id
        WHERE c.status = 'pending'
        ORDER BY c.created_at DESC
    """
    complaints = g.db.fetch_all(query)
    return render_template('admin/complaints.html', complaints=complaints)

@admin_bp.route('/complaints/handle/<int:complaint_id>', methods=['POST'])
@admin_required
def handle_complaint(complaint_id):
    action = request.form.get('action')
    complaint = g.db.fetch_one("SELECT * FROM complaints WHERE id = %s", (complaint_id,))
    if not complaint:
        abort(404)

    if action == 'dismiss':
        g.db.execute("UPDATE complaints SET status = 'dismissed' WHERE id = %s", (complaint_id,))
        session['flash'] = {'category': 'success', 'message': g.tr['complaint_dismissed']}
    
    elif action == 'delete_content':
        if complaint['content_type'] == 'review':
            g.db.execute("UPDATE reviews SET status = 'rejected' WHERE id = %s", (complaint['content_id'],))
            session['flash'] = {'category': 'success', 'message': g.tr['admin_review_rejected_and_complaint_resolved']}
        elif complaint['content_type'] == 'comment':
            g.db.execute("DELETE FROM comments WHERE id = %s", (complaint['content_id'],))
            session['flash'] = {'category': 'success', 'message': g.tr['admin_comment_deleted_and_complaint_resolved']}
        
        g.db.execute("UPDATE complaints SET status = 'resolved' WHERE id = %s", (complaint_id,))

    return redirect(url_for('admin.manage_complaints'))

@admin_bp.route('/comments')
@admin_required
def manage_comments():
    query = """
        SELECT c.id, c.content, u.email as author_email, r.id as review_id, r.title as review_title
        FROM comments c
        JOIN users u ON c.user_id = u.id
        JOIN reviews r ON c.review_id = r.id
        WHERE c.status = 'pending_review'
        ORDER BY c.created_at DESC
    """
    comments = g.db.fetch_all(query)
    return render_template('admin/comments.html', comments=comments)

@admin_bp.route('/comments/approve/<int:comment_id>', methods=['POST'])
@admin_required
def approve_comment(comment_id):
    g.db.execute("UPDATE comments SET status = 'published' WHERE id = %s", (comment_id,))
    session['flash'] = {'category': 'success', 'message': g.tr['admin_comment_approved']}
    return redirect(url_for('admin.manage_comments'))

@admin_bp.route('/comments/reject/<int:comment_id>', methods=['POST'])
@admin_required
def reject_comment(comment_id):
    g.db.execute("DELETE FROM comments WHERE id = %s", (comment_id,))
    session['flash'] = {'category': 'success', 'message': g.tr['admin_comment_rejected']}
    return redirect(url_for('admin.manage_comments'))