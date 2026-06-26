# SellerMate AI — Tester Message

---

## SHORT VERSION (WhatsApp / Messenger)

> Copy from the line below and send as-is.

---

SellerMate AI বেটা টেস্ট করার জন্য ধন্যবাদ! 🙏

**রেপো:** https://github.com/YOUR_USERNAME/sellermate

**চালু করতে (১০ মিনিট):**

```
# Step 1 — ডাটাবেজ চালু করুন (Docker লাগবে)
docker-compose up -d postgres redis

# Step 2 — ব্যাকএন্ড
cd apps/api
python -m venv .venv
.venv\Scripts\Activate.ps1        ← Windows
# source .venv/bin/activate       ← Mac/Linux
pip install -r requirements.txt
cp .env.example .env              ← APP_SECRET_KEY সেট করুন
alembic upgrade head
python scripts/seed_demo.py
python scripts/seed_beta.py
.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Step 3 — ফ্রন্টএন্ড (নতুন টার্মিনালে)
cd apps/web
cp .env.local.example .env.local
npm install && npm run dev
```

**ব্রাউজারে:** http://localhost:3000
**লগইন:** demo@sellermate.ai / Demo1234!
**অথবা:** "ডেমো হিসেবে ঢুকুন" বাটনে ক্লিক করুন

**টেস্ট করুন:**
- Dashboard, Orders, Products, Store Builder
- Marketplace → demo-shop → Cart → Checkout
- AI Tools, AI Agents

**⚠️ মনে রাখুন:** পেমেন্ট/কুরিয়ার সব মক — কোনো আসল টাকা কাটবে না।

**ফিডব্যাক:** fokrulanthro16@gmail.com
**Subject:** [SellerMate Beta] Feedback — আপনার নাম

সমস্যা হলে README.md → Troubleshooting দেখুন।

---

## FULL EMAIL VERSION

**Subject:** SellerMate AI Beta v0.9 — Setup & Testing Instructions

---

Hi [Name],

Thanks for agreeing to test **SellerMate AI** — our AI-powered commerce OS for Bangladeshi e-commerce sellers.

This is a pre-release beta. Your feedback will directly shape the product.

---

### What You're Testing

SellerMate is a single seller dashboard that handles orders, products, inventory, customers, analytics, AI content generation, and a public storefront — all in one place.

The demo account has 90+ products, 50+ orders, and 20+ customers already loaded.

---

### Step 1 — Clone the Repo

```bash
git clone https://github.com/YOUR_USERNAME/sellermate.git
cd sellermate
```

---

### Step 2 — Start the Database (Docker required)

```bash
docker-compose up -d postgres redis
```

Don't have Docker? Install from https://www.docker.com/products/docker-desktop/

---

### Step 3 — Set Up the Backend

```bash
cd apps/api
python -m venv .venv

# Windows (PowerShell):
.venv\Scripts\Activate.ps1
# Mac / Linux:
source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
```

Open `apps/api/.env` and set this minimum:
```
APP_SECRET_KEY=any-64-char-random-string
DATABASE_URL=postgresql+asyncpg://sellermate:password@localhost:5432/sellermate
REDIS_URL=redis://localhost:6379/0
```

Generate a key: `python -c "import secrets; print(secrets.token_hex(32))"`

```bash
alembic upgrade head
python scripts/seed_demo.py
python scripts/seed_beta.py

# Start backend:
# Windows:
.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
# Mac/Linux:
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Verify it's running: http://localhost:8000/api/v1/health → should return `{"status":"ok"}`

---

### Step 4 — Set Up the Frontend (New Terminal)

```bash
cd apps/web
cp .env.local.example .env.local
npm install
npm run dev
```

Open http://localhost:3000

If port 3000 is busy, Next.js will use 3001, 3002, etc. — check your terminal.

---

### Demo Credentials

```
Email:    demo@sellermate.ai
Password: Demo1234!
```

Or just click **"ডেমো হিসেবে ঢুকুন"** on the login page — it logs in automatically.

Demo Store: http://localhost:3000/store/demo-shop

---

### What to Test

**Seller side (after login):**
- [ ] Dashboard — KPI cards, recent orders, AI action suggestions
- [ ] Orders — list, filter, status update
- [ ] Products — browse, add, edit
- [ ] Inventory — stock levels, low-stock alerts
- [ ] Store Builder — edit store details, preview store
- [ ] AI Tools — generate Facebook post, caption, hashtags
- [ ] AI Agents — run Commerce Agent, check results

**Buyer side (no login needed):**
- [ ] `/marketplace` — see Demo Shop listed
- [ ] `/store/demo-shop` — browse products, filter by category, search
- [ ] Add to cart → adjust quantity → go to `/cart`
- [ ] Checkout → fill form → place order → note order number
- [ ] `/track-order` → enter order number → see tracking

---

### Important — What's Mocked

| Feature | Beta Status |
|---|---|
| Payments (bKash, Nagad) | Simulated — no real charge |
| Courier (Pathao, Steadfast) | Fake tracking ID — no real parcel |
| OTP / SMS | OTP printed to backend console only |
| AI content | Works without API key (rule-based fallback) |

**No real money moves. Test freely.**

---

### How to Submit Feedback

Fill in the bug report template (see `FEEDBACK_TEMPLATE.md` in the repo) and:

- **Email:** fokrulanthro16@gmail.com
- **Subject:** `[SellerMate Beta] Feedback — [Your Name]`
- Or open a **GitHub Issue** using the `bug_report` / `ui_feedback` / `feature_request` template

---

### Stuck? Check the README Troubleshooting Section

The README has fixes for all common setup issues:
- Backend not running
- Port conflict
- Demo login failing
- Empty dashboard (missing seed data)
- Store Builder stuck loading

---

Thank you again — your feedback makes SellerMate better for every seller in Bangladesh.

— Fokrul / SellerMate AI Team
