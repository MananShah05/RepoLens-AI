"use client";

import React, { useEffect, useState } from "react";
import { usePathname } from "next/navigation";
import { UserCircle, List } from "@phosphor-icons/react";
import { getRepo } from "@/lib/api";

interface TopbarProps {
  isCollapsed?: boolean;
  toggleSidebar?: () => void;
}

export default function Topbar({ isCollapsed = false, toggleSidebar }: TopbarProps) {
  const pathname = usePathname();
  const [repo, setRepo] = useState<any>(null);

  // Extract repo ID from URL
  const repoMatch = pathname.match(/^\/repos\/(\d+)/);
  const repoId = repoMatch ? Number(repoMatch[1]) : null;

  useEffect(() => {
    if (repoId) {
      getRepo(repoId)
        .then(setRepo)
        .catch(() => setRepo(null));
    } else {
      setRepo(null);
    }
  }, [repoId]);

  // Derive the current section name from the URL
  const sectionMatch = pathname.match(/^\/repos\/\d+\/(\w+)/);
  const section = sectionMatch ? sectionMatch[1] : repoId ? "dashboard" : "";

  return (
    <div className="flex items-center h-14 px-4">
      {toggleSidebar && (
        <button
          onClick={toggleSidebar}
          className="p-2 mr-1 rounded-md text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800/60 transition-colors focus:outline-none flex items-center justify-center"
          title={isCollapsed ? "Expand sidebar" : "Collapse sidebar"}
        >
          <List size={20} weight="bold" />
        </button>
      )}
      <div className="flex items-center gap-3">
        {repo ? (
          <div className="flex items-center gap-2 text-sm text-zinc-400">
            <span className="text-zinc-300 font-medium">{repo.owner}/{repo.name}</span>
            {section && (
              <>
                <span className="text-zinc-600">/</span>
                <span className="capitalize">{section}</span>
              </>
            )}
          </div>
        ) : (
          <div className="text-sm text-zinc-400">RepoLens AI</div>
        )}
      </div>
      <div className="flex-1" />
      <div className="flex items-center gap-4">
        {repo && (
          <div className="flex items-center gap-2 text-sm text-zinc-400">
            <span className="inline-flex items-center gap-2">
              <span
                className={`w-2 h-2 rounded-full ${
                  repo.status === "ready"
                    ? "bg-green-400"
                    : repo.status === "error"
                    ? "bg-red-400"
                    : "bg-yellow-400 animate-pulse"
                }`}
              />
              <span>{repo.status}</span>
            </span>
          </div>
        )}
        <div className="w-8 h-8 rounded-full bg-zinc-800 flex items-center justify-center">
          <UserCircle size={18} weight="duotone" className="text-zinc-300" />
        </div>
      </div>
    </div>
  );
}
