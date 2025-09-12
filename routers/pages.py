# Файл: app/routers/pages.py
import math
from flask import Blueprint, request, render_template, Response, g
from app.config import settings

# 1. Создаем Blueprint вместо APIRouter
pages_bp = Blueprint('pages', __name__)

# 2. Декоратор меняется на @pages_bp.route(...)
@pages_bp.route("/", methods=['GET'])
def read_root():
    # 3. Контекст (user, tr, db) теперь берется из `g` автоматически
    #    благодаря @app.context_processor в app/main.py
    return render_template("index.html", background_image="index.jpg")

@pages_bp.route("/search", methods=['GET'])
def search_results():
    # 4. Параметры запроса (Query) берутся из объекта request
    q = request.args.get('q', '')
    location = request.args.get('location', '')
    page = request.args.get('page', 1, type=int)

    offset = (page - 1) * settings.ITEMS_PER_PAGE
    search_term = f"%{q}%" if q else "%"
    location_term = f"%{location}%" if location else "%"
    
    base_query = """
        FROM videos v JOIN users u ON v.user_id = u.id
        WHERE v.status = 'published'
        AND (v.what LIKE ?1 OR v.title LIKE ?1 OR v.description LIKE ?1)
        AND v."where" LIKE ?2
    """
    
    # 5. Доступ к D1 через g.db
    count_query = f"SELECT COUNT(*) {base_query}"
    total_items = g.db.fetch_val(count_query, (search_term, location_term))
    total_pages = math.ceil(total_items / settings.ITEMS_PER_PAGE) if total_items > 0 else 0
    
    select_query = f"""
        SELECT v.*, u.email as author_email 
        {base_query}
        ORDER BY v.id DESC 
        LIMIT ?3 OFFSET ?4
    """
    params = (search_term, location_term, settings.ITEMS_PER_PAGE, offset)
    result_videos = g.db.fetch_all(select_query, params)
    
    # 6. TemplateResponse заменяется на render_template
    return render_template("search_results.html",
        videos=result_videos,
        query=q,
        location=location,
        current_page=page,
        total_pages=total_pages,
        background_image="index.jpg"
    )

@pages_bp.route("/terms", methods=['GET'])
def terms_page():
    return render_template("terms.html", background_image="index.jpg")

@pages_bp.route("/privacy", methods=['GET'])
def privacy_page():
    return render_template("privacy.html", background_image="index.jpg")

@pages_bp.route("/contact", methods=['GET'])
def contact_page():
    return render_template("contact.html", background_image="index.jpg")

@pages_bp.route("/sitemap.xml", methods=['GET'])
def sitemap():
    base_url = "https://videos-review.com" # В идеале брать из настроек
    
    query = "SELECT id FROM videos WHERE status = 'published' ORDER BY id DESC"
    all_videos = g.db.fetch_all(query)
    
    xml_content = '<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
    static_pages = ["/", "/live", "/category/real-estate", "/category/auto", "/category/services", "/terms", "/privacy", "/contact"]
    for page in static_pages:
        xml_content += f'<url><loc>{base_url}{page}</loc></url>'
    for video in all_videos:
        xml_content += f'<url><loc>{base_url}/video/{video["id"]}</loc></url>'
    xml_content += '</urlset>'
    
    return Response(xml_content, mimetype="application/xml")