import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import api from "@/lib/api-client";
import { getApiError } from "@/lib/utils";
import type { Conversation, Message, ApiResponse, PaginatedData } from "@/types";

const CONV_KEY = "conversations";

async function fetchConversations() {
  const { data } = await api.get("/assistant/conversations");
  const items = Array.isArray(data.data) ? data.data : [];
  const meta = data.meta ?? {};
  return { items, total: meta.total ?? items.length, page: meta.page ?? 1, limit: meta.limit ?? 50, pages: meta.total_pages ?? 1 } as PaginatedData<Conversation>;
}

async function fetchMessages(conversationId: string) {
  const { data } = await api.get(`/assistant/conversations/${conversationId}/messages`);
  const items = Array.isArray(data.data) ? data.data : [];
  const meta = data.meta ?? {};
  return { items, total: meta.total ?? items.length, page: meta.page ?? 1, limit: meta.limit ?? 100, pages: meta.total_pages ?? 1 } as PaginatedData<Message>;
}

async function createConversation(title?: string) {
  const { data } = await api.post<ApiResponse<Conversation>>("/assistant/conversations", { title });
  return data.data;
}

async function deleteConversation(id: string) {
  await api.delete(`/assistant/conversations/${id}`);
}

export function useConversations() {
  return useQuery({
    queryKey: [CONV_KEY],
    queryFn: fetchConversations,
  });
}

export function useMessages(conversationId: string) {
  return useQuery({
    queryKey: [CONV_KEY, conversationId, "messages"],
    queryFn: () => fetchMessages(conversationId),
    enabled: !!conversationId,
  });
}

export function useCreateConversation() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: createConversation,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: [CONV_KEY] });
    },
    onError: (e) => toast.error(getApiError(e)),
  });
}

export function useDeleteConversation() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: deleteConversation,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: [CONV_KEY] });
      toast.success("কথোপকথন মুছে ফেলা হয়েছে");
    },
    onError: (e) => toast.error(getApiError(e)),
  });
}
