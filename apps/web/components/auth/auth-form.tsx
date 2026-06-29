"use client";

import { useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { createClient } from "@/lib/supabase/client";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { FormField } from "@/components/ui/form-field";
import { PasswordInput } from "./password-input";

const baseSchema = z.object({
  email: z.email("Enter a valid email address"),
  password: z.string().min(8, "Use at least 8 characters"),
});
const signupSchema = baseSchema.extend({
  confirmPassword: z.string().min(1, "Confirm your password"),
}).refine((values) => values.password === values.confirmPassword, {
  message: "Passwords do not match",
  path: ["confirmPassword"],
});
type Values = z.infer<typeof baseSchema> & { confirmPassword?: string };

export function AuthForm({ mode }: { mode: "login" | "signup" }) {
  const router = useRouter();
  const params = useSearchParams();
  const [serverError, setServerError] = useState("");
  const { register, handleSubmit, setError, formState: { errors, isSubmitting } } = useForm<Values>();

  async function submit(raw: Values) {
    const parsed = mode === "signup" ? signupSchema.safeParse(raw) : baseSchema.safeParse(raw);
    if (!parsed.success) {
      for (const issue of parsed.error.issues) setError(issue.path[0] as keyof Values, { message: issue.message });
      return;
    }
    setServerError("");
    const credentials = { email: parsed.data.email, password: parsed.data.password };
    try {
      const supabase = createClient();
      if (mode === "login") {
        const { error } = await supabase.auth.signInWithPassword(credentials);
        if (error) throw error;
        const next = params.get("next");
        router.replace(next?.startsWith("/") ? next : "/dashboard/overview");
        router.refresh();
      } else {
        const { data, error } = await supabase.auth.signUp({ ...credentials, options: { emailRedirectTo: `${location.origin}/auth/callback?next=/onboarding/connect-data` } });
        if (error) throw error;
        router.replace(data.session ? "/onboarding/connect-data" : `/verify-email?email=${encodeURIComponent(credentials.email)}`);
      }
    } catch {
      setServerError(mode === "login" ? "We could not sign you in. Check your email and password, then try again." : "We could not create the account. Check your details and try again.");
    }
  }

  return (
    <form className="auth-form grid gap-5" onSubmit={handleSubmit(submit)} noValidate>
      {params.get("reason") === "session-expired" && <p role="status" className="auth-notice">Your session expired. Sign in again to continue.</p>}
      {params.get("error") === "callback" && <p role="alert" className="auth-notice auth-notice--error">That sign-in link is invalid or expired. Please try again.</p>}
      {params.get("reset") === "success" && <p role="status" className="auth-notice">Password updated. You can sign in now.</p>}
      {serverError && <p role="alert" className="auth-notice auth-notice--error">{serverError}</p>}
      <FormField label="Work email" error={errors.email?.message}><Input type="email" autoComplete="email" disabled={isSubmitting} aria-invalid={Boolean(errors.email)} {...register("email")}/></FormField>
      <FormField label="Password" error={errors.password?.message}><PasswordInput autoComplete={mode === "login" ? "current-password" : "new-password"} disabled={isSubmitting} aria-invalid={Boolean(errors.password)} {...register("password")}/></FormField>
      {mode === "signup" && <FormField label="Confirm password" error={errors.confirmPassword?.message}><PasswordInput autoComplete="new-password" disabled={isSubmitting} aria-invalid={Boolean(errors.confirmPassword)} {...register("confirmPassword")}/></FormField>}
      {mode === "login" && <Link href="/forgot-password" className="-mt-2 justify-self-end text-sm font-semibold text-[var(--marketing-mint)]">Forgot password?</Link>}
      <Button className="mt-1 min-h-12" disabled={isSubmitting} type="submit">{isSubmitting ? "Working…" : mode === "login" ? "Sign in" : "Create account"}</Button>
    </form>
  );
}
