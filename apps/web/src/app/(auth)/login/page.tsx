"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { toast } from "sonner";
import { Loader2, Zap, FlaskConical, TrendingUp, Shield, BarChart3 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import api from "@/lib/api-client";
import { setTokens } from "@/lib/auth";
import { getApiError } from "@/lib/utils";
import { enterDemoMode } from "@/lib/demo-auth";
import type { LoginResponse, ApiResponse } from "@/types";

const schema = z.object({
  identifier: z.string().min(1, "ফোন নম্বর বা ইমেইল আবশ্যক"),
  password: z.string().min(6, "পাসওয়ার্ড কমপক্ষে ৬ অক্ষর হতে হবে"),
});
type FormData = z.infer<typeof schema>;

const features = [
  { icon: TrendingUp, title: "রিয়েল-টাইম বিশ্লেষণ", desc: "বিক্রয়, অর্ডার ও রাজস্বের সম্পূর্ণ চিত্র" },
  { icon: Shield, title: "এআই ফ্রড সুরক্ষা", desc: "সন্দেহজনক অর্ডার স্বয়ংক্রিয়ভাবে চিহ্নিত করুন" },
  { icon: BarChart3, title: "কৌশলগত এআই", desc: "স্মার্ট সিদ্ধান্ত নিন ডেটার ভিত্তিতে" },
];

export default function LoginPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [demoLoading, setDemoLoading] = useState(false);

  const handleDemoAccess = async () => {
    setDemoLoading(true);
    try {
      await enterDemoMode();
      toast.success("ডেমো মোডে স্বাগতম!");
      router.push("/dashboard");
    } catch (e) {
      toast.error("ডেমো অ্যাক্সেস ব্যর্থ হয়েছে: " + getApiError(e));
    } finally {
      setDemoLoading(false);
    }
  };

  const { register, handleSubmit, formState: { errors } } = useForm<FormData>({
    resolver: zodResolver(schema),
  });

  const onSubmit = async (data: FormData) => {
    setLoading(true);
    try {
      const res = await api.post<ApiResponse<LoginResponse>>("/auth/login", data);
      const { tokens } = res.data.data;
      setTokens(tokens.access_token, tokens.refresh_token);
      toast.success("লগইন সফল হয়েছে!");
      router.push("/dashboard");
    } catch (e) {
      toast.error(getApiError(e));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex">
      {/* Left panel — brand & features */}
      <div className="hidden lg:flex lg:flex-1 flex-col justify-between p-12 bg-gradient-to-br from-primary via-primary/90 to-blue-700 text-primary-foreground relative overflow-hidden">
        {/* Background decoration */}
        <div className="absolute inset-0 pointer-events-none">
          <div className="absolute -top-32 -right-32 w-96 h-96 rounded-full bg-white/5" />
          <div className="absolute -bottom-20 -left-20 w-72 h-72 rounded-full bg-white/5" />
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] rounded-full bg-white/[0.03]" />
        </div>

        <div className="relative z-10">
          <div className="flex items-center gap-3 mb-12">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-white/20 backdrop-blur-sm">
              <Zap className="h-5 w-5" />
            </div>
            <span className="text-xl font-bold tracking-tight">SellerMate AI</span>
          </div>

          <h1 className="text-4xl font-bold leading-tight mb-4">
            বাংলাদেশি ই-কমার্সের<br />
            সেরা এআই সহকারী
          </h1>
          <p className="text-primary-foreground/70 text-lg leading-relaxed max-w-sm">
            আপনার ফেসবুক, ইনস্টাগ্রাম ও হোয়াটসঅ্যাপ শপের সম্পূর্ণ ব্যবস্থাপনা একটি প্ল্যাটফর্মে।
          </p>
        </div>

        <div className="relative z-10 space-y-4">
          {features.map((f) => (
            <div key={f.title} className="flex items-start gap-4 p-4 rounded-2xl bg-white/10 backdrop-blur-sm border border-white/10">
              <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-white/20">
                <f.icon className="h-4 w-4" />
              </div>
              <div>
                <p className="font-semibold text-sm">{f.title}</p>
                <p className="text-xs text-primary-foreground/60 mt-0.5">{f.desc}</p>
              </div>
            </div>
          ))}
        </div>

        <p className="relative z-10 text-xs text-primary-foreground/40">
          © 2026 SellerMate AI · বাংলাদেশ ই-কমার্স AI পরিচালনা
        </p>
      </div>

      {/* Right panel — form */}
      <div className="flex flex-1 flex-col justify-center px-6 py-12 sm:px-12 lg:max-w-md lg:flex-none xl:max-w-lg bg-background">
        <div className="mx-auto w-full max-w-sm">
          {/* Mobile logo */}
          <div className="flex items-center gap-2 mb-8 lg:hidden">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-primary">
              <Zap className="h-5 w-5 text-primary-foreground" />
            </div>
            <span className="text-xl font-bold">SellerMate AI</span>
          </div>

          <div className="mb-8">
            <h2 className="text-2xl font-bold text-foreground">স্বাগতম ফিরে!</h2>
            <p className="mt-1 text-sm text-muted-foreground">আপনার অ্যাকাউন্টে সাইন ইন করুন।</p>
          </div>

          <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
            <div className="space-y-1.5">
              <Label htmlFor="identifier" className="text-sm font-medium">ফোন নম্বর বা ইমেইল</Label>
              <Input
                id="identifier"
                placeholder="+8801XXXXXXXXX বা email@example.com"
                className="h-11"
                {...register("identifier")}
              />
              {errors.identifier && (
                <p className="text-xs text-destructive">{errors.identifier.message}</p>
              )}
            </div>

            <div className="space-y-1.5">
              <div className="flex items-center justify-between">
                <Label htmlFor="password" className="text-sm font-medium">পাসওয়ার্ড</Label>
                <Link href="/forgot-password" className="text-xs text-primary hover:underline">
                  পাসওয়ার্ড ভুলে গেছেন?
                </Link>
              </div>
              <Input
                id="password"
                type="password"
                placeholder="••••••••"
                className="h-11"
                {...register("password")}
              />
              {errors.password && (
                <p className="text-xs text-destructive">{errors.password.message}</p>
              )}
            </div>

            <Button type="submit" className="w-full h-11 text-sm font-semibold" disabled={loading || demoLoading}>
              {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              লগইন করুন
            </Button>
          </form>

          <div className="mt-5 flex items-center gap-3">
            <Separator className="flex-1" />
            <span className="text-xs text-muted-foreground px-1">অথবা</span>
            <Separator className="flex-1" />
          </div>

          <Button
            variant="outline"
            className="w-full mt-4 h-11 text-sm font-semibold border-amber-300 text-amber-700 hover:bg-amber-50 hover:text-amber-800 dark:border-amber-700 dark:text-amber-400 dark:hover:bg-amber-950/30"
            onClick={handleDemoAccess}
            disabled={demoLoading || loading}
          >
            {demoLoading
              ? <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              : <FlaskConical className="mr-2 h-4 w-4" />}
            ডেমো হিসেবে ঢুকুন
          </Button>

          <p className="mt-6 text-center text-sm text-muted-foreground">
            নতুন ব্যবহারকারী?{" "}
            <Link href="/register" className="text-primary font-semibold hover:underline">
              নিবন্ধন করুন
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
