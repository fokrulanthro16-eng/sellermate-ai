import { useQuery } from "@tanstack/react-query";
import api from "@/lib/api-client";

const fetch = async <T>(path: string): Promise<T> => {
  const { data } = await api.get<{ data: T }>(`/commerce${path}`);
  return data.data;
};

export function usePriceRecommendations() {
  return useQuery({ queryKey: ["commerce", "price-recs"], queryFn: () => fetch("/price-recommendations") });
}

export function useDemandPredictions() {
  return useQuery({ queryKey: ["commerce", "demand"], queryFn: () => fetch("/demand-predictions") });
}

export function useInventoryForecast() {
  return useQuery({ queryKey: ["commerce", "inv-forecast"], queryFn: () => fetch("/inventory-forecast") });
}

export function useRestockRecommendations() {
  return useQuery({ queryKey: ["commerce", "restock"], queryFn: () => fetch("/restock-recommendations") });
}

export function useBundleRecommendations() {
  return useQuery({ queryKey: ["commerce", "bundles"], queryFn: () => fetch("/bundle-recommendations") });
}

export function useBestSellers(days = 30) {
  return useQuery({ queryKey: ["commerce", "best-sellers", days], queryFn: () => fetch(`/best-sellers?days=${days}`) });
}

export function useWorstSellers(days = 30) {
  return useQuery({ queryKey: ["commerce", "worst-sellers", days], queryFn: () => fetch(`/worst-sellers?days=${days}`) });
}
