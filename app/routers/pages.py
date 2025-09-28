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
        FROM videos v JOIN users u ON v.user_id = u.id
        WHERE v.status = 'published'
        AND (v.what LIKE %s OR v.title LIKE %s OR v.description LIKE %s)
        AND v."where" LIKE %s
    """
    
    count_query = f"SELECT COUNT(*) AS total {base_query}"
    params_count = (search_term, search_term, search_term, location_term)
    total_items = g.db.fetch_one(count_query, params_count)['total']
    total_pages = math.ceil(total_items / settings.ITEMS_PER_PAGE) if total_items > 0 else 0
    
    select_query = f"""
        SELECT v.*, u.email as author_email 
        {base_query}
        ORDER BY v.id DESC 
        LIMIT %s OFFSET %s
    """
    params_select = (search_term, search_term, search_term, location_term, settings.ITEMS_PER_PAGE, offset)
    result_videos = g.db.fetch_all(select_query, params_select)
    
    return render_template("search_results.html",
        videos=result_videos,
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
    # Собираем статические страницы с метаданными
    urls = [
        {'loc': url_for('pages.home', _external=True), 'changefreq': 'daily', 'priority': '1.0'},
        {'loc': url_for('videos.live_page', _external=True), 'changefreq': 'daily', 'priority': '0.9'},
        {'loc': url_for('videos.category_page', category_name='real-estate', _external=True), 'changefreq': 'weekly', 'priority': '0.8'},
        {'loc': url_for('videos.category_page', category_name='auto', _external=True), 'changefreq': 'weekly', 'priority': '0.8'},
        {'loc': url_for('videos.category_page', category_name='services', _external=True), 'changefreq': 'weekly', 'priority': '0.8'},
        {'loc': url_for('pages.terms_page', _external=True), 'changefreq': 'monthly', 'priority': '0.5'},
        {'loc': url_for('pages.privacy_page', _external=True), 'changefreq': 'monthly', 'priority': '0.5'},
        {'loc': url_for('pages.contact_page', _external=True), 'changefreq': 'monthly', 'priority': '0.5'},
    ]
    
    # Получаем динамические страницы (видео) с датой обновления
    query = "SELECT id, created_at FROM videos WHERE status = 'published' ORDER BY id DESC"
    all_videos = g.db.fetch_all(query)
    
    if all_videos:
        for video in all_videos:
            url_info = {
                'loc': url_for('videos.view_video_page', video_id=video["id"], _external=True),
                'lastmod': video["created_at"].strftime('%Y-%m-%d'),
                'changefreq': 'yearly',
                'priority': '0.7'
            }
            urls.append(url_info)
    
    # Рендерим шаблон, передавая в него список URL
    sitemap_xml = render_template("sitemap.xml", urls=urls)
    
    return Response(sitemap_xml, mimetype="application/xml")