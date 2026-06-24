import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import api from "@/lib/api-client";
import { getApiError } from "@/lib/utils";
import type { Product, CreateProductPayload, ApiResponse, PaginatedData, ProductVariant } from "@/types";

const PRODUCTS_KEY = "products";

async function fetchProducts(params: { page?: number; limit?: number; search?: string; is_active?: boolean; category?: string }) {
  const { data } = await api.get("/products", { params });
  const items = Array.isArray(data.data) ? data.data : [];
  const meta = data.meta ?? {};
  return { items, total: meta.total ?? 0, page: meta.page ?? 1, limit: meta.limit ?? 20, pages: meta.total_pages ?? 1 } as PaginatedData<Product>;
}

async function fetchProduct(id: string) {
  const { data } = await api.get<ApiResponse<Product>>(`/products/${id}`);
  return data.data;
}

async function createProduct(payload: CreateProductPayload) {
  const { data } = await api.post<ApiResponse<Product>>("/products", payload);
  return data.data;
}

async function updateProduct(id: string, payload: Partial<CreateProductPayload>) {
  const { data } = await api.patch<ApiResponse<Product>>(`/products/${id}`, payload);
  return data.data;
}

async function deleteProduct(id: string) {
  await api.delete(`/products/${id}`);
}

async function addVariant(productId: string, variant: Omit<ProductVariant, "id" | "product_id" | "is_active" | "created_at">) {
  const { data } = await api.post<ApiResponse<ProductVariant>>(`/products/${productId}/variants`, variant);
  return data.data;
}

async function updateVariant(productId: string, variantId: string, payload: Partial<ProductVariant>) {
  const { data } = await api.patch<ApiResponse<ProductVariant>>(
    `/products/${productId}/variants/${variantId}`,
    payload
  );
  return data.data;
}

async function deleteVariant(productId: string, variantId: string) {
  await api.delete(`/products/${productId}/variants/${variantId}`);
}

export function useProducts(params: { page?: number; limit?: number; search?: string; is_active?: boolean; category?: string } = {}) {
  return useQuery({
    queryKey: [PRODUCTS_KEY, params],
    queryFn: () => fetchProducts(params),
  });
}

export function useProduct(id: string) {
  return useQuery({
    queryKey: [PRODUCTS_KEY, id],
    queryFn: () => fetchProduct(id),
    enabled: !!id,
  });
}

export function useCreateProduct() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: createProduct,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: [PRODUCTS_KEY] });
      toast.success("পণ্য তৈরি হয়েছে");
    },
    onError: (e) => toast.error(getApiError(e)),
  });
}

export function useUpdateProduct() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, ...payload }: { id: string } & Partial<CreateProductPayload>) =>
      updateProduct(id, payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: [PRODUCTS_KEY] });
      toast.success("পণ্য আপডেট হয়েছে");
    },
    onError: (e) => toast.error(getApiError(e)),
  });
}

export function useDeleteProduct() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: deleteProduct,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: [PRODUCTS_KEY] });
      toast.success("পণ্য মুছে ফেলা হয়েছে");
    },
    onError: (e) => toast.error(getApiError(e)),
  });
}

export function useAddVariant() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ productId, ...variant }: { productId: string } & Omit<ProductVariant, "id" | "product_id" | "is_active" | "created_at">) =>
      addVariant(productId, variant),
    onSuccess: (_data, { productId }) => {
      qc.invalidateQueries({ queryKey: [PRODUCTS_KEY, productId] });
      toast.success("ভ্যারিয়েন্ট যোগ হয়েছে");
    },
    onError: (e) => toast.error(getApiError(e)),
  });
}

export function useUpdateVariant() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ productId, variantId, ...payload }: { productId: string; variantId: string } & Partial<ProductVariant>) =>
      updateVariant(productId, variantId, payload),
    onSuccess: (_data, { productId }) => {
      qc.invalidateQueries({ queryKey: [PRODUCTS_KEY, productId] });
      toast.success("ভ্যারিয়েন্ট আপডেট হয়েছে");
    },
    onError: (e) => toast.error(getApiError(e)),
  });
}

export function useDeleteVariant() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ productId, variantId }: { productId: string; variantId: string }) =>
      deleteVariant(productId, variantId),
    onSuccess: (_data, { productId }) => {
      qc.invalidateQueries({ queryKey: [PRODUCTS_KEY, productId] });
      toast.success("ভ্যারিয়েন্ট মুছে ফেলা হয়েছে");
    },
    onError: (e) => toast.error(getApiError(e)),
  });
}
