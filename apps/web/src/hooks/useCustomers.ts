import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import api from "@/lib/api-client";
import { getApiError } from "@/lib/utils";
import type { Customer, CreateCustomerPayload, ApiResponse, PaginatedData } from "@/types";

const CUST_KEY = "customers";

async function fetchCustomers(params: { page?: number; limit?: number; search?: string; district?: string; source?: string; tags?: string }) {
  const { data } = await api.get("/customers", { params });
  const items = Array.isArray(data.data) ? data.data : [];
  const meta = data.meta ?? {};
  return { items, total: meta.total ?? 0, page: meta.page ?? 1, limit: meta.limit ?? 20, pages: meta.total_pages ?? 1 } as PaginatedData<Customer>;
}

async function fetchCustomer(id: string) {
  const { data } = await api.get<ApiResponse<Customer>>(`/customers/${id}`);
  return data.data;
}

async function createCustomer(payload: CreateCustomerPayload) {
  const { data } = await api.post<ApiResponse<Customer>>("/customers", payload);
  return data.data;
}

async function updateCustomer(id: string, payload: Partial<CreateCustomerPayload>) {
  const { data } = await api.patch<ApiResponse<Customer>>(`/customers/${id}`, payload);
  return data.data;
}

async function deleteCustomer(id: string) {
  await api.delete(`/customers/${id}`);
}

async function addTag(customerId: string, tag: string) {
  const { data } = await api.post<ApiResponse<Customer>>(`/customers/${customerId}/tags/${tag}`);
  return data.data;
}

async function removeTag(customerId: string, tag: string) {
  const { data } = await api.delete<ApiResponse<Customer>>(`/customers/${customerId}/tags/${tag}`);
  return data.data;
}

export function useCustomers(params: { page?: number; limit?: number; search?: string; district?: string; source?: string; tags?: string } = {}) {
  return useQuery({
    queryKey: [CUST_KEY, params],
    queryFn: () => fetchCustomers(params),
  });
}

export function useCustomer(id: string) {
  return useQuery({
    queryKey: [CUST_KEY, id],
    queryFn: () => fetchCustomer(id),
    enabled: !!id,
  });
}

export function useCreateCustomer() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: createCustomer,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: [CUST_KEY] });
      toast.success("গ্রাহক যোগ হয়েছে");
    },
    onError: (e) => toast.error(getApiError(e)),
  });
}

export function useUpdateCustomer() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, ...payload }: { id: string } & Partial<CreateCustomerPayload>) =>
      updateCustomer(id, payload),
    onSuccess: (_data, { id }) => {
      qc.invalidateQueries({ queryKey: [CUST_KEY, id] });
      qc.invalidateQueries({ queryKey: [CUST_KEY] });
      toast.success("গ্রাহক আপডেট হয়েছে");
    },
    onError: (e) => toast.error(getApiError(e)),
  });
}

export function useDeleteCustomer() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: deleteCustomer,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: [CUST_KEY] });
      toast.success("গ্রাহক মুছে ফেলা হয়েছে");
    },
    onError: (e) => toast.error(getApiError(e)),
  });
}

export function useAddTag() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ customerId, tag }: { customerId: string; tag: string }) => addTag(customerId, tag),
    onSuccess: (_data, { customerId }) => {
      qc.invalidateQueries({ queryKey: [CUST_KEY, customerId] });
      toast.success("ট্যাগ যোগ হয়েছে");
    },
    onError: (e) => toast.error(getApiError(e)),
  });
}

export function useRemoveTag() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ customerId, tag }: { customerId: string; tag: string }) => removeTag(customerId, tag),
    onSuccess: (_data, { customerId }) => {
      qc.invalidateQueries({ queryKey: [CUST_KEY, customerId] });
      toast.success("ট্যাগ সরানো হয়েছে");
    },
    onError: (e) => toast.error(getApiError(e)),
  });
}
