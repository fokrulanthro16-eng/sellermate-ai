import { CheckCircle2, Circle } from "lucide-react";
import { formatDateTime } from "@/lib/utils";
import type { OrderStatusHistory } from "@/types";

interface OrderTimelineProps {
  history?: OrderStatusHistory[];
}

const STATUS_LABELS: Record<string, string> = {
  PENDING: "অর্ডার গৃহীত",
  CONFIRMED: "অর্ডার নিশ্চিত",
  PROCESSING: "প্রক্রিয়াকরণ",
  SHIPPED: "শিপমেন্ট",
  DELIVERED: "ডেলিভারি সম্পন্ন",
  CANCELLED: "বাতিল",
  RETURNED: "ফেরত",
};

export default function OrderTimeline({ history }: OrderTimelineProps) {
  if (!history || history.length === 0) {
    return <p className="text-sm text-muted-foreground">কোনো ইতিহাস নেই</p>;
  }

  return (
    <div className="space-y-3">
      {history.map((item, i) => (
        <div key={item.id} className="flex gap-3">
          <div className="flex flex-col items-center">
            {i === 0 ? (
              <CheckCircle2 className="h-5 w-5 text-primary mt-0.5 shrink-0" />
            ) : (
              <Circle className="h-5 w-5 text-muted-foreground mt-0.5 shrink-0" />
            )}
            {i < history.length - 1 && (
              <div className="w-px flex-1 bg-border mt-1" />
            )}
          </div>
          <div className="pb-4">
            <p className="text-sm font-medium">{STATUS_LABELS[item.status] || item.status}</p>
            {item.note && <p className="text-xs text-muted-foreground mt-0.5">{item.note}</p>}
            <p className="text-xs text-muted-foreground mt-0.5">{formatDateTime(item.created_at)}</p>
          </div>
        </div>
      ))}
    </div>
  );
}
