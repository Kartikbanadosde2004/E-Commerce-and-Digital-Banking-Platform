from werkzeug.security import generate_password_hash
from app import create_app, db
from app.models.user import User
from app.models.address import Address
from app.models.products import Product, Inventory
from app.models.cart import Cart, CartItem
from app.models.orders import Order, OrderItem
from app.models.wallet import bank_accounts, wallets, ledgers_version
from app.models.payment import Payment
from app.models.refund import Refund
from app.models.audit import AuditLog

app = create_app()

names = ["Admin", "Amit", "Neha", "Rahul", "Priya", "Suresh", "Anita", "Vikas", "Pooja", "Rohan"]

# (sku, name, description, price in paise, stock)
products = [("LAP-001", "Laptop", "14 inch laptop", 4999900, 5),
            ("MOB-001", "Mobile Phone", "5G smartphone", 1499900, 30),
            ("HED-001", "Headphones", "Wireless headphones", 199900, 50),
            ("KEY-001", "Keyboard", "USB keyboard", 79900, 40),
            ("MOU-001", "Mouse", "Optical mouse", 49900, 60),
            ("MON-001", "Monitor", "24 inch monitor", 899900, 15),
            ("PEN-001", "Pen Drive", "64 GB pen drive", 39900, 80),
            ("BAG-001", "Backpack", "Laptop backpack", 129900, 35),
            ("WEB-001", "Webcam", "HD webcam", 299900, 20),
            ("POW-001", "Power Bank", "10000 mAh power bank", 159900, 45)]

statuses = ["CONFIRMED", "PACKED", "SHIPPED", "DELIVERED", "CANCELLED",
            "CONFIRMED", "CONFIRMED", "DELIVERED", "PACKED", "SHIPPED"]
quantities = [1, 2, 1, 3, 1, 2, 1, 1, 2, 1]

with app.app_context():
    if User.query.count() > 0 or Product.query.count() > 0:
        print("Data already exists.")
    else:
        pw = generate_password_hash("admin@123")
        for i in range(10):
            role = "customer"
            if i == 0:
                role = "admin"
            db.session.add(User(name=names[i], email=names[i].lower() + "@gmail.com",
            password_hash=pw, role=role))
        db.session.commit()

        for i in range(10):
            sku, name, desc, price, qty = products[i]
            p = Product(name=name, price=price, active=True, sku=sku, description=desc)
            db.session.add(p)
            db.session.flush()
            db.session.add(Inventory(product_id=p.id, available_qty=qty, reserved_qty=0, version=0))
        db.session.commit()

        for i in range(10):
            cart = Cart(user_id=i + 1)
            db.session.add(cart)
            db.session.flush()
            db.session.add(CartItem(cart_id=cart.id, product_id=i + 1, quantity=1))
        db.session.commit()

        totals = []
        for i in range(10):
            total = products[i][3] * quantities[i]
            totals.append(total)
            order = Order(user_id=i + 1, status=statuses[i], total_amount=total)
            db.session.add(order)
            db.session.flush()
            db.session.add(OrderItem(order_id=order.id, product_id=i + 1, product_name=products[i][1],
             unit_price=products[i][3], quantity=quantities[i]))
        db.session.commit()

        for i in range(10):
            db.session.add(bank_accounts(user_id=i + 1, provider_ref="sim_000" + str(i),
            masked_number="XXXX" + str(1001 + i), status="ACTIVE"))
        db.session.commit()

        for i in range(10):
            db.session.add(wallets(user_id=i + 1, balance=(i + 1) * 50000, currency="INR", version=0))
        db.session.commit()

        for i in range(10):
            method = "wallet"
            if i % 2 == 1:
                method = "bank"
            db.session.add(Payment(order_id=i + 1, amount=totals[i], method=method,
                 status="SUCCESS", idempotency_key="seed-key-" + str(i + 1)))
        db.session.commit()

        for i in range(10):
            db.session.add(ledgers_version(account_type="wallet", account_id=i + 1, direction="DEBIT",
                amount=totals[i], reference="payment:" + str(i + 1)))
        db.session.commit()

        for i in range(10):
            amount = totals[i] // 10
            reason = "Small damage refund"
            if i == 4:
                amount = totals[i]
                reason = "Order cancelled"
            db.session.add(Refund(payment_id=i + 1, amount=amount, reason=reason, status="DONE"))
        db.session.commit()

        for i in range(10):
            db.session.add(AuditLog(actor_id=1, action="CREATE_PRODUCT",
            entity_type="products", entity_id=i + 1))
        db.session.commit()
        print("Done: 10 records added in every one of the 14 tables.")