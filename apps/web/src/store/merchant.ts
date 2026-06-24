import type { Merchant } from "@/types";

let currentMerchant: Merchant | null = null;
const listeners = new Set<() => void>();

export function getMerchant(): Merchant | null {
  return currentMerchant;
}

export function setMerchant(m: Merchant | null): void {
  currentMerchant = m;
  listeners.forEach((fn) => fn());
}

export function subscribeMerchant(fn: () => void): () => void {
  listeners.add(fn);
  return () => listeners.delete(fn);
}
