"use client";

import { useState } from "react";
import { FileDown, TrendingUp, TrendingDown, Minus, Users, AlertTriangle, DollarSign, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { useLang } from "@/contexts/LangContext";
import {
  useCustomerLTV,
  useChurnRisk,
  useRevenueForecast,
  useHealthScore,
  useProfitReport,
  useTaxSummary,
  downloadPDF,
  downloadExcel,
} from "@/hooks/useReports";
import { cn } from "@/lib/utils";

const TABS = [
  { id: "profit",    labelBn: "মুনাফা রিপোর্ট",  labelEn: "Profit Report" },
  { id: "tax",       labelBn: "ট্যাক্স সারসংক্ষেপ", labelEn: "Tax Summary"  },
  { id: "health",    labelBn: "স্বাস্থ্য স্কোর",  labelEn: "Health Score" },
  { id: "ltv",       labelBn: "গ্রাহক মূল্য",     labelEn: "Customer LTV" },
  { id: "churn",     labelBn: "চার্ন ঝুঁকি",      labelEn: "Churn Risk"   },
  { id: "revenue",   labelBn: "রাজস্ব পূর্বাভাস", labelEn: "Revenue Forecast" },
] as const;

type TabId = (typeof TABS)[number]["id"];

function StatCard({ label, value, sub }: { label: string; value: string; sub?: string }) {
  return (
    <div className="bg-white border border-slate-200 rounded-xl p-4">
      <p className="text-xs text-slate-500">{label}</p>
      <p className="text-xl font-bold text-slate-900 mt-1">{value}</p>
      {sub && <p className="text-xs text-slate-400 mt-0.5">{sub}</p>}
    </div>
  );
}

function LoadingGrid({ n = 4 }: { n?: number }) {
  return <div className="grid grid-cols-2 md:grid-cols-4 gap-3">{Array.from({ length: n }).map((_, i) => <Skeleton key={i} className="h-20 w-full" />)}</div>;
}

function LoadingRows({ n = 5 }: { n?: number }) {
  return <div className="space-y-3">{Array.from({ length: n }).map((_, i) => <Skeleton key={i} className="h-12 w-full" />)}</div>;
}

export default function ReportsPage() {
  const { lang } = useLang();
  const l = (bn: string, en: string) => lang === "bn" ? bn : en;
  const [tab, setTab] = useState<TabId>("profit");
  const [days, setDays] = useState(30);
  const [pdfLoading, setPdfLoading] = useState(false);
  const [xlLoading, setXlLoading] = useState(false);

  const profitQ  = useProfitReport(days);
  const taxQ     = useTaxSummary(days);
  const healthQ  = useHealthScore();
  const ltvQ     = useCustomerLTV();
  const churnQ   = useChurnRisk();
  const forecastQ = useRevenueForecast();

  const handlePDF = async () => {
    setPdfLoading(true);
    await downloadPDF(days);
    setPdfLoading(false);
  };

  const handleExcel = async () => {
    setXlLoading(true);
    await downloadExcel(days);
    setXlLoading(false);
  };

  const profit  = (profitQ.data  as any) ?? {};
  const tax     = (taxQ.data     as any) ?? {};
  const health  = (healthQ.data  as any) ?? {};
  const forecast = (forecastQ.data as any) ?? {};

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">{l("রিপোর্ট ও বিশ্লেষণ", "Reports & Analytics")}</h1>
          <p className="text-sm text-slate-500 mt-1">{l("ব্যবসার সম্পূর্ণ আর্থিক চিত্র", "Complete financial picture of your business")}</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={handlePDF} disabled={pdfLoading}>
            {pdfLoading ? <Loader2 className="h-4 w-4 animate-spin mr-1" /> : <FileDown className="h-4 w-4 mr-1" />}
            PDF
          </Button>
          <Button variant="outline" size="sm" onClick={handleExcel} disabled={xlLoading}>
            {xlLoading ? <Loader2 className="h-4 w-4 animate-spin mr-1" /> : <FileDown className="h-4 w-4 mr-1" />}
            Excel
          </Button>
        </div>
      </div>

      {/* Days filter */}
      <div className="flex items-center gap-2">
        <span className="text-xs text-slate-500">{l("সময়কাল:", "Period:")}</span>
        {[7, 30, 90].map((d) => (
          <button
            key={d}
            onClick={() => setDays(d)}
            className={cn("px-3 py-1 text-sm rounded-lg border transition-colors",
              days === d ? "bg-blue-600 text-white border-blue-600" : "bg-white border-slate-200 text-slate-600 hover:bg-slate-50"
            )}
          >
            {d} {l("দিন", "days")}
          </button>
        ))}
      </div>

      {/* Tabs */}
      <div className="flex gap-1 flex-wrap">
        {TABS.map((t) => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            className={cn("px-3 py-1.5 text-sm font-medium rounded-lg transition-colors",
              tab === t.id ? "bg-blue-600 text-white" : "bg-slate-100 text-slate-600 hover:bg-slate-200"
            )}
          >
            {lang === "bn" ? t.labelBn : t.labelEn}
          </button>
        ))}
      </div>

      {/* Profit Report */}
      {tab === "profit" && (
        <div className="space-y-4">
          {profitQ.isLoading ? <LoadingGrid /> : (
            <>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                <StatCard label={l("মোট রাজস্ব", "Total Revenue")} value={`৳${(profit.total_revenue ?? 0).toLocaleString()}`} />
                <StatCard label={l("মোট মুনাফা", "Net Profit")} value={`৳${(profit.net_profit ?? 0).toLocaleString()}`}
                  sub={`${profit.net_margin_pct ?? 0}% ${l("মার্জিন", "margin")}`} />
                <StatCard label={l("মোট ছাড়", "Discounts")} value={`৳${(profit.total_discounts ?? 0).toLocaleString()}`} />
                <StatCard label={l("বিতরণ করা অর্ডার", "Delivered Orders")} value={`${profit.delivered_order_count ?? 0}`} />
              </div>
              <div className="bg-white border border-slate-200 rounded-xl p-5">
                <table className="w-full text-sm">
                  <tbody className="divide-y divide-slate-50">
                    {[
                      [l("মোট রাজস্ব", "Total Revenue"), `৳${(profit.total_revenue ?? 0).toLocaleString()}`],
                      [l("আনুমানিক পণ্য খরচ (৬০%)", "Est. COGS (60%)"), `৳${(profit.estimated_cogs ?? 0).toLocaleString()}`],
                      [l("মোট মুনাফা", "Gross Profit"), `৳${(profit.gross_profit ?? 0).toLocaleString()} (${profit.gross_margin_pct ?? 0}%)`],
                      [l("মোট ছাড়", "Total Discounts"), `- ৳${(profit.total_discounts ?? 0).toLocaleString()}`],
                      [l("শিপিং খরচ", "Shipping Cost"), `- ৳${(profit.total_shipping_cost ?? 0).toLocaleString()}`],
                      [l("নিট মুনাফা", "Net Profit"), `৳${(profit.net_profit ?? 0).toLocaleString()} (${profit.net_margin_pct ?? 0}%)`],
                    ].map(([label, val]) => (
                      <tr key={label} className="hover:bg-slate-50">
                        <td className="py-3 text-slate-600">{label}</td>
                        <td className="py-3 text-right font-medium text-slate-800">{val}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </>
          )}
        </div>
      )}

      {/* Tax Summary */}
      {tab === "tax" && (
        <div className="space-y-4">
          {taxQ.isLoading ? <LoadingGrid /> : (
            <>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                <StatCard label={l("আনুমানিক ভ্যাট (১৫%)", "Est. VAT (15%)")} value={`৳${(tax.estimated_vat ?? 0).toLocaleString()}`} />
                <StatCard label={l("আনুমানিক আয়কর", "Est. Income Tax")} value={`৳${(tax.estimated_income_tax ?? 0).toLocaleString()}`} />
                <StatCard label={l("মোট কর দায়", "Total Tax Liability")} value={`৳${(tax.total_tax_liability ?? 0).toLocaleString()}`} />
              </div>
              <div className="bg-white border border-slate-200 rounded-xl p-5">
                <div className="flex items-center gap-2 mb-4 p-3 bg-blue-50 rounded-lg">
                  <DollarSign className="h-4 w-4 text-blue-600" />
                  <p className="text-sm text-blue-700">{l("বাংলাদেশ ভ্যাট ১৫% হারে গণনা করা হয়েছে। এটি আনুমানিক — একজন কর উপদেষ্টার সাথে পরামর্শ করুন।",
                    "Bangladesh VAT calculated at 15%. This is an estimate — consult a tax advisor.")}</p>
                </div>
                <table className="w-full text-sm">
                  <tbody className="divide-y divide-slate-50">
                    {[
                      [l("মোট রাজস্ব", "Total Revenue"), `৳${(tax.total_revenue ?? 0).toLocaleString()}`],
                      [l("ভ্যাট হার", "VAT Rate"), `${tax.vat_rate_pct ?? 15}%`],
                      [l("আনুমানিক ভ্যাট", "Estimated VAT"), `৳${(tax.estimated_vat ?? 0).toLocaleString()}`],
                      [l("আনুমানিক আয়কর", "Estimated Income Tax"), `৳${(tax.estimated_income_tax ?? 0).toLocaleString()}`],
                      [l("মোট কর দায়", "Total Tax Liability"), `৳${(tax.total_tax_liability ?? 0).toLocaleString()}`],
                      [l("কাটযোগ্য শিপিং খরচ", "Deductible Shipping"), `৳${(tax.deductible_shipping ?? 0).toLocaleString()}`],
                      [l("কাটযোগ্য ছাড়", "Deductible Discounts"), `৳${(tax.deductible_discounts ?? 0).toLocaleString()}`],
                      [l("কাটার পর নিট কর", "Net Tax After Deductions"), `৳${(tax.net_tax_after_deductions ?? 0).toLocaleString()}`],
                    ].map(([label, val]) => (
                      <tr key={label} className="hover:bg-slate-50">
                        <td className="py-3 text-slate-600">{label}</td>
                        <td className="py-3 text-right font-medium text-slate-800">{val}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </>
          )}
        </div>
      )}

      {/* Health Score */}
      {tab === "health" && (
        <div className="space-y-4">
          {healthQ.isLoading ? <div className="space-y-3"><Skeleton className="h-40" /><LoadingRows n={5} /></div> : (
            <>
              <div className="bg-white border border-slate-200 rounded-xl p-6 text-center">
                <div className="inline-flex items-center justify-center w-24 h-24 rounded-full border-4 border-blue-500 mb-3">
                  <span className="text-3xl font-black text-blue-600">{health.score ?? 0}</span>
                </div>
                <p className="text-lg font-bold text-slate-800">{l("স্বাস্থ্য স্কোর", "Health Score")} — {l("গ্রেড", "Grade")} {health.grade}</p>
                <p className="text-sm text-slate-500 mt-1 max-w-md mx-auto">{lang === "bn" ? health.explanation_bn : health.explanation_en}</p>
              </div>
              <div className="bg-white border border-slate-200 rounded-xl p-5">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-slate-100">
                      <th className="text-left py-2 text-slate-500 font-medium">{l("উপাদান", "Component")}</th>
                      <th className="text-right py-2 pr-4 text-slate-500 font-medium">{l("স্কোর", "Score")}</th>
                      <th className="text-center py-2 text-slate-500 font-medium">{l("অবস্থা", "Status")}</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-50">
                    {((health.components ?? []) as any[]).map((c: any) => (
                      <tr key={c.name} className="hover:bg-slate-50">
                        <td className="py-3">
                          <div className="font-medium text-slate-800">{lang === "bn" ? c.name_bn : c.name}</div>
                        </td>
                        <td className="py-3 pr-4 text-right">
                          <span className="font-semibold text-slate-800">{c.score}</span>
                          <span className="text-slate-400 text-xs">/{c.max_score}</span>
                          <div className="h-1.5 bg-slate-100 rounded-full mt-1 w-24 ml-auto">
                            <div
                              className={cn("h-1.5 rounded-full", c.status === "GOOD" ? "bg-green-500" : c.status === "OK" ? "bg-yellow-500" : "bg-red-500")}
                              style={{ width: `${(c.score / c.max_score) * 100}%` }}
                            />
                          </div>
                        </td>
                        <td className="py-3 text-center">
                          <span className={cn("text-[11px] font-medium px-2 py-0.5 rounded border",
                            c.status === "GOOD" ? "bg-green-50 text-green-700 border-green-200" :
                            c.status === "OK" ? "bg-yellow-50 text-yellow-700 border-yellow-200" :
                            "bg-red-50 text-red-700 border-red-200"
                          )}>
                            {c.status}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </>
          )}
        </div>
      )}

      {/* Customer LTV */}
      {tab === "ltv" && (
        <div className="bg-white border border-slate-200 rounded-xl p-5">
          <h2 className="font-semibold text-slate-800 mb-4">{l("গ্রাহক লাইফটাইম ভ্যালু", "Customer Lifetime Value")}</h2>
          {ltvQ.isLoading ? <LoadingRows /> : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-slate-100">
                    <th className="text-left py-2 pr-4 text-slate-500 font-medium">{l("গ্রাহক", "Customer")}</th>
                    <th className="text-right py-2 pr-4 text-slate-500 font-medium">{l("অর্ডার", "Orders")}</th>
                    <th className="text-right py-2 pr-4 text-slate-500 font-medium">{l("মোট ব্যয়", "Total Spent")}</th>
                    <th className="text-right py-2 pr-4 text-slate-500 font-medium">{l("LTV ১২ মাস", "LTV 12m")}</th>
                    <th className="text-center py-2 text-slate-500 font-medium">{l("স্তর", "Tier")}</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-50">
                  {((ltvQ.data as any[]) ?? []).map((r: any) => (
                    <tr key={r.customer_id} className="hover:bg-slate-50">
                      <td className="py-3 pr-4">
                        <div className="font-medium text-slate-800">{r.customer_name}</div>
                        <div className="text-xs text-slate-400">{r.phone}</div>
                      </td>
                      <td className="py-3 pr-4 text-right text-slate-600">{r.total_orders}</td>
                      <td className="py-3 pr-4 text-right text-slate-600">৳{r.total_spent.toLocaleString()}</td>
                      <td className="py-3 pr-4 text-right font-semibold text-blue-700">৳{r.predicted_ltv_12m.toLocaleString()}</td>
                      <td className="py-3 text-center">
                        <span className={cn("text-[11px] font-medium px-2 py-0.5 rounded border",
                          r.segment === "PLATINUM" ? "bg-purple-50 text-purple-700 border-purple-200" :
                          r.segment === "GOLD" ? "bg-yellow-50 text-yellow-700 border-yellow-200" :
                          r.segment === "SILVER" ? "bg-slate-50 text-slate-600 border-slate-200" :
                          "bg-orange-50 text-orange-700 border-orange-200"
                        )}>
                          {r.segment}
                        </span>
                      </td>
                    </tr>
                  ))}
                  {((ltvQ.data as any[]) ?? []).length === 0 && (
                    <tr><td colSpan={5} className="py-8 text-center text-slate-400">
                      <Users className="h-8 w-8 mx-auto mb-2 opacity-30" />
                      {l("ডেটা নেই", "No data")}
                    </td></tr>
                  )}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* Churn Risk */}
      {tab === "churn" && (
        <div className="bg-white border border-slate-200 rounded-xl p-5">
          <h2 className="font-semibold text-slate-800 mb-4">{l("গ্রাহক চার্ন ঝুঁকি", "Customer Churn Risk")}</h2>
          {churnQ.isLoading ? <LoadingRows /> : (
            <>
              {((churnQ.data as any[]) ?? []).length === 0 ? (
                <div className="text-center py-12 text-slate-400">
                  <Users className="h-10 w-10 mx-auto mb-2 opacity-30" />
                  <p>{l("দুর্দান্ত! কোনো গ্রাহক হারানোর ঝুঁকিতে নেই।", "Great! No customers at churn risk.")}</p>
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-slate-100">
                        <th className="text-left py-2 pr-4 text-slate-500 font-medium">{l("গ্রাহক", "Customer")}</th>
                        <th className="text-right py-2 pr-4 text-slate-500 font-medium">{l("নিষ্ক্রিয় দিন", "Days Inactive")}</th>
                        <th className="text-right py-2 pr-4 text-slate-500 font-medium">{l("শেষ অর্ডার", "Last Order")}</th>
                        <th className="text-right py-2 pr-4 text-slate-500 font-medium">{l("মোট অর্ডার", "Total Orders")}</th>
                        <th className="text-center py-2 text-slate-500 font-medium">{l("ঝুঁকি", "Risk")}</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-50">
                      {((churnQ.data as any[]) ?? []).map((r: any) => (
                        <tr key={r.customer_id} className="hover:bg-slate-50">
                          <td className="py-3 pr-4">
                            <div className="font-medium text-slate-800">{r.customer_name}</div>
                            <div className="text-xs text-slate-400">{r.phone}</div>
                          </td>
                          <td className="py-3 pr-4 text-right font-medium text-red-600">{r.days_inactive} {l("দিন", "d")}</td>
                          <td className="py-3 pr-4 text-right text-slate-500">{r.last_order_date}</td>
                          <td className="py-3 pr-4 text-right text-slate-600">{r.total_orders}</td>
                          <td className="py-3 text-center">
                            <span className={cn("text-[11px] font-medium px-2 py-0.5 rounded border",
                              r.risk_level === "HIGH" ? "bg-red-50 text-red-700 border-red-200" :
                              r.risk_level === "MEDIUM" ? "bg-orange-50 text-orange-700 border-orange-200" :
                              "bg-yellow-50 text-yellow-700 border-yellow-200"
                            )}>
                              {r.risk_level}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </>
          )}
        </div>
      )}

      {/* Revenue Forecast */}
      {tab === "revenue" && (
        <div className="space-y-4">
          {forecastQ.isLoading ? <LoadingGrid n={3} /> : (
            <>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                <StatCard
                  label={l("গত ৩০ দিনের রাজস্ব", "Last 30d Revenue")}
                  value={`৳${(forecast.current_30d ?? 0).toLocaleString()}`}
                />
                <StatCard
                  label={l("পরবর্তী ৩০ দিনের পূর্বাভাস", "Predicted Next 30d")}
                  value={`৳${(forecast.predicted_next_30d ?? 0).toLocaleString()}`}
                  sub={`${forecast.growth_pct > 0 ? "+" : ""}${forecast.growth_pct ?? 0}%`}
                />
                <StatCard
                  label={l("প্রবণতা", "Trend")}
                  value={forecast.trend === "RISING" ? l("বাড়ছে ↑", "Rising ↑") :
                         forecast.trend === "FALLING" ? l("কমছে ↓", "Falling ↓") : l("স্থিতিশীল →", "Stable →")}
                  sub={forecast.confidence}
                />
              </div>
              {((forecast.daily_points ?? []) as any[]).length > 0 && (
                <div className="bg-white border border-slate-200 rounded-xl p-5">
                  <h3 className="font-semibold text-slate-700 mb-4">{l("দৈনিক রাজস্ব", "Daily Revenue")}</h3>
                  <div className="overflow-x-auto max-h-64 overflow-y-auto">
                    <table className="w-full text-sm">
                      <thead className="sticky top-0 bg-white">
                        <tr className="border-b border-slate-100">
                          <th className="text-left py-2 pr-4 text-slate-500 font-medium">{l("তারিখ", "Date")}</th>
                          <th className="text-right py-2 text-slate-500 font-medium">{l("রাজস্ব", "Revenue")}</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-50">
                        {((forecast.daily_points ?? []) as any[]).slice().reverse().map((p: any) => (
                          <tr key={p.date} className="hover:bg-slate-50">
                            <td className="py-2 pr-4 text-slate-600">{p.date}</td>
                            <td className="py-2 text-right font-medium text-slate-800">৳{p.revenue.toLocaleString()}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      )}
    </div>
  );
}
