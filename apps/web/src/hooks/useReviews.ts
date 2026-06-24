import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import api from "@/lib/api-client";
import { getApiError } from "@/lib/utils";

const REV_KEY = "reviews";

export interface ReviewOut {
  id: string;
  order_id: string;
  order_number: string | null;
  customer_id: string | null;
  reviewer_name: string | null;
  rating: number;
  comment: string | null;
  created_at: string;
}

export interface ReviewStatsOut {
  avg_rating: number;
  total_reviews: number;
  five_star: number;
  four_star: number;
  three_star: number;
  two_star: number;
  one_star: number;
}

export interface ReviewCreate {
  order_id: string;
  rating: number;
  comment?: string;
  reviewer_name?: string;
}

async function fetchReviews(limit = 50) {
  const { data } = await api.get<{ data: ReviewOut[] }>("/reviews", { params: { limit } });
  return data.data;
}

async function fetchReviewStats() {
  const { data } = await api.get<{ data: ReviewStatsOut }>("/reviews/stats");
  return data.data;
}

async function submitReview(body: ReviewCreate) {
  const { data } = await api.post<{ data: ReviewOut }>("/reviews", body);
  return data.data;
}

export function useReviews(limit = 50) {
  return useQuery({
    queryKey: [REV_KEY, "list", limit],
    queryFn: () => fetchReviews(limit),
  });
}

export function useReviewStats() {
  return useQuery({
    queryKey: [REV_KEY, "stats"],
    queryFn: fetchReviewStats,
  });
}

export function useSubmitReview() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: submitReview,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: [REV_KEY] });
      toast.success("রিভিউ সফলভাবে জমা হয়েছে");
    },
    onError: (e) => toast.error(getApiError(e)),
  });
}
