# SellerMate AI — Release Checklist

Use this checklist before tagging any public release.

---

## Pre-Release: Code & Security

- [ ] `git status` is clean — no uncommitted changes
- [ ] No `.env` or `.env.local` files are tracked (`git ls-files | grep "\.env$"` returns nothing)
- [ ] No real API keys, tokens, or passwords committed in source code
- [ ] All `.env.example` files are up to date with current variables
- [ ] TypeScript builds without errors (`cd apps/web && npx tsc --noEmit`)
- [ ] No `console.log` secrets or debug dumps in committed files
- [ ] `.gitignore` covers: `.env`, `.env.local`, `.venv/`, `node_modules/`, `.next/`, `__pycache__/`, `*.log`, `*.tsbuildinfo`

---

## Pre-Release: Backend

- [ ] Backend starts cleanly: `uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`
- [ ] Health check passes: `GET /api/v1/health` → `{"status":"ok"}`
- [ ] Database component is `"ok"` in health response
- [ ] All Alembic migrations applied: `alembic upgrade head` runs without errors
- [ ] `seed_demo.py` runs without errors (creates demo account)
- [ ] `seed_beta.py` runs without errors (populates 90+ products, 50+ orders)
- [ ] Demo login works: `POST /api/v1/auth/login` with `demo@sellermate.ai` / `Demo1234!` returns JWT
- [ ] Merchant profile loads: `GET /api/v1/merchant/me` returns `store_slug: "demo-shop"`
- [ ] Public store products load: `GET /api/v1/public/stores/demo-shop/products?limit=5` returns products
- [ ] Public checkout works: `POST /api/v1/public/orders` returns order number

---

## Pre-Release: Frontend

- [ ] `npm install` completes without errors
- [ ] `npm run dev` starts on port 3000 (or next available)
- [ ] `.env.local` contains `NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1`
- [ ] `http://localhost:3000` redirects to `/login` (unauthenticated) or `/dashboard` (authenticated)

---

## Functional Verification

Walk through this checklist in the browser:

### Seller Flow
- [ ] `/login` — "ডেমো হিসেবে ঢুকুন" button enters dashboard
- [ ] `/dashboard` — 6 KPI cards visible, recent orders table loads
- [ ] `/orders` — order list loads with filters, status update works
- [ ] `/products` — product list with 90+ items, search works
- [ ] `/inventory` — stock levels visible, low-stock items highlighted
- [ ] `/customers` — customer list with 20+ entries
- [ ] `/analytics` — charts render with data
- [ ] `/store-builder` — form loads (not stuck on "Loading store settings...")
- [ ] `/ai-tools` — select tool → generate content → copy button works
- [ ] `/agents` → click Run on Commerce Agent → results appear

### Buyer Flow
- [ ] `/marketplace` — Demo Shop card visible
- [ ] `/store/demo-shop` — products load, category chips filter, search works
- [ ] Add to cart → cart count badge increments
- [ ] `/cart` — items visible, quantity change works, remove works
- [ ] `/checkout` — fill form → Place Order → order number shown in success screen
- [ ] `/track-order` → enter order number → tracking steps displayed

### AI & System
- [ ] `/ai-tools` works without any AI API key (rule-based fallback)
- [ ] `/agents` — at least one agent runs and returns insights
- [ ] Sidebar health indicator shows "All systems OK" (not "Connecting...")
- [ ] Language toggle (Bangla ↔ English) works in sidebar

---

## Documentation

- [ ] README.md is current and accurate
- [ ] Troubleshooting section covers all known setup issues
- [ ] BETA_NOTES.md correctly describes what is mocked vs real
- [ ] TESTING_GUIDE.md covers all 11 key pages
- [ ] FEEDBACK_TEMPLATE.md is clear and easy to fill in
- [ ] TESTER_MESSAGE.md has a short WhatsApp-ready version
- [ ] RELEASE_NOTES.md describes what's new in this version
- [ ] CHANGELOG.md is up to date
- [ ] Issue templates exist in `.github/ISSUE_TEMPLATE/`

---

## GitHub Release

- [ ] All commits pushed: `git push origin main`
- [ ] Release tag created and pushed: `git push origin v0.9-beta`
- [ ] GitHub Release drafted at: Releases → Draft a new release
  - Tag: `v0.9-beta`
  - Title: `SellerMate AI v0.9-beta — Public Beta`
  - Body: paste from `RELEASE_NOTES.md`
- [ ] Release published (not draft)

---

## Tester Communication

- [ ] Tester list confirmed (5–10 people)
- [ ] TESTER_MESSAGE.md short version sent via WhatsApp/Messenger
- [ ] Full email sent with setup instructions to each tester
- [ ] Feedback collection method confirmed (email or GitHub Issues)
- [ ] Testers have been told: payments and courier are mocked, no real money involved

---

## Post-Release Monitoring

- [ ] Backend stays up for at least 1 hour under tester load
- [ ] No `500 Internal Server Error` responses in backend logs
- [ ] First round of feedback received and triaged
- [ ] Critical bugs (if any) hot-fixed and a patch tag created (e.g. `v0.9.1-beta`)
