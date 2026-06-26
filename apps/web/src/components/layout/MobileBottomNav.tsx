"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { LayoutDashboard, ShoppingCart, Package, Bot, MoreHorizontal } from "lucide-react";
import { cn } from "@/lib/utils";
import { useLang } from "@/contexts/LangContext";

const tabs = [
  { href: "/dashboard", icon: LayoutDashboard, labelKey: "dashboard" as const },
  { href: "/orders",    icon: ShoppingCart,    labelKey: "orders"    as const },
  { href: "/products",  icon: Package,         labelKey: "products"  as const },
  { href: "/assistant", icon: Bot,             labelKey: "assistant" as const },
] as const;

interface Props {
  onMoreClick: () => void;
}

export default function MobileBottomNav({ onMoreClick }: Props) {
  const pathname = usePathname();
  const { t, lang } = useLang();

  return (
    <nav className="lg:hidden fixed bottom-0 inset-x-0 z-40 flex border-t"
      style={{ background: "hsl(var(--sidebar-bg))", borderColor: "hsl(var(--sidebar-border))" }}
    >
      {tabs.map(({ href, icon: Icon, labelKey }) => {
        const active = pathname === href || pathname.startsWith(href + "/");
        return (
          <Link
            key={href}
            href={href}
            className={cn(
              "flex-1 flex flex-col items-center justify-center gap-0.5 py-2 text-[10px] font-medium transition-colors",
              active ? "text-indigo-400" : "text-white/50 hover:text-white/80"
            )}
          >
            <Icon className="h-5 w-5" />
            <span>{t(labelKey)}</span>
          </Link>
        );
      })}
      <button
        onClick={onMoreClick}
        className="flex-1 flex flex-col items-center justify-center gap-0.5 py-2 text-[10px] font-medium text-white/50 hover:text-white/80 transition-colors"
      >
        <MoreHorizontal className="h-5 w-5" />
        <span>{lang === "bn" ? "আরো" : "More"}</span>
      </button>
    </nav>
  );
}
