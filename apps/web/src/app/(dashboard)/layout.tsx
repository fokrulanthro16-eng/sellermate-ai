"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { isAuthenticated } from "@/lib/auth";
import Sidebar from "@/components/layout/Sidebar";
import Header from "@/components/layout/Header";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    if (!isAuthenticated()) router.replace("/login");
  }, [router]);

  if (!mounted) return null;
  if (!isAuthenticated()) return null;

  return (
    <div className="min-h-screen bg-background">
      <Sidebar />
      <div className="lg:pl-56 flex flex-col min-h-screen">
        <Header />
        <main className="flex-1 p-4 sm:p-5 animate-fade-in">
          {children}
        </main>
      </div>
    </div>
  );
}
