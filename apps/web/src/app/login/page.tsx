"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { login } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";

export default function LoginPage() {
  const router = useRouter();
  const [tenant_slug, setTenantSlug] = useState("demo-realty");
  const [email, setEmail] = useState("owner@demo.local");
  const [password, setPassword] = useState("DemoPass123!");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      await login(tenant_slug, email, password);
      router.push("/dashboard");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-background via-background to-primary/5 p-4">
      <Card className="w-full max-w-md border-border/80 shadow-lg">
        <CardHeader>
          <p className="text-xs font-semibold uppercase tracking-widest text-muted-foreground">Vyrenlo</p>
          <CardTitle>Sign in to LeadFlow</CardTitle>
          <CardDescription>AI lead management and follow-up automation</CardDescription>
        </CardHeader>
        <CardContent>
          <form className="space-y-4" onSubmit={onSubmit}>
            <div className="space-y-2">
              <label className="text-sm font-medium">Tenant slug</label>
              <Input value={tenant_slug} onChange={(e) => setTenantSlug(e.target.value)} required />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">Email</label>
              <Input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">Password</label>
              <Input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required />
            </div>
            {error ? <p className="text-sm text-red-600 dark:text-red-400">{error}</p> : null}
            <Button className="w-full" disabled={loading} type="submit">
              {loading ? "Signing in…" : "Sign in"}
            </Button>
          </form>
          <p className="mt-4 text-center text-xs text-muted-foreground">
            Demo: <code>demo-realty</code> / <code>owner@demo.local</code>
          </p>
          <p className="mt-2 text-center text-xs text-muted-foreground">
            <Link href="https://vyrenlo.com" className="underline-offset-4 hover:underline">
              Vyrenlo automation agency
            </Link>
          </p>
        </CardContent>
      </Card>
    </div>
  );
}