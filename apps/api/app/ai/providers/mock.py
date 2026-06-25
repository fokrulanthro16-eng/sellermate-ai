"""
MockTextProvider — deterministic text generation based on prompt keywords.
Used when no API key is configured. Produces real, readable Bangla/English content.
"""
from __future__ import annotations

from .base import AITextProvider

_FB_POST_BN = """🌟 আমাদের {name} এখন পাওয়া যাচ্ছে! 🌟

দারুণ মানের এই পণ্যটি আপনার প্রিয়জনদের জন্য আদর্শ উপহার হতে পারে।
💰 মূল্য: {price}
📦 দ্রুত ডেলিভারি নিশ্চিত!

👉 অর্ডার করতে ইনবক্সে মেসেজ করুন।
📞 যোগাযোগ করুন আজই!

#বাংলাদেশ #অনলাইনশপিং #SellerMate"""

_FB_POST_EN = """🌟 Introducing {name}! 🌟

Premium quality product now available at an amazing price.
💰 Price: {price}
📦 Fast delivery guaranteed!

👉 Message us to place your order.
📞 Contact us today!

#Bangladesh #OnlineShopping #SellerMate"""

_FB_AD_BN = """🔥 সীমিত সময়ের অফার! 🔥

✅ {name}
✅ মূল্য: মাত্র {price}
✅ দ্রুত হোম ডেলিভারি
✅ ১০০% অরিজিনাল পণ্য

আজই অর্ডার করুন — স্টক সীমিত!
👆 উপরে ক্লিক করুন বা ইনবক্সে মেসেজ করুন"""

_FB_AD_EN = """🔥 Limited Time Offer! 🔥

✅ {name}
✅ Price: Only {price}
✅ Fast Home Delivery
✅ 100% Original Product

Order Today — Limited Stock!
👆 Click above or message us now"""

_EMAIL_BN = """বিষয়: {name} — বিশেষ অফার আপনার জন্য!

প্রিয় গ্রাহক,

আশা করি আপনি ভালো আছেন। আমরা আপনার জন্য একটি বিশেষ সুযোগ নিয়ে এসেছি।

আমাদের {name} পণ্যটি এখন মাত্র {price}-এ পাওয়া যাচ্ছে। এই অফারটি সীমিত সময়ের জন্য।

👉 এখনই অর্ডার করুন এবং দ্রুত ডেলিভারি পান।

ধন্যবাদ,
SellerMate টিম"""

_EMAIL_EN = """Subject: Special Offer on {name} — Just for You!

Dear Valued Customer,

We hope you are doing well. We have an exclusive offer just for you.

Our {name} is now available at only {price}. This offer is for a limited time only.

👉 Order now and enjoy fast delivery.

Thank you,
SellerMate Team"""

_SMS_BN = """{name} এখন {price}-এ! সীমিত অফার। দ্রুত অর্ডার করুন। SellerMate"""
_SMS_EN = """{name} now at {price}! Limited offer. Order fast. SellerMate"""


class MockTextProvider(AITextProvider):
    name = "mock"

    async def complete(self, system: str, user: str, max_tokens: int = 1024) -> str:
        combined = (system + " " + user).lower()
        bn = "বাংলা" in combined or "bangla" in combined or "bn" in combined

        # Extract product name and price from the prompt if present
        name = "পণ্য" if bn else "Product"
        price = "সেরা দামে" if bn else "best price"

        for line in (system + "\n" + user).split("\n"):
            if "product:" in line.lower() or "পণ্য:" in line:
                name = line.split(":", 1)[-1].strip()[:50]
            if "মূল্য:" in line or "price:" in line.lower():
                price = line.split(":", 1)[-1].strip()[:20]

        if "fb_ad" in combined or "facebook ad" in combined:
            tmpl = _FB_AD_BN if bn else _FB_AD_EN
        elif "email" in combined:
            tmpl = _EMAIL_BN if bn else _EMAIL_EN
        elif "sms" in combined:
            tmpl = _SMS_BN if bn else _SMS_EN
        else:
            tmpl = _FB_POST_BN if bn else _FB_POST_EN

        return tmpl.format(name=name, price=price)
