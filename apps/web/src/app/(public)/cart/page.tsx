"use client";

import Link from "next/link";
import { Minus, Plus, Trash2, ShoppingCart } from "lucide-react";
import { useCart } from "@/contexts/CartContext";

const SHIPPING = 60;

export default function CartPage() {
  const { items, update, remove, total, count } = useCart();

  if (count === 0) {
    return (
      <div className="max-w-2xl mx-auto px-4 py-16 text-center">
        <ShoppingCart className="w-16 h-16 mx-auto text-gray-300 mb-4" />
        <h1 className="text-2xl font-bold text-gray-900 mb-2">Your cart is empty</h1>
        <p className="text-gray-600 mb-6">Discover products from local sellers</p>
        <Link href="/marketplace"
              className="px-6 py-3 bg-indigo-600 text-white rounded-xl font-medium hover:bg-indigo-700 transition-colors">
          Browse Marketplace
        </Link>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-4xl mx-auto px-4 py-8">
        <h1 className="text-2xl font-bold text-gray-900 mb-6">
          Shopping Cart <span className="text-gray-400 font-normal text-lg">({count} items)</span>
        </h1>

        <div className="grid lg:grid-cols-3 gap-6">
          {/* Items */}
          <div className="lg:col-span-2 space-y-3">
            {items.map((item) => (
              <div
                key={item.product_id}
                className="bg-white rounded-2xl border border-gray-100 shadow-sm p-4 flex gap-4 items-center"
              >
                {item.image_url ? (
                  <img
                    src={item.image_url}
                    alt={item.name}
                    className="w-16 h-16 object-cover rounded-xl shrink-0"
                  />
                ) : (
                  <div className="w-16 h-16 rounded-xl bg-indigo-50 flex items-center justify-center shrink-0">
                    <ShoppingCart className="w-6 h-6 text-indigo-300" />
                  </div>
                )}
                <div className="flex-1 min-w-0">
                  <p className="font-medium text-gray-900 truncate text-sm">{item.name}</p>
                  <p className="text-sm text-indigo-600 font-semibold mt-0.5">৳{item.price} each</p>
                </div>
                <div className="flex items-center gap-1.5">
                  <button
                    onClick={() => update(item.product_id, item.quantity - 1)}
                    className="w-7 h-7 rounded-lg border border-gray-200 flex items-center justify-center hover:bg-gray-50 transition-colors"
                  >
                    <Minus className="w-3 h-3 text-gray-600" />
                  </button>
                  <span className="w-8 text-center font-semibold text-sm">{item.quantity}</span>
                  <button
                    onClick={() => update(item.product_id, item.quantity + 1)}
                    className="w-7 h-7 rounded-lg border border-gray-200 flex items-center justify-center hover:bg-gray-50 transition-colors"
                  >
                    <Plus className="w-3 h-3 text-gray-600" />
                  </button>
                </div>
                <p className="font-bold text-gray-900 w-20 text-right text-sm shrink-0">
                  ৳{(item.price * item.quantity).toFixed(0)}
                </p>
                <button
                  onClick={() => remove(item.product_id)}
                  className="text-gray-300 hover:text-red-500 transition-colors shrink-0"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            ))}
          </div>

          {/* Summary */}
          <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6 h-fit sticky top-20">
            <h2 className="font-semibold text-gray-900 mb-4">Order Summary</h2>
            <div className="space-y-2.5 text-sm">
              <div className="flex justify-between text-gray-600">
                <span>Subtotal ({count} items)</span>
                <span>৳{total.toFixed(0)}</span>
              </div>
              <div className="flex justify-between text-gray-600">
                <span>Delivery fee</span>
                <span>৳{SHIPPING}</span>
              </div>
              <div className="border-t border-gray-100 pt-2.5 flex justify-between font-bold text-gray-900 text-base">
                <span>Total</span>
                <span>৳{(total + SHIPPING).toFixed(0)}</span>
              </div>
            </div>
            <Link
              href="/checkout"
              className="mt-5 block w-full py-3 bg-indigo-600 text-white rounded-xl font-semibold text-center hover:bg-indigo-700 transition-colors text-sm"
            >
              Proceed to Checkout
            </Link>
            <Link
              href="/marketplace"
              className="mt-2 block w-full py-2.5 text-center text-sm text-gray-400 hover:text-gray-600 transition-colors"
            >
              Continue Shopping
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
