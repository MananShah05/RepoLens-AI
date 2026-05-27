"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { getTree, getFile, explainFile } from "@/lib/api";
import { ChevronRight, ChevronDown, FileCode, Loader2, Folder, FileText, Sparkles, Search } from "lucide-react";
import MarkdownRenderer from "@/app/components/ui/MarkdownRenderer";

interface TreeNode {
  name: string;
  type: "folder" | "file";
  id?: number;
  language?: string;
  children?: TreeNode[];
}

function TreeItem({ node, depth = 0, repoId, search }: { node: TreeNode; depth?: number; repoId: number; search: string }) {
  const [open, setOpen] = useState(depth < 2);
  const [fileData, setFileData] = useState<any>(null);
  const [explaining, setExplaining] = useState(false);
  const [explanation, setExplanation] = useState("");

  const matchesSearch = search && node.name.toLowerCase().includes(search.toLowerCase());

  async function loadFile() {
    if (!node.id || fileData) return;
    const data = await getFile(repoId, node.id);
    setFileData(data);
  }

  async function handleExplain() {
    if (!node.id) return;
    setExplaining(true);
    try {
      const res = await explainFile(repoId, node.id);
      setExplanation(res.explanation);
    } catch (e) {
      setExplanation("Could not generate explanation.");
    } finally {
      setExplaining(false);
    }
  }

  if (node.type === "folder") {
    return (
      <div>
        <button
          onClick={() => setOpen(!open)}
          className={`flex items-center w-full py-1.5 px-2 hover:bg-secondary/50 rounded-lg text-sm transition-colors group ${matchesSearch ? "bg-primary/5" : ""}`}
          style={{ paddingLeft: `${depth * 16 + 8}px` }}
        >
          {open ? <ChevronDown className="h-3.5 w-3.5 mr-1.5 text-muted-foreground shrink-0" /> : <ChevronRight className="h-3.5 w-3.5 mr-1.5 text-muted-foreground shrink-0" />}
          <Folder className="h-4 w-4 mr-1.5 text-primary/60 shrink-0" />
          <span className="font-medium text-sm">{node.name}</span>
          <span className="ml-auto text-xs text-muted-foreground/50">{node.children?.length || 0} items</span>
        </button>
        {open && node.children?.map((child) => (
          <TreeItem key={child.name} node={child} depth={depth + 1} repoId={repoId} search={search} />
        ))}
      </div>
    );
  }

  return (
    <div>
      <button
        onClick={loadFile}
        className={`flex items-center w-full py-1.5 px-2 hover:bg-secondary/50 rounded-lg text-sm transition-colors group ${matchesSearch ? "bg-primary/5 border border-primary/20" : ""}`}
        style={{ paddingLeft: `${depth * 16 + 8}px` }}
      >
        <FileCode className="h-4 w-4 mr-1.5 text-muted-foreground/60 shrink-0" />
        <span className="truncate">{node.name}</span>
        {node.language && (
          <span className="ml-auto text-[10px] text-muted-foreground/50 bg-secondary/50 rounded px-1.5 py-0.5">{node.language}</span>
        )}
      </button>
      {fileData && (
        <div className="mx-4 my-2 rounded-xl border bg-gradient-card shadow-sm animate-in">
          <div className="flex items-center justify-between p-3 border-b">
            <span className="text-sm font-medium truncate">{fileData.path}</span>
            <button
              onClick={handleExplain}
              disabled={explaining}
              className="inline-flex items-center gap-1.5 rounded-lg bg-secondary hover:bg-secondary/80 px-3 py-1.5 text-xs font-medium transition-colors disabled:opacity-50"
            >
              {explaining ? (
                <Loader2 className="h-3 w-3 animate-spin" />
              ) : (
                <Sparkles className="h-3 w-3" />
              )}
              Explain
            </button>
          </div>
          <pre className="max-h-72 overflow-auto p-3 text-xs leading-relaxed text-muted-foreground font-mono">{fileData.content_preview}</pre>
          {fileData.symbols && fileData.symbols.length > 0 && (
            <div className="px-3 pb-3">
              <div className="text-[10px] text-muted-foreground/60 uppercase tracking-wider mb-1.5 font-medium">Symbols</div>
              <div className="flex flex-wrap gap-1">
                {fileData.symbols.map((s: any, i: number) => (
                  <span key={i} className="text-[11px] bg-secondary/50 rounded-md px-2 py-0.5 font-mono text-muted-foreground">{s.name}</span>
                ))}
              </div>
            </div>
          )}
          {explanation && (
            <div className="px-3 pb-3 pt-2 border-t">
              <div className="flex items-center gap-1.5 mb-1.5">
                <Sparkles className="h-3 w-3 text-primary" />
                <span className="text-[10px] text-muted-foreground/60 uppercase tracking-wider font-medium">AI Explanation</span>
              </div>
              <MarkdownRenderer content={explanation} />
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default function ExplorePage() {
  const { id } = useParams();
  const repoId = Number(id);
  const [tree, setTree] = useState<TreeNode[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");

  useEffect(() => {
    getTree(repoId)
      .then((data) => setTree(data))
      .finally(() => setLoading(false));
  }, [repoId]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="flex flex-col items-center gap-3">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
          <p className="text-sm text-muted-foreground">Loading file tree...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="animate-in-up">
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-2xl font-bold tracking-tight">File Explorer</h1>
      </div>
      <div className="relative mb-4">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
        <input
          type="text"
          placeholder="Search files..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full rounded-xl border border-input bg-card pl-10 pr-4 py-2.5 text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-ring focus:border-ring transition-shadow"
        />
      </div>
      <div className="rounded-xl border bg-gradient-card shadow-sm">
        <div className="p-3">
          {tree.length > 0 ? (
            tree.map((node) => (
              <TreeItem key={node.name} node={node} repoId={repoId} search={search} />
            ))
          ) : (
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <Folder className="h-10 w-10 text-muted-foreground/30 mb-3" />
              <p className="text-sm text-muted-foreground">No files found</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
