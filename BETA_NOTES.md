# SellerMate AI — Beta Notes

> **This is a public beta build. Not for production use.**

---

## What "Beta" Means

SellerMate AI is feature-complete enough for real sellers to evaluate and test. All core seller flows work. However, some integrations run in **mock mode** by default — meaning no real money moves and no real courier bookings are created until you supply live API credentials.

---

## Mock Mode — What Is Simulated

| Feature | Beta Behaviour |
|---|---|
| **Payments** (bKash, Nagad, SSLCommerz) | Simulated — no real charge, no real gateway redirect |
| **Courier booking** (Pathao, Steadfast, REDX) | Simulated — tracking IDs are generated locally, no parcel created |
| **SMS / OTP** | Simulated — OTP is logged to the console, not sent via SMS |
| **Email notifications** | Simulated — printed to backend logs unless SMTP is configured |
| **WhatsApp** | Simulated — messages are logged, not sent |
| **AI content generation** | Works with Gemini / Claude / OpenAI if keys are set; falls back to rule-based templates if not |
| **File uploads (images)** | Stored as base64 locally — works for testing; configure S3/R2 for persistence |

---

## Demo Data Included

The demo account comes pre-loaded with:

- **90+ products** across multiple categories (fashion, electronics, home goods, etc.)
- **20+ customers** with realistic profiles
- **50+ orders** in various statuses (Pending, Confirmed, Shipped, Delivered, Cancelled)
- **Inventory history** and reorder levels
- **Launch checklist** at 100% completion

All demo data is seeded via `scripts/seed_beta.py`.

---

## Real APIs (When You're Ready)

Set these in `apps/api/.env` to unlock live integrations:

```
# Payments
SSLCOMMERZ_STORE_ID=...
BKASH_APP_KEY=...
NAGAD_MERCHANT_ID=...

# Courier
PATHAO_CLIENT_ID=...
STEADFAST_API_KEY=...
REDX_API_KEY=...

# AI
GEMINI_API_KEY=...
ANTHROPIC_API_KEY=...
```

See `apps/api/.env.example` for the full list of available variables.

---

## No Real Money Movement

**Important:** During beta, all payment flows complete with a simulated success response. No charges are made to any card or mobile wallet. Do not use real customer payment credentials during beta testing.

---

## No Real Courier Booking

Courier bookings during beta generate a fake tracking number (format: `MOCK-XXXXXXXX`). No parcel is created with Pathao, Steadfast, or REDX.

---

## Known Limitations in This Beta

- Image uploads are stored as base64 in the database (not an external CDN). Large images may slow responses.
- AI features fall back to rule-based content if no AI API key is provided.
- OTP-based phone verification sends OTP to the backend console, not your phone.
- Multi-merchant mode is not yet implemented — each install is single-merchant.
- The mobile app is not yet available.

---

## Feedback

Please use [FEEDBACK_TEMPLATE.md](FEEDBACK_TEMPLATE.md) to report bugs and suggestions.
