import { useQuery } from "@tanstack/react-query";
import { toast } from "sonner";
import api from "@/lib/api-client";
import { getApiError } from "@/lib/utils";

const fetch = async <T>(path: string): Promise<T> => {
  const { data } = await api.get<{ data: T }>(`/reports${path}`);
  return data.data;
};

export function useCustomerLTV() {
  return useQuery({ queryKey: ["reports", "ltv"], queryFn: () => fetch("/customer-ltv") });
}

export function useChurnRisk() {
  return useQuery({ queryKey: ["reports", "churn"], queryFn: () => fetch("/churn-risk") });
}

export function useRevenueForecast() {
  return useQuery({ queryKey: ["reports", "revenue-forecast"], queryFn: () => fetch("/revenue-forecast") });
}

export function useHealthScore() {
  return useQuery({ queryKey: ["reports", "health-score"], queryFn: () => fetch("/health-score") });
}

export function useProfitReport(days = 30) {
  return useQuery({ queryKey: ["reports", "profit", days], queryFn: () => fetch(`/profit?days=${days}`) });
}

export function useTaxSummary(days = 30) {
  return useQuery({ queryKey: ["reports", "tax", days], queryFn: () => fetch(`/tax-summary?days=${days}`) });
}

export async function downloadFile(path: string, filename: string) {
  try {
    const res = await api.get(`/reports/${path}`, { responseType: "blob" });
    const url = URL.createObjectURL(res.data as Blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
  } catch (e) {
    toast.error(getApiError(e));
  }
}

export const downloadPDF = (days = 30) => downloadFile(`export/pdf?days=${days}`, `sellermate_${days}d.pdf`);
export const downloadExcel = (days = 30) => downloadFile(`export/excel?days=${days}`, `sellermate_${days}d.xlsx`);
