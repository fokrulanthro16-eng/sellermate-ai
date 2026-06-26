"use client";

import { useState } from "react";
import Link from "next/link";
import {
  TrendingUp, Package, Megaphone, BarChart3, LifeBuoy,
  Play, Loader2, CheckCircle2, XCircle, ArrowRight, Zap,
  RefreshCw, ChevronDown, ChevronUp,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { useAgentList, useRunAgent, type AgentResult, type AgentInfo } from "@/hooks/useAgents";
import { useLang } from "@/contexts/LangContext";
import { cn } from "@/lib/utils";

const ICONS: Record<string, React.ElementType> = {
  TrendingUp, Package, Megaphone, BarChart3, LifeBuoy,
};

const COLOR_MAP: Record<string, string> = {
  indigo:  "border-indigo-500/30 bg-indigo-500/10",
  amber:   "border-amber-500/30 bg-amber-500/10",
  emerald: "border-emerald-500/30 bg-emerald-500/10",
  blue:    "border-blue-500/30 bg-blue-500/10",
  violet:  "border-violet-500/30 bg-violet-500/10",
};
const ICON_COLOR: Record<string, string> = {
  indigo:  "text-indigo-400",
  amber:   "text-amber-400",
  emerald: "text-emerald-400",
  blue:    "text-blue-400",
  violet:  "text-violet-400",
};

// ── Insight card ─────────────────────────────────────────────────────────────

function InsightCard({ ins }: { ins: AgentResult["insights"][number] }) {
  return (
    <div className={cn(
      "rounded-lg p-3 border",
      ins.positive ? "border-emerald-500/20 bg-emerald-500/5" : "border-red-500/20 bg-red-500/5"
    )}>
      <div className="flex items-start justify-between gap-2 mb-1">
        <span className="text-xs text-white/50 font-medium">{ins.title}</span>
        {ins.change && (
          <span className={cn("text-[10px] font-bold px-1.5 py-0.5 rounded-full",
            ins.positive ? "bg-emerald-500/20 text-emerald-300" : "bg-red-500/20 text-red-300"
          )}>
            {ins.change}
          </span>
        )}
      </div>
      <p className="text-lg font-bold text-white">{ins.value}</p>
      <p className="text-[11px] text-white/40 mt-0.5">{ins.detail}</p>
    </div>
  );
}

// ── Agent card ────────────────────────────────────────────────────────────────

function AgentCard({ agent }: { agent: AgentInfo }) {
  const { lang } = useLang();
  const run = useRunAgent();
  const [result, setResult] = useState<AgentResult | null>(null);
  const [expanded, setExpanded] = useState(false);

  const Icon = ICONS[agent.icon] ?? Zap;
  const borderCls = COLOR_MAP[agent.color] ?? COLOR_MAP.indigo;
  const iconCls   = ICON_COLOR[agent.color] ?? ICON_COLOR.indigo;

  const handleRun = async () => {
    const res = await run.mutateAsync(agent.id);
    setResult(res);
    setExpanded(true);
  };

  return (
    <div className={cn("glass-card rounded-xl border overflow-hidden", borderCls)}>
      {/* Header */}
      <div className="p-4">
        <div className="flex items-start gap-3">
          <div className={cn("h-9 w-9 rounded-lg flex items-center justify-center shrink-0", borderCls)}>
            <Icon className={cn("h-5 w-5", iconCls)} />
          </div>
          <div className="flex-1 min-w-0">
            <h3 className="text-sm font-semibold text-white leading-tight">
              {lang === "bn" ? agent.name_bn : agent.name}
            </h3>
            <p className="text-[11px] text-white/50 mt-0.5 leading-snug">
              {lang === "bn" ? agent.description_bn : agent.description}
            </p>
          </div>
          <Button
            size="sm"
            onClick={handleRun}
            disabled={run.isPending}
            className="h-8 gap-1.5 shrink-0 text-xs"
          >
            {run.isPending ? <Loader2 className="h-3 w-3 animate-spin" /> : <Play className="h-3 w-3" />}
            {lang === "bn" ? "চালান" : "Run"}
          </Button>
        </div>
      </div>

      {/* Results */}
      {result && (
        <>
          <div
            className="flex items-center justify-between px-4 py-2 border-t border-white/5 cursor-pointer hover:bg-white/5 transition-colors"
            onClick={() => setExpanded((v) => !v)}
          >
            <span className="text-[11px] text-white/50 font-medium">{result.title}</span>
            <div className="flex items-center gap-2">
              <span className="text-[10px] text-white/30">
                {new Date(result.generated_at).toLocaleTimeString()}
              </span>
              {expanded
                ? <ChevronUp className="h-3.5 w-3.5 text-white/30" />
                : <ChevronDown className="h-3.5 w-3.5 text-white/30" />}
            </div>
          </div>

          {expanded && (
            <div className="px-4 pb-4 space-y-4 border-t border-white/5">
              {/* Insights grid */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 pt-3">
                {result.insights.map((ins, i) => <InsightCard key={i} ins={ins} />)}
              </div>

              {/* Checklist (support agent only) */}
              {result.checklist && (
                <div className="space-y-1.5">
                  <p className="text-[10px] font-semibold uppercase tracking-wide text-white/30">
                    Setup Checklist
                  </p>
                  {result.checklist.map((item, i) => (
                    <Link key={i} href={item.href}
                      className="flex items-center gap-2 py-1.5 px-2.5 rounded-lg hover:bg-white/5 transition-colors group"
                    >
                      {item.done
                        ? <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400 shrink-0" />
                        : <XCircle className="h-3.5 w-3.5 text-white/25 shrink-0" />}
                      <span className={cn("text-xs", item.done ? "text-white/60 line-through" : "text-white/80")}>
                        {item.label}
                      </span>
                      <ArrowRight className="h-3 w-3 text-white/20 ml-auto opacity-0 group-hover:opacity-100 transition-opacity" />
                    </Link>
                  ))}
                </div>
              )}

              {/* Actions */}
              {result.actions.length > 0 && (
                <div className="space-y-1.5">
                  <p className="text-[10px] font-semibold uppercase tracking-wide text-white/30">
                    Recommended Actions
                  </p>
                  <div className="flex flex-wrap gap-2">
                    {result.actions.map((action, i) => (
                      <Link key={i} href={action.href}>
                        <Button
                          variant="outline"
                          size="sm"
                          className={cn(
                            "h-7 text-xs gap-1.5",
                            action.priority === "high" && "border-red-500/40 text-red-300 hover:bg-red-500/10",
                            action.priority === "medium" && "border-amber-500/40 text-amber-300 hover:bg-amber-500/10",
                          )}
                        >
                          <ArrowRight className="h-3 w-3" />
                          {action.label}
                        </Button>
                      </Link>
                    ))}
                  </div>
                </div>
              )}

              {/* Re-run */}
              <button
                onClick={handleRun}
                disabled={run.isPending}
                className="flex items-center gap-1.5 text-[11px] text-white/30 hover:text-white/60 transition-colors"
              >
                <RefreshCw className="h-3 w-3" />
                {lang === "bn" ? "আবার চালান" : "Re-run analysis"}
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}

// ── Page ──────────────────────────────────────────────────────────────────────

export default function AgentsPage() {
  const { lang } = useLang();
  const { data: agents, isLoading } = useAgentList();

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <div className="flex items-center gap-2 text-xs text-white/40 mb-1">
          <span>{lang === "bn" ? "এআই" : "AI"}</span>
          <span>/</span>
          <span className="text-white/60">{lang === "bn" ? "এজেন্ট সিস্টেম" : "Agent System"}</span>
        </div>
        <h1 className="text-xl font-bold gradient-text">
          {lang === "bn" ? "এআই এজেন্ট সিস্টেম" : "AI Agent System"}
        </h1>
        <p className="text-sm text-white/40 mt-0.5">
          {lang === "bn"
            ? "প্রতিটি এজেন্ট আপনার ব্যবসার ডেটা বিশ্লেষণ করে কার্যকর পরামর্শ দেয়"
            : "Each agent reads your live business data and generates actionable insights"}
        </p>
      </div>

      {/* Beta badge */}
      <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-violet-500/10 border border-violet-500/20">
        <Zap className="h-3 w-3 text-violet-400" />
        <span className="text-xs font-medium text-violet-300">
          {lang === "bn" ? "বেটা মোড — কোনো AI কী প্রয়োজন নেই" : "Beta Mode — No AI key required"}
        </span>
      </div>

      {/* Agent grid */}
      {isLoading ? (
        <div className="grid grid-cols-1 gap-4">
          {Array.from({ length: 5 }).map((_, i) => (
            <Skeleton key={i} className="h-32 rounded-xl" />
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4">
          {(agents ?? []).map((agent) => (
            <AgentCard key={agent.id} agent={agent} />
          ))}
        </div>
      )}
    </div>
  );
}
