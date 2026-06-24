"use client";

import { useEffect, useState, useRef } from "react";
import { useRouter } from "next/navigation";
import { LogOut, User, Bell, Menu, Globe, Search, ChevronDown } from "lucide-react";
import { toast } from "sonner";
import api from "@/lib/api-client";
import { clearTokens } from "@/lib/auth";
import { getInitials } from "@/lib/utils";
import { useLang } from "@/contexts/LangContext";
import type { Merchant } from "@/types";
import {
  DropdownMenu, DropdownMenuContent, DropdownMenuItem,
  DropdownMenuLabel, DropdownMenuSeparator, DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import MobileNav from "@/components/layout/MobileNav";

const SEARCH_SUGGESTIONS = {
  bn: [
    "অর্ডার সার্চ করুন...",
    "পণ্য খুঁজুন...",
    "গ্রাহক খুঁজুন...",
  ],
  en: [
    "Search orders, products, customers...",
  ],
};

export default function Header() {
  const router = useRouter();
  const { lang, setLang } = useLang();
  const [merchant, setMerchant] = useState<Merchant | null>(null);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [search, setSearch] = useState("");
  const [searchFocus, setSearchFocus] = useState(false);
  const searchRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    api.get<{ data: Merchant }>("/auth/me").then((r) => setMerchant(r.data.data)).catch(() => {});
  }, []);

  const handleLogout = async () => {
    try { await api.post("/auth/logout"); } catch {}
    clearTokens();
    toast.success(lang === "bn" ? "লগআউট সফল হয়েছে" : "Logged out successfully");
    router.push("/login");
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (!search.trim()) return;
    const q = encodeURIComponent(search.trim());
    router.push(`/orders?search=${q}`);
    setSearch("");
  };

  const placeholder = lang === "bn"
    ? "অর্ডার, পণ্য, গ্রাহক সার্চ করুন..."
    : "Search orders, products, customers...";

  return (
    <>
      <header className="sticky top-0 z-40 flex h-14 shrink-0 items-center gap-3 border-b bg-card px-4 sm:px-6">
        {/* Mobile menu button */}
        <Button
          variant="ghost"
          size="icon"
          className="lg:hidden h-8 w-8"
          onClick={() => setMobileOpen(true)}
        >
          <Menu className="h-4 w-4" />
        </Button>

        {/* Search bar */}
        <form onSubmit={handleSearch} className="flex-1 max-w-xl">
          <div className={`relative flex items-center transition-all duration-150 ${searchFocus ? "ring-1 ring-primary" : ""} rounded-md border border-border bg-background`}>
            <Search className="absolute left-3 h-3.5 w-3.5 text-muted-foreground pointer-events-none" />
            <input
              ref={searchRef}
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              onFocus={() => setSearchFocus(true)}
              onBlur={() => setSearchFocus(false)}
              placeholder={placeholder}
              className="w-full bg-transparent pl-9 pr-3 py-1.5 text-sm outline-none placeholder:text-muted-foreground"
            />
            {search && (
              <button
                type="button"
                onClick={() => setSearch("")}
                className="absolute right-2 text-muted-foreground hover:text-foreground text-lg leading-none"
              >
                ×
              </button>
            )}
          </div>
        </form>

        {/* Right controls */}
        <div className="flex items-center gap-1.5 ml-auto">
          {/* Language toggle */}
          <button
            onClick={() => setLang(lang === "bn" ? "en" : "bn")}
            className="flex items-center gap-1 px-2.5 py-1.5 rounded border border-border bg-background hover:bg-accent transition-colors text-xs font-semibold"
          >
            <Globe className="h-3.5 w-3.5 text-muted-foreground" />
            <span>{lang === "bn" ? "EN" : "বাং"}</span>
          </button>

          {/* Notifications */}
          <Button
            variant="ghost"
            size="icon"
            className="h-8 w-8 relative"
          >
            <Bell className="h-4 w-4 text-muted-foreground" />
            <span className="absolute top-1.5 right-1.5 h-1.5 w-1.5 rounded-full bg-red-500" />
          </Button>

          {/* User menu */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <button className="flex items-center gap-2 px-2 py-1 rounded border border-border bg-background hover:bg-accent transition-colors">
                <Avatar className="h-6 w-6 rounded">
                  <AvatarFallback className="rounded text-[10px] font-bold bg-primary text-primary-foreground">
                    {merchant ? getInitials(merchant.business_name) : "SM"}
                  </AvatarFallback>
                </Avatar>
                <span className="text-xs font-medium hidden sm:block max-w-[120px] truncate">
                  {merchant?.business_name || "SellerMate"}
                </span>
                <ChevronDown className="h-3 w-3 text-muted-foreground hidden sm:block" />
              </button>
            </DropdownMenuTrigger>
            <DropdownMenuContent className="w-52" align="end" forceMount>
              <DropdownMenuLabel className="font-normal py-2">
                <div className="flex flex-col gap-0.5">
                  <p className="text-sm font-semibold">{merchant?.business_name || "..."}</p>
                  <p className="text-xs text-muted-foreground truncate">{merchant?.email || ""}</p>
                </div>
              </DropdownMenuLabel>
              <DropdownMenuSeparator />
              <DropdownMenuItem onClick={() => router.push("/settings")} className="gap-2 text-sm">
                <User className="h-3.5 w-3.5" />
                {lang === "bn" ? "প্রোফাইল ও সেটিংস" : "Profile & Settings"}
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem onClick={handleLogout} className="gap-2 text-sm text-destructive focus:text-destructive">
                <LogOut className="h-3.5 w-3.5" />
                {lang === "bn" ? "লগআউট" : "Logout"}
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </header>
      <MobileNav open={mobileOpen} onClose={() => setMobileOpen(false)} />
    </>
  );
}
