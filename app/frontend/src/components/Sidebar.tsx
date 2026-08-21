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
      <aside className="app-sidebar hidden md:flex flex-col bg-surface-container-low/90 backdrop-blur-xl h-full left-0 w-64 border-r border-outline-variant p-4 gap-stack-md z-10 transition-all duration-300">
        <div className="mb-6 flex flex-col items-center justify-center p-4">
          <div className="w-12 h-12 rounded-full bg-primary-container text-on-primary-container flex items-center justify-center mb-2">
            <span className="material-symbols-outlined" data-icon="local_hospital">local_hospital</span>
          </div>
          <h1 className="font-headline-md text-headline-md font-bold text-primary">MedQuest</h1>
          <p className="font-label-md text-label-md text-on-surface-variant">Preparação USP</p>
        </div>

        <nav className="flex-1 flex flex-col gap-1 overflow-y-auto" aria-label="Navegação principal">
          {NAV_ITEMS.map((item) => {
            const isActive = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                aria-current={isActive ? "page" : undefined}
                className={clsx(
                  "flex items-center gap-3 py-3 rounded-xl transition-all duration-200",
                  isActive 
                    ? "bg-primary/10 text-primary font-bold border-l-4 border-primary px-3 shadow-sm" 
                    : "px-4 text-on-surface-variant hover:bg-surface-container-high"
                )}
              >
                <span className="material-symbols-outlined" data-icon={item.icon}>{item.icon}</span>
                <span className="font-label-md text-label-md">{item.label}</span>
              </Link>
            );
          })}
        </nav>

        <div className="mt-auto flex flex-col gap-2 pt-2 border-t border-outline-variant">
          <div className="flex items-center justify-between gap-2">
            <button 
              className="flex items-center gap-3 px-4 py-3 rounded-xl text-on-surface-variant hover:bg-surface-container-high transition-all duration-200 text-left flex-1 cursor-pointer"
              onClick={() => window.dispatchEvent(new Event('open-command-palette'))}
              aria-label="Abrir barra de busca"
            >
              <span className="material-symbols-outlined" data-icon="search" aria-hidden="true">search</span>
              <span className="font-label-md text-label-md flex-1">Buscar...</span>
              <kbd className="text-[10px] bg-surface px-1.5 py-0.5 rounded border border-outline-variant opacity-70">{shortcut}</kbd>
            </button>
            <button
              onClick={toggleZenMode}
              className="flex items-center justify-center p-3 rounded-xl text-on-surface-variant hover:bg-surface-container-high transition-colors text-left cursor-pointer"
              title={isZenMode ? "Sair do Modo Zen" : "Entrar no Modo Zen (Z)"}
              aria-label={isZenMode ? "Sair do modo Zen" : "Entrar no modo Zen"}
              aria-pressed={isZenMode}
            >
              <span className="material-symbols-outlined">{isZenMode ? "fullscreen_exit" : "fullscreen"}</span>
            </button>
            <ThemeToggle />
          </div>
          
          <button
            onClick={() => setIsModalOpen(true)}
            className="flex items-center gap-3 px-4 py-3 rounded-xl text-on-surface hover:bg-surface-container-high transition-all duration-200 justify-between w-full text-left cursor-pointer border border-transparent focus:outline-none focus:border-outline-variant"
            aria-label="Minha Conta"
          >
            <div className="flex items-center gap-3 min-w-0">
              {isLoaded && user?.imageUrl ? (
                <div className="relative w-5 h-5 rounded-full overflow-hidden flex-shrink-0">
                  <Image src={user.imageUrl} alt="Avatar" fill sizes="20px" className="object-cover" />
                </div>
              ) : (
                <span className="material-symbols-outlined flex-shrink-0" data-icon="person">person</span>
              )}
              <span className="font-label-md text-label-md truncate">
                {isLoaded ? (user?.firstName || "Conta") : "Conta"}
              </span>
            </div>
            {isLoaded && user?.imageUrl && (
              <div className="relative w-8 h-8 rounded-full bg-surface-container-high overflow-hidden border border-outline-variant/30 flex-shrink-0">
                <Image src={user.imageUrl} alt="Avatar Mini" fill sizes="32px" className="object-cover" />
              </div>
            )}
          </button>
        </div>
      </aside>
      
      <AccountModal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} />
    </>
  );
}
