import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api-client";

export interface ProviderStatus {
  active_provider: "gemini" | "openai" | "anthropic" | "mock";
  display_label: string;
  is_mock: boolean;
}

export function useProviderStatus() {
  return useQuery<ProviderStatus>({
    queryKey: ["ai-provider-status"],
    queryFn: async () => {
      const res = await api.get<ProviderStatus>("/ai/provider/status");
      return res.data;
    },
    staleTime: 60_000,
  });
}
