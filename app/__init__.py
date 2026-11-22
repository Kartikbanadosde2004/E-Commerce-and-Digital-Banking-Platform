import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager

db = SQLAlchemy()
jwt = JWTManager()

def create_app(test_db=None):
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = test_db or os.environ.get('DATABASE_URL', 'sqlite:///shop.db')
    app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'change-this-secret-key-before-deploying-123456')

    db.init_app(app)
    jwt.init_app(app)

    from app.models.user import User
    from app.routes.auth import auth_bp
    from app.routes.cart import cart_bp
    from app.models.products import Product, Inventory
    from app.models.cart import Cart, CartItem
    from app.routes.products import products_bp
    from app.routes.orders import orders_bp
    from app.models import orders
    from app.routes.bank import bank_bp
    from app.models import wallet
    from app.models import refund

    from app.routes.payment import payments_bp
    from app.models import payment
    app.register_blueprint(payments_bp)
    app.register_blueprint(bank_bp)
    app.register_blueprint(orders_bp)
    app.register_blueprint(products_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(cart_bp)
    from app.routes.admin import admin_bp
    from app.models import audit
    app.register_blueprint(admin_bp)
    from app.routes.addresses import addresses_bp
    from app.models import address
    app.register_blueprint(addresses_bp)

    from app.routes.auth import success, fail

    @jwt.unauthorized_loader
    def token_missing(reason):
        return fail('UNAUTHORIZED', 'token is missing', 401)

    @jwt.invalid_token_loader
    def token_invalid(reason):
        return fail('INVALID_TOKEN', 'token is invalid', 401)

    @jwt.expired_token_loader
    def token_expired(header, payload):
        return fail('TOKEN_EXPIRED', 'token has expired', 401)

    from sqlalchemy.exc import IntegrityError

    @app.errorhandler(IntegrityError)
    def handle_conflict(e):
        db.session.rollback()
        return fail('CONFLICT', 'this data conflicts with existing data', 409)

    @app.route('/health')
    def health():
        return success({"status": "ok"})

    with app.app_context():
        db.create_all()
    return app