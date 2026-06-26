"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useCart } from "@/contexts/CartContext";
import { usePlaceOrder } from "@/hooks/usePublicStore";
import { toast } from "sonner";
import Link from "next/link";
import { CheckCircle } from "lucide-react";

const SHIPPING = 60;

const PAYMENT_METHODS = [
  { id: "COD", label: "Cash on Delivery", emoji: "💵" },
  { id: "BKASH", label: "bKash", emoji: "🔴" },
  { id: "NAGAD", label: "Nagad", emoji: "🟠" },
  { id: "BANK_TRANSFER", label: "Bank Transfer", emoji: "🏦" },
];

export default function CheckoutPage() {
  const { items, total, clear } = useCart();
  const router = useRouter();
  const placeOrder = usePlaceOrder();
  const [ordered, setOrdered] = useState<{ id: string; number: string } | null>(null);

  const [form, setForm] = useState({
    name: "",
    phone: "",
    email: "",
    address: "",
    district: "",
    payment: "COD",
    notes: "",
  });

  if (items.length === 0 && !ordered) {
    return (
      <div className="max-w-xl mx-auto px-4 py-16 text-center">
        <p className="text-gray-600 mb-4">Your cart is empty.</p>
        <Link href="/marketplace" className="text-indigo-600 underline">Browse Marketplace</Link>
      </div>
    );
  }

  if (ordered) {
    return (
      <div className="max-w-lg mx-auto px-4 py-16 text-center">
        <div className="w-20 h-20 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-5">
          <CheckCircle className="w-10 h-10 text-green-600" />
        </div>
        <h1 className="text-2xl font-bold text-gray-900 mb-2">Order Placed!</h1>
        <p className="text-gray-600 mb-1 text-sm">
          Order <strong className="text-gray-900">{ordered.number}</strong> confirmed
        </p>
        <p className="text-gray-500 text-sm mb-3">
          We will contact you on <strong>{form.phone}</strong> to confirm delivery.
        </p>
        <div className="bg-indigo-50 border border-indigo-100 rounded-xl p-4 mb-8 text-sm text-indigo-700">
          Track your order status anytime using your order number or phone.
        </div>
        <div className="flex gap-3 justify-center">
          <Link href="/track-order"
                className="px-5 py-2.5 border border-indigo-200 text-indigo-600 rounded-xl font-medium hover:bg-indigo-50 transition-colors text-sm">
            Track Order
          </Link>
          <Link href="/marketplace"
                className="px-5 py-2.5 bg-indigo-600 text-white rounded-xl font-medium hover:bg-indigo-700 transition-colors text-sm">
            Continue Shopping
          </Link>
        </div>
      </div>
    );
  }

  const merchantId = items[0]?.merchant_id;
  const hasMixed = items.some((i) => i.merchant_id !== merchantId);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!form.name || !form.phone || !form.address) {
      toast.error("Please fill in name, phone and address");
      return;
    }
    if (hasMixed) {
      toast.error("All items must be from the same store for checkout");
      return;
    }
    try {
      const result = await placeOrder.mutateAsync({
        merchant_id: merchantId,
        items: items.map((i) => ({ product_id: i.product_id, quantity: i.quantity })),
        customer_name: form.name,
        customer_phone: form.phone,
        customer_email: form.email || undefined,
        delivery_address: form.address,
        delivery_district: form.district || undefined,
        payment_method: form.payment,
        notes: form.notes || undefined,
      });
      clear();
      setOrdered({ id: result.data.order_id, number: result.data.order_number });
    } catch (err: any) {
      toast.error(err.message || "Failed to place order");
    }
  }

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Checkout</h1>

      {hasMixed && (
        <div className="mb-4 p-3 bg-amber-50 border border-amber-200 rounded-lg text-amber-700 text-sm">
          Cart has items from multiple stores. Please keep items from one store only.
        </div>
      )}

      <form onSubmit={handleSubmit} className="grid lg:grid-cols-2 gap-8">
        {/* Delivery Info */}
        <div className="space-y-4">
          <h2 className="font-semibold text-gray-900">Delivery Information</h2>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Name *</label>
            <input className="w-full border border-gray-200 rounded-xl px-3.5 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                   value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })}
                   placeholder="Your full name" required />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Phone *</label>
            <input className="w-full border border-gray-200 rounded-xl px-3.5 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                   value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })}
                   placeholder="+8801..." type="tel" required />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
            <input className="w-full border border-gray-200 rounded-xl px-3.5 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                   value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })}
                   placeholder="Optional" type="email" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Delivery Address *</label>
            <textarea className="w-full border border-gray-200 rounded-xl px-3.5 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent resize-none"
                      rows={3} value={form.address}
                      onChange={(e) => setForm({ ...form, address: e.target.value })}
                      placeholder="House, road, area..." required />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">District</label>
            <input className="w-full border border-gray-200 rounded-xl px-3.5 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                   value={form.district} onChange={(e) => setForm({ ...form, district: e.target.value })}
                   placeholder="e.g. Dhaka" />
          </div>

          <h2 className="font-semibold text-gray-900 pt-2">Payment Method</h2>
          <div className="grid grid-cols-2 gap-2">
            {PAYMENT_METHODS.map((m) => (
              <label key={m.id}
                     className={`flex items-center gap-2 p-3 rounded-lg border-2 cursor-pointer transition-colors ${
                       form.payment === m.id ? "border-indigo-600 bg-indigo-50" : "border-gray-200 hover:border-gray-300"
                     }`}>
                <input type="radio" name="payment" value={m.id} checked={form.payment === m.id}
                       onChange={() => setForm({ ...form, payment: m.id })} className="sr-only" />
                <span>{m.emoji}</span>
                <span className="text-sm font-medium text-gray-700">{m.label}</span>
              </label>
            ))}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Order Notes</label>
            <textarea className="w-full border border-gray-200 rounded-xl px-3.5 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent resize-none"
                      rows={2} value={form.notes}
                      onChange={(e) => setForm({ ...form, notes: e.target.value })}
                      placeholder="Special instructions..." />
          </div>
        </div>

        {/* Summary */}
        <div>
          <h2 className="font-semibold text-gray-900 mb-4">Order Summary</h2>
          <div className="bg-white rounded-xl border border-gray-200 p-4 space-y-3 mb-4">
            {items.map((item) => (
              <div key={item.product_id} className="flex justify-between text-sm">
                <span className="text-gray-700 truncate flex-1 mr-2">
                  {item.name} × {item.quantity}
                </span>
                <span className="font-medium text-gray-900">৳{(item.price * item.quantity).toFixed(0)}</span>
              </div>
            ))}
            <div className="border-t pt-3 space-y-1">
              <div className="flex justify-between text-sm text-gray-600">
                <span>Subtotal</span><span>৳{total.toFixed(0)}</span>
              </div>
              <div className="flex justify-between text-sm text-gray-600">
                <span>Shipping</span><span>৳{SHIPPING}</span>
              </div>
              <div className="flex justify-between font-bold text-gray-900 pt-1">
                <span>Total</span><span>৳{(total + SHIPPING).toFixed(0)}</span>
              </div>
            </div>
          </div>

          <button type="submit" disabled={placeOrder.isPending}
                  className="w-full py-3.5 bg-indigo-600 text-white rounded-xl font-semibold hover:bg-indigo-700 disabled:opacity-60 transition-colors">
            {placeOrder.isPending ? "Placing Order..." : "Place Order"}
          </button>
          <Link href="/cart"
                className="mt-2 block w-full py-2.5 text-center text-sm text-gray-500 hover:text-gray-700">
            Back to Cart
          </Link>
        </div>
      </form>
    </div>
  );
}
