from flask import Blueprint, request, jsonify
from models.vocab import replace_project_vocab, get_project_vocab
from models.projects import get_project
from routes.auth import require_auth

vocab_bp = Blueprint("vocab", __name__)

@vocab_bp.get("/projects/<project_id>/vocab")
def list_vocab(project_id):
    items = get_project_vocab(project_id)
    return jsonify(items)

@vocab_bp.post("/projects/<project_id>/vocab")
@require_auth
def save_vocab(project_id):
    proj = get_project(project_id)
    if not proj:
        return jsonify({"success": False, "message": "项目不存在"}), 404
    if proj.get("author_id") != request.current_user_id:
        return jsonify({"success": False, "message": "无权修改此项目"}), 403
    data = request.get_json()
    replace_project_vocab(project_id, data or [])
    return jsonify({"success": True})
