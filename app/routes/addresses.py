from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models.address import Address
from app.routes.auth import success, fail

addresses_bp = Blueprint('addresses', __name__)
@addresses_bp.route('/api/v1/addresses', methods=['POST'])
@jwt_required()
def add_address():
    data = request.get_json(silent=True) or {}
    line1 = data.get('line1')
    city = data.get('city')
    state = data.get('state')
    postal_code = data.get('postal_code')
    if not line1 or not city or not state or not postal_code:
        return fail('MISSING_FIELDS', 'line1, city, state and postal_code are required', 400)

    address = Address(user_id=int(get_jwt_identity()), line1=line1, city=city,
                      state=state, postal_code=str(postal_code))
    db.session.add(address)
    db.session.commit()
    return success({"id": address.id, "line1": address.line1, "city": address.city,
                    "state": address.state, "postal_code": address.postal_code}, 201)

@addresses_bp.route('/api/v1/addresses', methods=['GET'])
@jwt_required()
def my_addresses():
    result = []
    for a in Address.query.filter_by(user_id=int(get_jwt_identity())).all():
        result.append({"id": a.id, "line1": a.line1, "city": a.city,
                       "state": a.state, "postal_code": a.postal_code})
    return success({"addresses": result})