"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { getOnboarding } from "@/lib/api";
import { Loader2, BookOpen, Compass } from "lucide-react";
import MarkdownRenderer from "@/app/components/ui/MarkdownRenderer";

export default function OnboardingPage() {
  const { id } = useParams();
  const repoId = Number(id);
  const [guide, setGuide] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getOnboarding(repoId)
      .then((res) => setGuide(res.guide))
      .catch(() => setGuide("Could not load onboarding guide."))
      .finally(() => setLoading(false));
  }, [repoId]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="flex flex-col items-center gap-3">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
          <p className="text-sm text-muted-foreground">Generating onboarding guide...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="animate-in-up">
      <div className="flex items-center gap-3 mb-6">
        <div className="flex items-center justify-center w-10 h-10 rounded-xl bg-gradient-primary shadow-lg shadow-primary/25">
          <Compass className="h-5 w-5 text-white" />
        </div>
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Onboarding Guide</h1>
          <p className="text-sm text-muted-foreground mt-0.5">AI-generated guide to help you get started</p>
        </div>
      </div>

      <div className="rounded-xl border bg-gradient-card p-6 shadow-sm">
        <div className="flex items-center gap-2 mb-4 pb-3 border-b">
          <BookOpen className="h-4 w-4 text-primary" />
          <span className="text-sm font-medium">Getting Started Guide</span>
        </div>
        <MarkdownRenderer content={guide} />
      </div>
    </div>
  );
}
