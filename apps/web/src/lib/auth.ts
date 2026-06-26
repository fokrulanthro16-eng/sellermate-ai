const ACCESS_KEY = "sellermate_token";
const REFRESH_KEY = "sellermate_refresh";
const DEMO_KEY = "sm_demo_mode";

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
  localStorage.removeItem(DEMO_KEY);
};

export const isAuthenticated = (): boolean => !!getToken();

export const isDemoMode = (): boolean =>
  typeof window !== "undefined" && localStorage.getItem(DEMO_KEY) === "true";

// Stores a synthetic token so isAuthenticated() returns true without a real JWT.
export const setDemoMode = (): void => {
  localStorage.setItem(DEMO_KEY, "true");
  localStorage.setItem(ACCESS_KEY, "beta_demo_session");
};
