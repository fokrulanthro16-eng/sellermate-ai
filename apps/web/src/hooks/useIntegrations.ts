import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api-client";

// ── Types ─────────────────────────────────────────────────────────────────────

export interface ProviderInfo {
  name: string;
  display_name: string;
  is_configured: boolean;
  mode: "real" | "mock";
}

export interface IntegrationsStatus {
  courier: ProviderInfo[];
  payment: ProviderInfo[];
  marketplace: ProviderInfo[];
  notification: ProviderInfo[];
}

export interface IntegrationConfig {
  courier?: Record<string, unknown>;
  payment?: Record<string, unknown>;
  marketplace?: Record<string, unknown>;
  notification?: Record<string, unknown>;
}

// ── Hooks ─────────────────────────────────────────────────────────────────────

export function useIntegrationsStatus() {
  return useQuery<IntegrationsStatus>({
    queryKey: ["integrations-status"],
    queryFn: async () => {
      const res = await api.get<IntegrationsStatus>("/integrations/status");
      return res.data;
    },
    staleTime: 30_000,
  });
}

export function useIntegrationSettings() {
  return useQuery<{ data: IntegrationConfig }>({
    queryKey: ["integration-settings"],
    queryFn: async () => {
      const res = await api.get<{ data: IntegrationConfig }>("/integrations/settings");
      return res.data;
    },
  });
}

export function useSaveIntegrationSettings() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (config: IntegrationConfig) => {
      const res = await api.put("/integrations/settings", { config });
      return res.data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["integration-settings"] }),
  });
}

export function useTestConnection() {
  return useMutation({
    mutationFn: async ({ domain, provider }: { domain: string; provider: string }) => {
      const res = await api.post(`/integrations/test/${domain}/${provider}`);
      return res.data as { success: boolean; message: string; mode: string };
    },
  });
}

export function useCreateShipment() {
  return useMutation({
    mutationFn: async (body: { order_id: string; courier_name: string }) => {
      const res = await api.post("/integrations/courier/shipment", body);
      return res.data as { success: boolean; data: Record<string, unknown> };
    },
  });
}

export function useCreatePaymentIntent() {
  return useMutation({
    mutationFn: async (body: { order_id: string; amount: number; provider: string }) => {
      const res = await api.post("/integrations/payment/intent", body);
      return res.data as { success: boolean; data: Record<string, unknown> };
    },
  });
}

export function useMarketplaceSync() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (body: { provider: string; sync_type: string }) => {
      const res = await api.post("/integrations/marketplace/sync", body);
      return res.data as { success: boolean; data: Record<string, unknown> };
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["marketplace-sync-status"] }),
  });
}

export function useMarketplaceSyncStatus() {
  return useQuery({
    queryKey: ["marketplace-sync-status"],
    queryFn: async () => {
      const res = await api.get("/integrations/marketplace/sync/status");
      return res.data as { success: boolean; data: Array<Record<string, unknown>> };
    },
  });
}

export function useSendNotification() {
  return useMutation({
    mutationFn: async (body: { channel: string; notification_type: string; recipient: string; extra_body?: string }) => {
      const res = await api.post("/integrations/notifications/send", body);
      return res.data as { success: boolean; data: Record<string, unknown> };
    },
  });
}

export const downloadInvoice = async (orderId: string, orderNumber: string) => {
  const res = await api.get(`/integrations/documents/invoice/${orderId}`, { responseType: "blob" });
  const url = URL.createObjectURL(res.data as Blob);
  const a = document.createElement("a");
  a.href = url; a.download = `invoice_${orderNumber}.pdf`; a.click();
  URL.revokeObjectURL(url);
};

export const downloadShippingLabel = async (orderId: string, orderNumber: string, courier = "manual") => {
  const res = await api.get(`/integrations/documents/shipping-label/${orderId}?courier=${courier}`, { responseType: "blob" });
  const url = URL.createObjectURL(res.data as Blob);
  const a = document.createElement("a");
  a.href = url; a.download = `label_${orderNumber}.pdf`; a.click();
  URL.revokeObjectURL(url);
};
