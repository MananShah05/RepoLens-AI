"use client";

import { useState, useEffect } from "react";
import { listRepos, importRepo, deleteRepo } from "@/lib/api";
import { GitBranch, Loader2, Plus, Trash2, ExternalLink, Github, BookOpen } from "lucide-react";
import Link from "next/link";
import Button from "@/app/components/ui/Button";
import Input from "@/app/components/ui/Input";
import Card from "@/app/components/ui/Card";
import Badge from "@/app/components/ui/Badge";

interface Repo {
  id: number;
  name: string;
  owner: string;
  github_url: string;
  default_branch: string;
  status: string;
  status_message: string;
  language_summary: Record<string, number>;
  created_at: string;
}

const statusStyles: Record<string, string> = {
  ready: "bg-success/10 text-success border-success/20",
  pending: "bg-muted text-muted-foreground border-border",
  cloning: "bg-warning/10 text-warning border-warning/20",
  parsing: "bg-primary/10 text-primary border-primary/20",
  indexing: "bg-primary/10 text-primary border-primary/20",
  error: "bg-destructive/10 text-destructive border-destructive/20",
};

export default function HomePage() {
  const [repos, setRepos] = useState<Repo[]>([]);
  const [url, setUrl] = useState("");
  const [branch, setBranch] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function load() {
    try {
      const data = await listRepos();
      setRepos(data);
    } catch (e: any) {
      setError(e.message);
    }
  }

  useEffect(() => {
    load();
    const interval = setInterval(load, 3000);
    return () => clearInterval(interval);
  }, []);

  async function handleImport(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      await importRepo(url, branch || undefined);
      setUrl("");
      setBranch("");
      await load();
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleDelete(id: number) {
    if (!confirm("Delete this repository?")) return;
    try {
      await deleteRepo(id);
      await load();
    } catch (e: any) {
      setError(e.message || "Failed to delete repository");
    }
  }

  return (
    <div className="min-h-[calc(100vh-3.5rem)]">
      <section className="relative overflow-hidden border-b">
        <div className="absolute inset-0 bg-gradient-hero" />
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top_right,hsl(var(--primary)/0.08),transparent_50%)]" />
        <div className="relative max-w-4xl mx-auto px-6 pt-20 pb-24 text-left">
          <div className="inline-flex items-center gap-2 rounded-full border bg-[color:var(--card)]/40 px-3 py-1 text-xs text-zinc-400 mb-6">
            <BookOpen className="h-3 w-3" />
            <span className="font-medium">AI-Powered Codebase Intelligence</span>
          </div>
          <h1 className="font-display text-5xl sm:text-6xl font-bold tracking-tight mb-4">
            Understand any <span className="text-[color:rgb(var(--primary))]">repository</span>
            <br />
            in seconds
          </h1>
          <p className="text-base leading-relaxed text-zinc-400 max-w-[65ch] mb-8">
            Turn any GitHub repository into an interactive, explainable knowledge base. Get AI-powered summaries, architecture diagrams, and chat with your codebase.
          </p>

          <form onSubmit={handleImport} className="flex flex-col sm:flex-row gap-3 max-w-4xl w-full">
            <div className="flex-1 relative">
              <Github className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-zinc-400" />
              <Input
                type="url"
                required
                placeholder="https://github.com/owner/repo"
                value={url}
                onChange={(e: any) => setUrl(e.target.value)}
                className="pl-10"
              />
            </div>
            <Input
              type="text"
              placeholder="branch (optional)"
              value={branch}
              onChange={(e: any) => setBranch(e.target.value)}
              className="sm:w-36"
            />
            <Button type="submit" disabled={loading} className="inline-flex items-center gap-2">
              {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Plus className="h-4 w-4" />}
              Import
            </Button>
          </form>
        </div>
      </section>

      <section className="max-w-[1400px] mx-auto px-6 py-12">
        {error && (
          <div className="mb-8 text-sm text-red-400">{error}</div>
        )}

        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-xl font-semibold">Your Repositories</h2>
            <p className="text-sm text-zinc-400 mt-0.5">{repos.length} repo{repos.length !== 1 ? "s" : ""} imported</p>
          </div>
          {repos.length > 0 && (
            <Button onClick={load} variant="ghost">Refresh</Button>
          )}
        </div>

        {repos.length === 0 ? (
          <div className="py-16">
            <Card className="p-8 text-zinc-400">
              <div className="flex items-center gap-4">
                <Github className="h-8 w-8 text-zinc-400" />
                <div>
                  <h3 className="text-lg font-medium mb-1">No repositories yet</h3>
                  <p className="text-sm text-zinc-400 max-w-sm">Paste a GitHub URL above to import your first repository and start exploring.</p>
                </div>
              </div>
            </Card>
          </div>
        ) : (
          <div className="grid gap-4 md:grid-cols-2">
            {repos.map((repo, i) => (
              <Card key={repo.id} className="group relative p-5">
                <Link href={`/repos/${repo.id}`} className="absolute inset-0 rounded-xl" />
                <div className="relative">
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="text-base font-semibold truncate">{repo.owner}/{repo.name}</h3>
                      <div className="flex items-center gap-3 text-xs text-zinc-400 mt-1">
                        <span className="flex items-center gap-1"><GitBranch className="h-3 w-3" />{repo.default_branch}</span>
                        <Badge className="bg-zinc-800 text-xs px-2">{repo.status}</Badge>
                      </div>
                    </div>
                    <button onClick={(e) => { e.preventDefault(); handleDelete(repo.id); }} className="p-1.5 rounded-md text-zinc-400 hover:text-red-400">
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                  {repo.status_message && <p className="mt-2 text-xs text-zinc-400/80">{repo.status_message}</p>}
                  {repo.language_summary && Object.keys(repo.language_summary).length > 0 && (
                    <div className="mt-3 flex flex-wrap gap-2">
                      {Object.entries(repo.language_summary).sort((a,b)=> b[1]-a[1]).slice(0,5).map(([lang,count])=> (
                        <span key={lang} className="inline-flex items-center rounded-full bg-zinc-800 text-xs px-2 py-0.5 text-zinc-300">{lang} <span className="ml-1 text-[10px] text-zinc-500">{count as number}</span></span>
                      ))}
                    </div>
                  )}
                </div>
              </Card>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
