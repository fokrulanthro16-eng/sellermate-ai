import { useMutation, useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api-client";

export interface AgentInfo {
  id: string;
  name: string;
  name_bn: string;
  description: string;
  description_bn: string;
  icon: string;
  color: string;
}

export interface AgentInsight {
  type: string;
  title: string;
  value: string;
  change: string;
  detail: string;
  positive: boolean;
}

export interface AgentAction {
  label: string;
  href: string;
  priority: "high" | "medium" | "low";
}

export interface AgentChecklistItem {
  label: string;
  done: boolean;
  href: string;
}

export interface AgentResult {
  agent: string;
  generated_at: string;
  title: string;
  insights: AgentInsight[];
  actions: AgentAction[];
  checklist?: AgentChecklistItem[];
}

export function useAgentList() {
  return useQuery<AgentInfo[]>({
    queryKey: ["agents-list"],
    queryFn: async () => {
      const { data } = await api.get("/agents");
      return data.data;
    },
    staleTime: Infinity,
  });
}

export function useRunAgent() {
  return useMutation<AgentResult, Error, string>({
    mutationFn: async (agentId: string) => {
      const { data } = await api.post(`/agents/${agentId}/run`);
      return data.data;
    },
  });
}
