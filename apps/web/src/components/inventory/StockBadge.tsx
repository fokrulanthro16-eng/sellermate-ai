import { Badge } from "@/components/ui/badge";

interface StockBadgeProps {
  quantity: number;
  threshold: number;
}

export default function StockBadge({ quantity, threshold }: StockBadgeProps) {
  if (quantity === 0) return <Badge variant="destructive">স্টক নেই</Badge>;
  if (quantity <= threshold) return <Badge variant="warning">কম স্টক</Badge>;
  return <Badge variant="success">পর্যাপ্ত</Badge>;
}
