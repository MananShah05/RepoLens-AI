"use client";

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

function cleanThinkingTags(text: string): string {
  // Client-side double-protection: strip <think>…</think> blocks and stray tags
  let cleaned = text.replace(/<think>[\s\S]*?<\/think>/gi, "");
  cleaned = cleaned.replace(/<\/?(think|assistant|output|response)>/gi, "");
  return cleaned.trim();
}

export default function MarkdownRenderer({
  content,
  className = "",
}: {
  content: string;
  className?: string;
}) {
  const cleaned = cleanThinkingTags(content);

  return (
    <div className={`prose-renderer ${className}`}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          h1: ({ children }) => (
            <h1 className="text-xl font-bold tracking-tight mt-6 mb-3 text-foreground first:mt-0">
              {children}
            </h1>
          ),
          h2: ({ children }) => (
            <h2 className="text-lg font-semibold tracking-tight mt-5 mb-2 text-foreground">
              {children}
            </h2>
          ),
          h3: ({ children }) => (
            <h3 className="text-base font-semibold mt-4 mb-2 text-foreground">
              {children}
            </h3>
          ),
          h4: ({ children }) => (
            <h4 className="text-sm font-semibold mt-3 mb-1.5 text-foreground">
              {children}
            </h4>
          ),
          p: ({ children }) => (
            <p className="text-sm leading-relaxed text-foreground/85 mb-3 last:mb-0">
              {children}
            </p>
          ),
          ul: ({ children }) => (
            <ul className="list-disc list-outside pl-5 space-y-1 mb-3 text-sm text-foreground/85">
              {children}
            </ul>
          ),
          ol: ({ children }) => (
            <ol className="list-decimal list-outside pl-5 space-y-1 mb-3 text-sm text-foreground/85">
              {children}
            </ol>
          ),
          li: ({ children }) => (
            <li className="leading-relaxed">{children}</li>
          ),
          strong: ({ children }) => (
            <strong className="font-semibold text-foreground">{children}</strong>
          ),
          em: ({ children }) => (
            <em className="italic text-foreground/80">{children}</em>
          ),
          a: ({ href, children }) => (
            <a
              href={href}
              target="_blank"
              rel="noopener noreferrer"
              className="text-primary hover:text-primary/80 underline underline-offset-2 transition-colors"
            >
              {children}
            </a>
          ),
          blockquote: ({ children }) => (
            <blockquote className="border-l-2 border-primary/40 pl-4 py-1 my-3 text-sm text-foreground/70 italic">
              {children}
            </blockquote>
          ),
          code: ({ className: codeClass, children, ...rest }) => {
            const isInline = !codeClass;
            if (isInline) {
              return (
                <code className="bg-secondary/60 text-primary/90 rounded px-1.5 py-0.5 text-[13px] font-mono">
                  {children}
                </code>
              );
            }
            return (
              <div className="relative my-3 rounded-xl border bg-[hsl(224,71%,3%)] overflow-hidden">
                <div className="flex items-center gap-2 px-4 py-2 border-b border-border/40 bg-secondary/20">
                  <div className="flex gap-1.5">
                    <span className="w-2.5 h-2.5 rounded-full bg-red-500/40" />
                    <span className="w-2.5 h-2.5 rounded-full bg-yellow-500/40" />
                    <span className="w-2.5 h-2.5 rounded-full bg-green-500/40" />
                  </div>
                  <span className="text-[10px] text-muted-foreground/50 uppercase tracking-wider font-medium">
                    {codeClass?.replace("language-", "") || "code"}
                  </span>
                </div>
                <pre className="overflow-x-auto p-4 text-[13px] leading-relaxed">
                  <code className={`font-mono text-foreground/90 ${codeClass || ""}`}>
                    {children}
                  </code>
                </pre>
              </div>
            );
          },
          table: ({ children }) => (
            <div className="my-3 overflow-x-auto rounded-xl border">
              <table className="w-full text-sm">{children}</table>
            </div>
          ),
          thead: ({ children }) => (
            <thead className="bg-secondary/30 border-b">{children}</thead>
          ),
          th: ({ children }) => (
            <th className="px-4 py-2.5 text-left text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              {children}
            </th>
          ),
          td: ({ children }) => (
            <td className="px-4 py-2.5 text-sm text-foreground/85 border-b border-border/30">
              {children}
            </td>
          ),
          hr: () => (
            <hr className="my-5 border-border/40" />
          ),
        }}
      >
        {cleaned}
      </ReactMarkdown>
    </div>
  );
}
