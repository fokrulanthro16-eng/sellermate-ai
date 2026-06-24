"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { toast } from "sonner";
import { Loader2, Zap, FlaskConical, CheckCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Separator } from "@/components/ui/separator";
import api from "@/lib/api-client";
import { setTokens } from "@/lib/auth";
import { getApiError } from "@/lib/utils";
import { enterDemoMode } from "@/lib/demo-auth";
import type { LoginResponse, ApiResponse } from "@/types";

const businessTypes = [
  { value: "FASHION_CLOTHING", label: "ফ্যাশন ও পোশাক" },
  { value: "FOOD_BEVERAGE", label: "খাদ্য ও পানীয়" },
  { value: "ELECTRONICS", label: "ইলেকট্রনিক্স" },
  { value: "HOME_DECOR", label: "গৃহস্থালি পণ্য" },
  { value: "BEAUTY_COSMETICS", label: "সৌন্দর্য পণ্য" },
  { value: "HANDICRAFTS", label: "হস্তশিল্প" },
  { value: "BOOKS_STATIONERY", label: "বই ও স্টেশনারি" },
  { value: "SPORTS_FITNESS", label: "খেলাধুলা ও ফিটনেস" },
  { value: "OTHER", label: "অন্যান্য" },
];

const perks = [
  "ফ্রি অ্যাকাউন্ট, ক্রেডিট কার্ড লাগবে না",
  "সীমাহীন পণ্য ও অর্ডার ম্যানেজমেন্ট",
  "রিয়েল-টাইম এআই বিশ্লেষণ ও সুরক্ষা",
];

const schema = z.object({
  business_name: z.string().min(2, "ব্যবসার নাম আবশ্যক"),
  owner_name: z.string().min(2, "মালিকের নাম আবশ্যক"),
  phone: z.string().min(10, "সঠিক ফোন নম্বর দিন"),
  email: z.string().email("সঠিক ইমেইল ঠিকানা দিন"),
  password: z.string().min(8, "পাসওয়ার্ড কমপক্ষে ৮ অক্ষর হতে হবে"),
  business_type: z.string().min(1, "ব্যবসার ধরন নির্বাচন করুন"),
});
type FormData = z.infer<typeof schema>;

export default function RegisterPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [demoLoading, setDemoLoading] = useState(false);
  const [businessType, setBusinessType] = useState("");

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

  const { register, handleSubmit, setValue, formState: { errors } } = useForm<FormData>({
    resolver: zodResolver(schema),
  });

  const onSubmit = async (data: FormData) => {
    setLoading(true);
    try {
      await api.post("/auth/register", data);
      const res = await api.post<ApiResponse<LoginResponse>>("/auth/login", {
        identifier: data.phone,
        password: data.password,
      });
      const { tokens } = res.data.data;
      setTokens(tokens.access_token, tokens.refresh_token);
      toast.success("নিবন্ধন সফল হয়েছে!");
      router.push("/dashboard");
    } catch (e) {
      toast.error(getApiError(e));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex">
      {/* Left panel */}
      <div className="hidden lg:flex lg:flex-1 flex-col justify-between p-12 bg-gradient-to-br from-violet-600 via-primary to-blue-700 text-primary-foreground relative overflow-hidden">
        <div className="absolute inset-0 pointer-events-none">
          <div className="absolute -top-32 -right-32 w-96 h-96 rounded-full bg-white/5" />
          <div className="absolute -bottom-20 -left-20 w-72 h-72 rounded-full bg-white/5" />
        </div>

        <div className="relative z-10">
          <div className="flex items-center gap-3 mb-12">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-white/20">
              <Zap className="h-5 w-5" />
            </div>
            <span className="text-xl font-bold">SellerMate AI</span>
          </div>

          <h1 className="text-4xl font-bold leading-tight mb-4">
            আপনার ব্যবসার<br />
            ডিজিটাল যাত্রা শুরু করুন
          </h1>
          <p className="text-primary-foreground/70 text-lg leading-relaxed max-w-sm">
            মাত্র ২ মিনিটে নিবন্ধন করুন এবং বাংলাদেশের সেরা ই-কমার্স AI প্ল্যাটফর্ম ব্যবহার শুরু করুন।
          </p>
        </div>

        <div className="relative z-10 space-y-3">
          {perks.map((perk) => (
            <div key={perk} className="flex items-center gap-3">
              <CheckCircle className="h-4 w-4 shrink-0 text-green-300" />
              <p className="text-sm text-primary-foreground/80">{perk}</p>
            </div>
          ))}
        </div>

        <p className="relative z-10 text-xs text-primary-foreground/40">
          © 2026 SellerMate AI · বাংলাদেশ ই-কমার্স AI পরিচালনা
        </p>
      </div>

      {/* Right panel — form */}
      <div className="flex flex-1 flex-col justify-center px-6 py-10 sm:px-12 lg:max-w-md lg:flex-none xl:max-w-lg bg-background overflow-y-auto">
        <div className="mx-auto w-full max-w-sm">
          <div className="flex items-center gap-2 mb-6 lg:hidden">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-primary">
              <Zap className="h-5 w-5 text-primary-foreground" />
            </div>
            <span className="text-xl font-bold">SellerMate AI</span>
          </div>

          <div className="mb-7">
            <h2 className="text-2xl font-bold text-foreground">নতুন অ্যাকাউন্ট</h2>
            <p className="mt-1 text-sm text-muted-foreground">আপনার ব্যবসার তথ্য দিয়ে শুরু করুন।</p>
          </div>

          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1.5">
                <Label htmlFor="business_name" className="text-sm font-medium">ব্যবসার নাম</Label>
                <Input id="business_name" className="h-10" placeholder="শপের নাম" {...register("business_name")} />
                {errors.business_name && <p className="text-xs text-destructive">{errors.business_name.message}</p>}
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="owner_name" className="text-sm font-medium">মালিকের নাম</Label>
                <Input id="owner_name" className="h-10" placeholder="আপনার নাম" {...register("owner_name")} />
                {errors.owner_name && <p className="text-xs text-destructive">{errors.owner_name.message}</p>}
              </div>
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="business_type" className="text-sm font-medium">ব্যবসার ধরন</Label>
              <Select value={businessType} onValueChange={(v) => { setBusinessType(v); setValue("business_type", v); }}>
                <SelectTrigger className="h-10">
                  <SelectValue placeholder="ধরন নির্বাচন করুন" />
                </SelectTrigger>
                <SelectContent>
                  {businessTypes.map((bt) => (
                    <SelectItem key={bt.value} value={bt.value}>{bt.label}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
              {errors.business_type && <p className="text-xs text-destructive">{errors.business_type.message}</p>}
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="phone" className="text-sm font-medium">ফোন নম্বর</Label>
              <Input id="phone" className="h-10" placeholder="+8801XXXXXXXXX" {...register("phone")} />
              {errors.phone && <p className="text-xs text-destructive">{errors.phone.message}</p>}
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="email" className="text-sm font-medium">ইমেইল</Label>
              <Input id="email" type="email" className="h-10" placeholder="email@example.com" {...register("email")} />
              {errors.email && <p className="text-xs text-destructive">{errors.email.message}</p>}
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="password" className="text-sm font-medium">পাসওয়ার্ড</Label>
              <Input id="password" type="password" className="h-10" placeholder="কমপক্ষে ৮ অক্ষর" {...register("password")} />
              {errors.password && <p className="text-xs text-destructive">{errors.password.message}</p>}
            </div>

            <Button type="submit" className="w-full h-11 text-sm font-semibold" disabled={loading || demoLoading}>
              {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              অ্যাকাউন্ট তৈরি করুন
            </Button>
          </form>

          <div className="mt-4 flex items-center gap-3">
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
            {demoLoading ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <FlaskConical className="mr-2 h-4 w-4" />}
            ডেমো হিসেবে ঢুকুন
          </Button>

          <p className="mt-5 text-center text-sm text-muted-foreground">
            ইতিমধ্যে অ্যাকাউন্ট আছে?{" "}
            <Link href="/login" className="text-primary font-semibold hover:underline">লগইন করুন</Link>
          </p>
        </div>
      </div>
    </div>
  );
}
