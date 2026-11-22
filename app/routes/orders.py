from flask import Blueprint
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from app import db
from app.models.products import Product, Inventory
from app.models.cart import Cart, CartItem
from app.models.orders import Order, OrderItem
from app.routes.auth import success, fail
from app.models.payment import Payment
from app.services.refund import refunded_so_far, make_refund

orders_bp = Blueprint('orders', __name__, url_prefix='/api/v1/orders')

def order_view(order):
    items = []
    for i in OrderItem.query.filter_by(order_id=order.id).all():
        items.append({"name": i.product_name, "unit_price": i.unit_price, "quantity": i.quantity})
    return {"order_id": order.id, "status": order.status,
            "total_amount": order.total_amount, "items": items}

@orders_bp.route('/checkout', methods=['POST'])
@jwt_required()
def checkout():
    user_id = int(get_jwt_identity())
    cart = Cart.query.filter_by(user_id=user_id).first()
    cart_items = CartItem.query.filter_by(cart_id=cart.id).all() if cart else []
    if not cart_items:
        return fail('EMPTY_CART', 'your cart is empty', 422)

    pending = Order.query.filter_by(user_id=user_id, status='PENDING').first()
    if pending:
        return fail('ORDER_PENDING', 'you already have an unpaid order (id ' + str(pending.id) +
          '). Pay or cancel it first', 409)

    order = Order(user_id=user_id, status='PENDING', total_amount=0)
    db.session.add(order)
    db.session.flush()

    total = 0
    for ci in cart_items:
        product = Product.query.filter_by(id=ci.product_id, active=True).first()
        stock = Inventory.query.filter_by(product_id=ci.product_id).first()
        if product is None or stock is None or stock.available_qty < ci.quantity:
            db.session.rollback()
            return fail('INSUFFICIENT_STOCK', 'product is not available ', 409)

        changed = Inventory.query.filter_by(product_id=ci.product_id, version=stock.version).update(
            {"available_qty": stock.available_qty - ci.quantity,
             "reserved_qty": stock.reserved_qty + ci.quantity,
             "version": stock.version + 1})
        if changed == 0:
            db.session.rollback()
            return fail('STOCK_CHANGED', 'stock just changed,try again', 409)

        total = total + product.price * ci.quantity
        db.session.add(OrderItem(order_id=order.id, product_id=product.id, product_name=product.name,
                                 unit_price=product.price, quantity=ci.quantity))

    order.total_amount = total
    db.session.commit()
    return success(order_view(order), 201)

@orders_bp.route('/<int:order_id>', methods=['GET'])
@jwt_required()
def view_order(order_id):
    order = Order.query.get(order_id)
    if order is None:
        return fail('NOT_FOUND', 'order not found', 404)
    if order.user_id != int(get_jwt_identity()) and get_jwt().get('role') != 'admin':
        return fail('FORBIDDEN', 'this is not your order', 403)
    return success(order_view(order))

@orders_bp.route('/<int:order_id>/cancel', methods=['POST'])
@jwt_required()
def cancel_order(order_id):
    order = Order.query.get(order_id)
    if order is None:
        return fail('NOT_FOUND', 'order not found', 404)
    if order.user_id != int(get_jwt_identity()) and get_jwt().get('role') != 'admin':
        return fail('FORBIDDEN', 'this is not your order', 403)
    if order.status not in ('PENDING', 'CONFIRMED'):
        return fail('CANNOT_CANCEL', 'only a PENDING or CONFIRMED order can be cancelled', 409)

    for item in OrderItem.query.filter_by(order_id=order.id).all():
        stock = Inventory.query.filter_by(product_id=item.product_id).first()
        stock.available_qty = stock.available_qty + item.quantity
        if order.status == 'PENDING':
            stock.reserved_qty = stock.reserved_qty - item.quantity
        stock.version = stock.version + 1

    if order.status == 'CONFIRMED':
        payment = Payment.query.filter_by(order_id=order.id, status='SUCCESS').first()
        left = payment.amount - refunded_so_far(payment.id)
        if left > 0 and not make_refund(payment, left, 'order cancelled'):
            db.session.rollback()
            return fail('WALLET_BUSY', 'wallet changed, please try again', 409)

    order.status = 'CANCELLED'
    db.session.commit()
    return success(order_view(order))