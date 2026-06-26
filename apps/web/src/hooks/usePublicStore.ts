import { useMutation, useQuery } from "@tanstack/react-query";

const BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";
const API = `${BASE}/public`;

async function get(path: string) {
  const res = await fetch(`${API}${path}`);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

async function post(path: string, body: unknown) {
  const res = await fetch(`${API}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err?.error?.message || `HTTP ${res.status}`);
  }
  return res.json();
}

export function useMarketplace(search?: string, district?: string) {
  return useQuery({
    queryKey: ["public-stores", search, district],
    queryFn: () => {
      const params = new URLSearchParams();
      if (search) params.set("search", search);
      if (district) params.set("district", district);
      return get(`/stores?${params}`);
    },
  });
}

export function useStoreBySlug(slug: string) {
  return useQuery({
    queryKey: ["public-store", slug],
    queryFn: () => get(`/stores/${slug}`),
    enabled: !!slug,
  });
}

export function useStoreProducts(slug: string, category?: string, limit = 100) {
  return useQuery({
    queryKey: ["public-store-products", slug, category, limit],
    queryFn: () => {
      const params = new URLSearchParams();
      if (category) params.set("category", category);
      params.set("limit", String(limit));
      return get(`/stores/${slug}/products?${params}`);
    },
    enabled: !!slug,
  });
}

export function useSearchProducts(q: string, category?: string, minPrice?: number, maxPrice?: number) {
  return useQuery({
    queryKey: ["public-search", q, category, minPrice, maxPrice],
    queryFn: () => {
      const params = new URLSearchParams({ q });
      if (category) params.set("category", category);
      if (minPrice != null) params.set("min_price", String(minPrice));
      if (maxPrice != null) params.set("max_price", String(maxPrice));
      return get(`/search?${params}`);
    },
    enabled: q.length > 0,
  });
}

export function usePlaceOrder() {
  return useMutation({
    mutationFn: (body: {
      merchant_id: string;
      items: Array<{ product_id: string; quantity: number }>;
      customer_name: string;
      customer_phone: string;
      customer_email?: string;
      delivery_address: string;
      delivery_district?: string;
      payment_method?: string;
      notes?: string;
    }) => post("/orders", body),
  });
}

export function usePublicOrder(orderId: string) {
  return useQuery({
    queryKey: ["public-order", orderId],
    queryFn: () => get(`/orders/${orderId}`),
    enabled: !!orderId,
  });
}
