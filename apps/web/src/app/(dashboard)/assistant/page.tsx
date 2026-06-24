"use client";

import { useState } from "react";
import { Plus, Trash2, MessageSquare, Bot, Sparkles, X, Menu } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import ChatWindow from "@/components/assistant/ChatWindow";
import { useConversations, useCreateConversation, useDeleteConversation } from "@/hooks/useAssistant";
import { useLang } from "@/contexts/LangContext";
import { formatDateTime, cn } from "@/lib/utils";

const SUGGESTIONS_BN = [
  "আজকের অর্ডার কেমন?",
  "কম স্টক কোনটা?",
  "শীর্ষ বিক্রিত পণ্য দেখাও",
  "আমার ট্রাস্ট স্কোর কত?",
  "এই মাসে কত আয়?",
  "গ্রাহক বিশ্লেষণ দেখাও",
];
const SUGGESTIONS_EN = [
  "How are today's orders?",
  "What's low on stock?",
  "Show top selling products",
  "What's my trust score?",
  "How much did I earn this month?",
  "Show customer analytics",
];

export default function AssistantPage() {
  const { t, lang } = useLang();
  const { data, isLoading } = useConversations();
  const createConversation = useCreateConversation();
  const deleteConversation = useDeleteConversation();
  const [activeId, setActiveId] = useState<string | null>(null);
  const [initialMsg, setInitialMsg] = useState<string | undefined>();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const conversations = data?.items || [];
  const active = conversations.find((c) => c.id === activeId);
  const suggestions = lang === "en" ? SUGGESTIONS_EN : SUGGESTIONS_BN;

  const handleNew = async () => {
    const conv = await createConversation.mutateAsync(t("newConversation"));
    setInitialMsg(undefined);
    setActiveId(conv.id);
  };

  const handleSuggestion = async (text: string) => {
    const conv = await createConversation.mutateAsync(text.slice(0, 60));
    setInitialMsg(text);
    setActiveId(conv.id);
  };

  const handleDelete = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (confirm(t("deleteConversation"))) {
      await deleteConversation.mutateAsync(id);
      if (activeId === id) {
        setActiveId(null);
        setInitialMsg(undefined);
      }
    }
  };

  const handleSelect = (id: string) => {
    setActiveId(id);
    setInitialMsg(undefined);
    setSidebarOpen(false);
  };

  return (
    <div className="space-y-4 h-[calc(100vh-120px)] flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-3 animate-slide-up shrink-0">
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            className="md:hidden gap-1.5 rounded-xl"
            onClick={() => setSidebarOpen(true)}
          >
            <Menu className="h-3.5 w-3.5" />
            {lang === "bn" ? "চ্যাট তালিকা" : "Chats"}
          </Button>
          <div>
            <div className="flex items-center gap-2 mb-0.5">
              <Bot className="h-4 w-4 text-primary" />
              <h1 className="text-xl font-bold">{t("assistantTitle")}</h1>
              <Badge variant="secondary" className="text-xs px-2 py-0.5 ml-1">
                <span className="inline-block h-1.5 w-1.5 rounded-full bg-emerald-500 mr-1 animate-pulse" />
                {lang === "bn" ? "অনলাইন" : "Online"}
              </Badge>
            </div>
            <p className="text-sm text-muted-foreground">
              {lang === "bn"
                ? "বাংলা ও ইংরেজিতে আপনার ব্যবসার ডেটা জিজ্ঞেস করুন"
                : "Ask about your business data in Bangla or English"}
            </p>
          </div>
        </div>
        <Button onClick={handleNew} disabled={createConversation.isPending} className="gap-2 rounded-xl">
          <Plus className="h-4 w-4" /> {t("newConversation")}
        </Button>
      </div>

      {/* Two-panel layout */}
      <div className="flex gap-4 flex-1 min-h-0 animate-slide-up animation-delay-100">

        {/* Mobile backdrop */}
        {sidebarOpen && (
          <div
            className="fixed inset-0 bg-black/50 z-40 md:hidden"
            onClick={() => setSidebarOpen(false)}
          />
        )}

        {/* Sidebar — fixed drawer on mobile, static on md+ */}
        <div className={cn(
          "glass-card flex flex-col shrink-0",
          "fixed inset-y-0 left-0 w-72 z-50 rounded-none transition-transform duration-300 ease-in-out",
          sidebarOpen ? "translate-x-0" : "-translate-x-full",
          "md:static md:translate-x-0 md:w-64 xl:md:w-72 md:rounded-2xl md:z-auto"
        )}>
          {/* Sidebar header */}
          <div className="p-4 border-b border-border/50 flex items-center justify-between">
            <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
              {t("conversationList")}
            </p>
            <button
              onClick={() => setSidebarOpen(false)}
              className="md:hidden p-1 rounded-lg hover:bg-accent transition-colors"
            >
              <X className="h-4 w-4 text-muted-foreground" />
            </button>
          </div>

          {/* Conversation list */}
          <div className="flex-1 overflow-y-auto">
            {isLoading ? (
              <div className="p-3 space-y-2">
                {[1, 2, 3].map((i) => <Skeleton key={i} className="h-14 w-full rounded-xl" />)}
              </div>
            ) : conversations.length === 0 ? (
              <div className="p-4 text-center text-muted-foreground mt-4">
                <MessageSquare className="h-8 w-8 mx-auto mb-2 opacity-20" />
                <p className="text-xs">{t("noConversations")}</p>
              </div>
            ) : (
              <div className="p-2 space-y-1">
                {conversations.map((conv) => (
                  <div
                    key={conv.id}
                    onClick={() => handleSelect(conv.id)}
                    className={cn(
                      "group flex items-start justify-between p-2.5 rounded-xl cursor-pointer transition-all duration-200",
                      activeId === conv.id
                        ? "bg-primary/10 text-primary border border-primary/20"
                        : "hover:bg-accent border border-transparent"
                    )}
                  >
                    <div className="min-w-0 flex-1 flex items-start gap-2">
                      <MessageSquare className={cn(
                        "h-3.5 w-3.5 shrink-0 mt-0.5",
                        activeId === conv.id ? "text-primary" : "text-muted-foreground"
                      )} />
                      <div className="min-w-0">
                        <p className="text-sm font-medium truncate">{conv.title}</p>
                        <p className="text-xs text-muted-foreground mt-0.5">{formatDateTime(conv.created_at)}</p>
                      </div>
                    </div>
                    <button
                      onClick={(e) => handleDelete(conv.id, e)}
                      className="opacity-0 group-hover:opacity-100 p-1 hover:text-destructive transition-opacity shrink-0 rounded"
                    >
                      <Trash2 className="h-3 w-3" />
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* New chat button */}
          <div className="p-3 border-t border-border/50 shrink-0">
            <Button
              onClick={handleNew}
              disabled={createConversation.isPending}
              variant="outline"
              size="sm"
              className="w-full gap-2 rounded-xl"
            >
              <Plus className="h-3.5 w-3.5" />
              {t("newConversation")}
            </Button>
          </div>
        </div>

        {/* Chat area */}
        <div className="flex-1 glass-card rounded-2xl p-4 flex flex-col min-h-0">
          {active ? (
            <ChatWindow
              key={active.id}
              conversationId={active.id}
              initialMessage={initialMsg}
            />
          ) : (
            /* Empty state with suggestion chips */
            <div className="flex-1 flex flex-col items-center justify-center text-center px-6">
              <div className="h-16 w-16 rounded-2xl bg-primary/10 flex items-center justify-center mb-4">
                <Sparkles className="h-8 w-8 text-primary" />
              </div>
              <h2 className="text-lg font-semibold mb-1">{t("startChatPrompt")}</h2>
              <p className="text-sm text-muted-foreground mb-6 max-w-sm">
                {lang === "bn"
                  ? "নিচের যেকোনো বিষয়ে জিজ্ঞেস করুন অথবা নতুন চ্যাট শুরু করুন"
                  : "Ask about any of the topics below or start a new chat"}
              </p>

              {/* Suggestion chips */}
              <div className="flex flex-wrap gap-2 justify-center max-w-lg">
                {suggestions.map((text) => (
                  <button
                    key={text}
                    onClick={() => handleSuggestion(text)}
                    disabled={createConversation.isPending}
                    className="px-4 py-2 rounded-full text-sm font-medium border border-border bg-background hover:bg-accent hover:border-primary/50 transition-all duration-200 disabled:opacity-50"
                  >
                    {text}
                  </button>
                ))}
              </div>

              <Button
                className="mt-6 gap-2 rounded-xl"
                onClick={handleNew}
                disabled={createConversation.isPending}
              >
                <Plus className="h-4 w-4" /> {t("startChat")}
              </Button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
