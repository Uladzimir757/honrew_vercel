# Файл: app/routers/pages.py
import math
from flask import Blueprint, request, render_template, Response, g, url_for
from app.config import settings
from app.decorators import login_required

pages_bp = Blueprint('pages', __name__)

@pages_bp.route("/", methods=['GET'], endpoint='home')
def read_root():
    return render_template("index.html")

@pages_bp.route("/search", methods=['GET'])
def search_results():
    q = request.args.get('q', '')
    location = request.args.get('location', '')
    page = request.args.get('page', 1, type=int)

    offset = (page - 1) * settings.ITEMS_PER_PAGE
    search_term = f"%{q}%" if q else "%"
    location_term = f"%{location}%" if location else "%"
    
    base_query = """
        FROM reviews r JOIN users u ON r.user_id = u.id
        WHERE r.status = 'published'
        AND (r.what LIKE %s OR r.title LIKE %s OR r.description LIKE %s)
        AND r."where" LIKE %s
    """
    
    count_query = f"SELECT COUNT(*) AS total {base_query}"
    params = (search_term, search_term, search_term, location_term)
    total_items = g.db.fetch_one(count_query, params)['total']
    total_pages = math.ceil(total_items / settings.ITEMS_PER_PAGE) if total_items > 0 else 0
    
    select_query = f"""
        SELECT r.*, u.email as author_email 
        {base_query}
        ORDER BY r.id DESC 
        LIMIT %s OFFSET %s
    """
    params_select = list(params) + [settings.ITEMS_PER_PAGE, offset]
    result_reviews = g.db.fetch_all(select_query, tuple(params_select))
    
    return render_template("search_results.html",
        reviews=result_reviews,
        query=q,
        location=location,
        current_page=page,
        total_pages=total_pages
    )

@pages_bp.route("/terms", methods=['GET'])
def terms_page():
    return render_template("terms.html")

@pages_bp.route("/privacy", methods=['GET'])
def privacy_page():
    return render_template("privacy.html")

@pages_bp.route("/contact", methods=['GET'])
def contact_page():
    return render_template("contact.html")

@pages_bp.route('/record')
@login_required
def record_page():
    return render_template("record.html")

@pages_bp.route("/sitemap.xml", methods=['GET'])
def sitemap():
    # Собираем статические страницы
    urls = [
        {'loc': url_for('pages.home', _external=True), 'changefreq': 'daily', 'priority': '1.0'},
        {'loc': url_for('reviews.live_page', _external=True), 'changefreq': 'daily', 'priority': '0.9'},
        {'loc': url_for('pages.terms_page', _external=True), 'changefreq': 'monthly', 'priority': '0.5'},
        {'loc': url_for('pages.privacy_page', _external=True), 'changefreq': 'monthly', 'priority': '0.5'},
        {'loc': url_for('pages.contact_page', _external=True), 'changefreq': 'monthly', 'priority': '0.5'},
    ]
    
    # Динамически добавляем все категории и подкатегории
    categories = g.db.fetch_all("SELECT slug FROM categories")
    if categories:
        for cat in categories:
            urls.append({'loc': url_for('reviews.category_page', category_slug=cat['slug'], _external=True), 'changefreq': 'weekly', 'priority': '0.8'})

    subcategories = g.db.fetch_all("SELECT c.slug as cat_slug, sc.slug as sub_slug FROM subcategories sc JOIN categories c ON sc.category_id = c.id")
    if subcategories:
        for sub in subcategories:
             urls.append({'loc': url_for('reviews.category_page', category_slug=sub['cat_slug'], subcategory_slug=sub['sub_slug'], _external=True), 'changefreq': 'weekly', 'priority': '0.7'})

    # Динамически добавляем все отзывы
    all_reviews = g.db.fetch_all("SELECT id, created_at FROM reviews WHERE status = 'published'")
    if all_reviews:
        for review in all_reviews:
            urls.append({
                'loc': url_for('reviews.view_review_page', review_id=review["id"], _external=True),
                'lastmod': review["created_at"].strftime('%Y-%m-%d'),
                'changefreq': 'yearly',
                'priority': '0.6'
            })
    
    sitemap_xml = render_template("sitemap.xml", urls=urls)
    return Response(sitemap_xml, mimetype="application/xml")