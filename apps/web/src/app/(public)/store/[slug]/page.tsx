"use client";

import { useState } from "react";
import { useParams } from "next/navigation";
import { MapPin, ShoppingCart, Search, Phone, Package } from "lucide-react";
import { toast } from "sonner";
import { useStoreBySlug, useStoreProducts } from "@/hooks/usePublicStore";
import { useCart } from "@/contexts/CartContext";
import Link from "next/link";

const TRUST_BADGES = [
  { label: "Verified Seller", emoji: "✅" },
  { label: "Secure Checkout", emoji: "🔒" },
  { label: "Fast Delivery", emoji: "🚚" },
];

function ProductCard({ product, merchantId }: { product: any; merchantId: string }) {
  const { add } = useCart();
  const [added, setAdded] = useState(false);

  function handleAdd() {
    add({
      product_id: product.id,
      merchant_id: merchantId,
      name: product.name,
      price: Number(product.sale_price ?? product.base_price),
      image_url: product.image_urls?.[0],
    });
    setAdded(true);
    toast.success(`${product.name} added to cart`);
    setTimeout(() => setAdded(false), 1500);
  }

  const price = Number(product.sale_price ?? product.base_price);
  const originalPrice = product.sale_price ? Number(product.base_price) : null;
  const discount = originalPrice ? Math.round((1 - price / originalPrice) * 100) : null;

  return (
    <div className="bg-white rounded-2xl border border-gray-100 overflow-hidden shadow-sm hover:shadow-md transition-all group">
      <div className="relative">
        {product.image_urls?.[0] ? (
          <img
            src={product.image_urls[0]}
            alt={product.name}
            className="w-full h-48 object-cover group-hover:scale-105 transition-transform duration-300"
          />
        ) : (
          <div className="w-full h-48 bg-gradient-to-br from-indigo-50 to-purple-50 flex items-center justify-center">
            <Package className="w-12 h-12 text-indigo-200" />
          </div>
        )}
        {discount && (
          <div className="absolute top-2 left-2 bg-red-500 text-white text-xs font-bold px-2 py-0.5 rounded-full">
            -{discount}%
          </div>
        )}
      </div>
      <div className="p-3">
        <p className="font-medium text-sm text-gray-900 line-clamp-2 leading-snug">{product.name}</p>
        {product.description && (
          <p className="text-xs text-gray-500 mt-0.5 line-clamp-1">{product.description}</p>
        )}
        <div className="mt-2 flex items-center justify-between">
          <div>
            <span className="text-indigo-600 font-bold text-base">৳{price}</span>
            {originalPrice && (
              <span className="text-gray-400 line-through text-xs ml-1">৳{originalPrice}</span>
            )}
          </div>
          {product.total_sold > 0 && (
            <span className="text-xs text-gray-400">{product.total_sold} sold</span>
          )}
        </div>
        <button
          onClick={handleAdd}
          className={`mt-2.5 w-full flex items-center justify-center gap-1.5 py-2 rounded-xl text-xs font-semibold transition-all ${
            added
              ? "bg-green-600 text-white"
              : "bg-indigo-600 text-white hover:bg-indigo-700"
          }`}
        >
          <ShoppingCart className="w-3.5 h-3.5" />
          {added ? "Added!" : "Add to Cart"}
        </button>
      </div>
    </div>
  );
}

function StoreSkeleton() {
  return (
    <div className="animate-pulse">
      <div className="w-full h-48 bg-gray-200 rounded-b-2xl" />
      <div className="max-w-6xl mx-auto px-4 -mt-8">
        <div className="bg-white rounded-2xl p-6">
          <div className="w-16 h-16 rounded-full bg-gray-200 mb-3" />
          <div className="h-6 bg-gray-200 rounded w-48 mb-2" />
          <div className="h-4 bg-gray-200 rounded w-32" />
        </div>
      </div>
    </div>
  );
}

export default function StorePage() {
  const { slug } = useParams<{ slug: string }>();
  const [search, setSearch] = useState("");
  const [activeSearch, setActiveSearch] = useState("");
  const [selectedCategory, setSelectedCategory] = useState("");

  const storeQuery = useStoreBySlug(slug);
  const productsQuery = useStoreProducts(slug, selectedCategory || undefined);
  const { count } = useCart();

  const store = storeQuery.data?.data;
  const allProducts: any[] = productsQuery.data?.data?.products || [];

  const filteredProducts = activeSearch
    ? allProducts.filter((p) =>
        p.name.toLowerCase().includes(activeSearch.toLowerCase()) ||
        (p.description || "").toLowerCase().includes(activeSearch.toLowerCase())
      )
    : allProducts;

  // Collect unique categories
  const categories = Array.from(new Set(allProducts.map((p) => p.category).filter(Boolean)));

  if (storeQuery.isLoading) return <StoreSkeleton />;

  if (!store) {
    return (
      <div className="max-w-2xl mx-auto px-4 py-16 text-center">
        <Package className="w-16 h-16 mx-auto text-gray-300 mb-4" />
        <h1 className="text-xl font-bold text-gray-900 mb-2">Store not found</h1>
        <p className="text-gray-500 mb-4">This store link may have changed or been removed.</p>
        <Link href="/marketplace" className="text-indigo-600 underline">Browse Marketplace</Link>
      </div>
    );
  }

  return (
    <div>
      {/* Banner */}
      {store.store_banner_url ? (
        <div className="w-full h-52 overflow-hidden">
          <img src={store.store_banner_url} alt={store.business_name} className="w-full h-full object-cover" />
        </div>
      ) : (
        <div className="w-full h-52 bg-gradient-to-br from-indigo-500 via-purple-500 to-pink-500" />
      )}

      <div className="max-w-6xl mx-auto px-4">
        {/* Store Header Card */}
        <div className="bg-white rounded-2xl border border-gray-100 shadow-sm -mt-10 relative z-10 p-6 mb-6">
          <div className="flex items-start gap-4 flex-wrap">
            {/* Logo */}
            <div className="w-20 h-20 rounded-2xl border-4 border-white shadow-md overflow-hidden bg-indigo-100 flex items-center justify-center shrink-0 -mt-14">
              {store.logo_url
                ? <img src={store.logo_url} alt="Logo" className="w-full h-full object-cover" />
                : <span className="text-3xl">🏪</span>}
            </div>

            <div className="flex-1 min-w-0">
              <h1 className="text-xl font-bold text-gray-900">{store.business_name}</h1>
              {store.district && (
                <p className="text-sm text-gray-500 flex items-center gap-1 mt-0.5">
                  <MapPin className="w-3.5 h-3.5" /> {store.district}
                </p>
              )}
              {store.store_description && (
                <p className="text-gray-600 text-sm mt-1.5 leading-relaxed">{store.store_description}</p>
              )}

              {/* Trust badges */}
              <div className="flex flex-wrap gap-2 mt-2">
                {TRUST_BADGES.map((b) => (
                  <span key={b.label} className="inline-flex items-center gap-1 text-xs text-gray-600 bg-gray-50 border border-gray-200 px-2 py-0.5 rounded-full">
                    {b.emoji} {b.label}
                  </span>
                ))}
              </div>
            </div>

            <div className="flex items-center gap-2 flex-wrap">
              {store.whatsapp_phone && (
                <a
                  href={`https://wa.me/${store.whatsapp_phone?.replace(/\D/g, "")}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-1.5 px-4 py-2 bg-green-500 text-white rounded-xl text-sm font-medium hover:bg-green-600 transition-colors"
                >
                  <Phone className="w-4 h-4" /> WhatsApp
                </a>
              )}
              <Link
                href="/cart"
                className="relative flex items-center gap-1.5 px-4 py-2 bg-indigo-600 text-white rounded-xl text-sm font-medium hover:bg-indigo-700 transition-colors"
              >
                <ShoppingCart className="w-4 h-4" /> Cart
                {count > 0 && (
                  <span className="absolute -top-1.5 -right-1.5 bg-red-500 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center font-bold">
                    {count}
                  </span>
                )}
              </Link>
            </div>
          </div>
        </div>

        {/* Search bar */}
        <div className="flex gap-2 mb-4">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              className="w-full pl-9 pr-4 py-2.5 border border-gray-200 rounded-xl text-sm bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
              placeholder="Search products..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && setActiveSearch(search)}
            />
          </div>
          {search && (
            <button
              onClick={() => setActiveSearch(search)}
              className="px-4 py-2.5 bg-indigo-600 text-white rounded-xl text-sm font-medium hover:bg-indigo-700 transition-colors"
            >
              Search
            </button>
          )}
        </div>

        {/* Category chips */}
        {categories.length > 0 && (
          <div className="flex gap-2 overflow-x-auto pb-1 mb-5" style={{ scrollbarWidth: "none" }}>
            <button
              onClick={() => setSelectedCategory("")}
              className={`shrink-0 px-4 py-1.5 rounded-full text-xs font-semibold border transition-colors ${
                !selectedCategory
                  ? "bg-indigo-600 text-white border-indigo-600"
                  : "bg-white text-gray-600 border-gray-200 hover:border-indigo-300 hover:text-indigo-600"
              }`}
            >
              All
            </button>
            {categories.map((cat) => (
              <button
                key={cat}
                onClick={() => setSelectedCategory(cat)}
                className={`shrink-0 px-4 py-1.5 rounded-full text-xs font-semibold border transition-colors ${
                  selectedCategory === cat
                    ? "bg-indigo-600 text-white border-indigo-600"
                    : "bg-white text-gray-600 border-gray-200 hover:border-indigo-300 hover:text-indigo-600"
                }`}
              >
                {cat.replace(/_/g, " ").toLowerCase().replace(/\b\w/g, (l: string) => l.toUpperCase())}
              </button>
            ))}
          </div>
        )}

        {/* Product count header */}
        <div className="flex items-center justify-between mb-4">
          <h2 className="font-semibold text-gray-900">
            {activeSearch
              ? `${filteredProducts.length} result(s) for "${activeSearch}"`
              : `Products (${store.product_count || allProducts.length})`}
          </h2>
          {activeSearch && (
            <button onClick={() => { setSearch(""); setActiveSearch(""); }} className="text-sm text-indigo-600 hover:underline">
              Clear search
            </button>
          )}
        </div>

        {/* Products Grid */}
        {productsQuery.isLoading ? (
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
            {Array.from({ length: 8 }).map((_, i) => (
              <div key={i} className="rounded-2xl bg-gray-100 animate-pulse h-64" />
            ))}
          </div>
        ) : filteredProducts.length === 0 ? (
          <div className="text-center py-16 text-gray-500">
            <Package className="w-12 h-12 mx-auto mb-3 text-gray-300" />
            <p>{activeSearch ? "No products match your search" : "No products available yet"}</p>
          </div>
        ) : (
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4 pb-12">
            {filteredProducts.map((p) => (
              <ProductCard key={p.id} product={p} merchantId={store.id} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
