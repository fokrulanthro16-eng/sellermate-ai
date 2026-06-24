import Link from "next/link";
import { Card, CardContent } from "@/components/ui/card";
import { OrderStatusBadge, PaymentStatusBadge } from "@/components/orders/StatusBadge";
import { formatCurrency, formatDate, cn } from "@/lib/utils";
import { MapPin, Hash } from "lucide-react";
import type { Order } from "@/types";

const CHANNEL_STYLE: Record<string, { label: string; bg: string; text: string }> = {
  FACEBOOK:  { label: "FB",  bg: "bg-blue-100 dark:bg-blue-900",   text: "text-blue-700 dark:text-blue-300" },
  WHATSAPP:  { label: "WA",  bg: "bg-green-100 dark:bg-green-900",  text: "text-green-700 dark:text-green-300" },
  INSTAGRAM: { label: "IG",  bg: "bg-pink-100 dark:bg-pink-900",    text: "text-pink-700 dark:text-pink-300" },
  WEBSITE:   { label: "WEB", bg: "bg-violet-100 dark:bg-violet-900",text: "text-violet-700 dark:text-violet-300" },
  MANUAL:    { label: "M",   bg: "bg-gray-100 dark:bg-gray-800",    text: "text-gray-600 dark:text-gray-300" },
};

interface OrderCardProps {
  order: Order;
}

export default function OrderCard({ order }: OrderCardProps) {
  const ch = CHANNEL_STYLE[order.channel] ?? CHANNEL_STYLE.MANUAL;
  const orderRef = order.order_number ?? `#${order.id.slice(-8).toUpperCase()}`;

  return (
    <Link href={`/orders/${order.id}`}>
      <Card className="hover:shadow-md hover:border-primary/30 transition-all cursor-pointer group">
        <CardContent className="p-4">
          <div className="flex items-center gap-3">
            {/* Channel badge */}
            <div className={cn(
              "h-10 w-10 rounded-xl flex items-center justify-center text-xs font-bold shrink-0",
              ch.bg, ch.text
            )}>
              {ch.label}
            </div>

            {/* Main info */}
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 flex-wrap">
                <span className="text-sm font-semibold font-mono">{orderRef}</span>
                <OrderStatusBadge status={order.status} />
                <PaymentStatusBadge status={order.payment_status} />
              </div>
              <div className="flex items-center gap-3 mt-1 text-xs text-muted-foreground flex-wrap">
                <span className="font-medium text-foreground/80">{order.customer_name || "গ্রাহক"}</span>
                {order.delivery_district && (
                  <span className="flex items-center gap-0.5">
                    <MapPin className="h-3 w-3" />
                    {order.delivery_district}
                  </span>
                )}
                <span>{formatDate(order.created_at)}</span>
              </div>
            </div>

            {/* Amount */}
            <div className="text-right shrink-0">
              <p className="text-sm font-bold text-foreground">{formatCurrency(order.total_amount)}</p>
              <p className="text-xs text-muted-foreground">{order.payment_method}</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </Link>
  );
}
