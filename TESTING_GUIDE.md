# SellerMate AI — Beta Testing Guide

This guide walks through every major flow testers should verify. Work through each section in order — each one builds on the previous.

---

## Before You Start

1. Backend running at `http://localhost:8000`
2. Frontend running at `http://localhost:3000`
3. Demo data seeded (see README setup steps)
4. Use the demo account: `demo@sellermate.ai` / `Demo1234!`

---

## 1. Authentication Flow

| Step | What to do | Expected |
|---|---|---|
| 1.1 | Go to `http://localhost:3000` | Redirects to `/login` |
| 1.2 | Click **"ডেমো হিসেবে ঢুকুন"** (Enter as Demo) | Logs in and redirects to `/dashboard` |
| 1.3 | Verify dashboard shows KPI cards | Today's Orders, Revenue, Pending, COD cards visible |
| 1.4 | Log out (Settings → Logout) | Returns to `/login` |
| 1.5 | Log in with email + password: `demo@sellermate.ai` / `Demo1234!` | Logs in successfully |

---

## 2. Seller Dashboard Flow

| Step | What to do | Expected |
|---|---|---|
| 2.1 | Check KPI row | 6 cards: Orders, Pending, Revenue, COD, Courier, Low Stock |
| 2.2 | Check "Do these 3 things today" box | Shows actionable tasks with links |
| 2.3 | Check Recent Orders table | At least 10 orders visible with status pills |
| 2.4 | Check Top Products list | Products ranked by revenue |
| 2.5 | Check Trust Score widget | Score 0-100, no red flags |

---

## 3. Order Management Flow

| Step | What to do | Expected |
|---|---|---|
| 3.1 | Go to `/orders` | Order list with filters |
| 3.2 | Filter by status: `PENDING` | Shows only pending orders |
| 3.3 | Click any order | Order detail page opens |
| 3.4 | Change order status to `CONFIRMED` | Status updates, toast confirmation |
| 3.5 | Try `SHIPPED` status with a tracking number | Tracking ID saved |

---

## 4. Product Management Flow

| Step | What to do | Expected |
|---|---|---|
| 4.1 | Go to `/products` | Product list loads with 90+ items |
| 4.2 | Search for a product name | Results filter in real time |
| 4.3 | Click **Add Product** | Product form opens |
| 4.4 | Fill in name, price, stock, category → Save | Product created, appears in list |
| 4.5 | Edit an existing product's price | Price updates |

---

## 5. Inventory Flow

| Step | What to do | Expected |
|---|---|---|
| 5.1 | Go to `/inventory` | Inventory list with stock levels |
| 5.2 | Identify a low-stock item (red indicator) | Alert indicator visible |
| 5.3 | Adjust stock quantity for an item | Stock count updates |
| 5.4 | Check inventory health summary | Out-of-stock and low-stock counts shown |

---

## 6. Customer Management Flow

| Step | What to do | Expected |
|---|---|---|
| 6.1 | Go to `/customers` | Customer list (20+ demo customers) |
| 6.2 | Click a customer | Customer profile with order history |
| 6.3 | Check customer tags (VIP, New, etc.) | Tags visible based on order history |

---

## 7. Store Builder Flow (Seller Side)

| Step | What to do | Expected |
|---|---|---|
| 7.1 | Go to `/store-builder` | Store settings form loads (not stuck) |
| 7.2 | Check that Store Name is pre-filled | Shows "Fresh Test Shop" or your store name |
| 7.3 | Edit the store description | Text updates in form |
| 7.4 | Click **Save Changes** | Saves successfully, toast shown |
| 7.5 | Click **Preview Store** | Opens `/store/demo-shop` in new tab |
| 7.6 | Copy store link | Clipboard copy works |

---

## 8. AI Tools Flow

| Step | What to do | Expected |
|---|---|---|
| 8.1 | Go to `/ai-tools` | AI content tool UI loads |
| 8.2 | Select tool: **FB Post** | Tool configuration appears |
| 8.3 | Choose a product from the dropdown | Product selected |
| 8.4 | Click **Generate** | Content generated (AI or rule-based) |
| 8.5 | Click **Copy** | Text copied to clipboard |
| 8.6 | Try tool: **Daily Action** | Generates daily seller action plan |

---

## 9. AI Agents Flow

| Step | What to do | Expected |
|---|---|---|
| 9.1 | Go to `/agents` | Agent card list visible |
| 9.2 | Click **Run** on "Sales Analyzer" agent | Agent runs, results shown |
| 9.3 | Expand results | Insights panel shows metrics and suggestions |
| 9.4 | Run another agent (e.g. Inventory Monitor) | Separate insights shown |

---

## 10. Buyer / Public Store Flow

| Step | What to do | Expected |
|---|---|---|
| 10.1 | Go to `http://localhost:3000/marketplace` | Marketplace page loads with Demo Shop card |
| 10.2 | Click on the Demo Shop card | Opens `/store/demo-shop` |
| 10.3 | Browse products — search for "shirt" | Filtered products appear |
| 10.4 | Click category chips to filter | Products filter by category |
| 10.5 | Click **Add to Cart** on any product | Toast: "Added to cart" |
| 10.6 | Add 2-3 more products | Cart count in header increases |
| 10.7 | Click the cart icon → go to `/cart` | Cart page shows all items |
| 10.8 | Change quantity or remove an item | Cart updates |
| 10.9 | Click **Proceed to Checkout** | Checkout form appears |
| 10.10 | Fill in name, phone, address → Place Order | Success screen with order number |
| 10.11 | Note the order number → go to `/track-order` | Enter order number → tracking shown |

---

## 11. Analytics Flow

| Step | What to do | Expected |
|---|---|---|
| 11.1 | Go to `/analytics` | Analytics page loads |
| 11.2 | Check 30-day revenue chart | Chart renders with data |
| 11.3 | Check order breakdown by status | Pie/bar chart visible |

---

## Integration Flow (Mock Mode)

These flows work in mock mode — no real API credentials needed.

| Step | What to do | Expected |
|---|---|---|
| I.1 | Go to `/integrations` | Integration hub page |
| I.2 | View Courier section | Pathao, Steadfast, REDX shown as "Mock Mode" |
| I.3 | View Payment section | bKash, Nagad, SSLCommerz shown as "Mock Mode" |

---

## Bug Report Format

If something fails, report it using this format:

```
Page: /store-builder
Steps: Navigated to /store-builder → waited 10 seconds
Expected: Store form loads
Actual: Stuck on "Loading store settings..."
Error (console): TypeError: Cannot read property 'merchant' of undefined
Severity: Major
```

Fill in [FEEDBACK_TEMPLATE.md](FEEDBACK_TEMPLATE.md) and send to fokrulanthro16@gmail.com.

---

## What NOT to Test

- Do not attempt real payment flows with live bKash/Nagad/SSLCommerz credentials — beta uses mock mode
- Do not attempt real courier bookings — all tracking IDs are simulated
- Do not upload large files (>5MB) — storage is base64 local mode during beta
