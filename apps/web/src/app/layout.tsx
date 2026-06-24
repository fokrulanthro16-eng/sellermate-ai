import type { Metadata } from "next";
import { Toaster } from "sonner";
import "./globals.css";
import QueryProvider from "@/providers/QueryProvider";
import { LangProvider } from "@/contexts/LangContext";
import { ThemeProvider } from "@/providers/ThemeProvider";

export const metadata: Metadata = {
  title: "SellerMate AI",
  description: "Bangladesh e-commerce AI management platform",
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
      </body>
    </html>
  );
}
