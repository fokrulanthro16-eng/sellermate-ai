"use client";

import { useEffect, useState } from "react";
import { Loader2, Save, Store, Lock, SlidersHorizontal, Sun, Moon, Monitor, Info, Zap } from "lucide-react";
import { useTheme } from "next-themes";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { toast } from "sonner";
import api from "@/lib/api-client";
import { getApiError, cn } from "@/lib/utils";
import { useLang } from "@/contexts/LangContext";

interface MerchantProfile {
  id: string;
  business_name: string;
  owner_name: string;
  phone?: string;
  email: string;
  business_type?: string;
  address?: string;
  district?: string;
  division?: string;
  whatsapp_phone?: string;
  onboarding_completed?: boolean;
}

interface UpdatePayload {
  business_name?: string;
  owner_name?: string;
  address?: string;
  district?: string;
  division?: string;
  whatsapp_phone?: string;
}

export default function SettingsPage() {
  const { t, lang, setLang } = useLang();
  const { theme, setTheme } = useTheme();
  const label = (bn: string, en: string) => lang === "bn" ? bn : en;

  const [mounted, setMounted] = useState(false);
  const [profile, setProfile] = useState<MerchantProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => setMounted(true), []);

  useEffect(() => {
    api.get<{ data: MerchantProfile }>("/auth/me")
      .then((r) => setProfile(r.data.data))
      .catch(() => toast.error(label("প্রোফাইল লোড করা যায়নি", "Failed to load profile")))
      .finally(() => setLoading(false));
  }, []);

  const handleSave = async () => {
    if (!profile) return;
    setSaving(true);
    try {
      const payload: UpdatePayload = {
        business_name:  profile.business_name,
        owner_name:     profile.owner_name,
        address:        profile.address        || undefined,
        district:       profile.district       || undefined,
        division:       profile.division       || undefined,
        whatsapp_phone: profile.whatsapp_phone || undefined,
      };
      await api.patch("/merchant/me", payload);
      toast.success(t("profileUpdated"));
    } catch (e) {
      toast.error(getApiError(e));
    } finally {
      setSaving(false);
    }
  };

  const update = (field: keyof MerchantProfile, value: string) => {
    setProfile((p) => p ? { ...p, [field]: value } : p);
  };

  const THEME_OPTIONS = [
    { value: "light",  icon: Sun,     label: label("আলো", "Light") },
    { value: "dark",   icon: Moon,    label: label("অন্ধকার", "Dark") },
    { value: "system", icon: Monitor, label: label("সিস্টেম", "System") },
  ];

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      {/* Header */}
      <div className="animate-slide-up">
        <h1 className="text-2xl font-bold tracking-tight gradient-text">{t("settingsTitle")}</h1>
        <p className="text-sm text-muted-foreground mt-1">{t("settingsDesc")}</p>
      </div>

      {/* Tabbed layout */}
      <div className="animate-slide-up animation-delay-100">
        <Tabs defaultValue="profile">
          <TabsList className="rounded-xl w-full">
            <TabsTrigger value="profile" className="flex-1 gap-1.5 rounded-lg">
              <Store className="h-3.5 w-3.5" />
              {label("প্রোফাইল", "Profile")}
            </TabsTrigger>
            <TabsTrigger value="security" className="flex-1 gap-1.5 rounded-lg">
              <Lock className="h-3.5 w-3.5" />
              {label("নিরাপত্তা", "Security")}
            </TabsTrigger>
            <TabsTrigger value="preferences" className="flex-1 gap-1.5 rounded-lg">
              <SlidersHorizontal className="h-3.5 w-3.5" />
              {label("পছন্দ", "Preferences")}
            </TabsTrigger>
            <TabsTrigger value="about" className="flex-1 gap-1.5 rounded-lg">
              <Info className="h-3.5 w-3.5" />
              {label("পরিচিতি", "About")}
            </TabsTrigger>
          </TabsList>

          {/* Profile tab */}
          <TabsContent value="profile" className="mt-4">
            <div className="admin-card p-5 space-y-5">
              <div className="flex items-center gap-3 pb-1">
                <div className="h-8 w-8 rounded-lg bg-primary/10 flex items-center justify-center">
                  <Store className="h-4 w-4 text-primary" />
                </div>
                <div>
                  <h3 className="text-sm font-semibold">{t("businessProfile")}</h3>
                  <p className="text-xs text-muted-foreground">{t("businessProfileDesc")}</p>
                </div>
              </div>

              {loading ? (
                <div className="flex items-center justify-center py-10">
                  <Loader2 className="h-7 w-7 animate-spin text-muted-foreground" />
                </div>
              ) : !profile ? (
                <p className="text-center text-muted-foreground py-6">
                  {label("প্রোফাইল লোড করা যায়নি", "Failed to load profile")}
                </p>
              ) : (
                <>
                  {/* Read-only info */}
                  <div className="rounded-xl bg-muted/50 p-3 flex items-center justify-between gap-3">
                    <div>
                      <p className="text-xs text-muted-foreground">
                        {label("ইমেইল (পরিবর্তনযোগ্য নয়)", "Email (read-only)")}
                      </p>
                      <p className="text-sm font-medium">{profile.email}</p>
                    </div>
                    {profile.onboarding_completed && (
                      <Badge variant="secondary" className="text-xs shrink-0">
                        {label("অনবোর্ডড", "Onboarded")}
                      </Badge>
                    )}
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label>{t("businessName")}</Label>
                      <Input
                        value={profile.business_name}
                        onChange={(e) => update("business_name", e.target.value)}
                        placeholder={label("আপনার শপের নাম", "Your shop name")}
                        className="rounded-xl"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>{t("ownerName")}</Label>
                      <Input
                        value={profile.owner_name}
                        onChange={(e) => update("owner_name", e.target.value)}
                        placeholder={label("পূর্ণ নাম", "Full name")}
                        className="rounded-xl"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>{t("districtOptional")}</Label>
                      <Input
                        value={profile.district ?? ""}
                        onChange={(e) => update("district", e.target.value)}
                        placeholder={t("districtPlaceholder")}
                        className="rounded-xl"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>{label("বিভাগ", "Division")}</Label>
                      <Input
                        value={profile.division ?? ""}
                        onChange={(e) => update("division", e.target.value)}
                        placeholder={t("districtPlaceholder")}
                        className="rounded-xl"
                      />
                    </div>
                    <div className="sm:col-span-2 space-y-2">
                      <Label>{label("ঠিকানা", "Address")}</Label>
                      <Input
                        value={profile.address ?? ""}
                        onChange={(e) => update("address", e.target.value)}
                        placeholder={label("সম্পূর্ণ ঠিকানা", "Full address")}
                        className="rounded-xl"
                      />
                    </div>
                    <div className="sm:col-span-2 space-y-2">
                      <Label>{label("হোয়াটসঅ্যাপ নম্বর", "WhatsApp Number")}</Label>
                      <Input
                        value={profile.whatsapp_phone ?? ""}
                        onChange={(e) => update("whatsapp_phone", e.target.value)}
                        placeholder="+8801XXXXXXXXX"
                        className="rounded-xl"
                      />
                    </div>
                  </div>

                  <Button onClick={handleSave} disabled={saving} className="gap-2 rounded-xl">
                    {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
                    {saving ? t("saving") : t("save")}
                  </Button>
                </>
              )}
            </div>
          </TabsContent>

          {/* Security tab */}
          <TabsContent value="security" className="mt-4">
            <div className="admin-card p-5 space-y-4">
              <div className="flex items-center gap-3">
                <div className="h-8 w-8 rounded-lg bg-muted flex items-center justify-center">
                  <Lock className="h-4 w-4 text-muted-foreground" />
                </div>
                <div>
                  <h3 className="text-sm font-semibold">{t("security")}</h3>
                  <p className="text-xs text-muted-foreground">
                    {label("পাসওয়ার্ড ও অ্যাকাউন্ট সুরক্ষা", "Password & account security")}
                  </p>
                </div>
              </div>
              <div className="rounded-xl bg-muted/50 p-4 text-center">
                <p className="text-sm text-muted-foreground">
                  {label("পাসওয়ার্ড পরিবর্তনের সুবিধা শীঘ্রই যোগ হবে।", "Password change feature is coming soon.")}
                </p>
              </div>
            </div>
          </TabsContent>

          {/* Preferences tab */}
          <TabsContent value="preferences" className="mt-4">
            <div className="admin-card p-5 space-y-6">
              <div className="flex items-center gap-3">
                <div className="h-8 w-8 rounded-lg bg-primary/10 flex items-center justify-center">
                  <SlidersHorizontal className="h-4 w-4 text-primary" />
                </div>
                <div>
                  <h3 className="text-sm font-semibold">{label("অ্যাপ পছন্দ", "App Preferences")}</h3>
                  <p className="text-xs text-muted-foreground">
                    {label("ভাষা ও থিম পরিবর্তন করুন", "Change language and theme")}
                  </p>
                </div>
              </div>

              {/* Language toggle */}
              <div className="space-y-2">
                <Label className="text-sm">{label("ভাষা", "Language")}</Label>
                <div className="flex items-center gap-2">
                  {(["bn", "en"] as const).map((l) => (
                    <button
                      key={l}
                      onClick={() => setLang(l)}
                      className={cn(
                        "flex-1 py-2 rounded-xl text-sm font-medium border transition-all duration-200",
                        lang === l
                          ? "bg-primary text-primary-foreground border-primary"
                          : "bg-background border-input hover:bg-accent text-muted-foreground"
                      )}
                    >
                      {l === "bn" ? "বাংলা" : "English"}
                    </button>
                  ))}
                </div>
              </div>

              {/* Theme toggle */}
              <div className="space-y-2">
                <Label className="text-sm">{label("থিম", "Theme")}</Label>
                <div className="flex items-center gap-2">
                  {mounted ? THEME_OPTIONS.map((opt) => {
                    const Icon = opt.icon;
                    return (
                      <button
                        key={opt.value}
                        onClick={() => setTheme(opt.value)}
                        className={cn(
                          "flex-1 flex items-center justify-center gap-1.5 py-2 rounded-xl text-sm font-medium border transition-all duration-200",
                          theme === opt.value
                            ? "bg-primary text-primary-foreground border-primary"
                            : "bg-background border-input hover:bg-accent text-muted-foreground"
                        )}
                      >
                        <Icon className="h-3.5 w-3.5" />
                        {opt.label}
                      </button>
                    );
                  }) : THEME_OPTIONS.map((opt) => (
                    <div key={opt.value} className="flex-1 h-9 rounded-xl bg-muted/50 animate-pulse" />
                  ))}
                </div>
              </div>
            </div>
          </TabsContent>
          {/* About tab */}
          <TabsContent value="about" className="mt-4">
            <div className="admin-card p-5 space-y-5">
              <div className="flex items-center gap-3">
                <div className="h-8 w-8 rounded-lg bg-violet-500/10 flex items-center justify-center">
                  <Zap className="h-4 w-4 text-violet-400" />
                </div>
                <div>
                  <h3 className="text-sm font-semibold">{label("সফটওয়্যার পরিচিতি", "About SellerMate")}</h3>
                  <p className="text-xs text-muted-foreground">{label("সংস্করণ ও মোড তথ্য", "Version and mode information")}</p>
                </div>
              </div>

              {/* Beta badge */}
              <div className="rounded-xl bg-violet-500/10 border border-violet-500/20 p-4 flex items-center gap-3">
                <div className="h-10 w-10 rounded-lg bg-violet-500/20 flex items-center justify-center shrink-0">
                  <Zap className="h-5 w-5 text-violet-400" />
                </div>
                <div>
                  <div className="flex items-center gap-2 mb-0.5">
                    <span className="text-sm font-bold text-foreground">SellerMate AI</span>
                    <span className="px-2 py-0.5 rounded-full bg-violet-500/20 text-violet-300 text-[10px] font-bold border border-violet-500/30">
                      BETA
                    </span>
                  </div>
                  <p className="text-xs text-muted-foreground">
                    {label(
                      "বাংলাদেশি ই-কমার্স বিক্রেতাদের জন্য সম্পূর্ণ AI সমাধান",
                      "Complete AI solution for Bangladeshi e-commerce sellers"
                    )}
                  </p>
                </div>
              </div>

              {/* Info rows */}
              <div className="space-y-3 text-sm">
                {[
                  { label: label("সংস্করণ", "Version"),    value: "1.0.0" },
                  { label: label("ফেজ", "Phase"),           value: "11.5 — Beta Test Mode" },
                  { label: label("অ্যাপ মোড", "App Mode"),  value: "Beta (Safe Mode)" },
                  { label: label("পেমেন্ট", "Payments"),    value: label("স্যান্ডবক্স / মক", "Sandbox / Mock") },
                  { label: label("কুরিয়ার", "Courier"),     value: label("সিমুলেটেড", "Simulated") },
                  { label: label("AI প্রদানকারী", "AI"),    value: label("মক ফলব্যাক সক্রিয়", "Mock fallback active") },
                  { label: label("স্টোরেজ", "Storage"),     value: label("লোকাল প্রিভিউ", "Local preview") },
                ].map(({ label: l, value }) => (
                  <div key={l} className="flex items-center justify-between py-2 border-b border-border/50 last:border-0">
                    <span className="text-muted-foreground">{l}</span>
                    <span className="font-medium text-foreground text-right">{value}</span>
                  </div>
                ))}
              </div>

              <div className="rounded-lg bg-amber-500/10 border border-amber-500/20 p-3 text-xs text-amber-600 dark:text-amber-400">
                {label(
                  "বেটা মোডে কোনো বাস্তব অর্থ লেনদেন, কুরিয়ার বুকিং বা বাহ্যিক চার্জ হয় না।",
                  "In Beta Mode, no real money moves, no real courier bookings, no external charges."
                )}
              </div>
            </div>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
