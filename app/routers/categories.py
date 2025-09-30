# Файл: app/routers/categories.py
from flask import Blueprint, jsonify, g

categories_bp = Blueprint('categories', __name__)

@categories_bp.route("/api/categories", methods=['GET'])
def get_categories():
    """Возвращает список всех основных категорий."""
    query = "SELECT id, name, slug FROM categories ORDER BY name"
    categories = g.db.fetch_all(query)
    return jsonify(categories)

@categories_bp.route("/api/subcategories/<int:category_id>", methods=['GET'])
def get_subcategories(category_id: int):
    """Возвращает список подкатегорий для указанной основной категории."""
    query = "SELECT id, name, slug FROM subcategories WHERE category_id = %s ORDER BY name"
    subcategories = g.db.fetch_all(query, (category_id,))
    return jsonify(subcategories)