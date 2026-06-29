"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { navItems } from "./nav-items";

export function MobileNav() {
  const path = usePathname();
  return <nav aria-label="Mobile navigation" className="dashboard-mobile-nav fixed left-3 right-3 z-40 flex justify-around p-1.5 md:hidden">{navItems.slice(0, 5).map(({href,label,icon:Icon}) => <Link key={href} href={href} aria-label={label} aria-current={path === href ? "page" : undefined} className={`dashboard-mobile-item ${path === href ? "is-active" : ""}`}><Icon aria-hidden="true" size={18}/><span>{label === "Data" ? "Sources" : label}</span></Link>)}</nav>;
}
