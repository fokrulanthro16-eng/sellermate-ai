# SellerMate AI — Beta Tester Welcome Message

> Copy this message and send it to your testers via WhatsApp, email, or Messenger.

---

**Subject: SellerMate AI Beta — আপনার টেস্টিং লিংক**

---

হ্যালো! 👋

SellerMate AI-এর বেটা ভার্সন টেস্ট করার জন্য আপনাকে স্বাগতম।

নিচের ইন্সট্রাকশন ফলো করুন — মাত্র ১০ মিনিটেই সব রেডি হয়ে যাবে।

---

**ধাপ ১: রেপো ক্লোন করুন**

```bash
git clone https://github.com/YOUR_USERNAME/sellermate.git
cd sellermate
```

---

**ধাপ ২: ব্যাকএন্ড চালু করুন**

```bash
# PostgreSQL + Redis (Docker দরকার)
docker-compose up -d postgres redis

# API সেটআপ
cd apps/api
python -m venv .venv

# Windows:
.venv\Scripts\Activate.ps1
# Mac/Linux:
# source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
```

`.env` ফাইলে এই ৩টা লাইন সেট করুন:

```
APP_SECRET_KEY=any-random-64-char-string-here
DATABASE_URL=postgresql+asyncpg://sellermate:password@localhost:5432/sellermate
REDIS_URL=redis://localhost:6379/0
```

```bash
alembic upgrade head
python scripts/seed_demo.py
python scripts/seed_beta.py

# Windows:
.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
# Mac/Linux:
# python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

ব্যাকএন্ড রেডি হলে দেখবেন: `http://localhost:8000/api/v1/health` → `{"status":"ok"}`

---

**ধাপ ৩: ফ্রন্টএন্ড চালু করুন** (নতুন টার্মিনালে)

```bash
cd apps/web
cp .env.local.example .env.local
npm install
npm run dev
```

ব্রাউজারে যান: `http://localhost:3000`

---

**ডেমো লগইন**

```
Email:    demo@sellermate.ai
Password: Demo1234!
```

অথবা লগইন পেজে **"ডেমো হিসেবে ঢুকুন"** বাটনে ক্লিক করুন — এটা সবচেয়ে সহজ।

---

**ডেমো স্টোর দেখতে**

`http://localhost:3000/store/demo-shop`

---

**কী কী টেস্ট করবেন**

1. ✅ ড্যাশবোর্ড লোড হচ্ছে কিনা
2. ✅ অর্ডার লিস্ট + ফিল্টার কাজ করছে কিনা
3. ✅ প্রোডাক্ট যোগ/সম্পাদনা করা যাচ্ছে কিনা
4. ✅ স্টোর বিল্ডার লোড হচ্ছে কিনা
5. ✅ মার্কেটপ্লেসে ডেমো শপ দেখা যাচ্ছে কিনা
6. ✅ ডেমো স্টোরে প্রোডাক্ট দেখা যাচ্ছে কিনা
7. ✅ কার্টে পণ্য যোগ করা যাচ্ছে কিনা
8. ✅ চেকআউট সম্পন্ন হচ্ছে কিনা
9. ✅ AI টুলস কন্টেন্ট জেনারেট করছে কিনা
10. ✅ AI এজেন্ট রান করা যাচ্ছে কিনা

বিস্তারিত টেস্ট ফ্লো: `TESTING_GUIDE.md` দেখুন।

---

**⚠️ গুরুত্বপূর্ণ — বেটা সীমাবদ্ধতা**

- 💳 পেমেন্ট (bKash, Nagad) — সিমুলেটেড। কোনো টাকা কাটবে না।
- 🚚 কুরিয়ার (Pathao, Steadfast) — ফেক ট্র্যাকিং ID। আসল পার্সেল তৈরি হবে না।
- 📱 OTP — কনসোলে প্রিন্ট হবে, ফোনে যাবে না।
- 🤖 AI — API কি ছাড়াও কাজ করে (রুল-বেসড ফলব্যাক)।

**কোনো আসল টাকা বা কুরিয়ার জড়িত নেই। নিরাপদে টেস্ট করুন।**

---

**ফিডব্যাক কীভাবে দেবেন**

`FEEDBACK_TEMPLATE.md` ফিলআপ করে পাঠান:

📧 **fokrulanthro16@gmail.com**
📌 Subject: `[SellerMate Beta] Feedback — আপনার নাম`

অথবা GitHub Issue খুলুন (bug_report / ui_feedback / feature_request template ব্যবহার করুন)।

---

ধন্যবাদ! আপনার ফিডব্যাক SellerMate-কে আরও ভালো করতে সাহায্য করবে। 🙏

— SellerMate AI Team
