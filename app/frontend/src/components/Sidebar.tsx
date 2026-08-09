"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import clsx from "clsx";

const NAV_ITEMS = [
  { href: "/", label: "Dashboard", icon: "dashboard" },
  { href: "/cobertura", label: "Cobertura", icon: "my_location" },
  { href: "/analise", label: "Análise", icon: "analytics" },
  { href: "/planner", label: "Planner", icon: "calendar_month" },
  { href: "/estudar", label: "Estudar", icon: "menu_book" },
  { href: "/revisao-ativa", label: "Revisão Ativa", icon: "psychology" },
  { href: "/simulado", label: "Simulado USP", icon: "description" },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="hidden md:flex flex-col bg-surface-container-low h-screen left-0 w-64 border-r border-outline-variant p-4 gap-stack-md z-10">
      <div className="mb-6 flex flex-col items-center justify-center p-4">
        <div className="w-12 h-12 rounded-full bg-primary-container text-on-primary-container flex items-center justify-center mb-2">
          <span className="material-symbols-outlined" data-icon="local_hospital">local_hospital</span>
        </div>
        <h1 className="font-headline-md text-headline-md font-bold text-primary">MedQuest</h1>
        <p className="font-label-md text-label-md text-on-surface-variant">Preparação USP</p>
      </div>

      <nav className="flex-1 flex flex-col gap-1 overflow-y-auto">
        {NAV_ITEMS.map((item) => {
          const isActive = pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={clsx(
                "flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200",
                isActive 
                  ? "bg-secondary-container text-on-secondary-container font-bold opacity-80 shadow-[0_1px_2px_rgba(0,0,0,0.05)]" 
                  : "text-on-surface-variant hover:bg-surface-container-high"
              )}
            >
              <span className="material-symbols-outlined" data-icon={item.icon}>{item.icon}</span>
              <span className="font-label-md text-label-md">{item.label}</span>
            </Link>
          );
        })}
      </nav>

      <div className="mt-auto flex flex-col gap-2 pt-2 border-t border-outline-variant">
        <button 
          className="flex items-center gap-3 px-4 py-3 rounded-xl text-on-surface-variant hover:bg-surface-container-high transition-all duration-200 text-left w-full"
          onClick={() => document.dispatchEvent(new KeyboardEvent('keydown', { key: 'k', metaKey: true }))}
        >
          <span className="material-symbols-outlined" data-icon="search">search</span>
          <span className="font-label-md text-label-md flex-1">Buscar...</span>
          <kbd className="text-[10px] bg-surface px-1.5 py-0.5 rounded border border-outline-variant opacity-70">Cmd+K</kbd>
        </button>
        <div className="flex items-center gap-3 px-4 py-3 rounded-xl text-on-surface-variant hover:bg-surface-container-high transition-all duration-200 justify-between">
          <div className="flex items-center gap-3">
            <span className="material-symbols-outlined" data-icon="person">person</span>
            <span className="font-label-md text-label-md">Conta</span>
          </div>
          <div className="w-8 h-8 rounded-full bg-surface-container-high" />
        </div>
      </div>
    </aside>
  );
}
