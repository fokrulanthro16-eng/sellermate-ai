import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api-client";

export interface HealthStatus {
  status: "ok" | "degraded";
  version: string;
  components: {
    api: { status: string };
    database: { status: string; error?: string | null };
  };
}

export function useHealth() {
  return useQuery<HealthStatus>({
    queryKey: ["health"],
    queryFn: async () => {
      const res = await api.get("/health");
      return res.data as HealthStatus;
    },
    staleTime: 30_000,
    refetchInterval: 60_000,
    retry: false,
  });
}
