import { LucideIcon, TrendingUp, TrendingDown } from "lucide-react";
import { cn } from "@/lib/utils";

type CardVariant = "blue" | "violet" | "emerald" | "amber" | "rose" | "default";

interface StatCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: LucideIcon;
  iconColor?: string;
  iconBg?: string;
  loading?: boolean;
  change?: number;
  variant?: CardVariant;
}

const variantConfig: Record<CardVariant, {
  card: string;
  icon: string;
  iconBg: string;
  valueColor: string;
}> = {
  blue: {
    card: "stat-card-blue",
    icon: "text-blue-600 dark:text-blue-400",
    iconBg: "bg-blue-500/10 dark:bg-blue-500/20",
    valueColor: "",
  },
  violet: {
    card: "stat-card-violet",
    icon: "text-violet-600 dark:text-violet-400",
    iconBg: "bg-violet-500/10 dark:bg-violet-500/20",
    valueColor: "",
  },
  emerald: {
    card: "stat-card-emerald",
    icon: "text-emerald-600 dark:text-emerald-400",
    iconBg: "bg-emerald-500/10 dark:bg-emerald-500/20",
    valueColor: "",
  },
  amber: {
    card: "stat-card-amber",
    icon: "text-amber-600 dark:text-amber-400",
    iconBg: "bg-amber-500/10 dark:bg-amber-500/20",
    valueColor: "",
  },
  rose: {
    card: "",
    icon: "text-rose-600 dark:text-rose-400",
    iconBg: "bg-rose-500/10 dark:bg-rose-500/20",
    valueColor: "",
  },
  default: {
    card: "",
    icon: "text-primary",
    iconBg: "bg-primary/10",
    valueColor: "",
  },
};

function SkeletonCard() {
  return (
    <div className="glass-card p-5">
      <div className="flex items-center justify-between mb-4">
        <div className="h-4 w-28 rounded-lg bg-muted animate-pulse" />
        <div className="h-10 w-10 rounded-xl bg-muted animate-pulse" />
      </div>
      <div className="h-8 w-32 rounded-lg bg-muted animate-pulse mb-2" />
      <div className="h-3 w-20 rounded-lg bg-muted animate-pulse" />
    </div>
  );
}

export default function StatCard({
  title,
  value,
  subtitle,
  icon: Icon,
  iconColor,
  iconBg,
  loading,
  change,
  variant = "default",
}: StatCardProps) {
  if (loading) return <SkeletonCard />;

  const cfg = variantConfig[variant];
  const resolvedIconColor = iconColor ?? cfg.icon;
  const resolvedIconBg    = iconBg    ?? cfg.iconBg;

  return (
    <div className={cn(
      "glass-card p-5 rounded-2xl border transition-all duration-300 hover:shadow-premium-hover group cursor-default",
      cfg.card,
    )}>
      {/* Top row: label + icon */}
      <div className="flex items-start justify-between mb-3">
        <p className="text-sm font-medium text-muted-foreground leading-snug pr-2">{title}</p>
        <div className={cn(
          "flex h-10 w-10 items-center justify-center rounded-xl shrink-0 transition-transform duration-200 group-hover:scale-110",
          resolvedIconBg,
        )}>
          <Icon className={cn("h-5 w-5", resolvedIconColor)} />
        </div>
      </div>

      {/* Value */}
      <div className="text-2xl font-bold text-foreground tracking-tight mb-1.5">
        {value}
      </div>

      {/* Bottom: subtitle + change */}
      {(subtitle || change !== undefined) && (
        <div className="flex items-center gap-2 flex-wrap">
          {change !== undefined && (
            <span className={cn(
              "inline-flex items-center gap-1 text-xs font-semibold rounded-md px-1.5 py-0.5",
              change >= 0
                ? "text-emerald-700 bg-emerald-100/80 dark:text-emerald-400 dark:bg-emerald-500/15"
                : "text-red-700 bg-red-100/80 dark:text-red-400 dark:bg-red-500/15"
            )}>
              {change >= 0
                ? <TrendingUp className="h-3 w-3" />
                : <TrendingDown className="h-3 w-3" />}
              {change >= 0 ? "+" : ""}{change.toFixed(1)}%
            </span>
          )}
          {subtitle && (
            <p className="text-xs text-muted-foreground/70">{subtitle}</p>
          )}
        </div>
      )}
    </div>
  );
}
