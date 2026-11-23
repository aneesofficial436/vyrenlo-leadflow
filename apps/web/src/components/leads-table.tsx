"use client";

import Link from "next/link";
import {
  flexRender,
  getCoreRowModel,
  useReactTable,
  type ColumnDef,
} from "@tanstack/react-table";
import type { Lead } from "@/lib/types";
import { PriorityBadge } from "@/components/priority-badge";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

const columns: ColumnDef<Lead>[] = [
  {
    accessorKey: "full_name",
    header: "Lead",
    cell: ({ row }) => (
      <div>
        <Link href={`/leads/${row.original.id}`} className="font-medium hover:underline">
          {row.original.full_name}
        </Link>
        <p className="text-xs text-muted-foreground">{row.original.email ?? row.original.phone ?? "—"}</p>
      </div>
    ),
  },
  { accessorKey: "source", header: "Source", cell: ({ row }) => <span className="capitalize">{row.original.source}</span> },
  {
    accessorKey: "priority",
    header: "Priority",
    cell: ({ row }) => <PriorityBadge priority={row.original.priority} />,
  },
  {
    accessorKey: "status",
    header: "Status",
    cell: ({ row }) => (
      <Badge variant="outline" className="capitalize">
        {row.original.status.replace("_", " ")}
      </Badge>
    ),
  },
  {
    accessorKey: "last_interaction_at",
    header: "Last touch",
    cell: ({ row }) =>
      row.original.last_interaction_at
        ? new Date(row.original.last_interaction_at).toLocaleDateString()
        : "—",
  },
  {
    accessorKey: "next_follow_up_at",
    header: "Next follow-up",
    cell: ({ row }) =>
      row.original.next_follow_up_at ? new Date(row.original.next_follow_up_at).toLocaleDateString() : "—",
  },
];

export function LeadsTable({ data }: { data: Lead[] }) {
  const table = useReactTable({ data, columns, getCoreRowModel: getCoreRowModel() });

  return (
    <div className="overflow-hidden rounded-lg border border-border">
      <table className="w-full text-sm">
        <thead className="bg-muted/50">
          {table.getHeaderGroups().map((hg) => (
            <tr key={hg.id} className="border-b border-border text-left">
              {hg.headers.map((header) => (
                <th key={header.id} className="px-4 py-3 font-medium text-muted-foreground">
                  {header.isPlaceholder ? null : flexRender(header.column.columnDef.header, header.getContext())}
                </th>
              ))}
            </tr>
          ))}
        </thead>
        <tbody>
          {table.getRowModel().rows.length === 0 ? (
            <tr>
              <td colSpan={columns.length} className="px-4 py-10 text-center text-muted-foreground">
                No leads match your filters
              </td>
            </tr>
          ) : (
            table.getRowModel().rows.map((row) => (
              <tr key={row.id} className={cn("border-b border-border/70 hover:bg-muted/30")}>
                {row.getVisibleCells().map((cell) => (
                  <td key={cell.id} className="px-4 py-3 align-top">
                    {flexRender(cell.column.columnDef.cell, cell.getContext())}
                  </td>
                ))}
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}