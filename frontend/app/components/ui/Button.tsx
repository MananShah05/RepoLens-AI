"use client";

import React from "react";
import { cn } from "@/lib/utils";

type ButtonProps = React.ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "primary" | "secondary" | "ghost";
  size?: "sm" | "md" | "lg";
};

export default function Button({ children, variant = "primary", size = "md", className, ...props }: ButtonProps) {
  const base = "inline-flex items-center justify-center rounded-md font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2";
  const variants: Record<string, string> = {
    primary: "bg-primary text-primary-foreground hover:brightness-95",
    secondary: "bg-secondary text-foreground hover:bg-secondary/80",
    ghost: "bg-transparent text-primary hover:bg-primary/5",
  };
  const sizes: Record<string, string> = {
    sm: "px-2 py-1 text-sm",
    md: "px-4 py-2 text-sm",
    lg: "px-6 py-3 text-base",
  };

  return (
    <button className={cn(base, variants[variant], sizes[size], className)} {...props}>
      {children}
    </button>
  );
}
