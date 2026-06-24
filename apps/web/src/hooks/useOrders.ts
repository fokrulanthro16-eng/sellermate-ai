import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import api from "@/lib/api-client";
import { getApiError } from "@/lib/utils";
import type { Order, CreateOrderPayload, ApiResponse, PaginatedData, OrderStatus, PaymentMethod } from "@/types";

const ORDERS_KEY = "orders";

interface OrderFilters {
  page?: number;
  limit?: number;
  status?: OrderStatus;
  payment_status?: string;
  search?: string;
}

async function fetchOrders(params: OrderFilters) {
  const { data } = await api.get("/orders", { params });
  const items = Array.isArray(data.data) ? data.data : [];
  const meta = data.meta ?? {};
  return { items, total: meta.total ?? 0, page: meta.page ?? 1, limit: meta.limit ?? 20, pages: meta.total_pages ?? 1 } as PaginatedData<Order>;
}

async function fetchOrder(id: string) {
  const { data } = await api.get<ApiResponse<Order>>(`/orders/${id}`);
  return data.data;
}

async function createOrder(payload: CreateOrderPayload) {
  const { data } = await api.post<ApiResponse<Order>>("/orders", payload);
  return data.data;
}

async function updateOrder(id: string, payload: Partial<{ delivery_address: string; tracking_number: string; courier_name: string; notes: string }>) {
  const { data } = await api.patch<ApiResponse<Order>>(`/orders/${id}`, payload);
  return data.data;
}

async function changeStatus(id: string, status: OrderStatus, note?: string) {
  const { data } = await api.post<ApiResponse<Order>>(`/orders/${id}/status`, { status, note });
  return data.data;
}

async function recordPayment(id: string, amount: string, method: PaymentMethod, reference?: string) {
  const { data } = await api.post<ApiResponse<Order>>(`/orders/${id}/payment`, {
    amount,
    method,
    reference,
  });
  return data.data;
}

async function cancelOrder(id: string) {
  const { data } = await api.delete<ApiResponse<Order>>(`/orders/${id}`);
  return data.data;
}

export function useOrders(params: OrderFilters = {}) {
  return useQuery({
    queryKey: [ORDERS_KEY, params],
    queryFn: () => fetchOrders(params),
  });
}

export function useOrder(id: string) {
  return useQuery({
    queryKey: [ORDERS_KEY, id],
    queryFn: () => fetchOrder(id),
    enabled: !!id,
  });
}

export function useCreateOrder() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: createOrder,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: [ORDERS_KEY] });
      toast.success("অর্ডার তৈরি হয়েছে");
    },
    onError: (e) => toast.error(getApiError(e)),
  });
}

export function useUpdateOrder() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, ...payload }: { id: string } & Partial<{ delivery_address: string; tracking_number: string; courier_name: string; notes: string }>) =>
      updateOrder(id, payload),
    onSuccess: (_data, { id }) => {
      qc.invalidateQueries({ queryKey: [ORDERS_KEY, id] });
      toast.success("অর্ডার আপডেট হয়েছে");
    },
    onError: (e) => toast.error(getApiError(e)),
  });
}

export function useChangeOrderStatus() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, status, note }: { id: string; status: OrderStatus; note?: string }) =>
      changeStatus(id, status, note),
    onSuccess: (_data, { id }) => {
      qc.invalidateQueries({ queryKey: [ORDERS_KEY, id] });
      qc.invalidateQueries({ queryKey: [ORDERS_KEY] });
      toast.success("স্ট্যাটাস আপডেট হয়েছে");
    },
    onError: (e) => toast.error(getApiError(e)),
  });
}

export function useRecordPayment() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, amount, method, reference }: { id: string; amount: string; method: PaymentMethod; reference?: string }) =>
      recordPayment(id, amount, method, reference),
    onSuccess: (_data, { id }) => {
      qc.invalidateQueries({ queryKey: [ORDERS_KEY, id] });
      qc.invalidateQueries({ queryKey: [ORDERS_KEY] });
      toast.success("পেমেন্ট রেকর্ড হয়েছে");
    },
    onError: (e) => toast.error(getApiError(e)),
  });
}

export function useCancelOrder() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: cancelOrder,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: [ORDERS_KEY] });
      toast.success("অর্ডার বাতিল করা হয়েছে");
    },
    onError: (e) => toast.error(getApiError(e)),
  });
}
