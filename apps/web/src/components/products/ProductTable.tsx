"use client";

import Link from "next/link";
import { Edit2, Trash2, Package } from "lucide-react";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { formatCurrency } from "@/lib/utils";
import type { Product } from "@/types";

interface ProductTableProps {
  products?: Product[];
  loading?: boolean;
  onDelete?: (id: string) => void;
}

export default function ProductTable({ products, loading, onDelete }: ProductTableProps) {
  if (loading) {
    return (
      <div className="space-y-2">
        {[1, 2, 3, 4, 5].map((i) => <Skeleton key={i} className="h-14 w-full" />)}
      </div>
    );
  }

  if (!products || products.length === 0) {
    return (
      <div className="text-center py-12 text-muted-foreground">
        <Package className="h-12 w-12 mx-auto mb-3 opacity-30" />
        <p>কোনো পণ্য নেই। নতুন পণ্য যোগ করুন।</p>
      </div>
    );
  }

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>পণ্যের নাম</TableHead>
          <TableHead>বিভাগ</TableHead>
          <TableHead className="text-right">মূল্য</TableHead>
          <TableHead className="text-center">ভ্যারিয়েন্ট</TableHead>
          <TableHead>অবস্থা</TableHead>
          <TableHead className="text-right">অ্যাকশন</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {products.map((product) => (
          <TableRow key={product.id}>
            <TableCell>
              <Link href={`/products/${product.id}`} className="font-medium text-sm hover:text-primary">
                {product.name}
              </Link>
            </TableCell>
            <TableCell className="text-sm text-muted-foreground">{product.category}</TableCell>
            <TableCell className="text-right text-sm font-semibold">{formatCurrency(product.base_price)}</TableCell>
            <TableCell className="text-center text-sm">{product.variants?.length || 0}</TableCell>
            <TableCell>
              <Badge variant={product.is_active ? "success" : "secondary"}>
                {product.is_active ? "সক্রিয়" : "নিষ্ক্রিয়"}
              </Badge>
            </TableCell>
            <TableCell className="text-right">
              <div className="flex items-center justify-end gap-1">
                <Link href={`/products/${product.id}/edit`}>
                  <Button variant="ghost" size="icon" className="h-8 w-8">
                    <Edit2 className="h-3.5 w-3.5" />
                  </Button>
                </Link>
                {onDelete && (
                  <Button variant="ghost" size="icon" className="h-8 w-8 text-destructive hover:text-destructive"
                    onClick={() => onDelete(product.id)}>
                    <Trash2 className="h-3.5 w-3.5" />
                  </Button>
                )}
              </div>
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
