"use client";

import { useState, useRef } from "react";
import { ExternalLink, Upload, Save, Store, Image as ImageIcon, Phone, MapPin, Globe, CheckCircle2, XCircle, AlertTriangle } from "lucide-react";
import { toast } from "sonner";
import { useMerchantProfile, useUpdateMerchant, useUploadImage, useUploadLogo, useLaunchChecklist } from "@/hooks/useMerchant";

function LaunchChecklist() {
  const { data } = useLaunchChecklist();
  if (!data) return null;
  return (
    <div className="glass-card rounded-2xl p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-semibold text-gray-900">Launch Checklist</h3>
        <span className="text-sm font-bold text-indigo-600">{data.pct}%</span>
      </div>
      <div className="w-full bg-gray-200 rounded-full h-2 mb-4">
        <div className="bg-indigo-600 h-2 rounded-full transition-all" style={{ width: `${data.pct}%` }} />
      </div>
      <div className="space-y-2">
        {data.items.map((item) => (
          <div key={item.id} className="flex items-center gap-3">
            {item.done
              ? <CheckCircle2 className="w-4 h-4 text-green-500 shrink-0" />
              : <XCircle className="w-4 h-4 text-gray-300 shrink-0" />}
            <div className="flex-1 min-w-0">
              <p className={`text-sm font-medium ${item.done ? "text-gray-900" : "text-gray-500"}`}>{item.label}</p>
              {item.detail && !item.done && <p className="text-xs text-gray-400">{item.detail}</p>}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function ImageUploader({ label, value, onUpload, accept = "image/*" }: {
  label: string;
  value?: string | null;
  onUpload: (url: string) => void;
  accept?: string;
}) {
  const uploadMut = useUploadImage();
  const inputRef = useRef<HTMLInputElement>(null);

  async function handleFile(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    try {
      const result = await uploadMut.mutateAsync(file);
      onUpload(result.url);
      toast.success(`${label} uploaded`);
    } catch {
      toast.error("Upload failed");
    }
  }

  return (
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-1">{label}</label>
      <div
        className="border-2 border-dashed border-gray-300 rounded-xl p-4 flex flex-col items-center justify-center gap-2 cursor-pointer hover:border-indigo-400 hover:bg-indigo-50/50 transition-colors min-h-[100px]"
        onClick={() => inputRef.current?.click()}
      >
        {value ? (
          <img src={value} alt={label} className="max-h-24 rounded-lg object-cover" />
        ) : (
          <>
            <Upload className="w-6 h-6 text-gray-400" />
            <p className="text-sm text-gray-500">Click to upload</p>
          </>
        )}
        {uploadMut.isPending && <p className="text-xs text-indigo-600">Uploading...</p>}
      </div>
      <input ref={inputRef} type="file" accept={accept} className="hidden" onChange={handleFile} />
    </div>
  );
}

function LogoUploader({ label, value, onUpload }: { label: string; value?: string | null; onUpload: (url: string) => void }) {
  const uploadMut = useUploadLogo();
  const inputRef = useRef<HTMLInputElement>(null);

  async function handleFile(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    try {
      const result = await uploadMut.mutateAsync(file);
      onUpload(result.url);
      toast.success("Logo uploaded");
    } catch {
      toast.error("Upload failed");
    }
  }

  return (
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-1">{label}</label>
      <div
        className="w-20 h-20 rounded-2xl border-2 border-dashed border-gray-300 flex items-center justify-center cursor-pointer hover:border-indigo-400 hover:bg-indigo-50/50 transition-colors overflow-hidden"
        onClick={() => inputRef.current?.click()}
      >
        {value
          ? <img src={value} alt="Logo" className="w-full h-full object-cover" />
          : <ImageIcon className="w-8 h-8 text-gray-400" />}
      </div>
      {uploadMut.isPending && <p className="text-xs text-indigo-600 mt-1">Uploading...</p>}
      <input ref={inputRef} type="file" accept="image/*" className="hidden" onChange={handleFile} />
    </div>
  );
}

function slugify(text: string) {
  return text.toLowerCase().replace(/[^\w\s-]/g, "").replace(/[\s_-]+/g, "-").replace(/^-+|-+$/g, "").slice(0, 40);
}

export default function StoreBuilderPage() {
  const { data: merchant, isLoading, isError } = useMerchantProfile();
  const updateMerchant = useUpdateMerchant();

  const [form, setForm] = useState<{
    store_slug: string;
    business_name: string;
    store_description: string;
    logo_url: string;
    store_banner_url: string;
    district: string;
    address: string;
    whatsapp_phone: string;
  } | null>(null);

  // Init form from merchant data once loaded
  if (merchant && !form) {
    setForm({
      store_slug: merchant.store_slug || "",
      business_name: merchant.business_name || "",
      store_description: merchant.store_description || "",
      logo_url: merchant.logo_url || "",
      store_banner_url: merchant.store_banner_url || "",
      district: merchant.district || "",
      address: merchant.address || "",
      whatsapp_phone: merchant.whatsapp_phone || "",
    });
  }

  // On query error unblock the form with empty defaults so it never stays stuck
  if (isError && !form) {
    setForm({
      store_slug: "",
      business_name: "",
      store_description: "",
      logo_url: "",
      store_banner_url: "",
      district: "",
      address: "",
      whatsapp_phone: "",
    });
  }

  function set<K extends keyof NonNullable<typeof form>>(key: K, val: string) {
    setForm((p) => p ? { ...p, [key]: val } : p);
  }

  async function handleSave() {
    if (!form) return;
    await updateMerchant.mutateAsync({
      store_slug: form.store_slug || undefined,
      business_name: form.business_name,
      store_description: form.store_description || undefined,
      logo_url: form.logo_url || undefined,
      store_banner_url: form.store_banner_url || undefined,
      district: form.district || undefined,
      address: form.address || undefined,
      whatsapp_phone: form.whatsapp_phone || undefined,
    } as any);
  }

  if (isLoading) {
    return (
      <div className="p-8 text-center text-gray-500">Loading store settings...</div>
    );
  }

  // form is always set at this point (merchant loaded or error fallback applied above)
  if (!form) return null;

  const previewUrl = form.store_slug ? `/store/${form.store_slug}` : null;

  return (
    <div className="max-w-5xl mx-auto p-6 space-y-6">
      {isError && (
        <div className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-amber-50 border border-amber-200 text-amber-800 text-sm">
          <AlertTriangle className="w-4 h-4 shrink-0" />
          Could not load store settings from server. Fill in your details and save.
        </div>
      )}
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <Store className="w-6 h-6 text-indigo-600" /> Store Builder
          </h1>
          <p className="text-gray-500 mt-0.5">Customize your public storefront</p>
        </div>
        <div className="flex gap-2">
          {previewUrl && (
            <a
              href={previewUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-1.5 px-4 py-2 border border-gray-300 rounded-xl text-sm font-medium text-gray-600 hover:bg-gray-50 transition-colors"
            >
              <ExternalLink className="w-4 h-4" /> Preview Store
            </a>
          )}
          <button
            onClick={handleSave}
            disabled={updateMerchant.isPending}
            className="flex items-center gap-1.5 px-5 py-2 bg-indigo-600 text-white rounded-xl text-sm font-semibold hover:bg-indigo-700 disabled:opacity-60 transition-colors"
          >
            <Save className="w-4 h-4" />
            {updateMerchant.isPending ? "Saving..." : "Save Changes"}
          </button>
        </div>
      </div>

      <div className="grid lg:grid-cols-3 gap-6">
        {/* Main form */}
        <div className="lg:col-span-2 space-y-5">
          {/* Store Identity */}
          <div className="bg-white rounded-2xl border border-gray-200 p-6 space-y-4">
            <h2 className="font-semibold text-gray-900 flex items-center gap-2">
              <Store className="w-4 h-4 text-indigo-600" /> Store Identity
            </h2>
            <div className="grid sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Store Name *</label>
                <input
                  className="w-full border border-gray-300 rounded-xl px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  value={form.business_name}
                  onChange={(e) => set("business_name", e.target.value)}
                  placeholder="Your Business Name"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Store URL Slug *</label>
                <div className="flex items-center border border-gray-300 rounded-xl overflow-hidden focus-within:ring-2 focus-within:ring-indigo-500">
                  <span className="px-2 py-2.5 bg-gray-50 text-gray-400 text-xs border-r border-gray-300">/store/</span>
                  <input
                    className="flex-1 px-2 py-2.5 text-sm focus:outline-none"
                    value={form.store_slug}
                    onChange={(e) => set("store_slug", slugify(e.target.value))}
                    placeholder="my-store"
                  />
                </div>
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Store Description / Tagline</label>
              <textarea
                className="w-full border border-gray-300 rounded-xl px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 resize-none"
                rows={3}
                value={form.store_description}
                onChange={(e) => set("store_description", e.target.value)}
                placeholder="Tell buyers what you sell and what makes your store special..."
              />
            </div>
          </div>

          {/* Media */}
          <div className="bg-white rounded-2xl border border-gray-200 p-6 space-y-4">
            <h2 className="font-semibold text-gray-900 flex items-center gap-2">
              <ImageIcon className="w-4 h-4 text-indigo-600" /> Images
            </h2>
            <div className="grid sm:grid-cols-2 gap-6">
              <LogoUploader
                label="Store Logo"
                value={form.logo_url}
                onUpload={(url) => set("logo_url", url)}
              />
              <ImageUploader
                label="Store Banner"
                value={form.store_banner_url}
                onUpload={(url) => set("store_banner_url", url)}
              />
            </div>
            {(!form.logo_url && !form.store_banner_url) && (
              <p className="text-xs text-gray-400">
                Images are stored locally in preview mode. Configure S3/R2 in settings for permanent storage.
              </p>
            )}
          </div>

          {/* Contact & Location */}
          <div className="bg-white rounded-2xl border border-gray-200 p-6 space-y-4">
            <h2 className="font-semibold text-gray-900 flex items-center gap-2">
              <MapPin className="w-4 h-4 text-indigo-600" /> Contact & Location
            </h2>
            <div className="grid sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  <Phone className="w-3 h-3 inline mr-1" />Contact Phone
                </label>
                <input
                  className="w-full border border-gray-300 rounded-xl px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  value={form.whatsapp_phone}
                  onChange={(e) => set("whatsapp_phone", e.target.value)}
                  placeholder="+8801..."
                  type="tel"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">District</label>
                <input
                  className="w-full border border-gray-300 rounded-xl px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  value={form.district}
                  onChange={(e) => set("district", e.target.value)}
                  placeholder="e.g. Dhaka"
                />
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Full Address</label>
              <input
                className="w-full border border-gray-300 rounded-xl px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                value={form.address}
                onChange={(e) => set("address", e.target.value)}
                placeholder="House, road, area, district"
              />
            </div>
          </div>
        </div>

        {/* Sidebar */}
        <div className="space-y-5">
          {/* Store Status */}
          <div className="bg-white rounded-2xl border border-gray-200 p-5">
            <h3 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
              <Globe className="w-4 h-4 text-indigo-600" /> Store Status
            </h3>
            {form.store_slug ? (
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
                  <span className="text-sm font-medium text-green-700">Store is Live</span>
                </div>
                <p className="text-xs text-gray-500 break-all">/store/{form.store_slug}</p>
                <a
                  href={`/store/${form.store_slug}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-1.5 text-xs text-indigo-600 hover:text-indigo-800 mt-2"
                >
                  <ExternalLink className="w-3 h-3" /> Open public store
                </a>
              </div>
            ) : (
              <div>
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 rounded-full bg-gray-400" />
                  <span className="text-sm text-gray-600">Store is Private</span>
                </div>
                <p className="text-xs text-gray-400 mt-1">Set a store slug to make it public</p>
              </div>
            )}
          </div>

          <LaunchChecklist />

          {/* Share */}
          {form.store_slug && (
            <div className="bg-indigo-50 rounded-2xl border border-indigo-100 p-5">
              <h3 className="font-semibold text-indigo-900 mb-2">Share Your Store</h3>
              <p className="text-xs text-indigo-700 break-all mb-3">
                {typeof window !== "undefined" ? window.location.origin : "https://sellermate.ai"}/store/{form.store_slug}
              </p>
              <button
                onClick={() => {
                  const url = `${window.location.origin}/store/${form.store_slug}`;
                  navigator.clipboard?.writeText(url);
                  toast.success("Store link copied!");
                }}
                className="w-full py-2 bg-indigo-600 text-white rounded-xl text-sm font-medium hover:bg-indigo-700 transition-colors"
              >
                Copy Store Link
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
