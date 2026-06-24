"use client";

import {
  Loader2, ShieldAlert, Network, Play,
  CheckCircle2, AlertTriangle, Zap, TrendingUp, TrendingDown,
  BarChart3, Package, Minus, CreditCard, ArrowRight,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import {
  useTrustScore, useFraudReport, useRunAgents,
  useGrowthCoach, useMarginGuardian, useDemandOracle, useCreditReadiness,
} from "@/hooks/useStrategic";
import { cn } from "@/lib/utils";
import { useLang } from "@/contexts/LangContext";
import type { TrustScoreOut, FraudReportOut } from "@/types";

/* ── Flag label map ─────────────────────────────────────── */
function flagLabel(flag: string, lang: string) {
  const map: Record<string, { bn: string; en: string }> = {
    ELEVATED_CANCELLATION_RATE: { bn: "বাতিলের হার বেশি",           en: "High cancellation rate"    },
    HIGH_FRAUD_RISK:            { bn: "উচ্চ ফ্রড ঝুঁকি",            en: "High fraud risk"           },
    LOW_PAYMENT_RATE:           { bn: "পেমেন্টের হার কম",            en: "Low payment rate"          },
    STALE_UNPAID_ORDERS:        { bn: "মেয়াদোত্তীর্ণ বকেয়া",       en: "Stale unpaid orders"       },
    SUSPICIOUS_CUSTOMERS:       { bn: "সন্দেহজনক গ্রাহক",            en: "Suspicious customers"      },
    HIGH_COD_EXPOSURE:          { bn: "উচ্চ COD ঋণ",                 en: "High COD exposure"         },
    ELEVATED_COD_RATIO:         { bn: "COD অনুপাত বেশি",             en: "Elevated COD ratio"        },
    HIGH_RETURN_RATE:           { bn: "ফেরতের হার বেশি",              en: "High return rate"          },
    HEAVY_DISCOUNTING:          { bn: "অতিরিক্ত ছাড়",               en: "Heavy discounting"         },
    HIGH_UNPAID_EXPOSURE:       { bn: "উচ্চ বকেয়া",                  en: "High unpaid exposure"      },
  };
  const entry = map[flag];
  if (entry) return lang === "bn" ? entry.bn : entry.en;
  return flag.replace(/_/g, " ");
}

/* ── Score bar ──────────────────────────────────────────── */
function ScoreBar({ score, color = "bg-blue-500" }: { score: number; color?: string }) {
  const s = Math.min(100, Math.max(0, Math.round(score)));
  const textColor = color.replace("bg-", "text-");
  return (
    <div className="flex items-center gap-3">
      <div className="flex-1 h-2 rounded-full bg-muted overflow-hidden">
        <div className={cn("h-full rounded-full transition-all duration-700", color)} style={{ width: `${s}%` }} />
      </div>
      <span className={cn("text-lg font-bold tabular-nums w-10 text-right", textColor)}>{s}</span>
    </div>
  );
}

/* ── Agent card ─────────────────────────────────────────── */
interface AgentCardProps {
  title: string;
  subtitle: string;
  icon: React.ElementType;
  score: number;
  scoreColor?: string;
  loading: boolean;
  empty: boolean;
  onRun: () => void;
  running: boolean;
  children?: React.ReactNode;
  accent?: string;
}
function AgentCard({ title, subtitle, icon: Icon, score, scoreColor = "bg-blue-500", loading, empty, onRun, running, children, accent = "border-l-blue-500" }: AgentCardProps) {
  return (
    <div className={cn("admin-card p-5 border-l-4", accent)}>
      {/* Card header */}
      <div className="flex items-start justify-between gap-3 mb-4">
        <div className="flex items-center gap-2.5">
          <div className="h-8 w-8 rounded bg-muted flex items-center justify-center shrink-0">
            <Icon className="h-4 w-4 text-foreground" />
          </div>
          <div>
            <p className="text-sm font-semibold">{title}</p>
            <p className="text-xs text-muted-foreground">{subtitle}</p>
          </div>
        </div>
      </div>

      {loading ? (
        <div className="space-y-2">
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-3/4" />
          <Skeleton className="h-4 w-1/2" />
        </div>
      ) : empty ? (
        <div className="text-center py-6 space-y-3">
          <Icon className="h-8 w-8 mx-auto text-muted-foreground/25" />
          <p className="text-xs text-muted-foreground">
            {/* "Run agents to generate analysis" */}
            Run agents to generate analysis
          </p>
          <Button size="sm" variant="outline" onClick={onRun} disabled={running} className="gap-1.5 text-xs h-7">
            {running ? <Loader2 className="h-3 w-3 animate-spin" /> : <Play className="h-3 w-3" />}
            Run Now
          </Button>
        </div>
      ) : (
        <>
          {/* Score */}
          <div className="mb-4">
            <ScoreBar score={score} color={scoreColor} />
          </div>
          {/* Content */}
          {children}
        </>
      )}
    </div>
  );
}

/* ── Flags list ─────────────────────────────────────────── */
function FlagList({ flags, lang }: { flags: string[]; lang: string }) {
  if (flags.length === 0) {
    return (
      <div className="flex items-center gap-2 text-xs text-green-700 dark:text-green-400 bg-green-50 dark:bg-green-950/30 rounded p-2 border border-green-200 dark:border-green-900">
        <CheckCircle2 className="h-3.5 w-3.5 shrink-0" />
        {lang === "bn" ? "কোনো ঝুঁকি নেই" : "No risks detected"}
      </div>
    );
  }
  return (
    <div className="space-y-1.5">
      {flags.slice(0, 4).map((flag, i) => (
        <div key={i} className="flex items-center gap-2 text-xs bg-amber-50 dark:bg-amber-950/20 border border-amber-200 dark:border-amber-800 rounded p-1.5">
          <AlertTriangle className="h-3 w-3 text-amber-600 shrink-0" />
          <span className="font-medium text-amber-800 dark:text-amber-300">{flagLabel(flag, lang)}</span>
        </div>
      ))}
    </div>
  );
}

/* ── Recommendations ────────────────────────────────────── */
function RecList({ items, lang, color = "blue" }: { items: string[]; lang: string; color?: string }) {
  if (items.length === 0) return null;
  const borderColor = `border-${color}-200 dark:border-${color}-800`;
  const bgColor = `bg-${color}-50 dark:bg-${color}-950/20`;
  const textColor = `text-${color}-800 dark:text-${color}-300`;
  return (
    <div className="space-y-1.5">
      {items.slice(0, 3).map((item, i) => (
        <div key={i} className={cn("flex items-start gap-2 text-xs rounded p-1.5 border", bgColor, borderColor)}>
          <ArrowRight className={cn("h-3 w-3 mt-0.5 shrink-0", `text-${color}-600`)} />
          <span className={cn("font-medium", textColor)}>{item.replace(/_/g, " ")}</span>
        </div>
      ))}
    </div>
  );
}

/* ── Main Page ──────────────────────────────────────────── */
export default function AICenterPage() {
  const { lang } = useLang();
  const label = (bn: string, en: string) => lang === "bn" ? bn : en;

  const { data: trustInsight,  isLoading: trustLoading  } = useTrustScore();
  const { data: fraudInsight,  isLoading: fraudLoading  } = useFraudReport();
  const { data: growthInsight, isLoading: growthLoading } = useGrowthCoach();
  const { data: marginInsight, isLoading: marginLoading } = useMarginGuardian();
  const { data: demandInsight, isLoading: demandLoading } = useDemandOracle();
  const { data: creditInsight, isLoading: creditLoading } = useCreditReadiness();
  const runAgents = useRunAgents();

  const trust  = trustInsight?.payload  as unknown as TrustScoreOut  | undefined;
  const fraud  = fraudInsight?.payload  as unknown as FraudReportOut | undefined;
  const growth = growthInsight?.payload as Record<string, unknown>   | undefined;
  const margin = marginInsight?.payload as Record<string, unknown>   | undefined;
  const demand = demandInsight?.payload as Record<string, unknown>   | undefined;
  const credit = creditInsight?.payload as Record<string, unknown>   | undefined;

  const scores = {
    trust:  Math.round(trustInsight?.score  ?? 0),
    fraud:  Math.round(fraud?.fraud_risk_score ?? 0),
    growth: Math.round(growthInsight?.score ?? 0),
    margin: Math.round(marginInsight?.score ?? 0),
    demand: Math.round(demandInsight?.score ?? 0),
    credit: Math.round(creditInsight?.score ?? 0),
  };

  const trendIcon = (dir: string) => {
    if (dir === "GROWING") return <TrendingUp className="h-3.5 w-3.5 text-green-600" />;
    if (dir === "DECLINING") return <TrendingDown className="h-3.5 w-3.5 text-red-600" />;
    return <Minus className="h-3.5 w-3.5 text-amber-500" />;
  };

  return (
    <div className="space-y-4 max-w-[1400px]">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold">{label("কৌশলগত AI সেন্টার", "Strategic AI Center")}</h1>
          <p className="text-sm text-muted-foreground">
            {label("৬টি বিশেষজ্ঞ এজেন্ট · রিয়েল-টাইম ব্যবসায়িক বিশ্লেষণ", "6 expert agents · Real-time business intelligence")}
          </p>
        </div>
        <Button
          onClick={() => runAgents.mutate()}
          disabled={runAgents.isPending}
          size="sm"
          className="gap-2 gradient-primary text-white hover:opacity-90"
        >
          {runAgents.isPending ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Zap className="h-3.5 w-3.5" />}
          {label("এজেন্ট চালান", "Run All Agents")}
        </Button>
      </div>

      {/* Score Overview Row */}
      <div className="grid grid-cols-3 sm:grid-cols-6 gap-2">
        {[
          { label: label("ট্রাস্ট", "Trust"),    score: scores.trust,  color: "text-emerald-700 dark:text-emerald-400", bar: "bg-emerald-500", border: "border-l-emerald-500" },
          { label: label("ফ্রড", "Fraud"),       score: scores.fraud,  color: "text-red-700 dark:text-red-400",         bar: "bg-red-500",     border: "border-l-red-500" },
          { label: label("প্রবৃদ্ধি", "Growth"), score: scores.growth, color: "text-blue-700 dark:text-blue-400",       bar: "bg-blue-500",    border: "border-l-blue-500" },
          { label: label("মার্জিন", "Margin"),   score: scores.margin, color: "text-violet-700 dark:text-violet-400",   bar: "bg-violet-500",  border: "border-l-violet-500" },
          { label: label("রিস্টক", "Restock"),   score: scores.demand, color: "text-amber-700 dark:text-amber-400",     bar: "bg-amber-500",   border: "border-l-amber-500" },
          { label: label("ক্রেডিট", "Credit"),   score: scores.credit, color: "text-indigo-700 dark:text-indigo-400",   bar: "bg-indigo-500",  border: "border-l-indigo-500" },
        ].map((item) => (
          <div key={item.label} className={cn("admin-card p-3 border-l-4", item.border)}>
            <p className="text-[11px] text-muted-foreground mb-1">{item.label}</p>
            <p className={cn("text-2xl font-bold tabular-nums", item.color)}>{item.score}<span className="text-xs text-muted-foreground font-normal">/100</span></p>
            <div className="mt-1.5 h-1 rounded-full bg-muted overflow-hidden">
              <div className={cn("h-full rounded-full", item.bar)} style={{ width: `${item.score}%` }} />
            </div>
          </div>
        ))}
      </div>

      {/* Agent Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">

        {/* Trust Score */}
        <AgentCard
          title={label("ট্রাস্ট স্কোর", "Trust Score")}
          subtitle={label("ব্যবসার বিশ্বাসযোগ্যতা", "Business credibility")}
          icon={Network}
          score={scores.trust}
          scoreColor="bg-emerald-500"
          loading={trustLoading}
          empty={!trustInsight}
          onRun={() => runAgents.mutate()}
          running={runAgents.isPending}
          accent="border-l-emerald-500"
        >
          <FlagList flags={trust?.risk_flags ?? []} lang={lang} />
          {trust?.confidence && (
            <p className="text-xs text-muted-foreground mt-3">
              {label("নির্ভরযোগ্যতা:", "Confidence:")} <span className="font-semibold">{trust.confidence}</span>
            </p>
          )}
        </AgentCard>

        {/* Fraud Risk */}
        <AgentCard
          title={label("ফ্রড ঝুঁকি", "Fraud Risk")}
          subtitle={label("প্রতারণার সম্ভাবনা", "Fraud probability")}
          icon={ShieldAlert}
          score={scores.fraud}
          scoreColor={scores.fraud <= 20 ? "bg-emerald-500" : scores.fraud <= 50 ? "bg-amber-500" : "bg-red-500"}
          loading={fraudLoading}
          empty={!fraudInsight}
          onRun={() => runAgents.mutate()}
          running={runAgents.isPending}
          accent="border-l-orange-500"
        >
          {fraud?.alert_reasons && fraud.alert_reasons.length > 0 ? (
            <div className="space-y-1.5">
              {fraud.alert_reasons.slice(0, 3).map((reason, i) => {
                const [title, ...rest] = reason.split(":");
                return (
                  <div key={i} className="flex items-start gap-2 text-xs bg-red-50 dark:bg-red-950/20 border border-red-200 dark:border-red-800 rounded p-1.5">
                    <ShieldAlert className="h-3 w-3 text-red-500 shrink-0 mt-0.5" />
                    <div>
                      <p className="font-semibold text-red-800 dark:text-red-300">{flagLabel(title.trim(), lang)}</p>
                      {rest.length > 0 && <p className="text-red-600/70 dark:text-red-400/60">{rest.join(":").trim()}</p>}
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="flex items-center gap-2 text-xs text-green-700 dark:text-green-400 bg-green-50 dark:bg-green-950/30 rounded p-2 border border-green-200 dark:border-green-900">
              <CheckCircle2 className="h-3.5 w-3.5 shrink-0" />
              {label("কোনো সতর্কতা নেই", "No fraud alerts")}
            </div>
          )}
        </AgentCard>

        {/* Growth Coach */}
        <AgentCard
          title={label("প্রবৃদ্ধি কোচ", "Growth Coach")}
          subtitle={label("রাজস্ব প্রবণতা ও গতিশীলতা", "Revenue trend & momentum")}
          icon={TrendingUp}
          score={scores.growth}
          scoreColor="bg-blue-500"
          loading={growthLoading}
          empty={!growthInsight}
          onRun={() => runAgents.mutate()}
          running={runAgents.isPending}
          accent="border-l-blue-500"
        >
          {!!growth?.trend_direction && (
            <div className="flex items-center gap-2 mb-3">
              {trendIcon(String(growth.trend_direction))}
              <span className="text-xs font-semibold">
                {String(growth.trend_direction) === "GROWING" ? label("বৃদ্ধি পাচ্ছে", "Growing") :
                 String(growth.trend_direction) === "DECLINING" ? label("হ্রাস পাচ্ছে", "Declining") :
                 label("স্থিতিশীল", "Stable")}
              </span>
              {growth.revenue_growth_pct !== undefined && (
                <span className={cn("text-xs font-bold ml-auto tabular-nums",
                  Number(growth.revenue_growth_pct) >= 0 ? "text-green-600" : "text-red-500"
                )}>
                  {Number(growth.revenue_growth_pct) >= 0 ? "+" : ""}{Number(growth.revenue_growth_pct).toFixed(1)}%
                </span>
              )}
            </div>
          )}
          {!!growth?.explanation_en && (
            <p className="text-xs text-muted-foreground mb-3 line-clamp-2">
              {lang === "bn" ? String(growth.explanation_bn ?? "") : String(growth.explanation_en ?? "")}
            </p>
          )}
          {Array.isArray(growth?.recommendations) && (
            <RecList items={growth.recommendations as string[]} lang={lang} color="blue" />
          )}
        </AgentCard>

        {/* Margin Guardian */}
        <AgentCard
          title={label("মার্জিন গার্ডিয়ান", "Margin Guardian")}
          subtitle={label("আর্থিক স্বাস্থ্য সূচক", "Financial health index")}
          icon={BarChart3}
          score={scores.margin}
          scoreColor="bg-violet-500"
          loading={marginLoading}
          empty={!marginInsight}
          onRun={() => runAgents.mutate()}
          running={runAgents.isPending}
          accent="border-l-violet-500"
        >
          {!!margin?.risk_level && (
            <div className="mb-3">
              <Badge variant={
                margin.risk_level === "LOW" ? "success" :
                margin.risk_level === "MEDIUM" ? "warning" : "destructive"
              } className="text-xs">
                {margin.risk_level === "LOW" ? label("কম ঝুঁকি", "Low Risk") :
                 margin.risk_level === "MEDIUM" ? label("মধ্যম ঝুঁকি", "Medium Risk") :
                 label("উচ্চ ঝুঁকি", "High Risk")}
              </Badge>
            </div>
          )}
          {!!margin?.explanation_en && (
            <p className="text-xs text-muted-foreground mb-3 line-clamp-2">
              {lang === "bn" ? String(margin.explanation_bn ?? "") : String(margin.explanation_en ?? "")}
            </p>
          )}
          <div className="space-y-1.5 text-xs">
            {margin?.cod_ratio !== undefined && (
              <div className="flex justify-between">
                <span className="text-muted-foreground">COD {label("অনুপাত", "ratio")}</span>
                <span className="font-semibold">{(Number(margin.cod_ratio) * 100).toFixed(1)}%</span>
              </div>
            )}
            {margin?.refund_rate !== undefined && (
              <div className="flex justify-between">
                <span className="text-muted-foreground">{label("ফেরত হার", "Refund rate")}</span>
                <span className="font-semibold">{(Number(margin.refund_rate) * 100).toFixed(1)}%</span>
              </div>
            )}
          </div>
          {Array.isArray(margin?.flags) && (margin.flags as string[]).length > 0 && (
            <div className="mt-3">
              <FlagList flags={margin.flags as string[]} lang={lang} />
            </div>
          )}
        </AgentCard>

        {/* Demand Oracle */}
        <AgentCard
          title={label("ডিমান্ড ওরাকল", "Demand Oracle")}
          subtitle={label("স্টক জরুরিতা বিশ্লেষণ", "Stock urgency analysis")}
          icon={Package}
          score={scores.demand}
          scoreColor="bg-amber-500"
          loading={demandLoading}
          empty={!demandInsight}
          onRun={() => runAgents.mutate()}
          running={runAgents.isPending}
          accent="border-l-amber-500"
        >
          <div className="grid grid-cols-2 gap-2 mb-3">
            <div className="text-center p-2 rounded bg-red-50 dark:bg-red-950/20 border border-red-200 dark:border-red-800">
              <p className="text-xl font-bold text-red-600">{Number(demand?.critical_count ?? 0)}</p>
              <p className="text-[11px] text-muted-foreground mt-0.5">{label("জরুরি", "Critical")}</p>
            </div>
            <div className="text-center p-2 rounded bg-amber-50 dark:bg-amber-950/20 border border-amber-200 dark:border-amber-800">
              <p className="text-xl font-bold text-amber-600">{Number(demand?.high_count ?? 0)}</p>
              <p className="text-[11px] text-muted-foreground mt-0.5">{label("উচ্চ", "High")}</p>
            </div>
          </div>
          {!!demand?.explanation_en && (
            <p className="text-xs text-muted-foreground mb-3 line-clamp-2">
              {lang === "bn" ? String(demand.explanation_bn ?? "") : String(demand.explanation_en ?? "")}
            </p>
          )}
          {Array.isArray(demand?.critical_items) && (demand.critical_items as unknown[]).length > 0 && (
            <div className="space-y-1">
              {(demand.critical_items as Record<string, unknown>[]).slice(0, 3).map((item, i) => (
                <div key={i} className="flex items-center justify-between text-xs bg-red-50 dark:bg-red-950/10 border border-red-200 dark:border-red-900 rounded p-1.5">
                  <span className="font-medium truncate">{String(item.product_name ?? "")}</span>
                  <span className="font-bold text-red-600 ml-2 shrink-0">{label("স্টক:", "Stock:")} {Number(item.current_stock ?? 0)}</span>
                </div>
              ))}
            </div>
          )}
        </AgentCard>

        {/* Credit Readiness */}
        <AgentCard
          title={label("ক্রেডিট রেডিনেস", "Credit Readiness")}
          subtitle={label("ঋণ যোগ্যতার সূচক", "Financing eligibility")}
          icon={CreditCard}
          score={scores.credit}
          scoreColor="bg-indigo-500"
          loading={creditLoading}
          empty={!creditInsight}
          onRun={() => runAgents.mutate()}
          running={runAgents.isPending}
          accent="border-l-indigo-500"
        >
          {!!credit?.eligibility && (
            <div className="mb-3">
              <Badge variant={
                credit.eligibility === "ELIGIBLE" ? "success" :
                credit.eligibility === "BORDERLINE" ? "warning" : "destructive"
              } className="text-xs">
                {credit.eligibility === "ELIGIBLE" ? label("✓ যোগ্য", "✓ Eligible") :
                 credit.eligibility === "BORDERLINE" ? label("~ সীমান্তরেখা", "~ Borderline") :
                 label("✗ যোগ্য নয়", "✗ Not Eligible")}
              </Badge>
            </div>
          )}
          {credit?.credit_limit_estimate !== undefined && Number(credit.credit_limit_estimate) > 0 && (
            <div className="mb-3 p-2.5 rounded bg-indigo-50 dark:bg-indigo-950/20 border border-indigo-200 dark:border-indigo-800">
              <p className="text-[11px] text-muted-foreground">{label("আনুমানিক সীমা", "Est. credit limit")}</p>
              <p className="text-lg font-bold text-indigo-700 dark:text-indigo-400 tabular-nums">
                ৳{Number(credit.credit_limit_estimate).toLocaleString()}
              </p>
            </div>
          )}
          {!!credit?.explanation_en && (
            <p className="text-xs text-muted-foreground mb-3 line-clamp-2">
              {lang === "bn" ? String(credit.explanation_bn ?? "") : String(credit.explanation_en ?? "")}
            </p>
          )}
          {Array.isArray(credit?.improvement_tips) && (credit.improvement_tips as string[]).length > 0 && (
            <RecList items={credit.improvement_tips as string[]} lang={lang} color="indigo" />
          )}
        </AgentCard>

      </div>
    </div>
  );
}
