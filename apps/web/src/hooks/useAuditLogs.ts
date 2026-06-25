import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api-client";

export interface AuditLogEntry {
  id: string;
  action: string;
  resource_type: string;
  resource_id: string;
  resource_label: string;
  details: Record<string, unknown> | null;
  created_at: string;
}

export interface AuditLogPage {
  logs: AuditLogEntry[];
  total: number;
  page: number;
  limit: number;
}

export function useAuditLogs(params?: { page?: number; resource_type?: string; action?: string }) {
  const p = params || {};
  return useQuery<AuditLogPage>({
    queryKey: ["audit-logs", p.page, p.resource_type, p.action],
    queryFn: async () => {
      const search = new URLSearchParams();
      if (p.page) search.set("page", String(p.page));
      if (p.resource_type) search.set("resource_type", p.resource_type);
      if (p.action) search.set("action", p.action);
      const res = await api.get(`/audit-logs?${search.toString()}`);
      return (res.data as any).data as AuditLogPage;
    },
    staleTime: 15_000,
  });
}

export function useAuditSummary() {
  return useQuery<Record<string, number>>({
    queryKey: ["audit-summary"],
    queryFn: async () => {
      const res = await api.get("/audit-logs/summary");
      return (res.data as any).data as Record<string, number>;
    },
    staleTime: 30_000,
  });
}
