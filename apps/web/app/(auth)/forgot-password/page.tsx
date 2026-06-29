import Link from"next/link";import{AuthShell}from"@/components/auth/auth-shell";import{ForgotForm}from"@/components/auth/forgot-form";
export default function Forgot(){return <AuthShell eyebrow="Account recovery" title="Reset your password" description="We’ll email you a time-limited link to choose a new password." footer={<Link href="/login">Back to sign in</Link>}><ForgotForm/></AuthShell>}
