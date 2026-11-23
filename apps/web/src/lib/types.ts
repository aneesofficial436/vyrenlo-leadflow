export type LeadStatus =
  | "new"
  | "qualifying"
  | "qualified"
  | "contacted"
  | "engaged"
  | "won"
  | "lost"
  | "spam"
  | "opted_out";

export type LeadPriority = "hot" | "warm" | "cold" | "unqualified";

export interface Lead {
  id: string;
  tenant_id: string;
  source: string;
  source_detail: Record<string, unknown>;
  full_name: string;
  email: string | null;
  phone: string | null;
  enquiry_text: string;
  status: LeadStatus;
  priority: LeadPriority;
  assigned_user_id: string | null;
  consent_marketing: boolean;
  consent_channel_email: boolean;
  consent_channel_whatsapp: boolean;
  last_interaction_at: string | null;
  next_follow_up_at: string | null;
  follow_up_paused: boolean;
  metadata: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface LeadListResponse {
  items: Lead[];
  total: number;
  page: number;
  page_size: number;
}

export interface AnalyticsOverview {
  total_leads: number;
  new_today: number;
  hot: number;
  warm: number;
  cold: number;
  follow_up_pending: number;
  conversion_rate: number;
}

export interface SourceBreakdownItem {
  source: string;
  count: number;
}

export interface ActivityItem {
  id: number;
  event_type: string;
  lead_id: string | null;
  created_at: string;
  payload: Record<string, unknown>;
}

export interface LeadQualification {
  id: string;
  lead_id: string;
  model: string;
  prompt_version: string;
  summary: string;
  category: string;
  intent_score: number;
  priority: LeadPriority;
  requirements: Record<string, unknown>;
  recommended_action: string;
  created_at: string;
}

export interface LeadDetail {
  lead: Lead;
  latest_qualification: LeadQualification | null;
}

export interface Communication {
  id: string;
  lead_id: string;
  channel: string;
  direction: "inbound" | "outbound";
  subject: string | null;
  body: string;
  status: string;
  ai_generated: boolean;
  sent_at: string | null;
  created_at: string;
}

export interface UserProfile {
  id: string;
  tenant_id: string;
  email: string;
  full_name: string;
  role: string;
}