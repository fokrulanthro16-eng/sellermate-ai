import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/** Coerces any API value to a finite number, defaulting to `fallback` (0) on null/undefined/NaN. */
export function safeNum(value: number | string | null | undefined, fallback = 0): number {
  const n = typeof value === "string" ? parseFloat(value) : Number(value);
  return isFinite(n) ? n : fallback;
}

export function formatCurrency(amount: number | string): string {
  const num = typeof amount === "string" ? parseFloat(amount) : amount;
  if (isNaN(num)) return "৳০";
  return `৳${num.toLocaleString("en-IN", { minimumFractionDigits: 0, maximumFractionDigits: 2 })}`;
}

export function formatDate(dateStr: string): string {
  try {
    return new Date(dateStr).toLocaleDateString("en-GB", {
      year: "numeric",
      month: "short",
      day: "numeric",
    });
  } catch {
    return dateStr;
  }
}

export function formatDateTime(dateStr: string): string {
  try {
    return new Date(dateStr).toLocaleString("en-GB", {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return dateStr;
  }
}

export function getInitials(name: string): string {
  return name
    .split(" ")
    .map((n) => n[0])
    .join("")
    .toUpperCase()
    .slice(0, 2);
}

export function getApiError(error: unknown): string {
  if (error && typeof error === "object" && "response" in error) {
    const e = error as { response?: { data?: { detail?: string; message?: string } } };
    return e.response?.data?.detail || e.response?.data?.message || "একটি ত্রুটি ঘটেছে";
  }
  if (error instanceof Error) return error.message;
  return "একটি ত্রুটি ঘটেছে";
}
