from app import db


class bank_accounts(db.Model):
    __tablename__ = 'bank_accounts'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    provider_ref = db.Column(db.String)
    masked_number = db.Column(db.String)
    status = db.Column(db.String, nullable=False, default='ACTIVE')


class wallets(db.Model):
    __tablename__ = 'wallets'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False, unique=True)
    balance = db.Column(db.Integer, nullable=False, default=0)
    currency = db.Column(db.String, nullable=False, default='INR')
    version = db.Column(db.Integer, nullable=False, default=0)


class ledgers_version(db.Model):
    __tablename__ = 'ledger_entries'
    id = db.Column(db.Integer, primary_key=True)
    account_type = db.Column(db.String, nullable=False)
    account_id = db.Column(db.Integer, nullable=False)
    direction = db.Column(db.String, nullable=False)
    amount = db.Column(db.Integer, nullable=False)
    reference = db.Column(db.String)