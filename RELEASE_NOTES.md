# SellerMate AI — Release Notes

## v0.9-beta (2026-06-26)

**Public Beta Release**

---

### What This Release Is

v0.9-beta is the first release of SellerMate AI made available to external testers. It represents a feature-complete seller operations platform for Bangladeshi e-commerce sellers, with the full buyer-side shopping experience included.

This release is for **feedback and testing only**. Payments, courier bookings, and OTP delivery are all simulated. No real money moves. No real shipments are created.

---

### What's New Since Phase 7

#### Complete Buyer-Side Experience
- **Marketplace** (`/marketplace`) — public store listing, search, hero section
- **Store Page** (`/store/demo-shop`) — 90+ products, category filters, image gallery
- **Cart** (`/cart`) — add/remove items, quantity control, persistent across sessions
- **Checkout** (`/checkout`) — COD form, address capture, mock payment gateway
- **Order Tracking** (`/track-order`) — track by order number with visual progress

#### Seller Store Builder
- `/store-builder` — set store name, slug, description, logo, banner, contact
- Live status indicator (store is live / private)
- Launch checklist with percentage completion
- Copy store link to clipboard
- **Bug fixed:** page no longer gets stuck on "Loading store settings..." when the API errors — now always renders with graceful fallback

#### Demo Mode
- "ডেমো হিসেবে ঢুকুন" button on login and register — always enters the app even if API is unreachable
- Demo account pre-seeded with 90+ products, 50+ orders, 20+ customers
- Fixed demo password to match seed script (`Demo1234!`)

#### AI Agents Dashboard
- `/agents` — run business intelligence agents from the seller dashboard
- Sales Analyzer, Inventory Monitor, Demand Forecaster, Trust Score, Campaign Planner

---

### Demo Credentials

```
Email:    demo@sellermate.ai
Password: Demo1234!
Store:    http://localhost:3000/store/demo-shop
```

---

### Known Issues in v0.9-beta

- Image uploads are base64 local (no CDN) — large images may be slow
- OTP not delivered by SMS — OTP appears in backend console only
- Multi-tenant not yet implemented — single merchant per install
- Mobile app not yet available
- AI content requires an API key for real generation; rule-based fallback is used otherwise

---

### How to Run

```bash
# Infrastructure (PostgreSQL + Redis)
docker-compose up -d postgres redis

# Backend
cd apps/api
cp .env.example .env          # edit APP_SECRET_KEY, DATABASE_URL, REDIS_URL
pip install -r requirements.txt
alembic upgrade head
python scripts/seed_demo.py
python scripts/seed_beta.py
.venv/Scripts/python.exe -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Frontend (new terminal)
cd apps/web
cp .env.local.example .env.local
npm install
npm run dev
```

Open `http://localhost:3000` → click **"ডেমো হিসেবে ঢুকুন"**

---

### Feedback

Use [FEEDBACK_TEMPLATE.md](FEEDBACK_TEMPLATE.md) and send to **fokrulanthro16@gmail.com**
or open a GitHub Issue using the provided templates.

See [TESTING_GUIDE.md](TESTING_GUIDE.md) for full test flows.
See [BETA_NOTES.md](BETA_NOTES.md) for details on what is mocked vs real.

---

### What Comes After Beta

Phase 12 roadmap:
- Live payment gateway integration (bKash, SSLCommerz)
- Live courier booking (Pathao, Steadfast)
- Real OTP delivery via SMS
- Multi-merchant / SaaS mode
- Mobile app (React Native)
- Persistent file storage (S3/R2)
