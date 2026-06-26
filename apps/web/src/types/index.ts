// ── API Wrappers ────────────────────────────────────────────────────────────
export interface ApiResponse<T> {
  success: boolean;
  data: T;
  message?: string;
}

export interface PaginatedData<T> {
  items: T[];
  total: number;
  page: number;
  limit: number;
  pages: number;
}

// ── Auth ────────────────────────────────────────────────────────────────────
export interface Merchant {
  id: string;
  email: string;
  phone: string;
  business_name: string;
  owner_name: string;
  business_type: string;
  is_active: boolean;
  onboarding_step: number;
  plan: string;
  created_at: string;
}

export interface TokenPair {
  access_token: string;
  refresh_token: string;
}

export interface LoginResponse {
  merchant: Merchant;
  tokens: TokenPair;
}

export interface RegisterPayload {
  email: string;
  phone: string;
  password: string;
  business_name: string;
  owner_name: string;
  business_type: string;
}

export interface LoginPayload {
  identifier: string;
  password: string;
}

// ── Products ─────────────────────────────────────────────────────────────────
export interface ProductVariant {
  id: string;
  product_id: string;
  name: string;
  sku: string;
  price: string;
  stock_quantity: number;
  low_stock_alert: number;
  is_active: boolean;
  created_at: string;
}

export interface Product {
  id: string;
  merchant_id: string;
  name: string;
  category: string;
  description?: string;
  base_price: string;
  is_active: boolean;
  image_urls?: string[];
  variants: ProductVariant[];
  created_at: string;
  updated_at: string;
}

export interface CreateProductPayload {
  name: string;
  category: string;
  description?: string;
  base_price: string;
  variants?: {
    name: string;
    sku: string;
    price: string;
    stock_quantity: number;
    low_stock_alert?: number;
  }[];
}

// ── Inventory ─────────────────────────────────────────────────────────────────
export interface InventoryItem {
  variant_id: string;
  variant_name: string;
  sku: string;
  product_id: string;
  product_name: string;
  stock_quantity: number;
  low_stock_alert: number;
  is_low_stock: boolean;
}

export interface InventoryLog {
  id: string;
  variant_id: string;
  change_type: string;
  quantity_change: number;
  quantity_after: number;
  note?: string;
  created_at: string;
}

export interface AdjustmentItem {
  variant_id: string;
  quantity_change: number;
  note?: string;
}

// ── Customers ─────────────────────────────────────────────────────────────────
export interface Customer {
  id: string;
  merchant_id: string;
  name: string;
  phone: string;
  email?: string;
  address?: string;
  district?: string;
  division?: string;
  source?: string;
  tags: string[];
  total_orders: number;
  total_spent: string;
  last_order_at?: string;
  created_at: string;
  updated_at: string;
}

export interface CreateCustomerPayload {
  name: string;
  phone: string;
  email?: string;
  address?: string;
  district?: string;
}

// ── Orders ─────────────────────────────────────────────────────────────────
export type OrderStatus =
  | "PENDING"
  | "CONFIRMED"
  | "PROCESSING"
  | "SHIPPED"
  | "DELIVERED"
  | "CANCELLED"
  | "RETURNED";

export type PaymentStatus = "UNPAID" | "PARTIAL" | "PAID";
export type PaymentMethod = "COD" | "BKASH" | "NAGAD" | "ROCKET" | "BANK" | "CARD" | "OTHER";
export type OrderChannel = "FACEBOOK" | "INSTAGRAM" | "WHATSAPP" | "WEBSITE" | "DIRECT" | "OTHER";

export interface OrderItem {
  id: string;
  order_id: string;
  product_id: string;
  variant_id: string;
  product_name: string;
  variant_name: string;
  sku: string;
  quantity: number;
  unit_price: string;
  subtotal: string;
}

export interface OrderStatusHistory {
  id: string;
  order_id: string;
  status: OrderStatus;
  note?: string;
  created_at: string;
}

export interface Order {
  id: string;
  merchant_id: string;
  customer_id: string;
  order_number?: string;
  customer_name?: string;
  customer_phone?: string;
  delivery_district?: string;
  delivery_division?: string;
  status: OrderStatus;
  payment_status: PaymentStatus;
  payment_method: PaymentMethod;
  channel: OrderChannel;
  subtotal: string;
  discount_amount: string;
  shipping_cost: string;
  total_amount: string;
  paid_amount: string;
  due_amount?: string;
  delivery_address?: string;
  tracking_number?: string;
  courier_name?: string;
  notes?: string;
  items?: OrderItem[];
  status_history?: OrderStatusHistory[];
  created_at: string;
  updated_at: string;
}

export interface CreateOrderPayload {
  customer_id: string;
  items: { product_id: string; variant_id: string; quantity: number }[];
  discount_amount?: string;
  shipping_cost?: string;
  payment_method: PaymentMethod;
  channel?: OrderChannel;
  delivery_address?: string;
  notes?: string;
}

// ── Analytics ─────────────────────────────────────────────────────────────────
export interface TopProductItem {
  product_id: string;
  product_name: string;
  total_revenue: number;
  total_quantity: number;
}

export interface TopCustomerItem {
  customer_id: string;
  customer_name: string;
  total_orders: number;
  total_spent: number;
}

export interface DashboardMetrics {
  today_revenue: number;
  weekly_revenue: number;
  monthly_revenue: number;
  total_orders: number;
  delivered_orders: number;
  cancelled_orders: number;
  repeat_customers: number;
  average_order_value: number;
  top_products: TopProductItem[];
  top_customers: TopCustomerItem[];
}

export interface OverviewMetrics {
  total_revenue: number;
  total_orders: number;
  average_order_value: number;
  revenue_change_pct: number;
  orders_change_pct: number;
  aov_change_pct: number;
}

export interface RevenuePoint {
  period: string;
  revenue: number;
  orders: number;
}

export interface OrderBreakdown {
  by_status: Record<string, number>;
  by_channel: Record<string, number>;
  by_payment_status: Record<string, number>;
}

export interface CustomerMetrics {
  new_customers: number;
  returning_customers: number;
  top_customers: TopCustomerItem[];
}

export interface InventoryHealth {
  total_variants: number;
  low_stock_count: number;
  out_of_stock_count: number;
}

// ── Strategic Agents ─────────────────────────────────────────────────────────
export interface TrustScoreOut {
  trust_score: number;
  confidence: "LOW" | "MEDIUM" | "HIGH";
  risk_flags: string[];
  details: Record<string, number>;
}

export interface FraudReportOut {
  fraud_risk_score: number;
  alert_reasons: string[];
  details: Record<string, number | string>;
}

export interface StrategicRunResult {
  trust: TrustScoreOut;
  fraud: FraudReportOut;
  insights_saved: number;
}

export interface StrategicInsight {
  id: string;
  agent_name: string;
  score: number;
  payload: Record<string, unknown>;
  created_at: string;
}

// ── AI Assistant ─────────────────────────────────────────────────────────────
export interface Conversation {
  id: string;
  title?: string;
  created_at: string;
  updated_at: string;
}

export interface Message {
  id: string;
  conversation_id: string;
  role: "user" | "assistant";
  content: string;
  created_at: string;
}
