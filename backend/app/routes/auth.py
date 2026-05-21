"""Authentication routes."""
import logging
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from app.extensions import db, limiter
from app.models import User
from app.utils.validators import validate_email, validate_password
from app.utils.auth_helpers import hash_password, check_password, get_current_user

logger = logging.getLogger(__name__)

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


def _ensure_tables():
    """Create tables if missing (safe for first run)."""
    try:
        db.create_all()
    except Exception as e:
        logger.warning("create_all: %s", e)


@auth_bp.route("/register", methods=["POST"])
@limiter.limit("30 per minute")
def register():
    try:
        _ensure_tables()

        if not request.is_json:
            return jsonify({"error": "Content-Type must be application/json"}), 400

        data = request.get_json(silent=True) or {}
        username = (data.get("username") or "").strip()
        email = (data.get("email") or "").strip().lower()
        password = data.get("password") or ""
        full_name = (data.get("full_name") or username).strip()
        preferred_language = data.get("preferred_language") or "en"

        if not username or len(username) < 3:
            return jsonify({"error": "Username must be at least 3 characters"}), 400
        if not validate_email(email):
            return jsonify({"error": "Invalid email address"}), 400
        valid, msg = validate_password(password)
        if not valid:
            return jsonify({"error": msg}), 400

        if User.query.filter(
            (User.email == email) | (User.username == username)
        ).first():
            return jsonify({"error": "User already exists with this email or username"}), 409

        password_hash = hash_password(password)
        user = User(
            username=username,
            email=email,
            password_hash=password_hash,
            full_name=full_name,
            preferred_language=preferred_language,
            role="user",
            is_active=True,
        )

        db.session.add(user)
        db.session.commit()

        access = create_access_token(identity=str(user.id))
        refresh = create_refresh_token(identity=str(user.id))

        return jsonify({
            "message": "Registration successful",
            "access_token": access,
            "refresh_token": refresh,
            "user": user.to_dict(),
        }), 201

    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "User already exists with this email or username"}), 409
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.exception("Registration database error: %s", e)
        err = str(e).lower()
        if "locked" in err:
            return jsonify({
                "error": "Database busy. Stop duplicate backend servers and try again."
            }), 500
        if "sqlite" in current_app.config.get("SQLALCHEMY_DATABASE_URI", ""):
            return jsonify({
                "error": "Database error. Restart backend: python run.py"
            }), 500
        return jsonify({
            "error": "Database connection failed. Set USE_SQLITE=true in backend/.env"
        }), 500
    except Exception as e:
        db.session.rollback()
        logger.exception("Registration failed: %s", e)
        return jsonify({"error": f"Registration failed: {str(e)}"}), 500


@auth_bp.route("/login", methods=["POST"])
@limiter.limit("30 per minute")
def login():
    try:
        _ensure_tables()
        data = request.get_json(silent=True) or {}
        email = (data.get("email") or "").strip().lower()
        password = data.get("password") or ""

        user = User.query.filter_by(email=email).first()
        if not user or not check_password(password, user.password_hash):
            return jsonify({"error": "Invalid email or password"}), 401
        if not user.is_active:
            return jsonify({"error": "Account is deactivated"}), 403

        access = create_access_token(identity=str(user.id))
        refresh = create_refresh_token(identity=str(user.id))

        return jsonify({
            "message": "Login successful",
            "access_token": access,
            "refresh_token": refresh,
            "user": user.to_dict(),
        })
    except Exception as e:
        logger.exception("Login failed: %s", e)
        return jsonify({"error": f"Login failed: {str(e)}"}), 500


@auth_bp.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():
    user_id = get_jwt_identity()
    access = create_access_token(identity=user_id)
    return jsonify({"access_token": access})


@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def me():
    user = get_current_user()
    if not user:
        return jsonify({"error": "User not found"}), 404
    return jsonify({"user": user.to_dict()})


@auth_bp.route("/profile", methods=["PUT"])
@jwt_required()
def update_profile():
    user = get_current_user()
    data = request.get_json() or {}

    if "full_name" in data:
        user.full_name = data["full_name"]
    if "preferred_language" in data:
        user.preferred_language = data["preferred_language"]
    if "avatar_url" in data:
        user.avatar_url = data["avatar_url"]

    db.session.commit()
    return jsonify({"message": "Profile updated", "user": user.to_dict()})


@auth_bp.route("/change-password", methods=["PUT"])
@jwt_required()
def change_password():
    user = get_current_user()
    data = request.get_json() or {}
    current = data.get("current_password", "")
    new_pass = data.get("new_password", "")

    if not check_password(current, user.password_hash):
        return jsonify({"error": "Current password is incorrect"}), 400
    valid, msg = validate_password(new_pass)
    if not valid:
        return jsonify({"error": msg}), 400

    user.password_hash = hash_password(new_pass)
    db.session.commit()
    return jsonify({"message": "Password changed successfully"})
