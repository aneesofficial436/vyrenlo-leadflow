import {
  clearSession,
  getAccessToken,
  getRefreshToken,
  setSession,
  getTenantSlug,
} from "@/lib/auth";
import type {
  ActivityItem,
  AnalyticsOverview,
  Lead,
  LeadDetail,
  LeadListResponse,
  LeadQualification,
  Communication,
  SourceBreakdownItem,
  UserProfile,
} from "@/lib/types";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function refreshIfNeeded(res: Response): Promise<boolean> {
  if (res.status !== 401) return false;
  const refresh = getRefreshToken();
  const tenant = getTenantSlug();
  if (!refresh) return false;

  const refreshRes = await fetch(`${API_URL}/v1/auth/refresh`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh_token: refresh }),
  });
  if (!refreshRes.ok) {
    clearSession();
    return false;
  }
  const tokens = await refreshRes.json();
  if (tenant) {
    setSession({
      access_token: tokens.access_token,
      refresh_token: tokens.refresh_token,
      tenant_slug: tenant,
    });
  }
  return true;
}

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const token = getAccessToken();
  const headers = new Headers(init?.headers);
  headers.set("Content-Type", "application/json");
  if (token) headers.set("Authorization", `Bearer ${token}`);

  let res = await fetch(`${API_URL}${path}`, { ...init, headers });
  if (res.status === 401 && (await refreshIfNeeded(res))) {
    headers.set("Authorization", `Bearer ${getAccessToken()}`);
    res = await fetch(`${API_URL}${path}`, { ...init, headers });
  }

  if (res.status === 204) return undefined as T;
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new ApiError(res.status, body.detail ?? res.statusText);
  }
  return res.json() as Promise<T>;
}

export async function login(tenant_slug: string, email: string, password: string) {
  const res = await fetch(`${API_URL}/v1/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ tenant_slug, email, password }),
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new ApiError(res.status, body.detail ?? "Login failed");
  }
  const data = await res.json();
  setSession({
    access_token: data.access_token,
    refresh_token: data.refresh_token,
    tenant_slug,
  });
  return data;
}

export function logout() {
  const refresh = getRefreshToken();
  clearSession();
  if (refresh) {
    void fetch(`${API_URL}/v1/auth/logout`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: refresh }),
    });
  }
}

export const api = {
  me: () => apiFetch<UserProfile>("/v1/auth/me"),
  overview: () => apiFetch<AnalyticsOverview>("/v1/analytics/overview"),
  sources: () => apiFetch<SourceBreakdownItem[]>("/v1/analytics/sources"),
  activity: () => apiFetch<ActivityItem[]>("/v1/analytics/activity?limit=12"),
  leads: (params: URLSearchParams) => apiFetch<LeadListResponse>(`/v1/leads?${params}`),
  lead: (id: string) => apiFetch<LeadDetail>(`/v1/leads/${id}`),
  qualifyLead: (id: string) =>
    apiFetch<LeadQualification>(`/v1/leads/${id}/qualify`, { method: "POST" }),
  patchLead: (id: string, body: Record<string, unknown>) =>
    apiFetch<Lead>(`/v1/leads/${id}`, { method: "PATCH", body: JSON.stringify(body) }),
  addNote: (id: string, body: string) =>
    apiFetch(`/v1/leads/${id}/notes`, {
      method: "POST",
      body: JSON.stringify({ body }),
    }),
  pendingApprovals: () => apiFetch<Communication[]>("/v1/communications/pending-approval"),
  leadCommunications: (leadId: string) => apiFetch<Communication[]>(`/v1/communications/leads/${leadId}`),
  approveCommunication: (id: string) => apiFetch<Communication>(`/v1/communications/${id}/approve`, { method: "POST" }),
  sendCommunication: (id: string) => apiFetch<Communication>(`/v1/communications/${id}/send`, { method: "POST" }),
};