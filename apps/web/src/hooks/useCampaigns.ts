import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import api from "@/lib/api-client";
import { getApiError } from "@/lib/utils";

export interface CampaignGenerateRequest {
  campaign_type: string;
  product_name: string;
  product_price: string;
  language?: string;
  tone?: string;
  extra_context?: string;
}

export interface Campaign {
  id: string;
  title: string;
  campaign_type: string;
  content: string;
  language: string;
  status: string;
  provider: string;
  created_at: string;
}

export function useCampaigns(campaign_type?: string) {
  const params = campaign_type ? `?campaign_type=${campaign_type}` : "";
  return useQuery<Campaign[]>({
    queryKey: ["campaigns", campaign_type],
    queryFn: async () => {
      const { data } = await api.get<{ data: Campaign[] }>(`/campaigns${params}`);
      return data.data;
    },
  });
}

export function useGenerateCampaign() {
  const qc = useQueryClient();
  return useMutation<Campaign, Error, CampaignGenerateRequest>({
    mutationFn: async (payload) => {
      const { data } = await api.post<{ data: Campaign }>("/campaigns", payload);
      return data.data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["campaigns"] });
      toast.success("Campaign generated!");
    },
    onError: (e) => toast.error(getApiError(e)),
  });
}

export function useDeleteCampaign() {
  const qc = useQueryClient();
  return useMutation<void, Error, string>({
    mutationFn: async (id) => {
      await api.delete(`/campaigns/${id}`);
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["campaigns"] });
      toast.success("Campaign deleted");
    },
    onError: (e) => toast.error(getApiError(e)),
  });
}
