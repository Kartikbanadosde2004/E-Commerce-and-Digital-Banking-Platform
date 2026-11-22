import uuid
from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token
from app import db
from app.models.user import User

auth_bp = Blueprint('auth', __name__, url_prefix='/api/v1/auth')

def success (data, status=200):
    return jsonify({"data": data, "request_id": uuid.uuid4().hex[:12]}), status

def fail(code, message, status):
    return jsonify({"error": {"code": code, "message": message},
                    "request_id": uuid.uuid4().hex[:12]}), status

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json(silent=True) or {}
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')

    if not name or not email or not password:
        return fail('VALIDATION_ERROR', 'name, email and password are required', 400)
    if type(email) is not str or type(password) is not str:
        return fail('VALIDATION_ERROR', 'email and password must be text', 422)
    if '@' not in email or '.' not in email:
        return fail('VALIDATION_ERROR', 'email is not valid', 422)
    if len(password) < 8:
        return fail('VALIDATION_ERROR', 'password must be at least 8 characters', 422)

    email = email.strip().lower()
    if User.query.filter_by(email=email).first():
        return fail('EMAIL_EXISTS', 'this email is already registered', 409)

    user = User(name=name.strip(),
                email=email,
                password_hash=generate_password_hash(password),
                role='customer')
    db.session.add(user)
    db.session.commit()

    return success({"id": user.id, "name": user.name,
                    "email": user.email, "role": user.role}, 201)

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json(silent=True) or {}
    email = data.get('email')
    password = data.get('password')

    if  not email or not password:
        return fail('VALIDATION_ERROR', 'email and password are required', 400)
    if type(email) is not str or type(password) is not str:
        return fail('VALIDATION_ERROR', 'email and password must be text', 422)
    user = User.query.filter_by(email=email.strip().lower()).first()
    if user is None or not check_password_hash(user.password_hash, password):
        return fail('INVALID_CREDENTIALS', 'email or password is wrong', 401)

    token = create_access_token(identity=str(user.id), additional_claims={"role": user.role})
    return success({"access_token": token, "role": user.role})