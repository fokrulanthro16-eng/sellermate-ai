"use client";

import { useState } from "react";
import { useInventory, useAdjustStock } from "@/hooks/useInventory";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Loader2 } from "lucide-react";

interface AdjustmentFormProps {
  onSuccess?: () => void;
}

export default function AdjustmentForm({ onSuccess }: AdjustmentFormProps) {
  const { data: inventoryData } = useInventory({ limit: 200 });
  const inventoryList = Array.isArray(inventoryData?.items) ? inventoryData.items : [];
  const adjustMutation = useAdjustStock();
  const [variantId, setVariantId] = useState("");
  const [quantity, setQuantity] = useState("");
  const [note, setNote] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!variantId || !quantity) return;
    await adjustMutation.mutateAsync([{
      variant_id: variantId,
      quantity_change: parseInt(quantity),
      note: note || undefined,
    }]);
    setVariantId("");
    setQuantity("");
    setNote("");
    onSuccess?.();
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="space-y-2">
        <Label>পণ্য ভ্যারিয়েন্ট</Label>
        <Select value={variantId} onValueChange={setVariantId}>
          <SelectTrigger>
            <SelectValue placeholder="ভ্যারিয়েন্ট নির্বাচন করুন" />
          </SelectTrigger>
          <SelectContent>
            {inventoryList.map((item) => (
              <SelectItem key={item.variant_id} value={item.variant_id}>
                {item.product_name} — {item.variant_name} (স্টক: {item.stock_quantity})
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <div className="space-y-2">
        <Label>পরিমাণ পরিবর্তন</Label>
        <Input
          type="number"
          placeholder="ধনাত্মক (+) বা ঋণাত্মক (-) সংখ্যা"
          value={quantity}
          onChange={(e) => setQuantity(e.target.value)}
        />
        <p className="text-xs text-muted-foreground">যেমন: +50 (যোগ) বা -10 (বিয়োগ)</p>
      </div>

      <div className="space-y-2">
        <Label>নোট (ঐচ্ছিক)</Label>
        <Input
          placeholder="কারণ বা মন্তব্য"
          value={note}
          onChange={(e) => setNote(e.target.value)}
        />
      </div>

      <Button type="submit" className="w-full" disabled={adjustMutation.isPending || !variantId || !quantity}>
        {adjustMutation.isPending ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
        স্টক আপডেট করুন
      </Button>
    </form>
  );
}
