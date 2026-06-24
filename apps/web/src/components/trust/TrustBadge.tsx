"use client";

import { Shield, ShieldCheck, ShieldOff } from "lucide-react";
import { cn } from "@/lib/utils";
import { useLang } from "@/contexts/LangContext";

interface TrustBadgeProps {
  score: number;
  size?: "sm" | "md" | "lg";
  showScore?: boolean;
}

export default function TrustBadge({ score, size = "md", showScore = false }: TrustBadgeProps) {
  const { lang } = useLang();
  const l = (bn: string, en: string) => lang === "bn" ? bn : en;

  let Icon: React.ElementType;
  let label: string;
  let cls: string;

  if (score >= 80) {
    Icon = ShieldCheck;
    label = l("বিশ্বস্ত বিক্রেতা", "Trusted Seller");
    cls = "bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-950/30 dark:text-emerald-400 dark:border-emerald-800";
  } else if (score >= 60) {
    Icon = Shield;
    label = l("যাচাইকৃত বিক্রেতা", "Verified Seller");
    cls = "bg-blue-50 text-blue-700 border-blue-200 dark:bg-blue-950/30 dark:text-blue-400 dark:border-blue-800";
  } else if (score >= 1) {
    Icon = Shield;
    label = l("ট্রাস্ট বাড়ানো হচ্ছে", "Building Trust");
    cls = "bg-amber-50 text-amber-700 border-amber-200 dark:bg-amber-950/30 dark:text-amber-400 dark:border-amber-800";
  } else {
    Icon = ShieldOff;
    label = l("পর্যাপ্ত ডেটা নেই", "Not enough data");
    cls = "bg-muted text-muted-foreground border-border";
  }

  const sizes = {
    sm: { wrapper: "px-2 py-0.5 text-[11px] gap-1", icon: "h-3 w-3" },
    md: { wrapper: "px-2.5 py-1 text-xs gap-1.5", icon: "h-3.5 w-3.5" },
    lg: { wrapper: "px-3 py-1.5 text-sm gap-2", icon: "h-4 w-4" },
  };

  return (
    <div className={cn("inline-flex items-center rounded-full border font-semibold", cls, sizes[size].wrapper)}>
      <Icon className={sizes[size].icon} />
      <span>{label}</span>
      {showScore && score > 0 && <span className="opacity-60">({score})</span>}
    </div>
  );
}
