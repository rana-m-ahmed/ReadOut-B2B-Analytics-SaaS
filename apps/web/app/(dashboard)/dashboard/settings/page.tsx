"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { createClient } from "@/lib/supabase/client";
import { PageHeader } from "@/components/dashboard/page-header";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { FormField } from "@/components/ui/form-field";
import { Input } from "@/components/ui/input";
import { Badge, Skeleton } from "@/components/ui/states";
export default function Settings() {
  const router = useRouter(),
    [loading, setLoading] = useState(true),
    [email, setEmail] = useState(""),
    [anon, setAnon] = useState(false),
    [upgradeEmail, setUpgradeEmail] = useState(""),
    [password, setPassword] = useState(""),
    [pending, setPending] = useState(false),
    [message, setMessage] = useState("");
  useEffect(() => {
    createClient()
      .auth.getUser()
      .then(({ data }) => {
        setEmail(data.user?.email ?? "Private anonymous session");
        setAnon(!!data.user?.is_anonymous);
        setLoading(false);
      });
  }, []);
  async function logout() {
    setPending(true);
    await createClient().auth.signOut();
    router.replace("/login");
    router.refresh();
  }
  async function upgrade(e: React.FormEvent) {
    e.preventDefault();
    if (password.length < 8)
      return setMessage("Use at least 8 characters for your new password.");
    setPending(true);
    setMessage("");
    const { error } = await createClient().auth.updateUser(
      { email: upgradeEmail, password },
      {
        emailRedirectTo: `${location.origin}/auth/callback?next=/dashboard/settings`,
      },
    );
    setPending(false);
    if (error)
      return setMessage(
        "We could not upgrade this session. Check the email and try again.",
      );
    setMessage(
      "Check your inbox to confirm the email and finish securing this workspace.",
    );
  }
  return (
    <div className="mx-auto max-w-5xl">
      <PageHeader
        eyebrow="Workspace preferences"
        title="Account and session"
        description="Review your identity, recovery options, and the limits of this project workspace."
      />
      <div className="grid gap-5">
        {loading ? (
          <Skeleton className="h-32" />
        ) : (
          <Card className="signal-card p-6 md:p-7">
            <div className="flex flex-wrap items-center justify-between gap-4">
              <div>
                <p className="text-sm text-[var(--ink-secondary)]">
                  Signed in as
                </p>
                <p className="mt-1 font-bold">{email}</p>
              </div>
              <Badge tone={anon ? "warning" : "success"}>
                {anon ? "Anonymous demo" : "Verified account"}
              </Badge>
            </div>
          </Card>
        )}
        {anon && (
          <Card className="signal-card border-[color-mix(in_srgb,var(--warning)_45%,transparent)] p-6 md:p-7">
            <h2 className="text-xl font-bold">Secure this workspace</h2>
            <p className="mt-2 text-sm leading-6 text-[var(--ink-secondary)]">
              Add an email and password to convert this anonymous Supabase
              identity without starting a separate account.
            </p>
            <form className="mt-5 grid gap-4 sm:grid-cols-2" onSubmit={upgrade}>
              <FormField label="Email">
                <Input
                  required
                  type="email"
                  autoComplete="email"
                  value={upgradeEmail}
                  onChange={(e) => setUpgradeEmail(e.target.value)}
                />
              </FormField>
              <FormField label="New password">
                <Input
                  required
                  type="password"
                  minLength={8}
                  autoComplete="new-password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                />
              </FormField>
              <Button
                className="sm:col-span-2 sm:justify-self-start"
                disabled={pending}
              >
                Secure workspace
              </Button>
            </form>
            {message && (
              <p role="status" className="mt-4 text-sm font-semibold">
                {message}
              </p>
            )}
          </Card>
        )}
        <Card className="signal-card p-6 md:p-7">
          <h2 className="text-lg font-bold">Password and recovery</h2>
          <p className="my-3 text-sm text-[var(--ink-secondary)]">
            Account holders can request a secure password-reset link. Anonymous
            sessions must be upgraded first.
          </p>
          <Link
            className="font-semibold text-[var(--accent)]"
            href="/forgot-password"
          >
            Reset account password →
          </Link>
        </Card>
        <Card className="signal-card p-6 md:p-7">
          <h2 className="text-lg font-bold">Current project limits</h2>
          <ul className="mt-3 list-disc space-y-2 pl-5 text-sm text-[var(--ink-secondary)]">
            <li>
              CSV uploads default to 25 MB, matching the backend configuration.
            </li>
            <li>
              Anonymous workspaces expire after the configured retention window.
            </li>
            <li>
              AI availability depends on the connected model provider and may
              briefly degrade.
            </li>
          </ul>
          <div className="mt-5 flex gap-4 text-sm font-semibold">
            <Link href="/privacy">Privacy</Link>
            <Link href="/terms">Terms</Link>
          </div>
        </Card>
        <Card className="signal-card p-6 md:p-7">
          <h2 className="text-lg font-bold">Session</h2>
          <p className="my-3 text-sm text-[var(--ink-secondary)]">
            Signing out ends this browser session. Unsecured anonymous work may
            not be recoverable.
          </p>
          <Button variant="secondary" disabled={pending} onClick={logout}>
            Sign out
          </Button>
        </Card>
      </div>
    </div>
  );
}
