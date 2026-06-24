"use client";

import { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { ArrowLeft, Phone, Mail, MapPin, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Skeleton } from "@/components/ui/skeleton";
import { Input } from "@/components/ui/input";
import CustomerOrderHistory from "@/components/customers/CustomerOrderHistory";
import { useCustomer, useAddTag, useRemoveTag } from "@/hooks/useCustomers";
import { formatCurrency, getInitials } from "@/lib/utils";

export default function CustomerDetailPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const { data: customer, isLoading } = useCustomer(id);
  const addTag = useAddTag();
  const removeTag = useRemoveTag();
  const [newTag, setNewTag] = useState("");

  if (isLoading) return <div className="max-w-3xl mx-auto space-y-4"><Skeleton className="h-8 w-48" /><Skeleton className="h-48 w-full" /></div>;
  if (!customer) return <p className="text-center text-muted-foreground py-12">গ্রাহক পাওয়া যায়নি</p>;

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div className="flex items-center gap-3">
        <Button variant="ghost" size="icon" onClick={() => router.back()}><ArrowLeft className="h-4 w-4" /></Button>
        <h1 className="text-2xl font-bold">গ্রাহক প্রোফাইল</h1>
      </div>
      <Card>
        <CardContent className="p-6">
          <div className="flex items-start gap-4">
            <Avatar className="h-16 w-16">
              <AvatarFallback className="text-lg bg-primary/10 text-primary">{getInitials(customer.name)}</AvatarFallback>
            </Avatar>
            <div className="flex-1">
              <h2 className="text-xl font-bold">{customer.name}</h2>
              <div className="mt-2 space-y-1">
                {customer.phone && <div className="flex items-center gap-2 text-sm text-muted-foreground"><Phone className="h-3.5 w-3.5" />{customer.phone}</div>}
                {customer.email && <div className="flex items-center gap-2 text-sm text-muted-foreground"><Mail className="h-3.5 w-3.5" />{customer.email}</div>}
                {customer.district && <div className="flex items-center gap-2 text-sm text-muted-foreground"><MapPin className="h-3.5 w-3.5" />{customer.district}</div>}
              </div>
            </div>
            <div className="text-right">
              <p className="text-2xl font-bold text-primary">{formatCurrency(customer.total_spent)}</p>
              <p className="text-sm text-muted-foreground">মোট ব্যয়</p>
              <p className="text-lg font-semibold mt-1">{customer.total_orders}</p>
              <p className="text-sm text-muted-foreground">অর্ডার</p>
            </div>
          </div>
        </CardContent>
      </Card>
      <Card>
        <CardHeader><CardTitle className="text-base">ট্যাগ</CardTitle></CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-2 mb-3">
            {customer.tags?.map((tag) => (
              <Badge key={tag} variant="secondary" className="gap-1">
                {tag}
                <button onClick={() => removeTag.mutate({ customerId: id, tag })} className="hover:text-destructive"><X className="h-3 w-3" /></button>
              </Badge>
            ))}
            {(!customer.tags || customer.tags.length === 0) && <p className="text-sm text-muted-foreground">কোনো ট্যাগ নেই</p>}
          </div>
          <div className="flex gap-2">
            <Input value={newTag} onChange={(e) => setNewTag(e.target.value)}
              onKeyDown={(e) => { if (e.key === "Enter") { e.preventDefault(); addTag.mutateAsync({ customerId: id, tag: newTag.trim() }).then(() => setNewTag("")); } }}
              placeholder="নতুন ট্যাগ (Enter চাপুন)" className="flex-1" />
            <Button size="sm" disabled={!newTag.trim() || addTag.isPending}
              onClick={() => addTag.mutateAsync({ customerId: id, tag: newTag.trim() }).then(() => setNewTag(""))}>
              যোগ করুন
            </Button>
          </div>
        </CardContent>
      </Card>
      <CustomerOrderHistory customerId={id} />
    </div>
  );
}
