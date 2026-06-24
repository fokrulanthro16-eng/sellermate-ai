"use client";

import { useOrders } from "@/hooks/useOrders";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { OrderStatusBadge, PaymentStatusBadge } from "@/components/orders/StatusBadge";
import { formatCurrency, formatDate } from "@/lib/utils";
import Link from "next/link";

interface CustomerOrderHistoryProps {
  customerId: string;
}

export default function CustomerOrderHistory({ customerId }: CustomerOrderHistoryProps) {
  const { data, isLoading } = useOrders({ limit: 20 });
  const orders = (data?.items || []).filter((o) => o.customer_id === customerId);

  return (
    <Card>
      <CardHeader><CardTitle className="text-base">অর্ডার ইতিহাস</CardTitle></CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="space-y-2">
            {[1, 2, 3].map((i) => <Skeleton key={i} className="h-12 w-full" />)}
          </div>
        ) : orders.length === 0 ? (
          <p className="text-sm text-muted-foreground text-center py-4">কোনো অর্ডার নেই</p>
        ) : (
          <div className="space-y-3">
            {orders.map((order) => (
              <Link key={order.id} href={`/orders/${order.id}`}>
                <div className="flex items-center justify-between p-3 rounded-lg border hover:bg-accent transition-colors cursor-pointer">
                  <div>
                    <p className="text-sm font-medium">#{order.id.slice(-8).toUpperCase()}</p>
                    <div className="flex gap-2 mt-1">
                      <OrderStatusBadge status={order.status} />
                      <PaymentStatusBadge status={order.payment_status} />
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-bold">{formatCurrency(order.total_amount)}</p>
                    <p className="text-xs text-muted-foreground">{formatDate(order.created_at)}</p>
                  </div>
                </div>
              </Link>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
