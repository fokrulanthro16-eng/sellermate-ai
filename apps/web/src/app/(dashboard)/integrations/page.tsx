"use client";

import { useState, useEffect } from "react";
import {
  Truck, CreditCard, Store, Bell, FileText,
  CheckCircle2, XCircle, Loader2, RefreshCw, Save, Zap, Play,
  Download, Package,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { useLang } from "@/contexts/LangContext";
import {
  useIntegrationsStatus, useSaveIntegrationSettings, useIntegrationSettings,
  useTestConnection, useMarketplaceSync, useMarketplaceSyncStatus,
  useSendNotification, type ProviderInfo, type IntegrationConfig,
} from "@/hooks/useIntegrations";
import { cn } from "@/lib/utils";

// ── Status badge ─────────────────────────────────────────────────────────────

function ProviderBadge({ p }: { p: ProviderInfo }) {
  const isReal = p.is_configured;
  return (
    <div className="flex items-center justify-between py-2 px-3 rounded-lg bg-slate-50 border border-slate-100">
      <span className="text-sm font-medium text-slate-700">{p.display_name}</span>
      <span className={cn(
        "flex items-center gap-1 text-[11px] font-semibold px-2 py-0.5 rounded-full",
        isReal ? "bg-emerald-50 text-emerald-700 border border-emerald-200"
               : "bg-amber-50 text-amber-700 border border-amber-200"
      )}>
        {isReal ? <CheckCircle2 className="h-3 w-3" /> : <Zap className="h-3 w-3" />}
        {isReal ? "Live" : "Mock"}
      </span>
    </div>
  );
}

// ── Test button ───────────────────────────────────────────────────────────────

function TestBtn({ domain, provider, label }: { domain: string; provider: string; label: string }) {
  const test = useTestConnection();
  const [result, setResult] = useState<string | null>(null);

  const run = async () => {
    setResult(null);
    try {
      const r = await test.mutateAsync({ domain, provider });
      setResult(r.success ? `✓ ${r.message}` : `✗ ${r.message}`);
    } catch {
      setResult("✗ Connection error");
    }
    setTimeout(() => setResult(null), 4000);
  };

  return (
    <div className="flex items-center gap-2">
      <Button variant="outline" size="sm" onClick={run} disabled={test.isPending} className="h-7 text-xs gap-1.5">
        {test.isPending ? <Loader2 className="h-3 w-3 animate-spin" /> : <Play className="h-3 w-3" />}
        Test {label}
      </Button>
      {result && (
        <span className={cn("text-xs", result.startsWith("✓") ? "text-emerald-600" : "text-red-500")}>
          {result}
        </span>
      )}
    </div>
  );
}

// ── Tab ───────────────────────────────────────────────────────────────────────

const TABS = [
  { id: "courier",      icon: Truck,       labelBn: "কুরিয়ার",    labelEn: "Courier"       },
  { id: "payment",      icon: CreditCard,  labelBn: "পেমেন্ট",    labelEn: "Payment"       },
  { id: "marketplace",  icon: Store,       labelBn: "মার্কেটপ্লেস", labelEn: "Marketplace"  },
  { id: "notification", icon: Bell,        labelBn: "বিজ্ঞপ্তি",  labelEn: "Notifications" },
  { id: "documents",    icon: FileText,    labelBn: "ডকুমেন্ট",   labelEn: "Documents"     },
] as const;

type TabId = (typeof TABS)[number]["id"];

// ── Courier tab ───────────────────────────────────────────────────────────────

function CourierTab({ providers, lang, savedConfig }: { providers: ProviderInfo[]; lang: string; savedConfig?: IntegrationConfig }) {
  const l = (bn: string, en: string) => lang === "bn" ? bn : en;
  const save = useSaveIntegrationSettings();
  const [activeCourier, setActive] = useState("manual");
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    const v = (savedConfig?.courier as any)?.active_provider;
    if (v) setActive(v);
  }, [savedConfig]);

  const handleSave = async () => {
    try {
      await save.mutateAsync({ courier: { active_provider: activeCourier } });
      setSaved(true);
      setTimeout(() => setSaved(false), 2500);
    } catch { /* silent — auth handled by interceptor */ }
  };

  return (
    <div className="space-y-5">
      <div className="space-y-3">
        <h3 className="text-sm font-semibold text-slate-700">{l("কুরিয়ার প্রদানকারী", "Courier Providers")}</h3>
        {providers.map((p) => <ProviderBadge key={p.name} p={p} />)}
      </div>

      <div className="space-y-2">
        <label className="text-xs font-medium text-slate-600">{l("সক্রিয় কুরিয়ার", "Active Courier")}</label>
        <div className="grid grid-cols-2 gap-2">
          {providers.map((p) => (
            <button key={p.name} onClick={() => setActive(p.name)}
              className={cn("py-2 text-sm rounded-lg border font-medium transition-colors",
                activeCourier === p.name ? "bg-blue-600 text-white border-blue-600" : "bg-white border-slate-200 text-slate-600 hover:bg-slate-50")}>
              {p.display_name}
            </button>
          ))}
        </div>
      </div>

      <div className="space-y-2">
        <h3 className="text-xs font-semibold text-slate-600 uppercase tracking-wide">{l("সংযোগ পরীক্ষা", "Test Connection")}</h3>
        <div className="space-y-2">
          {providers.map((p) => <TestBtn key={p.name} domain="courier" provider={p.name} label={p.display_name} />)}
        </div>
      </div>

      <div className="pt-1 border-t border-slate-100">
        <p className="text-xs text-slate-400 mb-3">{l("বাস্তব সংযোগের জন্য .env ফাইলে কী যোগ করুন", "Add real API keys in .env to enable live mode")}</p>
        <Button onClick={handleSave} disabled={save.isPending} className="gap-2">
          {save.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
          {saved ? l("সংরক্ষিত ✓", "Saved ✓") : l("সেটিংস সংরক্ষণ করুন", "Save Settings")}
        </Button>
      </div>
    </div>
  );
}

// ── Payment tab ───────────────────────────────────────────────────────────────

function PaymentTab({ providers, lang, savedConfig }: { providers: ProviderInfo[]; lang: string; savedConfig?: IntegrationConfig }) {
  const l = (bn: string, en: string) => lang === "bn" ? bn : en;
  const save = useSaveIntegrationSettings();
  const [activePayment, setActive] = useState("cod");
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    const v = (savedConfig?.payment as any)?.active_provider;
    if (v) setActive(v);
  }, [savedConfig]);

  const handleSave = async () => {
    try {
      await save.mutateAsync({ payment: { active_provider: activePayment } });
      setSaved(true);
      setTimeout(() => setSaved(false), 2500);
    } catch { /* silent */ }
  };

  return (
    <div className="space-y-5">
      <div className="space-y-3">
        <h3 className="text-sm font-semibold text-slate-700">{l("পেমেন্ট গেটওয়ে", "Payment Gateways")}</h3>
        {providers.map((p) => <ProviderBadge key={p.name} p={p} />)}
      </div>

      <div className="space-y-2">
        <label className="text-xs font-medium text-slate-600">{l("ডিফল্ট পেমেন্ট মেথড", "Default Payment Method")}</label>
        <div className="grid grid-cols-2 gap-2">
          {providers.map((p) => (
            <button key={p.name} onClick={() => setActive(p.name)}
              className={cn("py-2 text-sm rounded-lg border font-medium transition-colors",
                activePayment === p.name ? "bg-blue-600 text-white border-blue-600" : "bg-white border-slate-200 text-slate-600 hover:bg-slate-50")}>
              {p.display_name}
            </button>
          ))}
        </div>
      </div>

      <div className="space-y-2">
        <h3 className="text-xs font-semibold text-slate-600 uppercase tracking-wide">{l("সংযোগ পরীক্ষা", "Test Connection")}</h3>
        <div className="space-y-2">
          {providers.map((p) => <TestBtn key={p.name} domain="payment" provider={p.name} label={p.display_name} />)}
        </div>
      </div>

      <div className="pt-1 border-t border-slate-100">
        <p className="text-xs text-slate-400 mb-3">{l("বাস্তব গেটওয়ের জন্য API কী যোগ করুন", "Add real gateway API keys in .env")}</p>
        <Button onClick={handleSave} disabled={save.isPending} className="gap-2">
          {save.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
          {saved ? l("সংরক্ষিত ✓", "Saved ✓") : l("সেটিংস সংরক্ষণ করুন", "Save Settings")}
        </Button>
      </div>
    </div>
  );
}

// ── Marketplace tab ───────────────────────────────────────────────────────────

function MarketplaceTab({ providers, lang }: { providers: ProviderInfo[]; lang: string }) {
  const l = (bn: string, en: string) => lang === "bn" ? bn : en;
  const sync = useMarketplaceSync();
  const { data: syncStatus } = useMarketplaceSyncStatus();
  const [syncResult, setSyncResult] = useState<string | null>(null);

  const handleSync = async (provider: string, type: "products" | "orders" | "all") => {
    setSyncResult(null);
    try {
      const r = await sync.mutateAsync({ provider, sync_type: type });
      if (r.success && r.data && Array.isArray((r.data as any).results)) {
        const msgs = (r.data as any).results.map((x: any) => x.message).join(" | ");
        setSyncResult(`✓ ${msgs}`);
      }
    } catch {
      setSyncResult("✗ Sync error");
    }
    setTimeout(() => setSyncResult(null), 5000);
  };

  return (
    <div className="space-y-5">
      <div className="space-y-3">
        <h3 className="text-sm font-semibold text-slate-700">{l("মার্কেটপ্লেস সংযোগ", "Marketplace Connections")}</h3>
        {providers.map((p) => <ProviderBadge key={p.name} p={p} />)}
      </div>

      <div className="space-y-2">
        <h3 className="text-xs font-semibold text-slate-600 uppercase tracking-wide">{l("সিঙ্ক কন্ট্রোল", "Sync Controls")}</h3>
        <div className="space-y-3">
          {providers.map((p) => (
            <div key={p.name} className="flex items-center gap-2 flex-wrap">
              <span className="text-sm text-slate-700 w-24">{p.display_name}</span>
              <Button variant="outline" size="sm" className="h-7 text-xs gap-1" disabled={sync.isPending}
                onClick={() => handleSync(p.name, "products")}>
                {sync.isPending ? <Loader2 className="h-3 w-3 animate-spin" /> : <Package className="h-3 w-3" />}
                {l("পণ্য সিঙ্ক", "Sync Products")}
              </Button>
              <Button variant="outline" size="sm" className="h-7 text-xs gap-1" disabled={sync.isPending}
                onClick={() => handleSync(p.name, "orders")}>
                {sync.isPending ? <Loader2 className="h-3 w-3 animate-spin" /> : <RefreshCw className="h-3 w-3" />}
                {l("অর্ডার সিঙ্ক", "Sync Orders")}
              </Button>
              <TestBtn domain="marketplace" provider={p.name} label="" />
            </div>
          ))}
        </div>
        {syncResult && <p className="text-xs text-emerald-600">{syncResult}</p>}
      </div>

      {syncStatus && Array.isArray((syncStatus as any).data) && (
        <div className="space-y-1.5 pt-2 border-t border-slate-100">
          <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wide">{l("সিঙ্ক অবস্থা", "Sync Status")}</h3>
          <div className="grid grid-cols-2 gap-2">
            {((syncStatus as any).data as Array<{provider: string; display_name: string; status: string; is_configured: boolean}>).map((s) => (
              <div key={s.provider} className="flex items-center gap-2 text-xs text-slate-500">
                <span className={cn("h-1.5 w-1.5 rounded-full shrink-0", s.status === "never_synced" ? "bg-slate-300" : "bg-emerald-400")} />
                {s.display_name}: {s.status === "never_synced" ? l("কখনো সিঙ্ক হয়নি", "Never synced") : s.status}
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="pt-1 border-t border-slate-100">
        <p className="text-xs text-slate-400">{l("বাস্তব সিঙ্কের জন্য API কী প্রয়োজন", "Real sync requires API keys in .env")}</p>
      </div>
    </div>
  );
}

// ── Notification tab ──────────────────────────────────────────────────────────

const NOTIF_TYPES = [
  { id: "low_stock",         labelBn: "স্টক কম সতর্কতা",       labelEn: "Low Stock Alert"      },
  { id: "pending_order",     labelBn: "নতুন পেন্ডিং অর্ডার",  labelEn: "Pending Order Alert"   },
  { id: "payment_reminder",  labelBn: "পেমেন্ট রিমাইন্ডার",   labelEn: "Payment Reminder"      },
  { id: "courier_update",    labelBn: "কুরিয়ার আপডেট",         labelEn: "Courier Update"        },
  { id: "customer_followup", labelBn: "গ্রাহক ফলো-আপ",         labelEn: "Customer Follow-up"   },
] as const;

function NotificationTab({ providers, lang }: { providers: ProviderInfo[]; lang: string }) {
  const l = (bn: string, en: string) => lang === "bn" ? bn : en;
  const send = useSendNotification();
  const [testResult, setTestResult] = useState<string | null>(null);
  const [channel, setChannel] = useState("inapp");
  const [notifType, setNotifType] = useState("pending_order");
  const [recipient, setRecipient] = useState("test@sellermate.app");

  const handleTest = async () => {
    setTestResult(null);
    try {
      const r = await send.mutateAsync({ channel, notification_type: notifType, recipient, extra_body: `Test from SellerMate Integrations` });
      if (r.success) {
        const d = r.data as any;
        setTestResult(`✓ ${d.status} via ${d.channel} (${d.is_mock ? "mock" : "live"}) — ID: ${d.message_id}`);
      }
    } catch {
      setTestResult("✗ Send error");
    }
    setTimeout(() => setTestResult(null), 6000);
  };

  return (
    <div className="space-y-5">
      <div className="space-y-3">
        <h3 className="text-sm font-semibold text-slate-700">{l("বিজ্ঞপ্তি চ্যানেল", "Notification Channels")}</h3>
        {providers.map((p) => <ProviderBadge key={p.name} p={p} />)}
      </div>

      <div className="space-y-3">
        <h3 className="text-xs font-semibold text-slate-600 uppercase tracking-wide">{l("বিজ্ঞপ্তি টাইপ", "Notification Types")}</h3>
        <div className="grid grid-cols-1 gap-1.5">
          {NOTIF_TYPES.map((t) => (
            <div key={t.id} className="flex items-center gap-2 py-1.5 px-3 bg-slate-50 rounded-lg border border-slate-100">
              <CheckCircle2 className="h-3.5 w-3.5 text-emerald-500 shrink-0" />
              <span className="text-xs text-slate-700">{lang === "bn" ? t.labelBn : t.labelEn}</span>
            </div>
          ))}
        </div>
      </div>

      <div className="space-y-3 pt-2 border-t border-slate-100">
        <h3 className="text-xs font-semibold text-slate-600 uppercase tracking-wide">{l("টেস্ট বিজ্ঞপ্তি পাঠান", "Send Test Notification")}</h3>
        <div className="space-y-2">
          <div className="flex gap-2">
            {providers.map((p) => (
              <button key={p.name} onClick={() => setChannel(p.name)}
                className={cn("px-2.5 py-1 text-xs rounded border font-medium",
                  channel === p.name ? "bg-blue-600 text-white border-blue-600" : "bg-white border-slate-200 text-slate-600")}>
                {p.display_name}
              </button>
            ))}
          </div>
          <div className="flex gap-2">
            {NOTIF_TYPES.slice(0, 3).map((t) => (
              <button key={t.id} onClick={() => setNotifType(t.id)}
                className={cn("px-2 py-0.5 text-[10px] rounded border font-medium",
                  notifType === t.id ? "bg-slate-700 text-white border-slate-700" : "bg-white border-slate-200 text-slate-500")}>
                {lang === "bn" ? t.labelBn : t.labelEn}
              </button>
            ))}
          </div>
          <input type="text" value={recipient} onChange={(e) => setRecipient(e.target.value)}
            placeholder="Recipient (email / phone / user ID)"
            className="w-full h-9 px-3 text-sm border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
          <Button onClick={handleTest} disabled={send.isPending || !recipient} size="sm" className="gap-2">
            {send.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Bell className="h-4 w-4" />}
            {l("টেস্ট পাঠান", "Send Test")}
          </Button>
          {testResult && <p className="text-xs text-emerald-600 break-all">{testResult}</p>}
        </div>
      </div>
    </div>
  );
}

// ── Documents tab ─────────────────────────────────────────────────────────────

function DocumentsTab({ lang }: { lang: string }) {
  const l = (bn: string, en: string) => lang === "bn" ? bn : en;
  const [orderId, setOrderId] = useState("");
  const [orderNum, setOrderNum] = useState("ORD-001");
  const [courier, setCourier] = useState("manual");
  const [busy, setBusy] = useState<string | null>(null);

  const download = async (type: "invoice" | "label") => {
    if (!orderId.trim()) return;
    setBusy(type);
    try {
      if (type === "invoice") {
        const { downloadInvoice } = await import("@/hooks/useIntegrations");
        await downloadInvoice(orderId, orderNum);
      } else {
        const { downloadShippingLabel } = await import("@/hooks/useIntegrations");
        await downloadShippingLabel(orderId, orderNum, courier);
      }
    } catch {
      // silent fail
    } finally {
      setBusy(null);
    }
  };

  return (
    <div className="space-y-5">
      <div className="space-y-3">
        <h3 className="text-sm font-semibold text-slate-700">{l("ডকুমেন্ট জেনারেটর", "Document Generator")}</h3>
        <p className="text-xs text-slate-500">{l("অর্ডার আইডি দিয়ে ইনভয়েস ও শিপিং লেবেল ডাউনলোড করুন", "Enter an order ID to download invoice or shipping label PDF")}</p>
      </div>

      <div className="space-y-3">
        <div className="space-y-1">
          <label className="text-xs font-medium text-slate-600">{l("অর্ডার UUID", "Order UUID")}</label>
          <input type="text" value={orderId} onChange={(e) => setOrderId(e.target.value)}
            placeholder="e.g. 3fa85f64-5717-4562-b3fc-2c963f66afa6"
            className="w-full h-9 px-3 text-sm border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
        </div>
        <div className="space-y-1">
          <label className="text-xs font-medium text-slate-600">{l("অর্ডার নম্বর (ফাইলনেম)", "Order Number (filename)")}</label>
          <input type="text" value={orderNum} onChange={(e) => setOrderNum(e.target.value)}
            placeholder="ORD-001"
            className="w-full h-9 px-3 text-sm border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
        </div>
        <div className="space-y-1">
          <label className="text-xs font-medium text-slate-600">{l("কুরিয়ার (শিপিং লেবেলের জন্য)", "Courier (for label)")}</label>
          <div className="flex gap-2">
            {["manual", "pathao", "steadfast", "redx"].map((c) => (
              <button key={c} onClick={() => setCourier(c)}
                className={cn("px-2.5 py-1.5 text-xs rounded border font-medium capitalize",
                  courier === c ? "bg-blue-600 text-white border-blue-600" : "bg-white border-slate-200 text-slate-600")}>
                {c}
              </button>
            ))}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3">
        <Button variant="outline" onClick={() => download("invoice")} disabled={!orderId.trim() || busy === "invoice"} className="gap-2">
          {busy === "invoice" ? <Loader2 className="h-4 w-4 animate-spin" /> : <Download className="h-4 w-4" />}
          {l("ইনভয়েস PDF", "Invoice PDF")}
        </Button>
        <Button variant="outline" onClick={() => download("label")} disabled={!orderId.trim() || busy === "label"} className="gap-2">
          {busy === "label" ? <Loader2 className="h-4 w-4 animate-spin" /> : <Download className="h-4 w-4" />}
          {l("শিপিং লেবেল", "Shipping Label")}
        </Button>
      </div>

      <div className="rounded-lg bg-blue-50 border border-blue-200 p-3 text-xs text-blue-800 space-y-1">
        <p className="font-semibold">{l("কীভাবে ব্যবহার করবেন:", "How to use:")}</p>
        <p>{l("১. অর্ডার পেজ থেকে অর্ডার UUID কপি করুন", "1. Copy an Order UUID from the Orders page")}</p>
        <p>{l("২. এখানে পেস্ট করুন এবং ডাউনলোড করুন", "2. Paste here and click download")}</p>
        <p>{l("৩. শিপিং লেবেলে ট্র্যাকিং নম্বর স্বয়ংক্রিয়ভাবে তৈরি হবে", "3. Tracking ID is auto-generated if not set")}</p>
      </div>
    </div>
  );
}

// ── Main page ─────────────────────────────────────────────────────────────────

export default function IntegrationsPage() {
  const { lang } = useLang();
  const l = (bn: string, en: string) => lang === "bn" ? bn : en;
  const [tab, setTab] = useState<TabId>("courier");

  const { data: status, isLoading } = useIntegrationsStatus();
  const { data: settingsRes } = useIntegrationSettings();
  const savedConfig = (settingsRes as any)?.data as IntegrationConfig | undefined;

  return (
    <div className="p-6 max-w-5xl space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-slate-900">{l("ইন্টিগ্রেশন কেন্দ্র", "Integration Center")}</h1>
        <p className="text-sm text-slate-500 mt-1">
          {l("কুরিয়ার, পেমেন্ট, মার্কেটপ্লেস ও বিজ্ঞপ্তি সংযোগ পরিচালনা করুন", "Manage courier, payment, marketplace and notification connections")}
        </p>
      </div>

      {/* Provider status summary */}
      {isLoading ? (
        <div className="grid grid-cols-4 gap-3">
          {Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-20 w-full" />)}
        </div>
      ) : status && (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
          {[
            { domain: "courier",      label: l("কুরিয়ার", "Courier"),       providers: status.courier      },
            { domain: "payment",      label: l("পেমেন্ট", "Payment"),       providers: status.payment      },
            { domain: "marketplace",  label: l("মার্কেটপ্লেস", "Marketplace"), providers: status.marketplace },
            { domain: "notification", label: l("বিজ্ঞপ্তি", "Notifications"), providers: status.notification },
          ].map(({ domain, label, providers }) => {
            const live = providers.filter((p) => p.is_configured).length;
            return (
              <div key={domain} className="bg-white border border-slate-200 rounded-xl p-4 text-center">
                <p className="text-xs text-slate-500 mb-1">{label}</p>
                <p className="text-2xl font-bold text-slate-800">{live}/{providers.length}</p>
                <p className="text-[10px] text-slate-400">{l("লাইভ সংযোগ", "live connections")}</p>
              </div>
            );
          })}
        </div>
      )}

      {/* Tab bar */}
      <div className="flex gap-1 overflow-x-auto bg-slate-100 p-1 rounded-xl">
        {TABS.map((t) => {
          const Icon = t.icon;
          return (
            <button key={t.id} onClick={() => setTab(t.id)}
              className={cn(
                "flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm font-medium transition-all whitespace-nowrap",
                tab === t.id ? "bg-white text-slate-900 shadow-sm" : "text-slate-500 hover:text-slate-700"
              )}>
              <Icon className="h-4 w-4" />
              {lang === "bn" ? t.labelBn : t.labelEn}
            </button>
          );
        })}
      </div>

      {/* Tab content */}
      <div className="bg-white border border-slate-200 rounded-xl p-6">
        {isLoading ? (
          <div className="space-y-3">{Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-12" />)}</div>
        ) : (
          <>
            {tab === "courier"      && <CourierTab      providers={status?.courier      ?? []} lang={lang} savedConfig={savedConfig} />}
            {tab === "payment"      && <PaymentTab      providers={status?.payment      ?? []} lang={lang} savedConfig={savedConfig} />}
            {tab === "marketplace"  && <MarketplaceTab  providers={status?.marketplace  ?? []} lang={lang} />}
            {tab === "notification" && <NotificationTab providers={status?.notification ?? []} lang={lang} />}
            {tab === "documents"    && <DocumentsTab lang={lang} />}
          </>
        )}
      </div>
    </div>
  );
}
