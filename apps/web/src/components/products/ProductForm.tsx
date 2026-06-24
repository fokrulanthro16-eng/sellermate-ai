"use client";

import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import type { Product } from "@/types";

const CATEGORIES = [
  "FASHION_CLOTHING", "FOOD_BEVERAGE", "ELECTRONICS", "HOME_DECOR",
  "BEAUTY_COSMETICS", "HANDICRAFTS", "BOOKS_STATIONERY", "SPORTS_FITNESS", "OTHER"
];

const CATEGORY_LABELS: Record<string, string> = {
  FASHION_CLOTHING: "ফ্যাশন ও পোশাক",
  FOOD_BEVERAGE: "খাদ্য ও পানীয়",
  ELECTRONICS: "ইলেকট্রনিক্স",
  HOME_DECOR: "গৃহসজ্জা",
  BEAUTY_COSMETICS: "সৌন্দর্য পণ্য",
  HANDICRAFTS: "হস্তশিল্প",
  BOOKS_STATIONERY: "বই ও স্টেশনারি",
  SPORTS_FITNESS: "খেলাধুলা",
  OTHER: "অন্যান্য",
};

const schema = z.object({
  name: z.string().min(1, "পণ্যের নাম আবশ্যক"),
  category: z.string().min(1, "বিভাগ নির্বাচন করুন"),
  base_price: z.string().min(1, "মূল্য আবশ্যক"),
  description: z.string().optional(),
});
type FormData = z.infer<typeof schema>;

interface ProductFormProps {
  product?: Product;
  onSubmit: (data: FormData) => Promise<void>;
  loading?: boolean;
}

export default function ProductForm({ product, onSubmit, loading }: ProductFormProps) {
  const { register, handleSubmit, setValue, formState: { errors } } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: product ? {
      name: product.name,
      category: product.category,
      base_price: product.base_price,
      description: product.description,
    } : undefined,
  });

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <div className="space-y-2">
        <Label htmlFor="name">পণ্যের নাম</Label>
        <Input id="name" placeholder="পণ্যের নাম লিখুন" {...register("name")} />
        {errors.name && <p className="text-xs text-destructive">{errors.name.message}</p>}
      </div>

      <div className="space-y-2">
        <Label>বিভাগ</Label>
        <Select defaultValue={product?.category} onValueChange={(v) => setValue("category", v)}>
          <SelectTrigger>
            <SelectValue placeholder="বিভাগ নির্বাচন করুন" />
          </SelectTrigger>
          <SelectContent>
            {CATEGORIES.map((cat) => (
              <SelectItem key={cat} value={cat}>{CATEGORY_LABELS[cat]}</SelectItem>
            ))}
          </SelectContent>
        </Select>
        {errors.category && <p className="text-xs text-destructive">{errors.category.message}</p>}
      </div>

      <div className="space-y-2">
        <Label htmlFor="base_price">মূল মূল্য (টাকা)</Label>
        <Input id="base_price" type="number" step="0.01" placeholder="0.00" {...register("base_price")} />
        {errors.base_price && <p className="text-xs text-destructive">{errors.base_price.message}</p>}
      </div>

      <div className="space-y-2">
        <Label htmlFor="description">বিবরণ (ঐচ্ছিক)</Label>
        <Input id="description" placeholder="পণ্যের বিবরণ" {...register("description")} />
      </div>

      <Button type="submit" className="w-full" disabled={loading}>
        {loading ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
        {product ? "আপডেট করুন" : "পণ্য তৈরি করুন"}
      </Button>
    </form>
  );
}
