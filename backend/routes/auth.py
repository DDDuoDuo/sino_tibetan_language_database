from functools import wraps
from flask import Blueprint, request, jsonify, make_response, current_app
import secrets
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from models.users import (
    create_user, get_user_by_email, get_user_by_id,
    update_user_profile, list_contributors,
    verify_password, hash_password, update_user_password_hash,
    update_user_account_type,
)

auth_bp = Blueprint("auth", __name__)

COOKIE_NAME = "lan_auth"
COOKIE_MAX_AGE = 60 * 60 * 24 * 14  # 14天

def _serializer():
    secret = current_app.secret_key
    if not secret:
        raise RuntimeError("Flask secret_key 未设置，无法签名 cookie")
    return URLSafeTimedSerializer(secret, salt="lan-project-auth")

def _make_token(user_id: str) -> str:
    return _serializer().dumps({"uid": user_id, "r": secrets.token_hex(8)})

def _read_token(token: str) -> str | None:
    try:
        data = _serializer().loads(token, max_age=COOKIE_MAX_AGE)
        return data.get("uid")
    except (BadSignature, SignatureExpired):
        return None

def _set_auth_cookie(resp, user_id: str):
    token = _make_token(user_id)
    resp.set_cookie(
        COOKIE_NAME,
        token,
        max_age=COOKIE_MAX_AGE,
        httponly=True,
        samesite="Lax",
        secure=False,  # 如果是 HTTPS，改成 True
        path="/",
    )
    return resp

def _clear_auth_cookie(resp):
    resp.delete_cookie(COOKIE_NAME, path="/")
    return resp

def require_auth(f):
    """Decorator: rejects the request with 401 if no valid auth cookie."""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.cookies.get(COOKIE_NAME)
        if not token:
            return jsonify({"success": False, "message": "未登录"}), 401
        user_id = _read_token(token)
        if not user_id:
            return jsonify({"success": False, "message": "登录已过期"}), 401
        request.current_user_id = user_id
        return f(*args, **kwargs)
    return decorated

def require_admin(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.cookies.get(COOKIE_NAME)
        if not token:
            return jsonify({"success": False, "message": "未登录"}), 401
        user_id = _read_token(token)
        if not user_id:
            return jsonify({"success": False, "message": "登录已过期"}), 401
        user = get_user_by_id(user_id)
        if not user:
            return jsonify({"success": False, "message": "用户不存在"}), 401
        if user.get("account_type") != "admin":
            return jsonify({"success": False, "message": "需要管理员权限"}), 403
        request.current_user_id = user_id
        request.current_user = user
        return f(*args, **kwargs)
    return decorated

def serialize_user(user_row):
    if not user_row:
        return None
    return {
        "id": user_row["id"],
        "email": user_row["email"],
        "username": user_row["username"],
        "title": user_row.get("title"),
        "workplace": user_row.get("workplace"),
        "accountType": user_row.get("account_type") or "user",
        "created_at": (
            user_row["created_at"].isoformat()
            if user_row.get("created_at") is not None
            else None
        ),
    }

@auth_bp.post("/register")
def register():
    data = request.get_json() or {}

    email = data.get("email", "").strip()
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()
    title = data.get("title") or "教授"
    workplace = data.get("workplace") or ""

    if not email or not username or not password:
        return jsonify({"success": False, "message": "email/用户名/密码必填"}), 400

    existing = get_user_by_email(email)
    if existing:
        return jsonify({"success": False, "message": "邮箱已注册"}), 400

    created = create_user(email, username, password, title, workplace)

    db_user = get_user_by_id(created["id"])
    resp = make_response(jsonify({
        "success": True,
        "user": serialize_user(db_user),
    }))
    return _set_auth_cookie(resp, db_user["id"])

@auth_bp.post("/login")
def login():
    data = request.get_json() or {}
    email = data.get("email", "").strip()
    password = data.get("password", "").strip()

    if not email or not password:
        return jsonify({"success": False, "message": "email/密码必填"}), 400

    user = get_user_by_email(email)
    if not user:
        return jsonify({"success": False, "message": "用户不存在"}), 400

    if not verify_password(password, user["password"]):
        return jsonify({"success": False, "message": "密码错误"}), 400

    # Rehash legacy plaintext passwords to bcrypt on successful login
    if not user["password"].startswith("$2b$"):
        update_user_password_hash(user["id"], hash_password(password))

    resp = make_response(jsonify({
        "success": True,
        "user": serialize_user(user),
    }))
    return _set_auth_cookie(resp, user["id"])

@auth_bp.post("/profile")
@require_auth
def update_profile():
    data = request.get_json() or {}

    user_id = request.current_user_id
    username = (data.get("username") or "").strip()
    title = data.get("title") or "教授"
    workplace = data.get("workplace") or ""

    if not user_id:
        return jsonify({"success": False, "message": "缺少用户ID"}), 400
    if not username:
        return jsonify({"success": False, "message": "用户名不能为空"}), 400

    updated = update_user_profile(user_id, username, title, workplace)
    if not updated:
        return jsonify({"success": False, "message": "用户不存在"}), 404

    return jsonify({"success": True, "user": serialize_user(updated)})

@auth_bp.get("/me")
def me():
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        return jsonify({"success": False, "message": "未登录"}), 401

    user_id = _read_token(token)
    if not user_id:
        return jsonify({"success": False, "message": "登录已过期"}), 401

    user = get_user_by_id(user_id)
    if not user:
        return jsonify({"success": False, "message": "用户不存在"}), 401

    return jsonify({"success": True, "user": serialize_user(user)})

@auth_bp.get("/contributors")
def get_contributors():
    page = request.args.get("page", "1")
    per_page = request.args.get("perPage", "10")

    try:
        page = max(1, int(page))
    except (ValueError, TypeError):
        page = 1

    try:
        per_page = int(per_page)
        per_page = 10 if per_page <= 0 else min(per_page, 50)
    except (ValueError, TypeError):
        per_page = 10

    rows, total = list_contributors(page=page, per_page=per_page)

    def dt(v):
        if not v:
            return None
        return v.strftime("%Y-%m-%d %H:%M:%S") if hasattr(v, "strftime") else str(v)

    out = []
    for r in rows:
        out.append({
            "id": r.get("id"),
            "username": r.get("username"),
            "workplace": r.get("workplace"),
            "accountType": r.get("account_type") or "user",
            "createdAt": dt(r.get("created_at")),
            "projectCount": int(r.get("project_count") or 0),
            "vocabCount": int(r.get("vocab_count") or 0),
        })

    return jsonify({
        "success": True,
        "contributors": out,
        "page": page,
        "perPage": per_page,
        "total": total
    })

@auth_bp.post("/contributors/<user_id>/account-type")
@require_admin
def set_contributor_account_type(user_id):
    data = request.get_json() or {}
    account_type = (data.get("accountType") or "").strip()
    if account_type not in ("user", "admin"):
        return jsonify({"success": False, "message": "无效账户类型"}), 400
    if user_id == request.current_user_id and account_type != "admin":
        return jsonify({"success": False, "message": "不能取消自己的管理员权限"}), 400

    updated = update_user_account_type(user_id, account_type)
    if not updated:
        return jsonify({"success": False, "message": "用户不存在"}), 404
    return jsonify({"success": True, "user": serialize_user(updated)})

@auth_bp.post("/logout")
def logout():
    resp = make_response(jsonify({"success": True}))
    return _clear_auth_cookie(resp)
