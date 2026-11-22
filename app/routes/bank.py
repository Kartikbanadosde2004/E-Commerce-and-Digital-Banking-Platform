import uuid
from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models.wallet import bank_accounts, wallets, ledgers_version
from app.routes.auth import success, fail

import uuid
from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models.wallet import bank_accounts, wallets, ledgers_version
from app.routes.auth import success, fail

bank_bp = Blueprint('bank', __name__)

def get_my_wallet(user_id):
    wallet = wallets.query.filter_by(user_id=user_id).first()
    if wallet is None:
        wallet = wallets(user_id=user_id, balance=0, currency='INR', version=0)
        db.session.add(wallet)
        db.session.commit()
    return wallet

@bank_bp.route('/api/v1/bank-accounts', methods=['POST'])
@jwt_required()
def link_account():
    data = request.get_json(silent=True) or {}
    number = str(data.get('account_number') or '')
    if not number:
        return fail('MISSING_FIELDS', 'account number is required', 400)
    if not number.isdigit() or len(number) < 8:
        return fail('VALIDATION_ERROR', 'account number must be 8 or more digits', 422)

    account = bank_accounts(user_id=int(get_jwt_identity()),
                          provider_ref='sim_' + uuid.uuid4().hex[:8],
                          masked_number='XXXX' + number[-4:], status='ACTIVE')
    db.session.add(account)
    db.session.commit()
    return success({"id": account.id, "masked_number": account.masked_number,
                    "status": account.status}, 201)

@bank_bp.route('/api/v1/wallet/topups', methods=['POST'])
@jwt_required()
def top_up():
    user_id = int(get_jwt_identity())
    data = request.get_json(silent=True) or {}
    bank_id = data.get('bank_account_id')
    amount = data.get('amount')
    if bank_id is None or amount is None:
        return fail('MISSING_FIELDS', 'bank account_id and amount are required', 400)
    if type(bank_id) is not int or type(amount) is not int or amount <= 0:
        return fail('VALIDATION_ERROR', 'amount must be a positive whole number', 422)

    bank = bank_accounts.query.filter_by(id=bank_id, user_id=user_id, status='ACTIVE').first()
    if bank is None:
        return fail('NOT_FOUND', 'bank account not found', 404)

    wallet = get_my_wallet(user_id)
    changed = wallets.query.filter_by(id=wallet.id, version=wallet.version).update(
        {"balance": wallet.balance + amount, "version": wallet.version + 1})
    if changed == 0:
        db.session.rollback()
        return fail('WALLET_BUSY', 'wallet changed,please try again', 409)

    db.session.add(ledgers_version(account_type='bank', account_id=bank.id, direction='DEBIT',
                               amount=amount, reference='top'))
    db.session.add(ledgers_version(account_type='wallet', account_id=wallet.id, direction='CREDIT',
                               amount=amount, reference='top'))
    db.session.commit()
    return success({"balance": wallet.balance, "top_amount": amount}, 201)

@bank_bp.route('/api/v1/wallet', methods=['GET'])
@jwt_required()
def view_wallet():
    wallet = get_my_wallet(int(get_jwt_identity()))
    entries = []
    rows = ledgers_version.query.filter_by(account_type='wallet', account_id=wallet.id)
    for e in rows.order_by(ledgers_version.id.desc()).limit(10).all():
        entries.append({"direction": e.direction, "amount": e.amount, "reference": e.reference})
    return success({"balance": wallet.balance, "currency": wallet.currency,
                    "recent_entries": entries})