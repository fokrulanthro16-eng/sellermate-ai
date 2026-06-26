import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import api from "@/lib/api-client";
import { toast } from "sonner";

export interface MerchantProfile {
  id: string;
  email: string;
  phone: string;
  business_name: string;
  owner_name: string;
  business_type: string;
  address: string | null;
  district: string | null;
  division: string | null;
  logo_url: string | null;
  whatsapp_phone: string | null;
  whatsapp_connected: boolean;
  trust_score: number;
  status: string;
  plan: string;
  onboarding_step: number;
  onboarding_done: boolean;
  store_slug: string | null;
  store_description: string | null;
  store_banner_url: string | null;
  latitude: number | null;
  longitude: number | null;
}

export function useMerchantProfile() {
  return useQuery<MerchantProfile>({
    queryKey: ["merchant-profile"],
    queryFn: async () => {
      const { data } = await api.get("/merchant/me");
      return data.data;
    },
  });
}

export function useUpdateMerchant() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: Partial<MerchantProfile>) => {
      const { data } = await api.patch("/merchant/me", payload);
      return data.data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["merchant-profile"] });
      toast.success("Profile updated");
    },
    onError: (err: any) => {
      toast.error(err?.response?.data?.error?.message || "Update failed");
    },
  });
}

export function useLaunchChecklist() {
  return useQuery({
    queryKey: ["launch-checklist"],
    queryFn: async () => {
      const { data } = await api.get("/merchant/launch-checklist");
      return data.data as {
        items: Array<{ id: string; label: string; done: boolean; detail?: string }>;
        done: number;
        total: number;
        pct: number;
      };
    },
  });
}

export function useUploadImage() {
  return useMutation({
    mutationFn: async (file: File) => {
      const form = new FormData();
      form.append("file", file);
      const { data } = await api.post("/media/upload", form, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      return data.data as { url: string; key: string; mode: string };
    },
  });
}

export function useUploadLogo() {
  return useMutation({
    mutationFn: async (file: File) => {
      const form = new FormData();
      form.append("file", file);
      const { data } = await api.post("/media/upload/logo", form, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      return data.data as { url: string; key: string; mode: string };
    },
  });
}
