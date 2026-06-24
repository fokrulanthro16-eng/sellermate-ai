"use client";

import { useState } from "react";
import Link from "next/link";
import { format, parseISO } from "date-fns";
import {
  Plus, Search, Users, UserCheck, Facebook,
  MessageCircle, Instagram, UserPlus, Store, Eye, ShoppingBag,
} from "lucide-react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { useCustomers, useCreateCustomer } from "@/hooks/useCustomers";
import { useDashboard } from "@/hooks/useAnalytics";
import { useLang } from "@/contexts/LangContext";
import { formatCurrency, safeNum, getInitials, cn } from "@/lib/utils";

const LIMIT = 30;

const schema = z.object({
  name:     z.string().min(1),
  phone:    z.string().min(11),
  email:    z.string().email().optional().or(z.literal("")),
  district: z.string().optional(),
});
type FormData = z.infer<typeof schema>;

const SOURCE_ICONS: Record<string, React.ElementType> = {
  FACEBOOK: Facebook, WHATSAPP: MessageCircle, INSTAGRAM: Instagram,
  MANUAL: UserPlus, WALK_IN: Store,
};
const SOURCE_LABELS: Record<string, string> = {
  FACEBOOK: "Facebook", WHATSAPP: "WhatsApp", INSTAGRAM: "Instagram",
  MANUAL: "Manual", WALK_IN: "Walk-in",
};
const TAG_STYLE: Record<string, string> = {
  VIP:          "bg-amber-100 text-amber-800 border-amber-200",
  "নিয়মিত":    "bg-blue-100 text-blue-800 border-blue-200",
  "নতুন":       "bg-green-100 text-green-800 border-green-200",
  "সন্দেহজনক":  "bg-red-100 text-red-700 border-red-200",
  "ফলো-আপ":     "bg-violet-100 text-violet-800 border-violet-200",
  "follow-up":  "bg-violet-100 text-violet-800 border-violet-200",
};

export default function CustomersPage() {
  const { t, lang } = useLang();
  const label = (bn: string, en: string) => lang === "bn" ? bn : en;

  const [search, setSearch] = useState("");
  const [source, setSource] = useState("");
  const [page, setPage] = useState(1);
  const [newOpen, setNewOpen] = useState(false);

  const { data, isLoading } = useCustomers({ page, limit: LIMIT, search: search || undefined, source: source || undefined });
  const { data: dashboard } = useDashboard();
  const createCustomer = useCreateCustomer();
  const { register, handleSubmit, reset, formState: { errors } } = useForm<FormData>({
    resolver: zodResolver(schema),
  });

  const SOURCE_OPTIONS = [
    { value: "",          label: label("সব উৎস", "All Sources") },
    { value: "FACEBOOK",  label: "Facebook" },
    { value: "WHATSAPP",  label: "WhatsApp" },
    { value: "INSTAGRAM", label: "Instagram" },
    { value: "MANUAL",    label: "Manual" },
    { value: "WALK_IN",   label: "Walk-in" },
  ];

  const customers = Array.isArray(data?.items) ? data.items : [];
  const total      = data?.total ?? 0;
  const totalPages = Math.max(1, Math.ceil(total / LIMIT));

  const repeatCount = safeNum(dashboard?.repeat_customers);
  const avgOrder    = safeNum(dashboard?.average_order_value);

  const onSubmit = async (formData: FormData) => {
    await createCustomer.mutateAsync(formData);
    reset();
    setNewOpen(false);
  };

  return (
    <div className="space-y-4 max-w-[1500px]">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold">{label("গ্রাহক ব্যবস্থাপনা", "Customer Management")}</h1>
          <p className="text-sm text-muted-foreground">
            {total > 0
              ? `${total} ${label("জন গ্রাহক", "customers registered")}`
              : label("গ্রাহকদের পরিচালনা করুন", "Manage your customers")}
          </p>
        </div>
        <Button onClick={() => setNewOpen(true)} size="sm" className="gap-1.5">
          <Plus className="h-3.5 w-3.5" /> {label("নতুন গ্রাহক", "Add Customer")}
        </Button>
      </div>

      {/* KPI Row */}
      <div className="grid grid-cols-3 gap-3">
        <div className="kpi-card">
          <div className="flex items-center gap-2.5">
            <div className="h-8 w-8 rounded bg-violet-100 dark:bg-violet-900/40 flex items-center justify-center shrink-0">
              <Users className="h-4 w-4 text-violet-700 dark:text-violet-400" />
            </div>
            <div>
              <p className="kpi-label">{label("মোট গ্রাহক", "Total Customers")}</p>
              <p className="kpi-value">{total}</p>
            </div>
          </div>
        </div>
        <div className="kpi-card">
          <div className="flex items-center gap-2.5">
            <div className="h-8 w-8 rounded bg-emerald-100 dark:bg-emerald-900/40 flex items-center justify-center shrink-0">
              <UserCheck className="h-4 w-4 text-emerald-700 dark:text-emerald-400" />
            </div>
            <div>
              <p className="kpi-label">{label("নিয়মিত গ্রাহক", "Repeat Customers")}</p>
              <p className="kpi-value">{repeatCount}</p>
            </div>
          </div>
        </div>
        <div className="kpi-card">
          <div className="flex items-center gap-2.5">
            <div className="h-8 w-8 rounded bg-blue-100 dark:bg-blue-900/40 flex items-center justify-center shrink-0">
              <ShoppingBag className="h-4 w-4 text-blue-700 dark:text-blue-400" />
            </div>
            <div>
              <p className="kpi-label">{label("গড় অর্ডার মূল্য", "Avg Order Value")}</p>
              <p className="kpi-value">{formatCurrency(avgOrder)}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Search + Filters */}
      <div className="flex gap-2 flex-wrap items-center">
        <div className="relative flex-1 min-w-[200px] max-w-sm">
          <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground" />
          <Input
            placeholder={label("নাম, ফোন, জেলা...", "Name, phone, district...")}
            value={search}
            onChange={(e) => { setSearch(e.target.value); setPage(1); }}
            className="pl-8 h-8 text-sm"
          />
        </div>
        <Select value={source} onValueChange={(v) => { setSource(v); setPage(1); }}>
          <SelectTrigger className="w-40 h-8 text-sm">
            <SelectValue placeholder={label("উৎস", "Source")} />
          </SelectTrigger>
          <SelectContent>
            {SOURCE_OPTIONS.map((o) => <SelectItem key={o.value} value={o.value}>{o.label}</SelectItem>)}
          </SelectContent>
        </Select>
        {(search || source) && (
          <Button variant="ghost" size="sm" className="h-8 text-xs"
            onClick={() => { setSearch(""); setSource(""); setPage(1); }}>
            {label("ফিল্টার মুছুন", "Clear")}
          </Button>
        )}
        {total > 0 && (
          <span className="ml-auto text-xs text-muted-foreground">{total} {label("জন", "customers")}</span>
        )}
      </div>

      {/* Customers Table */}
      <div className="admin-card overflow-hidden">
        {isLoading ? (
          <div className="p-4 space-y-2">
            {Array.from({ length: 8 }).map((_, i) => <Skeleton key={i} className="h-10 w-full" />)}
          </div>
        ) : customers.length === 0 ? (
          <div className="py-16 text-center space-y-2">
            <Users className="h-10 w-10 mx-auto text-muted-foreground/25" />
            <p className="text-sm text-muted-foreground">{label("কোনো গ্রাহক পাওয়া যায়নি", "No customers found")}</p>
            <Button size="sm" onClick={() => setNewOpen(true)} className="gap-1.5">
              <Plus className="h-3.5 w-3.5" /> {label("গ্রাহক যোগ করুন", "Add Customer")}
            </Button>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="commerce-table">
              <thead>
                <tr>
                  <th>{label("গ্রাহক", "Customer")}</th>
                  <th>{label("ফোন", "Phone")}</th>
                  <th>{label("উৎস", "Source")}</th>
                  <th>{label("জেলা", "District")}</th>
                  <th className="text-right">{label("অর্ডার", "Orders")}</th>
                  <th className="text-right">{label("মোট খরচ", "Total Spent")}</th>
                  <th>{label("শেষ অর্ডার", "Last Order")}</th>
                  <th>{label("ট্যাগ", "Tags")}</th>
                  <th>{label("অ্যাকশন", "Action")}</th>
                </tr>
              </thead>
              <tbody>
                {customers.map((customer) => {
                  const tags = (customer.tags || []).slice(0, 2);
                  const isVIP = tags.includes("VIP");
                  const isSuspicious = tags.includes("সন্দেহজনক");
                  const SourceIcon = SOURCE_ICONS[customer.source ?? ""] ?? Users;
                  const lastOrder = customer.last_order_at
                    ? format(parseISO(customer.last_order_at), "dd MMM yy")
                    : "—";

                  return (
                    <tr key={customer.id}>
                      <td>
                        <div className="flex items-center gap-2">
                          <Avatar className="h-7 w-7 shrink-0">
                            <AvatarFallback className={cn(
                              "text-[10px] font-bold rounded",
                              isVIP ? "bg-amber-100 text-amber-800" : "bg-primary/10 text-primary"
                            )}>
                              {getInitials(customer.name)}
                            </AvatarFallback>
                          </Avatar>
                          <span className={cn("text-sm font-medium", isSuspicious && "text-red-600 dark:text-red-400")}>
                            {customer.name}
                          </span>
                        </div>
                      </td>
                      <td>
                        <span className="text-xs font-mono text-muted-foreground">{customer.phone}</span>
                      </td>
                      <td>
                        <div className="flex items-center gap-1 text-xs text-muted-foreground">
                          <SourceIcon className="h-3 w-3 shrink-0" />
                          <span>{SOURCE_LABELS[customer.source ?? ""] ?? customer.source ?? "—"}</span>
                        </div>
                      </td>
                      <td>
                        <span className="text-xs text-muted-foreground">{customer.district || "—"}</span>
                      </td>
                      <td className="text-right">
                        <span className="text-sm font-semibold">{customer.total_orders}</span>
                      </td>
                      <td className="text-right">
                        <span className={cn(
                          "text-sm font-semibold",
                          isVIP ? "text-amber-700 dark:text-amber-400" : "text-foreground"
                        )}>
                          {formatCurrency(customer.total_spent)}
                        </span>
                      </td>
                      <td>
                        <span className="text-xs text-muted-foreground whitespace-nowrap">{lastOrder}</span>
                      </td>
                      <td>
                        <div className="flex items-center gap-1 flex-wrap">
                          {tags.map((tag) => (
                            <span
                              key={tag}
                              className={cn(
                                "inline-flex items-center px-1.5 py-0 rounded text-[10px] font-semibold border",
                                TAG_STYLE[tag] ?? "bg-secondary text-secondary-foreground border-border"
                              )}
                            >
                              {tag}
                            </span>
                          ))}
                        </div>
                      </td>
                      <td>
                        <Link href={`/customers/${customer.id}`}>
                          <Button variant="ghost" size="sm" className="h-6 px-2 text-xs gap-1">
                            <Eye className="h-3 w-3" />
                            {label("দেখুন", "View")}
                          </Button>
                        </Link>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Pagination */}
      {total > LIMIT && (
        <div className="flex items-center justify-between text-sm">
          <span className="text-muted-foreground text-xs">
            {label("পৃষ্ঠা", "Page")} {page} / {totalPages} · {total} {label("জন", "customers")}
          </span>
          <div className="flex gap-2">
            <Button variant="outline" size="sm" className="h-7 text-xs" disabled={page === 1} onClick={() => setPage((p) => p - 1)}>
              {label("আগের", "Prev")}
            </Button>
            <Button variant="outline" size="sm" className="h-7 text-xs" disabled={page >= totalPages} onClick={() => setPage((p) => p + 1)}>
              {label("পরের", "Next")}
            </Button>
          </div>
        </div>
      )}

      {/* New Customer Dialog */}
      <Dialog open={newOpen} onOpenChange={setNewOpen}>
        <DialogContent>
          <DialogHeader><DialogTitle>{label("নতুন গ্রাহক যোগ করুন", "Add New Customer")}</DialogTitle></DialogHeader>
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <div className="space-y-1.5">
              <Label className="text-sm">{label("নাম", "Full Name")} *</Label>
              <Input {...register("name")} placeholder={label("গ্রাহকের পূর্ণ নাম", "Customer full name")} className="h-8 text-sm" />
              {errors.name && <p className="text-xs text-destructive">{label("নাম আবশ্যক", "Name is required")}</p>}
            </div>
            <div className="space-y-1.5">
              <Label className="text-sm">{label("ফোন নম্বর", "Phone Number")} *</Label>
              <Input {...register("phone")} placeholder="+8801XXXXXXXXX" className="h-8 text-sm font-mono" />
              {errors.phone && <p className="text-xs text-destructive">{label("সঠিক ফোন নম্বর দিন", "Enter valid phone number")}</p>}
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1.5">
                <Label className="text-sm">{label("ইমেইল", "Email")} ({label("ঐচ্ছিক", "optional")})</Label>
                <Input {...register("email")} placeholder="email@example.com" className="h-8 text-sm" />
              </div>
              <div className="space-y-1.5">
                <Label className="text-sm">{label("জেলা", "District")} ({label("ঐচ্ছিক", "optional")})</Label>
                <Input {...register("district")} placeholder={label("যেমন: ঢাকা", "e.g. Dhaka")} className="h-8 text-sm" />
              </div>
            </div>
            <div className="flex gap-2 pt-1">
              <Button type="button" variant="outline" className="flex-1 h-9 text-sm" onClick={() => setNewOpen(false)}>
                {label("বাতিল", "Cancel")}
              </Button>
              <Button type="submit" className="flex-1 h-9 text-sm" disabled={createCustomer.isPending}>
                {createCustomer.isPending ? label("যোগ করা হচ্ছে...", "Adding...") : label("গ্রাহক যোগ করুন", "Add Customer")}
              </Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
