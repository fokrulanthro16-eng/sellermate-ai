import api from "@/lib/api-client";
import { setTokens, setDemoMode } from "@/lib/auth";
import type { LoginResponse, ApiResponse } from "@/types";

const DEMO_EMAIL = "demo@sellermate.ai";
const DEMO_PHONE = "+8801700000001";
const DEMO_PASSWORD = "Demo1234!"; // must match apps/api/scripts/seed_demo.py

const DEMO_REGISTER_PAYLOAD = {
  email: DEMO_EMAIL,
  phone: DEMO_PHONE,
  password: DEMO_PASSWORD,
  owner_name: "Demo Owner",
  business_name: "Demo Shop",
  business_type: "FASHION_CLOTHING",
};

async function loginDemo(): Promise<void> {
  const res = await api.post<ApiResponse<LoginResponse>>("/auth/login", {
    identifier: DEMO_EMAIL,
    password: DEMO_PASSWORD,
  });
  const { tokens } = res.data.data;
  setTokens(tokens.access_token, tokens.refresh_token);
}

async function registerDemo(): Promise<void> {
  await api.post("/auth/register", DEMO_REGISTER_PAYLOAD);
}

/**
 * Attempts demo login; auto-registers if the account doesn't exist yet.
 * If all API calls fail (API unreachable), falls back to a local beta session
 * so the button never shows an error during testing.
 */
export async function enterDemoMode(): Promise<void> {
  try {
    await loginDemo();
    return; // real JWT stored — dashboard will have full data
  } catch {
    // Login failed — account may not exist yet
  }

  try {
    await registerDemo();
  } catch {
    // May fail if account exists but with a different credential — ignore
  }

  try {
    await loginDemo();
    return; // real JWT stored after registration
  } catch {
    // All API attempts failed (API unreachable or wrong credentials)
  }

  // Local beta fallback: store a synthetic session so the dashboard layout
  // doesn't redirect to /login. API calls will fail silently in this mode.
  setDemoMode();
}
