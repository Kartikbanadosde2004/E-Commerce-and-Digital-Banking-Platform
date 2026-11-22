from app import db


class Refund(db.Model):
    __tablename__ = 'refunds'
    id = db.Column(db.Integer, primary_key=True)
    payment_id = db.Column(db.Integer, nullable=False)
    amount = db.Column(db.Integer, nullable=False)
    reason = db.Column(db.String)
    status = db.Column(db.String, nullable=False, default='DONE')