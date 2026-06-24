"use client";

import { useState } from "react";
import Link from "next/link";
import { Plus, Search } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useProducts, useDeleteProduct } from "@/hooks/useProducts";
import { useLang } from "@/contexts/LangContext";
import ProductTable from "@/components/products/ProductTable";

const LIMIT = 25;

const CATEGORIES = [
  { value: "পোশাক",             en: "Clothing" },
  { value: "জুতা",              en: "Shoes" },
  { value: "ব্যাগ",             en: "Bags" },
  { value: "ইলেকট্রনিক্স",      en: "Electronics" },
  { value: "সৌন্দর্য",          en: "Beauty" },
  { value: "গৃহস্থালি",         en: "Household" },
  { value: "খাদ্যপণ্য",         en: "Food" },
  { value: "মোবাইল আক্সেসরিজ", en: "Mobile Accessories" },
  { value: "ধর্মীয় পণ্য",      en: "Religious Items" },
];

export default function ProductsPage() {
  const { lang } = useLang();
  const l = (bn: string, en: string) => lang === "bn" ? bn : en;

  const [search,   setSearch]   = useState("");
  const [category, setCategory] = useState("");
  const [stock,    setStock]    = useState("");   // "" | "low" | "out"
  const [page,     setPage]     = useState(1);

  const { data, isLoading } = useProducts({
    page, limit: LIMIT,
    search:       search   || undefined,
    category:     category || undefined,
    low_stock:    stock === "low" ? true : undefined,
    out_of_stock: stock === "out" ? true : undefined,
  });
  const deleteProduct = useDeleteProduct();

  const products   = Array.isArray(data?.items) ? data.items : [];
  const total      = data?.total ?? 0;
  const totalPages = Math.max(1, Math.ceil(total / LIMIT));

  const handleDelete = async (id: string) => {
    if (confirm(l("এই পণ্যটি মুছে ফেলবেন?", "Delete this product?"))) {
      await deleteProduct.mutateAsync(id);
    }
  };

  return (
    <div className="space-y-4 max-w-[1500px]">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold">{l("পণ্য ব্যবস্থাপনা", "Product Management")}</h1>
          <p className="text-sm text-muted-foreground">
            {total > 0
              ? `${total} ${l("টি পণ্য", "products in catalog")}`
              : l("পণ্য ক্যাটালগ পরিচালনা করুন", "Manage your product catalog")}
          </p>
        </div>
        <Button asChild size="sm" className="gap-1.5 h-8 text-xs">
          <Link href="/products/new"><Plus className="h-3.5 w-3.5" />{l("নতুন পণ্য", "Add Product")}</Link>
        </Button>
      </div>

      {/* Filters row */}
      <div className="flex gap-2 flex-wrap items-center">
        <div className="relative flex-1 min-w-[200px] max-w-xs">
          <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground" />
          <Input
            placeholder={l("পণ্যের নাম বা SKU...", "Product name or SKU...")}
            value={search}
            onChange={(e) => { setSearch(e.target.value); setPage(1); }}
            className="pl-8 h-8 text-sm"
          />
        </div>

        <Select value={category} onValueChange={(v) => { setCategory(v); setPage(1); }}>
          <SelectTrigger className="w-44 h-8 text-sm">
            <SelectValue placeholder={l("সব বিভাগ", "All Categories")} />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="">{l("সব বিভাগ", "All Categories")}</SelectItem>
            {CATEGORIES.map((c) => (
              <SelectItem key={c.value} value={c.value}>
                {lang === "bn" ? c.value : c.en}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        <Select value={stock} onValueChange={(v) => { setStock(v); setPage(1); }}>
          <SelectTrigger className="w-40 h-8 text-sm">
            <SelectValue placeholder={l("স্টক অবস্থা", "Stock Status")} />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="">{l("সব স্টক", "All Stock")}</SelectItem>
            <SelectItem value="low">{l("কম স্টক", "Low Stock")}</SelectItem>
            <SelectItem value="out">{l("স্টক নেই", "Out of Stock")}</SelectItem>
          </SelectContent>
        </Select>

        {(search || category || stock) && (
          <Button variant="ghost" size="sm" className="h-8 text-xs"
            onClick={() => { setSearch(""); setCategory(""); setStock(""); setPage(1); }}>
            {l("ফিল্টার মুছুন", "Clear")}
          </Button>
        )}

        {total > 0 && (
          <span className="ml-auto text-xs text-muted-foreground">{total} {l("টি পণ্য", "products")}</span>
        )}
      </div>

      {/* Table */}
      <ProductTable products={products} loading={isLoading} onDelete={handleDelete} />

      {/* Pagination */}
      {total > LIMIT && (
        <div className="flex items-center justify-between text-sm">
          <span className="text-xs text-muted-foreground">
            {l("পৃষ্ঠা", "Page")} {page} / {totalPages}
          </span>
          <div className="flex gap-2">
            <Button variant="outline" size="sm" className="h-7 text-xs" disabled={page === 1} onClick={() => setPage((p) => p - 1)}>
              {l("আগের", "Prev")}
            </Button>
            <Button variant="outline" size="sm" className="h-7 text-xs" disabled={page >= totalPages} onClick={() => setPage((p) => p + 1)}>
              {l("পরের", "Next")}
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
