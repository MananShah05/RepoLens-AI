"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { getRepo, getRepoStatus, getSummary, getFiles } from "@/lib/api";
import MarkdownRenderer from "@/app/components/ui/MarkdownRenderer";
import {
  Loader2,
  FileCode,
  Building2,
  GitBranch,
  CheckCircle2,
  AlertCircle,
  ExternalLink,
  MessageSquare,
  FolderTree,
  Boxes,
  Compass,
} from "lucide-react";

const quickLinks = [
  {
    label: "Chat",
    desc: "Ask questions about the codebase",
    icon: MessageSquare,
    path: "chat",
    color: "from-violet-500/20 to-purple-600/10",
    iconColor: "text-violet-400",
  },
  {
    label: "Explorer",
    desc: "Browse files and get AI explanations",
    icon: FolderTree,
    path: "explore",
    color: "from-emerald-500/20 to-green-600/10",
    iconColor: "text-emerald-400",
  },
  {
    label: "Architecture",
    desc: "System overview and dependency graph",
    icon: Boxes,
    path: "architecture",
    color: "from-sky-500/20 to-blue-600/10",
    iconColor: "text-sky-400",
  },
  {
    label: "Onboarding",
    desc: "AI-generated getting started guide",
    icon: Compass,
    path: "onboarding",
    color: "from-amber-500/20 to-orange-600/10",
    iconColor: "text-amber-400",
  },
];

export default function RepoDashboardPage() {
  const { id } = useParams();
  const repoId = Number(id);
  const [repo, setRepo] = useState<any>(null);
  const [summary, setSummary] = useState("");
  const [files, setFiles] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const r = await getRepo(repoId);
        setRepo(r);
        const f = await getFiles(repoId);
        setFiles(f);
        if (r.status === "ready") {
          const s = await getSummary(repoId);
          setSummary(s.summary);
        }
      } catch (e) {
        // ignore
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [repoId]);

  useEffect(() => {
    if (!repo || repo.status === "ready" || repo.status === "error") return;

    const interval = setInterval(async () => {
      try {
        const r = await getRepoStatus(repoId);
        if (r.status !== repo.status) {
          const full = await getRepo(repoId);
          setRepo(full);
          if (full.status === "ready") {
            const s = await getSummary(repoId);
            setSummary(s.summary);
            const f = await getFiles(repoId);
            setFiles(f);
          }
        }
      } catch (e) {
        // ignore
      }
    }, 3000);

    return () => clearInterval(interval);
  }, [repoId, repo, summary]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="flex flex-col items-center gap-3">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
          <p className="text-sm text-muted-foreground">Loading repository...</p>
        </div>
      </div>
    );
  }

  if (!repo) return (
    <div className="flex flex-col items-center justify-center h-64 gap-3">
      <AlertCircle className="h-8 w-8 text-destructive" />
      <p className="text-sm text-muted-foreground">Repository not found</p>
      <Link href="/" className="text-sm text-primary hover:underline">Back to repositories</Link>
    </div>
  );

  const langSummary = repo.language_summary || {};
  const langCount = Object.keys(langSummary).length;
  const totalLangFiles = Object.values(langSummary).reduce((a: number, b: any) => a + Number(b), 0);

  const stats = [
    { label: "Files", value: files.length, icon: FileCode },
    { label: "Languages", value: langCount, icon: Building2 },
    { label: "Branch", value: repo.default_branch, icon: GitBranch },
    {
      label: "Status",
      value: repo.status === "ready" ? "Ready" : "Processing",
      icon: repo.status === "ready" ? CheckCircle2 : Loader2,
    },
  ];

  return (
    <div className="space-y-6 animate-in-up">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">
            {repo.owner}/<span className="text-primary">{repo.name}</span>
          </h1>
          <a
            href={repo.github_url}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground transition-colors mt-0.5"
          >
            {repo.github_url}
            <ExternalLink className="h-3 w-3" />
          </a>
        </div>
        <span className={`inline-flex items-center rounded-full border px-3 py-1 text-xs font-medium capitalize ${
          repo.status === "ready"
            ? "bg-success/10 text-success border-success/20"
            : repo.status === "error"
            ? "bg-destructive/10 text-destructive border-destructive/20"
            : "bg-warning/10 text-warning border-warning/20"
        }`}>
          {repo.status === "ready" ? <CheckCircle2 className="h-3 w-3 mr-1" /> : <Loader2 className="h-3 w-3 mr-1 animate-spin" />}
          {repo.status}
        </span>
      </div>

      {/* Processing / Error banners */}
      {repo.status !== "ready" && repo.status !== "error" && (
        <div className="rounded-xl border border-primary/10 bg-primary/[0.03] p-4">
          <div className="flex items-center gap-3">
            <Loader2 className="h-5 w-5 animate-spin text-primary" />
            <div>
              <p className="text-sm font-medium">Analysis in progress</p>
              <p className="text-xs text-muted-foreground mt-0.5">
                {repo.status_message || `Status: ${repo.status}`}
              </p>
            </div>
          </div>
        </div>
      )}

      {repo.status === "error" && (
        <div className="rounded-xl border border-destructive/20 bg-destructive/[0.03] p-4">
          <div className="flex items-center gap-3">
            <AlertCircle className="h-5 w-5 text-destructive shrink-0" />
            <div>
              <p className="text-sm font-medium text-destructive">Analysis failed</p>
              <p className="text-xs text-muted-foreground mt-0.5">{repo.status_message}</p>
            </div>
          </div>
        </div>
      )}

      {/* Stats row */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {stats.map((stat) => (
          <div key={stat.label} className="rounded-xl border bg-gradient-card p-4 hover:border-primary/20 transition-colors">
            <div className="flex items-center gap-2 text-xs text-muted-foreground mb-2">
              <stat.icon className={`h-3.5 w-3.5 ${stat.label === "Status" && repo.status !== "ready" ? "animate-spin" : ""}`} />
              {stat.label}
            </div>
            <div className="text-2xl font-semibold tracking-tight">{stat.value}</div>
          </div>
        ))}
      </div>

      {/* Main two-column grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        {/* Left column — Summary + Quick Access */}
        <div className="lg:col-span-2 space-y-5">
          {summary && (
            <div className="rounded-xl border bg-gradient-card p-5 animate-in-up">
              <h2 className="text-lg font-semibold mb-3 flex items-center gap-2">
                <Building2 className="h-4 w-4 text-primary" />
                Repository Summary
              </h2>
              <MarkdownRenderer content={summary} />
            </div>
          )}

          {/* Quick Access Panel */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {quickLinks.map((link) => (
              <Link
                key={link.path}
                href={`/repos/${repoId}/${link.path}`}
                className={`group rounded-xl border bg-gradient-to-br ${link.color} p-4 hover:border-primary/30 transition-all hover:shadow-lg hover:shadow-primary/5`}
              >
                <div className="flex items-start gap-3">
                  <div className={`flex items-center justify-center w-9 h-9 rounded-lg bg-card/60 border border-border/30 ${link.iconColor}`}>
                    <link.icon className="h-4 w-4" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <h3 className="text-sm font-semibold group-hover:text-foreground transition-colors">
                      {link.label}
                    </h3>
                    <p className="text-xs text-muted-foreground mt-0.5 leading-relaxed">
                      {link.desc}
                    </p>
                  </div>
                </div>
              </Link>
            ))}
          </div>
        </div>

        {/* Right column — Languages */}
        <div className="space-y-5">
          {langCount > 0 && (
            <div className="rounded-xl border bg-gradient-card p-5">
              <h2 className="text-base font-semibold mb-4">Languages</h2>
              <div className="space-y-3">
                {Object.entries(langSummary)
                  .sort((a: any, b: any) => b[1] - a[1])
                  .map(([lang, count]: [string, any]) => {
                    const pct = totalLangFiles > 0 ? Math.round((count / totalLangFiles) * 100) : 0;
                    return (
                      <div key={lang}>
                        <div className="flex items-center justify-between text-sm mb-1.5">
                          <span className="font-medium capitalize">{lang}</span>
                          <span className="text-xs text-muted-foreground">{count} files · {pct}%</span>
                        </div>
                        <div className="h-1.5 rounded-full bg-secondary/50 overflow-hidden">
                          <div
                            className="h-full rounded-full bg-gradient-to-r from-primary/80 to-primary/40 transition-all duration-500"
                            style={{ width: `${Math.max(pct, 2)}%` }}
                          />
                        </div>
                      </div>
                    );
                  })}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
