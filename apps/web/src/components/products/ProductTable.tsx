"use client";

import Link from "next/link";
import { Edit2, Trash2, Package } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { formatCurrency, cn } from "@/lib/utils";
import type { Product } from "@/types";

interface ProductTableProps {
  products?: Product[];
  loading?: boolean;
  onDelete?: (id: string) => void;
}

function StockPill({ qty, threshold }: { qty: number; threshold: number }) {
  if (qty === 0)
    return <span className="inline-flex px-1.5 py-0.5 rounded text-[11px] font-semibold bg-red-100 text-red-700 border border-red-200">স্টক নেই</span>;
  if (qty <= threshold)
    return <span className="inline-flex px-1.5 py-0.5 rounded text-[11px] font-semibold bg-amber-100 text-amber-700 border border-amber-200">কম স্টক</span>;
  return <span className="inline-flex px-1.5 py-0.5 rounded text-[11px] font-semibold bg-emerald-100 text-emerald-700 border border-emerald-200">ঠিকঠাক</span>;
}

export default function ProductTable({ products, loading, onDelete }: ProductTableProps) {
  if (loading) {
    return (
      <div className="admin-card overflow-hidden">
        <div className="p-4 space-y-2">
          {[1, 2, 3, 4, 5].map((i) => <Skeleton key={i} className="h-11 w-full" />)}
        </div>
      </div>
    );
  }

  if (!products || products.length === 0) {
    return (
      <div className="admin-card py-16 text-center space-y-2">
        <Package className="h-10 w-10 mx-auto text-muted-foreground/25" />
        <p className="text-sm text-muted-foreground">কোনো পণ্য নেই। নতুন পণ্য যোগ করুন।</p>
      </div>
    );
  }

  return (
    <div className="admin-card overflow-hidden">
      <div className="overflow-x-auto">
        <table className="commerce-table">
          <thead>
            <tr>
              <th>পণ্যের নাম</th>
              <th>বিভাগ</th>
              <th>SKU</th>
              <th className="text-right">মূল্য</th>
              <th className="text-right">স্টক</th>
              <th>স্টক অবস্থা</th>
              <th>স্ট্যাটাস</th>
              <th className="text-right">অ্যাকশন</th>
            </tr>
          </thead>
          <tbody>
            {products.map((product) => {
              const firstVariant = product.variants?.[0];
              const totalStock = (product.variants ?? []).reduce((s, v) => s + (v.stock_quantity ?? 0), 0);
              const minThreshold = (product.variants ?? []).reduce((mn, v) => Math.min(mn, v.low_stock_alert ?? 5), 5);
              const sku = firstVariant?.sku ?? "—";
              const price = firstVariant?.price ?? product.base_price;

              return (
                <tr key={product.id}>
                  <td>
                    <Link href={`/products/${product.id}`} className="font-medium text-sm hover:text-primary hover:underline">
                      {product.name}
                    </Link>
                    {product.variants && product.variants.length > 1 && (
                      <span className="ml-1.5 text-[10px] text-muted-foreground">({product.variants.length} ভ্যারিয়েন্ট)</span>
                    )}
                  </td>
                  <td className="text-xs text-muted-foreground">{product.category || "—"}</td>
                  <td className="font-mono text-[11px] text-muted-foreground">{sku}</td>
                  <td className="text-right text-sm font-semibold">{formatCurrency(price)}</td>
                  <td className="text-right">
                    <span className={cn(
                      "text-sm font-bold tabular-nums",
                      totalStock === 0 ? "text-red-600" : totalStock <= minThreshold ? "text-amber-600" : "text-foreground"
                    )}>
                      {totalStock}
                    </span>
                  </td>
                  <td>
                    <StockPill qty={totalStock} threshold={minThreshold} />
                  </td>
                  <td>
                    <span className={cn(
                      "inline-flex px-1.5 py-0.5 rounded text-[11px] font-semibold",
                      product.is_active
                        ? "bg-emerald-100 text-emerald-700 border border-emerald-200"
                        : "bg-slate-100 text-slate-500 border border-slate-200"
                    )}>
                      {product.is_active ? "সক্রিয়" : "নিষ্ক্রিয়"}
                    </span>
                  </td>
                  <td className="text-right">
                    <div className="flex items-center justify-end gap-1">
                      <Link href={`/products/${product.id}/edit`}>
                        <Button variant="ghost" size="sm" className="h-7 w-7 p-0">
                          <Edit2 className="h-3.5 w-3.5" />
                        </Button>
                      </Link>
                      {onDelete && (
                        <Button variant="ghost" size="sm" className="h-7 w-7 p-0 text-destructive hover:text-destructive"
                          onClick={() => onDelete(product.id)}>
                          <Trash2 className="h-3.5 w-3.5" />
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
    </div>
  );
}
