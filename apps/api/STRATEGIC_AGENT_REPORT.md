# Strategic Agent Layer Report

**Date:** 2026-06-22  
**Module:** Strategic Agents (`/api/v1/ai/strategic`)  
**Status:** PASS — 34/34 tests green

---

## Summary

New strategic agent layer built on top of the existing analytics and order data.
Two intelligent agents (TrustGraph and FraudSentinel) analyse merchant data and
persist scored insights to the new `strategic_insights` table. Four REST endpoints
expose the agent results.

---

## Architecture

```
app/
├── ai/
│   └── strategic_agents/
│       ├── __init__.py
│       ├── trust_graph.py      ← TrustGraph agent
│       └── fraud_sentinel.py   ← FraudSentinel agent
├── models/
│   └── strategic_insight.py    ← StrategicInsight ORM model
├── schemas/
│   └── strategic.py            ← Pydantic response schemas
├── services/
│   └── strategic_service.py    ← Orchestration + DB persistence
└── routers/
    └── strategic.py            ← 4 REST endpoints
alembic/versions/
└── c3d4e5f6a7b8_strategic_insights.py  ← Migration
```

---

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/ai/strategic/run` | Run both agents, persist insights |
| GET | `/api/v1/ai/strategic/insights` | List stored insights (filterable) |
| GET | `/api/v1/ai/strategic/trust-score` | Latest trust score for merchant |
| GET | `/api/v1/ai/strategic/fraud-report` | Latest fraud report for merchant |

---

## Agents

### TrustGraph
Computes merchant trust score (0–100) and confidence level (LOW/MEDIUM/HIGH).

**Scoring factors:**
- **+20** delivery rate ≥ 80%, **+10** ≥ 50%, **−0** otherwise + `LOW_DELIVERY_RATE` flag
- **+15** payment collection rate ≥ 70%, **+7** ≥ 40%, otherwise + `LOW_PAYMENT_COLLECTION` flag
- **+15** customer retention ≥ 30%, **+7** ≥ 10%
- **−25** cancellation rate > 40% + `HIGH_CANCELLATION_RATE` flag
- **−10** cancellation rate > 20% + `ELEVATED_CANCELLATION_RATE` flag

**Confidence tiers:**
- `LOW` — < 10 total orders
- `MEDIUM` — 10–49 orders
- `HIGH` — 50+ orders

**Output:** `trust_score`, `confidence`, `risk_flags`, `details` (all rates)

### FraudSentinel
Scans the last 30-day window for anomalous order patterns.

**Detection rules:**
- **+40** cancellation rate > 50% → `CANCELLATION_SPIKE`
- **+20** cancellation rate > 30% → `HIGH_CANCELLATION_RATE`
- **+25** ≥ 5 unpaid orders older than 7 days → `STALE_UNPAID_ORDERS`
- **+10** 2–4 stale unpaid orders → `UNPAID_ORDER_ACCUMULATION`
- **+25** single-day spike ≥ 5× daily average (min 10 orders) → `ORDER_SPIKE`

**Output:** `fraud_risk_score`, `alert_reasons`, `details` (window stats)

---

## Data Model

### `StrategicInsight` table (`strategic_insights`)

| Column | Type | Description |
|--------|------|-------------|
| `id` | VARCHAR(36) | UUID primary key |
| `merchant_id` | VARCHAR(36) | FK → merchants.id (CASCADE DELETE) |
| `agent_name` | VARCHAR(64) | `trust_graph` or `fraud_sentinel` |
| `score` | INTEGER | Agent's primary score (0–100) |
| `payload` | JSON | Full agent result including details |
| `created_at` | TIMESTAMPTZ | Auto-set server default |

**Indexes:** merchant_id, (merchant_id, agent_name), (merchant_id, created_at)

---

## Test Suite Results

```
tests/test_strategic.py — 34 passed in 157s
```

| Class | Tests | Result |
|-------|-------|--------|
| TestJWTProtection | 4 | PASS |
| TestRunAgents | 9 | PASS |
| TestListInsights | 6 | PASS |
| TestTrustScore | 4 | PASS |
| TestFraudReport | 4 | PASS |
| TestTrustScoringLogic | 3 | PASS |
| TestMerchantIsolation | 4 | PASS |
| **TOTAL** | **34** | **PASS** |

---

## Coverage Details

### JWT Protection
All 4 endpoints return 401 without Authorization header ✓

### POST /run
- Returns 200 with `trust`, `fraud`, `insights_saved` ✓
- Trust schema: trust_score, confidence, risk_flags, details ✓
- Fraud schema: fraud_risk_score, alert_reasons, details ✓
- trust_score in [0, 100] ✓
- fraud_risk_score in [0, 100] ✓
- confidence is LOW | MEDIUM | HIGH ✓
- insights_saved = 2 (one per agent) ✓
- Good merchant (3 delivered/paid orders) scores above 50 ✓

### GET /insights
- Empty list before any run ✓
- Populated with 2+ entries after run ✓
- Schema: id, agent_name, score, payload, created_at ✓
- `agent_name=trust_graph` filter works ✓
- `agent_name=fraud_sentinel` filter works ✓
- `limit` parameter respected ✓

### GET /trust-score
- 404 before any run ✓
- 200 after run, agent_name=trust_graph ✓
- payload contains trust_score ✓

### GET /fraud-report
- 404 before any run ✓
- 200 after run, agent_name=fraud_sentinel ✓
- payload contains fraud_risk_score ✓

### Trust Scoring Logic
- New merchant with no orders → confidence=LOW ✓
- Details contain all rate metrics ✓
- risk_flags is always a list ✓

### Merchant Isolation
- Merchant B cannot see Merchant A's insights ✓
- Merchant B gets 404 on trust-score when only A has run ✓
- Merchant B gets 404 on fraud-report when only A has run ✓
- Running twice accumulates insights (min 4 records) ✓

---

## Files Created

| File | Description |
|------|-------------|
| `app/ai/strategic_agents/__init__.py` | Package init |
| `app/ai/strategic_agents/trust_graph.py` | TrustGraph agent |
| `app/ai/strategic_agents/fraud_sentinel.py` | FraudSentinel agent |
| `app/models/strategic_insight.py` | StrategicInsight ORM model |
| `app/schemas/strategic.py` | Response schemas |
| `app/services/strategic_service.py` | Orchestration service |
| `app/routers/strategic.py` | 4-endpoint router |
| `alembic/versions/c3d4e5f6a7b8_strategic_insights.py` | DB migration |
| `tests/test_strategic.py` | 34-test integration suite |
