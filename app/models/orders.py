from app import db

class Order(db.Model):
    __tablename__ = 'orders'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String, nullable=False, default='PENDING')
    total_amount = db.Column(db.Integer, nullable=False)

class OrderItem(db.Model):
    __tablename__ = 'order_items'
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, nullable=False)
    product_id = db.Column(db.Integer)
    product_name = db.Column(db.String)
    unit_price = db.Column(db.Integer)
    quantity = db.Column(db.Integer, nullable=False)