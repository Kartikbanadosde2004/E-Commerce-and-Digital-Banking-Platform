from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models.products import Inventory
from app.models.cart import Cart, CartItem
from app.models.orders import Order, OrderItem
from app.models.wallet import bank_accounts, wallets, ledgers_version
from app.models.payment import Payment
from app.routes.bank import get_my_wallet
from app.routes.auth import success, fail
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from app.services.refund import refunded_so_far, make_refund

payments_bp = Blueprint('payments', __name__)

def payment_view(p):
    return {"payment_id": p.id, "order_id": p.order_id, "amount": p.amount,
            "method": p.method, "status": p.status}

@payments_bp.route('/api/v1/payments', methods=['POST'])
@jwt_required()
def pay():
    user_id = int(get_jwt_identity())
    data = request.get_json(silent=True) or {}
    order_id = data.get('order_id')
    method = data.get('method')
    key = data.get('idempotency_key')

    if order_id is None or not method or not key:
        return fail('MISSING_FIELDS', 'order_id, method and idempotency_key are required', 400)
    if type(order_id) is not int or method not in ('wallet', 'bank') or type(key) is not str:
        return fail('VALIDATION_ERROR', 'order_id must be a number, method wallet or bank, key text', 422)

    old = Payment.query.filter_by(idempotency_key=key).first()
    if old:
        old_order = Order.query.get(old.order_id)
        if old_order.user_id != user_id:
            return fail('KEY_IN_USE', 'this idempotency key is already used', 409)
        result = payment_view(old)
        result["message"] = "same key: original result returned, no new debit"
        return success(result)

    order = Order.query.get(order_id)
    if order is None:
        return fail('NOT_FOUND', 'order not found', 404)
    if order.user_id != user_id:
        return fail('FORBIDDEN', 'this is not your order', 403)
    if order.status != 'PENDING':
        return fail('ORDER_NOT_PAYABLE', 'only a PENDING order can be paid', 409)

    amount = order.total_amount
    wallet = get_my_wallet(user_id)
    bank = bank_accounts.query.filter_by(user_id=user_id, status='ACTIVE').first()
    if method == 'wallet' and wallet.balance < amount:
        return fail('INSUFFICIENT_FUNDS', 'wallet balance is not enough', 422)
    if method == 'bank' and bank is None:
        return fail('NO_BANK_ACCOUNT', 'link a bank account first', 422)

    payment = Payment(order_id=order.id, amount=amount, method=method,
                      status='PENDING', idempotency_key=key)
    db.session.add(payment)
    db.session.flush()

    if method == 'wallet':
        changed = wallet.query.filter_by(id=wallet.id, version=wallet.version).update(
            {"balance": wallet.balance - amount, "version": wallet.version + 1})
        if changed == 0:
            db.session.rollback()
            return fail('WALLET_BUSY', 'wallet changed, please try again', 409)
        db.session.add(ledgers_version(account_type='wallet', account_id=wallet.id, direction='DEBIT',
                                   amount=amount, reference='payment:' + str(payment.id)))
    else:
        db.session.add(ledgers_version(account_type='bank', account_id=bank.id, direction='DEBIT',
                                   amount=amount, reference='payment:' + str(payment.id)))
    payment.status = 'SUCCESS'
    order.status = 'CONFIRMED'

    for item in OrderItem.query.filter_by(order_id=order.id).all():
        stock = Inventory.query.filter_by(product_id=item.product_id).first()
        stock.reserved_qty = stock.reserved_qty - item.quantity

    cart = Cart.query.filter_by(user_id=user_id).first()
    if cart:
        CartItem.query.filter_by(cart_id=cart.id).delete()

    db.session.commit()
    return success(payment_view(payment), 201)

@payments_bp.route('/api/v1/payments/<int:payment_id>/refunds', methods=['POST'])
@jwt_required()
def refund(payment_id):
    data = request.get_json(silent=True) or {}
    payment = Payment.query.get(payment_id)
    if payment is None:
        return fail('NOT_FOUND', 'payment not found', 404)
    order = Order.query.get(payment.order_id)
    if order.user_id != int(get_jwt_identity()) and get_jwt().get('role') != 'admin':
        return fail('FORBIDDEN', 'this is not your payment', 403)
    if payment.status != 'SUCCESS':
        return fail('PAYMENT_NOT_PAID', 'only a paid payment can be refunded', 422)

    left = payment.amount - refunded_so_far(payment.id)
    if left <= 0:
        return fail('REFUND_TOO_HIGH', 'this payment is already fully refunded', 422)
    amount = data.get('amount', left)          # no amount sent = refund everything left
    if type(amount) is not int or amount <= 0:
        return fail('VALIDATION_ERROR', 'amount must be a positive whole number (in paise)', 422)
    if amount > left:
        return fail('REFUND_TOO_HIGH', 'only ' + str(left) + ' is left to refund', 422)

    if not make_refund(payment, amount, str(data.get('reason') or 'customer request')):
        db.session.rollback()
        return fail('WALLET_BUSY', 'wallet changed, please try again', 409)
    db.session.commit()
    return success({"refund_amount": amount, "left_to_refund": left - amount}, 201)
