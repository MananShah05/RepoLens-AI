"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { List, Gear, Chat, Graph, TreeStructure, BookOpen, CaretLeft, CaretRight } from "@phosphor-icons/react";
import { listRepos } from "@/lib/api";

interface Repo {
  id: number;
  name: string;
  owner: string;
  status: string;
}

const NavItem = ({
  href,
  icon: Icon,
  active,
  children,
  isCollapsed,
}: {
  href: string;
  icon: any;
  active: boolean;
  children: React.ReactNode;
  isCollapsed?: boolean;
}) => (
  <Link
    href={href}
    title={isCollapsed ? String(children) : undefined}
    className={`flex items-center rounded-md transition-all ${
      isCollapsed ? "justify-center h-10 w-10 mx-auto px-0" : "gap-3 px-4 py-2 text-sm"
    } ${
      active
        ? "bg-zinc-800 text-white font-medium"
        : "text-zinc-400 hover:bg-zinc-800/60 hover:text-zinc-200"
    }`}
  >
    {Icon ? (
      <Icon size={isCollapsed ? 20 : 18} weight={active ? "fill" : "duotone"} />
    ) : (
      <span className="inline-block w-4 h-4 rounded bg-zinc-700" />
    )}
    {!isCollapsed && <span>{children}</span>}
  </Link>
);

interface SidebarProps {
  isCollapsed?: boolean;
  toggleSidebar?: () => void;
}

export default function Sidebar({ isCollapsed = false, toggleSidebar }: SidebarProps) {
  const pathname = usePathname();
  const router = useRouter();
  const [repos, setRepos] = useState<Repo[]>([]);

  // Extract repo ID from the current path: /repos/123/...
  const repoMatch = pathname.match(/^\/repos\/(\d+)/);
  const currentRepoId = repoMatch ? repoMatch[1] : null;

  useEffect(() => {
    function load() {
      listRepos()
        .then((data: Repo[]) => setRepos(data))
        .catch(() => {});
    }
    load();
    const interval = setInterval(load, 5000);
    return () => clearInterval(interval);
  }, []);

  const currentRepo = repos.find((r) => String(r.id) === currentRepoId);

  function handleRepoChange(e: React.ChangeEvent<HTMLSelectElement>) {
    const repoId = e.target.value;
    if (repoId) {
      router.push(`/repos/${repoId}`);
    }
  }

  // Build nav items — context-aware based on whether a repo is selected
  const repoNav = currentRepoId
    ? [
        { href: `/repos/${currentRepoId}`, label: "Dashboard", icon: List },
        { href: `/repos/${currentRepoId}/chat`, label: "Chat", icon: Chat },
        { href: `/repos/${currentRepoId}/explore`, label: "Explore", icon: TreeStructure },
        { href: `/repos/${currentRepoId}/architecture`, label: "Architecture", icon: Graph },
        { href: `/repos/${currentRepoId}/onboarding`, label: "Onboarding", icon: BookOpen },
      ]
    : [];

  return (
    <div className="flex flex-col h-full">
      <Link
        href="/"
        className={`flex items-center hover:opacity-80 transition-opacity ${
          isCollapsed ? "justify-center py-4 px-0" : "gap-3 px-4 py-4"
        }`}
      >
        {isCollapsed ? (
          <div className="flex items-center justify-center w-9 h-9 rounded-lg bg-zinc-800 text-cyan-400 font-semibold text-lg border border-zinc-700 shadow-sm">
            R
          </div>
        ) : (
          <div className="flex items-center gap-2">
            <span style={{ fontFamily: "Geist" }} className="text-lg font-semibold">
              RepoLens
            </span>
            <span className="w-2 h-2 rounded-full bg-cyan-400" />
          </div>
        )}
      </Link>

      {!isCollapsed && (
        <div className="px-3">
          <div className="mt-2 rounded-md border border-zinc-800 bg-zinc-900/40 p-2">
            <select
              className="w-full bg-transparent text-sm text-zinc-300 p-2 rounded cursor-pointer outline-none"
              value={currentRepoId || ""}
              onChange={handleRepoChange}
            >
              <option value="" disabled>
                Select a repository
              </option>
              {repos.map((repo) => (
                <option key={repo.id} value={repo.id}>
                  {repo.owner}/{repo.name}
                </option>
              ))}
            </select>
          </div>
        </div>
      )}

      <nav className={`mt-6 flex-1 space-y-1 ${isCollapsed ? "px-1" : "px-2"}`}>
        <NavItem href="/" icon={List} active={pathname === "/"} isCollapsed={isCollapsed}>
          Repositories
        </NavItem>

        {repoNav.length > 0 && (
          <>
            {isCollapsed ? (
              <div className="border-t border-zinc-800/80 my-3 mx-2" />
            ) : (
              <div className="pt-4 pb-1 px-2">
                <span className="text-[10px] font-semibold uppercase tracking-wider text-zinc-500">
                  {currentRepo ? `${currentRepo.owner}/${currentRepo.name}` : "Repository"}
                </span>
              </div>
            )}
            {repoNav.map((item) => (
              <NavItem
                key={item.label}
                href={item.href}
                icon={item.icon}
                active={pathname === item.href}
                isCollapsed={isCollapsed}
              >
                {item.label}
              </NavItem>
            ))}
          </>
        )}

        {isCollapsed ? (
          <div className="border-t border-zinc-800/80 my-3 mx-2" />
        ) : (
          <div className="pt-4 pb-1 px-2">
            <span className="text-[10px] font-semibold uppercase tracking-wider text-zinc-500">
              Dev
            </span>
          </div>
        )}
        <NavItem href="/components" icon={Gear} active={pathname === "/components"} isCollapsed={isCollapsed}>
          Components
        </NavItem>
      </nav>

      <div className={`mt-auto border-t border-zinc-800/60 ${isCollapsed ? "px-1 py-3" : "px-2 py-4"}`}>
        {toggleSidebar && (
          <button
            onClick={toggleSidebar}
            className={`flex items-center gap-3 w-full rounded-md text-zinc-400 hover:bg-zinc-800/60 hover:text-zinc-200 transition-all mb-3 ${
              isCollapsed ? "justify-center h-10 w-10 mx-auto px-0" : "px-4 py-2 text-sm"
            }`}
            title={isCollapsed ? "Expand sidebar" : "Collapse sidebar"}
          >
            {isCollapsed ? (
              <CaretRight size={18} weight="bold" />
            ) : (
              <>
                <CaretLeft size={18} weight="bold" />
                <span>Collapse Sidebar</span>
              </>
            )}
          </button>
        )}
        {!isCollapsed && (
          <div className="px-4 text-xs text-zinc-500">v0.1.0</div>
        )}
      </div>
    </div>
  );
}
