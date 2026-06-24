"use client";

import Link from "next/link";
import { ArrowRight, Package, TrendingUp } from "lucide-react";
import { Button } from "@/components/ui/button";
import { formatCurrency, cn } from "@/lib/utils";
import { useLang } from "@/contexts/LangContext";
import type { TopProductItem } from "@/types";

interface TopProductsProps {
  data?: TopProductItem[];
  loading?: boolean;
}

const RANK_STYLES = [
  "bg-amber-500/10 text-amber-600 dark:bg-amber-500/20 dark:text-amber-400",
  "bg-slate-300/30 text-slate-600 dark:bg-slate-600/30 dark:text-slate-300",
  "bg-orange-500/10 text-orange-700 dark:bg-orange-500/20 dark:text-orange-400",
];

function SkeletonRow() {
  return (
    <div className="flex items-center gap-3 py-3">
      <div className="h-8 w-8 rounded-lg bg-muted animate-pulse shrink-0" />
      <div className="flex-1 space-y-1.5">
        <div className="h-4 w-3/4 rounded-lg bg-muted animate-pulse" />
        <div className="h-3 w-1/2 rounded-lg bg-muted animate-pulse" />
      </div>
      <div className="h-5 w-16 rounded-lg bg-muted animate-pulse" />
    </div>
  );
}

export default function TopProducts({ data, loading }: TopProductsProps) {
  const { lang } = useLang();
  const label = (bn: string, en: string) => lang === "bn" ? bn : en;

  const maxRevenue = data?.[0]?.total_revenue ?? 1;

  return (
    <div className="glass-card rounded-2xl p-5 flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between mb-5">
        <div className="flex items-center gap-3">
          <div className="h-8 w-8 rounded-lg bg-primary/10 dark:bg-primary/20 flex items-center justify-center">
            <TrendingUp className="h-4 w-4 text-primary" />
          </div>
          <div>
            <h3 className="text-sm font-semibold">{label("শীর্ষ পণ্য", "Top Products")}</h3>
            <p className="text-xs text-muted-foreground">{label("বিক্রয় অনুযায়ী", "By revenue")}</p>
          </div>
        </div>
        <Button asChild variant="ghost" size="sm" className="gap-1 text-xs text-muted-foreground hover:text-foreground rounded-lg">
          <Link href="/products">
            {label("সব দেখুন", "View all")}
            <ArrowRight className="h-3.5 w-3.5" />
          </Link>
        </Button>
      </div>

      {/* List */}
      {loading ? (
        <div className="divide-y divide-border/50">
          {[1, 2, 3, 4, 5].map((i) => <SkeletonRow key={i} />)}
        </div>
      ) : !data?.length ? (
        <div className="flex-1 flex flex-col items-center justify-center gap-2 py-8 text-muted-foreground">
          <Package className="h-8 w-8 opacity-40" />
          <p className="text-sm">{label("কোনো ডেটা নেই", "No data available")}</p>
        </div>
      ) : (
        <div className="divide-y divide-border/40">
          {data.map((product, i) => {
            const barPct = maxRevenue > 0 ? (product.total_revenue / maxRevenue) * 100 : 0;
            const rankStyle = RANK_STYLES[i] ?? "bg-muted text-muted-foreground";

            return (
              <div
                key={product.product_id}
                className="py-3 first:pt-0 last:pb-0 group"
              >
                <div className="flex items-start gap-3">
                  {/* Rank badge */}
                  <div className={cn(
                    "flex h-7 w-7 items-center justify-center rounded-lg text-xs font-bold shrink-0 mt-0.5",
                    rankStyle,
                  )}>
                    {i + 1}
                  </div>

                  {/* Info */}
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium truncate text-foreground group-hover:text-primary transition-colors">
                      {product.product_name}
                    </p>
                    <div className="flex items-center gap-3 mt-1">
                      <span className="text-xs text-muted-foreground">
                        {product.total_quantity} {label("পিস", "units")}
                      </span>
                      {/* Mini bar */}
                      <div className="flex-1 h-1 rounded-full bg-muted/60 overflow-hidden max-w-[80px]">
                        <div
                          className="h-full rounded-full bg-primary/60 transition-all duration-700"
                          style={{ width: `${barPct}%` }}
                        />
                      </div>
                    </div>
                  </div>

                  {/* Revenue */}
                  <div className="text-sm font-bold text-foreground tabular-nums shrink-0">
                    {formatCurrency(product.total_revenue)}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
