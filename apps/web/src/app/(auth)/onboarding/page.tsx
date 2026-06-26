"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { CheckCircle2, ChevronRight, ChevronLeft, Store, User, MapPin, Tag, Globe, Truck, CreditCard, Languages, Upload } from "lucide-react";
import api from "@/lib/api-client";
import { toast } from "sonner";

const BUSINESS_TYPES = [
  { value: "FASHION_CLOTHING", label: "Fashion & Clothing", emoji: "👗" },
  { value: "ELECTRONICS", label: "Electronics", emoji: "📱" },
  { value: "FOOD_BEVERAGE", label: "Food & Beverage", emoji: "🍔" },
  { value: "HOME_DECOR", label: "Home & Decor", emoji: "🏠" },
  { value: "BEAUTY_COSMETICS", label: "Beauty & Cosmetics", emoji: "💄" },
  { value: "BOOKS_STATIONERY", label: "Books & Stationery", emoji: "📚" },
  { value: "HANDICRAFTS", label: "Handicrafts", emoji: "🎨" },
  { value: "AGRICULTURE", label: "Agriculture", emoji: "🌾" },
  { value: "OTHER", label: "Other", emoji: "📦" },
];

const DISTRICTS = [
  "Dhaka", "Chittagong", "Rajshahi", "Khulna", "Barisal", "Sylhet", "Rangpur", "Mymensingh",
  "Comilla", "Narayanganj", "Gazipur", "Narsingdi", "Tangail", "Bogura", "Jessore", "Noakhali",
  "Cox's Bazar", "Feni", "Lakshmipur", "Chandpur",
];

const PAYMENT_METHODS = [
  { id: "bkash", label: "bKash", emoji: "🔴" },
  { id: "nagad", label: "Nagad", emoji: "🟠" },
  { id: "sslcommerz", label: "SSLCommerz (Card)", emoji: "💳" },
  { id: "cod", label: "Cash on Delivery", emoji: "💵" },
];

const COURIER_METHODS = [
  { id: "pathao", label: "Pathao", emoji: "🛵" },
  { id: "steadfast", label: "Steadfast", emoji: "📦" },
  { id: "redx", label: "REDX", emoji: "🚚" },
  { id: "manual", label: "Self-delivery", emoji: "🚶" },
];

function slugify(text: string) {
  return text.toLowerCase().replace(/[^\w\s-]/g, "").replace(/[\s_-]+/g, "-").replace(/^-+|-+$/g, "").slice(0, 40);
}

interface WizardState {
  business_name: string;
  owner_name: string;
  phone: string;
  district: string;
  area: string;
  business_type: string;
  store_slug: string;
  payment_methods: string[];
  courier_methods: string[];
  language: string;
}

const STEPS = [
  { id: "business", label: "Business", icon: Store },
  { id: "owner", label: "Owner", icon: User },
  { id: "location", label: "Location", icon: MapPin },
  { id: "category", label: "Category", icon: Tag },
  { id: "store", label: "Store", icon: Globe },
  { id: "payment", label: "Payment", icon: CreditCard },
  { id: "delivery", label: "Delivery", icon: Truck },
  { id: "prefs", label: "Preferences", icon: Languages },
];

export default function OnboardingPage() {
  const router = useRouter();
  const [step, setStep] = useState(0);
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState<WizardState>({
    business_name: "",
    owner_name: "",
    phone: "",
    district: "",
    area: "",
    business_type: "",
    store_slug: "",
    payment_methods: ["cod"],
    courier_methods: ["manual"],
    language: "bn",
  });

  function setField<K extends keyof WizardState>(key: K, val: WizardState[K]) {
    setForm((p) => ({ ...p, [key]: val }));
    if (key === "business_name" && typeof val === "string") {
      setForm((p) => ({ ...p, [key]: val, store_slug: slugify(val) }));
    }
  }

  function toggleList(key: "payment_methods" | "courier_methods", val: string) {
    setForm((p) => {
      const arr = p[key];
      return { ...p, [key]: arr.includes(val) ? arr.filter((x) => x !== val) : [...arr, val] };
    });
  }

  function canProceed() {
    if (step === 0) return form.business_name.length >= 2;
    if (step === 1) return form.owner_name.length >= 2;
    if (step === 2) return !!form.district;
    if (step === 3) return !!form.business_type;
    if (step === 4) return form.store_slug.length >= 3;
    return true;
  }

  async function handleFinish() {
    setSaving(true);
    try {
      await api.patch("/merchant/me", {
        business_name: form.business_name,
        owner_name: form.owner_name,
        district: form.district,
        address: form.area ? `${form.area}, ${form.district}` : form.district,
        business_type: form.business_type || undefined,
        store_slug: form.store_slug || undefined,
      });
      await api.post("/merchant/onboarding", { step: 4, data: { done: true } });
      toast.success("Setup complete! Welcome to SellerMate.");
      router.push("/dashboard");
    } catch (err: any) {
      toast.error(err?.response?.data?.error?.message || "Setup failed");
    } finally {
      setSaving(false);
    }
  }

  const CurrentIcon = STEPS[step].icon;

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-white to-purple-50 flex flex-col items-center justify-center px-4 py-12">
      {/* Header */}
      <div className="text-center mb-8">
        <div className="inline-flex items-center gap-2 bg-indigo-600 text-white px-4 py-1.5 rounded-full text-sm font-medium mb-4">
          <Store className="w-4 h-4" /> SellerMate Setup
        </div>
        <h1 className="text-2xl font-bold text-gray-900">Set up your store</h1>
        <p className="text-gray-500 mt-1">Step {step + 1} of {STEPS.length}</p>
      </div>

      {/* Progress */}
      <div className="w-full max-w-lg mb-6">
        <div className="flex gap-1">
          {STEPS.map((s, i) => (
            <div key={s.id} className={`h-1.5 flex-1 rounded-full transition-colors ${i <= step ? "bg-indigo-600" : "bg-gray-200"}`} />
          ))}
        </div>
        <div className="flex justify-between mt-1">
          <span className="text-xs text-indigo-600 font-medium">{STEPS[step].label}</span>
          <span className="text-xs text-gray-400">{Math.round(((step + 1) / STEPS.length) * 100)}%</span>
        </div>
      </div>

      {/* Card */}
      <div className="bg-white rounded-2xl shadow-sm border border-gray-200 w-full max-w-lg p-8">
        <div className="flex items-center gap-3 mb-6">
          <div className="w-10 h-10 rounded-xl bg-indigo-100 flex items-center justify-center">
            <CurrentIcon className="w-5 h-5 text-indigo-600" />
          </div>
          <div>
            <h2 className="font-semibold text-gray-900 text-lg">
              {step === 0 && "Business Name"}
              {step === 1 && "Owner Name"}
              {step === 2 && "Location"}
              {step === 3 && "Business Category"}
              {step === 4 && "Store URL"}
              {step === 5 && "Payment Methods"}
              {step === 6 && "Delivery Methods"}
              {step === 7 && "Preferences"}
            </h2>
            <p className="text-sm text-gray-500">
              {step === 0 && "What is your business called?"}
              {step === 1 && "What is your name?"}
              {step === 2 && "Where is your business located?"}
              {step === 3 && "What do you sell?"}
              {step === 4 && "Choose your public store link"}
              {step === 5 && "How will customers pay?"}
              {step === 6 && "How will you deliver?"}
              {step === 7 && "Language and notifications"}
            </p>
          </div>
        </div>

        {/* Step content */}
        {step === 0 && (
          <div>
            <input
              className="w-full border border-gray-300 rounded-xl px-4 py-3 text-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
              placeholder="e.g. Rina Fashion House"
              value={form.business_name}
              onChange={(e) => setField("business_name", e.target.value)}
              autoFocus
            />
            <p className="text-xs text-gray-400 mt-2">This appears on your public store</p>
          </div>
        )}

        {step === 1 && (
          <div>
            <input
              className="w-full border border-gray-300 rounded-xl px-4 py-3 text-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
              placeholder="Your full name"
              value={form.owner_name}
              onChange={(e) => setField("owner_name", e.target.value)}
              autoFocus
            />
          </div>
        )}

        {step === 2 && (
          <div className="space-y-3">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">District *</label>
              <select
                className="w-full border border-gray-300 rounded-xl px-4 py-3 focus:outline-none focus:ring-2 focus:ring-indigo-500 bg-white"
                value={form.district}
                onChange={(e) => setField("district", e.target.value)}
              >
                <option value="">Select district</option>
                {DISTRICTS.map((d) => <option key={d} value={d}>{d}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Area / Upazila</label>
              <input
                className="w-full border border-gray-300 rounded-xl px-4 py-3 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                placeholder="e.g. Mirpur-10, Gulshan, Rayer Bazar"
                value={form.area}
                onChange={(e) => setField("area", e.target.value)}
              />
            </div>
          </div>
        )}

        {step === 3 && (
          <div className="grid grid-cols-3 gap-2">
            {BUSINESS_TYPES.map((bt) => (
              <button
                key={bt.value}
                onClick={() => setField("business_type", bt.value)}
                className={`flex flex-col items-center gap-1.5 p-3 rounded-xl border-2 text-sm font-medium transition-all ${
                  form.business_type === bt.value
                    ? "border-indigo-600 bg-indigo-50 text-indigo-700"
                    : "border-gray-200 text-gray-600 hover:border-gray-300"
                }`}
              >
                <span className="text-2xl">{bt.emoji}</span>
                <span className="text-xs text-center leading-tight">{bt.label}</span>
              </button>
            ))}
          </div>
        )}

        {step === 4 && (
          <div>
            <div className="flex items-center border border-gray-300 rounded-xl overflow-hidden focus-within:ring-2 focus-within:ring-indigo-500">
              <span className="px-3 py-3 bg-gray-50 text-gray-500 text-sm border-r border-gray-300 whitespace-nowrap">
                sellermate.ai/store/
              </span>
              <input
                className="flex-1 px-3 py-3 text-sm focus:outline-none"
                placeholder="my-store-name"
                value={form.store_slug}
                onChange={(e) => setField("store_slug", slugify(e.target.value))}
              />
            </div>
            <p className="text-xs text-gray-400 mt-2">Only lowercase letters, numbers, and hyphens</p>
            {form.store_slug && (
              <div className="mt-3 p-3 bg-green-50 rounded-lg text-sm text-green-700">
                Your store: <strong>/store/{form.store_slug}</strong>
              </div>
            )}
          </div>
        )}

        {step === 5 && (
          <div className="space-y-2">
            {PAYMENT_METHODS.map((m) => (
              <label key={m.id}
                className={`flex items-center gap-3 p-3.5 rounded-xl border-2 cursor-pointer transition-all ${
                  form.payment_methods.includes(m.id)
                    ? "border-indigo-600 bg-indigo-50"
                    : "border-gray-200 hover:border-gray-300"
                }`}>
                <input
                  type="checkbox"
                  className="sr-only"
                  checked={form.payment_methods.includes(m.id)}
                  onChange={() => toggleList("payment_methods", m.id)}
                />
                <span className="text-xl">{m.emoji}</span>
                <span className="font-medium text-gray-700">{m.label}</span>
                {form.payment_methods.includes(m.id) && (
                  <CheckCircle2 className="w-4 h-4 text-indigo-600 ml-auto" />
                )}
              </label>
            ))}
          </div>
        )}

        {step === 6 && (
          <div className="space-y-2">
            {COURIER_METHODS.map((m) => (
              <label key={m.id}
                className={`flex items-center gap-3 p-3.5 rounded-xl border-2 cursor-pointer transition-all ${
                  form.courier_methods.includes(m.id)
                    ? "border-indigo-600 bg-indigo-50"
                    : "border-gray-200 hover:border-gray-300"
                }`}>
                <input
                  type="checkbox"
                  className="sr-only"
                  checked={form.courier_methods.includes(m.id)}
                  onChange={() => toggleList("courier_methods", m.id)}
                />
                <span className="text-xl">{m.emoji}</span>
                <span className="font-medium text-gray-700">{m.label}</span>
                {form.courier_methods.includes(m.id) && (
                  <CheckCircle2 className="w-4 h-4 text-indigo-600 ml-auto" />
                )}
              </label>
            ))}
          </div>
        )}

        {step === 7 && (
          <div className="space-y-4">
            <div>
              <p className="text-sm font-medium text-gray-700 mb-2">Display Language</p>
              <div className="flex gap-3">
                {[{ id: "bn", label: "বাংলা" }, { id: "en", label: "English" }].map((lang) => (
                  <button
                    key={lang.id}
                    onClick={() => setField("language", lang.id)}
                    className={`flex-1 py-3 rounded-xl border-2 font-medium transition-all ${
                      form.language === lang.id
                        ? "border-indigo-600 bg-indigo-50 text-indigo-700"
                        : "border-gray-200 text-gray-600 hover:border-gray-300"
                    }`}
                  >
                    {lang.label}
                  </button>
                ))}
              </div>
            </div>
            <div className="bg-indigo-50 rounded-xl p-4">
              <h3 className="font-semibold text-indigo-800 mb-2">Setup Summary</h3>
              <div className="space-y-1 text-sm text-indigo-700">
                <p>🏪 {form.business_name}</p>
                <p>👤 {form.owner_name}</p>
                {form.district && <p>📍 {form.area ? `${form.area}, ` : ""}{form.district}</p>}
                {form.store_slug && <p>🔗 /store/{form.store_slug}</p>}
              </div>
            </div>
          </div>
        )}

        {/* Navigation */}
        <div className="flex gap-3 mt-8">
          {step > 0 && (
            <button
              onClick={() => setStep((s) => s - 1)}
              className="flex items-center gap-1 px-4 py-2.5 border border-gray-300 rounded-xl text-sm font-medium text-gray-600 hover:bg-gray-50 transition-colors"
            >
              <ChevronLeft className="w-4 h-4" /> Back
            </button>
          )}
          <div className="flex-1" />
          {step < STEPS.length - 1 ? (
            <button
              onClick={() => setStep((s) => s + 1)}
              disabled={!canProceed()}
              className="flex items-center gap-1 px-6 py-2.5 bg-indigo-600 text-white rounded-xl text-sm font-semibold hover:bg-indigo-700 disabled:opacity-50 transition-colors"
            >
              Next <ChevronRight className="w-4 h-4" />
            </button>
          ) : (
            <button
              onClick={handleFinish}
              disabled={saving}
              className="flex items-center gap-2 px-6 py-2.5 bg-green-600 text-white rounded-xl text-sm font-semibold hover:bg-green-700 disabled:opacity-60 transition-colors"
            >
              <CheckCircle2 className="w-4 h-4" />
              {saving ? "Saving..." : "Launch My Store"}
            </button>
          )}
        </div>
      </div>

      <button
        onClick={() => router.push("/dashboard")}
        className="mt-4 text-sm text-gray-400 hover:text-gray-600 transition-colors"
      >
        Skip for now
      </button>
    </div>
  );
}
