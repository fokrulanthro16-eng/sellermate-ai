import { useMutation, useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api-client";

export interface BackupSummary {
  counts: { products: number; customers: number; orders: number; campaigns: number };
  merchant_id: string;
}

export function useBackupSummary() {
  return useQuery<BackupSummary>({
    queryKey: ["backup-summary"],
    queryFn: async () => {
      const res = await api.get("/backup/export/summary");
      return (res.data as any).data as BackupSummary;
    },
    staleTime: 60_000,
  });
}

export function useDownloadBackup() {
  return useMutation({
    mutationFn: async () => {
      const res = await api.get("/backup/export", { responseType: "blob" });
      const url = URL.createObjectURL(res.data as Blob);
      const a = document.createElement("a");
      a.href = url;
      const cd = (res.headers as any)["content-disposition"] || "";
      const match = cd.match(/filename="(.+?)"/);
      a.download = match ? match[1] : `sellermate_backup_${Date.now()}.json`;
      a.click();
      URL.revokeObjectURL(url);
    },
  });
}
