"use client";

import { useState } from "react";
import { Plus, Trash2, Edit2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Badge } from "@/components/ui/badge";
import { useAddVariant, useUpdateVariant, useDeleteVariant } from "@/hooks/useProducts";
import { formatCurrency } from "@/lib/utils";
import type { Product, ProductVariant } from "@/types";

interface VariantEditorProps {
  product: Product;
}

export default function VariantEditor({ product }: VariantEditorProps) {
  const addVariant = useAddVariant();
  const updateVariant = useUpdateVariant();
  const deleteVariant = useDeleteVariant();
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingVariant, setEditingVariant] = useState<ProductVariant | null>(null);
  const [form, setForm] = useState({ name: "", sku: "", price: "", stock_quantity: 0, low_stock_alert: 10 });

  const openAdd = () => {
    setEditingVariant(null);
    setForm({ name: "", sku: "", price: "", stock_quantity: 0, low_stock_alert: 10 });
    setDialogOpen(true);
  };

  const openEdit = (v: ProductVariant) => {
    setEditingVariant(v);
    setForm({ name: v.name, sku: v.sku, price: v.price, stock_quantity: v.stock_quantity, low_stock_alert: v.low_stock_alert });
    setDialogOpen(true);
  };

  const handleSave = async () => {
    if (editingVariant) {
      await updateVariant.mutateAsync({ productId: product.id, variantId: editingVariant.id, ...form });
    } else {
      await addVariant.mutateAsync({ productId: product.id, ...form });
    }
    setDialogOpen(false);
  };

  const handleDelete = async (variantId: string) => {
    if (confirm("এই ভ্যারিয়েন্ট মুছে ফেলবেন?")) {
      await deleteVariant.mutateAsync({ productId: product.id, variantId });
    }
  };

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle className="text-base">ভ্যারিয়েন্ট</CardTitle>
        <Button size="sm" onClick={openAdd}><Plus className="h-4 w-4 mr-1" /> যোগ করুন</Button>
      </CardHeader>
      <CardContent>
        {product.variants.length === 0 ? (
          <p className="text-sm text-muted-foreground text-center py-4">কোনো ভ্যারিয়েন্ট নেই</p>
        ) : (
          <div className="space-y-2">
            {product.variants.map((v) => (
              <div key={v.id} className="flex items-center justify-between p-3 rounded-lg border">
                <div>
                  <p className="text-sm font-medium">{v.name}</p>
                  <p className="text-xs text-muted-foreground">{v.sku} · স্টক: {v.stock_quantity}</p>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-sm font-bold">{formatCurrency(v.price)}</span>
                  <Badge variant={v.stock_quantity > v.low_stock_alert ? "success" : "warning"} className="text-xs">
                    {v.stock_quantity > v.low_stock_alert ? "পর্যাপ্ত" : "কম"}
                  </Badge>
                  <Button variant="ghost" size="icon" className="h-7 w-7" onClick={() => openEdit(v)}>
                    <Edit2 className="h-3.5 w-3.5" />
                  </Button>
                  <Button variant="ghost" size="icon" className="h-7 w-7 text-destructive hover:text-destructive"
                    onClick={() => handleDelete(v.id)}>
                    <Trash2 className="h-3.5 w-3.5" />
                  </Button>
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>

      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{editingVariant ? "ভ্যারিয়েন্ট সম্পাদনা" : "নতুন ভ্যারিয়েন্ট"}</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-2">
                <Label>নাম</Label>
                <Input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} placeholder="White — M" />
              </div>
              <div className="space-y-2">
                <Label>SKU</Label>
                <Input value={form.sku} onChange={(e) => setForm({ ...form, sku: e.target.value })} placeholder="SKU-001" />
              </div>
            </div>
            <div className="grid grid-cols-3 gap-3">
              <div className="space-y-2">
                <Label>মূল্য</Label>
                <Input type="number" value={form.price} onChange={(e) => setForm({ ...form, price: e.target.value })} placeholder="0" />
              </div>
              <div className="space-y-2">
                <Label>স্টক</Label>
                <Input type="number" value={form.stock_quantity} onChange={(e) => setForm({ ...form, stock_quantity: parseInt(e.target.value) || 0 })} />
              </div>
              <div className="space-y-2">
                <Label>সতর্কতা</Label>
                <Input type="number" value={form.low_stock_alert} onChange={(e) => setForm({ ...form, low_stock_alert: parseInt(e.target.value) || 0 })} />
              </div>
            </div>
            <Button className="w-full" onClick={handleSave} disabled={addVariant.isPending || updateVariant.isPending}>
              সংরক্ষণ করুন
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </Card>
  );
}
