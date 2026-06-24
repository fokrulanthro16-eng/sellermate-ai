"use client";

import { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { ArrowLeft, CheckCircle2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { OrderStatusBadge, PaymentStatusBadge } from "@/components/orders/StatusBadge";
import OrderTimeline from "@/components/orders/OrderTimeline";
import { useOrder, useChangeOrderStatus, useRecordPayment } from "@/hooks/useOrders";
import { formatCurrency, formatDateTime } from "@/lib/utils";
import type { OrderStatus, PaymentMethod } from "@/types";

const NEXT_STATUSES: Partial<Record<OrderStatus, { value: OrderStatus; label: string }[]>> = {
  PENDING: [{ value: "CONFIRMED", label: "নিশ্চিত করুন" }, { value: "CANCELLED", label: "বাতিল করুন" }],
  CONFIRMED: [{ value: "PROCESSING", label: "প্রক্রিয়া শুরু" }, { value: "CANCELLED", label: "বাতিল করুন" }],
  PROCESSING: [{ value: "SHIPPED", label: "পাঠানো হয়েছে" }],
  SHIPPED: [{ value: "DELIVERED", label: "বিতরণ সম্পন্ন" }, { value: "RETURNED", label: "ফেরত এসেছে" }],
};

export default function OrderDetailPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const { data: order, isLoading } = useOrder(id);
  const changeStatus = useChangeOrderStatus();
  const recordPayment = useRecordPayment();
  const [payAmount, setPayAmount] = useState("");
  const [payMethod, setPayMethod] = useState("COD");

  if (isLoading) return (
    <div className="max-w-3xl mx-auto space-y-4">
      <Skeleton className="h-8 w-48" /><Skeleton className="h-48 w-full" /><Skeleton className="h-32 w-full" />
    </div>
  );
  if (!order) return <p className="text-center text-muted-foreground py-12">অর্ডার পাওয়া যায়নি</p>;

  const availableStatuses = NEXT_STATUSES[order.status] || [];
  const items = order.items || [];
  const paidAmount = parseFloat(order.paid_amount ?? "0");
  const totalAmount = parseFloat(order.total_amount);
  const remaining = totalAmount - paidAmount;

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div className="flex items-center gap-3 flex-wrap">
        <Button variant="ghost" size="icon" onClick={() => router.back()}><ArrowLeft className="h-4 w-4" /></Button>
        <h1 className="text-2xl font-bold">অর্ডার #{order.id.slice(-8).toUpperCase()}</h1>
        <OrderStatusBadge status={order.status} />
        <PaymentStatusBadge status={order.payment_status} />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card>
          <CardHeader><CardTitle className="text-base">গ্রাহকের তথ্য</CardTitle></CardHeader>
          <CardContent className="text-sm space-y-1">
            <p className="font-medium">{order.customer_name || "অজ্ঞাত"}</p>
            {order.customer_phone && <p className="text-muted-foreground">{order.customer_phone}</p>}
            {order.delivery_address && <p className="text-muted-foreground">{order.delivery_address}</p>}
          </CardContent>
        </Card>
        <Card>
          <CardHeader><CardTitle className="text-base">অর্ডারের তথ্য</CardTitle></CardHeader>
          <CardContent className="text-sm space-y-1">
            <div className="flex justify-between"><span className="text-muted-foreground">চ্যানেল</span><span>{order.channel}</span></div>
            <div className="flex justify-between"><span className="text-muted-foreground">তারিখ</span><span>{formatDateTime(order.created_at)}</span></div>
            <div className="flex justify-between"><span className="text-muted-foreground">পেমেন্ট</span><span>{order.payment_method}</span></div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader><CardTitle className="text-base">পণ্য তালিকা</CardTitle></CardHeader>
        <CardContent>
          <div className="space-y-2">
            {items.map((item) => (
              <div key={item.id} className="flex justify-between items-center py-2 border-b last:border-0 text-sm">
                <div>
                  <p className="font-medium">{item.product_name}</p>
                  <p className="text-muted-foreground">{item.variant_name} × {item.quantity}</p>
                </div>
                <p className="font-bold">{formatCurrency(String(parseFloat(item.unit_price) * item.quantity))}</p>
              </div>
            ))}
          </div>
          <div className="mt-4 space-y-1 text-sm border-t pt-3">
            {parseFloat(order.discount_amount) > 0 && <div className="flex justify-between text-muted-foreground"><span>ছাড়</span><span>-{formatCurrency(order.discount_amount)}</span></div>}
            {parseFloat(order.shipping_cost) > 0 && <div className="flex justify-between text-muted-foreground"><span>শিপিং</span><span>{formatCurrency(order.shipping_cost)}</span></div>}
            <div className="flex justify-between font-bold text-base pt-1"><span>মোট</span><span>{formatCurrency(order.total_amount)}</span></div>
            <div className="flex justify-between text-green-600"><span>পরিশোধিত</span><span>{formatCurrency(order.paid_amount ?? "0")}</span></div>
            {remaining > 0 && (
              <div className="flex justify-between text-destructive font-semibold"><span>বাকি</span><span>{formatCurrency(String(remaining))}</span></div>
            )}
          </div>
        </CardContent>
      </Card>

      {availableStatuses.length > 0 && (
        <Card>
          <CardHeader><CardTitle className="text-base">অবস্থা পরিবর্তন</CardTitle></CardHeader>
          <CardContent className="flex gap-2 flex-wrap">
            {availableStatuses.map((s) => (
              <Button key={s.value} variant="outline" size="sm" disabled={changeStatus.isPending}
                onClick={() => changeStatus.mutate({ id, status: s.value })}>
                <CheckCircle2 className="h-4 w-4 mr-1" /> {s.label}
              </Button>
            ))}
          </CardContent>
        </Card>
      )}

      {order.payment_status !== "PAID" && (
        <Card>
          <CardHeader><CardTitle className="text-base">পেমেন্ট রেকর্ড</CardTitle></CardHeader>
          <CardContent>
            <div className="flex gap-3 items-end flex-wrap">
              <div className="flex-1 min-w-[120px] space-y-1">
                <Label>পরিমাণ (টাকা)</Label>
                <Input type="number" value={payAmount} onChange={(e) => setPayAmount(e.target.value)} placeholder="0" />
              </div>
              <div className="w-36 space-y-1">
                <Label>পদ্ধতি</Label>
                <Select value={payMethod} onValueChange={setPayMethod}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    {["COD","BKASH","NAGAD","ROCKET","BANK","CARD"].map((m) => <SelectItem key={m} value={m}>{m}</SelectItem>)}
                  </SelectContent>
                </Select>
              </div>
              <Button onClick={() => recordPayment.mutate({ id, amount: payAmount, method: payMethod as PaymentMethod })}
                disabled={!payAmount || recordPayment.isPending}>
                পেমেন্ট রেকর্ড
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {order.status_history && order.status_history.length > 0 && <OrderTimeline history={order.status_history} />}
    </div>
  );
}
