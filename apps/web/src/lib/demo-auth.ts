import api from "@/lib/api-client";
import { setTokens } from "@/lib/auth";
import type { LoginResponse, ApiResponse } from "@/types";

const DEMO_EMAIL = "demo@sellermate.ai";
const DEMO_PHONE = "+8801700000009";
const DEMO_PASSWORD = "Demo@123456";

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
 * Throws on any unrecoverable error.
 */
export async function enterDemoMode(): Promise<void> {
  try {
    await loginDemo();
    return;
  } catch {
    // Login failed — account may not exist yet. Try to register.
  }

  try {
    await registerDemo();
  } catch {
    // Registration may fail if account already exists but password differs,
    // or if there's a network issue. Try login one more time before giving up.
  }

  // Final login attempt (covers: just registered, or account existed all along)
  await loginDemo();
}
