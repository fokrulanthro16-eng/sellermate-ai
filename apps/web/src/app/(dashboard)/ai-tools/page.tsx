"use client";

import { useState } from "react";
import {
  Wand2, Copy, CheckCheck, FileText, Image, Hash,
  Package, Tag, MessageCircle, CalendarCheck, ChevronDown,
  Loader2, Zap,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useLang } from "@/contexts/LangContext";
import { useToolProducts, useGenerateContent, type GenerateOut } from "@/hooks/useSellerTools";
import { useProviderStatus } from "@/hooks/useProviderStatus";
import { cn } from "@/lib/utils";

// ── Tool definitions ────────────────────────────────────────────────────────

const TOOLS = [
  { id: "post",         icon: FileText,      labelBn: "ফেসবুক পোস্ট",  labelEn: "FB Post",     needsProduct: true,  needsOrder: false },
  { id: "caption",      icon: Image,         labelBn: "ক্যাপশন",        labelEn: "Caption",     needsProduct: true,  needsOrder: false },
  { id: "hashtag",      icon: Hash,          labelBn: "হ্যাশট্যাগ",     labelEn: "Hashtags",    needsProduct: true,  needsOrder: false },
  { id: "description",  icon: Package,       labelBn: "পণ্য বিবরণ",     labelEn: "Description", needsProduct: true,  needsOrder: false },
  { id: "offer",        icon: Tag,           labelBn: "অফার টেক্সট",    labelEn: "Offer Text",  needsProduct: true,  needsOrder: false },
  { id: "reply",        icon: MessageCircle, labelBn: "গ্রাহক রিপ্লাই", labelEn: "Customer Reply", needsProduct: false, needsOrder: true },
  { id: "daily_action", icon: CalendarCheck, labelBn: "দৈনিক অ্যাকশন", labelEn: "Daily Action", needsProduct: false, needsOrder: false },
] as const;

type ToolId = (typeof TOOLS)[number]["id"];

const TONES = [
  { id: "friendly",     labelBn: "বন্ধুত্বপূর্ণ", labelEn: "Friendly" },
  { id: "professional", labelBn: "পেশাদার",        labelEn: "Professional" },
  { id: "urgent",       labelBn: "জরুরি",          labelEn: "Urgent" },
] as const;

// ── Source badge ─────────────────────────────────────────────────────────────

function SourceBadge({ source }: { source: string }) {
  const labels: Record<string, { label: string; color: string }> = {
    gemini:     { label: "Gemini AI", color: "text-blue-600 bg-blue-50 border-blue-200" },
    anthropic:  { label: "Claude AI", color: "text-purple-600 bg-purple-50 border-purple-200" },
    rule_based: { label: "Rule-based", color: "text-slate-600 bg-slate-50 border-slate-200" },
  };
  const meta = labels[source] ?? { label: source, color: "text-slate-600 bg-slate-50 border-slate-200" };
  return (
    <span className={cn("text-[10px] font-medium px-2 py-0.5 rounded border", meta.color)}>
      {meta.label}
    </span>
  );
}

// ── Output box ────────────────────────────────────────────────────────────────

function OutputBox({ result }: { result: GenerateOut | null }) {
  const [copied, setCopied] = useState(false);
  const { lang } = useLang();
  const l = (bn: string, en: string) => lang === "bn" ? bn : en;

  if (!result) {
    return (
      <div className="admin-card p-6 flex flex-col items-center justify-center min-h-[200px] text-center text-muted-foreground border-dashed">
        <Wand2 className="h-10 w-10 mb-3 opacity-20" />
        <p className="text-sm">{l("উপরে টুল ও সেটিংস বেছে নিন, তারপর Generate করুন", "Select a tool and settings above, then click Generate")}</p>
      </div>
    );
  }

  const handleCopy = () => {
    navigator.clipboard.writeText(result.text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="admin-card overflow-hidden">
      <div className="flex items-center justify-between px-4 py-2.5 border-b border-border">
        <div className="flex items-center gap-2">
          <Zap className="h-4 w-4 text-primary" />
          <span className="text-sm font-semibold">{l("তৈরি হওয়া টেক্সট", "Generated Text")}</span>
          <SourceBadge source={result.source} />
        </div>
        <Button variant="ghost" size="sm" className="h-7 gap-1.5 text-xs" onClick={handleCopy}>
          {copied ? <CheckCheck className="h-3.5 w-3.5 text-emerald-500" /> : <Copy className="h-3.5 w-3.5" />}
          {copied ? l("কপি হয়েছে!", "Copied!") : l("কপি করুন", "Copy")}
        </Button>
      </div>
      <div className="p-4">
        <pre className="text-sm leading-relaxed whitespace-pre-wrap font-sans text-foreground">{result.text}</pre>
      </div>
    </div>
  );
}

// ── Main page ─────────────────────────────────────────────────────────────────

export default function AIToolsPage() {
  const { lang } = useLang();
  const l = (bn: string, en: string) => lang === "bn" ? bn : en;

  const [activeTool, setActiveTool] = useState<ToolId>("post");
  const [activeLang, setActiveLang] = useState(lang === "bn" ? "bn" : "en");
  const [tone, setTone]             = useState("friendly");
  const [productId, setProductId]   = useState("");
  const [orderId, setOrderId]       = useState("");
  const [extraCtx, setExtraCtx]     = useState("");
  const [result, setResult]         = useState<GenerateOut | null>(null);

  const { data: products, isLoading: productsLoading } = useToolProducts();
  const generate = useGenerateContent();
  const { data: providerStatus } = useProviderStatus();

  const toolMeta = TOOLS.find((t) => t.id === activeTool)!;

  const handleGenerate = async () => {
    const res = await generate.mutateAsync({
      tool: activeTool,
      lang: activeLang,
      tone,
      product_id: toolMeta.needsProduct && productId ? productId : undefined,
      order_id: toolMeta.needsOrder && orderId ? orderId : undefined,
      extra_context: extraCtx || undefined,
    });
    setResult(res);
  };

  return (
    <div className="space-y-5 max-w-[900px]">
      {/* Header */}
      <div className="flex items-start justify-between gap-3">
        <div>
          <h1 className="text-xl font-bold">{l("এআই সেলার টুলস", "AI Seller Tools")}</h1>
          <p className="text-sm text-muted-foreground">
            {l("মার্কেটিং টেক্সট, পোস্ট, অফার ও গ্রাহক রিপ্লাই এআই দিয়ে তৈরি করুন", "Generate marketing posts, captions, offers and customer replies with AI")}
          </p>
        </div>
        {providerStatus && (
          <span className={cn(
            "shrink-0 text-[11px] font-semibold px-2.5 py-1 rounded-full border",
            providerStatus.is_mock
              ? "bg-slate-100 text-slate-600 border-slate-300"
              : "bg-emerald-50 text-emerald-700 border-emerald-300"
          )}>
            AI Mode: {providerStatus.display_label}
          </span>
        )}
      </div>

      {/* Tool selector */}
      <div className="admin-card p-4">
        <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-3">
          {l("টুল বেছে নিন", "Select Tool")}
        </p>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
          {TOOLS.map((tool) => {
            const Icon = tool.icon;
            const isActive = activeTool === tool.id;
            return (
              <button
                key={tool.id}
                onClick={() => { setActiveTool(tool.id); setResult(null); }}
                className={cn(
                  "flex flex-col items-center gap-1.5 rounded-lg p-3 border text-xs font-medium transition-all",
                  isActive
                    ? "border-primary bg-primary/5 text-primary"
                    : "border-border hover:border-primary/40 hover:bg-muted/50 text-muted-foreground hover:text-foreground"
                )}
              >
                <Icon className="h-5 w-5" />
                <span>{lang === "bn" ? tool.labelBn : tool.labelEn}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Controls */}
      <div className="admin-card p-4 space-y-4">
        <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
          {l("সেটিংস", "Settings")}
        </p>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {/* Language */}
          <div className="space-y-1.5">
            <label className="text-xs font-medium text-muted-foreground">{l("ভাষা", "Language")}</label>
            <div className="flex gap-2">
              {(["bn", "en"] as const).map((lc) => (
                <button
                  key={lc}
                  onClick={() => setActiveLang(lc)}
                  className={cn(
                    "flex-1 py-2 rounded-md text-sm font-medium border transition-all",
                    activeLang === lc
                      ? "border-primary bg-primary/5 text-primary"
                      : "border-border text-muted-foreground hover:border-primary/40"
                  )}
                >
                  {lc === "bn" ? "বাংলা" : "English"}
                </button>
              ))}
            </div>
          </div>

          {/* Tone */}
          <div className="space-y-1.5">
            <label className="text-xs font-medium text-muted-foreground">{l("টোন", "Tone")}</label>
            <div className="flex gap-2">
              {TONES.map((t) => (
                <button
                  key={t.id}
                  onClick={() => setTone(t.id)}
                  className={cn(
                    "flex-1 py-2 rounded-md text-xs font-medium border transition-all",
                    tone === t.id
                      ? "border-primary bg-primary/5 text-primary"
                      : "border-border text-muted-foreground hover:border-primary/40"
                  )}
                >
                  {lang === "bn" ? t.labelBn : t.labelEn}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Product selector */}
        {toolMeta.needsProduct && (
          <div className="space-y-1.5">
            <label className="text-xs font-medium text-muted-foreground">
              {l("পণ্য বেছে নিন (ঐচ্ছিক)", "Select Product (optional)")}
            </label>
            {productsLoading ? (
              <Skeleton className="h-9 w-full" />
            ) : (
              <Select value={productId} onValueChange={setProductId}>
                <SelectTrigger className="h-9 text-sm">
                  <SelectValue placeholder={l("পণ্য নির্বাচন করুন...", "Select a product...")} />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="">{l("— পণ্য ছাড়া জেনারেট করুন —", "— Generate without product —")}</SelectItem>
                  {(products ?? []).map((p) => (
                    <SelectItem key={p.id} value={p.id}>
                      {lang === "bn" && p.name_bangla ? p.name_bangla : p.name}
                      {p.sale_price ? ` — ৳${p.sale_price}` : p.base_price ? ` — ৳${p.base_price}` : ""}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            )}
            {products && products.length === 0 && (
              <p className="text-xs text-muted-foreground">{l("কোনো পণ্য পাওয়া যায়নি", "No products found")}</p>
            )}
          </div>
        )}

        {/* Order ID input for reply tool */}
        {toolMeta.needsOrder && (
          <div className="space-y-1.5">
            <label className="text-xs font-medium text-muted-foreground">
              {l("অর্ডার আইডি (ঐচ্ছিক)", "Order ID (optional)")}
            </label>
            <input
              type="text"
              value={orderId}
              onChange={(e) => setOrderId(e.target.value)}
              placeholder={l("অর্ডার UUID পেস্ট করুন...", "Paste order UUID...")}
              className="w-full h-9 px-3 text-sm border border-input rounded-md bg-background focus:outline-none focus:ring-1 focus:ring-ring"
            />
          </div>
        )}

        {/* Extra context */}
        <div className="space-y-1.5">
          <label className="text-xs font-medium text-muted-foreground">
            {l("অতিরিক্ত তথ্য (ঐচ্ছিক)", "Extra context (optional)")}
          </label>
          <textarea
            value={extraCtx}
            onChange={(e) => setExtraCtx(e.target.value)}
            rows={2}
            placeholder={l("বিশেষ নির্দেশনা বা তথ্য যোগ করুন...", "Add special instructions or context...")}
            className="w-full px-3 py-2 text-sm border border-input rounded-md bg-background focus:outline-none focus:ring-1 focus:ring-ring resize-none"
          />
        </div>

        {/* Generate button */}
        <Button
          onClick={handleGenerate}
          disabled={generate.isPending}
          className="w-full gap-2"
          size="lg"
        >
          {generate.isPending
            ? <><Loader2 className="h-4 w-4 animate-spin" />{l("তৈরি হচ্ছে...", "Generating...")}</>
            : <><Wand2 className="h-4 w-4" />{l("টেক্সট তৈরি করুন", "Generate")}</>
          }
        </Button>
      </div>

      {/* Output */}
      <OutputBox result={result} />

      {/* Daily Action Box info */}
      {activeTool === "daily_action" && !result && (
        <div className="flex items-start gap-3 p-3 rounded-lg bg-blue-50 border border-blue-200 text-blue-800 text-xs">
          <CalendarCheck className="h-4 w-4 mt-0.5 shrink-0" />
          <p>
            {l(
              "দৈনিক অ্যাকশন বক্স আপনার সংরক্ষিত AI বিশ্লেষণের ভিত্তিতে কাজের তালিকা তৈরি করে। প্রথমে AI সেন্টার থেকে এজেন্ট চালান।",
              "Daily Action Box generates a task list based on your saved AI analysis. Run agents from AI Center first for best results."
            )}
          </p>
        </div>
      )}
    </div>
  );
}
