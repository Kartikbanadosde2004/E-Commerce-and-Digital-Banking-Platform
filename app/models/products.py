from app import db

class Product(db.Model):
    __tablename__ = 'products'

    id = db.Column(db.Integer, primary_key=True)
    sku = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.String(500))
    price = db.Column(db.Integer, nullable=False)      # in paise
    active = db.Column(db.Boolean, default=True, nullable=False)

class Inventory(db.Model):
    __tablename__ = 'inventory'

    product_id = db.Column(db.Integer,primary_key=True)
    available_qty = db.Column(db.Integer, default=0, nullable=False)
    reserved_qty = db.Column(db.Integer, default=0)
    version = db.Column(db.Integer, default=0, nullable=False)
