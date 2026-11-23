"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import type { Communication } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export default function ApprovalsPage() {
  const [items, setItems] = useState<Communication[]>([]);
  const [loading, setLoading] = useState<string | null>(null);

  function reload() {
    void api.pendingApprovals().then(setItems);
  }

  useEffect(() => {
    reload();
  }, []);

  async function approveAndSend(id: string) {
    setLoading(id);
    try {
      await api.approveCommunication(id);
      await api.sendCommunication(id);
      reload();
    } finally {
      setLoading(null);
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-semibold tracking-tight">Message approvals</h1>
        <p className="text-muted-foreground">Review AI-generated outbound email before sending</p>
      </div>

      {items.length === 0 ? (
        <Card>
          <CardContent className="py-10 text-center text-sm text-muted-foreground">
            No messages awaiting approval
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-4">
          {items.map((item) => (
            <Card key={item.id}>
              <CardHeader className="flex flex-row items-start justify-between gap-4">
                <div>
                  <CardTitle className="text-base">{item.subject ?? "No subject"}</CardTitle>
                  <CardDescription>
                    Lead{" "}
                    <Link href={`/leads/${item.lead_id}`} className="text-primary hover:underline">
                      {item.lead_id.slice(0, 8)}…
                    </Link>
                    {item.ai_generated ? " · AI-generated" : ""}
                  </CardDescription>
                </div>
                <Button size="sm" disabled={loading === item.id} onClick={() => void approveAndSend(item.id)}>
                  {loading === item.id ? "Sending…" : "Approve & send"}
                </Button>
              </CardHeader>
              <CardContent>
                <pre className="max-h-40 overflow-auto whitespace-pre-wrap rounded-md bg-muted/40 p-3 text-xs">
                  {item.body}
                </pre>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}