"use client";

import { useCallback, useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { Lead, LeadPriority, LeadStatus } from "@/lib/types";
import { LeadsTable } from "@/components/leads-table";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

const statuses: (LeadStatus | "")[] = [
  "",
  "new",
  "qualified",
  "contacted",
  "engaged",
  "won",
  "lost",
];
const priorities: (LeadPriority | "")[] = ["", "hot", "warm", "cold", "unqualified"];

export default function LeadsPage() {
  const [items, setItems] = useState<Lead[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(15);
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState<LeadStatus | "">("");
  const [priority, setPriority] = useState<LeadPriority | "">("");
  const [debouncedSearch, setDebouncedSearch] = useState("");

  useEffect(() => {
    const t = setTimeout(() => setDebouncedSearch(search), 300);
    return () => clearTimeout(t);
  }, [search]);

  const load = useCallback(() => {
    const params = new URLSearchParams({
      page: String(page),
      page_size: String(pageSize),
      sort: "created_at_desc",
    });
    if (debouncedSearch) params.set("search", debouncedSearch);
    if (status) params.set("status", status);
    if (priority) params.set("priority", priority);
    void api.leads(params).then((res) => {
      setItems(res.items);
      setTotal(res.total);
    });
  }, [page, pageSize, debouncedSearch, status, priority]);

  useEffect(() => {
    load();
  }, [load]);

  const totalPages = Math.max(1, Math.ceil(total / pageSize));

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-semibold tracking-tight">Leads</h1>
        <p className="text-muted-foreground">Search, filter, and open lead records</p>
      </div>

      <div className="flex flex-col gap-3 lg:flex-row lg:items-end">
        <div className="flex-1 space-y-2">
          <label className="text-sm font-medium">Search</label>
          <Input placeholder="Name, email, phone, enquiry…" value={search} onChange={(e) => setSearch(e.target.value)} />
        </div>
        <div className="space-y-2">
          <label className="text-sm font-medium">Status</label>
          <select
            className="flex h-10 w-full rounded-md border border-input bg-background px-3 text-sm lg:w-44"
            value={status}
            onChange={(e) => {
              setPage(1);
              setStatus(e.target.value as LeadStatus | "");
            }}
          >
            {statuses.map((s) => (
              <option key={s || "all"} value={s}>
                {s ? s.replace("_", " ") : "All statuses"}
              </option>
            ))}
          </select>
        </div>
        <div className="space-y-2">
          <label className="text-sm font-medium">Priority</label>
          <select
            className="flex h-10 w-full rounded-md border border-input bg-background px-3 text-sm lg:w-40"
            value={priority}
            onChange={(e) => {
              setPage(1);
              setPriority(e.target.value as LeadPriority | "");
            }}
          >
            {priorities.map((p) => (
              <option key={p || "all"} value={p}>
                {p || "All priorities"}
              </option>
            ))}
          </select>
        </div>
      </div>

      <LeadsTable data={items} />

      <div className="flex items-center justify-between text-sm text-muted-foreground">
        <span>
          {total} lead{total === 1 ? "" : "s"}
        </span>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>
            Previous
          </Button>
          <span>
            Page {page} / {totalPages}
          </span>
          <Button variant="outline" size="sm" disabled={page >= totalPages} onClick={() => setPage((p) => p + 1)}>
            Next
          </Button>
        </div>
      </div>
    </div>
  );
}