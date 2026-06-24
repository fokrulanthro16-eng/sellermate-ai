"use client";

import { useState } from "react";
import {
  AlertTriangle, Package, TrendingDown, CheckCircle2, ArrowRightLeft, Activity,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Badge } from "@/components/ui/badge";
import InventoryTable from "@/components/inventory/InventoryTable";
import AdjustmentForm from "@/components/inventory/AdjustmentForm";
import { useInventory, useInventoryAlerts } from "@/hooks/useInventory";
import { useInventoryHealth } from "@/hooks/useAnalytics";
import { useLang } from "@/contexts/LangContext";
import { safeNum, cn } from "@/lib/utils";

const LIMIT = 50;

function safePercent(n: number, d: number) {
  if (!d) return 0;
  const p = (n / d) * 100;
  return isFinite(p) ? Math.min(p, 100) : 0;
}

export default function InventoryPage() {
  const { t, lang } = useLang();
  const label = (bn: string, en: string) => lang === "bn" ? bn : en;

  const [page, setPage] = useState(1);
  const [adjustOpen, setAdjustOpen] = useState(false);
  const [activeTab, setActiveTab] = useState("all");
  const { data, isLoading } = useInventory({ page, limit: LIMIT });
  const { data: alertsRaw } = useInventoryAlerts();
  const { data: health } = useInventoryHealth();

  const inventoryItems = Array.isArray(data?.items) ? data.items : [];
  const alerts = Array.isArray(alertsRaw) ? alertsRaw : [];
  const total = data?.total ?? 0;
  const totalPages = Math.max(1, Math.ceil(total / LIMIT));

  const totalVariants = safeNum(health?.total_variants) || total;
  const lowStock   = safeNum(health?.low_stock_count) || alerts.length;
  const outOfStock = safeNum(health?.out_of_stock_count);
  const inStock    = Math.max(0, totalVariants - lowStock - outOfStock);

  const HEALTH_CARDS = [
    {
      key: "in",
      title: t("adequateStock"),
      value: inStock,
      percent: safePercent(inStock, totalVariants),
      icon: CheckCircle2,
      barColor: "bg-emerald-500",
      numColor: "text-emerald-600 dark:text-emerald-400",
      iconBg: "bg-emerald-100 dark:bg-emerald-900/40",
      iconColor: "text-emerald-600 dark:text-emerald-400",
      borderAccent: "border-emerald-200/60 dark:border-emerald-800/40",
    },
    {
      key: "low",
      title: t("lowStock"),
      value: lowStock,
      percent: safePercent(lowStock, totalVariants),
      icon: TrendingDown,
      barColor: "bg-amber-500",
      numColor: "text-amber-600 dark:text-amber-400",
      iconBg: "bg-amber-100 dark:bg-amber-900/40",
      iconColor: "text-amber-600 dark:text-amber-400",
      borderAccent: "border-amber-200/60 dark:border-amber-800/40",
    },
    {
      key: "out",
      title: t("outOfStock"),
      value: outOfStock,
      percent: safePercent(outOfStock, totalVariants),
      icon: Package,
      barColor: "bg-red-500",
      numColor: "text-red-600 dark:text-red-400",
      iconBg: "bg-red-100 dark:bg-red-900/40",
      iconColor: "text-red-600 dark:text-red-400",
      borderAccent: "border-red-200/60 dark:border-red-800/40",
    },
  ] as const;

  return (
    <div className="space-y-4 max-w-[1400px]">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-xl font-bold">{t("inventoryMgmt")}</h1>
          <p className="text-sm text-muted-foreground">{t("monitorStock")}</p>
        </div>
        <Button onClick={() => setAdjustOpen(true)} className="gap-2 rounded-xl">
          <ArrowRightLeft className="h-4 w-4" /> {t("stockAdjust")}
        </Button>
      </div>

      {/* Health summary cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 animate-slide-up animation-delay-100">
        {HEALTH_CARDS.map((card) => {
          const Icon = card.icon;
          return (
            <div
              key={card.key}
              className={cn("admin-card p-4 border-l-4", card.borderAccent)}
            >
              <div className="flex items-center gap-3 mb-3">
                <div className={cn("h-9 w-9 rounded-xl flex items-center justify-center shrink-0", card.iconBg)}>
                  <Icon className={cn("h-4.5 w-4.5", card.iconColor)} style={{ width: 18, height: 18 }} />
                </div>
                <p className="text-sm font-medium text-muted-foreground">{card.title}</p>
              </div>
              <p className={cn("text-3xl font-bold tabular-nums mb-3", card.numColor)}>{card.value}</p>
              <div className="h-1.5 w-full rounded-full bg-muted/50 overflow-hidden">
                <div
                  className={cn("h-full rounded-full transition-all duration-700", card.barColor)}
                  style={{ width: `${card.percent}%` }}
                />
              </div>
              <p className="text-xs text-muted-foreground mt-1.5 tabular-nums">
                {card.percent.toFixed(0)}% {label("মোট ভ্যারিয়েন্টের", "of total variants")}
              </p>
            </div>
          );
        })}
      </div>

      {/* Alert banner */}
      {alerts.length > 0 && (
        <div className="flex items-start gap-3 p-4 rounded-2xl bg-amber-50 dark:bg-amber-950/20 border border-amber-200 dark:border-amber-800 animate-slide-up animation-delay-200">
          <AlertTriangle className="h-5 w-5 text-amber-500 shrink-0 mt-0.5" />
          <div className="flex-1 min-w-0">
            <p className="text-sm font-semibold text-amber-800 dark:text-amber-300">{t("lowStockAlert")}</p>
            <p className="text-sm text-amber-700 dark:text-amber-400">
              {t("lowStockBanner").replace("{{n}}", String(alerts.length))}
            </p>
          </div>
          <Button
            size="sm"
            variant="outline"
            className="shrink-0 rounded-xl border-amber-300 text-amber-700 hover:bg-amber-100 dark:text-amber-300 dark:border-amber-700 dark:hover:bg-amber-950"
            onClick={() => setActiveTab("alerts")}
          >
            {label("দেখুন", "View")}
          </Button>
        </div>
      )}

      {/* Tabs */}
      <div className="animate-slide-up animation-delay-300">
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="rounded-xl">
            <TabsTrigger value="all" className="rounded-lg">{t("allInventory")}</TabsTrigger>
            <TabsTrigger value="alerts" className="gap-2 rounded-lg">
              {t("alerts")}
              {alerts.length > 0 && (
                <Badge variant="destructive" className="h-4 w-4 p-0 flex items-center justify-center text-[10px] rounded-full">
                  {alerts.length}
                </Badge>
              )}
            </TabsTrigger>
          </TabsList>

          <TabsContent value="all" className="mt-4">
            <InventoryTable items={inventoryItems} loading={isLoading} />
            {total > LIMIT && (
              <div className="flex items-center justify-center gap-3 mt-4">
                <Button variant="outline" size="sm" className="rounded-xl" disabled={page === 1} onClick={() => setPage((p) => p - 1)}>{t("prev")}</Button>
                <span className="text-sm text-muted-foreground tabular-nums">{page} / {totalPages}</span>
                <Button variant="outline" size="sm" className="rounded-xl" disabled={page >= totalPages} onClick={() => setPage((p) => p + 1)}>{t("next")}</Button>
              </div>
            )}
          </TabsContent>

          <TabsContent value="alerts" className="mt-4">
            {!alertsRaw ? (
              <div className="space-y-2">{[1, 2, 3].map((i) => <Skeleton key={i} className="h-16 w-full rounded-xl" />)}</div>
            ) : alerts.length === 0 ? (
              <div className="glass-card rounded-2xl py-12 text-center space-y-2">
                <CheckCircle2 className="h-10 w-10 mx-auto text-emerald-500" />
                <p className="text-muted-foreground font-medium">{t("noAlerts")}</p>
                <p className="text-sm text-muted-foreground">{t("allStockAdequate")}</p>
              </div>
            ) : (
              <div className="space-y-2">
                {alerts.map((item) => (
                  <div key={item.variant_id} className="glass-card rounded-xl border-amber-200/60 dark:border-amber-800/40 border p-4 flex items-center justify-between gap-4">
                    <div className="min-w-0 flex items-center gap-3">
                      <div className="h-8 w-8 rounded-lg bg-amber-100 dark:bg-amber-900/40 flex items-center justify-center shrink-0">
                        <AlertTriangle className="h-4 w-4 text-amber-600 dark:text-amber-400" />
                      </div>
                      <div>
                        <p className="font-semibold text-sm truncate">{item.product_name}</p>
                        <p className="text-xs text-muted-foreground">
                          {item.variant_name} · SKU: <span className="font-mono">{item.sku}</span>
                        </p>
                      </div>
                    </div>
                    <div className="text-right shrink-0">
                      <p className="text-sm font-bold text-destructive">{t("stockLabel")}: {item.stock_quantity}</p>
                      <p className="text-xs text-muted-foreground">{t("thresholdLabel")}: {item.low_stock_alert}</p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </TabsContent>
        </Tabs>
      </div>

      <Dialog open={adjustOpen} onOpenChange={setAdjustOpen}>
        <DialogContent>
          <DialogHeader><DialogTitle>{t("stockAdjust")}</DialogTitle></DialogHeader>
          <AdjustmentForm onSuccess={() => setAdjustOpen(false)} />
        </DialogContent>
      </Dialog>
    </div>
  );
}
