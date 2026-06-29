"use client";
import { forwardRef, type ButtonHTMLAttributes } from "react";
import { cn } from "@/lib/utils";
type Props=ButtonHTMLAttributes<HTMLButtonElement>&{variant?:"primary"|"secondary"|"ghost"|"danger";size?:"sm"|"md"|"icon"};
export const Button=forwardRef<HTMLButtonElement,Props>(({className,variant="primary",size="md",...props},ref)=><button ref={ref} className={cn("inline-flex min-h-11 items-center justify-center gap-2 rounded-[var(--radius-control)] px-5 font-semibold transition duration-200 motion-reduce:transform-none active:scale-[.97] disabled:cursor-not-allowed disabled:opacity-55",variant==="primary"&&"bg-gradient-to-br from-[var(--accent)] to-[var(--marketing-violet)] text-white shadow-[0_12px_30px_rgba(74,89,220,.3)] hover:-translate-y-0.5 hover:brightness-110",variant==="secondary"&&"border border-[var(--hairline)] bg-[var(--surface-subtle)] hover:border-[color-mix(in_srgb,var(--accent)_45%,transparent)]",variant==="ghost"&&"hover:bg-[var(--surface-subtle)]",variant==="danger"&&"bg-[var(--danger)] text-white",size==="sm"&&"min-h-9 px-3 text-sm",size==="icon"&&"h-11 w-11 p-0",className)} {...props}/>);
Button.displayName="Button";
