"use client";

import React, { useState, useMemo } from "react";
import { format, parseISO } from "date-fns";
import {
  AlertTriangle, Package, TrendingDown, CheckCircle2,
  ArrowRightLeft, Activity, Search, Plus, Minus, ArrowUpDown,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Badge } from "@/components/ui/badge";
import AdjustmentForm from "@/components/inventory/AdjustmentForm";
import { useInventory, useInventoryAlerts, useInventoryLogs } from "@/hooks/useInventory";
import { useInventoryHealth } from "@/hooks/useAnalytics";
import { useLang } from "@/contexts/LangContext";
import { safeNum, cn } from "@/lib/utils";

const LIMIT    = 50;
const LOG_LIMIT = 30;

function safePercent(n: number, d: number) {
  if (!d) return 0;
  const p = (n / d) * 100;
  return isFinite(p) ? Math.min(p, 100) : 0;
}

function StockBadge({ qty, threshold }: { qty: number; threshold: number }) {
  if (qty === 0)
    return <span className="inline-flex px-1.5 py-0.5 rounded text-[11px] font-semibold bg-red-100 text-red-700 border border-red-200">স্টক নেই</span>;
  if (qty <= threshold)
    return <span className="inline-flex px-1.5 py-0.5 rounded text-[11px] font-semibold bg-amber-100 text-amber-700 border border-amber-200">কম স্টক</span>;
  return <span className="inline-flex px-1.5 py-0.5 rounded text-[11px] font-semibold bg-emerald-100 text-emerald-700 border border-emerald-200">ঠিকঠাক</span>;
}

const LOG_TYPE_LABEL: Record<string, string> = {
  SALE:       "বিক্রয়",
  PURCHASE:   "ক্রয়",
  ADJUSTMENT: "সমন্বয়",
  RETURN:     "ফেরত",
  DAMAGE:     "নষ্ট",
};
const LOG_TYPE_COLOR: Record<string, string> = {
  SALE:       "text-red-600",
  PURCHASE:   "text-emerald-600",
  ADJUSTMENT: "text-blue-600",
  RETURN:     "text-violet-600",
  DAMAGE:     "text-orange-600",
};

export default function InventoryPage() {
  const { lang } = useLang();
  const l = (bn: string, en: string) => lang === "bn" ? bn : en;

  const [page,       setPage]       = useState(1);
  const [logPage,    setLogPage]    = useState(1);
  const [adjustOpen, setAdjustOpen] = useState(false);
  const [activeTab,  setActiveTab]  = useState("all");
  const [search,     setSearch]     = useState("");

  const { data,        isLoading }  = useInventory({ page, limit: LIMIT });
  const { data: alertsRaw }         = useInventoryAlerts();
  const { data: health }            = useInventoryHealth();
  const { data: logsData, isLoading: logsLoading } = useInventoryLogs({ page: logPage, limit: LOG_LIMIT });

  const allItems  = Array.isArray(data?.items) ? data.items : [];
  const alerts    = Array.isArray(alertsRaw)   ? alertsRaw  : [];
  const logs      = logsData?.items ?? [];
  const logTotal  = logsData?.total ?? 0;
  const logPages  = Math.max(1, Math.ceil(logTotal / LOG_LIMIT));
  const total      = data?.total ?? 0;
  const totalPages = Math.max(1, Math.ceil(total / LIMIT));

  /* sort: out-of-stock → low-stock → ok */
  const sortedItems = useMemo(() => {
    const filtered = search
      ? allItems.filter((i) =>
          i.product_name.toLowerCase().includes(search.toLowerCase()) ||
          i.variant_name.toLowerCase().includes(search.toLowerCase()) ||
          i.sku.toLowerCase().includes(search.toLowerCase()))
      : allItems;
    return [...filtered].sort((a, b) => {
      const score = (i: typeof a) => i.stock_quantity === 0 ? 0 : i.is_low_stock ? 1 : 2;
      return score(a) - score(b);
    });
  }, [allItems, search]);

  const totalVariants = safeNum(health?.total_variants) || total;
  const lowStock      = safeNum(health?.low_stock_count) || alerts.length;
  const outOfStock    = safeNum(health?.out_of_stock_count);
  const inStock       = Math.max(0, totalVariants - lowStock - outOfStock);

  type HealthCard = { key: string; title: string; value: number; pct: number; bar: string; num: string; border: string; icon: React.ElementType; alert?: boolean };
  const HEALTH: HealthCard[] = [
    { key: "in",  title: l("পর্যাপ্ত স্টক", "Adequate Stock"),  value: inStock,    pct: safePercent(inStock, totalVariants),    bar: "bg-emerald-500", num: "text-emerald-600", border: "border-l-emerald-500", icon: CheckCircle2 },
    { key: "low", title: l("কম স্টক",        "Low Stock"),        value: lowStock,   pct: safePercent(lowStock, totalVariants),   bar: "bg-amber-500",   num: "text-amber-600",   border: "border-l-amber-500",   icon: TrendingDown, alert: lowStock > 0 },
    { key: "out", title: l("স্টক নেই",       "Out of Stock"),     value: outOfStock, pct: safePercent(outOfStock, totalVariants), bar: "bg-red-500",     num: "text-red-600",     border: "border-l-red-500",     icon: Package,      alert: outOfStock > 0 },
  ];

  return (
    <div className="space-y-4 max-w-[1500px]">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold">{l("ইনভেন্টরি ব্যবস্থাপনা", "Inventory Management")}</h1>
          <p className="text-sm text-muted-foreground">{l("স্টক পর্যবেক্ষণ ও সমন্বয়", "Monitor and adjust stock levels")}</p>
        </div>
        <Button onClick={() => setAdjustOpen(true)} size="sm" className="gap-1.5 h-8 text-xs">
          <ArrowRightLeft className="h-3.5 w-3.5" /> {l("স্টক সমন্বয়", "Adjust Stock")}
        </Button>
      </div>

      {/* KPI row */}
      <div className="grid grid-cols-3 gap-3">
        {HEALTH.map((h) => {
          const Icon = h.icon;
          return (
            <div key={h.key} className={cn("admin-card p-3.5 border-l-4", h.border, h.alert && "ring-1 ring-inset ring-amber-400 dark:ring-amber-600")}>
              <div className="flex items-center gap-2 mb-2">
                <Icon className="h-4 w-4 text-muted-foreground shrink-0" />
                <p className="text-xs text-muted-foreground">{h.title}</p>
              </div>
              <p className={cn("text-2xl font-bold tabular-nums mb-2", h.num)}>{h.value}</p>
              <div className="h-1.5 w-full rounded-full bg-muted/50 overflow-hidden">
                <div className={cn("h-full rounded-full", h.bar)} style={{ width: `${h.pct}%` }} />
              </div>
              <p className="text-[10px] text-muted-foreground mt-1">{h.pct.toFixed(0)}% {l("মোটের মধ্যে", "of total")}</p>
            </div>
          );
        })}
      </div>

      {/* Alert banner */}
      {(lowStock > 0 || outOfStock > 0) && (
        <div className="flex items-center gap-3 p-3 rounded border border-amber-200 bg-amber-50 dark:bg-amber-950/20 dark:border-amber-800">
          <AlertTriangle className="h-4 w-4 text-amber-600 shrink-0" />
          <p className="text-sm text-amber-800 dark:text-amber-300 flex-1">
            {outOfStock > 0 && <span className="font-semibold">{outOfStock}টি পণ্যের স্টক শেষ</span>}
            {outOfStock > 0 && lowStock > 0 && " · "}
            {lowStock > 0 && <span>{lowStock}টি পণ্যের স্টক কম</span>}
            {" — "}{l("অবিলম্বে রিঅর্ডার দিন", "reorder immediately")}
          </p>
          <Button size="sm" variant="outline" className="h-7 text-xs shrink-0 border-amber-300 text-amber-700"
            onClick={() => setActiveTab("alerts")}>
            {l("দেখুন", "View")}
          </Button>
        </div>
      )}

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="all">{l("সব স্টক", "All Stock")}</TabsTrigger>
          <TabsTrigger value="alerts" className="gap-1.5">
            {l("সতর্কতা", "Alerts")}
            {alerts.length > 0 && (
              <Badge variant="destructive" className="h-4 w-4 p-0 flex items-center justify-center text-[10px] rounded-full">
                {alerts.length}
              </Badge>
            )}
          </TabsTrigger>
          <TabsTrigger value="history" className="gap-1.5">
            <Activity className="h-3.5 w-3.5" />
            {l("ইতিহাস", "History")}
          </TabsTrigger>
        </TabsList>

        {/* All Stock tab */}
        <TabsContent value="all" className="mt-3 space-y-3">
          <div className="relative max-w-xs">
            <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground" />
            <Input
              placeholder={l("পণ্য বা SKU খুঁজুন...", "Search product or SKU...")}
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="pl-8 h-8 text-sm"
            />
          </div>

          {isLoading ? (
            <div className="admin-card p-4 space-y-2">
              {[1, 2, 3, 4, 5].map((i) => <Skeleton key={i} className="h-10 w-full" />)}
            </div>
          ) : sortedItems.length === 0 ? (
            <div className="admin-card py-14 text-center">
              <Package className="h-8 w-8 mx-auto mb-2 text-muted-foreground/25" />
              <p className="text-sm text-muted-foreground">{l("কোনো পণ্য পাওয়া যায়নি", "No items found")}</p>
            </div>
          ) : (
            <div className="admin-card overflow-hidden">
              <div className="overflow-x-auto">
                <table className="commerce-table">
                  <thead>
                    <tr>
                      <th>{l("পণ্য / ভ্যারিয়েন্ট", "Product / Variant")}</th>
                      <th>SKU</th>
                      <th className="text-right">
                        <span className="flex items-center justify-end gap-1">
                          <ArrowUpDown className="h-3 w-3" />{l("স্টক", "Stock")}
                        </span>
                      </th>
                      <th className="text-right">{l("সতর্কতা সীমা", "Alert Threshold")}</th>
                      <th>{l("অবস্থা", "Status")}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {sortedItems.map((item) => (
                      <tr key={item.variant_id}>
                        <td>
                          <p className="text-sm font-medium">{item.product_name}</p>
                          <p className="text-[11px] text-muted-foreground">{item.variant_name}</p>
                        </td>
                        <td className="font-mono text-[11px] text-muted-foreground">{item.sku}</td>
                        <td className="text-right">
                          <span className={cn(
                            "text-sm font-bold tabular-nums",
                            item.stock_quantity === 0 ? "text-red-600" : item.is_low_stock ? "text-amber-600" : "text-foreground"
                          )}>
                            {item.stock_quantity}
                          </span>
                        </td>
                        <td className="text-right text-xs text-muted-foreground">{item.low_stock_alert}</td>
                        <td><StockBadge qty={item.stock_quantity} threshold={item.low_stock_alert} /></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {total > LIMIT && !search && (
            <div className="flex items-center justify-between text-sm">
              <span className="text-xs text-muted-foreground">{l("পৃষ্ঠা", "Page")} {page} / {totalPages}</span>
              <div className="flex gap-2">
                <Button variant="outline" size="sm" className="h-7 text-xs" disabled={page === 1} onClick={() => setPage((p) => p - 1)}>{l("আগের", "Prev")}</Button>
                <Button variant="outline" size="sm" className="h-7 text-xs" disabled={page >= totalPages} onClick={() => setPage((p) => p + 1)}>{l("পরের", "Next")}</Button>
              </div>
            </div>
          )}
        </TabsContent>

        {/* Alerts tab */}
        <TabsContent value="alerts" className="mt-3">
          {alerts.length === 0 ? (
            <div className="admin-card py-14 text-center space-y-2">
              <CheckCircle2 className="h-8 w-8 mx-auto text-emerald-500" />
              <p className="text-sm text-muted-foreground">{l("সব স্টক পর্যাপ্ত", "All stock levels are adequate")}</p>
            </div>
          ) : (
            <div className="admin-card overflow-hidden">
              <div className="overflow-x-auto">
                <table className="commerce-table">
                  <thead>
                    <tr>
                      <th>{l("পণ্য", "Product")}</th>
                      <th>SKU</th>
                      <th className="text-right">{l("বর্তমান স্টক", "Current Stock")}</th>
                      <th className="text-right">{l("সতর্কতা সীমা", "Alert At")}</th>
                      <th>{l("অবস্থা", "Status")}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {alerts
                      .slice()
                      .sort((a, b) => a.stock_quantity - b.stock_quantity)
                      .map((item) => (
                        <tr key={item.variant_id}>
                          <td>
                            <p className="text-sm font-medium">{item.product_name}</p>
                            <p className="text-[11px] text-muted-foreground">{item.variant_name}</p>
                          </td>
                          <td className="font-mono text-[11px] text-muted-foreground">{item.sku}</td>
                          <td className="text-right">
                            <span className={cn("text-sm font-bold", item.stock_quantity === 0 ? "text-red-600" : "text-amber-600")}>
                              {item.stock_quantity}
                            </span>
                          </td>
                          <td className="text-right text-xs text-muted-foreground">{item.low_stock_alert}</td>
                          <td><StockBadge qty={item.stock_quantity} threshold={item.low_stock_alert} /></td>
                        </tr>
                      ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </TabsContent>

        {/* Movement History tab */}
        <TabsContent value="history" className="mt-3 space-y-3">
          {logsLoading ? (
            <div className="admin-card p-4 space-y-2">
              {[1, 2, 3, 4, 5].map((i) => <Skeleton key={i} className="h-10 w-full" />)}
            </div>
          ) : logs.length === 0 ? (
            <div className="admin-card py-14 text-center">
              <Activity className="h-8 w-8 mx-auto mb-2 text-muted-foreground/25" />
              <p className="text-sm text-muted-foreground">{l("কোনো ইতিহাস নেই", "No movement history")}</p>
            </div>
          ) : (
            <div className="admin-card overflow-hidden">
              <div className="overflow-x-auto">
                <table className="commerce-table">
                  <thead>
                    <tr>
                      <th>{l("তারিখ", "Date")}</th>
                      <th>{l("ধরন", "Type")}</th>
                      <th>{l("পণ্য", "Product")}</th>
                      <th className="text-right">{l("পরিবর্তন", "Change")}</th>
                      <th className="text-right">{l("পরবর্তী স্টক", "After")}</th>
                      <th>{l("নোট", "Note")}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {logs.map((log) => {
                      const dt = log.created_at ? format(parseISO(log.created_at), "dd MMM yy, HH:mm") : "—";
                      const isPos = log.quantity_change > 0;
                      return (
                        <tr key={log.id}>
                          <td className="text-[11px] text-muted-foreground whitespace-nowrap">{dt}</td>
                          <td>
                            <span className={cn("text-xs font-semibold", LOG_TYPE_COLOR[log.change_type] ?? "text-foreground")}>
                              {LOG_TYPE_LABEL[log.change_type] ?? log.change_type}
                            </span>
                          </td>
                          <td className="text-sm">{log.variant_id}</td>
                          <td className="text-right">
                            <span className={cn("text-sm font-bold flex items-center justify-end gap-0.5", isPos ? "text-emerald-600" : "text-red-600")}>
                              {isPos ? <Plus className="h-3 w-3" /> : <Minus className="h-3 w-3" />}
                              {Math.abs(log.quantity_change)}
                            </span>
                          </td>
                          <td className="text-right text-sm font-semibold tabular-nums">{log.quantity_after}</td>
                          <td className="text-xs text-muted-foreground">{log.note || "—"}</td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {logTotal > LOG_LIMIT && (
            <div className="flex items-center justify-between">
              <span className="text-xs text-muted-foreground">{l("পৃষ্ঠা", "Page")} {logPage} / {logPages}</span>
              <div className="flex gap-2">
                <Button variant="outline" size="sm" className="h-7 text-xs" disabled={logPage === 1} onClick={() => setLogPage((p) => p - 1)}>{l("আগের", "Prev")}</Button>
                <Button variant="outline" size="sm" className="h-7 text-xs" disabled={logPage >= logPages} onClick={() => setLogPage((p) => p + 1)}>{l("পরের", "Next")}</Button>
              </div>
            </div>
          )}
        </TabsContent>
      </Tabs>

      {/* Adjustment Dialog */}
      <Dialog open={adjustOpen} onOpenChange={setAdjustOpen}>
        <DialogContent>
          <DialogHeader><DialogTitle>{l("স্টক সমন্বয়", "Stock Adjustment")}</DialogTitle></DialogHeader>
          <AdjustmentForm onSuccess={() => setAdjustOpen(false)} />
        </DialogContent>
      </Dialog>
    </div>
  );
}
