from flask import Blueprint, request
from app.models.products import Product, Inventory
from app.routes.auth import success

products_bp = Blueprint('products', __name__)

@products_bp.route('/api/v1/products', methods=['GET'])
def list_products():
    search = request.args.get('q', '')
    page = request.args.get('page', '1')
    page = int(page) if page.isdigit() and int(page) > 0 else 1

    query = Product.query.filter_by(active=True).filter(Product.name.ilike('%' + search + '%'))
    rows = query.order_by(Product.id).paginate(page=page, per_page=8, error_out=False)

    result = []
    for p in rows.items:
        stock = Inventory.query.filter_by(product_id=p.id).first()
        result.append({"id": p.id, "name": p.name, "price": p.price,
                       "stock": stock.available_qty if stock else 0})
    return success({"products": result, "page": page, "per_page": 8})