"use client";

import { useState } from "react";
import { Shield, Download, Database, CheckCircle2, AlertCircle, Loader2, Key, Users2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { useLang } from "@/contexts/LangContext";
import { useHealth } from "@/hooks/useHealth";
import { useBackupSummary, useDownloadBackup } from "@/hooks/useBackup";
import { useAuditSummary } from "@/hooks/useAuditLogs";
import { cn } from "@/lib/utils";
import { toast } from "sonner";

const ROLE_INFO: Record<string, { color: string; desc: string; descBn: string }> = {
  OWNER: { color: "bg-purple-100 text-purple-700 border-purple-200", desc: "Full access — all actions", descBn: "সম্পূর্ণ অ্যাক্সেস" },
  ADMIN: { color: "bg-blue-100 text-blue-700 border-blue-200",   desc: "Manage orders, products, customers", descBn: "অর্ডার ও পণ্য ব্যবস্থাপনা" },
  STAFF: { color: "bg-amber-100 text-amber-700 border-amber-200", desc: "Process orders and view reports", descBn: "অর্ডার প্রক্রিয়া ও রিপোর্ট দেখা" },
  VIEWER: { color: "bg-slate-100 text-slate-600 border-slate-200", desc: "Read-only access", descBn: "শুধু দেখার অ্যাক্সেস" },
};

function HealthBadge({ ok, label }: { ok: boolean; label: string }) {
  return (
    <div className="flex items-center gap-2 py-2 px-3 rounded-lg bg-slate-50 border border-slate-100">
      {ok
        ? <CheckCircle2 className="h-4 w-4 text-emerald-500 shrink-0" />
        : <AlertCircle className="h-4 w-4 text-red-500 shrink-0" />}
      <span className="text-sm text-slate-700">{label}</span>
      <span className={cn("ml-auto text-xs font-semibold px-2 py-0.5 rounded-full",
        ok ? "bg-emerald-50 text-emerald-700" : "bg-red-50 text-red-600")}>
        {ok ? "OK" : "Error"}
      </span>
    </div>
  );
}

export default function SecurityPage() {
  const { lang } = useLang();
  const l = (bn: string, en: string) => lang === "bn" ? bn : en;

  const { data: health, isLoading: healthLoading } = useHealth();
  const { data: backupSummary, isLoading: summaryLoading } = useBackupSummary();
  const { data: auditSummary } = useAuditSummary();
  const download = useDownloadBackup();

  const storedRole = typeof window !== "undefined"
    ? (() => { try { const t = localStorage.getItem("sellermate_token"); if (!t) return "OWNER"; const p = JSON.parse(atob(t.split(".")[1])); return p.role || "OWNER"; } catch { return "OWNER"; } })()
    : "OWNER";

  const role = storedRole;
  const roleInfo = ROLE_INFO[role] || ROLE_INFO.OWNER;

  const handleDownload = async () => {
    try {
      await download.mutateAsync();
      toast.success(l("ব্যাকআপ ডাউনলোড শুরু হয়েছে", "Backup download started"));
    } catch {
      toast.error(l("ব্যাকআপ ডাউনলোড ব্যর্থ হয়েছে", "Backup download failed"));
    }
  };

  return (
    <div className="p-6 max-w-3xl space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-slate-900">{l("নিরাপত্তা ও ব্যাকআপ", "Security & Backup")}</h1>
        <p className="text-sm text-slate-500 mt-1">
          {l("অ্যাকাউন্ট নিরাপত্তা, রোল ও ডেটা ব্যাকআপ পরিচালনা", "Manage account security, roles, and data backup")}
        </p>
      </div>

      {/* Role card */}
      <div className="bg-white border border-slate-200 rounded-xl p-6 space-y-4">
        <div className="flex items-center gap-2">
          <Users2 className="h-5 w-5 text-slate-400" />
          <h2 className="text-base font-semibold text-slate-800">{l("অ্যাকাউন্ট রোল", "Account Role")}</h2>
        </div>
        <div className={cn("flex items-center gap-3 p-4 rounded-lg border", roleInfo.color)}>
          <Key className="h-5 w-5 shrink-0" />
          <div>
            <p className="font-semibold">{role}</p>
            <p className="text-xs mt-0.5">{lang === "bn" ? roleInfo.descBn : roleInfo.desc}</p>
          </div>
        </div>
        <div className="grid grid-cols-2 gap-2 text-xs">
          {Object.entries(ROLE_INFO).map(([r, info]) => (
            <div key={r} className={cn("flex items-center gap-2 px-3 py-2 rounded-lg border",
              r === role ? info.color : "bg-slate-50 border-slate-100 text-slate-400")}>
              <span className="font-semibold w-14 shrink-0">{r}</span>
              <span>{lang === "bn" ? info.descBn : info.desc}</span>
            </div>
          ))}
        </div>
      </div>

      {/* System health */}
      <div className="bg-white border border-slate-200 rounded-xl p-6 space-y-4">
        <div className="flex items-center gap-2">
          <Shield className="h-5 w-5 text-slate-400" />
          <h2 className="text-base font-semibold text-slate-800">{l("সিস্টেম স্বাস্থ্য", "System Health")}</h2>
          {health && (
            <span className={cn("ml-auto text-xs font-semibold px-2.5 py-1 rounded-full border",
              health.status === "ok" ? "bg-emerald-50 text-emerald-700 border-emerald-200" : "bg-amber-50 text-amber-700 border-amber-200")}>
              {health.status === "ok" ? "● All Systems Operational" : "● Degraded"}
            </span>
          )}
        </div>
        {healthLoading ? (
          <div className="space-y-2">{Array.from({ length: 2 }).map((_, i) => <Skeleton key={i} className="h-10" />)}</div>
        ) : health ? (
          <div className="space-y-2">
            <HealthBadge ok={health.components.api.status === "ok"} label={l("এপিআই সার্ভার", "API Server")} />
            <HealthBadge ok={health.components.database.status === "ok"} label={l("ডেটাবেস সংযোগ", "Database Connection")} />
            <p className="text-xs text-slate-400">v{health.version}</p>
          </div>
        ) : (
          <p className="text-sm text-slate-400">{l("স্বাস্থ্য তথ্য পাওয়া যায়নি", "Health info unavailable")}</p>
        )}
      </div>

      {/* Activity summary */}
      {auditSummary && Object.keys(auditSummary).length > 0 && (
        <div className="bg-white border border-slate-200 rounded-xl p-6 space-y-4">
          <h2 className="text-base font-semibold text-slate-800">{l("কার্যকলাপ সারাংশ", "Activity Summary")}</h2>
          <div className="grid grid-cols-3 gap-2">
            {Object.entries(auditSummary).map(([action, count]) => (
              <div key={action} className="text-center p-3 bg-slate-50 rounded-lg border border-slate-100">
                <p className="text-lg font-bold text-slate-800">{count}</p>
                <p className="text-[11px] text-slate-500 capitalize mt-0.5">{action.replace("_", " ")}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Backup & Export */}
      <div className="bg-white border border-slate-200 rounded-xl p-6 space-y-4">
        <div className="flex items-center gap-2">
          <Database className="h-5 w-5 text-slate-400" />
          <h2 className="text-base font-semibold text-slate-800">{l("ডেটা ব্যাকআপ", "Data Backup")}</h2>
        </div>

        {summaryLoading ? (
          <Skeleton className="h-20" />
        ) : backupSummary ? (
          <div className="grid grid-cols-4 gap-3">
            {Object.entries(backupSummary.counts).map(([key, count]) => (
              <div key={key} className="text-center p-3 bg-slate-50 rounded-lg border border-slate-100">
                <p className="text-xl font-bold text-slate-800">{count}</p>
                <p className="text-[11px] text-slate-500 capitalize mt-0.5">{key}</p>
              </div>
            ))}
          </div>
        ) : null}

        <div className="rounded-lg bg-blue-50 border border-blue-200 p-3 text-xs text-blue-800 space-y-1">
          <p className="font-semibold">{l("ব্যাকআপে অন্তর্ভুক্ত:", "Export includes:")}</p>
          <p>{l("পণ্য, গ্রাহক, অর্ডার, ক্যাম্পেইন · JSON ফরম্যাট", "Products, customers, orders, campaigns · JSON format")}</p>
        </div>

        <Button onClick={handleDownload} disabled={download.isPending} className="gap-2">
          {download.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Download className="h-4 w-4" />}
          {l("ব্যাকআপ ডাউনলোড করুন", "Download Backup")}
        </Button>
      </div>
    </div>
  );
}
