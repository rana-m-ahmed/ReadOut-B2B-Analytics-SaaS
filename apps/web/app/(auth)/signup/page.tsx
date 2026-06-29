import { Suspense } from "react";
import Link from "next/link";
import { AuthShell } from "@/components/auth/auth-shell";
import { AuthForm } from "@/components/auth/auth-form";

export default function Signup() {
  return <AuthShell eyebrow="Start clearly" title="Create your account" description="Bring a CSV or start with demo data. Your first answer is minutes away." footer={<>Already have an account? <Link className="font-semibold text-[var(--marketing-mint)]" href="/login">Sign in</Link></>}><Suspense fallback={<p>Loading secure signup…</p>}><AuthForm mode="signup"/></Suspense></AuthShell>;
}
