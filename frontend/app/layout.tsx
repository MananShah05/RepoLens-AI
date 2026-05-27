import './globals.css';
import DashboardLayout from "@/app/components/DashboardLayout";

export const metadata = {
  title: "RepoLens AI",
  description: "AI-powered GitHub repository understanding platform",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="" />
        <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet" />
      </head>
      <body className="min-h-[100dvh] bg-background text-foreground antialiased">
        <DashboardLayout>
          {children}
        </DashboardLayout>
      </body>
    </html>
  );
}
