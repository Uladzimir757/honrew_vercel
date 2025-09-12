# Файл: app/routers/complaints.py
from flask import Blueprint, request, g, jsonify, session

# Создаем Blueprint
complaints_bp = Blueprint('complaints', __name__)

@complaints_bp.route("/api/complaints", methods=['POST'])
def handle_complaint():
    # Проверяем, залогинен ли пользователь (берем из `g`)
    if not g.user:
        return jsonify({"status": "error", "message": "Authentication required"}), 401

    # Получаем данные из формы
    content_id = request.form.get('content_id', type=int)
    content_type = request.form.get('content_type')
    reason = request.form.get('reason')

    if not all([content_id, content_type, reason]):
        return jsonify({"status": "error", "message": "Missing required fields"}), 400

    query = """
        INSERT INTO complaints (content_id, content_type, reason, user_id, status)
        VALUES (?1, ?2, ?3, ?4, 'pending')
    """
    params = (content_id, content_type, reason, g.user["id"])

    try:
        # Доступ к базе данных через g.db
        g.db.execute(query, params)
        # Возвращаем JSON через jsonify
        return jsonify({"status": "success", "message": g.tr.get("complaint_success", "Your complaint has been submitted.")})
    except Exception as e:
        print(f"Ошибка при сохранении жалобы: {e}")
        return jsonify({"status": "error", "message": g.tr.get("complaint_error_generic", "An error occurred.")}), 500