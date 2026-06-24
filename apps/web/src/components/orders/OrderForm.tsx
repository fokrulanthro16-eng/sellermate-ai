"use client";

import { useState } from "react";
import { useForm, useFieldArray } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Loader2, Plus, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useCreateOrder } from "@/hooks/useOrders";
import { useCustomers } from "@/hooks/useCustomers";
import { useProducts } from "@/hooks/useProducts";
import type { PaymentMethod, OrderChannel } from "@/types";

const schema = z.object({
  customer_id: z.string().min(1, "গ্রাহক নির্বাচন করুন"),
  payment_method: z.string().min(1, "পেমেন্ট পদ্ধতি নির্বাচন করুন"),
  channel: z.string().optional(),
  delivery_address: z.string().optional(),
  discount_amount: z.string().optional(),
  shipping_cost: z.string().optional(),
  items: z.array(z.object({
    product_id: z.string().min(1),
    variant_id: z.string().min(1),
    quantity: z.number().min(1),
  })).min(1, "কমপক্ষে একটি পণ্য যোগ করুন"),
});
type FormData = z.infer<typeof schema>;

interface OrderFormProps {
  onSuccess?: () => void;
}

const PAYMENT_METHODS: { value: PaymentMethod; label: string }[] = [
  { value: "COD", label: "ক্যাশ অন ডেলিভারি" },
  { value: "BKASH", label: "বিকাশ" },
  { value: "NAGAD", label: "নগদ" },
  { value: "ROCKET", label: "রকেট" },
  { value: "BANK", label: "ব্যাংক" },
  { value: "CARD", label: "কার্ড" },
];

const CHANNELS: { value: OrderChannel; label: string }[] = [
  { value: "FACEBOOK", label: "ফেসবুক" },
  { value: "INSTAGRAM", label: "ইনস্টাগ্রাম" },
  { value: "WHATSAPP", label: "হোয়াটসঅ্যাপ" },
  { value: "WEBSITE", label: "ওয়েবসাইট" },
  { value: "DIRECT", label: "সরাসরি" },
  { value: "OTHER", label: "অন্যান্য" },
];

export default function OrderForm({ onSuccess }: OrderFormProps) {
  const createOrder = useCreateOrder();
  const { data: customersData } = useCustomers({ limit: 200 });
  const { data: productsData } = useProducts({ limit: 200, is_active: true });
  const customerList = Array.isArray(customersData?.items) ? customersData.items : [];
  const productList = Array.isArray(productsData?.items) ? productsData.items : [];
  const [selectedProductIds, setSelectedProductIds] = useState<string[]>([""]);

  const { register, handleSubmit, setValue, watch, control, formState: { errors } } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: { items: [{ product_id: "", variant_id: "", quantity: 1 }] },
  });

  const { fields, append, remove } = useFieldArray({ control, name: "items" });

  const onSubmit = async (data: FormData) => {
    await createOrder.mutateAsync({
      customer_id: data.customer_id,
      items: data.items,
      payment_method: data.payment_method as PaymentMethod,
      channel: data.channel as OrderChannel | undefined,
      delivery_address: data.delivery_address,
      discount_amount: data.discount_amount,
      shipping_cost: data.shipping_cost,
    });
    onSuccess?.();
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4 max-h-[70vh] overflow-y-auto pr-1">
      <div className="space-y-2">
        <Label>গ্রাহক</Label>
        <Select onValueChange={(v) => setValue("customer_id", v)}>
          <SelectTrigger>
            <SelectValue placeholder="গ্রাহক নির্বাচন করুন" />
          </SelectTrigger>
          <SelectContent>
            {customerList.map((c) => (
              <SelectItem key={c.id} value={c.id}>{c.name} ({c.phone})</SelectItem>
            ))}
          </SelectContent>
        </Select>
        {errors.customer_id && <p className="text-xs text-destructive">{errors.customer_id.message}</p>}
      </div>

      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <Label>পণ্য তালিকা</Label>
          <Button type="button" variant="ghost" size="sm"
            onClick={() => { append({ product_id: "", variant_id: "", quantity: 1 }); setSelectedProductIds([...selectedProductIds, ""]); }}>
            <Plus className="h-4 w-4 mr-1" /> যোগ করুন
          </Button>
        </div>
        {fields.map((field, i) => {
          const pid = selectedProductIds[i] || "";
          const product = productList.find((p) => p.id === pid);
          return (
            <div key={field.id} className="flex gap-2 items-start border rounded-lg p-3">
              <div className="flex-1 space-y-2">
                <Select onValueChange={(v) => {
                  const updated = [...selectedProductIds];
                  updated[i] = v;
                  setSelectedProductIds(updated);
                  setValue(`items.${i}.product_id`, v);
                  setValue(`items.${i}.variant_id`, "");
                }}>
                  <SelectTrigger className="text-sm">
                    <SelectValue placeholder="পণ্য" />
                  </SelectTrigger>
                  <SelectContent>
                    {productList.map((p) => (
                      <SelectItem key={p.id} value={p.id}>{p.name}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                {product && (
                  <Select onValueChange={(v) => setValue(`items.${i}.variant_id`, v)}>
                    <SelectTrigger className="text-sm">
                      <SelectValue placeholder="ভ্যারিয়েন্ট" />
                    </SelectTrigger>
                    <SelectContent>
                      {(product.variants || []).map((v) => (
                        <SelectItem key={v.id} value={v.id}>{v.name} (৳{v.price})</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                )}
                <Input type="number" min={1} placeholder="পরিমাণ"
                  {...register(`items.${i}.quantity`, { valueAsNumber: true })} className="text-sm" />
              </div>
              {fields.length > 1 && (
                <Button type="button" variant="ghost" size="icon" className="mt-1"
                  onClick={() => { remove(i); setSelectedProductIds(selectedProductIds.filter((_, j) => j !== i)); }}>
                  <Trash2 className="h-4 w-4 text-destructive" />
                </Button>
              )}
            </div>
          );
        })}
        {errors.items && <p className="text-xs text-destructive">{errors.items.message}</p>}
      </div>

      <div className="grid grid-cols-2 gap-3">
        <div className="space-y-2">
          <Label>পেমেন্ট পদ্ধতি</Label>
          <Select onValueChange={(v) => setValue("payment_method", v)}>
            <SelectTrigger><SelectValue placeholder="নির্বাচন করুন" /></SelectTrigger>
            <SelectContent>
              {PAYMENT_METHODS.map((m) => <SelectItem key={m.value} value={m.value}>{m.label}</SelectItem>)}
            </SelectContent>
          </Select>
        </div>
        <div className="space-y-2">
          <Label>চ্যানেল</Label>
          <Select onValueChange={(v) => setValue("channel", v)}>
            <SelectTrigger><SelectValue placeholder="নির্বাচন করুন" /></SelectTrigger>
            <SelectContent>
              {CHANNELS.map((c) => <SelectItem key={c.value} value={c.value}>{c.label}</SelectItem>)}
            </SelectContent>
          </Select>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3">
        <div className="space-y-2">
          <Label>ছাড় (টাকা)</Label>
          <Input type="number" placeholder="0" {...register("discount_amount")} />
        </div>
        <div className="space-y-2">
          <Label>শিপিং চার্জ</Label>
          <Input type="number" placeholder="0" {...register("shipping_cost")} />
        </div>
      </div>

      <div className="space-y-2">
        <Label>ডেলিভারি ঠিকানা</Label>
        <Input placeholder="সম্পূর্ণ ঠিকানা" {...register("delivery_address")} />
      </div>

      <Button type="submit" className="w-full" disabled={createOrder.isPending}>
        {createOrder.isPending ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
        অর্ডার তৈরি করুন
      </Button>
    </form>
  );
}
