import { Suspense } from "react";
import Link from "next/link";
import { AuthShell } from "@/components/auth/auth-shell";
import { AuthForm } from "@/components/auth/auth-form";

export default function Login() {
  return <AuthShell eyebrow="Welcome back" title="Sign in to Readout" description="Return to the questions, trends, and decisions in your workspace." footer={<>New to Readout? <Link className="font-semibold text-[var(--marketing-mint)]" href="/signup">Create an account</Link></>}><Suspense fallback={<p>Loading secure sign in…</p>}><AuthForm mode="login"/></Suspense></AuthShell>;
}
