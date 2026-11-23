"use client";

import { useCallback, useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, Sparkles } from "lucide-react";
import { api } from "@/lib/api";
import type { Communication, Lead, LeadDetail, LeadPriority, LeadQualification, LeadStatus } from "@/lib/types";
import { PriorityBadge } from "@/components/priority-badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";

export default function LeadDetailPage() {
  const params = useParams<{ id: string }>();
  const [detail, setDetail] = useState<LeadDetail | null>(null);
  const [note, setNote] = useState("");
  const [saving, setSaving] = useState(false);
  const [qualifying, setQualifying] = useState(false);
  const [comms, setComms] = useState<Communication[]>([]);

  const load = useCallback(() => {
    if (!params.id) return;
    void api.lead(params.id).then(setDetail);
    void api.leadCommunications(params.id).then(setComms);
  }, [params.id]);

  useEffect(() => {
    load();
  }, [load]);

  const lead = detail?.lead;
  const qualification = detail?.latest_qualification ?? null;

  async function savePatch(patch: Record<string, unknown>) {
    if (!lead) return;
    setSaving(true);
    try {
      const updated = await api.patchLead(lead.id, patch);
      setDetail((prev) => (prev ? { ...prev, lead: updated } : prev));
    } finally {
      setSaving(false);
    }
  }

  async function requalify() {
    if (!lead) return;
    setQualifying(true);
    try {
      const row = await api.qualifyLead(lead.id);
      load();
      setDetail((prev) =>
        prev
          ? {
              ...prev,
              latest_qualification: row,
              lead: { ...prev.lead, priority: row.priority, status: "qualified" },
            }
          : prev
      );
    } finally {
      setQualifying(false);
    }
  }

  async function addNote() {
    if (!lead || !note.trim()) return;
    await api.addNote(lead.id, note.trim());
    setNote("");
  }

  if (!lead) {
    return <p className="text-muted-foreground">Loading lead…</p>;
  }

  return (
    <div className="mx-auto max-w-5xl space-y-6">
      <div className="flex flex-wrap items-center gap-3">
        <Button variant="ghost" size="sm" asChild>
          <Link href="/leads">
            <ArrowLeft className="mr-1 h-4 w-4" /> Back
          </Link>
        </Button>
        <div>
          <h1 className="text-2xl font-semibold">{lead.full_name}</h1>
          <p className="text-sm text-muted-foreground">
            {lead.email ?? "—"} · {lead.phone ?? "—"}
          </p>
        </div>
        <div className="ml-auto flex items-center gap-2">
          <PriorityBadge priority={lead.priority} />
          <Button variant="outline" size="sm" disabled={qualifying} onClick={() => void requalify()}>
            <Sparkles className="mr-1 h-4 w-4" />
            {qualifying ? "Qualifying…" : "Re-qualify"}
          </Button>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Enquiry</CardTitle>
            <CardDescription>
              Captured {new Date(lead.created_at).toLocaleString()} from {lead.source}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="whitespace-pre-wrap text-sm leading-relaxed">{lead.enquiry_text}</p>
            <div className="grid gap-3 sm:grid-cols-2">
              <Field label="Status">
                <select
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 text-sm"
                  value={lead.status}
                  disabled={saving}
                  onChange={(e) => void savePatch({ status: e.target.value as LeadStatus })}
                >
                  {(
                    ["new", "qualifying", "qualified", "contacted", "engaged", "won", "lost", "spam", "opted_out"] as const
                  ).map((s) => (
                    <option key={s} value={s}>
                      {s.replace("_", " ")}
                    </option>
                  ))}
                </select>
              </Field>
              <Field label="Priority">
                <select
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 text-sm"
                  value={lead.priority}
                  disabled={saving}
                  onChange={(e) => void savePatch({ priority: e.target.value as LeadPriority })}
                >
                  {(["hot", "warm", "cold", "unqualified"] as const).map((p) => (
                    <option key={p} value={p}>
                      {p}
                    </option>
                  ))}
                </select>
              </Field>
            </div>
            <label className="flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                checked={lead.follow_up_paused}
                onChange={(e) => void savePatch({ follow_up_paused: e.target.checked })}
              />
              Pause automated follow-ups
            </label>
          </CardContent>
        </Card>

        <div className="space-y-6">
          <QualificationCard qualification={qualification} />
          <Card>
            <CardHeader>
              <CardTitle>Consent</CardTitle>
              <CardDescription>Outbound channels</CardDescription>
            </CardHeader>
            <CardContent className="space-y-2 text-sm">
              <p>Marketing: {lead.consent_marketing ? "Yes" : "No"}</p>
              <p>Email: {lead.consent_channel_email ? "Yes" : "No"}</p>
              <p>WhatsApp: {lead.consent_channel_whatsapp ? "Yes" : "No"}</p>
            </CardContent>
          </Card>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Communication history</CardTitle>
          <CardDescription>Email and automation messages</CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          {comms.length === 0 ? (
            <p className="text-sm text-muted-foreground">No messages yet</p>
          ) : (
            comms.map((c) => (
              <div key={c.id} className="rounded-md border border-border p-3 text-sm">
                <div className="flex justify-between gap-2">
                  <span className="font-medium capitalize">
                    {c.direction} · {c.status.replace("_", " ")}
                  </span>
                  <time className="text-xs text-muted-foreground">{new Date(c.created_at).toLocaleString()}</time>
                </div>
                {c.subject ? <p className="mt-1 text-xs text-muted-foreground">{c.subject}</p> : null}
                <p className="mt-2 line-clamp-3 whitespace-pre-wrap text-xs">{c.body}</p>
              </div>
            ))
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Internal note</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-3 sm:flex-row">
          <Input value={note} onChange={(e) => setNote(e.target.value)} placeholder="Add context for your team…" />
          <Button onClick={() => void addNote()} disabled={!note.trim()}>
            Save note
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}

function QualificationCard({ qualification }: { qualification: LeadQualification | null }) {
  if (!qualification) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>AI qualification</CardTitle>
          <CardDescription>Run qualification to generate a lead summary</CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">No qualification on file yet.</p>
        </CardContent>
      </Card>
    );
  }

  const req = qualification.requirements;
  const reqEntries = Object.entries(req);

  return (
    <Card>
      <CardHeader>
        <CardTitle>AI qualification</CardTitle>
        <CardDescription>
          {qualification.model} · {new Date(qualification.created_at).toLocaleString()}
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-3 text-sm">
        <p className="leading-relaxed">{qualification.summary}</p>
        <DetailRow label="Category" value={qualification.category.replace("_", " ")} />
        <DetailRow label="Intent score" value={`${qualification.intent_score}/100`} />
        <DetailRow label="Next action" value={qualification.recommended_action} />
        {reqEntries.length > 0 ? (
          <div className="space-y-1 border-t border-border pt-3">
            <p className="text-xs font-medium uppercase text-muted-foreground">Extracted requirements</p>
            {reqEntries.map(([key, val]) => (
              <DetailRow key={key} label={key.replace("_", " ")} value={String(val)} />
            ))}
          </div>
        ) : null}
      </CardContent>
    </Card>
  );
}

function DetailRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between gap-4">
      <span className="text-muted-foreground capitalize">{label}</span>
      <span className="text-right font-medium capitalize">{value}</span>
    </div>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="space-y-2">
      <label className="text-sm font-medium">{label}</label>
      {children}
    </div>
  );
}