"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard, Package, Warehouse, ShoppingCart,
  Users, BarChart3, Bot, Shield, Settings, Zap,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Sheet, SheetContent, SheetHeader, SheetTitle } from "@/components/ui/sheet";

const navItems = [
  { href: "/dashboard", icon: LayoutDashboard, label: "ড্যাশবোর্ড" },
  { href: "/products", icon: Package, label: "পণ্য" },
  { href: "/inventory", icon: Warehouse, label: "স্টক" },
  { href: "/orders", icon: ShoppingCart, label: "অর্ডার" },
  { href: "/customers", icon: Users, label: "গ্রাহক" },
  { href: "/analytics", icon: BarChart3, label: "বিশ্লেষণ" },
  { href: "/assistant", icon: Bot, label: "এআই সহকারী" },
  { href: "/ai-center", icon: Shield, label: "কৌশলগত এআই" },
  { href: "/settings", icon: Settings, label: "সেটিংস" },
];

interface MobileNavProps {
  open: boolean;
  onClose: () => void;
}

export default function MobileNav({ open, onClose }: MobileNavProps) {
  const pathname = usePathname();

  return (
    <Sheet open={open} onOpenChange={(v) => !v && onClose()}>
      <SheetContent side="left" className="w-72 p-0">
        <SheetHeader className="p-6 border-b">
          <SheetTitle className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary">
              <Zap className="h-5 w-5 text-white" />
            </div>
            SellerMate AI
          </SheetTitle>
        </SheetHeader>
        <nav className="flex-1 px-3 py-4 space-y-1">
          {navItems.map((item) => {
            const isActive = pathname === item.href || pathname.startsWith(item.href + "/");
            return (
              <Link
                key={item.href}
                href={item.href}
                onClick={onClose}
                className={cn(
                  "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors",
                  isActive
                    ? "bg-primary text-primary-foreground"
                    : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
                )}
              >
                <item.icon className="h-4 w-4 shrink-0" />
                {item.label}
              </Link>
            );
          })}
        </nav>
      </SheetContent>
    </Sheet>
  );
}
