"use client";

import { useParams, useRouter } from "next/navigation";
import { ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import ProductForm from "@/components/products/ProductForm";
import { useProduct, useUpdateProduct } from "@/hooks/useProducts";

export default function EditProductPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const { data: product, isLoading } = useProduct(id);
  const updateProduct = useUpdateProduct();

  if (isLoading) return <div className="max-w-2xl mx-auto space-y-4"><Skeleton className="h-8 w-48" /><Skeleton className="h-64 w-full" /></div>;
  if (!product) return <p className="text-center text-muted-foreground py-12">পণ্য পাওয়া যায়নি</p>;

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div className="flex items-center gap-3">
        <Button variant="ghost" size="icon" onClick={() => router.back()}><ArrowLeft className="h-4 w-4" /></Button>
        <h1 className="text-2xl font-bold">পণ্য সম্পাদনা</h1>
      </div>
      <Card>
        <CardHeader><CardTitle className="text-base">{product.name}</CardTitle></CardHeader>
        <CardContent>
          <ProductForm product={product} loading={updateProduct.isPending} onSubmit={async (data) => {
            await updateProduct.mutateAsync({ id, ...data });
            router.push(`/products/${id}`);
          }} />
        </CardContent>
      </Card>
    </div>
  );
}
