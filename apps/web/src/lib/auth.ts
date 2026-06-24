const ACCESS_KEY = "sellermate_token";
const REFRESH_KEY = "sellermate_refresh";

export const getToken = (): string | null =>
  typeof window !== "undefined" ? localStorage.getItem(ACCESS_KEY) : null;

export const getRefreshToken = (): string | null =>
  typeof window !== "undefined" ? localStorage.getItem(REFRESH_KEY) : null;

export const setTokens = (access: string, refresh: string): void => {
  localStorage.setItem(ACCESS_KEY, access);
  localStorage.setItem(REFRESH_KEY, refresh);
};

export const clearTokens = (): void => {
  localStorage.removeItem(ACCESS_KEY);
  localStorage.removeItem(REFRESH_KEY);
};

export const isAuthenticated = (): boolean => !!getToken();
