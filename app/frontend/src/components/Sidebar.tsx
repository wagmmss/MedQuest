"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { LayoutDashboard, Target, Activity, CalendarDays, BrainCircuit, ChevronLeft, ChevronRight, Search, FileSignature } from "lucide-react";
import { useState } from "react";
import { ThemeToggle } from "./ThemeToggle";
import clsx from "clsx";
import { UserButton } from "@clerk/nextjs";

const NAV_ITEMS = [
  { href: "/", label: "Dashboard", icon: LayoutDashboard },
  { href: "/cobertura", label: "Cobertura", icon: Target },
  { href: "/analise", label: "Análise", icon: Activity },
  { href: "/planner", label: "Planner", icon: CalendarDays },
  { href: "/estudar", label: "Estudar", icon: BrainCircuit },
  { href: "/revisao-ativa", label: "Revisão Ativa", icon: BrainCircuit },
  { href: "/simulado", label: "Simulado USP", icon: FileSignature },
];

export function Sidebar() {
  const pathname = usePathname();
  const [collapsed, setCollapsed] = useState(false);

  return (
    <aside 
      className={clsx(
        "flex flex-col h-screen border-r border-border bg-card transition-all duration-300",
        collapsed ? "w-16" : "w-64"
      )}
    >
      <div className="flex items-center justify-between p-4 border-b border-border">
        {!collapsed && <span className="font-bold text-lg text-primary tracking-tight">MedQuest</span>}
        <button 
          onClick={() => setCollapsed(!collapsed)}
          className={clsx("p-1.5 rounded-md hover:bg-muted text-muted-foreground transition-colors", collapsed && "mx-auto")}
          aria-label="Toggle sidebar"
        >
          {collapsed ? <ChevronRight size={20} /> : <ChevronLeft size={20} />}
        </button>
      </div>

      <div className="flex-1 py-4 overflow-y-auto overflow-x-hidden flex flex-col gap-2 px-3">
        {NAV_ITEMS.map((item) => {
          const isActive = pathname === item.href;
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={clsx(
                "flex items-center gap-3 px-3 py-2.5 rounded-md transition-colors whitespace-nowrap",
                isActive 
                  ? "bg-primary text-primary-foreground font-medium shadow-1" 
                  : "text-muted-foreground hover:bg-muted hover:text-foreground"
              )}
            >
              <Icon size={20} className="shrink-0" />
              {!collapsed && <span>{item.label}</span>}
            </Link>
          );
        })}
      </div>

      <div className="p-4 border-t border-border flex flex-col gap-4">
        <button 
          className={clsx(
            "flex items-center gap-2 px-3 py-2 rounded-md bg-muted text-muted-foreground hover:text-foreground text-sm transition-colors",
            collapsed && "justify-center"
          )}
          onClick={() => document.dispatchEvent(new KeyboardEvent('keydown', { key: 'k', metaKey: true }))}
        >
          <Search size={16} className="shrink-0" />
          {!collapsed && (
            <div className="flex flex-1 items-center justify-between">
              <span>Buscar...</span>
              <kbd className="text-[10px] bg-background px-1.5 py-0.5 rounded border border-border opacity-70">Cmd+K</kbd>
            </div>
          )}
        </button>
        <div className={clsx("flex items-center", collapsed ? "justify-center flex-col gap-4" : "justify-between px-1")}>
          <UserButton appearance={{ elements: { userButtonAvatarBox: "w-8 h-8" } }} />
          <ThemeToggle />
        </div>
      </div>
    </aside>
  );
}
