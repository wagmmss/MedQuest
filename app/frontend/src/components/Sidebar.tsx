"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import clsx from "clsx";
import { useUser } from "@clerk/nextjs";
import { AccountModal } from "./AccountModal";
import { ThemeToggle } from "./ThemeToggle";
import { useZenMode } from "@/hooks/useZenMode";
import Image from "next/image";

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
  const { user, isLoaded } = useUser();
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [shortcut, setShortcut] = useState("Cmd+K");
  const { isZenMode, toggleZenMode } = useZenMode();

  useEffect(() => {
    if (typeof navigator !== "undefined") {
      const isMac = navigator.userAgent.indexOf("Mac") !== -1;
      const timer = setTimeout(() => {
        setShortcut(isMac ? "⌘K" : "Ctrl+K");
      }, 0);
      return () => clearTimeout(timer);
    }
  }, []);

  return (
    <>
      <aside className="app-sidebar hidden md:flex flex-col bg-surface/50 backdrop-blur-2xl h-full left-0 w-64 border-r border-border/50 p-4 gap-stack-md z-10 transition-all duration-300">
        <div className="mb-6 flex flex-col items-center justify-center p-4">
          <div className="w-10 h-10 rounded-xl bg-primary text-primary-foreground flex items-center justify-center mb-3 shadow-sm ring-1 ring-primary/10">
            <span className="material-symbols-outlined text-[20px]" data-icon="local_hospital">local_hospital</span>
          </div>
          <h1 className="font-semibold text-lg text-foreground tracking-tight">MedQuest</h1>
          <p className="text-[11px] font-medium text-muted-foreground uppercase tracking-widest mt-1">Preparação USP</p>
        </div>

        <nav className="flex-1 flex flex-col gap-1.5 overflow-y-auto px-1" aria-label="Navegação principal">
          {NAV_ITEMS.map((item) => {
            const isActive = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                aria-current={isActive ? "page" : undefined}
                className={clsx(
                  "flex items-center gap-3 py-2.5 px-3 rounded-lg transition-all duration-200 text-sm font-medium",
                  isActive 
                    ? "bg-primary text-primary-foreground shadow-sm" 
                    : "text-muted-foreground hover:bg-surface-variant/50 hover:text-foreground"
                )}
              >
                <span className={clsx("material-symbols-outlined text-[20px]", isActive && "font-variation-settings-'FILL' 1")} data-icon={item.icon}>{item.icon}</span>
                <span>{item.label}</span>
              </Link>
            );
          })}
        </nav>

        <div className="mt-auto flex flex-col gap-2 pt-4 border-t border-border/50">
          <div className="flex items-center justify-between gap-1 px-1">
            <button 
              className="flex items-center gap-2 px-2 py-2 rounded-md text-muted-foreground hover:bg-surface-variant/50 hover:text-foreground transition-all duration-200 text-left flex-1 cursor-pointer"
              onClick={() => window.dispatchEvent(new Event('open-command-palette'))}
              aria-label="Abrir barra de busca"
            >
              <span className="material-symbols-outlined text-[18px]" data-icon="search" aria-hidden="true">search</span>
              <span className="text-xs font-medium flex-1">Buscar...</span>
              <kbd className="text-[10px] bg-background px-1.5 py-0.5 rounded border border-border shadow-sm text-muted-foreground">{shortcut}</kbd>
            </button>
            <button
              onClick={toggleZenMode}
              className="flex items-center justify-center p-2 rounded-md text-muted-foreground hover:bg-surface-variant/50 hover:text-foreground transition-colors text-left cursor-pointer"
              title={isZenMode ? "Sair do Modo Zen" : "Entrar no Modo Zen (Z)"}
              aria-label={isZenMode ? "Sair do modo Zen" : "Entrar no modo Zen"}
              aria-pressed={isZenMode}
            >
              <span className="material-symbols-outlined text-[18px]">{isZenMode ? "fullscreen_exit" : "fullscreen"}</span>
            </button>
            <div className="scale-90 opacity-80 hover:opacity-100 transition-opacity"><ThemeToggle /></div>
          </div>
          
          <button
            onClick={() => setIsModalOpen(true)}
            className="flex items-center gap-3 px-3 py-2.5 mx-1 mt-1 rounded-lg text-foreground hover:bg-surface-variant/50 transition-all duration-200 justify-between w-auto text-left cursor-pointer border border-transparent hover:border-border/50 focus:outline-none focus:ring-2 focus:ring-primary/20"
            aria-label="Minha Conta"
          >
            <div className="flex items-center gap-2.5 min-w-0">
              {isLoaded && user?.imageUrl ? (
                <div className="relative w-6 h-6 rounded-full overflow-hidden flex-shrink-0 ring-1 ring-border shadow-sm">
                  <Image src={user.imageUrl} alt="Avatar" fill sizes="24px" className="object-cover" />
                </div>
              ) : (
                <div className="w-6 h-6 rounded-full bg-muted flex items-center justify-center flex-shrink-0 ring-1 ring-border">
                  <span className="material-symbols-outlined text-[14px]" data-icon="person">person</span>
                </div>
              )}
              <span className="text-sm font-medium truncate">
                {isLoaded ? (user?.firstName || "Conta") : "Conta"}
              </span>
            </div>
            <span className="material-symbols-outlined text-muted-foreground text-[16px] opacity-50">more_horiz</span>
          </button>
        </div>
      </aside>
      
      <AccountModal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} />
    </>
  );
}
