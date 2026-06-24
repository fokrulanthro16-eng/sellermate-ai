import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import api from "@/lib/api-client";
import { getApiError } from "@/lib/utils";
import type { InventoryItem, InventoryLog, AdjustmentItem, ApiResponse, PaginatedData } from "@/types";

const INV_KEY = "inventory";

async function fetchInventory(params: { page?: number; limit?: number; low_stock?: boolean; variant_id?: string }) {
  const { data } = await api.get("/inventory", { params });
  const items = Array.isArray(data.data) ? data.data : [];
  const meta = data.meta ?? {};
  return { items, total: meta.total ?? 0, page: meta.page ?? 1, limit: meta.limit ?? 50, pages: meta.total_pages ?? 1 } as PaginatedData<InventoryItem>;
}

async function fetchAlerts() {
  const { data } = await api.get<ApiResponse<InventoryItem[]>>("/inventory/alerts");
  return data.data;
}

async function fetchLogs(params: { page?: number; limit?: number; variant_id?: string }) {
  const { data } = await api.get("/inventory/logs", { params });
  const items = Array.isArray(data.data) ? data.data : [];
  const meta = data.meta ?? {};
  return { items, total: meta.total ?? 0, page: meta.page ?? 1, limit: meta.limit ?? 20, pages: meta.total_pages ?? 1 } as PaginatedData<InventoryLog>;
}

async function adjustStock(items: AdjustmentItem[]) {
  const { data } = await api.post<ApiResponse<{ adjusted: number }>>("/inventory/adjust", { adjustments: items });
  return data.data;
}

export function useInventory(params: { page?: number; limit?: number; low_stock?: boolean; variant_id?: string } = {}) {
  return useQuery({
    queryKey: [INV_KEY, "list", params],
    queryFn: () => fetchInventory(params),
  });
}

export function useInventoryAlerts() {
  return useQuery({
    queryKey: [INV_KEY, "alerts"],
    queryFn: fetchAlerts,
  });
}

export function useInventoryLogs(params: { page?: number; limit?: number; variant_id?: string } = {}) {
  return useQuery({
    queryKey: [INV_KEY, "logs", params],
    queryFn: () => fetchLogs(params),
  });
}

export function useAdjustStock() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: adjustStock,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: [INV_KEY] });
      toast.success("স্টক আপডেট হয়েছে");
    },
    onError: (e) => toast.error(getApiError(e)),
  });
}
