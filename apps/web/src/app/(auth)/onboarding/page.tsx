"use client";

import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { CheckCircle2, Zap } from "lucide-react";

export default function OnboardingPage() {
  const router = useRouter();
  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100 px-4">
      <Card className="w-full max-w-md shadow-lg">
        <CardHeader className="text-center">
          <div className="flex justify-center mb-2">
            <div className="flex h-12 w-12 items-center justify-center rounded-full bg-green-100">
              <CheckCircle2 className="h-7 w-7 text-green-600" />
            </div>
          </div>
          <CardTitle>অ্যাকাউন্ট সেটআপ সম্পন্ন!</CardTitle>
        </CardHeader>
        <CardContent className="text-center space-y-4">
          <p className="text-muted-foreground">
            আপনার SellerMate AI অ্যাকাউন্ট প্রস্তুত। এখন ড্যাশবোর্ড থেকে পণ্য, অর্ডার এবং গ্রাহক পরিচালনা শুরু করুন।
          </p>
          <div className="flex items-center justify-center gap-2">
            <Zap className="h-4 w-4 text-primary" />
            <span className="text-sm text-primary font-medium">AI-powered insights সক্রিয়</span>
          </div>
          <Button className="w-full" onClick={() => router.push("/dashboard")}>
            ড্যাশবোর্ডে যান
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
