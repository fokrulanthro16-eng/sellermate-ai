"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard, Package, Warehouse, ShoppingCart,
  Users, BarChart3, Bot, Shield, Settings, Zap, Star, Wand2,
  TrendingUp, Megaphone, FileBarChart2, Bell, Plug, Activity, Lock,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useLang } from "@/contexts/LangContext";
import { useHealth } from "@/hooks/useHealth";
import type { TranslationKey } from "@/lib/i18n";

interface NavItem {
  href: string;
  icon: React.ElementType;
  labelKey: TranslationKey;
}

const coreNav: NavItem[] = [
  { href: "/dashboard",  icon: LayoutDashboard, labelKey: "dashboard"  },
  { href: "/orders",     icon: ShoppingCart,    labelKey: "orders"     },
  { href: "/products",   icon: Package,         labelKey: "products"   },
  { href: "/inventory",  icon: Warehouse,       labelKey: "inventory"  },
  { href: "/customers",  icon: Users,           labelKey: "customers"  },
  { href: "/analytics",  icon: BarChart3,       labelKey: "analytics"  },
];

const aiNav: NavItem[] = [
  { href: "/assistant",  icon: Bot,    labelKey: "assistant" },
  { href: "/ai-center",  icon: Shield, labelKey: "aiCenter"  },
  { href: "/ai-tools",   icon: Wand2,  labelKey: "aiTools"   },
  { href: "/reviews",    icon: Star,   labelKey: "reviews"   },
];

const commerceNav: NavItem[] = [
  { href: "/commerce",       icon: TrendingUp,    labelKey: "commerce"       },
  { href: "/campaigns",      icon: Megaphone,     labelKey: "campaigns"      },
  { href: "/reports",        icon: FileBarChart2, labelKey: "reports"        },
  { href: "/notifications",  icon: Bell,          labelKey: "notifications"  },
  { href: "/integrations",   icon: Plug,          labelKey: "integrations"   },
];

const systemNav: NavItem[] = [
  { href: "/activity",  icon: Activity, labelKey: "activity" },
  { href: "/security",  icon: Lock,     labelKey: "security" },
];

function NavLink({ item }: { item: NavItem }) {
  const pathname = usePathname();
  const { t } = useLang();
  const isActive = pathname === item.href || pathname.startsWith(item.href + "/");

  return (
    <Link
      href={item.href}
      className={cn(
        "sidebar-nav-item",
        isActive && "sidebar-nav-active"
      )}
    >
      <item.icon className="h-4 w-4 shrink-0" />
      <span className="truncate">{t(item.labelKey)}</span>
    </Link>
  );
}

export default function Sidebar() {
  const pathname = usePathname();
  const { t } = useLang();
  const { data: health } = useHealth();

  return (
    <aside className="hidden lg:flex lg:flex-col lg:w-56 lg:fixed lg:inset-y-0 lg:z-50"
      style={{ background: "hsl(var(--sidebar-bg))", borderRight: "1px solid hsl(var(--sidebar-border))" }}
    >
      {/* Logo */}
      <div className="flex h-14 shrink-0 items-center gap-2.5 px-4"
        style={{ borderBottom: "1px solid hsl(var(--sidebar-border))" }}
      >
        <div className="h-7 w-7 rounded flex items-center justify-center gradient-primary shrink-0">
          <Zap className="h-4 w-4 text-white" />
        </div>
        <div>
          <p className="text-sm font-bold text-white leading-tight">SellerMate</p>
          <p className="text-[10px] text-white/50 leading-tight">Commerce OS</p>
        </div>
        <div className="ml-auto h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse-glow" />
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto px-2 py-4 space-y-5">
        {/* Core */}
        <div className="space-y-0.5">
          <p className="px-3 mb-1.5 text-[10px] font-semibold uppercase tracking-widest text-white/30">
            {t("coreMenu")}
          </p>
          {coreNav.map((item) => <NavLink key={item.href} item={item} />)}
        </div>

        {/* AI */}
        <div className="space-y-0.5">
          <p className="px-3 mb-1.5 text-[10px] font-semibold uppercase tracking-widest text-white/30">
            {t("aiMenu")}
          </p>
          {aiNav.map((item) => <NavLink key={item.href} item={item} />)}
        </div>

        {/* Commerce */}
        <div className="space-y-0.5">
          <p className="px-3 mb-1.5 text-[10px] font-semibold uppercase tracking-widest text-white/30">
            {t("commerceMenu")}
          </p>
          {commerceNav.map((item) => <NavLink key={item.href} item={item} />)}
        </div>

        {/* System */}
        <div className="space-y-0.5">
          <p className="px-3 mb-1.5 text-[10px] font-semibold uppercase tracking-widest text-white/30">
            {t("systemMenu")}
          </p>
          {systemNav.map((item) => <NavLink key={item.href} item={item} />)}
        </div>
      </nav>

      {/* Footer */}
      <div className="px-2 pb-4" style={{ borderTop: "1px solid hsl(var(--sidebar-border))" }}>
        <div className="pt-3 space-y-1">
          <Link
            href="/settings"
            className={cn("sidebar-nav-item", pathname === "/settings" && "sidebar-nav-active")}
          >
            <Settings className="h-4 w-4 shrink-0" />
            <span>{t("settings")}</span>
          </Link>
          {/* Health indicator */}
          <div className="flex items-center gap-2 px-3 py-1.5">
            <span className={cn("h-1.5 w-1.5 rounded-full shrink-0",
              !health ? "bg-slate-400" : health.status === "ok" ? "bg-emerald-400 animate-pulse" : "bg-amber-400 animate-pulse"
            )} />
            <span className="text-[10px] text-white/40">
              {!health ? "Connecting..." : health.status === "ok" ? "All systems OK" : "Degraded"}
            </span>
          </div>
        </div>
      </div>
    </aside>
  );
}
