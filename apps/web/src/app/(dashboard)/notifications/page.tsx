"use client";

import { Bell, AlertTriangle, TrendingDown, TrendingUp, Package, ChevronRight } from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";
import { useLang } from "@/contexts/LangContext";
import { useNotifications, type Notification } from "@/hooks/useNotifications";
import { useRouter } from "next/navigation";
import { cn } from "@/lib/utils";

const TYPE_ICONS: Record<string, React.ElementType> = {
  LOW_STOCK:       Package,
  CHURN_RISK:      AlertTriangle,
  REVENUE_ALERT:   TrendingDown,
  REVENUE_POSITIVE: TrendingUp,
};

const PRIORITY_COLORS: Record<string, string> = {
  HIGH:   "border-l-red-500 bg-red-50/40",
  MEDIUM: "border-l-orange-400 bg-orange-50/40",
  LOW:    "border-l-green-400 bg-green-50/40",
};

const PRIORITY_BADGE: Record<string, string> = {
  HIGH:   "bg-red-100 text-red-700",
  MEDIUM: "bg-orange-100 text-orange-700",
  LOW:    "bg-green-100 text-green-700",
};

function NotifCard({ n, lang }: { n: Notification; lang: string }) {
  const router = useRouter();
  const Icon = TYPE_ICONS[n.type] ?? Bell;

  return (
    <div
      className={cn(
        "bg-white border border-slate-200 border-l-4 rounded-xl p-4 cursor-pointer hover:shadow-sm transition-shadow flex items-start gap-3",
        PRIORITY_COLORS[n.priority] ?? "border-l-slate-300"
      )}
      onClick={() => router.push(n.action)}
    >
      <div className="shrink-0 mt-0.5">
        <Icon className={cn("h-5 w-5",
          n.priority === "HIGH" ? "text-red-500" :
          n.priority === "MEDIUM" ? "text-orange-500" :
          "text-green-500"
        )} />
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-1">
          <p className="font-semibold text-slate-800 text-sm">{lang === "bn" ? n.title_bn : n.title_en}</p>
          <span className={cn("text-[10px] font-medium px-1.5 py-0.5 rounded", PRIORITY_BADGE[n.priority])}>
            {n.priority}
          </span>
        </div>
        <p className="text-sm text-slate-500">{lang === "bn" ? n.body_bn : n.body_en}</p>
      </div>
      <ChevronRight className="h-4 w-4 text-slate-300 shrink-0 mt-0.5" />
    </div>
  );
}

export default function NotificationsPage() {
  const { lang } = useLang();
  const l = (bn: string, en: string) => lang === "bn" ? bn : en;
  const { data, isLoading } = useNotifications();
  const notifications = (data ?? []) as Notification[];

  const high   = notifications.filter((n) => n.priority === "HIGH");
  const medium = notifications.filter((n) => n.priority === "MEDIUM");
  const low    = notifications.filter((n) => n.priority === "LOW");

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">{l("বিজ্ঞপ্তি কেন্দ্র", "Notification Center")}</h1>
          <p className="text-sm text-slate-500 mt-1">{l("রিয়েল-টাইম ব্যবসায়িক সতর্কতা", "Real-time business alerts")}</p>
        </div>
        {notifications.length > 0 && (
          <div className="flex items-center gap-2 bg-blue-50 border border-blue-200 rounded-lg px-3 py-1.5">
            <Bell className="h-4 w-4 text-blue-600" />
            <span className="text-sm font-semibold text-blue-700">{notifications.length}</span>
          </div>
        )}
      </div>

      {isLoading ? (
        <div className="space-y-3">
          {Array.from({ length: 5 }).map((_, i) => <Skeleton key={i} className="h-20 w-full" />)}
        </div>
      ) : notifications.length === 0 ? (
        <div className="bg-white border border-slate-200 rounded-xl p-16 text-center">
          <Bell className="h-12 w-12 text-slate-200 mx-auto mb-4" />
          <p className="text-slate-400 font-medium">{l("কোনো সক্রিয় বিজ্ঞপ্তি নেই", "No active notifications")}</p>
          <p className="text-slate-300 text-sm mt-1">{l("সব কিছু ঠিকঠাক আছে!", "Everything looks good!")}</p>
        </div>
      ) : (
        <div className="space-y-6">
          {high.length > 0 && (
            <div className="space-y-3">
              <h2 className="text-sm font-semibold text-red-600 uppercase tracking-wide">
                {l("জরুরি", "Urgent")} ({high.length})
              </h2>
              {high.map((n) => <NotifCard key={n.id} n={n} lang={lang} />)}
            </div>
          )}
          {medium.length > 0 && (
            <div className="space-y-3">
              <h2 className="text-sm font-semibold text-orange-600 uppercase tracking-wide">
                {l("মাঝারি", "Medium")} ({medium.length})
              </h2>
              {medium.map((n) => <NotifCard key={n.id} n={n} lang={lang} />)}
            </div>
          )}
          {low.length > 0 && (
            <div className="space-y-3">
              <h2 className="text-sm font-semibold text-green-600 uppercase tracking-wide">
                {l("তথ্যমূলক", "Informational")} ({low.length})
              </h2>
              {low.map((n) => <NotifCard key={n.id} n={n} lang={lang} />)}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
