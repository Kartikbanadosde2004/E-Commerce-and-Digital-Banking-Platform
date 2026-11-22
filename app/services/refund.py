from app import db
from app.models.orders import Order
from app.models.wallet import wallets as Wallet, ledgers_version as LedgerEntry
from app.models.refund import Refund

def refunded_so_far(payment_id):
    total = 0
    for r in Refund.query.filter_by(payment_id=payment_id).all():
        total = total + r.amount
    return total

def make_refund(payment, amount, reason):

    order = Order.query.get(payment.order_id)
    wallet = Wallet.query.filter_by(user_id=order.user_id).first()
    changed = Wallet.query.filter_by(id=wallet.id, version=wallet.version).update(
        {"balance": wallet.balance + amount, "version": wallet.version + 1})
    if changed == 0:
        return False
    db.session.add(Refund(payment_id=payment.id, amount=amount, reason=reason, status='DONE'))
    db.session.add(LedgerEntry(account_type='wallet', account_id=wallet.id, direction='CREDIT',
    amount=amount, reference='refund:' + str(payment.id)))
    return True