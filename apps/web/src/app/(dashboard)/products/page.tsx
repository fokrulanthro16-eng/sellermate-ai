"use client";

import { useState } from "react";
import Link from "next/link";
import { Plus, Search, LayoutGrid, List, Package } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { useProducts, useDeleteProduct } from "@/hooks/useProducts";
import { useLang } from "@/contexts/LangContext";
import ProductTable from "@/components/products/ProductTable";
import ProductCard from "@/components/products/ProductCard";
import { cn } from "@/lib/utils";

const LIMIT = 20;

const CATEGORY_MAP = [
  { value: "পোশাক",               bn: "পোশাক",               en: "Clothing" },
  { value: "জুতা",                bn: "জুতা",                en: "Shoes" },
  { value: "ব্যাগ",               bn: "ব্যাগ",               en: "Bags" },
  { value: "ইলেকট্রনিক্স",        bn: "ইলেকট্রনিক্স",        en: "Electronics" },
  { value: "সৌন্দর্য",            bn: "সৌন্দর্য",            en: "Beauty" },
  { value: "গৃহস্থালি",           bn: "গৃহস্থালি",           en: "Household" },
  { value: "খাদ্যপণ্য",           bn: "খাদ্যপণ্য",           en: "Food" },
  { value: "মোবাইল আক্সেসরিজ",   bn: "মোবাইল আক্সেসরিজ",   en: "Mobile Accessories" },
  { value: "ধর্মীয় পণ্য",        bn: "ধর্মীয় পণ্য",        en: "Religious Items" },
];

export default function ProductsPage() {
  const { t, lang } = useLang();
  const label = (bn: string, en: string) => lang === "bn" ? bn : en;

  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("");
  const [view, setView] = useState<"table" | "grid">("table");
  const [page, setPage] = useState(1);

  const { data, isLoading } = useProducts({
    page, limit: LIMIT,
    search: search || undefined,
    category: category || undefined,
  });
  const deleteProduct = useDeleteProduct();

  const products = Array.isArray(data?.items) ? data.items : [];
  const total = data?.total ?? 0;
  const totalPages = Math.max(1, Math.ceil(total / LIMIT));

  const handleDelete = async (id: string) => {
    if (confirm(t("deleteProduct"))) {
      await deleteProduct.mutateAsync(id);
    }
  };

  return (
    <div className="space-y-4 max-w-[1400px]">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-xl font-bold">{t("productMgmt")}</h1>
          <p className="text-sm text-muted-foreground">
            {total > 0
              ? t("totalProducts").replace("{{n}}", String(total))
              : t("manageCatalog")}
          </p>
        </div>
        <div className="flex items-center gap-2">
          {/* View toggle */}
          <div className="flex items-center gap-1 bg-muted/60 p-1 rounded-xl border border-border/50">
            <Button
              variant="ghost"
              size="icon"
              className={cn("h-7 w-7 rounded-lg", view === "table" && "bg-background shadow-sm border border-border/50")}
              onClick={() => setView("table")}
            >
              <List className="h-3.5 w-3.5" />
            </Button>
            <Button
              variant="ghost"
              size="icon"
              className={cn("h-7 w-7 rounded-lg", view === "grid" && "bg-background shadow-sm border border-border/50")}
              onClick={() => setView("grid")}
            >
              <LayoutGrid className="h-3.5 w-3.5" />
            </Button>
          </div>
          <Button asChild className="gap-2 rounded-xl">
            <Link href="/products/new"><Plus className="h-4 w-4" /> {t("newProduct")}</Link>
          </Button>
        </div>
      </div>

      {/* Search + category chips */}
      <div className="space-y-3 animate-slide-up animation-delay-100">
        <div className="relative max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder={t("searchProduct")}
            value={search}
            onChange={(e) => { setSearch(e.target.value); setPage(1); }}
            className="pl-9 rounded-xl"
          />
        </div>

        <div className="flex items-center gap-2 flex-wrap">
          <button
            onClick={() => { setCategory(""); setPage(1); }}
            className={cn(
              "px-3.5 py-1.5 rounded-full text-xs font-medium border transition-all duration-200",
              !category
                ? "bg-primary text-primary-foreground border-primary shadow-sm"
                : "bg-background text-muted-foreground border-input hover:bg-accent"
            )}
          >
            {t("allCategories")}
          </button>
          {CATEGORY_MAP.map((cat) => (
            <button
              key={cat.value}
              onClick={() => { setCategory(cat.value === category ? "" : cat.value); setPage(1); }}
              className={cn(
                "px-3.5 py-1.5 rounded-full text-xs font-medium border transition-all duration-200",
                category === cat.value
                  ? "bg-primary text-primary-foreground border-primary shadow-sm"
                  : "bg-background text-muted-foreground border-input hover:bg-accent"
              )}
            >
              {lang === "en" ? cat.en : cat.bn}
            </button>
          ))}
        </div>
      </div>

      {/* Product list */}
      <div className="animate-slide-up animation-delay-200">
        {view === "table" ? (
          <ProductTable products={products} loading={isLoading} onDelete={handleDelete} />
        ) : (
          <>
            {isLoading ? (
              <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-4">
                {[1, 2, 3, 4, 5, 6].map((i) => <Skeleton key={i} className="h-36 w-full rounded-xl" />)}
              </div>
            ) : products.length === 0 ? (
              <div className="glass-card rounded-2xl py-16 text-center space-y-3">
                <Package className="h-12 w-12 mx-auto text-muted-foreground/30" />
                <p className="text-muted-foreground font-medium">{t("noProducts")}</p>
                {(search || category) && (
                  <Button size="sm" variant="outline" className="rounded-xl" onClick={() => { setSearch(""); setCategory(""); }}>
                    {t("clearFilters")}
                  </Button>
                )}
                <Button asChild size="sm" className="gap-1.5 rounded-xl">
                  <Link href="/products/new"><Plus className="h-3.5 w-3.5" /> {t("addProduct")}</Link>
                </Button>
              </div>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-4">
                {products.map((p) => <ProductCard key={p.id} product={p} onDelete={handleDelete} />)}
              </div>
            )}
          </>
        )}
      </div>

      {/* Pagination */}
      {total > LIMIT && (
        <div className="flex items-center justify-center gap-3">
          <Button variant="outline" size="sm" className="rounded-xl" disabled={page === 1} onClick={() => setPage((p) => p - 1)}>
            {t("prev")}
          </Button>
          <span className="text-sm text-muted-foreground tabular-nums">{page} / {totalPages}</span>
          <Button variant="outline" size="sm" className="rounded-xl" disabled={page >= totalPages} onClick={() => setPage((p) => p + 1)}>
            {t("next")}
          </Button>
        </div>
      )}
    </div>
  );
}
