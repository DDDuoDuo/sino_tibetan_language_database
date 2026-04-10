from flask import Blueprint, request, jsonify, send_file
from datetime import datetime, date
from models.projects import (
    list_projects_by_author,
    list_public_projects,
    get_project,
    upsert_project,
    set_project_public,
    delete_project,
)
from models.languages import replace_project_languages, get_project_languages, get_languages_for_projects
from models.vocab import replace_project_vocab, get_project_vocab
from models.treefiles import (
    upsert_project_tree_file,
    delete_project_tree_file,
    get_project_tree_file,
    get_file_path,
)
from routes.auth import require_auth
import json

projects_bp = Blueprint("projects", __name__)

def dt(v):
    if not v:
        return None
    if isinstance(v, str):
        return v
    if isinstance(v, (datetime, date)):
        return v.strftime("%Y-%m-%d %H:%M:%S")
    return str(v)

@projects_bp.get("/projects")
def list_projects():
    author_id = request.args.get("authorId")

    if author_id:
        rows = list_projects_by_author(author_id)
    else:
        rows = list_public_projects()

    project_ids = [p["id"] for p in rows]
    langs_by_project = get_languages_for_projects(project_ids)

    out = []
    for p in rows:
        langs = langs_by_project.get(p["id"], [])
        language_coords = [
            {
                "name": row["name"],
                "lng": row["longitude"],
                "lat": row["latitude"],
                "sortOrder": row.get("sort_order"),
            }
            for row in langs
        ]
        project_time_range = {
            "upper": p.get("time_upper"),
            "upperEra": p.get("time_upper_era") or "BC",
            "lower": p.get("time_lower"),
            "lowerEra": p.get("time_lower_era") or "AD",
        }

        out.append({
            "id": p["id"],
            "projectName": p.get("project_name"),
            "projectDesc": p.get("project_desc"),
            "projectType": str(p["project_type"]) if p.get("project_type") is not None else None,
            "references": p.get("references_text"),
            "author_username": p.get("author_username"),
            "author": p.get("author_username"),
            "authorId": p.get("author_id"),
            "isPublic": bool(p.get("is_public", 0)),
            "numVocab": p.get("num_vocab", 0),
            "hasTreeFile": bool(p.get("has_treefile", 0)),
            "createdAt": dt(p.get("created_at")),
            "updatedAt": dt(p.get("updated_at")),
            "languageCoords": language_coords,
            "projectTimeRange": project_time_range,
        })

    return jsonify({
        "success": True,
        "projects": out
    })

@projects_bp.get("/projects/<project_id>")
def get_project_detail(project_id):
    from flask import jsonify
    import json

    proj = get_project(project_id)
    if not proj:
        return jsonify({"success": False, "message": "project not found"}), 404

    langs = get_project_languages(project_id)
    vocab_rows = get_project_vocab(project_id)
    # include_tree = request.args.get("includeTree") == "1"
    # if include_tree:
    #     tree = get_project_tree_file(project_id) 
    # else:
    #     tree = None

    language_names = [row["name"] for row in langs]
    language_coords = [
        {
            "name": row["name"],
            "lng": row["longitude"],
            "lat": row["latitude"],
            "sortOrder": row.get("sort_order"),
        }
        for row in langs
    ]

    def convert_vocab(row):
        word_data = json.loads(row["word_data_json"]) if row.get("word_data_json") else None
        comp_data = json.loads(row["comp_data_json"]) if row.get("comp_data_json") else None

        time_info = None
        if row.get("time_event_type"):
            time_info = {
                "eventType": row["time_event_type"],
                "lower": row["time_lower"],
                "lowerEra": row["time_lower_era"],
                "upper": row["time_upper"],
                "upperEra": row["time_upper_era"],
            }

        return {
            "id": row["id"],
            "category": row["category"],
            "word": row["word"],
            "wordData": word_data,
            "compData": comp_data,
            "level": row["level"],
            "fullMatch": bool(row["full_match"]),
            "partialMatch": bool(row["partial_match"]),
            "relaxedMatch": bool(row["relaxed_match"]),
            "explainable": None if row["explainable"] is None else bool(row["explainable"]),
            "cognate": None if row["cognate"] is None else bool(row["cognate"]),
            "originType": row["origin_type"],
            "borrowSource": row["borrow_source"],
            "borrowSourceOther": row["borrow_source_other"],
            "borrowChange": row["borrow_change"],
            "borrowChangeOther": row["borrow_change_other"],
            "timeInfo": time_info,
            "evidence": row["evidence"],
            "recordedAt": dt(row.get("recorded_at")),
            "author": row.get("author"),
        }

    vocab_list = [convert_vocab(r) for r in vocab_rows]

    # tree_file = None
    # if tree:
    #     content = tree["content"]

    #     if isinstance(content, (bytes, bytearray)):
    #         try:
    #             content = content.decode("utf-8")
    #         except UnicodeDecodeError:
    #             content = base64.b64encode(content).decode("ascii")

    #     tree_file = {
    #         "name": tree["file_name"],
    #         "type": tree["mime_type"],
    #         "content": content,
    #     }

    project_time_range = {
        "upper": proj.get("time_upper"),
        "upperEra": proj.get("time_upper_era"),
        "lower": proj.get("time_lower"),
        "lowerEra": proj.get("time_lower_era"),
    }

    frontend_project = {
        "id": proj["id"],
        "projectName": proj["project_name"],
        "projectDesc": proj["project_desc"],
        "references": proj["references_text"],
        "projectType": str(proj["project_type"]) if proj.get("project_type") is not None else None,
        "languages": language_names,
        "languageCoords": language_coords,
        "createdAt": proj["created_at"].strftime("%Y-%m-%d %H:%M:%S") if proj.get("created_at") else None,
        "projectTimeRange": project_time_range,
        # "treeFile": None,
        "vocabList": vocab_list,
        "authorId": proj.get("author_id"),
        "isPublic": bool(proj.get("is_public", 0)),
        "lastPublicUpdate": dt(proj.get("updated_at")),
        "hasTreeFile": bool(proj.get("has_treefile", 0)),
    }

    return jsonify({"success": True, "project": frontend_project})

@projects_bp.get("/projects/<project_id>/treefile")
def get_treefile_info(project_id):
    """Return metadata about the treefile (no file content)."""
    tree = get_project_tree_file(project_id)
    if not tree:
        return jsonify({"success": True, "treeFile": None})

    return jsonify({
        "success": True,
        "treeFile": {
            "name": tree["file_name"],
            "type": tree["mime_type"] or "application/octet-stream",
            "updatedAt": tree["updated_at"].strftime("%Y-%m-%d %H:%M:%S") if tree.get("updated_at") else None,
        }
    })

@projects_bp.get("/projects/<project_id>/treefile/download")
def download_treefile(project_id):
    """Serve the actual treefile binary from disk."""
    tree = get_project_tree_file(project_id)
    if not tree:
        return jsonify({"success": False, "message": "未找到树图文件"}), 404

    path = get_file_path(tree.get("stored_name"))
    if not path:
        return jsonify({"success": False, "message": "文件不存在"}), 404

    return send_file(
        path,
        mimetype=tree["mime_type"] or "application/octet-stream",
        download_name=tree["file_name"],
    )

@projects_bp.post("/projects/<project_id>/treefile")
@require_auth
def upload_treefile(project_id):
    """Upload a treefile via multipart/form-data."""
    _, err = _check_project_owner(project_id)
    if err:
        return err

    if "file" not in request.files:
        return jsonify({"success": False, "message": "未上传文件"}), 400

    f = request.files["file"]
    if not f.filename:
        return jsonify({"success": False, "message": "文件名为空"}), 400

    result = upsert_project_tree_file(project_id, f)
    return jsonify({"success": True, "treeFile": result})

@projects_bp.delete("/projects/<project_id>/treefile")
@require_auth
def remove_treefile(project_id):
    """Delete the treefile for a project."""
    _, err = _check_project_owner(project_id)
    if err:
        return err
    delete_project_tree_file(project_id)
    return jsonify({"success": True})

@projects_bp.post("/projects")
@require_auth
def save_project():
    data = request.get_json()

    if not data.get("id"):
        return jsonify({"success": False, "message": "id 必填"}), 400

    # Enforce ownership: authorId must match the logged-in user
    data["authorId"] = request.current_user_id

    # If updating, verify the caller owns the project
    existing = get_project(data["id"])
    if existing and existing.get("author_id") != request.current_user_id:
        return jsonify({"success": False, "message": "无权修改此项目"}), 403

    upsert_project(data)

    raw_langs = data.get("languageCoords") or data.get("languages") or []
    norm_langs = []

    for idx, lang in enumerate(raw_langs):
        if isinstance(lang, str):
            norm_langs.append({
                "name": lang,
                "lng": None,
                "lat": None,
                "sortOrder": idx,
            })
        elif isinstance(lang, dict):
            norm_langs.append({
                "name": lang.get("name"),
                "lng": lang.get("lng"),
                "lat": lang.get("lat"),
                "sortOrder": lang.get("sortOrder", idx),
            })

    replace_project_languages(data["id"], norm_langs)
    replace_project_vocab(data["id"], data.get("vocabList") or [])

    saved = get_project(data["id"])

    return jsonify({
        "success": True,
        "project": {
            "id": saved["id"],
            "projectName": saved.get("project_name"),
            "projectDesc": saved.get("project_desc"),
            "references": saved.get("references_text"),
            "projectType": str(saved["project_type"]) if saved.get("project_type") is not None else None,
            "authorId": saved.get("author_id"),
            "isPublic": bool(saved.get("is_public", 0)),
            "numVocab": saved.get("num_vocab", 0),
            "hasTreeFile": bool(saved.get("has_treefile", 0)),
            "createdAt": dt(saved.get("created_at")),
            "updatedAt": dt(saved.get("updated_at")),
        }
    })

def _check_project_owner(project_id):
    """Return (project, error_response). If error_response is not None, return it."""
    proj = get_project(project_id)
    if not proj:
        return None, (jsonify({"success": False, "message": "项目不存在"}), 404)
    if proj.get("author_id") != request.current_user_id:
        return None, (jsonify({"success": False, "message": "无权操作此项目"}), 403)
    return proj, None

@projects_bp.post("/projects/<project_id>/publish")
@require_auth
def publish_project(project_id):
    _, err = _check_project_owner(project_id)
    if err:
        return err
    set_project_public(project_id, True)
    return jsonify({"success": True})

@projects_bp.post("/projects/<project_id>/unpublish")
@require_auth
def unpublish_project(project_id):
    _, err = _check_project_owner(project_id)
    if err:
        return err
    set_project_public(project_id, False)
    return jsonify({"success": True})

@projects_bp.delete("/projects/<project_id>")
@require_auth
def remove_project(project_id):
    _, err = _check_project_owner(project_id)
    if err:
        return err
    delete_project(project_id)
    return jsonify({"success": True})
