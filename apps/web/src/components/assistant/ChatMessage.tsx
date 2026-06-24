import { Bot, User } from "lucide-react";
import { cn, formatDateTime } from "@/lib/utils";
import type { Message } from "@/types";

interface ChatMessageProps {
  message: Message;
}

export default function ChatMessage({ message }: ChatMessageProps) {
  const isUser = message.role === "user";
  return (
    <div className={cn("flex gap-3", isUser ? "flex-row-reverse" : "flex-row")}>
      <div className={cn(
        "flex h-8 w-8 shrink-0 items-center justify-center rounded-full",
        isUser ? "bg-primary text-primary-foreground" : "bg-muted"
      )}>
        {isUser ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
      </div>
      <div className={cn("max-w-[75%] space-y-1", isUser ? "items-end" : "items-start")}>
        <div className={cn(
          "rounded-2xl px-4 py-2.5 text-sm",
          isUser
            ? "bg-primary text-primary-foreground rounded-tr-sm"
            : "bg-muted text-foreground rounded-tl-sm"
        )}>
          <p className="whitespace-pre-wrap leading-relaxed">{message.content}</p>
        </div>
        <p className={cn("text-xs text-muted-foreground px-1", isUser ? "text-right" : "text-left")}>
          {formatDateTime(message.created_at)}
        </p>
      </div>
    </div>
  );
}
