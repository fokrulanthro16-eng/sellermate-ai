"use client";

import { useRouter } from "next/navigation";
import { ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import AdjustmentForm from "@/components/inventory/AdjustmentForm";

export default function AdjustmentsPage() {
  const router = useRouter();
  return (
    <div className="max-w-lg mx-auto space-y-6">
      <div className="flex items-center gap-3">
        <Button variant="ghost" size="icon" onClick={() => router.back()}><ArrowLeft className="h-4 w-4" /></Button>
        <h1 className="text-2xl font-bold">স্টক সমন্বয়</h1>
      </div>
      <Card>
        <CardHeader><CardTitle className="text-base">নতুন সমন্বয়</CardTitle></CardHeader>
        <CardContent>
          <AdjustmentForm onSuccess={() => router.push("/inventory")} />
        </CardContent>
      </Card>
    </div>
  );
}
