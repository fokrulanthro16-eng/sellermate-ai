"use client";

import { useState, useMemo } from "react";
import { subDays, format } from "date-fns";
import {
  useRevenue, useOrderBreakdown, useTopProducts, useCustomerMetrics,
} from "@/hooks/useAnalytics";
import StatCard from "@/components/analytics/StatCard";
import RevenueChart from "@/components/analytics/RevenueChart";
import OrdersChart from "@/components/analytics/OrdersChart";
import TopProducts from "@/components/analytics/TopProducts";
import { Users, ShoppingBag, TrendingUp, Repeat, Crown, BarChart2 } from "lucide-react";
import { formatCurrency, cn } from "@/lib/utils";
import { useLang } from "@/contexts/LangContext";

const PERIODS = [
  { labelBn: "৭ দিন",   labelEn: "7 days",   days: 7   },
  { labelBn: "৩০ দিন",  labelEn: "30 days",  days: 30  },
  { labelBn: "৯০ দিন",  labelEn: "90 days",  days: 90  },
  { labelBn: "১৮০ দিন", labelEn: "180 days", days: 180 },
];

const RANK_STYLES = [
  "bg-amber-500/10 text-amber-600 dark:bg-amber-500/20 dark:text-amber-400",
  "bg-slate-300/30 text-slate-600 dark:bg-slate-600/30 dark:text-slate-300",
  "bg-orange-500/10 text-orange-700 dark:bg-orange-500/20 dark:text-orange-400",
];

export default function AnalyticsPage() {
  const [days, setDays] = useState(30);
  const { lang } = useLang();
  const label = (bn: string, en: string) => lang === "bn" ? bn : en;

  const to   = useMemo(() => format(new Date(), "yyyy-MM-dd"), []);
  const from = useMemo(() => format(subDays(new Date(), days), "yyyy-MM-dd"), [days]);

  const { data: revenue, isLoading: revLoading } = useRevenue(from, to, "daily");
  const { data: breakdown, isLoading: brkLoading } = useOrderBreakdown(from, to);
  const { data: topProducts } = useTopProducts(from, to);
  const { data: customerMetrics, isLoading: custLoading } = useCustomerMetrics(from, to);

  return (
    <div className="space-y-6 max-w-[1600px]">
      {/* ── Header ────────────────────────────────────────── */}
      <div className="flex items-start justify-between flex-wrap gap-4 animate-slide-up">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <BarChart2 className="h-4 w-4 text-primary" />
            <span className="text-sm text-muted-foreground font-medium">
              {label("বিশ্লেষণ কেন্দ্র", "Analytics Hub")}
            </span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight gradient-text">
            {label("বিশ্লেষণ", "Analytics")}
          </h1>
          <p className="text-sm text-muted-foreground mt-0.5">
            {label("বিক্রয়, গ্রাহক ও প্রবণতা বিশ্লেষণ", "Sales, customers & trend analysis")}
          </p>
        </div>

        {/* Period pills */}
        <div className="flex items-center gap-1 bg-muted/60 p-1 rounded-xl border border-border/50">
          {PERIODS.map((p) => (
            <button
              key={p.days}
              onClick={() => setDays(p.days)}
              className={cn(
                "px-3.5 py-1.5 text-sm rounded-lg transition-all duration-200 font-medium",
                days === p.days
                  ? "bg-background text-foreground shadow-sm border border-border/50"
                  : "text-muted-foreground hover:text-foreground"
              )}
            >
              {lang === "bn" ? p.labelBn : p.labelEn}
            </button>
          ))}
        </div>
      </div>

      {/* ── Customer KPI Cards ────────────────────────────── */}
      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
        <div className="animate-slide-up animation-delay-100">
          <StatCard
            title={label("নতুন গ্রাহক", "New Customers")}
            value={String(customerMetrics?.new_customers ?? 0)}
            icon={Users}
            variant="blue"
            loading={custLoading}
            subtitle={label("নির্বাচিত সময়ে", "In selected period")}
          />
        </div>
        <div className="animate-slide-up animation-delay-200">
          <StatCard
            title={label("পুনরায় কেনা", "Returning")}
            value={String(customerMetrics?.returning_customers ?? 0)}
            icon={Repeat}
            variant="violet"
            loading={custLoading}
            subtitle={label("বারবার কেনা গ্রাহক", "Repeat buyers")}
          />
        </div>
        <div className="animate-slide-up animation-delay-300">
          <StatCard
            title={label("শীর্ষ গ্রাহক", "Top Customers")}
            value={String(customerMetrics?.top_customers?.length ?? 0)}
            icon={TrendingUp}
            variant="emerald"
            loading={custLoading}
            subtitle={label("সর্বোচ্চ ব্যয়কারী", "Highest spenders")}
          />
        </div>
        <div className="animate-slide-up animation-delay-400">
          <StatCard
            title={label("শীর্ষ গ্রাহকের ব্যয়", "Top Buyer Spend")}
            value={
              customerMetrics?.top_customers?.[0]
                ? formatCurrency(String(customerMetrics.top_customers[0].total_spent))
                : formatCurrency("0")
            }
            icon={ShoppingBag}
            variant="amber"
            loading={custLoading}
            subtitle={label("১ম গ্রাহকের মোট ব্যয়", "First ranked customer")}
          />
        </div>
      </div>

      {/* ── Revenue + Orders ──────────────────────────────── */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-4">
        <div className="xl:col-span-2 animate-slide-up animation-delay-100">
          <RevenueChart
            data={revenue || []}
            loading={revLoading}
            title={label("রাজস্ব প্রবণতা", "Revenue Trend")}
          />
        </div>
        <div className="animate-slide-up animation-delay-200">
          <OrdersChart data={breakdown?.by_status} loading={brkLoading} />
        </div>
      </div>

      {/* ── Top Products + Top Customers ─────────────────── */}
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
        <div className="animate-slide-up animation-delay-100">
          <TopProducts data={topProducts || []} loading={false} />
        </div>

        {/* Top Customers */}
        <div className="animate-slide-up animation-delay-200">
          <div className="admin-card p-4 h-full flex flex-col">
            <div className="flex items-center gap-3 mb-5">
              <div className="h-8 w-8 rounded-lg bg-amber-500/10 dark:bg-amber-500/20 flex items-center justify-center">
                <Crown className="h-4 w-4 text-amber-600 dark:text-amber-400" />
              </div>
              <div>
                <h3 className="text-sm font-semibold">{label("শীর্ষ গ্রাহক", "Top Customers")}</h3>
                <p className="text-xs text-muted-foreground">{label("সর্বোচ্চ ব্যয়কারী", "Highest spenders")}</p>
              </div>
            </div>

            {custLoading ? (
              <div className="divide-y divide-border/40">
                {[1, 2, 3, 4, 5].map((i) => (
                  <div key={i} className="flex items-center gap-3 py-3">
                    <div className="h-7 w-7 rounded-lg bg-muted animate-pulse shrink-0" />
                    <div className="flex-1 space-y-1.5">
                      <div className="h-4 w-3/4 rounded-lg bg-muted animate-pulse" />
                      <div className="h-3 w-1/3 rounded-lg bg-muted animate-pulse" />
                    </div>
                    <div className="h-5 w-16 rounded-lg bg-muted animate-pulse" />
                  </div>
                ))}
              </div>
            ) : !customerMetrics?.top_customers?.length ? (
              <div className="flex-1 flex flex-col items-center justify-center gap-2 py-8 text-muted-foreground">
                <Users className="h-8 w-8 opacity-40" />
                <p className="text-sm">{label("কোনো ডেটা নেই", "No data available")}</p>
              </div>
            ) : (
              <div className="divide-y divide-border/40">
                {customerMetrics.top_customers.slice(0, 7).map((c, i) => {
                  const rankStyle = RANK_STYLES[i] ?? "bg-muted text-muted-foreground";
                  return (
                    <div key={c.customer_id} className="flex items-center gap-3 py-3 first:pt-0 last:pb-0 group">
                      <div className={cn(
                        "flex h-7 w-7 items-center justify-center rounded-lg text-xs font-bold shrink-0",
                        rankStyle,
                      )}>
                        {i + 1}
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium truncate text-foreground group-hover:text-primary transition-colors">
                          {c.customer_name || label("অজ্ঞাত", "Unknown")}
                        </p>
                        <p className="text-xs text-muted-foreground">
                          {c.total_orders} {label("অর্ডার", "orders")}
                        </p>
                      </div>
                      <p className="text-sm font-bold tabular-nums shrink-0">
                        {formatCurrency(String(c.total_spent))}
                      </p>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
