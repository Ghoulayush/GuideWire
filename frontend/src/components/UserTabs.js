"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const tabs = [
  { href: "/home", label: "Home" },
  { href: "/dashboard", label: "Dashboard" },
  { href: "/simulation", label: "Simulation" },
  { href: "/subscription", label: "Subscription" },
];

export default function UserTabs() {
  const pathname = usePathname();

  return (
    <nav className="user-tabs" aria-label="User workspace tabs">
      {tabs.map((tab) => {
        const active = pathname === tab.href;
        return (
          <Link
            key={tab.href}
            href={tab.href}
            className={active ? "tab-link tab-link-active" : "tab-link"}
          >
            {tab.label}
          </Link>
        );
      })}
    </nav>
  );
}
