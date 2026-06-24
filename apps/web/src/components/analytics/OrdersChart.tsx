"use client";

import {
  PieChart, Pie, Cell, Tooltip, ResponsiveContainer, TooltipProps,
} from "recharts";
import { useTheme } from "next-themes";
import { ShoppingCart } from "lucide-react";
import { useLang } from "@/contexts/LangContext";

const STATUS_META: Record<string, { label: string; labelEn: string; color: string }> = {
  DELIVERED:  { label: "ডেলিভারড",    labelEn: "Delivered",   color: "#22c55e" },
  PENDING:    { label: "মুলতুবি",      labelEn: "Pending",     color: "#f59e0b" },
  CONFIRMED:  { label: "নিশ্চিত",      labelEn: "Confirmed",   color: "#3b82f6" },
  PROCESSING: { label: "প্রক্রিয়াধীন", labelEn: "Processing",  color: "#8b5cf6" },
  SHIPPED:    { label: "শিপড",         labelEn: "Shipped",     color: "#06b6d4" },
  CANCELLED:  { label: "বাতিল",        labelEn: "Cancelled",   color: "#ef4444" },
  RETURNED:   { label: "ফেরত",         labelEn: "Returned",    color: "#f97316" },
};

interface OrdersChartProps {
  data?: Record<string, number>;
  loading?: boolean;
}

function CustomTooltip({ active, payload }: TooltipProps<number, string>) {
  if (!active || !payload?.length) return null;
  const { name, value } = payload[0];
  return (
    <div className="admin-card px-3 py-2 text-sm min-w-[120px]">
      <p className="font-semibold text-foreground">{name}</p>
      <p className="text-muted-foreground text-xs">{value} অর্ডার</p>
    </div>
  );
}

export default function OrdersChart({ data, loading }: OrdersChartProps) {
  const { resolvedTheme } = useTheme();
  const { lang } = useLang();
  const isDark = resolvedTheme === "dark";

  const chartData = Object.entries(data || {}).map(([status, count]) => {
    const meta = STATUS_META[status] ?? { label: status, labelEn: status, color: "#94a3b8" };
    return {
      name: lang === "bn" ? meta.label : meta.labelEn,
      value: count,
      color: meta.color,
    };
  }).filter((d) => d.value > 0);

  const total = chartData.reduce((s, d) => s + d.value, 0);

  if (loading) {
    return (
      <div className="admin-card p-4 h-full">
        <div className="flex items-center gap-3 mb-5">
          <div className="h-8 w-8 rounded-lg bg-muted animate-pulse" />
          <div className="h-4 w-32 rounded-lg bg-muted animate-pulse" />
        </div>
        <div className="h-[200px] w-full rounded-xl bg-muted/50 animate-pulse" />
        <div className="mt-4 space-y-2">
          {[1, 2, 3].map((i) => <div key={i} className="h-4 rounded-lg bg-muted animate-pulse" />)}
        </div>
      </div>
    );
  }

  return (
    <div className="admin-card p-4 h-full flex flex-col">
      {/* Header */}
      <div className="flex items-center gap-3 mb-4">
        <div className="h-8 w-8 rounded-lg bg-violet-500/10 dark:bg-violet-500/20 flex items-center justify-center">
          <ShoppingCart className="h-4 w-4 text-violet-600 dark:text-violet-400" />
        </div>
        <div>
          <h3 className="text-sm font-semibold">{lang === "bn" ? "অর্ডার বিভাজন" : "Order Breakdown"}</h3>
          <p className="text-xs text-muted-foreground">{lang === "bn" ? "মোট" : "Total"}: {total}</p>
        </div>
      </div>

      {chartData.length === 0 ? (
        <div className="flex-1 flex items-center justify-center text-sm text-muted-foreground">
          {lang === "bn" ? "কোনো ডেটা নেই" : "No data"}
        </div>
      ) : (
        <>
          {/* Donut */}
          <div className="relative">
            <ResponsiveContainer width="100%" height={200}>
              <PieChart>
                <Pie
                  data={chartData}
                  cx="50%"
                  cy="50%"
                  innerRadius={62}
                  outerRadius={90}
                  paddingAngle={2}
                  dataKey="value"
                  strokeWidth={0}
                >
                  {chartData.map((entry, i) => (
                    <Cell key={i} fill={entry.color} opacity={0.9} />
                  ))}
                </Pie>
                <Tooltip content={<CustomTooltip />} />
              </PieChart>
            </ResponsiveContainer>
            {/* Center label */}
            <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
              <div className="text-center">
                <p className="text-2xl font-bold">{total}</p>
                <p className="text-[10px] text-muted-foreground leading-tight">
                  {lang === "bn" ? "মোট অর্ডার" : "Total orders"}
                </p>
              </div>
            </div>
          </div>

          {/* Legend */}
          <div className="mt-3 space-y-2">
            {chartData.slice(0, 5).map((d, i) => (
              <div key={i} className="flex items-center justify-between text-xs">
                <div className="flex items-center gap-2">
                  <span className="h-2 w-2 rounded-full shrink-0" style={{ backgroundColor: d.color }} />
                  <span className="text-muted-foreground">{d.name}</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="font-semibold tabular-nums">{d.value}</span>
                  <span className="text-muted-foreground/60 w-9 text-right">
                    {total > 0 ? `${Math.round((d.value / total) * 100)}%` : "0%"}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
