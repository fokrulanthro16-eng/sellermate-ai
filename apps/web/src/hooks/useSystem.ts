import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api-client";

export interface SystemInfo {
  version: string;
  phase: string;
  python_version: string;
  platform: string;
  uptime_seconds: number;
  alembic_revision: string;
  is_production: boolean;
  env_keys: Record<string, boolean>;
}

export interface SystemMetrics {
  uptime_seconds: number;
  total_requests: number;
  total_errors: number;
  top_paths: Array<{ path: string; count: number }>;
}

export interface DataCounts {
  products: number;
  customers: number;
  orders: number;
  campaigns: number;
}

export function useSystemInfo() {
  return useQuery<SystemInfo>({
    queryKey: ["system-info"],
    queryFn: async () => {
      const { data } = await api.get("/system/info");
      return data.data;
    },
    refetchInterval: 60_000,
    retry: false,
  });
}

export function useSystemMetrics() {
  return useQuery<SystemMetrics>({
    queryKey: ["system-metrics"],
    queryFn: async () => {
      const { data } = await api.get("/system/metrics");
      return data.data;
    },
    refetchInterval: 30_000,
    retry: false,
  });
}

export function useSystemUptime() {
  return useQuery<{ status: string; uptime_seconds: number; started_at: string; version: string }>({
    queryKey: ["system-uptime"],
    queryFn: async () => {
      const { data } = await api.get("/system/uptime");
      return data;
    },
    refetchInterval: 15_000,
    retry: false,
  });
}

export function useDataCounts() {
  return useQuery<DataCounts>({
    queryKey: ["data-counts"],
    queryFn: async () => {
      const { data } = await api.get("/backup/export/summary");
      return data.data.counts;
    },
    refetchInterval: 60_000,
    retry: false,
  });
}
