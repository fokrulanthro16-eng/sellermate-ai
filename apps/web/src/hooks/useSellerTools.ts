import { useMutation, useQuery } from "@tanstack/react-query";
import { toast } from "sonner";
import api from "@/lib/api-client";
import { getApiError } from "@/lib/utils";

export interface ToolProduct {
  id: string;
  name: string;
  name_bangla: string | null;
  category: string;
  base_price: string;
  sale_price: string | null;
}

export interface GenerateRequest {
  tool: string;
  lang: string;
  tone: string;
  product_id?: string;
  order_id?: string;
  extra_context?: string;
}

export interface GenerateOut {
  text: string;
  tool: string;
  lang: string;
  source: string;
  context_used: Record<string, unknown>;
}

async function fetchToolProducts() {
  const { data } = await api.get<{ data: ToolProduct[] }>("/ai/seller-tools/products");
  return data.data;
}

async function generateContent(req: GenerateRequest): Promise<GenerateOut> {
  const { data } = await api.post<{ data: GenerateOut }>("/ai/seller-tools/generate", req);
  return data.data;
}

export function useToolProducts() {
  return useQuery({
    queryKey: ["seller-tools", "products"],
    queryFn: fetchToolProducts,
  });
}

export function useGenerateContent() {
  return useMutation({
    mutationFn: generateContent,
    onError: (e) => toast.error(getApiError(e)),
  });
}
