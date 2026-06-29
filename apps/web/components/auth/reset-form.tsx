"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { createClient } from "@/lib/supabase/client";
import { Button } from "@/components/ui/button";
import { FormField } from "@/components/ui/form-field";
import { PasswordInput } from "./password-input";
export function ResetForm() {
  const router = useRouter(),
    [password, setPassword] = useState(""),
    [confirm, setConfirm] = useState(""),
    [valid, setValid] = useState<boolean | null>(null),
    [pending, setPending] = useState(false),
    [error, setError] = useState("");
  useEffect(() => {
    Promise.resolve()
      .then(() => createClient().auth.getSession())
      .then(({ data }) => setValid(!!data.session))
      .catch(() => setValid(false));
  }, []);
  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (password.length < 8) return setError("Use at least 8 characters.");
    if (password !== confirm) return setError("Passwords do not match.");
    setPending(true);
    try {
      const { error } = await createClient().auth.updateUser({ password });
      if (error) {
        setError(
          "We could not update the password. Request a fresh link and try again.",
        );
        setPending(false);
        return;
      }
      await createClient().auth.signOut();
      router.replace("/login?reset=success");
    } catch {
      setError(
        "We could not update the password. Request a fresh link and try again.",
      );
      setPending(false);
      return;
    }
  }
  if (valid === null)
    return (
      <p role="status" className="animate-pulse">
        Verifying your reset link…
      </p>
    );
  if (!valid)
    return (
      <div role="alert">
        <h2 className="font-bold text-[var(--danger)]">
          This reset link is invalid or expired.
        </h2>
        <p className="my-3 text-sm text-[var(--ink-secondary)]">
          Request a fresh link to continue safely.
        </p>
        <Button onClick={() => router.replace("/forgot-password")}>
          Request another link
        </Button>
      </div>
    );
  return (
    <form onSubmit={submit} className="grid gap-5">
      {error && (
        <p role="alert" className="text-sm text-[var(--danger)]">
          {error}
        </p>
      )}
      <FormField label="New password">
        <PasswordInput
          required
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          autoComplete="new-password"
        />
      </FormField>
      <FormField label="Confirm new password">
        <PasswordInput
          required
          value={confirm}
          onChange={(e) => setConfirm(e.target.value)}
          autoComplete="new-password"
        />
      </FormField>
      <Button disabled={pending}>
        {pending ? "Updating…" : "Update password"}
      </Button>
    </form>
  );
}
