import type { Metadata, Viewport } from "next";
import { Toaster } from "sonner";
import "./globals.css";
import QueryProvider from "@/providers/QueryProvider";
import { LangProvider } from "@/contexts/LangContext";
import { ThemeProvider } from "@/providers/ThemeProvider";
import PwaInit from "@/components/PwaInit";

export const metadata: Metadata = {
  title: "SellerMate AI",
  description: "Bangladesh e-commerce AI management platform",
  manifest: "/manifest.json",
  appleWebApp: {
    capable: true,
    statusBarStyle: "black-translucent",
    title: "SellerMate",
  },
  icons: {
    apple: "/icons/icon-192.png",
    icon: "/icons/icon.svg",
  },
};

export const viewport: Viewport = {
  themeColor: "#6366f1",
  width: "device-width",
  initialScale: 1,
  maximumScale: 1,
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="bn" suppressHydrationWarning>
      <body>
        <ThemeProvider>
          <QueryProvider>
            <LangProvider>
              {children}
            </LangProvider>
            <Toaster richColors position="top-right" />
          </QueryProvider>
        </ThemeProvider>
        <PwaInit />
      </body>
    </html>
  );
}
