from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from app import db
from app.models.products import Product, Inventory
from app.models.orders import Order
from app.models.payment import Payment
from app.models.refund import Refund
from app.models.audit import AuditLog
from app.models.wallet import ledgers_version as LedgerEntry
from app.routes.auth import success, fail

admin_bp = Blueprint('admin', __name__, url_prefix='/api/v1/admin')

NEXT_STATUS = {"CONFIRMED": "PACKED", "PACKED": "SHIPPED", "SHIPPED": "DELIVERED"}

def not_admin():
    return get_jwt().get('role') != 'admin'

def log(action, entity_type, entity_id):
    db.session.add(AuditLog(actor_id=int(get_jwt_identity()), action=action,
         entity_type=entity_type, entity_id=entity_id))

@admin_bp.route('/products', methods=['POST'])
@jwt_required()
def create_product():
    if not_admin():
        return fail('FORBIDDEN', 'admin access only', 403)
    data = request.get_json(silent=True) or {}
    sku = data.get('sku')
    name = data.get('name')
    price = data.get('price')
    quantity = data.get('quantity')
    if not sku or not name or price is None or quantity is None:
        return fail('MISSING_FIELDS', 'sku, name, price and quantity are required', 400)
    if type(price) is not int or type(quantity) is not int or price <= 0 or quantity <= 0:
        return fail('VALIDATION_ERROR', 'price and quantity must be positive whole numbers', 422)
    if hasattr(Product, 'sku') and Product.query.filter_by(sku=sku).first():
        return fail('SKU_EXISTS', 'this sku already exists', 409)

    product = Product(name=name, price=price, active=True)
    if hasattr(Product, 'sku'):
        product.sku = sku
    if hasattr(Product, 'description'):
        product.description = data.get('description', '')
    db.session.add(product)
    db.session.flush()                      # gives product.id, nothing is saved yet
    db.session.add(Inventory(product_id=product.id, available_qty=quantity,
                             reserved_qty=0, version=0))
    log('CREATE_PRODUCT', 'products', product.id)
    db.session.commit()
    return success({"id": product.id, "name": product.name, "price": product.price,
                    "stock": quantity}, 201)

@admin_bp.route('/products/<int:product_id>/stock', methods=['PATCH'])
@jwt_required()
def change_stock(product_id):
    if not_admin():
        return fail('FORBIDDEN', 'admin access only', 403)
    data = request.get_json(silent=True) or {}
    qty = data.get('available_qty')
    if qty is None:
        return fail('MISSING_FIELDS', 'available_qty is required', 400)
    if type(qty) is not int or qty < 0:
        return fail('VALIDATION_ERROR', 'available_qty must be 0 or a positive whole number', 422)

    stock = Inventory.query.filter_by(product_id=product_id).first()
    if stock is None:
        return fail('NOT_FOUND', 'product not found', 404)
    stock.available_qty = qty
    stock.version = stock.version + 1
    log('UPDATE_STOCK', 'products', product_id)
    db.session.commit()
    return success({"product_id": product_id, "available_qty": qty})

@admin_bp.route('/orders/<int:order_id>/status', methods=['PATCH'])
@jwt_required()
def change_status(order_id):
    if not_admin():
        return fail('FORBIDDEN', 'admin access only', 403)
    data = request.get_json(silent=True) or {}
    new_status = data.get('status')
    if not new_status:
        return fail('MISSING_FIELDS', 'status is required', 400)

    order = Order.query.get(order_id)
    if order is None:
        return fail('NOT_FOUND', 'order not found', 404)
    if NEXT_STATUS.get(order.status) != new_status:
        return fail('BAD_STATUS', 'cannot move from ' + order.status + ' to ' + str(new_status), 409)
    order.status = new_status
    log('ORDER_' + new_status, 'orders', order_id)
    db.session.commit()
    return success({"order_id": order_id, "status": new_status})

@admin_bp.route('/reports/transactions', methods=['GET'])
@jwt_required()
def transaction_report():
    if not_admin():
        return fail('FORBIDDEN', 'admin access only', 403)

    paid_count = 0
    paid_total = 0
    for p in Payment.query.filter_by(status='SUCCESS').all():
        paid_count = paid_count + 1
        paid_total = paid_total + p.amount

    refund_count = 0
    refund_total = 0
    for r in Refund.query.all():
        refund_count = refund_count + 1
        refund_total = refund_total + r.amount

    topup_count = 0
    topup_total = 0
    topups = LedgerEntry.query.filter(LedgerEntry.account_type == 'wallet',
             LedgerEntry.direction == 'CREDIT',
             LedgerEntry.reference.like('top%')).all()
    for t in topups:
        topup_count = topup_count + 1
        topup_total = topup_total + t.amount

    orders = {}
    for status in ['PENDING', 'CONFIRMED', 'PACKED', 'SHIPPED', 'DELIVERED', 'CANCELLED']:
        orders[status] = Order.query.filter_by(status=status).count()

    return success({"payments": {"count": paid_count, "total_amount": paid_total},
            "refunds": {"count": refund_count, "total_amount": refund_total},
            "wallet_topups": {"count": topup_count, "total_amount": topup_total},
            "orders_by_status": orders})

@admin_bp.route('/audit-logs', methods=['GET'])
@jwt_required()
def audit_logs():
    if not_admin():
        return fail('FORBIDDEN', 'admin access only', 403)
    result = []
    for a in AuditLog.query.order_by(AuditLog.id.desc()).limit(20).all():
        result.append({"id": a.id, "actor_id": a.actor_id, "action": a.action,
             "entity_type": a.entity_type, "entity_id": a.entity_id,
             "created_at": str(a.created_at)})
    return success({"audit_logs": result})