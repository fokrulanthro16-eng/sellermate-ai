"use client";

import { useState } from "react";
import { Star, MessageSquare, TrendingUp, Plus } from "lucide-react";
import { format, parseISO } from "date-fns";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Skeleton } from "@/components/ui/skeleton";
import { useReviews, useReviewStats, useSubmitReview } from "@/hooks/useReviews";
import { useLang } from "@/contexts/LangContext";
import { cn } from "@/lib/utils";

function StarRow({ rating, interactive = false, onSelect }: { rating: number; interactive?: boolean; onSelect?: (n: number) => void }) {
  const [hover, setHover] = useState(0);
  return (
    <div className="flex gap-0.5">
      {[1, 2, 3, 4, 5].map((n) => (
        <Star
          key={n}
          className={cn(
            "h-4 w-4 transition-colors",
            (interactive ? (hover || rating) >= n : rating >= n)
              ? "fill-amber-400 text-amber-400"
              : "text-muted-foreground/30",
            interactive && "cursor-pointer"
          )}
          onMouseEnter={() => interactive && setHover(n)}
          onMouseLeave={() => interactive && setHover(0)}
          onClick={() => interactive && onSelect?.(n)}
        />
      ))}
    </div>
  );
}

function AddReviewDialog() {
  const [open, setOpen] = useState(false);
  const [orderId, setOrderId] = useState("");
  const [rating, setRating] = useState(0);
  const [comment, setComment] = useState("");
  const [reviewerName, setReviewerName] = useState("");
  const submit = useSubmitReview();
  const { lang } = useLang();
  const l = (bn: string, en: string) => lang === "bn" ? bn : en;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!orderId || rating === 0) return;
    await submit.mutateAsync({ order_id: orderId, rating, comment: comment || undefined, reviewer_name: reviewerName || undefined });
    setOpen(false);
    setOrderId(""); setRating(0); setComment(""); setReviewerName("");
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button size="sm" className="gap-1.5 h-8 text-xs">
          <Plus className="h-3.5 w-3.5" />{l("রিভিউ যোগ করুন", "Add Review")}
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{l("গ্রাহকের রিভিউ রেকর্ড করুন", "Record Customer Review")}</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4 mt-2">
          <p className="text-xs text-amber-700 bg-amber-50 border border-amber-200 rounded p-2">
            {l("শুধুমাত্র ডেলিভার করা অর্ডারের রিভিউ নেওয়া যাবে।", "Reviews are only allowed for delivered orders.")}
          </p>
          <div className="space-y-1.5">
            <Label>{l("অর্ডার আইডি", "Order ID")}</Label>
            <Input placeholder="Order UUID..." value={orderId} onChange={(e) => setOrderId(e.target.value)} required />
          </div>
          <div className="space-y-1.5">
            <Label>{l("রেটিং", "Rating")}</Label>
            <StarRow rating={rating} interactive onSelect={setRating} />
          </div>
          <div className="space-y-1.5">
            <Label>{l("গ্রাহকের নাম (ঐচ্ছিক)", "Customer Name (optional)")}</Label>
            <Input placeholder={l("নাম...", "Name...")} value={reviewerName} onChange={(e) => setReviewerName(e.target.value)} />
          </div>
          <div className="space-y-1.5">
            <Label>{l("মন্তব্য (ঐচ্ছিক)", "Comment (optional)")}</Label>
            <textarea
              className="w-full border rounded p-2 text-sm min-h-[80px] bg-background"
              placeholder={l("গ্রাহকের মতামত লিখুন...", "Write customer feedback...")}
              value={comment}
              onChange={(e) => setComment(e.target.value)}
            />
          </div>
          <Button type="submit" className="w-full" disabled={submit.isPending || rating === 0 || !orderId}>
            {l("রিভিউ জমা দিন", "Submit Review")}
          </Button>
        </form>
      </DialogContent>
    </Dialog>
  );
}

export default function ReviewsPage() {
  const { lang } = useLang();
  const l = (bn: string, en: string) => lang === "bn" ? bn : en;
  const { data: reviews, isLoading } = useReviews();
  const { data: stats, isLoading: statsLoading } = useReviewStats();

  return (
    <div className="space-y-4 max-w-[1200px]">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold">{l("যাচাইকৃত রিভিউ", "Verified Reviews")}</h1>
          <p className="text-sm text-muted-foreground">
            {l("শুধুমাত্র ডেলিভার করা অর্ডার থেকে রিভিউ সংগ্রহ করুন", "Collect reviews only from delivered orders")}
          </p>
        </div>
        <AddReviewDialog />
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {statsLoading ? (
          Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-20" />)
        ) : (
          <>
            <div className="admin-card p-4 border-l-4 border-l-amber-500 text-center">
              <p className="text-3xl font-bold text-amber-600">{stats?.avg_rating?.toFixed(1) ?? "—"}</p>
              <p className="text-xs text-muted-foreground mt-1">{l("গড় রেটিং", "Avg Rating")}</p>
              <StarRow rating={Math.round(stats?.avg_rating ?? 0)} />
            </div>
            <div className="admin-card p-4 border-l-4 border-l-emerald-500 text-center">
              <p className="text-3xl font-bold text-emerald-600">{stats?.total_reviews ?? 0}</p>
              <p className="text-xs text-muted-foreground mt-1">{l("মোট রিভিউ", "Total Reviews")}</p>
            </div>
            <div className="admin-card p-4 col-span-2">
              <p className="text-xs font-semibold mb-2 text-muted-foreground">{l("রেটিং বিভাজন", "Rating Breakdown")}</p>
              {[5,4,3,2,1].map((n) => {
                const count = stats ? (
                  n === 5 ? stats.five_star :
                  n === 4 ? stats.four_star :
                  n === 3 ? stats.three_star :
                  n === 2 ? stats.two_star : stats.one_star
                ) : 0;
                const pct = stats?.total_reviews ? Math.round((count / stats.total_reviews) * 100) : 0;
                return (
                  <div key={n} className="flex items-center gap-2 text-xs mb-1">
                    <span className="w-3 text-right text-muted-foreground">{n}</span>
                    <Star className="h-3 w-3 fill-amber-400 text-amber-400 shrink-0" />
                    <div className="flex-1 h-1.5 rounded-full bg-muted overflow-hidden">
                      <div className="h-full bg-amber-400 rounded-full" style={{ width: `${pct}%` }} />
                    </div>
                    <span className="w-5 text-right text-muted-foreground">{count}</span>
                  </div>
                );
              })}
            </div>
          </>
        )}
      </div>

      {/* Reviews list */}
      <div className="admin-card overflow-hidden">
        <div className="flex items-center gap-2 px-4 py-2.5 border-b border-border">
          <MessageSquare className="h-4 w-4 text-muted-foreground" />
          <p className="text-sm font-semibold">{l("রিভিউ তালিকা", "Review List")}</p>
          <span className="ml-auto text-xs text-muted-foreground">{reviews?.length ?? 0} {l("টি", "reviews")}</span>
        </div>

        {isLoading ? (
          <div className="p-4 space-y-3">
            {Array.from({ length: 3 }).map((_, i) => <Skeleton key={i} className="h-20" />)}
          </div>
        ) : !reviews?.length ? (
          <div className="py-16 text-center text-muted-foreground">
            <TrendingUp className="h-10 w-10 mx-auto mb-3 opacity-20" />
            <p className="text-sm font-medium">{l("এখনো কোনো রিভিউ নেই", "No reviews yet")}</p>
            <p className="text-xs mt-1">{l("ডেলিভার করা অর্ডারের রিভিউ নিন", "Collect reviews from delivered orders")}</p>
          </div>
        ) : (
          <div className="divide-y divide-border">
            {reviews.map((r) => (
              <div key={r.id} className="px-4 py-3 hover:bg-muted/30">
                <div className="flex items-start justify-between gap-3">
                  <div className="flex items-center gap-2">
                    <div className="h-7 w-7 rounded-full bg-primary/10 flex items-center justify-center text-xs font-bold text-primary">
                      {(r.reviewer_name ?? "?")[0]?.toUpperCase()}
                    </div>
                    <div>
                      <p className="text-sm font-medium">{r.reviewer_name ?? l("অজ্ঞাত গ্রাহক", "Unknown customer")}</p>
                      <p className="text-xs text-muted-foreground">
                        {l("অর্ডার", "Order")} #{r.order_number ?? r.order_id.slice(-6).toUpperCase()}
                      </p>
                    </div>
                  </div>
                  <div className="text-right shrink-0">
                    <StarRow rating={r.rating} />
                    <p className="text-[10px] text-muted-foreground mt-0.5">
                      {r.created_at ? format(parseISO(r.created_at), "dd MMM yyyy") : ""}
                    </p>
                  </div>
                </div>
                {r.comment && (
                  <p className="text-xs text-muted-foreground mt-2 ml-9 leading-relaxed">{r.comment}</p>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
