import { Badge } from "@/components/ui/badge";
import type { OrderStatus, PaymentStatus } from "@/types";

const STATUS_CONFIG: Record<OrderStatus, { label: string; variant: "default" | "secondary" | "destructive" | "outline" | "success" | "warning" | "info" }> = {
  PENDING: { label: "মুলতুবি", variant: "warning" },
  CONFIRMED: { label: "নিশ্চিত", variant: "info" },
  PROCESSING: { label: "প্রক্রিয়াধীন", variant: "secondary" },
  SHIPPED: { label: "শিপড", variant: "info" },
  DELIVERED: { label: "ডেলিভারড", variant: "success" },
  CANCELLED: { label: "বাতিল", variant: "destructive" },
  RETURNED: { label: "ফেরত", variant: "warning" },
};

const PAYMENT_CONFIG: Record<PaymentStatus, { label: string; variant: "default" | "secondary" | "destructive" | "outline" | "success" | "warning" | "info" }> = {
  UNPAID: { label: "অপরিশোধিত", variant: "destructive" },
  PARTIAL: { label: "আংশিক", variant: "warning" },
  PAID: { label: "পরিশোধিত", variant: "success" },
};

export function OrderStatusBadge({ status }: { status: OrderStatus }) {
  const config = STATUS_CONFIG[status] || { label: status, variant: "outline" as const };
  return <Badge variant={config.variant}>{config.label}</Badge>;
}

export function PaymentStatusBadge({ status }: { status: PaymentStatus }) {
  const config = PAYMENT_CONFIG[status] || { label: status, variant: "outline" as const };
  return <Badge variant={config.variant}>{config.label}</Badge>;
}
