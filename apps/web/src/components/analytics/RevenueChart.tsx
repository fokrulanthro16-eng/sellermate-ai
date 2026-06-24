"use client";

import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, TooltipProps,
} from "recharts";
import { useTheme } from "next-themes";
import { TrendingUp } from "lucide-react";
import { cn } from "@/lib/utils";
import type { RevenuePoint } from "@/types";

interface RevenueChartProps {
  data?: RevenuePoint[];
  loading?: boolean;
  title?: string;
}

function CustomTooltip({ active, payload, label }: TooltipProps<number, string>) {
  if (!active || !payload?.length) return null;
  const revenue = payload.find((p) => p.dataKey === "revenue")?.value ?? 0;
  const orders  = payload.find((p) => p.dataKey === "orders")?.value ?? 0;

  return (
    <div className="glass-card rounded-xl p-3 shadow-premium text-sm min-w-[140px]">
      <p className="text-muted-foreground text-xs mb-2 font-medium">{label}</p>
      <p className="font-bold text-foreground">
        ৳{Number(revenue).toLocaleString("en-BD")}
      </p>
      <p className="text-muted-foreground text-xs mt-0.5">{orders} অর্ডার</p>
    </div>
  );
}

function ChartSkeleton() {
  return (
    <div className="glass-card rounded-2xl p-5">
      <div className="flex items-center justify-between mb-5">
        <div className="h-5 w-32 rounded-lg bg-muted animate-pulse" />
        <div className="h-5 w-20 rounded-lg bg-muted animate-pulse" />
      </div>
      <div className="h-[260px] w-full rounded-xl bg-muted/50 animate-pulse" />
    </div>
  );
}

export default function RevenueChart({ data, loading, title }: RevenueChartProps) {
  const { resolvedTheme } = useTheme();
  const isDark = resolvedTheme === "dark";

  if (loading) return <ChartSkeleton />;

  const totalRevenue = (data || []).reduce((sum, d) => sum + (d.revenue ?? 0), 0);
  const gridColor    = isDark ? "rgba(255,255,255,0.05)" : "rgba(0,0,0,0.05)";
  const tickColor    = isDark ? "rgba(255,255,255,0.4)"  : "rgba(0,0,0,0.4)";
  const primaryHsl   = isDark ? "rgba(99,130,255,1)"     : "rgba(79,110,247,1)";
  const primaryFill  = isDark ? "rgba(99,130,255,0.08)"  : "rgba(79,110,247,0.06)";

  return (
    <div className="glass-card rounded-2xl p-5">
      {/* Header */}
      <div className="flex items-center justify-between mb-5">
        <div className="flex items-center gap-2">
          <div className="h-8 w-8 rounded-lg gradient-primary flex items-center justify-center">
            <TrendingUp className="h-4 w-4 text-white" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-foreground">{title ?? "রাজস্ব প্রবণতা"}</h3>
            <p className="text-xs text-muted-foreground">Revenue trend</p>
          </div>
        </div>
        <div className="text-right">
          <p className="text-lg font-bold text-foreground">
            ৳{totalRevenue.toLocaleString("en-BD")}
          </p>
          <p className="text-xs text-muted-foreground">মোট</p>
        </div>
      </div>

      <ResponsiveContainer width="100%" height={260}>
        <AreaChart data={data || []} margin={{ top: 5, right: 8, left: 0, bottom: 5 }}>
          <defs>
            <linearGradient id="revGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%"  stopColor={primaryHsl} stopOpacity={0.18} />
              <stop offset="95%" stopColor={primaryHsl} stopOpacity={0}    />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke={gridColor} vertical={false} />
          <XAxis
            dataKey="date"
            tick={{ fontSize: 11, fill: tickColor }}
            tickLine={false}
            axisLine={false}
            tickFormatter={(v: string) => {
              try { return new Date(v).toLocaleDateString("en-BD", { month: "short", day: "numeric" }); }
              catch { return v; }
            }}
            interval="preserveStartEnd"
          />
          <YAxis
            tick={{ fontSize: 11, fill: tickColor }}
            tickLine={false}
            axisLine={false}
            tickFormatter={(v: number) => `৳${v >= 1000 ? `${(v / 1000).toFixed(0)}k` : v}`}
            width={52}
          />
          <Tooltip content={<CustomTooltip />} cursor={{ stroke: primaryHsl, strokeWidth: 1, strokeDasharray: "4 2" }} />
          <Area
            type="monotone"
            dataKey="revenue"
            stroke={primaryHsl}
            strokeWidth={2.5}
            fill="url(#revGrad)"
            dot={false}
            activeDot={{ r: 4, strokeWidth: 0, fill: primaryHsl }}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
