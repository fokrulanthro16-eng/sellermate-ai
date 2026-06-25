"use client";

import { useState } from "react";
import { Clock, Filter, Package, ShoppingCart, Users, CreditCard, Truck, Settings2, Download } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { useLang } from "@/contexts/LangContext";
import { useAuditLogs, useAuditSummary } from "@/hooks/useAuditLogs";
import { cn } from "@/lib/utils";

const ACTION_COLORS: Record<string, string> = {
  create:        "bg-emerald-100 text-emerald-700",
  update:        "bg-blue-100 text-blue-700",
  delete:        "bg-red-100 text-red-700",
  status_change: "bg-amber-100 text-amber-700",
  export:        "bg-purple-100 text-purple-700",
  login:         "bg-slate-100 text-slate-600",
  logout:        "bg-slate-100 text-slate-600",
};

const RESOURCE_ICONS: Record<string, React.ElementType> = {
  order:    ShoppingCart,
  product:  Package,
  customer: Users,
  payment:  CreditCard,
  courier:  Truck,
  settings: Settings2,
  backup:   Download,
};

function ActionBadge({ action }: { action: string }) {
  return (
    <span className={cn("inline-block text-[10px] font-semibold px-2 py-0.5 rounded-full uppercase tracking-wide",
      ACTION_COLORS[action] ?? "bg-slate-100 text-slate-600")}>
      {action.replace("_", " ")}
    </span>
  );
}

function ResourceIcon({ type }: { type: string }) {
  const Icon = RESOURCE_ICONS[type] ?? Settings2;
  return <Icon className="h-4 w-4 text-slate-400 shrink-0" />;
}

function timeAgo(iso: string) {
  const diff = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  return new Date(iso).toLocaleDateString("en-BD");
}

const FILTERS = ["all", "order", "product", "customer", "payment", "courier", "backup"] as const;

export default function ActivityPage() {
  const { lang } = useLang();
  const l = (bn: string, en: string) => lang === "bn" ? bn : en;
  const [filter, setFilter] = useState<string>("all");
  const [page, setPage] = useState(1);

  const { data, isLoading } = useAuditLogs({
    page,
    resource_type: filter === "all" ? undefined : filter,
  });
  const { data: summary } = useAuditSummary();

  const logs = data?.logs ?? [];
  const total = data?.total ?? 0;
  const totalPages = Math.ceil(total / (data?.limit ?? 50));

  return (
    <div className="p-6 max-w-4xl space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-slate-900">{l("কার্যকলাপ লগ", "Activity Log")}</h1>
        <p className="text-sm text-slate-500 mt-1">
          {l("সকল কার্যক্রমের ইতিহাস", "Complete audit trail of all actions")}
        </p>
      </div>

      {/* Summary counts */}
      {summary && (
        <div className="flex flex-wrap gap-2">
          {Object.entries(summary).map(([action, count]) => (
            <span key={action} className={cn("text-xs font-medium px-2.5 py-1 rounded-full",
              ACTION_COLORS[action] ?? "bg-slate-100 text-slate-600")}>
              {action.replace("_", " ")}: {count}
            </span>
          ))}
        </div>
      )}

      {/* Filter bar */}
      <div className="flex items-center gap-2 flex-wrap">
        <Filter className="h-4 w-4 text-slate-400" />
        {FILTERS.map((f) => (
          <button key={f} onClick={() => { setFilter(f); setPage(1); }}
            className={cn("px-3 py-1 text-xs rounded-full border font-medium transition-colors capitalize",
              filter === f ? "bg-blue-600 text-white border-blue-600" : "bg-white border-slate-200 text-slate-600 hover:bg-slate-50")}>
            {f === "all" ? l("সব", "All") : f}
          </button>
        ))}
      </div>

      {/* Log list */}
      <div className="bg-white border border-slate-200 rounded-xl divide-y divide-slate-100">
        {isLoading ? (
          Array.from({ length: 8 }).map((_, i) => (
            <div key={i} className="flex items-start gap-3 p-4">
              <Skeleton className="h-8 w-8 rounded-full" />
              <div className="flex-1 space-y-2">
                <Skeleton className="h-4 w-3/4" />
                <Skeleton className="h-3 w-1/4" />
              </div>
            </div>
          ))
        ) : logs.length === 0 ? (
          <div className="py-16 text-center">
            <Clock className="h-10 w-10 text-slate-300 mx-auto mb-3" />
            <p className="text-sm text-slate-500">{l("কোনো কার্যক্রম পাওয়া যায়নি", "No activity yet")}</p>
            <p className="text-xs text-slate-400 mt-1">{l("অর্ডার, পণ্য বা পেমেন্ট পরিবর্তন করলে এখানে দেখাবে", "Actions on orders, products and payments appear here")}</p>
          </div>
        ) : logs.map((log) => (
          <div key={log.id} className="flex items-start gap-3 p-4 hover:bg-slate-50 transition-colors">
            <div className="mt-0.5 h-8 w-8 rounded-full bg-slate-100 flex items-center justify-center shrink-0">
              <ResourceIcon type={log.resource_type} />
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 flex-wrap">
                <ActionBadge action={log.action} />
                <span className="text-sm font-medium text-slate-700 capitalize">{log.resource_type}</span>
                {log.resource_label && (
                  <span className="text-sm text-slate-500 truncate max-w-[200px]">{log.resource_label}</span>
                )}
              </div>
              {log.details && Object.keys(log.details).length > 0 && (
                <p className="text-xs text-slate-400 mt-0.5">
                  {Object.entries(log.details).map(([k, v]) => `${k}: ${v}`).join(" · ")}
                </p>
              )}
            </div>
            <span className="text-[11px] text-slate-400 shrink-0 mt-0.5">{timeAgo(log.created_at)}</span>
          </div>
        ))}
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between pt-2">
          <p className="text-xs text-slate-400">{total} {l("মোট রেকর্ড", "total records")}</p>
          <div className="flex gap-2">
            <Button variant="outline" size="sm" onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page === 1}>
              {l("আগে", "Prev")}
            </Button>
            <span className="text-xs text-slate-500 self-center">
              {page} / {totalPages}
            </span>
            <Button variant="outline" size="sm" onClick={() => setPage(p => Math.min(totalPages, p + 1))} disabled={page >= totalPages}>
              {l("পরে", "Next")}
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
