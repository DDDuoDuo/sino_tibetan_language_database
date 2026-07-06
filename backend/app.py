import os
import secrets
from flask import Flask, request, jsonify, make_response
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from dotenv import load_dotenv

load_dotenv()

from routes.auth import auth_bp
from routes.projects import projects_bp
from routes.vocab import vocab_bp
from routes.languages import languages_bp
from routes.translations import translations_bp

CSRF_COOKIE = "csrf_token"
CSRF_HEADER = "X-CSRF-Token"

def create_app():
    app = Flask(__name__)

    allowed_origins = os.getenv("CORS_ORIGINS", "").split(",")
    allowed_origins = [o.strip() for o in allowed_origins if o.strip()]
    CORS(app,
         origins=allowed_origins or ["*"],
         supports_credentials=True,
         expose_headers=[CSRF_HEADER])

    secret = os.getenv("SECRET_KEY")
    if not secret:
        raise RuntimeError("SECRET_KEY 环境变量未设置，请在 .env 中配置")
    app.secret_key = secret

    # --- Rate limiter (issue 3) ---
    limiter = Limiter(
        get_remote_address,
        app=app,
        default_limits=[],
        storage_uri="memory://",
    )
    limiter.limit("10/minute")(auth_bp)

    # --- CSRF double-submit cookie (issue 2) ---
    @app.after_request
    def set_csrf_cookie(response):
        if CSRF_COOKIE not in request.cookies:
            token = secrets.token_hex(32)
            response.set_cookie(
                CSRF_COOKIE, token,
                httponly=False,  # JS must read it
                samesite="Lax",
                secure=False,   # set True for HTTPS
                path="/",
            )
        return response

    @app.before_request
    def check_csrf():
        if request.method in ("GET", "HEAD", "OPTIONS"):
            return
        cookie_token = request.cookies.get(CSRF_COOKIE)
        header_token = request.headers.get(CSRF_HEADER)
        if not cookie_token or not header_token or cookie_token != header_token:
            return make_response(
                jsonify({"success": False, "message": "CSRF 验证失败，请刷新页面重试"}), 403
            )

    app.register_blueprint(auth_bp, url_prefix="/api")
    app.register_blueprint(projects_bp, url_prefix="/api")
    app.register_blueprint(vocab_bp, url_prefix="/api")
    app.register_blueprint(languages_bp, url_prefix="/api")
    app.register_blueprint(translations_bp, url_prefix="/api")

    @app.get("/api/health")
    def health():
        return {"status": "ok"}

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, port=3000)
