"use client";

import { useRouter } from "next/navigation";
import { ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import OrderForm from "@/components/orders/OrderForm";

export default function NewOrderPage() {
  const router = useRouter();
  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div className="flex items-center gap-3">
        <Button variant="ghost" size="icon" onClick={() => router.back()}><ArrowLeft className="h-4 w-4" /></Button>
        <h1 className="text-2xl font-bold">নতুন অর্ডার</h1>
      </div>
      <Card>
        <CardHeader><CardTitle className="text-base">অর্ডারের তথ্য</CardTitle></CardHeader>
        <CardContent>
          <OrderForm onSuccess={() => router.push("/orders")} />
        </CardContent>
      </Card>
    </div>
  );
}
