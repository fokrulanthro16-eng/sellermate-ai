# Hydration Fix Report

## Root Cause Analysis

Next.js renders pages twice: once on the **server** (SSR/SSG) and once on the **client** during hydration. If the HTML produced by those two renders differs, React throws:

> Hydration failed because server rendered HTML doesn't match client.

Three patterns were found in the frontend that caused or risked this mismatch.

---

## Issues Found & Fixed

### 1. Dashboard Layout — `isAuthenticated()` in render body (CRITICAL)

**File:** `src/app/(dashboard)/layout.tsx`

**Before:**
```tsx
export default function DashboardLayout({ children }) {
  const router = useRouter();

  useEffect(() => {
    if (!isAuthenticated()) router.replace("/login");
  }, [router]);

  if (!isAuthenticated()) return null;   // ← CRASH: called during render

  return <div>...full layout...</div>;
}
```

**Why it broke:**
- `isAuthenticated()` → `getToken()` → reads `localStorage`
- On the **server**: `typeof window === "undefined"` → returns `null` → `isAuthenticated()` = `false` → renders `null`
- On the **client** (first render): `localStorage` has a token → `isAuthenticated()` = `true` → renders full layout
- **Server HTML ≠ Client HTML → hydration crash**

**After:**
```tsx
const [mounted, setMounted] = useState(false);

useEffect(() => {
  setMounted(true);
  if (!isAuthenticated()) router.replace("/login");
}, [router]);

if (!mounted) return null;          // ← both server and client return null here
if (!isAuthenticated()) return null; // ← only runs post-mount (client-only)

return <div>...full layout...</div>;
```

**Why this works:**
- Server renders `null` (mounted = false).
- Client's first paint also renders `null` (useState starts false, useEffect hasn't fired yet).
- Server HTML === initial client HTML → **no mismatch**.
- After hydration, `useEffect` fires: sets `mounted = true` and checks auth. The full layout appears only on the client, after React has taken control.

---

### 2. Dashboard Page — `new Date()` in render body

**File:** `src/app/(dashboard)/dashboard/page.tsx`

**Before:**
```tsx
const to   = format(new Date(), "yyyy-MM-dd");
const from = format(subDays(new Date(), days), "yyyy-MM-dd");
```

**After:**
```tsx
const to   = useMemo(() => format(new Date(), "yyyy-MM-dd"), []);
const from = useMemo(() => format(subDays(new Date(), days), "yyyy-MM-dd"), [days]);
```

**Why:** `new Date()` evaluated during render returns different millisecond values on server vs. client. `useMemo` pins the computation to the client's first paint and recomputes only when `days` changes (user interaction, always client-side).

---

### 3. Analytics Page — same `new Date()` pattern

**File:** `src/app/(dashboard)/analytics/page.tsx`

Same fix as above — both `to` and `from` wrapped in `useMemo`.

---

## Patterns Audited (Safe — No Changes Needed)

| Location | Pattern | Status |
|----------|---------|--------|
| `src/lib/auth.ts` | `localStorage` in `getToken` / `getRefreshToken` | ✅ Already guarded with `typeof window !== "undefined"` |
| `src/lib/auth.ts` | `localStorage` in `setTokens` / `clearTokens` | ✅ Only called from event handlers / useEffect |
| `src/lib/api-client.ts` | `window.location.href = "/login"` | ✅ Already guarded with `typeof window !== "undefined"` |
| `src/components/assistant/ChatWindow.tsx` | `Date.now()`, `new Date()` | ✅ Inside event handler `handleSend`, never during render |
| `src/providers/QueryProvider.tsx` | `new QueryClient(...)` | ✅ Inside `useState` initializer — runs client-side only |
| `src/app/layout.tsx` | `suppressHydrationWarning` on `<html>` | ✅ Correct — covers theme-class changes |
| `src/components/layout/Sidebar.tsx` | `usePathname()` | ✅ Next.js router hook, SSR-safe |
| `src/components/layout/Header.tsx` | `localStorage` via `clearTokens` | ✅ Only in logout handler |

---

## Files Changed

| File | Change |
|------|--------|
| `src/app/(dashboard)/layout.tsx` | Added `mounted` guard — eliminates critical mismatch |
| `src/app/(dashboard)/dashboard/page.tsx` | `new Date()` → `useMemo` |
| `src/app/(dashboard)/analytics/page.tsx` | `new Date()` → `useMemo` |

---

## Test Checklist

- [ ] Open browser DevTools Console — no "Hydration failed" warning
- [ ] Navigate to `/login` → click demo button → land on `/dashboard` without console errors
- [ ] Hard-refresh `/dashboard` while logged in — page loads without flicker or warning
- [ ] Hard-refresh `/dashboard` while logged out — redirects to `/login` (no layout flash)
- [ ] Navigate between pages in sidebar — no hydration warnings on any route
- [ ] `/analytics` page loads without hydration warning
- [ ] `npx tsc --noEmit` → exit code 0 ✅
