import Link from "next/link";
import { Phone, MapPin, ShoppingBag, Calendar } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { formatCurrency, formatDate, getInitials, cn } from "@/lib/utils";
import type { Customer } from "@/types";

const TAG_STYLE: Record<string, string> = {
  "VIP": "bg-amber-100 text-amber-800 dark:bg-amber-900 dark:text-amber-200 border-amber-200",
  "নিয়মিত": "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200 border-blue-200",
  "নতুন": "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200 border-green-200",
  "সন্দেহজনক": "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200 border-red-200",
};

interface CustomerCardProps {
  customer: Customer;
}

export default function CustomerCard({ customer }: CustomerCardProps) {
  const tags = (customer.tags || []).slice(0, 3);
  const isVIP = tags.includes("VIP");
  const isSuspicious = tags.includes("সন্দেহজনক");

  return (
    <Link href={`/customers/${customer.id}`}>
      <Card className={cn(
        "hover:shadow-md transition-all cursor-pointer group",
        isVIP && "border-amber-200 dark:border-amber-800",
        isSuspicious && "border-red-200 dark:border-red-900",
      )}>
        <CardContent className="p-4">
          <div className="flex items-start gap-3">
            <Avatar className={cn(
              "h-11 w-11 shrink-0",
              isVIP && "ring-2 ring-amber-400 ring-offset-1",
            )}>
              <AvatarFallback className={cn(
                "text-sm font-bold",
                isVIP
                  ? "bg-amber-100 text-amber-800 dark:bg-amber-900 dark:text-amber-200"
                  : "bg-primary/10 text-primary"
              )}>
                {getInitials(customer.name)}
              </AvatarFallback>
            </Avatar>

            <div className="flex-1 min-w-0">
              {/* Name + spend */}
              <div className="flex items-start justify-between gap-2">
                <p className="font-semibold text-sm truncate">{customer.name}</p>
                <span className={cn(
                  "text-sm font-bold shrink-0",
                  isVIP ? "text-amber-600 dark:text-amber-400" : "text-primary"
                )}>
                  {formatCurrency(customer.total_spent)}
                </span>
              </div>

              {/* Phone */}
              <div className="flex items-center gap-1 mt-1 text-xs text-muted-foreground">
                <Phone className="h-3 w-3 shrink-0" />
                <span className="font-mono">{customer.phone}</span>
              </div>

              {/* Location + last order */}
              <div className="flex items-center gap-3 mt-0.5 text-xs text-muted-foreground flex-wrap">
                {customer.district && (
                  <span className="flex items-center gap-0.5">
                    <MapPin className="h-3 w-3" />
                    {customer.district}
                  </span>
                )}
                {customer.last_order_at && (
                  <span className="flex items-center gap-0.5">
                    <Calendar className="h-3 w-3" />
                    {formatDate(customer.last_order_at)}
                  </span>
                )}
              </div>

              {/* Footer: orders + tags */}
              <div className="flex items-center gap-2 mt-2 flex-wrap">
                <div className="flex items-center gap-1 text-xs text-muted-foreground">
                  <ShoppingBag className="h-3 w-3" />
                  <span>{customer.total_orders} অর্ডার</span>
                </div>
                {tags.map((tag) => (
                  <span
                    key={tag}
                    className={cn(
                      "inline-flex items-center px-1.5 py-0 rounded text-[10px] font-semibold border",
                      TAG_STYLE[tag] ?? "bg-secondary text-secondary-foreground border-border"
                    )}
                  >
                    {tag}
                  </span>
                ))}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </Link>
  );
}
