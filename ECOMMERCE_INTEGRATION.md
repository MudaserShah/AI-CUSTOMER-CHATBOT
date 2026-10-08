# Ecommerce + AI Support integration patch

This patch turns the existing support-only React screen into a small ecommerce reference app and connects it to the existing customer-scoped backend.

## What changes

- `GET /store/products` exposes a server-owned catalog.
- `POST /store/checkout` creates a customer for a new email, generates a server-side `customer-<random>` ID and a random 5-digit order ID, calculates prices on the backend, stores the order, and returns a JWT for that customer.
- An unauthenticated checkout cannot claim an existing customer email; existing customers must authenticate first.
- `GET /orders` and `GET /orders/{order_id}` expose only the authenticated customer's orders.
- Orders keep a JSONB snapshot of product/quantity/price plus total, currency, payment method, and creation time.
- The existing refund service remains the source of truth: order ownership, Delivered status, 7-day window, duplicate protection, and refund status.
- `POST /refund` and `GET /refund/{order_id}` are still JWT-scoped.
- Chat checkpoint thread IDs are namespaced by customer to prevent cross-customer thread collisions.
- Frontend includes catalog, cart, checkout, customer ID/order ID confirmation, order history, refund request UI, refund status, and floating AI support.

## Apply locally

From the repository root:

```bash
cp -r /path/to/ai_customer_ecommerce_patch/src/store src/
cp /path/to/ai_customer_ecommerce_patch/src/services/store_service.py src/services/
cp /path/to/ai_customer_ecommerce_patch/src/services/order_service.py src/services/
cp /path/to/ai_customer_ecommerce_patch/src/database/order_repository.py src/database/
cp /path/to/ai_customer_ecommerce_patch/src/database/repository.py src/database/
cp /path/to/ai_customer_ecommerce_patch/src/auth/dependencies.py src/auth/
cp /path/to/ai_customer_ecommerce_patch/src/routes/store_routes.py src/routes/
cp /path/to/ai_customer_ecommerce_patch/src/routes/order_routes.py src/routes/
cp /path/to/ai_customer_ecommerce_patch/src/routes/refund_routes.py src/routes/
cp /path/to/ai_customer_ecommerce_patch/src/routes/chat_routes.py src/routes/
cp /path/to/ai_customer_ecommerce_patch/src/schemas/store_schemas.py src/schemas/
cp /path/to/ai_customer_ecommerce_patch/src/schemas/order_schemas.py src/schemas/
cp /path/to/ai_customer_ecommerce_patch/src/schemas/refund_schemas.py src/schemas/
cp /path/to/ai_customer_ecommerce_patch/src/main.py src/
cp /path/to/ai_customer_ecommerce_patch/frontend/src/App.tsx frontend/src/
cp /path/to/ai_customer_ecommerce_patch/frontend/src/App.css frontend/src/
cp /path/to/ai_customer_ecommerce_patch/frontend/src/api.ts frontend/src/
cp /path/to/ai_customer_ecommerce_patch/migrations/versions/*.py migrations/versions/
```

Before copying into `main`, make a normal git branch and commit the patch there.

## Database migration

The new order fields need migration `b7e3f6a9c2d1`; the customer email uniqueness migration is `c8f1a2d3e4b5`.

If your database has already been stamped at the existing baseline migration `a64e2b1f1cb3`, run:

```bash
alembic upgrade head
```

Before applying `c8f1a2d3e4b5` to an existing database, check for duplicate customer emails case-insensitively:

```sql
SELECT LOWER(email), COUNT(*)
FROM customers
WHERE email IS NOT NULL
GROUP BY LOWER(email)
HAVING COUNT(*) > 1;
```

Clean up duplicates first. For a brand-new database, `alembic upgrade head` creates the baseline and then the two new migrations.

## Local environment

Frontend:

```bash
cd frontend
cp .env.example .env
npm install
npm run dev
```

The browser should use `http://localhost:8000` unless `VITE_API_BASE_URL` is set.

Backend `.env` must allow the frontend origin, e.g.:

```dotenv
CORS_ALLOWED_ORIGINS=http://localhost:5173
```

## End-to-end test flow

1. Start Postgres/Qdrant and the FastAPI backend.
2. Run the migration.
3. Open the Vite frontend.
4. Add products to the cart.
5. Checkout with a new email.
6. The response displays a generated customer ID and 5-digit order ID.
7. `My orders` reads only that customer's orders using the returned JWT.
8. The AI widget can ask about order status using the authenticated customer context.
9. A refund request appears only when the backend says the order is eligible.
10. After the order is marked `Delivered` and is inside the 7-day window, the user can submit one active refund request; the existing partial unique index prevents duplicate active requests.

## Important production boundary

This reference checkout is not a payment gateway and the browser must never be trusted for order totals. The backend owns catalog prices and totals.

For a real ecommerce deployment, the host application's existing authentication system should mint the support JWT rather than making `/auth/token` or checkout the long-term identity provider. For real money movement, add a payment provider and a refund adapter; the current `/refund` flow is a refund-request workflow, not a payment-network reversal.

The demo currently stores the JWT in browser localStorage for simplicity. A production site should prefer its authenticated host session / secure HttpOnly cookies.
