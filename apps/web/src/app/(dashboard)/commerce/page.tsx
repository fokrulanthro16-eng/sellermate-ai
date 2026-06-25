"use client";

import { useState } from "react";
import { TrendingUp, TrendingDown, Minus, Package, AlertTriangle, ShoppingBag, Tag, ArrowUpDown } from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";
import { useLang } from "@/contexts/LangContext";
import {
  usePriceRecommendations,
  useDemandPredictions,
  useInventoryForecast,
  useRestockRecommendations,
  useBundleRecommendations,
  useBestSellers,
  useWorstSellers,
} from "@/hooks/useCommerce";
import { cn } from "@/lib/utils";

const TABS = [
  { id: "price",    labelBn: "মূল্য সুপারিশ",  labelEn: "Price Recs"       },
  { id: "demand",   labelBn: "চাহিদা পূর্বাভাস", labelEn: "Demand"          },
  { id: "inv",      labelBn: "ইনভেন্টরি পূর্বাভাস", labelEn: "Inventory Forecast" },
  { id: "restock",  labelBn: "রিস্টক",           labelEn: "Restock"          },
  { id: "bundle",   labelBn: "বান্ডেল",           labelEn: "Bundles"          },
  { id: "sellers",  labelBn: "বিক্রেতা র‍্যাংক",  labelEn: "Sellers"          },
] as const;

type TabId = (typeof TABS)[number]["id"];

function StatusBadge({ status }: { status: string }) {
  const map: Record<string, string> = {
    CRITICAL: "bg-red-100 text-red-700 border-red-200",
    WARNING:  "bg-orange-100 text-orange-700 border-orange-200",
    LOW:      "bg-yellow-100 text-yellow-700 border-yellow-200",
    OK:       "bg-green-100 text-green-700 border-green-200",
    NO_SALES: "bg-slate-100 text-slate-600 border-slate-200",
  };
  return (
    <span className={cn("text-[11px] font-medium px-2 py-0.5 rounded border", map[status] ?? "bg-slate-100 text-slate-600 border-slate-200")}>
      {status}
    </span>
  );
}

function TrendIcon({ trend }: { trend: string }) {
  if (trend === "RISING")  return <TrendingUp className="h-4 w-4 text-green-500" />;
  if (trend === "FALLING") return <TrendingDown className="h-4 w-4 text-red-500" />;
  return <Minus className="h-4 w-4 text-slate-400" />;
}

function Card({ children, className }: { children: React.ReactNode; className?: string }) {
  return (
    <div className={cn("bg-white border border-slate-200 rounded-xl p-4", className)}>
      {children}
    </div>
  );
}

function LoadingRows({ n = 5 }: { n?: number }) {
  return (
    <div className="space-y-3">
      {Array.from({ length: n }).map((_, i) => (
        <Skeleton key={i} className="h-12 w-full" />
      ))}
    </div>
  );
}

export default function CommercePage() {
  const { lang } = useLang();
  const l = (bn: string, en: string) => lang === "bn" ? bn : en;
  const [tab, setTab] = useState<TabId>("price");
  const [sellerDays, setSellerDays] = useState(30);

  const priceQ  = usePriceRecommendations();
  const demandQ = useDemandPredictions();
  const invQ    = useInventoryForecast();
  const restockQ = useRestockRecommendations();
  const bundleQ = useBundleRecommendations();
  const bestQ   = useBestSellers(sellerDays);
  const worstQ  = useWorstSellers(sellerDays);

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">{l("কমার্স অটোমেশন", "Commerce Automation")}</h1>
        <p className="text-sm text-slate-500 mt-1">{l("AI-চালিত বিশ্লেষণ ও সুপারিশ", "AI-powered analytics and recommendations")}</p>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 flex-wrap">
        {TABS.map((t) => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            className={cn(
              "px-3 py-1.5 text-sm font-medium rounded-lg transition-colors",
              tab === t.id ? "bg-blue-600 text-white" : "bg-slate-100 text-slate-600 hover:bg-slate-200"
            )}
          >
            {lang === "bn" ? t.labelBn : t.labelEn}
          </button>
        ))}
      </div>

      {/* Price Recommendations */}
      {tab === "price" && (
        <Card>
          <h2 className="font-semibold text-slate-800 mb-4">{l("মূল্য সুপারিশ", "Price Recommendations")}</h2>
          {priceQ.isLoading ? <LoadingRows /> : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-slate-100">
                    <th className="text-left py-2 pr-4 text-slate-500 font-medium">{l("পণ্য", "Product")}</th>
                    <th className="text-right py-2 pr-4 text-slate-500 font-medium">{l("বর্তমান দাম", "Current")}</th>
                    <th className="text-right py-2 pr-4 text-slate-500 font-medium">{l("সুপারিশ", "Suggested")}</th>
                    <th className="text-center py-2 pr-4 text-slate-500 font-medium">{l("পদক্ষেপ", "Action")}</th>
                    <th className="text-left py-2 text-slate-500 font-medium">{l("কারণ", "Reason")}</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-50">
                  {((priceQ.data as any[]) ?? []).map((r: any) => (
                    <tr key={r.product_id} className="hover:bg-slate-50">
                      <td className="py-3 pr-4 font-medium text-slate-800">{r.product_name}</td>
                      <td className="py-3 pr-4 text-right text-slate-600">৳{r.current_price.toLocaleString()}</td>
                      <td className="py-3 pr-4 text-right font-medium text-slate-800">৳{r.recommended_price.toLocaleString()}</td>
                      <td className="py-3 pr-4 text-center">
                        <span className={cn("text-[11px] font-semibold px-2 py-0.5 rounded border",
                          r.action === "RAISE" ? "bg-green-50 text-green-700 border-green-200" :
                          r.action === "LOWER" ? "bg-red-50 text-red-700 border-red-200" :
                          "bg-slate-50 text-slate-600 border-slate-200"
                        )}>
                          {r.action}
                        </span>
                      </td>
                      <td className="py-3 text-slate-500 text-xs max-w-xs">{lang === "bn" ? r.reason_bn : r.reason_en}</td>
                    </tr>
                  ))}
                  {!priceQ.isLoading && (priceQ.data as any[])?.length === 0 && (
                    <tr><td colSpan={5} className="py-8 text-center text-slate-400">{l("কোনো ডেটা নেই", "No data")}</td></tr>
                  )}
                </tbody>
              </table>
            </div>
          )}
        </Card>
      )}

      {/* Demand Predictions */}
      {tab === "demand" && (
        <Card>
          <h2 className="font-semibold text-slate-800 mb-4">{l("চাহিদা পূর্বাভাস", "Demand Predictions")}</h2>
          {demandQ.isLoading ? <LoadingRows /> : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-slate-100">
                    <th className="text-left py-2 pr-4 text-slate-500 font-medium">{l("পণ্য", "Product")}</th>
                    <th className="text-right py-2 pr-4 text-slate-500 font-medium">{l("৩০ দিনে বিক্রি", "Sold 30d")}</th>
                    <th className="text-right py-2 pr-4 text-slate-500 font-medium">{l("দৈনিক গতি", "Daily Vel.")}</th>
                    <th className="text-right py-2 pr-4 text-slate-500 font-medium">{l("পরবর্তী ৩০ দিন", "Pred. 30d")}</th>
                    <th className="text-center py-2 pr-4 text-slate-500 font-medium">{l("প্রবণতা", "Trend")}</th>
                    <th className="text-center py-2 text-slate-500 font-medium">{l("নির্ভরযোগ্যতা", "Conf.")}</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-50">
                  {((demandQ.data as any[]) ?? []).map((r: any) => (
                    <tr key={r.product_id} className="hover:bg-slate-50">
                      <td className="py-3 pr-4 font-medium text-slate-800">{r.product_name}</td>
                      <td className="py-3 pr-4 text-right text-slate-600">{r.units_sold_30d}</td>
                      <td className="py-3 pr-4 text-right text-slate-600">{r.daily_velocity}/d</td>
                      <td className="py-3 pr-4 text-right font-semibold text-blue-700">{r.predicted_next_30d}</td>
                      <td className="py-3 pr-4 text-center"><TrendIcon trend={r.trend} /></td>
                      <td className="py-3 text-center">
                        <span className={cn("text-[11px] font-medium px-2 py-0.5 rounded",
                          r.confidence === "HIGH" ? "bg-green-100 text-green-700" :
                          r.confidence === "MEDIUM" ? "bg-yellow-100 text-yellow-700" :
                          "bg-slate-100 text-slate-500"
                        )}>
                          {r.confidence}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Card>
      )}

      {/* Inventory Forecast */}
      {tab === "inv" && (
        <Card>
          <h2 className="font-semibold text-slate-800 mb-4">{l("ইনভেন্টরি পূর্বাভাস", "Inventory Forecast")}</h2>
          {invQ.isLoading ? <LoadingRows /> : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-slate-100">
                    <th className="text-left py-2 pr-4 text-slate-500 font-medium">{l("পণ্য", "Product")}</th>
                    <th className="text-right py-2 pr-4 text-slate-500 font-medium">{l("স্টক", "Stock")}</th>
                    <th className="text-right py-2 pr-4 text-slate-500 font-medium">{l("দৈনিক গতি", "Vel./d")}</th>
                    <th className="text-right py-2 pr-4 text-slate-500 font-medium">{l("বাকি দিন", "Days Left")}</th>
                    <th className="text-center py-2 text-slate-500 font-medium">{l("অবস্থা", "Status")}</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-50">
                  {((invQ.data as any[]) ?? []).filter((r: any) => r.status !== "OK" && r.status !== "NO_SALES").concat(
                    ((invQ.data as any[]) ?? []).filter((r: any) => r.status === "OK" || r.status === "NO_SALES")
                  ).map((r: any) => (
                    <tr key={r.variant_id} className="hover:bg-slate-50">
                      <td className="py-3 pr-4">
                        <div className="font-medium text-slate-800">{r.product_name}</div>
                        {r.variant_name !== r.product_name && <div className="text-xs text-slate-400">{r.variant_name}</div>}
                      </td>
                      <td className="py-3 pr-4 text-right text-slate-600">{r.current_stock}</td>
                      <td className="py-3 pr-4 text-right text-slate-500">{r.daily_velocity}</td>
                      <td className="py-3 pr-4 text-right font-medium text-slate-800">
                        {r.days_remaining >= 999 ? "∞" : r.days_remaining.toFixed(0)}
                      </td>
                      <td className="py-3 text-center"><StatusBadge status={r.status} /></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Card>
      )}

      {/* Restock */}
      {tab === "restock" && (
        <Card>
          <h2 className="font-semibold text-slate-800 mb-4">{l("রিস্টক সুপারিশ", "Restock Recommendations")}</h2>
          {restockQ.isLoading ? <LoadingRows /> : (
            <>
              {((restockQ.data as any[]) ?? []).length === 0 ? (
                <div className="text-center py-12 text-slate-400">
                  <Package className="h-10 w-10 mx-auto mb-2 opacity-30" />
                  <p>{l("সব পণ্যের স্টক যথেষ্ট!", "All products are well stocked!")}</p>
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-slate-100">
                        <th className="text-left py-2 pr-4 text-slate-500 font-medium">{l("পণ্য", "Product")}</th>
                        <th className="text-right py-2 pr-4 text-slate-500 font-medium">{l("বর্তমান", "Current")}</th>
                        <th className="text-right py-2 pr-4 text-slate-500 font-medium">{l("বাকি দিন", "Days Left")}</th>
                        <th className="text-right py-2 pr-4 text-slate-500 font-medium">{l("সুপারিশ করা পরিমাণ", "Order Qty")}</th>
                        <th className="text-center py-2 text-slate-500 font-medium">{l("অগ্রাধিকার", "Priority")}</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-50">
                      {((restockQ.data as any[]) ?? []).map((r: any) => (
                        <tr key={r.variant_id} className="hover:bg-slate-50">
                          <td className="py-3 pr-4 font-medium text-slate-800">{r.product_name}</td>
                          <td className="py-3 pr-4 text-right text-slate-600">{r.current_stock}</td>
                          <td className="py-3 pr-4 text-right text-red-600 font-medium">{r.days_remaining.toFixed(0)}</td>
                          <td className="py-3 pr-4 text-right font-bold text-blue-700">{r.recommended_qty}</td>
                          <td className="py-3 text-center"><StatusBadge status={r.priority} /></td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </>
          )}
        </Card>
      )}

      {/* Bundle */}
      {tab === "bundle" && (
        <Card>
          <h2 className="font-semibold text-slate-800 mb-4">{l("বান্ডেল সুপারিশ", "Bundle Recommendations")}</h2>
          {bundleQ.isLoading ? <LoadingRows n={4} /> : (
            <>
              {((bundleQ.data as any[]) ?? []).length === 0 ? (
                <div className="text-center py-12 text-slate-400">
                  <Tag className="h-10 w-10 mx-auto mb-2 opacity-30" />
                  <p>{l("বান্ডেল তৈরির জন্য পর্যাপ্ত ডেটা নেই", "Not enough co-purchase data yet")}</p>
                </div>
              ) : (
                <div className="grid gap-3">
                  {((bundleQ.data as any[]) ?? []).map((r: any, i: number) => (
                    <div key={i} className="flex items-center gap-4 p-3 border border-slate-100 rounded-lg hover:bg-slate-50">
                      <ShoppingBag className="h-5 w-5 text-blue-500 shrink-0" />
                      <div className="flex-1 min-w-0">
                        <p className="font-medium text-slate-800 text-sm">
                          {r.product_a_name} + {r.product_b_name}
                        </p>
                        <p className="text-xs text-slate-400 mt-0.5">
                          {l(`একসাথে ${r.co_purchase_count} বার কেনা হয়েছে`, `Bought together ${r.co_purchase_count} times`)}
                        </p>
                      </div>
                      <div className="text-right shrink-0">
                        <p className="text-sm font-semibold text-green-600">{r.suggested_discount_pct}% {l("ছাড়", "discount")}</p>
                        <p className="text-xs text-slate-400">{l("বান্ডেলে", "if bundled")}</p>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </>
          )}
        </Card>
      )}

      {/* Sellers */}
      {tab === "sellers" && (
        <div className="space-y-4">
          <div className="flex gap-2">
            {[7, 30, 90].map((d) => (
              <button
                key={d}
                onClick={() => setSellerDays(d)}
                className={cn("px-3 py-1 text-sm rounded-lg border transition-colors",
                  sellerDays === d ? "bg-blue-600 text-white border-blue-600" : "bg-white border-slate-200 text-slate-600 hover:bg-slate-50"
                )}
              >
                {d} {l("দিন", "days")}
              </button>
            ))}
          </div>
          <div className="grid md:grid-cols-2 gap-4">
            <Card>
              <h2 className="font-semibold text-green-700 mb-3 flex items-center gap-2">
                <TrendingUp className="h-4 w-4" />{l("সেরা বিক্রি", "Best Sellers")}
              </h2>
              {bestQ.isLoading ? <LoadingRows n={5} /> : (
                <div className="space-y-2">
                  {((bestQ.data as any[]) ?? []).map((r: any, i: number) => (
                    <div key={r.product_id} className="flex items-center gap-3">
                      <span className="text-lg font-bold text-slate-300 w-6 text-right">{i + 1}</span>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-slate-800 truncate">{r.product_name}</p>
                        <p className="text-xs text-slate-400">{r.total_units} {l("টি বিক্রি", "units")}</p>
                      </div>
                      <p className="text-sm font-semibold text-slate-800">৳{r.total_revenue.toLocaleString()}</p>
                    </div>
                  ))}
                  {((bestQ.data as any[]) ?? []).length === 0 && (
                    <p className="text-slate-400 text-sm text-center py-4">{l("কোনো ডেটা নেই", "No data")}</p>
                  )}
                </div>
              )}
            </Card>
            <Card>
              <h2 className="font-semibold text-red-700 mb-3 flex items-center gap-2">
                <TrendingDown className="h-4 w-4" />{l("কম বিক্রি", "Worst Sellers")}
              </h2>
              {worstQ.isLoading ? <LoadingRows n={5} /> : (
                <div className="space-y-2">
                  {((worstQ.data as any[]) ?? []).map((r: any, i: number) => (
                    <div key={r.product_id} className="flex items-center gap-3">
                      <span className="text-lg font-bold text-slate-300 w-6 text-right">{i + 1}</span>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-slate-800 truncate">{r.product_name}</p>
                        <p className="text-xs text-slate-400">{r.total_units} {l("টি বিক্রি", "units")}</p>
                      </div>
                      <p className="text-sm font-semibold text-slate-800">৳{r.total_revenue.toLocaleString()}</p>
                    </div>
                  ))}
                  {((worstQ.data as any[]) ?? []).length === 0 && (
                    <p className="text-slate-400 text-sm text-center py-4">{l("কোনো ডেটা নেই", "No data")}</p>
                  )}
                </div>
              )}
            </Card>
          </div>
        </div>
      )}
    </div>
  );
}
