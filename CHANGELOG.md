# Changelog

All notable changes to SellerMate AI are documented here.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [0.9-beta] — 2026-06-26

### Added — Public Buyer Side
- Marketplace page (`/marketplace`) with store listing and search
- Public store page (`/store/[slug]`) with category chips, product grid, and search
- Shopping cart with localStorage persistence and real-time count badge
- Checkout form with COD and mock payment gateway support
- Order tracking page (`/track-order`) with progress indicator
- `CartContext` for cross-page cart state

### Added — Seller Dashboard
- Store Builder page (`/store-builder`) — logo, banner, slug, contact, description
- Launch checklist widget with percentage completion
- AI Agents page (`/agents`) with runnable business intelligence agents
- System deployment page (`/system/deployment`)
- Mobile bottom navigation bar

### Added — Infrastructure & Integrations
- Courier client modules: Pathao, Steadfast, REDX (real API + mock fallback)
- Payment client modules: bKash, Nagad, SSLCommerz (real API + mock fallback)
- Public API router (`/api/v1/public/...`) — unauthenticated store and order endpoints
- Media upload router (`/api/v1/media/upload`)
- Agents router (`/api/v1/agents/...`)
- Alembic migration: `e6f7a8b9c0d1` — public store fields on merchant model
- `Dockerfile` for both API and web services
- `docker-compose.prod.yml` for full production stack

### Added — Auth & Demo Mode
- Demo login bypass: "ডেমো হিসেবে ঢুকুন" button on login and register pages
- `enterDemoMode()` — tries real login → register → login → synthetic local session
- `isDemoMode()` / `setDemoMode()` in `auth.ts`
- API client: demo mode guard suppresses 401 toasts and redirect loops
- Demo credentials fixed: `Demo1234!` (matches seed script)

### Added — Documentation & Beta Prep
- `README.md` — full rewrite with setup guide, env vars, checklist, roadmap
- `TESTING_GUIDE.md` — 11-section step-by-step test flows
- `FEEDBACK_TEMPLATE.md` — structured bug report template
- `BETA_NOTES.md` — explains mock mode, demo data, real API upgrade path
- `RELEASE_NOTES.md` — v0.9-beta release summary
- `.github/ISSUE_TEMPLATE/` — bug_report, ui_feedback, feature_request templates
- `apps/api/.env.production.example` — full production environment template
- `apps/web/.env.local.example`
- `*.tsbuildinfo` added to `.gitignore`; TypeScript build artifact untracked

### Fixed
- Store Builder stuck on "Loading store settings..." when merchant query errors — added `isError` fallback that initialises the form with empty defaults
- Sidebar health indicator permanently showing "Connecting..." after query error — fixed by separating `healthLoading` vs `healthError` states
- Marketplace double `/api/v1` URL prefix bug in `usePublicStore.ts`
- Track-order page hardcoded base URL causing double API prefix
- Demo login password mismatch (`Demo@123456` → `Demo1234!`)
- Store page TypeScript error in category chip replace callback
- `useCallback` and `useRouter` unused imports removed from store-builder page

### Changed
- `useStoreProducts` default limit raised from 24 to 100
- `tsconfig.tsbuildinfo` removed from git tracking (build artifact)
- All root-level and app-level `*.log` files deleted from workspace

---

## [0.8.x] — Phase 7: Connector Readiness (2026-06-25)

- Webhook handlers for Pathao, Steadfast, REDX, SSLCommerz, bKash, Nagad, Daraz, Shopify
- HMAC signature verification for all courier and payment webhooks
- Backup and restore router
- Commerce engine updates

## [0.7.x] — Phase 6: Production Foundation (2026-06-24)

- PostgreSQL async connection pooling
- Redis queue integration
- Alembic migration pipeline
- Health check endpoint with component status
- CORS hardening
- Production `.env` template

## [0.6.x] — Phase 5: Integration Foundation (2026-06-23)

- Courier integration layer (Pathao, Steadfast, REDX, Manual)
- Payment integration layer (SSLCommerz, bKash, Nagad, COD)
- Marketplace integration (Facebook, Daraz, Shopify)
- WhatsApp Cloud API notification channel
- SMS and email notification channels

## [0.5.x] — Phase 4 and earlier

- Core seller dashboard: orders, products, inventory, customers, analytics
- AI tools: Facebook post, caption, hashtag, product description, offer text
- Trust and safety engine: fraud detection, trust score
- Strategic AI agents: sales analyzer, inventory monitor, demand forecaster
- Bangla/English bilingual UI with language toggle
- JWT auth with refresh token rotation
