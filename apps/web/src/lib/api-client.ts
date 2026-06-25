import axios from "axios";
import { getToken, getRefreshToken, setTokens, clearTokens } from "@/lib/auth";

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export const api = axios.create({
  baseURL: BASE_URL,
  headers: { "Content-Type": "application/json" },
});

api.interceptors.request.use((config) => {
  const token = getToken();
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

let isRefreshing = false;
let failedQueue: Array<{ resolve: (v: unknown) => void; reject: (e: unknown) => void }> = [];

function processQueue(error: unknown, token: string | null = null) {
  failedQueue.forEach((p) => (error ? p.reject(error) : p.resolve(token)));
  failedQueue = [];
}

api.interceptors.response.use(
  (res) => res,
  async (error) => {
    const orig = error.config;

    // Show toast for non-401 errors (401 is handled below via redirect)
    if (error.response?.status && error.response.status !== 401) {
      const msg = error.response?.data?.error?.message
        || error.response?.data?.detail
        || error.response?.data?.message
        || `Error ${error.response.status}`;
      if (typeof window !== "undefined") {
        import("sonner").then(({ toast }) => toast.error(msg));
      }
    }

    if (error.response?.status !== 401 || orig._retry) return Promise.reject(error);

    if (isRefreshing) {
      return new Promise((resolve, reject) => {
        failedQueue.push({ resolve, reject });
      }).then((token) => {
        orig.headers.Authorization = `Bearer ${token}`;
        return api(orig);
      });
    }

    orig._retry = true;
    isRefreshing = true;

    const refreshToken = getRefreshToken();
    if (!refreshToken) {
      clearTokens();
      if (typeof window !== "undefined") window.location.href = "/login";
      return Promise.reject(error);
    }

    try {
      const { data } = await axios.post(`${BASE_URL}/auth/refresh`, {
        refresh_token: refreshToken,
      });
      const { access_token, refresh_token } = data.data;
      setTokens(access_token, refresh_token);
      api.defaults.headers.common.Authorization = `Bearer ${access_token}`;
      processQueue(null, access_token);
      orig.headers.Authorization = `Bearer ${access_token}`;
      return api(orig);
    } catch (err) {
      processQueue(err, null);
      clearTokens();
      if (typeof window !== "undefined") window.location.href = "/login";
      return Promise.reject(err);
    } finally {
      isRefreshing = false;
    }
  }
);

export default api;
