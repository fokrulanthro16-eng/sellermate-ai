import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import api from "@/lib/api-client";
import { getApiError } from "@/lib/utils";
import type { StrategicRunResult, StrategicInsight, ApiResponse } from "@/types";

export interface PriceCheckOut {
  verdict: string;
  avg_discount_pct: number;
  heavily_discounted_count: number;
  total_products_analyzed: number;
  recommendations: string[];
  price_items: { product_name: string; product_id: string; times_sold: number; avg_selling_price: number }[];
  explanation_bn: string;
  explanation_en: string;
}

const STR_KEY = "strategic";

async function runAgents() {
  const { data } = await api.post<ApiResponse<StrategicRunResult>>("/ai/strategic/run");
  return data.data;
}

async function fetchInsights(agent_name?: string, limit = 20) {
  const { data } = await api.get<ApiResponse<StrategicInsight[]>>("/ai/strategic/insights", {
    params: { agent_name, limit },
  });
  return data.data;
}

async function fetchTrustScore() {
  const { data } = await api.get<ApiResponse<StrategicInsight>>("/ai/strategic/trust-score");
  return data.data;
}

async function fetchFraudReport() {
  const { data } = await api.get<ApiResponse<StrategicInsight>>("/ai/strategic/fraud-report");
  return data.data;
}

export function useInsights(agent_name?: string) {
  return useQuery({
    queryKey: [STR_KEY, "insights", agent_name],
    queryFn: () => fetchInsights(agent_name),
  });
}

export function useTrustScore() {
  return useQuery({
    queryKey: [STR_KEY, "trust-score"],
    queryFn: fetchTrustScore,
    retry: false,
  });
}

export function useFraudReport() {
  return useQuery({
    queryKey: [STR_KEY, "fraud-report"],
    queryFn: fetchFraudReport,
    retry: false,
  });
}

export function useGrowthCoach() {
  return useQuery({
    queryKey: [STR_KEY, "growth_coach"],
    queryFn: () => fetchInsights("growth_coach", 1).then((r) => r[0] ?? null),
    retry: false,
  });
}

export function useCreditReadiness() {
  return useQuery({
    queryKey: [STR_KEY, "credit_readiness"],
    queryFn: () => fetchInsights("credit_readiness", 1).then((r) => r[0] ?? null),
    retry: false,
  });
}

export function useMarginGuardian() {
  return useQuery({
    queryKey: [STR_KEY, "margin_guardian"],
    queryFn: () => fetchInsights("margin_guardian", 1).then((r) => r[0] ?? null),
    retry: false,
  });
}

export function useDemandOracle() {
  return useQuery({
    queryKey: [STR_KEY, "demand_oracle"],
    queryFn: () => fetchInsights("demand_oracle", 1).then((r) => r[0] ?? null),
    retry: false,
  });
}

async function fetchPriceCheck() {
  const { data } = await api.get<ApiResponse<PriceCheckOut>>("/ai/strategic/price-check");
  return data.data;
}

export function usePriceCheck() {
  return useQuery({
    queryKey: [STR_KEY, "price_check"],
    queryFn: fetchPriceCheck,
    retry: false,
  });
}

export function useRunAgents() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: runAgents,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: [STR_KEY] });
      toast.success("এআই বিশ্লেষণ সম্পন্ন হয়েছে");
    },
    onError: (e) => toast.error(getApiError(e)),
  });
}
