"use client";

import { useState } from "react";
import { toast } from "sonner";
import {
  RefreshCw, Truck, CreditCard, Store, ShoppingBag,
  CheckCircle2, XCircle, Clock, Loader2, Webhook, Briefcase,
} from "lucide-react";
import {
  useJobs,
  useEnqueueJob,
  useRetryJob,
  useWebhookEvents,
  useRetryWebhookEvent,
  type BackgroundJob,
  type WebhookEvent,
} from "@/hooks/useOperations";

// ── helpers ────────────────────────────────────────────────────────────────

function timeAgo(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  const s = Math.floor(diff / 1000);
  if (s < 60) return `${s}s ago`;
  const m = Math.floor(s / 60);
  if (m < 60) return `${m}m ago`;
  const h = Math.floor(m / 60);
  if (h < 24) return `${h}h ago`;
  return `${Math.floor(h / 24)}d ago`;
}

function JobStatusBadge({ status }: { status: BackgroundJob["status"] }) {
  const cfg = {
    queued:  { cls: "bg-slate-500/20 text-slate-300",   icon: Clock,        label: "Queued"  },
    running: { cls: "bg-blue-500/20 text-blue-300",     icon: Loader2,      label: "Running" },
    done:    { cls: "bg-emerald-500/20 text-emerald-300", icon: CheckCircle2, label: "Done"    },
    failed:  { cls: "bg-red-500/20 text-red-300",       icon: XCircle,      label: "Failed"  },
  }[status] ?? { cls: "bg-slate-500/20 text-slate-300", icon: Clock, label: status };

  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium ${cfg.cls}`}>
      <cfg.icon className="h-3 w-3" />
      {cfg.label}
    </span>
  );
}

function WebhookStatusBadge({ status }: { status: WebhookEvent["status"] }) {
  const cfg = {
    pending:   { cls: "bg-amber-500/20 text-amber-300",    icon: Clock,        label: "Pending"   },
    processed: { cls: "bg-emerald-500/20 text-emerald-300", icon: CheckCircle2, label: "Processed" },
    failed:    { cls: "bg-red-500/20 text-red-300",        icon: XCircle,      label: "Failed"    },
  }[status] ?? { cls: "bg-slate-500/20 text-slate-300", icon: Clock, label: status };

  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium ${cfg.cls}`}>
      <cfg.icon className="h-3 w-3" />
      {cfg.label}
    </span>
  );
}

function resultSummary(result?: Record<string, unknown> | null): string {
  if (!result) return "—";
  const parts: string[] = [];
  for (const [k, v] of Object.entries(result)) {
    if (k === "provider") continue;
    parts.push(`${k}: ${v}`);
  }
  if (result.provider) parts.push(String(result.provider));
  return parts.join(" · ") || "—";
}

// ── sync cards ────────────────────────────────────────────────────────────

const SYNC_JOBS = [
  { job_type: "courier_sync",              label: "Courier Sync",      icon: Truck,       provider: "pathao"    },
  { job_type: "payment_sync",              label: "Payment Sync",      icon: CreditCard,  provider: "sslcommerz" },
  { job_type: "marketplace_product_sync",  label: "Product Sync",      icon: Store,       provider: "facebook"  },
  { job_type: "marketplace_order_sync",    label: "Order Sync",        icon: ShoppingBag, provider: "daraz"     },
] as const;

function SyncCard({
  job_type,
  label,
  icon: Icon,
  provider,
}: (typeof SYNC_JOBS)[number]) {
  const { mutateAsync, isPending } = useEnqueueJob();
  const [lastResult, setLastResult] = useState<string | null>(null);

  async function run() {
    try {
      const job = await mutateAsync({ job_type, payload: { provider } });
      setLastResult(resultSummary(job.result));
      toast.success(`${label} complete`);
    } catch {
      toast.error(`${label} failed`);
    }
  }

  return (
    <div className="glass-card rounded-xl p-4 flex flex-col gap-3">
      <div className="flex items-center gap-2">
        <div className="h-8 w-8 rounded-lg gradient-primary flex items-center justify-center shrink-0">
          <Icon className="h-4 w-4 text-white" />
        </div>
        <div>
          <p className="text-sm font-medium text-white">{label}</p>
          <p className="text-xs text-white/40">{provider} (mock)</p>
        </div>
      </div>
      {lastResult && (
        <p className="text-xs text-emerald-400 truncate">{lastResult}</p>
      )}
      <button
        onClick={run}
        disabled={isPending}
        className="flex items-center justify-center gap-1.5 w-full py-1.5 rounded-lg bg-primary/20 hover:bg-primary/30 text-primary text-xs font-medium transition-colors disabled:opacity-50"
      >
        {isPending ? (
          <Loader2 className="h-3 w-3 animate-spin" />
        ) : (
          <RefreshCw className="h-3 w-3" />
        )}
        Run Now
      </button>
    </div>
  );
}

// ── jobs table ────────────────────────────────────────────────────────────

function JobsTable() {
  const { data, isLoading } = useJobs();
  const retryJob = useRetryJob();

  if (isLoading) {
    return (
      <div className="flex justify-center py-8">
        <Loader2 className="h-5 w-5 animate-spin text-white/40" />
      </div>
    );
  }

  const items = data?.items ?? [];

  if (items.length === 0) {
    return (
      <div className="text-center py-10 text-white/30 text-sm">
        No jobs yet — run a sync above to create one.
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-white/10 text-white/40 text-xs">
            <th className="text-left py-2 px-3 font-medium">Type</th>
            <th className="text-left py-2 px-3 font-medium">Status</th>
            <th className="text-left py-2 px-3 font-medium">Result</th>
            <th className="text-left py-2 px-3 font-medium">Retries</th>
            <th className="text-left py-2 px-3 font-medium">Created</th>
            <th className="text-left py-2 px-3 font-medium">Action</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-white/5">
          {items.map((job) => (
            <tr key={job.id} className="hover:bg-white/3 transition-colors">
              <td className="py-2.5 px-3 text-white/80 font-mono text-xs">{job.job_type}</td>
              <td className="py-2.5 px-3"><JobStatusBadge status={job.status} /></td>
              <td className="py-2.5 px-3 text-white/50 text-xs max-w-xs truncate">
                {resultSummary(job.result)}
              </td>
              <td className="py-2.5 px-3 text-white/40 text-xs">{job.retry_count}</td>
              <td className="py-2.5 px-3 text-white/40 text-xs">{timeAgo(job.created_at)}</td>
              <td className="py-2.5 px-3">
                <button
                  onClick={() => retryJob.mutate(job.id)}
                  disabled={retryJob.isPending}
                  className="text-xs text-primary hover:text-primary/80 flex items-center gap-1 disabled:opacity-40"
                >
                  <RefreshCw className="h-3 w-3" /> Retry
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// ── webhook events table ──────────────────────────────────────────────────

function WebhookEventsTable() {
  const { data, isLoading } = useWebhookEvents();
  const retryEvent = useRetryWebhookEvent();

  if (isLoading) {
    return (
      <div className="flex justify-center py-8">
        <Loader2 className="h-5 w-5 animate-spin text-white/40" />
      </div>
    );
  }

  const items = data?.items ?? [];

  if (items.length === 0) {
    return (
      <div className="text-center py-10 text-white/30 text-sm">
        No webhook events received yet.
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-white/10 text-white/40 text-xs">
            <th className="text-left py-2 px-3 font-medium">Provider</th>
            <th className="text-left py-2 px-3 font-medium">Event Type</th>
            <th className="text-left py-2 px-3 font-medium">Status</th>
            <th className="text-left py-2 px-3 font-medium">Retries</th>
            <th className="text-left py-2 px-3 font-medium">Received</th>
            <th className="text-left py-2 px-3 font-medium">Action</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-white/5">
          {items.map((evt) => (
            <tr key={evt.id} className="hover:bg-white/3 transition-colors">
              <td className="py-2.5 px-3">
                <span className="px-2 py-0.5 rounded-full bg-white/10 text-white/70 text-xs font-mono">
                  {evt.provider}
                </span>
              </td>
              <td className="py-2.5 px-3 text-white/60 text-xs font-mono">{evt.event_type}</td>
              <td className="py-2.5 px-3"><WebhookStatusBadge status={evt.status} /></td>
              <td className="py-2.5 px-3 text-white/40 text-xs">{evt.retry_count}</td>
              <td className="py-2.5 px-3 text-white/40 text-xs">{timeAgo(evt.received_at)}</td>
              <td className="py-2.5 px-3">
                <button
                  onClick={() => retryEvent.mutate(evt.id)}
                  disabled={retryEvent.isPending}
                  className="text-xs text-primary hover:text-primary/80 flex items-center gap-1 disabled:opacity-40"
                >
                  <RefreshCw className="h-3 w-3" /> Retry
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// ── page ──────────────────────────────────────────────────────────────────

export default function IntegrationOperationsPage() {
  const [tab, setTab] = useState<"jobs" | "webhooks">("jobs");

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <div className="flex items-center gap-2 text-xs text-white/40 mb-1">
          <span>Integrations</span>
          <span>/</span>
          <span className="text-white/60">Operations</span>
        </div>
        <h1 className="text-xl font-bold gradient-text">Integration Operations</h1>
        <p className="text-sm text-white/40 mt-0.5">
          Background jobs, webhook events, and provider sync — all mock mode.
        </p>
      </div>

      {/* Sync Cards */}
      <div>
        <h2 className="text-xs font-semibold uppercase tracking-widest text-white/30 mb-3">
          Run Sync Jobs
        </h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {SYNC_JOBS.map((s) => (
            <SyncCard key={s.job_type} {...s} />
          ))}
        </div>
      </div>

      {/* Tabs */}
      <div className="glass-card rounded-xl overflow-hidden">
        <div className="flex border-b border-white/10">
          <button
            onClick={() => setTab("jobs")}
            className={`flex items-center gap-2 px-5 py-3 text-sm font-medium transition-colors ${
              tab === "jobs"
                ? "text-white border-b-2 border-primary -mb-px"
                : "text-white/40 hover:text-white/70"
            }`}
          >
            <Briefcase className="h-4 w-4" />
            Background Jobs
          </button>
          <button
            onClick={() => setTab("webhooks")}
            className={`flex items-center gap-2 px-5 py-3 text-sm font-medium transition-colors ${
              tab === "webhooks"
                ? "text-white border-b-2 border-primary -mb-px"
                : "text-white/40 hover:text-white/70"
            }`}
          >
            <Webhook className="h-4 w-4" />
            Webhook Events
          </button>
        </div>

        <div className="p-1">
          {tab === "jobs" ? <JobsTable /> : <WebhookEventsTable />}
        </div>
      </div>
    </div>
  );
}
