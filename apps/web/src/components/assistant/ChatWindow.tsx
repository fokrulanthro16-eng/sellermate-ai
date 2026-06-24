"use client";

import { useEffect, useRef, useState } from "react";
import { useMessages } from "@/hooks/useAssistant";
import { useLang } from "@/contexts/LangContext";
import { useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import ChatMessage from "@/components/assistant/ChatMessage";
import ChatInput from "@/components/assistant/ChatInput";
import TypingIndicator from "@/components/assistant/TypingIndicator";
import { Skeleton } from "@/components/ui/skeleton";
import api from "@/lib/api-client";
import { getToken } from "@/lib/auth";
import { getApiError } from "@/lib/utils";
import type { Message } from "@/types";

interface ChatWindowProps {
  conversationId: string;
  initialMessage?: string;
}

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export default function ChatWindow({ conversationId, initialMessage }: ChatWindowProps) {
  const { t } = useLang();
  const { data, isLoading } = useMessages(conversationId);
  const qc = useQueryClient();
  const [streaming, setStreaming] = useState(false);
  const [streamText, setStreamText] = useState("");
  const bottomRef = useRef<HTMLDivElement>(null);
  const initialSentRef = useRef<string | null>(null);
  const messages = data?.items || [];

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, streamText]);

  const handleSend = async (text: string) => {
    if (streaming) return;

    setStreaming(true);
    setStreamText("");

    try {
      const token = getToken();
      const response = await fetch(
        `${BASE_URL}/assistant/conversations/${conversationId}/chat`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({ message: text }),
        }
      );

      if (!response.ok) throw new Error("এআই সাড়া দিতে পারছে না");

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      let full = "";

      while (reader) {
        const { done, value } = await reader.read();
        if (done) break;
        const chunk = decoder.decode(value);
        const lines = chunk.split("\n");
        for (const line of lines) {
          if (line.startsWith("data: ")) {
            const payload = line.slice(6).trim();
            if (payload && payload !== "[DONE]") {
              full += payload;
              setStreamText(full);
            }
          }
        }
      }
    } catch (e) {
      toast.error(getApiError(e));
    } finally {
      setStreaming(false);
      setStreamText("");
      qc.invalidateQueries({ queryKey: ["conversations", conversationId, "messages"] });
    }
  };

  // Auto-send initialMessage once after the conversation loads (no prior messages)
  useEffect(() => {
    if (
      initialMessage &&
      initialMessage !== initialSentRef.current &&
      !isLoading &&
      !streaming &&
      messages.length === 0
    ) {
      initialSentRef.current = initialMessage;
      handleSend(initialMessage);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [initialMessage, isLoading, messages.length]);

  return (
    <div className="flex flex-col h-full">
      <div className="flex-1 overflow-y-auto space-y-4 pb-4">
        {isLoading ? (
          <div className="space-y-4">
            {[1, 2, 3].map((i) => <Skeleton key={i} className="h-16 w-3/4 rounded-xl" />)}
          </div>
        ) : messages.length === 0 && !streaming ? (
          <div className="text-center text-muted-foreground py-8">
            <p className="text-sm">{t("askQuestion")}</p>
            <p className="text-xs mt-1 opacity-70">{t("chatBothLangs")}</p>
          </div>
        ) : (
          <>
            {messages.map((msg) => <ChatMessage key={msg.id} message={msg} />)}
            {streaming && streamText && (
              <ChatMessage message={{
                id: "streaming",
                conversation_id: conversationId,
                role: "assistant",
                content: streamText,
                created_at: new Date().toISOString(),
              }} />
            )}
            {streaming && !streamText && <TypingIndicator />}
          </>
        )}
        <div ref={bottomRef} />
      </div>
      <ChatInput onSend={handleSend} loading={streaming} />
    </div>
  );
}
