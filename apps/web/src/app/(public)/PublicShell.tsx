"use client";

import Link from "next/link";
import { ShoppingCart } from "lucide-react";
import { CartProvider, useCart } from "@/contexts/CartContext";

function PublicHeader() {
  const { count } = useCart();
  return (
    <header className="sticky top-0 z-50 bg-white/90 backdrop-blur border-b border-gray-200">
      <div className="max-w-6xl mx-auto px-4 h-14 flex items-center justify-between">
        <Link href="/marketplace" className="font-bold text-lg text-indigo-600">
          SellerMate
        </Link>
        <nav className="flex items-center gap-6 text-sm">
          <Link href="/marketplace" className="text-gray-600 hover:text-indigo-600">
            Marketplace
          </Link>
          <Link href="/track-order" className="text-gray-600 hover:text-indigo-600">
            Track Order
          </Link>
          <Link href="/cart" className="relative flex items-center gap-1 text-gray-600 hover:text-indigo-600">
            <ShoppingCart className="w-5 h-5" />
            {count > 0 && (
              <span className="absolute -top-2 -right-2 bg-indigo-600 text-white text-xs rounded-full w-4 h-4 flex items-center justify-center">
                {count}
              </span>
            )}
          </Link>
        </nav>
      </div>
    </header>
  );
}

export function PublicShell({ children }: { children: React.ReactNode }) {
  return (
    <CartProvider>
      <div className="min-h-screen bg-gray-50">
        <PublicHeader />
        <main>{children}</main>
        <footer className="mt-16 py-8 border-t border-gray-200 text-center text-sm text-gray-500">
          <p>Powered by <span className="text-indigo-600 font-semibold">SellerMate AI</span></p>
        </footer>
      </div>
    </CartProvider>
  );
}
