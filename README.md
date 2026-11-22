# E-Commerce and Digital Banking Platform

This is a Python with SQL major project that combines an e-commerce marketplace with a simple wallet and banking service. 
Customers can register, browse products, manage a cart, place orders, pay from a wallet or linked bank account, and request refunds. 
Administrators manage products, stock, orders and transaction reports. The project is built with Python, Flask and SQLite,
and tested with Postman. It runs locally. Deployment files for AWS EC2 are prepared but the project is not hosted on a cloud server.

## Features

- Register, login (JWT) and manage addresses
- Browse, search and paginate products
- Cart, checkout, order tracking and cancellation
- Simulated bank account linking, wallet top-up and statement
- Payment with an idempotency key (no double debit)
- Full or partial refund
- Admin: products, stock, order status, transaction report, audit logs
- `/health` check

## Technology

| Layer | Technology |
|---|---|
| API | Python 3, Flask, Flask-JWT-Extended |
| Database | SQLite |
| Testing | Postman |
| Deployment | Runs locally. EC2 setup files are prepared but not hosted |

## Run Locally

```
pip install -r requirements.txt
python data.py
python run.py
```

Open `http://127.0.0.1:5000/health` to check it works.

## Postman

1. Import the collection and the Local environment.
2. Set `base_url` to `http://127.0.0.1:5000`.
3. Run the collection. The login request saves `access_token` automatically.

## Main API Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| POST | /api/v1/auth/register | Create account |
| POST | /api/v1/auth/login | Get token |
| GET | /api/v1/products?q=&page= | Search products |
| POST | /api/v1/cart/items | Add to cart |
| POST | /api/v1/orders/checkout | Create order |
| POST | /api/v1/orders/{id}/cancel | Cancel order |
| POST | /api/v1/wallet/topups | Add money to wallet |
| POST | /api/v1/payments | Pay for order |
| POST | /api/v1/payments/{id}/refunds | Refund |
| GET | /api/v1/admin/reports/transactions | Admin report |
| GET | /health | Health check |

## Deployment Notes

This project runs locally on Flask with SQLite.

## Security Notes

- Passwords are stored as hashes.
- Real secrets and the database file are not committed (only `.env.example`).
- The banking module is a sandbox simulation for learning only.