"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Flame, Inbox, Sparkles, Timer } from "lucide-react";
import { api } from "@/lib/api";
import type { ActivityItem, AnalyticsOverview, SourceBreakdownItem } from "@/lib/types";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

function KpiCard({
  title,
  value,
  hint,
  icon: Icon,
}: {
  title: string;
  value: string | number;
  hint?: string;
  icon: React.ComponentType<{ className?: string }>;
}) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">{title}</CardTitle>
        <Icon className="h-4 w-4 text-muted-foreground" />
      </CardHeader>
      <CardContent>
        <div className="text-3xl font-semibold tracking-tight">{value}</div>
        {hint ? <p className="mt-1 text-xs text-muted-foreground">{hint}</p> : null}
      </CardContent>
    </Card>
  );
}

export default function DashboardPage() {
  const [overview, setOverview] = useState<AnalyticsOverview | null>(null);
  const [sources, setSources] = useState<SourceBreakdownItem[]>([]);
  const [activity, setActivity] = useState<ActivityItem[]>([]);

  useEffect(() => {
    void Promise.all([api.overview(), api.sources(), api.activity()]).then(([o, s, a]) => {
      setOverview(o);
      setSources(s);
      setActivity(a);
    });
  }, []);

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-semibold tracking-tight">Pipeline overview</h1>
        <p className="text-muted-foreground">Real-time lead intelligence and follow-up health</p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <KpiCard title="Total leads" value={overview?.total_leads ?? "—"} icon={Inbox} />
        <KpiCard title="New today" value={overview?.new_today ?? "—"} icon={Sparkles} hint="Since midnight UTC" />
        <KpiCard
          title="Hot leads"
          value={overview?.hot ?? "—"}
          icon={Flame}
          hint={`${overview?.warm ?? 0} warm · ${overview?.cold ?? 0} cold`}
        />
        <KpiCard
          title="Follow-ups due"
          value={overview?.follow_up_pending ?? "—"}
          icon={Timer}
          hint={`${overview?.conversion_rate ?? 0}% win rate`}
        />
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Lead sources</CardTitle>
            <CardDescription>Where enquiries are coming from</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {sources.length === 0 ? (
              <p className="text-sm text-muted-foreground">No source data yet</p>
            ) : (
              sources.map((row) => (
                <div key={row.source} className="flex items-center justify-between text-sm">
                  <span className="capitalize text-foreground">{row.source.replace("_", " ")}</span>
                  <span className="font-medium">{row.count}</span>
                </div>
              ))
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Recent activity</CardTitle>
            <CardDescription>Automation and team events</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {activity.length === 0 ? (
              <p className="text-sm text-muted-foreground">No events yet</p>
            ) : (
              activity.map((item) => (
                <div key={item.id} className="flex items-start justify-between gap-4 text-sm">
                  <div>
                    <p className="font-medium">{item.event_type.replace(/\./g, " · ")}</p>
                    {item.lead_id ? (
                      <Link href={`/leads/${item.lead_id}`} className="text-xs text-primary hover:underline">
                        View lead
                      </Link>
                    ) : null}
                  </div>
                  <time className="shrink-0 text-xs text-muted-foreground">
                    {new Date(item.created_at).toLocaleString()}
                  </time>
                </div>
              ))
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}