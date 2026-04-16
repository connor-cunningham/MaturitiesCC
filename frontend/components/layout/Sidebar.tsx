"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard, FileText, Building2, Users, Map,
  Target, Upload, Settings, TrendingDown,
} from "lucide-react";

const navItems = [
  { href: "/dashboard",   label: "Dashboard",   icon: LayoutDashboard },
  { href: "/loans",       label: "Loans",        icon: FileText },
  { href: "/properties",  label: "Properties",   icon: Building2 },
  { href: "/owners",      label: "Owners",       icon: Users },
  { href: "/map",         label: "Map",          icon: Map },
  { href: "/pipeline",    label: "Pipeline",     icon: Target },
  { href: "/import",      label: "Import",       icon: Upload },
];

export function Sidebar() {
  const path = usePathname();

  return (
    <aside
      className="flex flex-col w-[220px] min-w-[220px] bg-[#1F4E79] text-white h-full overflow-y-auto"
    >
      {/* Logo */}
      <div className="px-5 py-4 border-b border-white/10">
        <div className="flex items-center gap-2">
          <TrendingDown className="w-5 h-5 text-sky-300" />
          <span className="font-bold text-base tracking-tight">MaturitiesCC</span>
        </div>
        <p className="text-xs text-white/50 mt-0.5">Maturity Intelligence</p>
      </div>

      {/* Nav */}
      <nav className="flex-1 px-3 py-4 space-y-0.5">
        {navItems.map(({ href, label, icon: Icon }) => {
          const active = path === href || (href !== "/dashboard" && path.startsWith(href));
          return (
            <Link
              key={href}
              href={href}
              className={`flex items-center gap-3 px-3 py-2 rounded-md text-sm transition-colors ${
                active
                  ? "bg-white/20 text-white font-medium"
                  : "text-white/70 hover:bg-white/10 hover:text-white"
              }`}
            >
              <Icon className="w-4 h-4 flex-shrink-0" />
              {label}
            </Link>
          );
        })}
      </nav>

      <div className="px-3 py-3 border-t border-white/10">
        <p className="text-xs text-white/40 text-center">v1.0 — Local</p>
      </div>
    </aside>
  );
}
