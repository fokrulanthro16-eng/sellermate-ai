# Package AI Engine Report

## Goal
Make SellerMate AI smarter without any external API key, without Ollama, and without inventing numbers.

---

## Packages Added

| Package | Version | Purpose |
|---------|---------|---------|
| `rapidfuzz` | ≥ 3.0.0 | Fuzzy intent matching (partial_ratio scorer) |
| `numpy` | ≥ 1.26.0 | Linear regression via `polyfit` for revenue trend |
| `scikit-learn` | ≥ 1.4.0 | Available for future ML scoring (not used in v1) |

All three are pure Python/C extensions — no Ollama, no LLM API required.

---

## Architecture

```
user message
     │
     ▼
intent_detector.py  ←── rapidfuzz partial_ratio against keyword bank
     │
     │  IntentResult{intent, confidence, lang}
     ▼
package_engine.py  ──  dispatches to response builder
     │
     ├── DB query helpers (real SQLAlchemy async queries)
     ├── _calc_trend()  ←── numpy polyfit slope
     └── _respond_*()  ──  bilingual Bangla + English output
```

### Agent routing in agent.py

```
Priority 1: GEMINI_API_KEY set  → Gemini 2.5 Flash (tool calling)
Priority 2: ANTHROPIC_API_KEY   → Claude Haiku (LangChain)
Priority 3: no key (default)    → Package Engine  ← NEW
```

---

## Intent Detection (`intent_detector.py`)

**Method**: rapidfuzz `process.extractOne` with `fuzz.partial_ratio` scorer, score_cutoff=55.

**Supported intents** (8 required + extras):

| Intent | Example triggers |
|--------|-----------------|
| `greeting` | হ্যালো, hello, hi, salam |
| `help` | সাহায্য, help, what can you do |
| `low_stock` | কম স্টক, low stock, inventory, স্টক শেষ |
| `top_products` | শীর্ষ পণ্য, best selling, most sold |
| `revenue_summary` | রাজস্ব, revenue, income, আয় |
| `order_summary` | অর্ডার, orders, pending orders |
| `best_customers` | শীর্ষ গ্রাহক, top customers, vip |
| `trust_score` | ট্রাস্ট স্কোর, trust score |
| `fraud_risk` | ফ্রড, fraud risk, suspicious |
| `restock_advice` | রিস্টক, what to restock, reorder |
| `growth_advice` | প্রবৃদ্ধি, grow business, strategy |
| `today_summary` | আজ, today, summary, overview |

Fallback: substring scan when rapidfuzz score < 55.
Default: `today_summary`.

---

## Package Engine (`package_engine.py`)

Each intent maps to a DB-backed response builder:

| Intent | Queries | Output |
|--------|---------|--------|
| `greeting` | none | Bilingual welcome + capabilities |
| `today_summary` | orders today + inventory alerts | Count, revenue, pending, stock status |
| `low_stock` | variants where stock ≤ low_stock_alert | Out/low counts + named item list |
| `top_products` | OrderItem JOIN delivered orders 30d | Top 5 by revenue + units |
| `revenue_summary` | daily sums → numpy slope | Revenue, AOV, trend label (Growing/Stable/Declining) |
| `order_summary` | status breakdown 7/30/90d | Total, revenue, by-status + cancellation warning |
| `best_customers` | Customer.total_spent desc | Total, repeat, retention %, top 5 names |
| `trust_score` | strategic_insights table | Score /100 + risk flags |
| `fraud_risk` | strategic_insights table | Score /100 + alert summary |
| `restock_advice` | low stock items + top products | Urgency-rated restock list |
| `growth_advice` | 30d vs prev 30d revenue + daily slope | MoM %, trend, retention, recommendations |

**Trend calculation** uses `numpy.polyfit(x, y, 1)`:
- `slope / mean_y > 0.05` → GROWING
- `slope / mean_y < -0.05` → DECLINING
- otherwise → STABLE

Pure-Python fallback (no numpy) is included for environments where numpy isn't installed.

---

## New Strategic Agents

### GrowthCoach (`growth_coach.py`)
**Score**: 0–100 (higher = stronger growth)

Signals:
- Revenue trend slope (numpy polyfit on 30 daily points)
- Month-over-month revenue change %
- Customer retention rate
- Top-product revenue concentration (diversification risk)

Recommendations emitted:
- `LAUNCH_PROMOTIONS` — declining trend or >10% MoM drop
- `IMPROVE_RETENTION` — retention < 15%
- `DIVERSIFY_PRODUCTS` — top product > 70% of revenue
- `EXPAND_PRODUCT_RANGE` — top product > 50% of revenue

### MarginGuardian (`margin_guardian.py`)
**Score**: 0–100 (higher = healthier margins), base 70

Signals:
- COD ratio (COD > 80% of orders → −20 pts, HIGH_COD_EXPOSURE)
- Return/refund rate (> 15% → −20 pts, HIGH_RETURN_RATE)
- Average discount depth (avg discount / avg subtotal)
- Total unpaid exposure (sum of due_amount on UNPAID orders)

Risk levels: LOW / MEDIUM / HIGH

### DemandOracle (`demand_oracle.py`)
**Score**: 0–100 (lower = more urgent restocking needed)

Algorithm:
```
velocity = units_delivered_last_30d / 30   (per variant)
days_left = current_stock / velocity
CRITICAL  if stock == 0 or days_left ≤ 3
HIGH      if 3 < days_left ≤ 7
MEDIUM    if 7 < days_left ≤ 14
LOW       otherwise
score = 100 − (CRITICAL_count × 20) − (HIGH_count × 10)
```

Returns: critical_items, high_items (up to 10 each), total_sku_tracked.

---

## Strategic Service Changes

`strategic_service.py` now runs **5 agents** in sequence:
1. TrustGraph
2. FraudSentinel
3. GrowthCoach
4. MarginGuardian
5. DemandOracle

All 5 results are stored in `strategic_insights` table under their respective `agent_name` values. `insights_saved` returns 5 instead of 2.

The `StrategicRunResult` schema was extended with optional `growth`, `margin`, `demand` fields.

---

## Response Quality

### Before (rule-based fallback)
- Hardcoded keyword matching (`"স্টক" in message`)
- No fuzzy tolerance — slight typos or alternate phrasings → wrong branch
- No trend calculation — only static counts
- 10 intents max

### After (package engine)
- rapidfuzz fuzzy matching — handles misspellings, partial phrases
- numpy polyfit slope → real trend detection from daily data
- 12 intent classes, both Bangla and English in one keyword bank
- Growth advice compares last 30d vs previous 30d from real DB
- Restock advice cross-references stock alerts + top-selling velocity
- Graceful degradation: no numpy → pure-Python slope fallback; no rapidfuzz → substring fallback

---

## Files Created / Modified

| File | Status |
|------|--------|
| `app/ai/intent_detector.py` | NEW |
| `app/ai/package_engine.py` | NEW |
| `app/ai/strategic_agents/growth_coach.py` | NEW |
| `app/ai/strategic_agents/margin_guardian.py` | NEW |
| `app/ai/strategic_agents/demand_oracle.py` | NEW |
| `app/ai/strategic_agents/__init__.py` | Updated — exports all 5 agents |
| `app/schemas/strategic.py` | Updated — 3 new output schemas + extended StrategicRunResult |
| `app/services/strategic_service.py` | Updated — runs 5 agents, saves 5 insights |
| `app/ai/agent.py` | Updated — Priority 3 now calls package_engine |
| `requirements.txt` | Updated — rapidfuzz, numpy, scikit-learn |
| `pyproject.toml` | Updated — same |

**Total: 5 new files, 6 updated files**

---

## No External Dependencies Required

- No Gemini API key
- No Anthropic API key
- No Ollama
- No internet connection at runtime
- All intelligence is deterministic + data-driven
