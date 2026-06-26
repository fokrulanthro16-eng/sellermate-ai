"use client";

import React, { createContext, useCallback, useContext, useEffect, useState } from "react";

export interface CartItem {
  product_id: string;
  merchant_id: string;
  name: string;
  price: number;
  image_url?: string;
  quantity: number;
}

interface CartContextValue {
  items: CartItem[];
  add: (item: Omit<CartItem, "quantity"> & { quantity?: number }) => void;
  remove: (product_id: string) => void;
  update: (product_id: string, quantity: number) => void;
  clear: () => void;
  total: number;
  count: number;
}

const CartContext = createContext<CartContextValue | null>(null);

const STORAGE_KEY = "sm_cart";

export function CartProvider({ children }: { children: React.ReactNode }) {
  const [items, setItems] = useState<CartItem[]>([]);

  useEffect(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored) setItems(JSON.parse(stored));
    } catch {}
  }, []);

  const persist = useCallback((next: CartItem[]) => {
    setItems(next);
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
    } catch {}
  }, []);

  const add = useCallback(
    (item: Omit<CartItem, "quantity"> & { quantity?: number }) => {
      setItems((prev) => {
        const qty = item.quantity ?? 1;
        const existing = prev.find((i) => i.product_id === item.product_id);
        const next = existing
          ? prev.map((i) =>
              i.product_id === item.product_id ? { ...i, quantity: i.quantity + qty } : i
            )
          : [...prev, { ...item, quantity: qty }];
        localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
        return next;
      });
    },
    []
  );

  const remove = useCallback((product_id: string) => {
    setItems((prev) => {
      const next = prev.filter((i) => i.product_id !== product_id);
      localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
      return next;
    });
  }, []);

  const update = useCallback((product_id: string, quantity: number) => {
    if (quantity <= 0) {
      remove(product_id);
      return;
    }
    setItems((prev) => {
      const next = prev.map((i) => (i.product_id === product_id ? { ...i, quantity } : i));
      localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
      return next;
    });
  }, [remove]);

  const clear = useCallback(() => persist([]), [persist]);

  const total = items.reduce((s, i) => s + i.price * i.quantity, 0);
  const count = items.reduce((s, i) => s + i.quantity, 0);

  return (
    <CartContext.Provider value={{ items, add, remove, update, clear, total, count }}>
      {children}
    </CartContext.Provider>
  );
}

export function useCart() {
  const ctx = useContext(CartContext);
  if (!ctx) throw new Error("useCart must be used within CartProvider");
  return ctx;
}
