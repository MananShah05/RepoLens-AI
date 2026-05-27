"use client";

import { useEffect, useRef, useState } from "react";
import { useParams } from "next/navigation";
import { sendChat, getRepo } from "@/lib/api";
import { Send, Loader2, User, Bot, Sparkles, Lightbulb, AlertCircle } from "lucide-react";
import MarkdownRenderer from "@/app/components/ui/MarkdownRenderer";

interface Message {
  role: "user" | "assistant";
  content: string;
  citations?: any[];
}

const suggestions = [
  "What does this repository do?",
  "What's the project structure?",
  "How do I set up the project?",
  "What are the main entry points?",
];

export default function ChatPage() {
  const { id } = useParams();
  const repoId = Number(id);
  const [messages, setMessages] = useState<Message[]>([
    { role: "assistant", content: "Hi! I'm RepoLens AI. Ask me anything about this codebase — architecture, setup, key files, or specific features." },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [repoStatus, setRepoStatus] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    let cancelled = false;
    async function checkStatus() {
      try {
        const repo = await getRepo(repoId);
        if (!cancelled) setRepoStatus(repo.status);
      } catch {
        if (!cancelled) setRepoStatus("error");
      }
    }
    checkStatus();
    const interval = setInterval(checkStatus, 4000);
    return () => { cancelled = true; clearInterval(interval); };
  }, [repoId]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!input.trim() || loading) return;
    const userMsg = input.trim();
    setInput("");
    setMessages((prev) => [...prev, { role: "user", content: userMsg }]);
    setLoading(true);
    try {
      const history = messages
        .filter((m) => m.role !== "assistant" || m.content !== messages[0].content)
        .map((m) => ({ role: m.role, content: m.content }));
      const res = await sendChat(repoId, userMsg, history);
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: res.answer, citations: res.citations },
      ]);
    } catch (e: any) {
      let errMsg = e.message || "Something went wrong.";
      try {
        const parsed = JSON.parse(errMsg);
        if (parsed.detail) errMsg = parsed.detail;
      } catch {}
      setMessages((prev) => [...prev, { role: "assistant", content: `Error: ${errMsg}` }]);
    } finally {
      setLoading(false);
    }
  }

  const isReady = repoStatus === "ready";

  return (
    <div className="flex flex-col h-[calc(100vh-7rem)]">
      {!isReady && repoStatus !== null && (
        <div className="mb-4 rounded-xl border border-warning/20 bg-warning/[0.05] px-4 py-3 flex items-center gap-3 animate-in-up">
          <AlertCircle className="h-4 w-4 text-warning shrink-0" />
          <p className="text-sm text-warning">
            Repository is still <span className="font-medium">{repoStatus}</span>. Chat will be available once processing is complete.
          </p>
        </div>
      )}
      <div className="flex-1 overflow-y-auto space-y-4 pr-2 scroll-smooth">
        {messages.map((m, i) => (
          <div key={i} className={`flex gap-3 ${m.role === "user" ? "justify-end" : ""} animate-in-up`} style={{ animationDelay: `${i * 50}ms` }}>
            {m.role === "assistant" && (
              <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-gradient-primary shadow-sm">
                <Bot className="h-4 w-4 text-white" />
              </div>
            )}
            <div
              className={`rounded-2xl px-4 py-3 text-sm max-w-[85%] leading-relaxed ${
                m.role === "user"
                  ? "bg-primary text-primary-foreground rounded-tr-md"
                  : "bg-card border text-foreground rounded-tl-md shadow-sm"
              }`}
            >
              <MarkdownRenderer content={m.content} />
              {m.citations && m.citations.length > 0 && (
                <div className="mt-3 pt-2 border-t border-border/50">
                  <div className="flex items-center gap-1.5 text-[10px] text-muted-foreground/60 uppercase tracking-wider font-medium mb-1.5">
                    <Sparkles className="h-3 w-3" />
                    Sources
                  </div>
                  <div className="flex flex-wrap gap-1">
                    {m.citations.map((c, idx) => (
                      <span key={idx} className="text-[11px] bg-secondary/50 rounded-lg px-2 py-1 font-mono text-muted-foreground">
                        {c.file_path}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
            {m.role === "user" && (
              <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-secondary">
                <User className="h-4 w-4 text-muted-foreground" />
              </div>
            )}
          </div>
        ))}
        {loading && (
          <div className="flex items-center gap-3 text-sm text-muted-foreground animate-in-up">
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-gradient-primary shadow-sm">
              <Bot className="h-4 w-4 text-white" />
            </div>
            <div className="flex items-center gap-1.5">
              <div className="flex gap-1">
                <span className="w-2 h-2 rounded-full bg-primary/40 animate-bounce" style={{ animationDelay: "0ms" }} />
                <span className="w-2 h-2 rounded-full bg-primary/40 animate-bounce" style={{ animationDelay: "150ms" }} />
                <span className="w-2 h-2 rounded-full bg-primary/40 animate-bounce" style={{ animationDelay: "300ms" }} />
              </div>
              <span className="text-xs ml-1">Thinking...</span>
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {messages.length === 1 && (
        <div className="mb-4">
          <div className="flex items-center gap-2 mb-2 text-xs text-muted-foreground">
            <Lightbulb className="h-3 w-3" />
            Suggested questions
          </div>
          <div className="flex flex-wrap gap-2">
            {suggestions.map((s) => (
              <button
                key={s}
                onClick={() => {
                  setInput(s);
                }}
                className="text-xs rounded-full border bg-secondary/50 px-3 py-1.5 text-muted-foreground hover:text-foreground hover:bg-secondary transition-colors"
              >
                {s}
              </button>
            ))}
          </div>
        </div>
      )}

      <form onSubmit={handleSubmit} className="flex gap-2">
        <div className="flex-1 relative">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={isReady ? "Ask about the codebase..." : "Waiting for repository to finish processing..."}
            disabled={!isReady}
            className="w-full rounded-xl border border-input bg-card pl-4 pr-4 py-3 text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-ring focus:border-ring transition-shadow disabled:opacity-50 disabled:cursor-not-allowed"
          />
        </div>
        <button
          type="submit"
          disabled={loading || !input.trim() || !isReady}
          className="inline-flex items-center justify-center rounded-xl bg-gradient-primary px-4 py-3 text-sm font-medium text-primary-foreground shadow-lg shadow-primary/25 hover:shadow-xl hover:shadow-primary/30 transition-all disabled:opacity-40 disabled:hover:shadow-lg"
        >
          <Send className="h-4 w-4" />
        </button>
      </form>
    </div>
  );
}
