import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api-client";

export interface BackgroundJob {
  id: string;
  job_type: string;
  status: "queued" | "running" | "done" | "failed";
  payload?: Record<string, unknown>;
  result?: Record<string, unknown>;
  error?: string | null;
  retry_count: number;
  scheduled_at?: string | null;
  started_at?: string | null;
  completed_at?: string | null;
  created_at: string;
}

export interface WebhookEvent {
  id: string;
  provider: string;
  event_type: string;
  status: "pending" | "processed" | "failed";
  retry_count: number;
  error_message?: string | null;
  received_at: string;
  processed_at?: string | null;
}

interface JobsPage {
  items: BackgroundJob[];
  total: number;
}

interface WebhookEventsPage {
  items: WebhookEvent[];
  total: number;
}

export function useJobs(limit = 50, offset = 0) {
  return useQuery<JobsPage>({
    queryKey: ["jobs", limit, offset],
    queryFn: async () => {
      const { data } = await api.get("/jobs", { params: { limit, offset } });
      return data.data;
    },
  });
}

export function useEnqueueJob() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (body: { job_type: string; payload?: Record<string, unknown> }) => {
      const { data } = await api.post("/jobs/enqueue", body);
      return data.data as BackgroundJob;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["jobs"] }),
  });
}

export function useRetryJob() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (jobId: string) => {
      const { data } = await api.post(`/jobs/${jobId}/retry`);
      return data.data as BackgroundJob;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["jobs"] }),
  });
}

export function useWebhookEvents(limit = 50, offset = 0) {
  return useQuery<WebhookEventsPage>({
    queryKey: ["webhook-events", limit, offset],
    queryFn: async () => {
      const { data } = await api.get("/webhooks/events", { params: { limit, offset } });
      return data.data;
    },
    refetchInterval: 30_000,
  });
}

export function useRetryWebhookEvent() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (eventId: string) => {
      const { data } = await api.post(`/webhooks/events/${eventId}/retry`);
      return data.data as WebhookEvent;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["webhook-events"] }),
  });
}
