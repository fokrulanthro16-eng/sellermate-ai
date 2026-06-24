import Link from "next/link";
import { Package, Edit2, Trash2 } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { formatCurrency } from "@/lib/utils";
import type { Product } from "@/types";

interface ProductCardProps {
  product: Product;
  onDelete?: (id: string) => void;
}

export default function ProductCard({ product, onDelete }: ProductCardProps) {
  return (
    <Card className="hover:shadow-md transition-shadow">
      <CardContent className="p-4">
        <div className="flex items-start gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10 shrink-0">
            <Package className="h-5 w-5 text-primary" />
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-start justify-between gap-2">
              <Link href={`/products/${product.id}`} className="min-w-0">
                <p className="font-semibold text-sm hover:text-primary truncate">{product.name}</p>
              </Link>
              <Badge variant={product.is_active ? "success" : "secondary"} className="shrink-0">
                {product.is_active ? "সক্রিয়" : "নিষ্ক্রিয়"}
              </Badge>
            </div>
            <p className="text-xs text-muted-foreground mt-0.5">{product.category}</p>
            <div className="flex items-center justify-between mt-2">
              <div>
                <p className="text-sm font-bold text-primary">{formatCurrency(product.base_price)}</p>
                <p className="text-xs text-muted-foreground">{product.variants?.length || 0} ভ্যারিয়েন্ট</p>
              </div>
              <div className="flex gap-1">
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
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
