"use client";

import type { FormEvent } from "react";
import { useState } from "react";
import Link from "next/link";
import { createClient } from "@/lib/supabase/client";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { FormField } from "@/components/ui/form-field";

export function ForgotForm() {
  const [email, setEmail] = useState("");
  const [pending, setPending] = useState(false);
  const [sent, setSent] = useState(false);
  const [error, setError] = useState("");

  async function submit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setPending(true);
    setError("");

    try {
      const { error } = await createClient().auth.resetPasswordForEmail(email, {
        redirectTo: `${location.origin}/auth/callback?next=/reset-password`,
      });

      if (error) throw error;
      setSent(true);
    } catch {
      setError("We could not send a reset email right now. Please try again shortly.");
    } finally {
      setPending(false);
    }
  }

  if (sent) {
    return (
      <div
        role="status"
        className="rounded-xl border border-[rgba(168,255,120,.2)] bg-[color-mix(in_srgb,var(--success)_10%,white)] p-5 text-[var(--marketing-ink)] shadow-[0_18px_40px_rgba(0,0,0,.12)]"
      >
        <p className="text-[9px] font-extrabold uppercase tracking-[.18em] text-[var(--marketing-violet)]">
          Account recovery
        </p>
        <h2 className="mt-3 text-lg font-bold tracking-[-.04em] text-[var(--marketing-ink)]">
          Check your inbox
        </h2>
        <p className="mt-2 text-sm leading-6 text-[rgba(9,11,19,.72)]">
          If an account exists for {email}, a secure reset link is on its way.
        </p>
        <Link href="/login" className="mt-4 inline-flex font-semibold text-[var(--marketing-violet)]">
          Back to sign in
        </Link>
      </div>
    );
  }

  return (
    <form onSubmit={submit} className="grid gap-5">
      {error && (
        <p role="alert" className="text-sm text-[var(--danger)]">
          {error}
        </p>
      )}

      <FormField label="Account email">
        <Input
          type="email"
          required
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          autoComplete="email"
        />
      </FormField>

      <Button disabled={pending}>{pending ? "Sending..." : "Send reset link"}</Button>

      <Link href="/login" className="text-center text-sm font-semibold text-[var(--accent)]">
        Back to sign in
      </Link>
    </form>
  );
}
