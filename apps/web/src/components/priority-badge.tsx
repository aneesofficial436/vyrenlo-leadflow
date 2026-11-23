import type { LeadPriority } from "@/lib/types";
import { Badge } from "@/components/ui/badge";

const map: Record<LeadPriority, "hot" | "warm" | "cold" | "secondary"> = {
  hot: "hot",
  warm: "warm",
  cold: "cold",
  unqualified: "secondary",
};

export function PriorityBadge({ priority }: { priority: LeadPriority }) {
  return (
    <Badge variant={map[priority]} className="capitalize">
      {priority}
    </Badge>
  );
}