"""
SellerToolsAgent — AI-powered text generation for seller marketing tools.

Priority: Gemini → Anthropic → Rule-based fallback.
Rule-based fallback produces real Bangla/English content using product/order data.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class GeneratedContent:
    text: str
    source: str  # "gemini" | "anthropic" | "rule_based"
    context_used: dict[str, Any] = field(default_factory=dict)


class SellerToolsAgent:
    """Multi-source text generator for seller marketing tools."""

    async def generate(
        self,
        tool: str,
        lang: str,
        tone: str,
        product: dict | None = None,
        order: dict | None = None,
        customer: dict | None = None,
        insights: dict | None = None,
        extra_context: str | None = None,
    ) -> GeneratedContent:
        context_used: dict[str, Any] = {}
        if product:
            context_used["product"] = {
                "id": product.get("id"),
                "name": product.get("name_bangla") or product.get("name"),
            }
        if order:
            context_used["order"] = {
                "id": order.get("id"),
                "order_number": order.get("order_number"),
            }
        if customer:
            context_used["customer"] = {"name": customer.get("name")}

        prompt = self._build_prompt(tool, lang, tone, product, order, customer, insights, extra_context)

        from app.ai.providers import get_provider
        provider = get_provider()

        if provider.name != "mock":
            try:
                system = (
                    "তুমি একজন বাংলাদেশি ই-কমার্স বিক্রেতার মার্কেটিং সহকারী।"
                    if lang == "bn" else
                    "You are a marketing assistant for a Bangladeshi e-commerce seller."
                )
                text = await provider.complete(system=system, user=prompt, max_tokens=1024)
                if text:
                    return GeneratedContent(text=text, source=provider.name, context_used=context_used)
            except Exception:
                pass

        text = _rule_based(tool, lang, tone, product, order, customer, insights)
        return GeneratedContent(text=text, source="rule_based", context_used=context_used)

    def _build_prompt(
        self, tool: str, lang: str, tone: str,
        product: dict | None, order: dict | None,
        customer: dict | None, insights: dict | None,
        extra_context: str | None,
    ) -> str:
        bn = lang == "bn"
        lang_instr = (
            "তুমি একজন বাংলাদেশি ই-কমার্স বিক্রেতার মার্কেটিং সহকারী। শুধুমাত্র বাংলায় উত্তর দাও।"
            if bn else
            "You are a marketing assistant for a Bangladeshi e-commerce seller. Respond only in English."
        )
        tool_tasks_bn = {
            "post": "ফেসবুক/হোয়াটসঅ্যাপ পোস্ট লিখুন (৩-৫ বাক্য, পণ্যের নাম, দাম, বৈশিষ্ট্য ও CTA সহ, ইমোজি ব্যবহার করুন)",
            "caption": "ইনস্টাগ্রাম/ফেসবুক ক্যাপশন লিখুন (১-২ বাক্য, আকর্ষণীয়, ইমোজি সহ)",
            "hashtag": "পণ্যের জন্য ১০-১৫টি হ্যাশট্যাগ তৈরি করুন (শুধু হ্যাশট্যাগ, স্পেস দিয়ে আলাদা করা)",
            "description": "পণ্যের বিস্তারিত বিবরণ লিখুন (৪-৬ বাক্য, বৈশিষ্ট্য, সুবিধা, স্পেসিফিকেশন)",
            "offer": "সীমিত সময়ের অফার টেক্সট লিখুন (ছাড়, জরুরিতা, CTA সহ, ইমোজি ব্যবহার করুন)",
            "reply": "গ্রাহক সেবার উত্তর লিখুন (ভদ্র, সহায়ক, সমস্যা সমাধানমুখী)",
            "daily_action": "ব্যবসার বর্তমান অবস্থার ভিত্তিতে আজকের জন্য ৩-৫টি কংক্রিট কাজের তালিকা দাও (ক্রমানুসারে)",
        }
        tool_tasks_en = {
            "post": "Write a Facebook/WhatsApp post (3-5 sentences, product name, price, features and CTA, use emojis)",
            "caption": "Write an Instagram/Facebook caption (1-2 sentences, engaging, with emojis)",
            "hashtag": "Generate 10-15 hashtags for this product (only hashtags, space-separated)",
            "description": "Write a detailed product description (4-6 sentences, features, benefits, specifications)",
            "offer": "Write a limited-time offer text (include discount, urgency, CTA, use emojis)",
            "reply": "Write a customer service reply (polite, helpful, solution-oriented)",
            "daily_action": "List 3-5 concrete tasks to do TODAY based on business metrics (ordered by priority)",
        }
        task = tool_tasks_bn.get(tool, "কন্টেন্ট তৈরি করুন") if bn else tool_tasks_en.get(tool, "Generate content")

        tone_map = {
            "friendly": ("বন্ধুত্বপূর্ণ ও উষ্ণ", "friendly and warm"),
            "professional": ("পেশাদার ও আনুষ্ঠানিক", "professional and formal"),
            "urgent": ("জরুরি ও উত্তেজনাপূর্ণ", "urgent and exciting"),
        }
        tone_text = tone_map.get(tone, (tone, tone))[0 if bn else 1]

        parts = [f"টোন: {tone_text}" if bn else f"Tone: {tone_text}", f"কাজ: {task}" if bn else f"Task: {task}"]

        if product:
            name = (product.get("name_bangla") or product.get("name", "পণ্য")) if bn else product.get("name", "Product")
            price = product.get("sale_price") or product.get("base_price")
            cat = product.get("category", "")
            desc = ((product.get("description_bangla") or product.get("description", "")) if bn else product.get("description", ""))
            parts.append(f"পণ্য: {name}" if bn else f"Product: {name}")
            if cat:
                parts.append(f"ক্যাটাগরি: {cat}" if bn else f"Category: {cat}")
            if price:
                parts.append(f"মূল্য: ৳{price}")
            if desc:
                parts.append((f"বিবরণ: {desc[:200]}" if bn else f"Description: {desc[:200]}"))

        if order:
            on = order.get("order_number", "")
            st = order.get("status", "")
            cname = customer.get("name", "") if customer else ""
            parts.append(
                f"অর্ডার #{on}, অবস্থা: {st}, গ্রাহক: {cname}"
                if bn else
                f"Order #{on}, Status: {st}, Customer: {cname}"
            )

        if insights:
            ts = insights.get("trust_score", "N/A")
            trend = insights.get("trend_direction", "N/A")
            risk = insights.get("risk_level", "N/A")
            gpct = insights.get("revenue_growth_pct", "N/A")
            parts.append(
                f"ব্যবসার তথ্য: ট্রাস্ট স্কোর={ts}, প্রবৃদ্ধি={trend} ({gpct}%), ঝুঁকি={risk}"
                if bn else
                f"Business: trust={ts}, growth={trend} ({gpct}%), risk={risk}"
            )

        if extra_context:
            parts.append(f"অতিরিক্ত: {extra_context}" if bn else f"Extra context: {extra_context}")

        instr = "শুধুমাত্র টেক্সট আউটপুট দাও, কোনো ব্যাখ্যা বা লেবেল নয়।" if bn else "Return ONLY the generated text, no explanations or labels."
        return f"{lang_instr}\n\n" + "\n".join(parts) + f"\n\n{instr}"


# ── Rule-based fallback ────────────────────────────────────────────────────────

def _rule_based(
    tool: str, lang: str, tone: str,
    product: dict | None, order: dict | None,
    customer: dict | None, insights: dict | None,
) -> str:
    bn = lang == "bn"
    if tool == "post":        return _post(bn, tone, product)
    if tool == "caption":     return _caption(bn, tone, product)
    if tool == "hashtag":     return _hashtag(bn, product)
    if tool == "description": return _description(bn, tone, product)
    if tool == "offer":       return _offer(bn, tone, product)
    if tool == "reply":       return _reply(bn, tone, order, customer)
    if tool == "daily_action":return _daily_action(bn, insights)
    return "কোনো ডেটা পাওয়া যায়নি।" if bn else "No data found."


def _pname(product: dict | None, bn: bool) -> str:
    if not product:
        return "পণ্য" if bn else "Product"
    return (product.get("name_bangla") or product.get("name", "পণ্য")) if bn else product.get("name", "Product")


def _price_str(product: dict | None) -> str:
    if not product:
        return ""
    p = product.get("sale_price") or product.get("base_price")
    return f"৳{p}" if p else ""


def _cat(product: dict | None, bn: bool) -> str:
    if not product:
        return "পণ্য" if bn else "product"
    return product.get("category", "পণ্য" if bn else "product")


def _post(bn: bool, tone: str, product: dict | None) -> str:
    name = _pname(product, bn)
    price = _price_str(product)
    cat = _cat(product, bn)

    if bn:
        openers = {
            "friendly": "🌟 আমাদের প্রিয় গ্রাহকদের জন্য দারুণ সংবাদ! 🌟\n\n",
            "professional": "📢 পণ্য বিজ্ঞপ্তি:\n\n",
            "urgent": "⚡ সীমিত সময়ের সুযোগ! এখনই সিদ্ধান্ত নিন! ⚡\n\n",
        }
        opener = openers.get(tone, openers["friendly"])
        body = f"{name} এখন আমাদের কাছে পাওয়া যাচ্ছে।"
        body += f" মাত্র {price}-এ পাচ্ছেন এই অসাধারণ {cat} পণ্যটি।" if price else f" সেরা মানের {cat} পণ্য এখন উপলব্ধ।"
        cta = "\n\n📲 অর্ডার করতে আমাদের ইনবক্সে মেসেজ করুন অথবা কমেন্টে জানান।\n✅ দ্রুত ডেলিভারি নিশ্চিত!\n📞 যেকোনো প্রশ্নে সরাসরি যোগাযোগ করুন।"
        return opener + body + cta
    else:
        openers = {
            "friendly": "🌟 Great news for our valued customers! 🌟\n\n",
            "professional": "📢 Product Announcement:\n\n",
            "urgent": "⚡ Limited Time Opportunity — Act Now! ⚡\n\n",
        }
        opener = openers.get(tone, openers["friendly"])
        body = f"{name} is now available in our store."
        body += f" Get this amazing {cat} for only {price}." if price else f" Premium quality {cat} delivered to your doorstep."
        cta = "\n\n📲 Message us to place your order or drop a comment below.\n✅ Fast delivery guaranteed!\n📞 Contact us for any questions."
        return opener + body + cta


def _caption(bn: bool, tone: str, product: dict | None) -> str:
    name = _pname(product, bn)
    price = _price_str(product)

    if bn:
        if tone == "urgent":
            return f"⚡ এখনই নিন {name}! {price + ' মাত্র' if price else 'অবিশ্বাস্য দামে'} — স্টক সীমিত! 🛒 আজই অর্ডার করুন।"
        if tone == "professional":
            return f"✨ {name} — গুণগত মান ও পরিশীলতার প্রতীক। {price + '-এ পাওয়া যাচ্ছে।' if price else 'এখন উপলব্ধ।'}"
        return f"💫 {name} — আপনার পছন্দের পণ্য! {price + ' মাত্র 🛍️' if price else 'এখনই অর্ডার করুন! 🛍️'}"
    else:
        if tone == "urgent":
            return f"⚡ Grab {name} NOW! {price + ' only' if price else 'Unbelievable price'} — Limited stock! 🛒 Order today."
        if tone == "professional":
            return f"✨ {name} — Quality and elegance redefined. {'Available at ' + price + '.' if price else 'Now available.'}"
        return f"💫 {name} — Your perfect find! {price + ' only 🛍️' if price else 'Order now! 🛍️'}"


def _hashtag(bn: bool, product: dict | None) -> str:
    cat_raw = (product.get("category", "") if product else "").replace(" ", "")
    name_raw = (product.get("name", "") if product else "").replace(" ", "")[:20]

    base = ["#Bangladesh", "#OnlineShopping", "#BangladeshOnlineShop", "#OrderNow", "#HomeDelivery", "#SellerMate", "#BestPrice", "#FastDelivery", "#QualityProduct", "#FBShop"]
    if cat_raw:
        base.insert(0, f"#{cat_raw}")
    if name_raw:
        base.insert(0, f"#{name_raw}")

    extra_bn = ["#বাংলাদেশ", "#অনলাইনশপিং", "#দ্রুতডেলিভারি", "#বিশেষছাড়", "#সেরাদাম"]
    extra_en = ["#EcommerceBD", "#ShopOnline", "#TrustedSeller", "#SpecialOffer", "#DailyDeals"]

    tags = base + (extra_bn if bn else extra_en)
    return " ".join(tags[:15])


def _description(bn: bool, tone: str, product: dict | None) -> str:
    name = _pname(product, bn)
    price = _price_str(product)
    cat = _cat(product, bn)
    desc_key = "description_bangla" if bn else "description"
    existing = (product.get(desc_key) or product.get("description", "")) if product else ""

    if bn:
        intro = f"**{name}** হলো আমাদের {cat} বিভাগের একটি প্রিমিয়াম পণ্য।"
        quality = " এটি সর্বোচ্চ মানের উপকরণ দিয়ে তৈরি, যা দীর্ঘস্থায়ী ব্যবহারের উপযোগী।"
        detail = f" {existing[:150]}" if existing else " এই পণ্যটি আপনার দৈনন্দিন জীবনকে আরও সহজ ও সুন্দর করে তুলবে।"
        price_info = f" **মূল্য:** {price}।" if price else ""
        cta = " আজই অর্ডার করুন এবং দ্রুত ডেলিভারি উপভোগ করুন।"
        return intro + quality + detail + price_info + cta
    else:
        intro = f"**{name}** is a premium {cat} product from our curated collection."
        quality = " Crafted with the finest materials, designed for long-lasting performance and durability."
        detail = f" {existing[:150]}" if existing else " This product is designed to enhance your daily life with its superior quality and versatile functionality."
        price_info = f" **Price:** {price}." if price else ""
        cta = " Order today and enjoy fast home delivery right to your doorstep."
        return intro + quality + detail + price_info + cta


def _offer(bn: bool, tone: str, product: dict | None) -> str:
    name = _pname(product, bn)
    sale = product.get("sale_price") if product else None
    base = product.get("base_price") if product else None

    if bn:
        if sale and base and float(str(sale)) < float(str(base)):
            pct = round((1 - float(str(sale)) / float(str(base))) * 100)
            return (
                f"🎉 **বিশেষ অফার!** 🎉\n\n"
                f"{name} এখন মাত্র **৳{sale}**-এ! (স্বাভাবিক মূল্য ৳{base})\n"
                f"🔥 {pct}% ছাড় — সীমিত সময়ের জন্য!\n\n"
                f"⏰ এই অফার যেকোনো সময় শেষ হতে পারে। আজই অর্ডার করুন এবং সাশ্রয় করুন!\n"
                f"📲 ইনবক্সে মেসেজ করুন বা কমেন্ট করুন।"
            )
        price_text = f"মাত্র **৳{sale}**-এ" if sale else "বিশেষ ছাড়ে"
        return (
            f"🎉 **সীমিত সময়ের অফার!** 🎉\n\n"
            f"{name} এখন {price_text} পাওয়া যাচ্ছে! এই দারুণ সুযোগ মিস করবেন না।\n\n"
            f"⏰ সীমিত স্টক — এখনই অর্ডার করুন!\n"
            f"📲 ইনবক্সে মেসেজ করুন।"
        )
    else:
        if sale and base and float(str(sale)) < float(str(base)):
            pct = round((1 - float(str(sale)) / float(str(base))) * 100)
            return (
                f"🎉 **Special Offer!** 🎉\n\n"
                f"{name} is now only **৳{sale}**! (Regular price ৳{base})\n"
                f"🔥 {pct}% OFF — For a limited time only!\n\n"
                f"⏰ This offer may end at any time. Order now and save big!\n"
                f"📲 Message us or drop a comment below."
            )
        price_text = f"just ৳{sale}" if sale else "an amazing discounted price"
        return (
            f"🎉 **Limited Time Offer!** 🎉\n\n"
            f"Get {name} at {price_text}! Don't miss this incredible deal.\n\n"
            f"⏰ Limited stock available — Order NOW!\n"
            f"📲 Message us to place your order."
        )


def _reply(bn: bool, tone: str, order: dict | None, customer: dict | None) -> str:
    cname = (customer.get("name", "") if customer else "") or ("প্রিয় গ্রাহক" if bn else "Valued Customer")
    order_num = order.get("order_number", "") if order else ""
    status = (order.get("status", "") if order else "").upper()

    status_bn = {
        "PENDING":    "আপনার অর্ডারটি পর্যালোচনাধীন আছে এবং শীঘ্রই নিশ্চিত করা হবে।",
        "CONFIRMED":  "আপনার অর্ডারটি নিশ্চিত হয়েছে এবং প্রস্তুত করা হচ্ছে।",
        "PROCESSING": "আপনার অর্ডারটি বর্তমানে প্রক্রিয়া করা হচ্ছে।",
        "SHIPPED":    "আপনার অর্ডারটি পাঠানো হয়েছে এবং শীঘ্রই পৌঁছাবে। ট্র্যাকিং তথ্য আলাদাভাবে পাঠানো হবে।",
        "DELIVERED":  "আপনার অর্ডারটি সফলভাবে ডেলিভারি দেওয়া হয়েছে। আপনার সন্তুষ্টি আমাদের অনুপ্রেরণা!",
        "CANCELLED":  "দুঃখিত, আপনার অর্ডারটি বাতিল হয়েছে। আমরা আপনাকে সহায়তা করতে প্রস্তুত।",
    }
    status_en = {
        "PENDING":    "Your order is under review and will be confirmed shortly.",
        "CONFIRMED":  "Your order has been confirmed and is being prepared for dispatch.",
        "PROCESSING": "Your order is currently being processed and will be shipped soon.",
        "SHIPPED":    "Your order has been shipped and will arrive shortly. Tracking details will be shared separately.",
        "DELIVERED":  "Your order has been successfully delivered. Your satisfaction is our motivation!",
        "CANCELLED":  "We're sorry, your order has been cancelled. We're here to assist you further.",
    }

    if bn:
        order_ref = f" (অর্ডার #{order_num})" if order_num else ""
        status_msg = status_bn.get(status, "আপনার অর্ডারের বিষয়ে আমরা সচেষ্ট আছি।")
        return (
            f"প্রিয় {cname},\n\n"
            f"আপনার{order_ref} বিষয়ে যোগাযোগ করার জন্য আন্তরিক ধন্যবাদ। "
            f"{status_msg}\n\n"
            f"কোনো প্রশ্ন বা সমস্যা থাকলে নির্দ্বিধায় আমাদের জানান। "
            f"আমরা সর্বদা আপনার সেবায় নিয়োজিত।\n\n"
            f"আন্তরিক ধন্যবাদ,\nআপনার বিক্রেতা"
        )
    else:
        order_ref = f" (Order #{order_num})" if order_num else ""
        status_msg = status_en.get(status, "We are actively working on your request.")
        return (
            f"Dear {cname},\n\n"
            f"Thank you for reaching out to us regarding your order{order_ref}. "
            f"{status_msg}\n\n"
            f"Please don't hesitate to contact us if you have any further questions. "
            f"We are always here to help.\n\n"
            f"Best regards,\nYour Seller"
        )


def _daily_action(bn: bool, insights: dict | None) -> str:
    if not insights:
        if bn:
            return (
                "📋 **আজকের কাজের তালিকা:**\n\n"
                "1. 🔍 কৌশলগত AI এজেন্ট চালান (AI সেন্টার → এজেন্ট চালান) — আপনার ব্যবসার বিশ্লেষণ পেতে\n"
                "2. 📦 পেন্ডিং অর্ডারগুলো কনফার্ম করুন এবং প্রসেস শুরু করুন\n"
                "3. 🏷️ কম স্টকের পণ্যগুলো চিহ্নিত করুন এবং রিস্টক করুন\n"
                "4. 📱 এআই টুলস দিয়ে আজকের জন্য একটি ফেসবুক পোস্ট তৈরি করুন\n"
                "5. 💬 অপেক্ষমান গ্রাহক বার্তাগুলোর উত্তর দিন"
            )
        return (
            "📋 **Today's Action List:**\n\n"
            "1. 🔍 Run Strategic AI Agents (AI Center → Run Agents) to get your business analysis\n"
            "2. 📦 Confirm and process all pending orders\n"
            "3. 🏷️ Identify low-stock products and restock them\n"
            "4. 📱 Create an engaging Facebook post using AI Tools\n"
            "5. 💬 Reply to all pending customer messages"
        )

    actions: list[str] = []
    trust_score = int(insights.get("trust_score") or 0)
    risk_level  = str(insights.get("risk_level") or "LOW").upper()
    trend       = str(insights.get("trend_direction") or "STABLE").upper()
    gpct        = float(insights.get("revenue_growth_pct") or 0)

    if bn:
        if trust_score < 60:
            actions.append(f"⭐ **ট্রাস্ট স্কোর উন্নয়ন ({trust_score}/100):** পেন্ডিং অর্ডারগুলো দ্রুত ডেলিভারি করুন এবং গ্রাহকদের সাথে সক্রিয় যোগাযোগ রাখুন।")
        if risk_level in ("HIGH", "VERY_HIGH"):
            actions.append("🚨 **ফ্রড ঝুঁকি উচ্চ:** সন্দেহজনক অর্ডারগুলো যাচাই করুন এবং পেমেন্ট নিশ্চিত হওয়ার আগে ডেলিভারি দেবেন না।")
        if trend == "DECLINING":
            actions.append(f"📉 **বিক্রয় কমছে ({gpct:+.1f}%):** একটি বিশেষ অফার বা ছাড় দিন এবং সোশ্যাল মিডিয়ায় সক্রিয় প্রচার বাড়ান।")
        elif trend == "GROWING":
            actions.append(f"📈 **বিক্রয় বাড়ছে ({gpct:+.1f}%):** এই গতি বজায় রাখুন — সেরা-বিক্রয় পণ্যের স্টক নিশ্চিত করুন।")
        else:
            actions.append("📊 **বিক্রয় স্থিতিশীল:** নতুন পণ্য যোগ করুন বা বিদ্যমান পণ্যে প্রচার বাড়ান।")
        actions.append("📦 **অর্ডার ম্যানেজমেন্ট:** আজকের সব পেন্ডিং অর্ডার কনফার্ম করুন এবং শিপমেন্ট শুরু করুন।")
        actions.append("📱 **মার্কেটিং:** এআই টুলস দিয়ে আজকের জন্য একটি আকর্ষণীয় ফেসবুক পোস্ট বা অফার টেক্সট তৈরি করুন।")
        return "📋 **আজকের কাজের তালিকা (AI বিশ্লেষণ ভিত্তিক):**\n\n" + "\n".join(f"{i+1}. {a}" for i, a in enumerate(actions[:5]))
    else:
        if trust_score < 60:
            actions.append(f"⭐ **Improve Trust Score ({trust_score}/100):** Deliver pending orders quickly and maintain proactive customer communication.")
        if risk_level in ("HIGH", "VERY_HIGH"):
            actions.append("🚨 **High Fraud Risk:** Verify suspicious orders carefully and do not deliver before confirming payment.")
        if trend == "DECLINING":
            actions.append(f"📉 **Sales Declining ({gpct:+.1f}%):** Launch a special offer or discount and increase social media promotion.")
        elif trend == "GROWING":
            actions.append(f"📈 **Sales Growing ({gpct:+.1f}%):** Keep the momentum — ensure stock of best-selling products.")
        else:
            actions.append("📊 **Sales Stable:** Add new products or increase promotion of existing ones.")
        actions.append("📦 **Order Management:** Confirm all pending orders today and start shipment processing.")
        actions.append("📱 **Marketing:** Use AI Tools to create an engaging Facebook post or offer text for today.")
        return "📋 **Today's Action List (AI-driven):**\n\n" + "\n".join(f"{i+1}. {a}" for i, a in enumerate(actions[:5]))
