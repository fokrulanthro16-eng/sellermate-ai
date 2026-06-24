"use client";

import { useMemo, useState } from "react";
import { format, subDays, parseISO } from "date-fns";
import Link from "next/link";
import {
  Plus, Search, Eye, Banknote, XCircle, Truck, ChevronDown,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import OrderForm from "@/components/orders/OrderForm";
import {
  useOrders, useChangeOrderStatus, useRecordPayment,
  useCancelOrder, useUpdateOrder,
} from "@/hooks/useOrders";
import { useDashboard, useOrderBreakdown } from "@/hooks/useAnalytics";
import { useLang } from "@/contexts/LangContext";
import { formatCurrency, safeNum, cn } from "@/lib/utils";
import type { OrderStatus, PaymentMethod } from "@/types";

const LIMIT = 25;

/* ── pills ─────────────────────────────────────────────────── */
function SPill({ s }: { s: string }) {
  const MAP: Record<string, string> = {
    PENDING: "status-pending", CONFIRMED: "status-confirmed",
    PROCESSING: "status-processing", SHIPPED: "status-shipped",
    DELIVERED: "status-delivered", CANCELLED: "status-cancelled",
    RETURNED: "status-returned",
  };
  const LBL: Record<string, string> = {
    PENDING: "পেন্ডিং", CONFIRMED: "নিশ্চিত", PROCESSING: "প্রক্রিয়া",
    SHIPPED: "পাঠানো", DELIVERED: "ডেলিভারি", CANCELLED: "বাতিল", RETURNED: "ফেরত",
  };
  return <span className={cn("inline-flex px-2 py-0.5 rounded text-[11px] font-semibold whitespace-nowrap", MAP[s] ?? "bg-muted text-foreground")}>{LBL[s] ?? s}</span>;
}
function PPill({ s }: { s: string }) {
  const MAP: Record<string, string> = { UNPAID: "pay-unpaid", PARTIAL: "pay-partial", PAID: "pay-paid", REFUNDED: "pay-refunded" };
  const LBL: Record<string, string> = { UNPAID: "বাকি", PARTIAL: "আংশিক", PAID: "পরিশোধ", REFUNDED: "ফেরত" };
  return <span className={cn("inline-flex px-2 py-0.5 rounded text-[11px] font-semibold whitespace-nowrap", MAP[s] ?? "bg-muted text-foreground")}>{LBL[s] ?? s}</span>;
}

/* ── status update dialog ──────────────────────────────────── */
function StatusDialog({
  open, onClose, orderId, currentStatus,
}: { open: boolean; onClose: () => void; orderId: string; currentStatus: string }) {
  const [next, setNext] = useState<OrderStatus>(currentStatus as OrderStatus);
  const [note, setNote] = useState("");
  const mut = useChangeOrderStatus();

  const OPTS: { value: OrderStatus; label: string }[] = [
    { value: "PENDING",    label: "পেন্ডিং" },
    { value: "CONFIRMED",  label: "নিশ্চিত" },
    { value: "PROCESSING", label: "প্রক্রিয়াধীন" },
    { value: "SHIPPED",    label: "পাঠানো হয়েছে" },
    { value: "DELIVERED",  label: "ডেলিভারি সম্পন্ন" },
    { value: "CANCELLED",  label: "বাতিল" },
    { value: "RETURNED",   label: "ফেরত" },
  ];

  const handle = async () => {
    await mut.mutateAsync({ id: orderId, status: next, note: note || undefined });
    onClose();
  };

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-sm">
        <DialogHeader><DialogTitle>অর্ডার স্ট্যাটাস পরিবর্তন</DialogTitle></DialogHeader>
        <div className="space-y-4">
          <div className="space-y-1.5">
            <Label className="text-sm">নতুন স্ট্যাটাস</Label>
            <Select value={next} onValueChange={(v) => setNext(v as OrderStatus)}>
              <SelectTrigger className="h-9 text-sm"><SelectValue /></SelectTrigger>
              <SelectContent>
                {OPTS.map((o) => <SelectItem key={o.value} value={o.value}>{o.label}</SelectItem>)}
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-1.5">
            <Label className="text-sm">নোট (ঐচ্ছিক)</Label>
            <Input value={note} onChange={(e) => setNote(e.target.value)} placeholder="কারণ লিখুন..." className="h-9 text-sm" />
          </div>
          <div className="flex gap-2">
            <Button variant="outline" className="flex-1 h-9 text-sm" onClick={onClose}>বাতিল</Button>
            <Button className="flex-1 h-9 text-sm" onClick={handle} disabled={mut.isPending}>
              {mut.isPending ? "আপডেট হচ্ছে..." : "স্ট্যাটাস আপডেট করুন"}
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}

/* ── mark paid dialog ──────────────────────────────────────── */
function MarkPaidDialog({
  open, onClose, orderId, dueAmount, paymentMethod,
}: { open: boolean; onClose: () => void; orderId: string; dueAmount: string; paymentMethod: string }) {
  const [amount, setAmount] = useState(dueAmount);
  const [method, setMethod] = useState<PaymentMethod>(paymentMethod as PaymentMethod);
  const mut = useRecordPayment();

  const METHODS: { value: PaymentMethod; label: string }[] = [
    { value: "COD",          label: "ক্যাশ অন ডেলিভারি" },
    { value: "BKASH",        label: "বিকাশ" },
    { value: "NAGAD",        label: "নগদ" },
    { value: "BANK",         label: "ব্যাংক ট্রান্সফার" },
    { value: "CARD",         label: "কার্ড" },
    { value: "OTHER",        label: "অন্যান্য" },
  ];

  const handle = async () => {
    await mut.mutateAsync({ id: orderId, amount, method });
    onClose();
  };

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-sm">
        <DialogHeader><DialogTitle>পেমেন্ট রেকর্ড করুন</DialogTitle></DialogHeader>
        <div className="space-y-4">
          <div className="space-y-1.5">
            <Label className="text-sm">পরিমাণ (৳)</Label>
            <Input type="number" value={amount} onChange={(e) => setAmount(e.target.value)} className="h-9 text-sm" />
          </div>
          <div className="space-y-1.5">
            <Label className="text-sm">পেমেন্ট মাধ্যম</Label>
            <Select value={method} onValueChange={(v) => setMethod(v as PaymentMethod)}>
              <SelectTrigger className="h-9 text-sm"><SelectValue /></SelectTrigger>
              <SelectContent>
                {METHODS.map((m) => <SelectItem key={m.value} value={m.value}>{m.label}</SelectItem>)}
              </SelectContent>
            </Select>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" className="flex-1 h-9 text-sm" onClick={onClose}>বাতিল</Button>
            <Button className="flex-1 h-9 text-sm" onClick={handle} disabled={mut.isPending}>
              {mut.isPending ? "রেকর্ড হচ্ছে..." : "পেমেন্ট নিশ্চিত করুন"}
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}

/* ── tracking dialog ───────────────────────────────────────── */
function TrackingDialog({
  open, onClose, orderId, currentTracking, currentCourier,
}: { open: boolean; onClose: () => void; orderId: string; currentTracking?: string; currentCourier?: string }) {
  const [tracking, setTracking] = useState(currentTracking ?? "");
  const [courier, setCourier]   = useState(currentCourier  ?? "");
  const mut = useUpdateOrder();

  const handle = async () => {
    await mut.mutateAsync({ id: orderId, tracking_number: tracking, courier_name: courier });
    onClose();
  };

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-sm">
        <DialogHeader><DialogTitle>ট্র্যাকিং তথ্য যোগ করুন</DialogTitle></DialogHeader>
        <div className="space-y-4">
          <div className="space-y-1.5">
            <Label className="text-sm">কুরিয়ার কোম্পানি</Label>
            <Input value={courier} onChange={(e) => setCourier(e.target.value)} placeholder="যেমন: Pathao, Steadfast, RedX" className="h-9 text-sm" />
          </div>
          <div className="space-y-1.5">
            <Label className="text-sm">ট্র্যাকিং নম্বর</Label>
            <Input value={tracking} onChange={(e) => setTracking(e.target.value)} placeholder="ট্র্যাকিং ID লিখুন" className="h-9 text-sm font-mono" />
          </div>
          <div className="flex gap-2">
            <Button variant="outline" className="flex-1 h-9 text-sm" onClick={onClose}>বাতিল</Button>
            <Button className="flex-1 h-9 text-sm" onClick={handle} disabled={mut.isPending}>
              {mut.isPending ? "সেভ হচ্ছে..." : "সেভ করুন"}
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}

/* ── main page ─────────────────────────────────────────────── */
export default function OrdersPage() {
  const { lang } = useLang();
  const l = (bn: string, en: string) => lang === "bn" ? bn : en;

  const [search,     setSearch]     = useState("");
  const [status,     setStatus]     = useState("");
  const [payStatus,  setPayStatus]  = useState("");
  const [page,       setPage]       = useState(1);
  const [newOpen,    setNewOpen]    = useState(false);

  /* dialogs */
  const [statusDlg,  setStatusDlg]  = useState<{ id: string; current: string } | null>(null);
  const [paidDlg,    setPaidDlg]    = useState<{ id: string; due: string; method: string } | null>(null);
  const [trackDlg,   setTrackDlg]   = useState<{ id: string; tracking?: string; courier?: string } | null>(null);

  const to   = useMemo(() => format(new Date(), "yyyy-MM-dd"), []);
  const from = useMemo(() => format(subDays(new Date(), 30), "yyyy-MM-dd"), []);

  const { data: dashboard } = useDashboard();
  const { data: bd }        = useOrderBreakdown(from, to);
  const cancelOrder         = useCancelOrder();

  const { data, isLoading } = useOrders({
    page, limit: LIMIT,
    search:         search     || undefined,
    status:        (status     || undefined) as OrderStatus | undefined,
    payment_status: payStatus  || undefined,
  });

  const orders     = data?.items ?? [];
  const total      = data?.total ?? 0;
  const totalPages = Math.max(1, Math.ceil(total / LIMIT));

  const byS = (bd?.by_status as Record<string, number> | undefined) ?? {};

  const STATUS_TABS = [
    { v: "",           label: l("সব", "All"),            count: safeNum(dashboard?.total_orders) },
    { v: "PENDING",    label: l("পেন্ডিং", "Pending"),   count: safeNum(byS.PENDING)    },
    { v: "CONFIRMED",  label: l("নিশ্চিত", "Confirmed"), count: safeNum(byS.CONFIRMED)  },
    { v: "PROCESSING", label: l("প্রক্রিয়া", "Processing"), count: safeNum(byS.PROCESSING) },
    { v: "SHIPPED",    label: l("পাঠানো", "Shipped"),    count: safeNum(byS.SHIPPED)    },
    { v: "DELIVERED",  label: l("ডেলিভারি", "Delivered"),count: safeNum(byS.DELIVERED)  },
    { v: "CANCELLED",  label: l("বাতিল", "Cancelled"),   count: safeNum(byS.CANCELLED)  },
    { v: "RETURNED",   label: l("ফেরত", "Returned"),     count: safeNum(byS.RETURNED)   },
  ];

  const PAYMENT_OPTS = [
    { value: "",          label: l("সব পেমেন্ট", "All") },
    { value: "UNPAID",    label: l("বাকি", "Unpaid") },
    { value: "PARTIAL",   label: l("আংশিক", "Partial") },
    { value: "PAID",      label: l("পরিশোধিত", "Paid") },
    { value: "REFUNDED",  label: l("ফেরত", "Refunded") },
  ];

  const handleCancel = async (id: string) => {
    if (!confirm(l("এই অর্ডার বাতিল করবেন?", "Cancel this order?"))) return;
    await cancelOrder.mutateAsync(id);
  };

  return (
    <div className="space-y-3 max-w-[1600px]">

      {/* header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-lg font-bold">{l("অর্ডার", "Orders")}</h1>
          <p className="text-xs text-muted-foreground">
            {total > 0 ? `${total} ${l("টি অর্ডার", "total orders")}` : l("অর্ডার ব্যবস্থাপনা", "Order management")}
          </p>
        </div>
        <Button onClick={() => setNewOpen(true)} size="sm" className="gap-1.5 h-8 text-xs">
          <Plus className="h-3.5 w-3.5" />{l("নতুন অর্ডার", "New Order")}
        </Button>
      </div>

      {/* status tabs */}
      <div className="admin-card px-3 py-2">
        <div className="flex items-center gap-0.5 overflow-x-auto">
          {STATUS_TABS.map((tab) => (
            <button
              key={tab.v}
              onClick={() => { setStatus(tab.v); setPage(1); }}
              className={cn(
                "flex items-center gap-1.5 px-3 py-1.5 rounded text-xs font-medium whitespace-nowrap transition-colors shrink-0",
                status === tab.v
                  ? "bg-primary text-primary-foreground"
                  : "text-muted-foreground hover:bg-accent hover:text-foreground"
              )}
            >
              {tab.label}
              {tab.count > 0 && (
                <span className={cn("px-1 py-0 rounded text-[10px] font-bold",
                  status === tab.v ? "bg-white/20 text-white" : "bg-muted"
                )}>{tab.count}</span>
              )}
            </button>
          ))}
        </div>
      </div>

      {/* search + filters */}
      <div className="flex gap-2 flex-wrap items-center">
        <div className="relative flex-1 min-w-[220px] max-w-sm">
          <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground" />
          <Input
            placeholder={l("অর্ডার নম্বর, গ্রাহক, ফোন...", "Order no, customer, phone...")}
            value={search}
            onChange={(e) => { setSearch(e.target.value); setPage(1); }}
            className="pl-8 h-8 text-sm"
          />
        </div>
        <Select value={payStatus} onValueChange={(v) => { setPayStatus(v); setPage(1); }}>
          <SelectTrigger className="w-36 h-8 text-xs"><SelectValue placeholder={l("পেমেন্ট", "Payment")} /></SelectTrigger>
          <SelectContent>
            {PAYMENT_OPTS.map((o) => <SelectItem key={o.value} value={o.value} className="text-sm">{o.label}</SelectItem>)}
          </SelectContent>
        </Select>
        {(search || status || payStatus) && (
          <Button variant="ghost" size="sm" className="h-8 text-xs px-2"
            onClick={() => { setSearch(""); setStatus(""); setPayStatus(""); setPage(1); }}>
            ✕ {l("ক্লিয়ার", "Clear")}
          </Button>
        )}
        <span className="ml-auto text-xs text-muted-foreground">{total} {l("টি", "orders")}</span>
      </div>

      {/* table */}
      <div className="admin-card overflow-hidden">
        {isLoading ? (
          <div className="p-4 space-y-2">
            {Array.from({ length: 8 }).map((_, i) => <Skeleton key={i} className="h-9 w-full" />)}
          </div>
        ) : orders.length === 0 ? (
          <div className="py-14 text-center space-y-2">
            <p className="text-sm text-muted-foreground">{l("কোনো অর্ডার পাওয়া যায়নি", "No orders found")}</p>
            <Button size="sm" onClick={() => setNewOpen(true)} className="gap-1.5 text-xs h-8">
              <Plus className="h-3.5 w-3.5" />{l("নতুন অর্ডার", "Create Order")}
            </Button>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="commerce-table">
              <thead>
                <tr>
                  <th>{l("অর্ডার#", "Order#")}</th>
                  <th>{l("গ্রাহক", "Customer")}</th>
                  <th>{l("ফোন", "Phone")}</th>
                  <th>{l("অবস্থা", "Status")}</th>
                  <th>{l("পেমেন্ট", "Payment")}</th>
                  <th>{l("কুরিয়ার", "Courier")}</th>
                  <th className="text-right">{l("পরিমাণ", "Amount")}</th>
                  <th className="text-right">{l("বাকি", "Due")}</th>
                  <th>{l("তারিখ", "Date")}</th>
                  <th>{l("অ্যাকশন", "Actions")}</th>
                </tr>
              </thead>
              <tbody>
                {orders.map((o) => {
                  const ref    = o.order_number ?? `#${o.id.slice(-6).toUpperCase()}`;
                  const dt     = o.created_at ? format(parseISO(o.created_at), "dd/MM/yy") : "—";
                  const due    = parseFloat(o.due_amount ?? "0");
                  const isPaid = o.payment_status === "PAID";
                  const isDone = o.status === "DELIVERED" || o.status === "CANCELLED";
                  return (
                    <tr key={o.id}>
                      <td>
                        <Link href={`/orders/${o.id}`} className="font-mono text-[11px] font-semibold text-primary hover:underline">
                          {ref}
                        </Link>
                      </td>
                      <td className="text-sm max-w-[130px] truncate">{o.customer_name || "—"}</td>
                      <td className="font-mono text-[11px] text-muted-foreground">{o.customer_phone || "—"}</td>
                      <td><SPill s={o.status} /></td>
                      <td><PPill s={o.payment_status} /></td>
                      <td>
                        {o.courier_name ? (
                          <div>
                            <p className="text-xs font-medium">{o.courier_name}</p>
                            {o.tracking_number && (
                              <p className="text-[10px] font-mono text-muted-foreground">{o.tracking_number}</p>
                            )}
                          </div>
                        ) : (
                          <span className="text-[11px] text-muted-foreground">—</span>
                        )}
                      </td>
                      <td className="text-right text-sm font-semibold">{formatCurrency(o.total_amount)}</td>
                      <td className="text-right">
                        {due > 0
                          ? <span className="text-[11px] font-semibold text-red-600 dark:text-red-400">{formatCurrency(due)}</span>
                          : <span className="text-[11px] text-muted-foreground">—</span>
                        }
                      </td>
                      <td className="text-[11px] text-muted-foreground whitespace-nowrap">{dt}</td>
                      <td>
                        <div className="flex items-center gap-0.5">
                          {/* view */}
                          <Link href={`/orders/${o.id}`} title={l("দেখুন", "View")}>
                            <Button variant="ghost" size="icon" className="h-7 w-7">
                              <Eye className="h-3.5 w-3.5" />
                            </Button>
                          </Link>
                          {/* update status */}
                          {!isDone && (
                            <Button
                              variant="ghost" size="icon" className="h-7 w-7"
                              title={l("স্ট্যাটাস বদলান", "Update Status")}
                              onClick={() => setStatusDlg({ id: o.id, current: o.status })}
                            >
                              <ChevronDown className="h-3.5 w-3.5" />
                            </Button>
                          )}
                          {/* mark paid */}
                          {!isPaid && (
                            <Button
                              variant="ghost" size="icon" className="h-7 w-7 text-green-700 hover:text-green-800 hover:bg-green-50 dark:text-green-400 dark:hover:bg-green-950/20"
                              title={l("পেমেন্ট মার্ক", "Mark Paid")}
                              onClick={() => setPaidDlg({ id: o.id, due: o.due_amount ?? o.total_amount, method: o.payment_method })}
                            >
                              <Banknote className="h-3.5 w-3.5" />
                            </Button>
                          )}
                          {/* add tracking */}
                          <Button
                            variant="ghost" size="icon" className="h-7 w-7 text-violet-700 hover:text-violet-800 hover:bg-violet-50 dark:text-violet-400 dark:hover:bg-violet-950/20"
                            title={l("ট্র্যাকিং যোগ করুন", "Add Tracking")}
                            onClick={() => setTrackDlg({ id: o.id, tracking: o.tracking_number, courier: o.courier_name })}
                          >
                            <Truck className="h-3.5 w-3.5" />
                          </Button>
                          {/* cancel */}
                          {!isDone && (
                            <Button
                              variant="ghost" size="icon" className="h-7 w-7 text-red-600 hover:text-red-700 hover:bg-red-50 dark:text-red-400 dark:hover:bg-red-950/20"
                              title={l("বাতিল করুন", "Cancel")}
                              onClick={() => handleCancel(o.id)}
                              disabled={cancelOrder.isPending}
                            >
                              <XCircle className="h-3.5 w-3.5" />
                            </Button>
                          )}
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* pagination */}
      {total > LIMIT && (
        <div className="flex items-center justify-between">
          <span className="text-xs text-muted-foreground">
            {l("পৃষ্ঠা", "Page")} {page}/{totalPages}
          </span>
          <div className="flex gap-2">
            <Button variant="outline" size="sm" className="h-7 text-xs" disabled={page === 1} onClick={() => setPage((p) => p - 1)}>
              {l("আগের", "Prev")}
            </Button>
            <Button variant="outline" size="sm" className="h-7 text-xs" disabled={page >= totalPages} onClick={() => setPage((p) => p + 1)}>
              {l("পরের", "Next")}
            </Button>
          </div>
        </div>
      )}

      {/* new order */}
      <Dialog open={newOpen} onOpenChange={setNewOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader><DialogTitle>{l("নতুন অর্ডার", "Create New Order")}</DialogTitle></DialogHeader>
          <OrderForm onSuccess={() => setNewOpen(false)} />
        </DialogContent>
      </Dialog>

      {/* status dialog */}
      {statusDlg && (
        <StatusDialog
          open
          onClose={() => setStatusDlg(null)}
          orderId={statusDlg.id}
          currentStatus={statusDlg.current}
        />
      )}

      {/* mark paid dialog */}
      {paidDlg && (
        <MarkPaidDialog
          open
          onClose={() => setPaidDlg(null)}
          orderId={paidDlg.id}
          dueAmount={paidDlg.due}
          paymentMethod={paidDlg.method}
        />
      )}

      {/* tracking dialog */}
      {trackDlg && (
        <TrackingDialog
          open
          onClose={() => setTrackDlg(null)}
          orderId={trackDlg.id}
          currentTracking={trackDlg.tracking}
          currentCourier={trackDlg.courier}
        />
      )}
    </div>
  );
}
