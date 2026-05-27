"use client";

import { useEffect, useState, useRef } from "react";
import { useParams } from "next/navigation";
import { getArchitecture, getGraph, apiFetch } from "@/lib/api";
import { Loader2, RefreshCw, GitBranch, Boxes, ZoomIn, ZoomOut, Maximize2, Move } from "lucide-react";
import MarkdownRenderer from "@/app/components/ui/MarkdownRenderer";

interface ZoomPanContainerProps {
  children: React.ReactNode;
}

function ZoomPanContainer({ children }: ZoomPanContainerProps) {
  const [scale, setScale] = useState(1);
  const [position, setPosition] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });

  const containerRef = useRef<HTMLDivElement>(null);

  const handleMouseDown = (e: React.MouseEvent<HTMLDivElement>) => {
    if (e.button !== 0) return; // Only drag with left mouse button
    setIsDragging(true);
    setDragStart({ x: e.clientX - position.x, y: e.clientY - position.y });
  };

  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!isDragging) return;
    setPosition({
      x: e.clientX - dragStart.x,
      y: e.clientY - dragStart.y,
    });
  };

  const handleMouseUp = () => {
    setIsDragging(false);
  };

  const handleWheel = (e: React.WheelEvent<HTMLDivElement>) => {
    e.preventDefault();
    const zoomFactor = 1.05;
    let newScale = scale;
    if (e.deltaY < 0) {
      newScale = Math.min(scale * zoomFactor, 4);
    } else {
      newScale = Math.max(scale / zoomFactor, 0.25);
    }

    if (containerRef.current) {
      const rect = containerRef.current.getBoundingClientRect();
      const mouseX = e.clientX - rect.left;
      const mouseY = e.clientY - rect.top;

      // Adjust position to zoom into mouse cursor
      const dx = mouseX - position.x;
      const dy = mouseY - position.y;

      setPosition({
        x: mouseX - dx * (newScale / scale),
        y: mouseY - dy * (newScale / scale),
      });
    }

    setScale(newScale);
  };

  const handleZoomIn = () => {
    setScale((prev) => Math.min(prev * 1.15, 4));
  };

  const handleZoomOut = () => {
    setScale((prev) => Math.max(prev / 1.15, 0.25));
  };

  const handleReset = () => {
    setScale(1);
    setPosition({ x: 0, y: 0 });
  };

  return (
    <div className="relative border rounded-xl overflow-hidden bg-background/30 select-none">
      {/* Zoom / Pan Controls Overlay */}
      <div className="absolute right-4 top-4 z-10 flex items-center gap-1 bg-card/80 backdrop-blur border border-border/60 rounded-xl p-1 shadow-lg">
        <button
          onClick={handleZoomIn}
          className="p-2 rounded-lg hover:bg-secondary transition-colors text-foreground/80 hover:text-foreground active:scale-95"
          title="Zoom In"
        >
          <ZoomIn className="h-4 w-4" />
        </button>
        <button
          onClick={handleZoomOut}
          className="p-2 rounded-lg hover:bg-secondary transition-colors text-foreground/80 hover:text-foreground active:scale-95"
          title="Zoom Out"
        >
          <ZoomOut className="h-4 w-4" />
        </button>
        <div className="w-[1px] h-4 bg-border/60 mx-1" />
        <button
          onClick={handleReset}
          className="p-2 rounded-lg hover:bg-secondary transition-colors text-foreground/80 hover:text-foreground active:scale-95"
          title="Fit / Reset View"
        >
          <Maximize2 className="h-4 w-4" />
        </button>
      </div>

      {/* Instructional text at bottom-left */}
      <div className="absolute left-4 bottom-4 z-10 flex items-center gap-1.5 text-xs text-muted-foreground bg-card/50 backdrop-blur px-2.5 py-1 rounded-lg border border-border/30">
        <Move className="h-3 w-3" />
        <span>Drag to pan · Scroll to zoom</span>
      </div>

      <div
        ref={containerRef}
        className="w-full relative overflow-hidden cursor-grab active:cursor-grabbing bg-background/25"
        style={{ minHeight: "450px", height: "65vh" }}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
        onWheel={handleWheel}
      >
        <div
          className="absolute w-full h-full flex items-center justify-center p-8 transition-transform duration-75 ease-out"
          style={{
            transform: `translate(${position.x}px, ${position.y}px) scale(${scale})`,
            transformOrigin: "center center",
          }}
        >
          {children}
        </div>
      </div>
    </div>
  );
}

export default function ArchitecturePage() {
  const { id } = useParams();
  const repoId = Number(id);
  const [architecture, setArchitecture] = useState("");
  const [graph, setGraph] = useState("");
  const [loading, setLoading] = useState(true);
  const [svg, setSvg] = useState("");

  async function load() {
    setLoading(true);
    try {
      const [a, g] = await Promise.all([getArchitecture(repoId), getGraph(repoId)]);
      setArchitecture(a.architecture);
      setGraph(g.payload);
    } catch (e) {
      // ignore
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, [repoId]);

  useEffect(() => {
    if (!graph) return;
    let cancelled = false;
    async function render() {
      try {
        const mermaid = await import("mermaid");
        mermaid.default.initialize({
          startOnLoad: false,
          theme: "dark",
          flowchart: {
            useMaxWidth: true,
            htmlLabels: true,
            curve: "basis",
            rankSpacing: 50,
            nodeSpacing: 30,
            padding: 15,
          },
          themeVariables: {
            fontSize: "14px",
            primaryColor: "#7c3aed",
            primaryTextColor: "#f4f4f5",
            primaryBorderColor: "#7c3aed",
            lineColor: "#6366f1",
            secondaryColor: "#1e1b4b",
            tertiaryColor: "#0f172a",
          },
          maxTextSize: 100000,
        });
        const { svg } = await mermaid.default.render("mermaid-graph", graph);
        if (!cancelled) setSvg(svg);
      } catch (e) {
        if (!cancelled) setSvg("");
      }
    }
    render();
    return () => {
      cancelled = true;
    };
  }, [graph]);

  async function regenerate() {
    try {
      await apiFetch(`/repos/${repoId}/diagram/regenerate`, { method: "POST" });
      const g = await getGraph(repoId);
      setGraph(g.payload);
    } catch (e) {
      // ignore regenerate errors
    }
  }

  return (
    <div className="space-y-6 animate-in-up">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Architecture</h1>
          <p className="text-sm text-muted-foreground mt-0.5">System overview and dependency graph</p>
        </div>
        <button
          onClick={regenerate}
          className="inline-flex items-center gap-2 rounded-xl border bg-secondary/50 px-4 py-2 text-sm font-medium hover:bg-secondary transition-colors"
        >
          <RefreshCw className="h-3.5 w-3.5" />
          Regenerate
        </button>
      </div>

      {loading && (
        <div className="flex items-center justify-center h-48">
          <div className="flex flex-col items-center gap-3">
            <Loader2 className="h-8 w-8 animate-spin text-primary" />
            <p className="text-sm text-muted-foreground">Analyzing architecture...</p>
          </div>
        </div>
      )}

      {architecture && (
        <div className="rounded-xl border bg-gradient-card p-5 animate-in-up">
          <h2 className="text-lg font-semibold mb-3 flex items-center gap-2">
            <Boxes className="h-4 w-4 text-primary" />
            Architecture Overview
          </h2>
          <MarkdownRenderer content={architecture} />
        </div>
      )}

      <div className="rounded-xl border bg-gradient-card p-5">
        <h2 className="text-lg font-semibold mb-3 flex items-center gap-2">
          <GitBranch className="h-4 w-4 text-primary" />
          Dependency Graph
        </h2>
        {svg ? (
          <ZoomPanContainer>
            <div
              className="w-full flex items-center justify-center p-4 [&_svg]:w-full [&_svg]:h-auto"
              dangerouslySetInnerHTML={{ __html: svg }}
            />
          </ZoomPanContainer>
        ) : (
          <div className="flex items-center justify-center h-32 rounded-lg bg-muted/30">
            <p className="text-sm text-muted-foreground">
              {graph ? "Rendering graph..." : "No graph available yet."}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
