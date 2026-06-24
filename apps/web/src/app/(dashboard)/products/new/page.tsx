"use client";

import { useRouter } from "next/navigation";
import { ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import ProductForm from "@/components/products/ProductForm";
import { useCreateProduct } from "@/hooks/useProducts";

export default function NewProductPage() {
  const router = useRouter();
  const createProduct = useCreateProduct();
  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div className="flex items-center gap-3">
        <Button variant="ghost" size="icon" onClick={() => router.back()}><ArrowLeft className="h-4 w-4" /></Button>
        <h1 className="text-2xl font-bold">নতুন পণ্য</h1>
      </div>
      <Card>
        <CardHeader><CardTitle className="text-base">পণ্যের তথ্য</CardTitle></CardHeader>
        <CardContent>
          <ProductForm loading={createProduct.isPending} onSubmit={async (data) => {
            const product = await createProduct.mutateAsync(data);
            router.push(`/products/${product.id}`);
          }} />
        </CardContent>
      </Card>
    </div>
  );
}
