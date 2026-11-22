from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models.products import Product, Inventory
from app.models.cart import Cart, CartItem
from app.routes.auth import success, fail

cart_bp = Blueprint('cart', __name__, url_prefix='/api/v1/cart')

def get_my_cart(user_id):
    cart = Cart.query.filter_by(user_id=user_id).first()
    if cart is None:
        cart = Cart(user_id=user_id)
        db.session.add(cart)
        db.session.commit()
    return cart

def stock_of(product_id):
    stock = Inventory.query.filter_by(product_id=product_id).first()
    return stock.available_qty if stock else 0

def cart_view(cart):
    items = []
    total = 0
    for ci in CartItem.query.filter_by(cart_id=cart.id).all():
        p = Product.query.get(ci.product_id)
        total = total + p.price * ci.quantity
        items.append({"id": ci.id, "product_id": p.id, "name": p.name, "unit_price": p.price,
                      "quantity": ci.quantity, "line_total": p.price * ci.quantity})
    return {"items": items, "total": total}

@cart_bp.route('/items', methods=['POST'])
@jwt_required()
def add_item():
    data = request.get_json(silent=True) or {}
    product_id = data.get('product_id')
    quantity = data.get('quantity')
    if type(product_id) is not int or type(quantity) is not int or quantity <= 0:
        return fail('VALIDATION_ERROR', 'product_id and a positive quantity are required', 422)
    if not Product.query.filter_by(id=product_id, active=True).first():
        return fail('NOT_FOUND', 'product not found', 404)

    cart = get_my_cart(int(get_jwt_identity()))
    item = CartItem.query.filter_by(cart_id=cart.id, product_id=product_id).first()
    if item:
        quantity = quantity + item.quantity
    if quantity > stock_of(product_id):
        return fail('INSUFFICIENT_STOCK', 'only ' + str(stock_of(product_id)) + ' in stock', 409)

    if item:
        item.quantity = quantity
    else:
        db.session.add(CartItem(cart_id=cart.id, product_id=product_id, quantity=quantity))
    db.session.commit()
    return success(cart_view(cart), 201)

@cart_bp.route('/items/<int:item_id>', methods=['PATCH'])
@jwt_required()
def change_quantity(item_id):
    quantity = (request.get_json(silent=True) or {}).get('quantity')
    if type(quantity) is not int or quantity <= 0:
        return fail('VALIDATION_ERROR', 'quantity must be a positive whole number', 422)

    cart = get_my_cart(int(get_jwt_identity()))
    item = CartItem.query.filter_by(id=item_id, cart_id=cart.id).first()
    if item is None:
        return fail('NOT_FOUND', 'cart item not found', 404)
    if quantity > stock_of(item.product_id):
        return fail('INSUFFICIENT_STOCK', 'only ' + str(stock_of(item.product_id)) + ' in stock', 409)

    item.quantity = quantity
    db.session.commit()
    return success(cart_view(cart))