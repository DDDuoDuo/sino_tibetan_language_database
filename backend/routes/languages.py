from flask import Blueprint, request, jsonify
from models.languages import replace_project_languages, get_project_languages
from models.projects import get_project
from routes.auth import require_auth

languages_bp = Blueprint("languages", __name__)

@languages_bp.get("/projects/<project_id>/languages")
def list_languages(project_id):
    langs = get_project_languages(project_id)
    return jsonify(langs)

@languages_bp.post("/projects/<project_id>/languages")
@require_auth
def save_languages(project_id):
    proj = get_project(project_id)
    if not proj:
        return jsonify({"success": False, "message": "项目不存在"}), 404
    if proj.get("author_id") != request.current_user_id:
        return jsonify({"success": False, "message": "无权修改此项目"}), 403
    data = request.get_json()
    replace_project_languages(project_id, data or [])
    return jsonify({"success": True})
