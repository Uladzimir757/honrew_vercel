# Файл: app/routers/complaints.py
from flask import Blueprint, request, g, jsonify, session

complaints_bp = Blueprint('complaints', __name__)

@complaints_bp.route("/api/complaints", methods=['POST'])
def handle_complaint():
    if not g.user:
        return jsonify({"status": "error", "message": "Authentication required"}), 401

    content_id = request.form.get('content_id', type=int)
    content_type = request.form.get('content_type')
    reason = request.form.get('reason')

    if not all([content_id, content_type, reason]):
        return jsonify({"status": "error", "message": "Missing required fields"}), 400

    query = """
        INSERT INTO complaints (content_id, content_type, reason, user_id, status)
        VALUES (%s, %s, %s, %s, 'pending')
    """
    params = (content_id, content_type, reason, g.user["id"])

    try:
        g.db.execute(query, params)
        return jsonify({"status": "success", "message": g.tr.get("complaint_success", "Your complaint has been submitted.")})
    except Exception as e:
        print(f"Ошибка при сохранении жалобы: {e}")
        return jsonify({"status": "error", "message": g.tr.get("complaint_error_generic", "An error occurred.")}), 500