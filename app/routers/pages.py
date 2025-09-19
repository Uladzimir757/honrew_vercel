# Файл: app/routers/pages.py
import math
from flask import Blueprint, request, render_template, Response, g
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
    base_url = "https://videos-review.com" 
    
    query = "SELECT id FROM videos WHERE status = 'published' ORDER BY id DESC"
    all_videos = g.db.fetch_all(query)
    
    xml_content = '<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
    static_pages = ["/", "/live", "/category/real-estate", "/category/auto", "/category/services", "/terms", "/privacy", "/contact"]
    for page in static_pages:
        xml_content += f'<url><loc>{base_url}{page}</loc></url>'
    if all_videos:
        for video in all_videos:
            xml_content += f'<url><loc>{base_url}/video/{video["id"]}</loc></url>'
    xml_content += '</urlset>'
    
    return Response(xml_content, mimetype="application/xml")