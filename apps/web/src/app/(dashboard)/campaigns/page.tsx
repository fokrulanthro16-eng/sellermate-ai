"use client";

import { useState } from "react";
import { Megaphone, Loader2, Trash2, Copy, CheckCheck } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { useLang } from "@/contexts/LangContext";
import { useCampaigns, useGenerateCampaign, useDeleteCampaign, type Campaign } from "@/hooks/useCampaigns";
import { cn } from "@/lib/utils";

const CAMPAIGN_TYPES = [
  { id: "fb_post", labelBn: "ফেসবুক পোস্ট",  labelEn: "Facebook Post" },
  { id: "fb_ad",   labelBn: "ফেসবুক বিজ্ঞাপন", labelEn: "Facebook Ad"  },
  { id: "email",   labelBn: "ইমেইল ক্যাম্পেইন", labelEn: "Email"       },
  { id: "sms",     labelBn: "এসএমএস",           labelEn: "SMS"          },
] as const;

const TONES = [
  { id: "friendly",     labelBn: "বন্ধুত্বপূর্ণ", labelEn: "Friendly" },
  { id: "professional", labelBn: "পেশাদার",        labelEn: "Professional" },
  { id: "urgent",       labelBn: "জরুরি",          labelEn: "Urgent" },
] as const;

function CampaignCard({ c, lang }: { c: Campaign; lang: string }) {
  const [copied, setCopied] = useState(false);
  const del = useDeleteCampaign();
  const l = (bn: string, en: string) => lang === "bn" ? bn : en;

  const copy = async () => {
    await navigator.clipboard.writeText(c.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const typeLabel = CAMPAIGN_TYPES.find((t) => t.id === c.campaign_type);

  return (
    <div className="bg-white border border-slate-200 rounded-xl p-4 space-y-3">
      <div className="flex items-start justify-between gap-2">
        <div>
          <p className="font-medium text-slate-800 text-sm">{c.title}</p>
          <div className="flex items-center gap-2 mt-1">
            <span className="text-[10px] font-medium px-2 py-0.5 rounded bg-blue-50 text-blue-700 border border-blue-200">
              {lang === "bn" ? typeLabel?.labelBn : typeLabel?.labelEn}
            </span>
            <span className="text-[10px] text-slate-400">{new Date(c.created_at).toLocaleDateString()}</span>
            <span className="text-[10px] text-slate-400 capitalize">{c.provider}</span>
          </div>
        </div>
        <div className="flex gap-1 shrink-0">
          <button onClick={copy} className="p-1.5 rounded hover:bg-slate-100 text-slate-400 hover:text-slate-700">
            {copied ? <CheckCheck className="h-4 w-4 text-green-500" /> : <Copy className="h-4 w-4" />}
          </button>
          <button
            onClick={() => del.mutate(c.id)}
            disabled={del.isPending}
            className="p-1.5 rounded hover:bg-red-50 text-slate-400 hover:text-red-500"
          >
            <Trash2 className="h-4 w-4" />
          </button>
        </div>
      </div>
      <pre className="text-sm text-slate-700 whitespace-pre-wrap font-sans bg-slate-50 rounded-lg p-3 max-h-48 overflow-y-auto">
        {c.content}
      </pre>
    </div>
  );
}

export default function CampaignsPage() {
  const { lang } = useLang();
  const l = (bn: string, en: string) => lang === "bn" ? bn : en;

  const [type, setType]         = useState<string>("fb_post");
  const [productName, setProd]  = useState("");
  const [productPrice, setPrice] = useState("");
  const [language, setLang]     = useState<"bn" | "en">("bn");
  const [tone, setTone]         = useState("friendly");
  const [extra, setExtra]       = useState("");
  const [filterType, setFilter] = useState<string | undefined>(undefined);

  const campaignsQ = useCampaigns(filterType);
  const generate   = useGenerateCampaign();

  const handleGenerate = () => {
    if (!productName.trim() || !productPrice.trim()) return;
    generate.mutate({ campaign_type: type, product_name: productName, product_price: productPrice, language, tone, extra_context: extra });
  };

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">{l("মার্কেটিং ক্যাম্পেইন", "Marketing Campaigns")}</h1>
        <p className="text-sm text-slate-500 mt-1">{l("AI দিয়ে ক্যাম্পেইন তৈরি করুন", "Generate campaigns with AI")}</p>
      </div>

      <div className="grid lg:grid-cols-3 gap-6">
        {/* Generator */}
        <div className="lg:col-span-1 bg-white border border-slate-200 rounded-xl p-5 space-y-4 h-fit">
          <h2 className="font-semibold text-slate-800 flex items-center gap-2">
            <Megaphone className="h-4 w-4 text-blue-600" />
            {l("নতুন ক্যাম্পেইন", "New Campaign")}
          </h2>

          <div className="space-y-1">
            <label className="text-xs font-medium text-slate-600">{l("ক্যাম্পেইন ধরন", "Type")}</label>
            <div className="grid grid-cols-2 gap-1.5">
              {CAMPAIGN_TYPES.map((t) => (
                <button
                  key={t.id}
                  onClick={() => setType(t.id)}
                  className={cn("py-1.5 text-xs font-medium rounded-lg border transition-colors",
                    type === t.id ? "bg-blue-600 text-white border-blue-600" : "bg-white border-slate-200 text-slate-600 hover:bg-slate-50"
                  )}
                >
                  {lang === "bn" ? t.labelBn : t.labelEn}
                </button>
              ))}
            </div>
          </div>

          <div className="space-y-1">
            <label className="text-xs font-medium text-slate-600">{l("পণ্যের নাম *", "Product Name *")}</label>
            <input
              value={productName}
              onChange={(e) => setProd(e.target.value)}
              placeholder={l("যেমন: প্রিমিয়াম শার্ট", "e.g. Premium Shirt")}
              className="w-full text-sm px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div className="space-y-1">
            <label className="text-xs font-medium text-slate-600">{l("মূল্য *", "Price *")}</label>
            <input
              value={productPrice}
              onChange={(e) => setPrice(e.target.value)}
              placeholder="e.g. ৳৮৯৯"
              className="w-full text-sm px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div className="space-y-1">
            <label className="text-xs font-medium text-slate-600">{l("ভাষা", "Language")}</label>
            <div className="flex gap-2">
              {(["bn", "en"] as const).map((lng) => (
                <button
                  key={lng}
                  onClick={() => setLang(lng)}
                  className={cn("flex-1 py-1.5 text-xs font-medium rounded-lg border transition-colors",
                    language === lng ? "bg-blue-600 text-white border-blue-600" : "bg-white border-slate-200 text-slate-600 hover:bg-slate-50"
                  )}
                >
                  {lng === "bn" ? "বাংলা" : "English"}
                </button>
              ))}
            </div>
          </div>

          <div className="space-y-1">
            <label className="text-xs font-medium text-slate-600">{l("টোন", "Tone")}</label>
            <div className="flex gap-1.5 flex-wrap">
              {TONES.map((t) => (
                <button
                  key={t.id}
                  onClick={() => setTone(t.id)}
                  className={cn("px-2.5 py-1 text-xs font-medium rounded-lg border transition-colors",
                    tone === t.id ? "bg-blue-600 text-white border-blue-600" : "bg-white border-slate-200 text-slate-600 hover:bg-slate-50"
                  )}
                >
                  {lang === "bn" ? t.labelBn : t.labelEn}
                </button>
              ))}
            </div>
          </div>

          <div className="space-y-1">
            <label className="text-xs font-medium text-slate-600">{l("অতিরিক্ত তথ্য", "Extra Context")}</label>
            <textarea
              value={extra}
              onChange={(e) => setExtra(e.target.value)}
              rows={2}
              placeholder={l("ঐচ্ছিক", "Optional")}
              className="w-full text-sm px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
            />
          </div>

          <Button
            onClick={handleGenerate}
            disabled={generate.isPending || !productName.trim() || !productPrice.trim()}
            className="w-full"
          >
            {generate.isPending ? (
              <><Loader2 className="h-4 w-4 animate-spin mr-2" />{l("তৈরি হচ্ছে...", "Generating...")}</>
            ) : l("ক্যাম্পেইন তৈরি করুন", "Generate Campaign")}
          </Button>
        </div>

        {/* Campaign List */}
        <div className="lg:col-span-2 space-y-4">
          <div className="flex gap-2 flex-wrap">
            <button
              onClick={() => setFilter(undefined)}
              className={cn("px-3 py-1.5 text-sm rounded-lg border transition-colors",
                !filterType ? "bg-blue-600 text-white border-blue-600" : "bg-white border-slate-200 text-slate-600 hover:bg-slate-50"
              )}
            >
              {l("সব", "All")}
            </button>
            {CAMPAIGN_TYPES.map((t) => (
              <button
                key={t.id}
                onClick={() => setFilter(t.id)}
                className={cn("px-3 py-1.5 text-sm rounded-lg border transition-colors",
                  filterType === t.id ? "bg-blue-600 text-white border-blue-600" : "bg-white border-slate-200 text-slate-600 hover:bg-slate-50"
                )}
              >
                {lang === "bn" ? t.labelBn : t.labelEn}
              </button>
            ))}
          </div>

          {campaignsQ.isLoading ? (
            <div className="space-y-3">
              {Array.from({ length: 3 }).map((_, i) => <Skeleton key={i} className="h-40 w-full" />)}
            </div>
          ) : ((campaignsQ.data ?? []) as Campaign[]).length === 0 ? (
            <div className="bg-white border border-slate-200 rounded-xl p-12 text-center">
              <Megaphone className="h-10 w-10 text-slate-300 mx-auto mb-3" />
              <p className="text-slate-400 text-sm">{l("এখনো কোনো ক্যাম্পেইন তৈরি হয়নি", "No campaigns yet — generate your first one!")}</p>
            </div>
          ) : (
            <div className="space-y-3">
              {((campaignsQ.data ?? []) as Campaign[]).map((c) => (
                <CampaignCard key={c.id} c={c} lang={lang} />
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
