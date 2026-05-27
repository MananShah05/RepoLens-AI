"use client";

import React, { useState, useEffect } from "react";
import Sidebar from "./Sidebar";
import Topbar from "./Topbar";

interface DashboardLayoutProps {
  children: React.ReactNode;
}

export default function DashboardLayout({ children }: DashboardLayoutProps) {
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    // Only run on client
    setMounted(true);
    const saved = localStorage.getItem("sidebar-collapsed");
    if (saved !== null) {
      setIsCollapsed(saved === "true");
    }
  }, []);

  const toggleSidebar = () => {
    const nextState = !isCollapsed;
    setIsCollapsed(nextState);
    localStorage.setItem("sidebar-collapsed", String(nextState));
  };

  return (
    <div className="flex min-h-[100dvh] bg-background">
      <aside
        className={`h-[100dvh] sticky top-0 border-r border-zinc-800 bg-[color:var(--card)] transition-all duration-300 ease-in-out shrink-0 overflow-y-auto overflow-x-hidden ${
          isCollapsed ? "w-16" : "w-60"
        }`}
      >
        <Sidebar isCollapsed={isCollapsed} toggleSidebar={toggleSidebar} />
      </aside>
      <div className="flex-1 min-h-[100dvh] flex flex-col min-w-0">
        <div className="h-14 w-full border-b bg-[color:var(--card)] shrink-0">
          <Topbar isCollapsed={isCollapsed} toggleSidebar={toggleSidebar} />
        </div>
        <main className="flex-1 overflow-auto">
          <div className="max-w-[1400px] mx-auto px-6 py-8">{children}</div>
        </main>
      </div>
    </div>
  );
}
