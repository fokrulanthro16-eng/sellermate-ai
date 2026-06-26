"use client";

import { useState } from "react";
import { Search, Package, CheckCircle, Clock, Truck, XCircle, RefreshCw } from "lucide-react";

const API_BASE = (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1") + "/public";

const STATUS_META: Record<string, { label: string; color: string; Icon: any }> = {
  PENDING:    { label: "Pending",    color: "text-amber-600 bg-amber-50 border-amber-200",   Icon: Clock },
  CONFIRMED:  { label: "Confirmed",  color: "text-blue-600 bg-blue-50 border-blue-200",      Icon: CheckCircle },
  PROCESSING: { label: "Processing", color: "text-indigo-600 bg-indigo-50 border-indigo-200", Icon: RefreshCw },
  SHIPPED:    { label: "Shipped",    color: "text-purple-600 bg-purple-50 border-purple-200", Icon: Truck },
  DELIVERED:  { label: "Delivered",  color: "text-green-600 bg-green-50 border-green-200",   Icon: CheckCircle },
  CANCELLED:  { label: "Cancelled",  color: "text-red-600 bg-red-50 border-red-200",         Icon: XCircle },
  RETURNED:   { label: "Returned",   color: "text-gray-600 bg-gray-50 border-gray-200",      Icon: RefreshCw },
};

const STEPS = ["PENDING", "CONFIRMED", "PROCESSING", "SHIPPED", "DELIVERED"];

function StatusBadge({ status }: { status: string }) {
  const meta = STATUS_META[status] || { label: status, color: "text-gray-600 bg-gray-50 border-gray-200", Icon: Package };
  const { label, color, Icon } = meta;
  return (
    <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-sm font-medium border ${color}`}>
      <Icon className="w-3.5 h-3.5" /> {label}
    </span>
  );
}

function ProgressBar({ status }: { status: string }) {
  const step = STEPS.indexOf(status);
  if (step === -1 || status === "CANCELLED" || status === "RETURNED") return null;
  const progress = step === 0 ? 0 : (step / (STEPS.length - 1)) * 100;
  return (
    <div className="mt-5 mb-1 px-1">
      <div className="relative flex justify-between">
        <div className="absolute top-3.5 left-0 right-0 h-0.5 bg-gray-200" />
        <div
          className="absolute top-3.5 left-0 h-0.5 bg-indigo-600 transition-all duration-500"
          style={{ width: `${progress}%` }}
        />
        {STEPS.map((s, i) => (
          <div key={s} className="relative flex flex-col items-center z-10">
            <div className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold border-2 transition-colors ${
              i <= step
                ? "bg-indigo-600 border-indigo-600 text-white"
                : "bg-white border-gray-300 text-gray-400"
            }`}>
              {i < step ? "✓" : i + 1}
            </div>
            <span className={`text-[10px] mt-1.5 text-center leading-tight max-w-12 ${
              i <= step ? "text-indigo-600 font-semibold" : "text-gray-400"
            }`}>
              {STATUS_META[s]?.label || s}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

function OrderCard({ order }: { order: any }) {
  return (
    <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-5 space-y-4">
      <div className="flex items-start justify-between flex-wrap gap-2">
        <div>
          <p className="font-bold text-gray-900 text-lg">{order.order_number}</p>
          <p className="text-sm text-gray-500 mt-0.5">
            {order.created_at
              ? new Date(order.created_at).toLocaleDateString("en-BD", {
                  day: "numeric", month: "short", year: "numeric",
                })
              : ""}
          </p>
        </div>
        <StatusBadge status={order.status} />
      </div>

      <ProgressBar status={order.status} />

      <div className="grid grid-cols-2 gap-3 text-sm pt-1">
        <div className="bg-gray-50 rounded-xl p-3">
          <p className="text-gray-500 text-xs mb-0.5">Total Amount</p>
          <p className="font-bold text-gray-900">৳{order.total_amount?.toFixed(0)}</p>
        </div>
        <div className="bg-gray-50 rounded-xl p-3">
          <p className="text-gray-500 text-xs mb-0.5">Payment Status</p>
          <p className="font-bold text-gray-900">{order.payment_status}</p>
        </div>
        {order.payment_method && (
          <div className="bg-gray-50 rounded-xl p-3">
            <p className="text-gray-500 text-xs mb-0.5">Payment Method</p>
            <p className="font-semibold text-gray-900">{order.payment_method}</p>
          </div>
        )}
        {order.due_amount > 0 && (
          <div className="bg-red-50 rounded-xl p-3">
            <p className="text-red-500 text-xs mb-0.5">Due Amount</p>
            <p className="font-bold text-red-600">৳{order.due_amount?.toFixed(0)}</p>
          </div>
        )}
      </div>

      {(order.courier_name || order.tracking_number) && (
        <div className="bg-blue-50 rounded-xl p-4 text-sm border border-blue-100">
          <p className="font-semibold text-blue-800 flex items-center gap-1.5 mb-2">
            <Truck className="w-4 h-4" /> Courier Tracking
          </p>
          {order.courier_name && (
            <p className="text-blue-700 text-xs">Courier: <strong>{order.courier_name}</strong></p>
          )}
          {order.tracking_number ? (
            <p className="text-blue-700 text-xs mt-0.5">Tracking ID: <strong>{order.tracking_number}</strong></p>
          ) : (
            <p className="text-blue-500 text-xs mt-0.5">Tracking ID will appear once shipped</p>
          )}
        </div>
      )}

      {order.delivery_address && (
        <div className="text-sm text-gray-600">
          <p className="text-gray-400 text-xs mb-0.5">Delivery to</p>
          <p className="font-medium">{order.delivery_address}</p>
        </div>
      )}

      {order.delivered_at && (
        <div className="flex items-center gap-2 text-green-600 text-sm font-medium">
          <CheckCircle className="w-4 h-4" />
          Delivered on {new Date(order.delivered_at).toLocaleDateString()}
        </div>
      )}
    </div>
  );
}

export default function TrackOrderPage() {
  const [orderNumber, setOrderNumber] = useState("");
  const [phone, setPhone] = useState("");
  const [loading, setLoading] = useState(false);
  const [orders, setOrders] = useState<any[] | null>(null);
  const [error, setError] = useState("");

  async function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    if (!orderNumber && !phone) {
      setError("Enter an order number or phone number");
      return;
    }
    setLoading(true);
    setError("");
    setOrders(null);
    try {
      const params = new URLSearchParams();
      if (orderNumber) params.set("order_number", orderNumber.trim());
      if (phone) params.set("phone", phone.trim());
      const res = await fetch(`${API_BASE}/track?${params}`);
      const json = await res.json();
      if (!res.ok) {
        setError(json?.error?.message || "Order not found");
      } else {
        setOrders(json.data.orders || [json.data]);
      }
    } catch {
      setError("Failed to connect. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-2xl mx-auto px-4 py-10">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="w-14 h-14 bg-indigo-100 rounded-2xl flex items-center justify-center mx-auto mb-4">
            <Package className="w-7 h-7 text-indigo-600" />
          </div>
          <h1 className="text-2xl font-bold text-gray-900">Track Your Order</h1>
          <p className="text-gray-500 mt-1 text-sm">Enter your order number or phone number to see your order status</p>
        </div>

        {/* Form */}
        <form onSubmit={handleSearch} className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6 space-y-4 mb-6">
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-1.5">Order Number</label>
            <input
              className="w-full border border-gray-200 rounded-xl px-3.5 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
              placeholder="e.g. PUB-1234567890-ABCD"
              value={orderNumber}
              onChange={(e) => setOrderNumber(e.target.value)}
            />
          </div>

          <div className="flex items-center gap-3">
            <div className="flex-1 h-px bg-gray-100" />
            <span className="text-xs text-gray-400 font-medium">or</span>
            <div className="flex-1 h-px bg-gray-100" />
          </div>

          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-1.5">Phone Number</label>
            <input
              className="w-full border border-gray-200 rounded-xl px-3.5 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
              placeholder="+8801..."
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
              type="tel"
            />
          </div>

          {error && (
            <div className="p-3 bg-red-50 border border-red-100 rounded-xl text-sm text-red-600">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full py-3 bg-indigo-600 text-white rounded-xl font-semibold hover:bg-indigo-700 disabled:opacity-60 transition-colors flex items-center justify-center gap-2"
          >
            <Search className="w-4 h-4" />
            {loading ? "Searching..." : "Track Order"}
          </button>
        </form>

        {orders && orders.length > 0 && (
          <div className="space-y-4">
            <p className="text-sm text-gray-500 font-medium">{orders.length} order(s) found</p>
            {orders.map((o) => <OrderCard key={o.order_id} order={o} />)}
          </div>
        )}

        {orders && orders.length === 0 && (
          <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-8 text-center">
            <Package className="w-10 h-10 mx-auto text-gray-200 mb-3" />
            <p className="text-gray-500 font-medium">No orders found</p>
            <p className="text-gray-400 text-sm mt-1">Check your order number or phone and try again</p>
          </div>
        )}
      </div>
    </div>
  );
}
