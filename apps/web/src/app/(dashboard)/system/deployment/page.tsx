"use client";

import {
  Server, Database, Cpu, Clock, Key, Package,
  Users, ShoppingCart, Megaphone, CheckCircle2, XCircle,
  RefreshCw, Terminal, Loader2, Rocket,
} from "lucide-react";
import { useHealth } from "@/hooks/useHealth";
import {
  useSystemInfo, useSystemMetrics, useDataCounts,
} from "@/hooks/useSystem";
import { useIntegrationsStatus } from "@/hooks/useIntegrations";
import { useQueryClient } from "@tanstack/react-query";

// ── helpers ──────────────────────────────────────────────────────────────────

function formatUptime(seconds: number): string {
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = seconds % 60;
  if (h > 0) return `${h}h ${m}m`;
  if (m > 0) return `${m}m ${s}s`;
  return `${s}s`;
}

function StatusDot({ ok }: { ok: boolean | undefined }) {
  if (ok === undefined) return <span className="h-2 w-2 rounded-full bg-slate-500 inline-block" />;
  return ok
    ? <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse inline-block" />
    : <span className="h-2 w-2 rounded-full bg-red-400 inline-block" />;
}

function StatusBadge({ ok, label }: { ok: boolean | undefined; label: string }) {
  const cls = ok === undefined
    ? "bg-slate-500/20 text-slate-300"
    : ok ? "bg-emerald-500/20 text-emerald-300" : "bg-red-500/20 text-red-300";
  const Icon = ok === undefined ? Loader2 : ok ? CheckCircle2 : XCircle;
  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${cls}`}>
      <Icon className={`h-3 w-3 ${ok === undefined ? "animate-spin" : ""}`} />
      {label}
    </span>
  );
}

function InfoRow({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="flex items-center justify-between py-2 border-b border-white/5 last:border-0">
      <span className="text-xs text-white/40">{label}</span>
      <span className="text-xs text-white/80 font-mono">{value}</span>
    </div>
  );
}

// ── Production launch checklist ───────────────────────────────────────────────

function LaunchReadinessSection() {
  const { data: health } = useHealth();
  const { data: info } = useSystemInfo();
  const { data: counts } = useDataCounts();
  const { data: integrations } = useIntegrationsStatus();

  const apiOk       = health?.status === "ok";
  const dbOk        = health?.components?.database?.status === "ok";
  const isProd      = !!info?.is_production;
  const aiOk        = !!(info?.env_keys?.gemini || info?.env_keys?.openai);
  const storageOk   = !!info?.env_keys?.s3;
  const courierOk   = integrations?.courier?.some((p) => p.is_configured) ?? false;
  const paymentOk   = integrations?.payment?.some((p) => p.is_configured) ?? false;
  const hasProducts = (counts?.products ?? 0) > 0;
  const hasOrders   = (counts?.orders ?? 0) > 0;

  const items: Array<{ label: string; ok: boolean | undefined; hint: string }> = [
    { label: "API Online",           ok: apiOk,       hint: "Backend API must respond"                     },
    { label: "Database Connected",   ok: dbOk,        hint: "PostgreSQL connection required"                },
    { label: "Production Mode",      ok: isProd,      hint: "Set IS_PRODUCTION=true in .env"               },
    { label: "AI Keys Configured",   ok: aiOk,        hint: "Set GEMINI_API_KEY or OPENAI_API_KEY"        },
    { label: "File Storage (S3/R2)", ok: storageOk,   hint: "Set S3_BUCKET_NAME + S3_ACCESS_KEY + S3_SECRET_KEY" },
    { label: "Courier Provider Live",ok: courierOk,   hint: "Configure Pathao, Steadfast, or REDX in .env" },
    { label: "Payment Gateway Live", ok: paymentOk,   hint: "Configure bKash, Nagad, or SSLCommerz in .env" },
    { label: "Products Published",   ok: hasProducts, hint: "Add at least one published product"           },
    { label: "First Order Received", ok: hasOrders,   hint: "Your store is live when orders arrive"        },
  ];

  const passed = items.filter((i) => i.ok).length;

  return (
    <div className="glass-card rounded-xl p-5 border border-primary/20">
      <div className="flex items-center gap-2 mb-1">
        <Rocket className="h-4 w-4 text-primary" />
        <h2 className="text-sm font-semibold text-white">Production Launch Checklist</h2>
        <span className="ml-auto text-xs font-bold text-white/60">
          {passed}/{items.length}
        </span>
      </div>
      <div className="w-full h-1.5 rounded-full bg-white/10 mb-4">
        <div
          className="h-1.5 rounded-full bg-primary transition-all"
          style={{ width: `${Math.round((passed / items.length) * 100)}%` }}
        />
      </div>
      <div className="space-y-2">
        {items.map(({ label, ok, hint }) => (
          <div key={label} className="flex items-start gap-2.5">
            {ok === undefined ? (
              <Loader2 className="h-3.5 w-3.5 text-white/30 animate-spin mt-0.5 shrink-0" />
            ) : ok ? (
              <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400 mt-0.5 shrink-0" />
            ) : (
              <XCircle className="h-3.5 w-3.5 text-red-400/70 mt-0.5 shrink-0" />
            )}
            <div>
              <p className={`text-xs font-medium ${ok ? "text-white/80" : "text-white/50"}`}>{label}</p>
              {!ok && <p className="text-[10px] text-white/30 mt-0.5">{hint}</p>}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ── sections ─────────────────────────────────────────────────────────────────

function HealthSection() {
  const { data: health } = useHealth();
  const apiOk = health?.status === "ok";
  const dbOk = health?.components?.database?.status === "ok";

  return (
    <div className="glass-card rounded-xl p-5 space-y-3">
      <div className="flex items-center gap-2 mb-2">
        <Server className="h-4 w-4 text-primary" />
        <h2 className="text-sm font-semibold text-white">System Status</h2>
      </div>
      <div className="grid grid-cols-2 gap-3">
        <div className="bg-white/5 rounded-lg p-3 flex items-center gap-2">
          <StatusDot ok={apiOk} />
          <div>
            <p className="text-xs font-medium text-white">API</p>
            <p className="text-[10px] text-white/40">{apiOk ? "Online" : "Offline"}</p>
          </div>
        </div>
        <div className="bg-white/5 rounded-lg p-3 flex items-center gap-2">
          <StatusDot ok={dbOk} />
          <div>
            <p className="text-xs font-medium text-white">Database</p>
            <p className="text-[10px] text-white/40">{dbOk ? "Connected" : "Error"}</p>
          </div>
        </div>
        <div className="bg-white/5 rounded-lg p-3 flex items-center gap-2">
          <StatusDot ok={health !== undefined} />
          <div>
            <p className="text-xs font-medium text-white">Version</p>
            <p className="text-[10px] text-white/40">{health?.version ?? "—"}</p>
          </div>
        </div>
        <div className="bg-white/5 rounded-lg p-3 flex items-center gap-2">
          <StatusDot ok={true} />
          <div>
            <p className="text-xs font-medium text-white">Phase</p>
            <p className="text-[10px] text-white/40">8 — Launch Ready</p>
          </div>
        </div>
      </div>
    </div>
  );
}

function SystemInfoSection() {
  const { data: info, isLoading } = useSystemInfo();

  return (
    <div className="glass-card rounded-xl p-5">
      <div className="flex items-center gap-2 mb-3">
        <Cpu className="h-4 w-4 text-primary" />
        <h2 className="text-sm font-semibold text-white">Runtime</h2>
        {isLoading && <Loader2 className="h-3 w-3 animate-spin text-white/30 ml-auto" />}
      </div>
      {info ? (
        <div>
          <InfoRow label="Version" value={info.version} />
          <InfoRow label="Python" value={info.python_version} />
          <InfoRow label="Platform" value={info.platform} />
          <InfoRow label="Uptime" value={formatUptime(info.uptime_seconds)} />
          <InfoRow label="Migration" value={info.alembic_revision} />
          <InfoRow label="Environment" value={
            <StatusBadge ok={info.is_production} label={info.is_production ? "Production" : "Development"} />
          } />
        </div>
      ) : (
        <p className="text-xs text-white/30 text-center py-4">Loading system info…</p>
      )}
    </div>
  );
}

function EnvKeysSection() {
  const { data: info } = useSystemInfo();
  const keys = info?.env_keys ?? {};

  const rows: Array<{ key: string; label: string }> = [
    { key: "gemini",    label: "Gemini AI"    },
    { key: "openai",    label: "OpenAI"       },
    { key: "anthropic", label: "Anthropic"    },
    { key: "whatsapp",  label: "WhatsApp API" },
    { key: "s3",        label: "S3 / R2 Storage" },
  ];

  return (
    <div className="glass-card rounded-xl p-5">
      <div className="flex items-center gap-2 mb-3">
        <Key className="h-4 w-4 text-primary" />
        <h2 className="text-sm font-semibold text-white">API Keys</h2>
      </div>
      <div className="space-y-2">
        {rows.map(({ key, label }) => (
          <div key={key} className="flex items-center justify-between">
            <span className="text-xs text-white/50">{label}</span>
            <StatusBadge ok={keys[key]} label={keys[key] ? "Configured" : "Not set"} />
          </div>
        ))}
      </div>
    </div>
  );
}

function DataSection() {
  const { data: counts } = useDataCounts();

  const rows = [
    { label: "Products",   icon: Package,      value: counts?.products   },
    { label: "Customers",  icon: Users,        value: counts?.customers  },
    { label: "Orders",     icon: ShoppingCart, value: counts?.orders     },
    { label: "Campaigns",  icon: Megaphone,    value: counts?.campaigns  },
  ];

  return (
    <div className="glass-card rounded-xl p-5">
      <div className="flex items-center gap-2 mb-3">
        <Database className="h-4 w-4 text-primary" />
        <h2 className="text-sm font-semibold text-white">Data Summary</h2>
      </div>
      <div className="grid grid-cols-2 gap-2">
        {rows.map(({ label, icon: Icon, value }) => (
          <div key={label} className="bg-white/5 rounded-lg p-3 flex items-center gap-2">
            <Icon className="h-3.5 w-3.5 text-white/30 shrink-0" />
            <div>
              <p className="text-xs text-white/40">{label}</p>
              <p className="text-sm font-semibold text-white">{value ?? "—"}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function MetricsSection() {
  const { data: metrics } = useSystemMetrics();

  return (
    <div className="glass-card rounded-xl p-5">
      <div className="flex items-center gap-2 mb-3">
        <Terminal className="h-4 w-4 text-primary" />
        <h2 className="text-sm font-semibold text-white">Request Metrics</h2>
      </div>
      {metrics ? (
        <>
          <div className="grid grid-cols-2 gap-3 mb-4">
            <div className="bg-white/5 rounded-lg p-3 text-center">
              <p className="text-lg font-bold text-white">{metrics.total_requests}</p>
              <p className="text-[10px] text-white/40">Total Requests</p>
            </div>
            <div className="bg-white/5 rounded-lg p-3 text-center">
              <p className="text-lg font-bold text-red-400">{metrics.total_errors}</p>
              <p className="text-[10px] text-white/40">Errors</p>
            </div>
          </div>
          {metrics.top_paths.length > 0 && (
            <div className="space-y-1">
              <p className="text-[10px] text-white/30 uppercase tracking-widest mb-2">Top Paths</p>
              {metrics.top_paths.slice(0, 5).map(({ path, count }) => (
                <div key={path} className="flex items-center justify-between text-xs">
                  <span className="text-white/40 font-mono truncate max-w-[70%]">{path}</span>
                  <span className="text-white/60">{count}</span>
                </div>
              ))}
            </div>
          )}
        </>
      ) : (
        <p className="text-xs text-white/30 text-center py-4">Loading metrics…</p>
      )}
    </div>
  );
}

function DemoCredentials() {
  return (
    <div className="glass-card rounded-xl p-5 border border-amber-500/20">
      <div className="flex items-center gap-2 mb-3">
        <Clock className="h-4 w-4 text-amber-400" />
        <h2 className="text-sm font-semibold text-white">Demo Credentials</h2>
        <span className="ml-auto px-2 py-0.5 rounded-full bg-amber-500/20 text-amber-300 text-[10px] font-medium">
          Dev only
        </span>
      </div>
      <div className="space-y-1.5 font-mono">
        <InfoRow label="Phone" value="+8801700000001" />
        <InfoRow label="Email" value="demo@sellermate.ai" />
        <InfoRow label="Password" value="Demo1234!" />
      </div>
      <p className="text-[10px] text-white/30 mt-3">
        Run <code className="bg-white/10 px-1 rounded">python -m scripts.seed_demo</code> from apps/api to seed this account.
      </p>
    </div>
  );
}

// ── page ─────────────────────────────────────────────────────────────────────

export default function DeploymentPage() {
  const qc = useQueryClient();

  function refresh() {
    qc.invalidateQueries({ queryKey: ["system-info"] });
    qc.invalidateQueries({ queryKey: ["system-metrics"] });
    qc.invalidateQueries({ queryKey: ["health"] });
    qc.invalidateQueries({ queryKey: ["data-counts"] });
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center gap-2 text-xs text-white/40 mb-1">
            <span>System</span>
            <span>/</span>
            <span className="text-white/60">Deployment</span>
          </div>
          <h1 className="text-xl font-bold gradient-text">Deployment Status</h1>
          <p className="text-sm text-white/40 mt-0.5">
            Runtime health, configuration, and data summary.
          </p>
        </div>
        <button
          onClick={refresh}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white/5 hover:bg-white/10 text-white/60 hover:text-white text-xs transition-colors"
        >
          <RefreshCw className="h-3 w-3" />
          Refresh
        </button>
      </div>

      {/* Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="md:col-span-2">
          <LaunchReadinessSection />
        </div>
        <HealthSection />
        <SystemInfoSection />
        <EnvKeysSection />
        <DataSection />
        <MetricsSection />
        <DemoCredentials />
      </div>
    </div>
  );
}
