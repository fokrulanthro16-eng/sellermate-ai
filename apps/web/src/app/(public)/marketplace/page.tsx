"use client";

import { useState } from "react";
import Link from "next/link";
import { Search, Store, MapPin, Shield, Truck, Zap, ChevronRight, Package } from "lucide-react";
import { useMarketplace, useStoreBySlug } from "@/hooks/usePublicStore";

const TRUST_ITEMS = [
  { icon: Shield, label: "Verified Sellers", sub: "100% authentic stores" },
  { icon: Truck, label: "Fast Delivery", sub: "Across Bangladesh" },
  { icon: Zap, label: "Easy Returns", sub: "7-day return policy" },
];

function StoreCard({ store }: { store: any }) {
  return (
    <Link href={`/store/${store.store_slug}`} className="block group">
      <div className="bg-white rounded-2xl border border-gray-100 overflow-hidden shadow-sm hover:shadow-lg hover:border-indigo-200 transition-all duration-200">
        {store.store_banner_url ? (
          <img
            src={store.store_banner_url}
            alt={store.business_name}
            className="w-full h-28 object-cover group-hover:scale-105 transition-transform duration-300"
          />
        ) : (
          <div className="w-full h-28 bg-gradient-to-br from-indigo-100 via-purple-50 to-pink-50 flex items-center justify-center">
            <Store className="w-10 h-10 text-indigo-300" />
          </div>
        )}
        <div className="p-4">
          <div className="flex items-center gap-2 mb-1.5">
            {store.logo_url ? (
              <img src={store.logo_url} alt="Logo" className="w-8 h-8 rounded-lg object-cover shrink-0" />
            ) : (
              <div className="w-8 h-8 rounded-lg bg-indigo-100 flex items-center justify-center shrink-0 text-base">🏪</div>
            )}
            <h3 className="font-semibold text-gray-900 text-sm truncate">{store.business_name}</h3>
          </div>

          {store.district && (
            <p className="text-xs text-gray-500 flex items-center gap-1 mt-0.5">
              <MapPin className="w-3 h-3 shrink-0" /> {store.district}
            </p>
          )}
          {store.store_description && (
            <p className="text-xs text-gray-500 mt-1.5 line-clamp-2 leading-relaxed">{store.store_description}</p>
          )}

          <div className="flex items-center justify-between mt-3 pt-3 border-t border-gray-50">
            <span className="text-xs font-semibold text-indigo-600">{store.product_count || 0} products</span>
            <span className="flex items-center gap-0.5 text-xs text-indigo-600 font-medium group-hover:gap-1.5 transition-all">
              Shop now <ChevronRight className="w-3 h-3" />
            </span>
          </div>
        </div>
      </div>
    </Link>
  );
}

function SkeletonCard() {
  return (
    <div className="bg-white rounded-2xl border border-gray-100 overflow-hidden animate-pulse">
      <div className="h-28 bg-gray-100" />
      <div className="p-4 space-y-2">
        <div className="h-4 bg-gray-100 rounded w-3/4" />
        <div className="h-3 bg-gray-100 rounded w-1/2" />
        <div className="h-3 bg-gray-100 rounded w-2/3 mt-2" />
      </div>
    </div>
  );
}

export default function MarketplacePage() {
  const [search, setSearch] = useState("");
  const [activeSearch, setActiveSearch] = useState("");

  const storesQuery = useMarketplace(activeSearch || undefined);
  const demoFallback = useStoreBySlug("demo-shop");

  const rawStores: any[] = storesQuery.data?.data?.stores ?? [];
  const demoStore = demoFallback.data?.data;

  // Always show demo-shop if API list is empty
  const stores = rawStores.length > 0 ? rawStores : demoStore ? [demoStore] : [];
  const isLoading = storesQuery.isLoading && demoFallback.isLoading;

  const firstSlug = stores[0]?.store_slug || "demo-shop";

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Hero */}
      <div className="bg-white border-b border-gray-100">
        <div className="max-w-6xl mx-auto px-4 py-12 text-center">
          <div className="inline-flex items-center gap-2 bg-indigo-50 text-indigo-700 text-xs font-semibold px-3 py-1.5 rounded-full mb-4 border border-indigo-100">
            <Zap className="w-3 h-3" /> Bangladesh's Local Commerce Platform
          </div>
          <h1 className="text-3xl sm:text-4xl font-bold text-gray-900 mb-3">
            Discover Local <span className="text-indigo-600">Sellers</span>
          </h1>
          <p className="text-gray-500 mb-8 max-w-xl mx-auto text-sm sm:text-base">
            Shop from verified local stores — fashion, electronics, lifestyle and more delivered to your door.
          </p>

          <form
            onSubmit={(e) => { e.preventDefault(); setActiveSearch(search); }}
            className="flex gap-2 max-w-xl mx-auto"
          >
            <div className="flex-1 relative">
              <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                className="w-full pl-10 pr-4 py-3 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent bg-white shadow-sm"
                placeholder="Search stores..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
            </div>
            <button
              type="submit"
              className="px-5 py-3 bg-indigo-600 text-white rounded-xl text-sm font-semibold hover:bg-indigo-700 transition-colors shadow-sm"
            >
              Search
            </button>
          </form>
        </div>
      </div>

      {/* Trust strip */}
      <div className="bg-white border-b border-gray-100">
        <div className="max-w-6xl mx-auto px-4 py-3">
          <div className="flex items-center justify-center gap-6 sm:gap-16">
            {TRUST_ITEMS.map(({ icon: Icon, label, sub }) => (
              <div key={label} className="flex items-center gap-2">
                <div className="w-7 h-7 rounded-lg bg-indigo-50 flex items-center justify-center shrink-0">
                  <Icon className="w-4 h-4 text-indigo-600" />
                </div>
                <div className="hidden sm:block">
                  <p className="text-xs font-semibold text-gray-800">{label}</p>
                  <p className="text-[10px] text-gray-500">{sub}</p>
                </div>
                <span className="sm:hidden text-xs font-medium text-gray-700">{label}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Store grid */}
      <div className="max-w-6xl mx-auto px-4 py-8">
        <div className="flex items-center justify-between mb-5">
          <div>
            <h2 className="text-lg font-bold text-gray-900">
              {activeSearch ? `Results for "${activeSearch}"` : "Featured Stores"}
            </h2>
            {!activeSearch && (
              <p className="text-sm text-gray-500 mt-0.5">Shop directly from local sellers</p>
            )}
          </div>
          {activeSearch && (
            <button
              onClick={() => { setSearch(""); setActiveSearch(""); }}
              className="text-sm text-indigo-600 hover:text-indigo-700 font-medium"
            >
              Clear
            </button>
          )}
        </div>

        {isLoading ? (
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
            {[...Array(4)].map((_, i) => <SkeletonCard key={i} />)}
          </div>
        ) : stores.length === 0 ? (
          <div className="text-center py-16">
            <Package className="w-12 h-12 mx-auto text-gray-200 mb-3" />
            <p className="text-gray-500 font-medium">No stores found</p>
            <p className="text-gray-400 text-sm mt-1">Try a different search term</p>
          </div>
        ) : (
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
            {stores.map((s: any) => <StoreCard key={s.id || s.store_slug} store={s} />)}
          </div>
        )}

        {/* CTA */}
        {!activeSearch && stores.length > 0 && (
          <div className="mt-10 bg-indigo-600 rounded-2xl p-6 sm:p-8 flex flex-col sm:flex-row items-center justify-between gap-4">
            <div>
              <h3 className="text-white font-bold text-lg">Looking for something specific?</h3>
              <p className="text-indigo-200 text-sm mt-1">Browse products or track an existing order</p>
            </div>
            <div className="flex gap-3 flex-wrap">
              <Link
                href="/track-order"
                className="px-5 py-2.5 bg-white/10 text-white border border-white/20 rounded-xl text-sm font-medium hover:bg-white/20 transition-colors whitespace-nowrap"
              >
                Track Order
              </Link>
              <Link
                href={`/store/${firstSlug}`}
                className="px-5 py-2.5 bg-white text-indigo-600 rounded-xl text-sm font-bold hover:bg-indigo-50 transition-colors whitespace-nowrap"
              >
                Shop Now
              </Link>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
