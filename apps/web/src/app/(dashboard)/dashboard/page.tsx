"use client";

import { useMemo } from "react";
import { format, subDays, parseISO } from "date-fns";
import Link from "next/link";
import {
  useDashboard, useOrderBreakdown, useTopProducts, useInventoryHealth,
} from "@/hooks/useAnalytics";
import { useOrders } from "@/hooks/useOrders";
import { useLang } from "@/contexts/LangContext";
import { formatCurrency, safeNum, cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import {
  ShoppingCart, Clock, Truck, AlertTriangle,
  TrendingUp, Banknote, Package, Plus, CheckCircle2,
  ArrowRight, Sparkles,
} from "lucide-react";

/* ── tiny status pill ─────────────────────────────────────── */
function SPill({ s }: { s: string }) {
  const MAP: Record<string, string> = {
    PENDING: "status-pending", CONFIRMED: "status-confirmed",
    PROCESSING: "status-processing", SHIPPED: "status-shipped",
    DELIVERED: "status-delivered", CANCELLED: "status-cancelled",
    RETURNED: "status-returned",
  };
  const LBL: Record<string, string> = {
    PENDING: "পেন্ডিং", CONFIRMED: "নিশ্চিত", PROCESSING: "প্রক্রিয়া",
    SHIPPED: "পাঠানো", DELIVERED: "ডেলিভারি", CANCELLED: "বাতিল", RETURNED: "ফেরত",
  };
  return <span className={cn("inline-flex px-1.5 py-0.5 rounded text-[11px] font-semibold", MAP[s] ?? "bg-muted text-foreground")}>{LBL[s] ?? s}</span>;
}
function PPill({ s }: { s: string }) {
  const MAP: Record<string, string> = { UNPAID: "pay-unpaid", PARTIAL: "pay-partial", PAID: "pay-paid", REFUNDED: "pay-refunded" };
  const LBL: Record<string, string> = { UNPAID: "বাকি", PARTIAL: "আংশিক", PAID: "পরিশোধ", REFUNDED: "ফেরত" };
  return <span className={cn("inline-flex px-1.5 py-0.5 rounded text-[11px] font-semibold", MAP[s] ?? "bg-muted text-foreground")}>{LBL[s] ?? s}</span>;
}

/* ── main ─────────────────────────────────────────────────── */
export default function DashboardPage() {
  const { lang } = useLang();
  const l = (bn: string, en: string) => lang === "bn" ? bn : en;

  const today     = useMemo(() => format(new Date(), "yyyy-MM-dd"), []);
  const from30    = useMemo(() => format(subDays(new Date(), 30), "yyyy-MM-dd"), []);

  const { data: dash,   isLoading: dashL  } = useDashboard();
  const { data: bd30                       } = useOrderBreakdown(from30, today);
  const { data: bdToday                    } = useOrderBreakdown(today, today);
  const { data: inv                        } = useInventoryHealth();
  const { data: top                        } = useTopProducts(from30, today);
  const { data: recentData                 } = useOrders({ page: 1, limit: 10 });
  /* COD pending = orders unpaid with COD method */
  const { data: codData                    } = useOrders({ page: 1, limit: 1, payment_status: "UNPAID" });

  const recent  = recentData?.items ?? [];
  const byS30   = (bd30?.by_status  as Record<string, number> | undefined) ?? {};
  const bySToday= (bdToday?.by_status as Record<string, number> | undefined) ?? {};
  const todayTotal = Object.values(bySToday).reduce((a, b) => a + b, 0);
  const pending30  = safeNum(byS30.PENDING);
  const shipped30  = safeNum(byS30.SHIPPED);
  const lowStock   = safeNum(inv?.low_stock_count) + safeNum(inv?.out_of_stock_count);
  const codPending = codData?.total ?? 0;

  /* ── AI action box: compute 3 tasks ─────────────────────── */
  const tasks: { icon: React.ElementType; text: string; href: string; color: string }[] = [];
  if (pending30 > 0)
    tasks.push({ icon: Clock,          text: l(`${pending30}টি পেন্ডিং অর্ডার কনফার্ম করুন`, `Confirm ${pending30} pending orders`),         href: "/orders?status=PENDING",  color: "text-amber-600" });
  if (lowStock > 0)
    tasks.push({ icon: AlertTriangle,  text: l(`${lowStock}টি পণ্যের স্টক কম — রিঅর্ডার দিন`, `${lowStock} products low on stock — reorder`), href: "/inventory",              color: "text-orange-600" });
  if (codPending > 0)
    tasks.push({ icon: Banknote,       text: l(`${codPending}টি COD অর্ডারের পেমেন্ট কালেক্ট করুন`, `Collect payment for ${codPending} COD orders`), href: "/orders?payment_status=UNPAID", color: "text-red-600" });
  if (shipped30 > 0 && tasks.length < 3)
    tasks.push({ icon: Truck,          text: l(`${shipped30}টি অর্ডার কুরিয়ারে আছে — ট্র্যাক করুন`, `${shipped30} orders with courier — track them`), href: "/orders?status=SHIPPED",  color: "text-violet-600" });
  const topTask = top?.[0];
  if (topTask && tasks.length < 3)
    tasks.push({ icon: Package,        text: l(`"${topTask.product_name}" সবচেয়ে বেশি বিক্রি হচ্ছে — স্টক চেক করুন`, `"${topTask.product_name}" is top seller — check stock`), href: "/inventory", color: "text-blue-600" });
  while (tasks.length < 3)
    tasks.push({ icon: CheckCircle2,   text: l("সব ভালো চলছে!", "Everything looks good!"),  href: "/dashboard", color: "text-green-600" });

  const KPIS = [
    { label: l("আজকের অর্ডার", "Today's Orders"),     value: dashL ? null : todayTotal,                       icon: ShoppingCart, cls: "text-blue-700 dark:text-blue-400",    bg: "bg-blue-100 dark:bg-blue-900/40",    border: "border-l-blue-500" },
    { label: l("পেন্ডিং অর্ডার", "Pending Orders"),   value: dashL ? null : pending30,                        icon: Clock,        cls: "text-amber-700 dark:text-amber-400",  bg: "bg-amber-100 dark:bg-amber-900/40",  border: "border-l-amber-500", alert: pending30 > 5 },
    { label: l("আজকের রাজস্ব", "Today's Revenue"),    value: dashL ? null : formatCurrency(safeNum(dash?.today_revenue)), icon: TrendingUp,   cls: "text-emerald-700 dark:text-emerald-400", bg: "bg-emerald-100 dark:bg-emerald-900/40", border: "border-l-emerald-500" },
    { label: l("COD বাকি", "COD Pending"),              value: codPending,                                      icon: Banknote,     cls: "text-red-700 dark:text-red-400",      bg: "bg-red-100 dark:bg-red-900/40",      border: "border-l-red-500",   alert: codPending > 0 },
    { label: l("কুরিয়ারে আছে", "With Courier"),       value: dashL ? null : shipped30,                        icon: Truck,        cls: "text-violet-700 dark:text-violet-400",bg: "bg-violet-100 dark:bg-violet-900/40",border: "border-l-violet-500" },
    { label: l("কম স্টক", "Low Stock"),                value: lowStock,                                        icon: AlertTriangle,cls: "text-orange-700 dark:text-orange-400",bg: "bg-orange-100 dark:bg-orange-900/40",border: "border-l-orange-500", alert: lowStock > 0 },
  ];

  return (
    <div className="space-y-4 max-w-[1500px]">

      {/* header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-lg font-bold">{l("ড্যাশবোর্ড", "Dashboard")}</h1>
          <p className="text-xs text-muted-foreground">{format(new Date(), "dd MMM yyyy")} · {l("আজকের সারাংশ", "Today's summary")}</p>
        </div>
        <Button asChild size="sm" className="gap-1.5 h-8 text-xs">
          <Link href="/orders"><Plus className="h-3.5 w-3.5" />{l("নতুন অর্ডার", "New Order")}</Link>
        </Button>
      </div>

      {/* KPI row */}
      <div className="grid grid-cols-2 sm:grid-cols-3 xl:grid-cols-6 gap-3">
        {KPIS.map((k) => {
          const Icon = k.icon;
          return (
            <div key={k.label} className={cn("admin-card p-3.5 border-l-4 relative", k.border, k.alert && "ring-1 ring-inset ring-amber-400 dark:ring-amber-600")}>
              <div className={cn("h-7 w-7 rounded flex items-center justify-center mb-2.5", k.bg)}>
                <Icon className={cn("h-3.5 w-3.5", k.cls)} />
              </div>
              {k.value === null ? (
                <Skeleton className="h-6 w-16 mb-1" />
              ) : (
                <p className="text-[22px] font-bold tabular-nums leading-tight">{k.value}</p>
              )}
              <p className="text-[11px] text-muted-foreground mt-0.5 leading-tight">{k.label}</p>
            </div>
          );
        })}
      </div>

      {/* AI action box */}
      <div className="admin-card p-4 border-l-4 border-l-primary">
        <div className="flex items-center gap-2 mb-3">
          <Sparkles className="h-4 w-4 text-primary" />
          <p className="text-sm font-semibold">{l("আজ এই ৩টা কাজ করুন", "Do these 3 things today")}</p>
        </div>
        <div className="space-y-2">
          {tasks.slice(0, 3).map((task, i) => {
            const Icon = task.icon;
            return (
              <Link key={i} href={task.href} className="flex items-center gap-3 p-2.5 rounded border border-border hover:bg-accent hover:border-primary/30 transition-colors group">
                <span className="h-6 w-6 rounded-full bg-muted flex items-center justify-center shrink-0 text-xs font-bold text-muted-foreground">{i + 1}</span>
                <Icon className={cn("h-4 w-4 shrink-0", task.color)} />
                <span className="text-sm flex-1">{task.text}</span>
                <ArrowRight className="h-3.5 w-3.5 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity" />
              </Link>
            );
          })}
        </div>
      </div>

      {/* recent orders + top products */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-4">

        {/* recent orders table */}
        <div className="xl:col-span-2 admin-card overflow-hidden">
          <div className="flex items-center justify-between px-4 py-2.5 border-b border-border">
            <p className="text-sm font-semibold">{l("সাম্প্রতিক অর্ডার", "Recent Orders")}</p>
            <Link href="/orders" className="text-xs text-primary hover:underline flex items-center gap-1">
              {l("সব দেখুন", "View all")} <ArrowRight className="h-3 w-3" />
            </Link>
          </div>
          {recent.length === 0 ? (
            <div className="py-10 text-center text-xs text-muted-foreground">
              <ShoppingCart className="h-7 w-7 mx-auto mb-2 opacity-20" />
              {l("কোনো অর্ডার নেই", "No orders yet")}
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="commerce-table">
                <thead>
                  <tr>
                    <th>{l("অর্ডার#", "Order#")}</th>
                    <th>{l("গ্রাহক", "Customer")}</th>
                    <th>{l("ফোন", "Phone")}</th>
                    <th>{l("অবস্থা", "Status")}</th>
                    <th>{l("পেমেন্ট", "Payment")}</th>
                    <th className="text-right">{l("পরিমাণ", "Amount")}</th>
                    <th>{l("তারিখ", "Date")}</th>
                  </tr>
                </thead>
                <tbody>
                  {recent.map((o) => {
                    const ref = o.order_number ?? `#${o.id.slice(-6).toUpperCase()}`;
                    const dt  = o.created_at ? format(parseISO(o.created_at), "dd MMM") : "—";
                    return (
                      <tr key={o.id}>
                        <td>
                          <Link href={`/orders/${o.id}`} className="font-mono text-[11px] font-semibold text-primary hover:underline">{ref}</Link>
                        </td>
                        <td className="text-sm">{o.customer_name || "—"}</td>
                        <td className="font-mono text-[11px] text-muted-foreground">{o.customer_phone || "—"}</td>
                        <td><SPill s={o.status} /></td>
                        <td><PPill s={o.payment_status} /></td>
                        <td className="text-right text-sm font-semibold">{formatCurrency(o.total_amount)}</td>
                        <td className="text-[11px] text-muted-foreground whitespace-nowrap">{dt}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* top products */}
        <div className="admin-card overflow-hidden">
          <div className="flex items-center justify-between px-4 py-2.5 border-b border-border">
            <p className="text-sm font-semibold">{l("শীর্ষ পণ্য (৩০দিন)", "Top Products (30d)")}</p>
            <Link href="/products" className="text-xs text-primary hover:underline">{l("সব", "All")}</Link>
          </div>
          {!top || top.length === 0 ? (
            <div className="py-10 text-center text-xs text-muted-foreground">
              <Package className="h-7 w-7 mx-auto mb-2 opacity-20" />
              {l("ডেটা নেই", "No data")}
            </div>
          ) : (
            <div className="divide-y divide-border">
              {top.slice(0, 8).map((p, i) => (
                <div key={p.product_id ?? i} className="flex items-center gap-2.5 px-4 py-2 hover:bg-muted/40">
                  <span className="text-[11px] font-bold text-muted-foreground w-4 shrink-0">{i + 1}</span>
                  <div className="flex-1 min-w-0">
                    <p className="text-xs font-medium truncate">{p.product_name}</p>
                    <p className="text-[10px] text-muted-foreground">{p.total_quantity}{l("টি বিক্রি", " sold")}</p>
                  </div>
                  <p className="text-xs font-semibold shrink-0">{formatCurrency(p.total_revenue)}</p>
                </div>
              ))}
            </div>
          )}
        </div>

      </div>
    </div>
  );
}
