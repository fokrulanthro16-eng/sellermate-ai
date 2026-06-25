import { useQuery } from "@tanstack/react-query";
import api from "@/lib/api-client";

export interface Notification {
  id: string;
  type: string;
  priority: string;
  title_en: string;
  title_bn: string;
  body_en: string;
  body_bn: string;
  action: string;
}

export function useNotifications() {
  return useQuery<Notification[]>({
    queryKey: ["notifications"],
    queryFn: async () => {
      const { data } = await api.get<{ data: Notification[] }>("/notifications");
      return data.data;
    },
    refetchInterval: 60_000,
  });
}
