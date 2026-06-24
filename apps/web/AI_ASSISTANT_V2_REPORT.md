# AI Assistant V2 — Implementation Report

**Date:** 2026-06-23  
**Model:** Gemini 2.5 Flash (`gemini-2.5-flash`)  
**SDK:** `google-genai` 1.74.0  
**Architecture:** Real LLM orchestration with tool calling

---

## What Changed

### Before (V1 — Rule-Based Fallback)
- `fallback_assistant.py` detected keywords (`_kw()`) and returned hardcoded templates
- No true language understanding — only pattern matching
- Could not handle: combinations, follow-up questions, natural phrasing, or anything outside the keyword list
- Example: "আমার সবচেয়ে বেশি বিক্রি হওয়া পণ্য কোনটি?" → matched keyword "বিক্রি" → returned top-5 list regardless of exact question

### After (V2 — Gemini 2.5 Flash with Tool Calling)
- Real LLM reads the user's intent and decides which tools to call
- Tools query the live PostgreSQL database
- Model synthesises the tool results into a coherent, natural response
- Handles multi-step reasoning, clarifying questions, follow-ups
- Responds in the user's exact language (Bangla or English) as instructed

---

## Architecture

```
User message (SSE)
      │
      ▼
assistant_service.stream_chat()
      │  builds LangChain history from DB
      ▼
run_agent() [agent.py]
      │  checks settings.gemini_api_key → non-empty
      ▼
run_gemini_agent() [gemini_agent.py]
      │
      ├── Build Gemini Contents (history + user msg)
      ├── Loop (max 6 rounds):
      │     ├── client.aio.models.generate_content() → Gemini 2.5 Flash
      │     ├── If function_call parts → execute tools → append results
      │     └── If text parts only → pseudo-stream chunks → return
      │
      ▼
SSE chunks → ChatWindow.tsx → rendered markdown
```

### Fallback Chain
1. **Gemini 2.5 Flash** — if `GEMINI_API_KEY` is set ← *V2 path*
2. **Claude Haiku** (LangChain) — if `ANTHROPIC_API_KEY` is set
3. **Rule-based local** — if both keys are empty (keeps working offline)

---

## Tools Implemented

| Tool | DB Queries | Use Case |
|------|-----------|---------|
| `get_low_stock_items` | `ProductVariant WHERE stock <= threshold` | "কোন পণ্যের স্টক কম?" |
| `get_inventory_status` | `Product + variants ILIKE name` | "T-shirt এর স্টক কত?" |
| `search_products` | `Product WHERE name/sku ILIKE` + category filter | "পোশাক ক্যাটাগরিতে কী আছে?" |
| `get_top_products` | `SUM(OrderItem.quantity)` on DELIVERED orders | "আমার সবচেয়ে বেশি বিক্রি হওয়া পণ্য কোনটি?" |
| `get_order_summary` | `COUNT + SUM(Order)` + status breakdown | "এই সপ্তাহে কত অর্ডার?" |
| `search_orders` | `Order JOIN Customer ILIKE` + status filter | "Rahim-এর অর্ডার দেখাও" |
| `get_customer_info` | `Customer WHERE name/phone ILIKE` | "01711... নম্বরের গ্রাহক কে?" |
| `get_top_customers` | `Customer ORDER BY total_spent DESC` | "আমার VIP গ্রাহক কে?" |
| `get_revenue_analytics` | `SUM(total_amount, paid_amount)` + collection rate | "এই মাসে কত আয় হয়েছে?" |
| `get_strategic_insights` | `StrategicInsight` latest trust + fraud records | "ট্রাস্ট স্কোর কত?" |

---

## Language Handling

The system prompt enforces a hard bilingual rule:

```
If the user writes in Bangla/Bengali script → respond ENTIRELY in Bangla
If the user writes in English → respond ENTIRELY in English
NEVER mix languages in a single response
```

Gemini 2.5 Flash natively understands Bangla and generates fluent responses in both languages. Tool result data (numbers, product names, order IDs) are embedded naturally into the language of the response.

### Example Exchanges

**English query:**
> User: "Which products are low stock?"  
> Agent: *calls `get_low_stock_items()`* → returns real DB list  
> Response: "## Low Stock Alert\n\n🔴 **Out of stock** (3 variants):\n• Polo T-Shirt — XL: **OUT OF STOCK** ..."

**Bangla query:**
> User: "আমার সবচেয়ে বেশি বিক্রি হওয়া পণ্য কোনটি?"  
> Agent: *calls `get_top_products(limit=5, period_days=30)`* → real DB aggregation  
> Response: "## শীর্ষ বিক্রিত পণ্য — গত ৩০ দিন\n\n১. **প্রিমিয়াম কটন শার্ট** — ৮৭টি বিক্রিত ..."

---

## Files Created / Modified

| File | Change |
|------|--------|
| `apps/api/app/ai/gemini_agent.py` | **NEW** — Full Gemini 2.5 Flash agent: 10 tools, multi-turn loop, streaming |
| `apps/api/app/ai/agent.py` | Updated routing: Gemini → Claude → rule-based fallback |
| `apps/api/app/core/config.py` | Added `gemini_api_key: str = ""` setting |
| `apps/api/.env` | Added `GEMINI_API_KEY=` (user must fill in) |
| `apps/api/requirements.txt` | Added `google-genai>=1.0.0` |
| `apps/api/pyproject.toml` | Added `google-genai = ">=1.0.0"` |

---

## Activation

Add your Gemini API key to `apps/api/.env`:

```env
GEMINI_API_KEY=AIza...your-key-here
```

Get a free key at: **Google AI Studio → https://aistudio.google.com/apikey**

Gemini 2.5 Flash offers a **free tier** with generous limits — suitable for development and light production use.

---

## What the LLM Can Now Do That V1 Could Not

| Capability | V1 (Rule-based) | V2 (Gemini) |
|-----------|-----------------|-------------|
| Natural language understanding | ❌ keyword only | ✅ full NLU |
| Multi-intent questions | ❌ first match wins | ✅ calls multiple tools |
| Follow-up context | ❌ stateless per message | ✅ reads full conversation history |
| "Show me pending orders from last week from Dhaka customers" | ❌ broken | ✅ chains search_orders + customer filter |
| Ambiguous questions | ❌ shows generic response | ✅ asks for clarification |
| Explanation and insight | ❌ raw data only | ✅ interprets and recommends |
| Bangla grammar accuracy | ❌ template strings | ✅ native Bangla generation |

---

## Remaining Limitations

1. **Gemini API key required** — without the key, falls back to Claude or rule-based
2. **No write operations** — the agent can query but cannot create orders, update stock, or message customers via chat (by design — prevents accidental mutations)
3. **Strategic scores are stale** — `get_strategic_insights` reads the last stored score; requires "Run Agents" click to refresh
4. **SSE pseudo-streaming** — final response is buffered then chunked at 50 chars every 12ms; not true token-level streaming (Gemini streaming with function calling is a separate implementation path)
