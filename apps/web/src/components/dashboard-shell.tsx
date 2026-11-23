"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { getAccessToken } from "@/lib/auth";
import { api } from "@/lib/api";
import { AppSidebar } from "@/components/app-sidebar";

export function DashboardShell({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const [userName, setUserName] = useState<string>();
  const [ready, setReady] = useState(false);

  useEffect(() => {
    if (!getAccessToken()) {
      router.replace("/login");
      return;
    }
    api
      .me()
      .then((u) => {
        setUserName(u.full_name);
        setReady(true);
      })
      .catch(() => {
        router.replace("/login");
      });
  }, [router]);

  if (!ready) {
    return (
      <div className="flex h-screen items-center justify-center text-muted-foreground">Loading workspace…</div>
    );
  }

  return (
    <div className="flex min-h-screen bg-background">
      <AppSidebar userName={userName} />
      <main className="min-w-0 flex-1 overflow-auto p-6 lg:p-8">{children}</main>
    </div>
  );
}