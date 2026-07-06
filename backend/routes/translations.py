import json
import os
from flask import Blueprint, jsonify, request
from routes.auth import require_admin

translations_bp = Blueprint("translations", __name__)

LOCALES_DIR = os.getenv(
    "LOCALES_DIR",
    os.path.join(os.path.dirname(os.path.dirname(__file__)), "locales")
)
ALLOWED_LOCALES = {
    "zh-cn": "zh-cn.json",
    "en-us": "en-us.json",
}

def _locale_path(locale: str):
    filename = ALLOWED_LOCALES.get((locale or "").lower())
    if not filename:
        return None
    return os.path.join(LOCALES_DIR, filename)

@translations_bp.get("/translations/<locale>")
def get_translation(locale):
    path = _locale_path(locale)
    if not path or not os.path.exists(path):
        return jsonify({"success": False, "message": "Locale not found"}), 404

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return jsonify({"success": True, "locale": locale.lower(), "data": data})

@translations_bp.put("/translations/<locale>")
@require_admin
def update_translation(locale):
    path = _locale_path(locale)
    if not path:
        return jsonify({"success": False, "message": "Invalid locale"}), 400

    data = request.get_json()
    if not isinstance(data, dict):
        return jsonify({"success": False, "message": "JSON object required"}), 400

    os.makedirs(LOCALES_DIR, exist_ok=True)
    tmp_path = path + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")
    os.replace(tmp_path, path)

    return jsonify({"success": True})
