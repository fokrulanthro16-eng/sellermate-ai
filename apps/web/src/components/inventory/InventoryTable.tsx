"use client";

import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Skeleton } from "@/components/ui/skeleton";
import StockBadge from "@/components/inventory/StockBadge";
import type { InventoryItem } from "@/types";

interface InventoryTableProps {
  items?: InventoryItem[];
  loading?: boolean;
}

export default function InventoryTable({ items, loading }: InventoryTableProps) {
  if (loading) {
    return (
      <div className="space-y-2">
        {[1, 2, 3, 4, 5].map((i) => <Skeleton key={i} className="h-12 w-full" />)}
      </div>
    );
  }

  if (!items || items.length === 0) {
    return (
      <div className="text-center py-12 text-muted-foreground">
        <p>কোনো পণ্য পাওয়া যায়নি</p>
      </div>
    );
  }

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>পণ্য / ভ্যারিয়েন্ট</TableHead>
          <TableHead>SKU</TableHead>
          <TableHead className="text-right">স্টক</TableHead>
          <TableHead className="text-right">সতর্কতা সীমা</TableHead>
          <TableHead>অবস্থা</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {items.map((item) => (
          <TableRow key={item.variant_id}>
            <TableCell>
              <div>
                <p className="font-medium text-sm">{item.product_name}</p>
                <p className="text-xs text-muted-foreground">{item.variant_name}</p>
              </div>
            </TableCell>
            <TableCell className="text-sm font-mono text-muted-foreground">{item.sku}</TableCell>
            <TableCell className="text-right font-semibold">{item.stock_quantity}</TableCell>
            <TableCell className="text-right text-muted-foreground">{item.low_stock_alert}</TableCell>
            <TableCell>
              <StockBadge quantity={item.stock_quantity} threshold={item.low_stock_alert} />
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
