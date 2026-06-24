import { useQuery } from "@tanstack/react-query";
import api from "@/lib/api-client";
import type { ApiResponse, DashboardMetrics, OverviewMetrics, RevenuePoint, OrderBreakdown, TopProductItem, InventoryHealth, CustomerMetrics } from "@/types";

const A_KEY = "analytics";

async function fetchDashboard() {
  const { data } = await api.get<ApiResponse<DashboardMetrics>>("/analytics/dashboard");
  return data.data;
}

async function fetchOverview(from_date: string, to_date: string) {
  const { data } = await api.get<ApiResponse<OverviewMetrics>>("/analytics/overview", {
    params: { from_date, to_date },
  });
  return data.data;
}

async function fetchRevenue(from_date: string, to_date: string, granularity = "day") {
  const { data } = await api.get("/analytics/revenue", {
    params: { from_date, to_date, granularity },
  });
  // API returns { data: { period, points: RevenuePoint[] } }
  const points = data.data?.points;
  return Array.isArray(points) ? points : (Array.isArray(data.data) ? data.data : []) as RevenuePoint[];
}

async function fetchOrderBreakdown(from_date: string, to_date: string) {
  const { data } = await api.get<ApiResponse<OrderBreakdown>>("/analytics/orders", {
    params: { from_date, to_date },
  });
  return data.data;
}

async function fetchTopProducts(from_date: string, to_date: string) {
  const { data } = await api.get<ApiResponse<TopProductItem[]>>("/analytics/products/top", {
    params: { from_date, to_date },
  });
  return data.data;
}

async function fetchInventoryHealth() {
  const { data } = await api.get("/analytics/inventory");
  const d = data.data ?? {};
  // Normalize field names: API uses low_stock / out_of_stock; type uses low_stock_count / out_of_stock_count
  return {
    total_variants: d.total_variants ?? 0,
    low_stock_count: d.low_stock_count ?? d.low_stock ?? 0,
    out_of_stock_count: d.out_of_stock_count ?? d.out_of_stock ?? 0,
  } as InventoryHealth;
}

async function fetchCustomerMetrics(from_date: string, to_date: string) {
  const { data } = await api.get<ApiResponse<CustomerMetrics>>("/analytics/customers", {
    params: { from_date, to_date },
  });
  return data.data;
}

export function useDashboard() {
  return useQuery({
    queryKey: [A_KEY, "dashboard"],
    queryFn: fetchDashboard,
    staleTime: 60_000,
  });
}

export function useOverview(from_date: string, to_date: string) {
  return useQuery({
    queryKey: [A_KEY, "overview", from_date, to_date],
    queryFn: () => fetchOverview(from_date, to_date),
    enabled: !!from_date && !!to_date,
  });
}

export function useRevenue(from_date: string, to_date: string, granularity = "day") {
  return useQuery({
    queryKey: [A_KEY, "revenue", from_date, to_date, granularity],
    queryFn: () => fetchRevenue(from_date, to_date, granularity),
    enabled: !!from_date && !!to_date,
  });
}

export function useOrderBreakdown(from_date: string, to_date: string) {
  return useQuery({
    queryKey: [A_KEY, "orders", from_date, to_date],
    queryFn: () => fetchOrderBreakdown(from_date, to_date),
    enabled: !!from_date && !!to_date,
  });
}

export function useTopProducts(from_date: string, to_date: string) {
  return useQuery({
    queryKey: [A_KEY, "top-products", from_date, to_date],
    queryFn: () => fetchTopProducts(from_date, to_date),
    enabled: !!from_date && !!to_date,
  });
}

export function useInventoryHealth() {
  return useQuery({
    queryKey: [A_KEY, "inventory-health"],
    queryFn: fetchInventoryHealth,
  });
}

export function useCustomerMetrics(from_date: string, to_date: string) {
  return useQuery({
    queryKey: [A_KEY, "customers", from_date, to_date],
    queryFn: () => fetchCustomerMetrics(from_date, to_date),
    enabled: !!from_date && !!to_date,
  });
}
