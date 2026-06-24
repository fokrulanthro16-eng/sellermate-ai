"use client";

import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, Edit2, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import VariantEditor from "@/components/products/VariantEditor";
import { useProduct, useDeleteProduct } from "@/hooks/useProducts";
import { formatCurrency } from "@/lib/utils";

export default function ProductDetailPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const { data: product, isLoading } = useProduct(id);
  const deleteProduct = useDeleteProduct();

  if (isLoading) return <div className="max-w-3xl mx-auto space-y-4"><Skeleton className="h-8 w-48" /><Skeleton className="h-64 w-full" /></div>;
  if (!product) return <p className="text-center text-muted-foreground py-12">পণ্য পাওয়া যায়নি</p>;

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div className="flex items-center justify-between gap-3 flex-wrap">
        <div className="flex items-center gap-3">
          <Button variant="ghost" size="icon" onClick={() => router.back()}><ArrowLeft className="h-4 w-4" /></Button>
          <h1 className="text-2xl font-bold">{product.name}</h1>
        </div>
        <div className="flex gap-2">
          <Link href={`/products/${id}/edit`}><Button variant="outline" size="sm"><Edit2 className="h-4 w-4 mr-1" /> সম্পাদনা</Button></Link>
          <Button variant="destructive" size="sm" disabled={deleteProduct.isPending}
            onClick={async () => { if (confirm("এই পণ্য মুছে ফেলবেন?")) { await deleteProduct.mutateAsync(id); router.push("/products"); } }}>
            <Trash2 className="h-4 w-4 mr-1" /> মুছুন
          </Button>
        </div>
      </div>
      <Card>
        <CardHeader><CardTitle className="text-base">পণ্যের বিবরণ</CardTitle></CardHeader>
        <CardContent className="grid grid-cols-2 gap-4 text-sm">
          <div><p className="text-muted-foreground">বিভাগ</p><p className="font-medium">{product.category}</p></div>
          <div><p className="text-muted-foreground">মূল মূল্য</p><p className="font-medium">{formatCurrency(product.base_price)}</p></div>
          <div><p className="text-muted-foreground">অবস্থা</p><Badge variant={product.is_active ? "success" : "secondary"}>{product.is_active ? "সক্রিয়" : "নিষ্ক্রিয়"}</Badge></div>
          {product.description && <div className="col-span-2"><p className="text-muted-foreground">বিবরণ</p><p>{product.description}</p></div>}
        </CardContent>
      </Card>
      <VariantEditor product={product} />
    </div>
  );
}
