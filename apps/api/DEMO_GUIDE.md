# SellerMate AI — Demo Guide

A complete walkthrough for demonstrating SellerMate AI to investors, clients, or team members. Covers the full merchant journey from registration to AI-powered business intelligence.

**Estimated demo time:** 20 minutes  
**Prerequisites:** API running locally or on staging. See [QUICK_START.md](QUICK_START.md).

---

## Before the Demo

```bash
# Confirm server is live
curl http://localhost:8000/health
# → {"status":"ok","version":"1.0.0"}
```

Set your base URL:
```bash
BASE="http://localhost:8000/api/v1"
```

---

## Section 1 — Merchant Onboarding (3 min)

### 1.1 Register

```bash
curl -X POST $BASE/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "demo@dhakafashion.com",
    "phone": "+8801712345678",
    "password": "Demo2026!",
    "business_name": "Dhaka Fashion House",
    "owner_name": "Rahim Chowdhury",
    "business_type": "FASHION_CLOTHING"
  }'
```

**Talk track:** "Registration takes seconds. We capture business type so the AI can tailor its language and insights for that vertical."

### 1.2 Login and Save Token

```bash
curl -X POST $BASE/auth/login \
  -H "Content-Type: application/json" \
  -d '{"identifier": "+8801712345678", "password": "Demo2026!"}'
```

Save the token:
```bash
TOKEN="<paste access_token here>"
```

### 1.3 View Profile

```bash
curl $BASE/auth/me \
  -H "Authorization: Bearer $TOKEN"
```

**Talk track:** "Every API call is authenticated and scoped — a merchant can only ever see their own data."

---

## Section 2 — Product & Inventory Setup (3 min)

### 2.1 Create a Product with Variants

```bash
curl -X POST $BASE/products \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Premium Panjabi",
    "category": "CLOTHING",
    "description": "Eid special collection, pure cotton",
    "base_price": "1200.00",
    "variants": [
      {
        "name": "White — M",
        "sku": "PAN-WH-M-001",
        "price": "1200.00",
        "stock_quantity": 50,
        "low_stock_alert": 10
      },
      {
        "name": "White — L",
        "sku": "PAN-WH-L-001",
        "price": "1200.00",
        "stock_quantity": 30,
        "low_stock_alert": 10
      },
      {
        "name": "Blue — M",
        "sku": "PAN-BL-M-001",
        "price": "1350.00",
        "stock_quantity": 20,
        "low_stock_alert": 5
      }
    ]
  }'
```

Save: `PRODUCT_ID` and `VARIANT_ID` (White M) from the response.

**Talk track:** "One product, multiple variants — size, colour, SKU. Each variant tracks its own stock with independent low-stock alerts."

### 2.2 Check Inventory

```bash
curl "$BASE/inventory?low_stock=false" \
  -H "Authorization: Bearer $TOKEN"
```

### 2.3 Check Low-Stock Alerts

```bash
curl $BASE/inventory/alerts \
  -H "Authorization: Bearer $TOKEN"
```

---

## Section 3 — Customer Management (2 min)

### 3.1 Add Customers

```bash
curl -X POST $BASE/customers \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Karim Rahman",
    "phone": "+8801812345678",
    "address": "Mirpur 10, Dhaka",
    "district": "Dhaka"
  }'
```

Save: `CUSTOMER_ID`

Add a second customer for repeat-order demo:
```bash
curl -X POST $BASE/customers \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Fatema Begum",
    "phone": "+8801912345678",
    "address": "Uttara, Dhaka",
    "district": "Dhaka",
    "tags": ["VIP", "wholesale"]
  }'
```

### 3.2 Tag a Customer

```bash
curl -X POST $BASE/customers/$CUSTOMER_ID/tags/repeat-buyer \
  -H "Authorization: Bearer $TOKEN"
```

**Talk track:** "Tags are free-form — merchants can label customers however makes sense for their business: VIP, wholesale, COD-only, anything."

---

## Section 4 — Order Lifecycle (5 min)

### 4.1 Place an Order

```bash
curl -X POST $BASE/orders \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": "'$CUSTOMER_ID'",
    "items": [
      {
        "product_id": "'$PRODUCT_ID'",
        "variant_id": "'$VARIANT_ID'",
        "quantity": 2
      }
    ],
    "discount_amount": "100",
    "shipping_cost": "80",
    "payment_method": "COD",
    "delivery_address": "Mirpur 10, Dhaka-1216",
    "channel": "FACEBOOK"
  }'
```

Save: `ORDER_ID`

**Talk track:** "Total is calculated automatically: (1200 × 2) − 100 + 80 = 2380 BDT. Inventory is deducted immediately. Customer stats update — total orders, total spent."

Note the `status: PENDING` and `payment_status: UNPAID` in the response.

### 4.2 Confirm the Order

```bash
curl -X POST $BASE/orders/$ORDER_ID/status \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"status": "CONFIRMED", "note": "Verified via WhatsApp"}'
```

### 4.3 Record Payment

```bash
curl -X POST $BASE/orders/$ORDER_ID/payment \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"amount": "2380", "method": "BKASH", "reference": "TXN-001"}'
```

**Talk track:** "Merchants record COD payments after delivery or bKash before. Partial payments are tracked — `amount_paid` vs `total_amount`."

### 4.4 Ship and Deliver

```bash
# Processing
curl -X POST $BASE/orders/$ORDER_ID/status \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"status": "PROCESSING"}'

# Shipped with tracking
curl -X POST $BASE/orders/$ORDER_ID/status \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"status": "SHIPPED", "note": "Pathao tracking: PTH-12345"}'

# Delivered
curl -X POST $BASE/orders/$ORDER_ID/status \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"status": "DELIVERED"}'
```

### 4.5 Demo Cancel Flow (Separate Order)

```bash
# Create another order
curl -X POST $BASE/orders \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": "'$CUSTOMER_ID'",
    "items": [{"product_id": "'$PRODUCT_ID'", "variant_id": "'$VARIANT_ID'", "quantity": 1}],
    "payment_method": "COD"
  }'
# Save ORDER_ID_2

# Cancel it
curl -X DELETE $BASE/orders/$ORDER_ID_2 \
  -H "Authorization: Bearer $TOKEN"
```

**Talk track:** "Cancellation automatically restores inventory and rolls back customer stats. No double-counting, no ghost stock."

---

## Section 5 — Analytics Dashboard (2 min)

### 5.1 Real-Time Dashboard

```bash
curl $BASE/analytics/dashboard \
  -H "Authorization: Bearer $TOKEN"
```

Response shows:
- `today_revenue`, `weekly_revenue`, `monthly_revenue`
- `total_orders`, `delivered_orders`, `cancelled_orders`
- `repeat_customers`, `average_order_value`
- `top_products` (last 30 days)
- `top_customers` (by total spent)

### 5.2 Revenue Time Series

```bash
curl "$BASE/analytics/revenue?from_date=2026-01-01&to_date=2026-06-22&granularity=month" \
  -H "Authorization: Bearer $TOKEN"
```

### 5.3 Overview KPIs with Period Comparison

```bash
curl "$BASE/analytics/overview?from_date=2026-06-01&to_date=2026-06-22" \
  -H "Authorization: Bearer $TOKEN"
```

**Talk track:** "Every number is compared against the equivalent prior period, so merchants immediately see if this month is better or worse than last month."

---

## Section 6 — AI Assistant (3 min)

### 6.1 Create a Conversation

```bash
curl -X POST $BASE/assistant/conversations \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title": "Business Review"}'
```

Save: `CONV_ID`

### 6.2 Ask in Bengali

```bash
curl -N $BASE/assistant/conversations/$CONV_ID/chat \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "আমার আজকের মোট বিক্রয় কত টাকা?"}'
```

The response streams via Server-Sent Events. Each `data:` line is a token.

**Talk track:** "The assistant speaks Bengali natively — not translation, actual reasoning in Bengali. It calls real tools behind the scenes: order lookup, inventory check, customer analysis. No hallucination on numbers."

### 6.3 Ask a Follow-Up

```bash
curl -N $BASE/assistant/conversations/$CONV_ID/chat \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "Which products are running low on stock?"}'
```

**Talk track:** "The conversation has memory — it knows from the prior message who you are and what you were asking about. It switches between Bengali and English in the same session."

---

## Section 7 — Strategic Intelligence (2 min)

### 7.1 Run Strategic Agents

```bash
curl -X POST $BASE/ai/strategic/run \
  -H "Authorization: Bearer $TOKEN"
```

**Talk track:** "Two agents run simultaneously: TrustGraph and FraudSentinel. These are not LLM calls — they're deterministic rules applied to your actual order history. That means instant results and zero hallucination risk."

### 7.2 View Trust Score

```bash
curl $BASE/ai/strategic/trust-score \
  -H "Authorization: Bearer $TOKEN"
```

Response explains:
- `trust_score`: 0-100 reliability score
- `confidence`: LOW/MEDIUM/HIGH (based on order count)
- `risk_flags`: specific issues detected
- `details`: all underlying rates (delivery, payment, cancellation, retention)

### 7.3 View Fraud Report

```bash
curl $BASE/ai/strategic/fraud-report \
  -H "Authorization: Bearer $TOKEN"
```

**Talk track:** "Fraud Sentinel looks at the last 30 days for three patterns: cancellation spikes (fake orders), stale unpaid orders accumulating, and sudden volume spikes that don't match the merchant's history. A clean merchant scores near zero."

### 7.4 Historical Insights

```bash
curl "$BASE/ai/strategic/insights?agent_name=trust_graph" \
  -H "Authorization: Bearer $TOKEN"
```

**Talk track:** "Every run is stored. You can track how trust and fraud risk evolve over time as the merchant grows."

---

## Section 8 — Data Export (30 sec)

```bash
# Orders to CSV
curl $BASE/orders/export \
  -H "Authorization: Bearer $TOKEN" \
  -o orders_export.csv

# Customers to CSV
curl $BASE/customers/export \
  -H "Authorization: Bearer $TOKEN" \
  -o customers_export.csv
```

**Talk track:** "One-click export to CSV. Compatible with Excel, Google Sheets, any accounting tool."

---

## Section 9 — Multi-Tenant Isolation (30 sec)

```bash
# Register a second merchant
curl -X POST $BASE/auth/register \
  -d '{"email":"other@shop.com","phone":"+8801900000002","password":"Pass123!","business_name":"Other Shop","owner_name":"Other Owner","business_type":"FOOD_BEVERAGE"}'

# Login as second merchant
curl -X POST $BASE/auth/login \
  -d '{"identifier":"+8801900000002","password":"Pass123!"}'
# Save TOKEN_B

# Try to access first merchant's order
curl $BASE/orders/$ORDER_ID \
  -H "Authorization: Bearer $TOKEN_B"
# → 404 Not Found
```

**Talk track:** "Total tenant isolation. Merchant B cannot see, search, or enumerate any data belonging to Merchant A — not orders, not customers, not inventory. Enforced at the query level, not the application level."

---

## Demo Tips

- **Slow internet?** The AI streaming endpoint (`/chat`) may take 1-3 seconds to start — this is the Anthropic API latency, not a backend issue.
- **Empty analytics?** Analytics need at least one order with status DELIVERED and payment recorded. Run Section 4 before Section 5.
- **Trust score too low?** The demo fixture only has 1-2 orders so confidence will be LOW. Explain that confidence rises with order history — a merchant with 50+ orders gets HIGH confidence.
- **Want Bengali responses?** Message in Bengali. The system prompt is bilingual; the model mirrors the language of the user's message.

---

## Reset Demo Data

To start fresh without restarting the server, register new merchants with different phone numbers. All data is scoped to `merchant_id`, so new registrations get a clean slate automatically.
