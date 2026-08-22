"use client";

import { useEffect, useRef, useState } from "react";
import { useUser } from "@clerk/nextjs";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { AccountModal } from "./AccountModal";
import { ThemeToggle } from "./ThemeToggle";
import { useZenMode } from "@/hooks/useZenMode";
import Image from "next/image";
import clsx from "clsx";

const NAV_ITEMS = [
  { href: "/", label: "Dashboard", icon: "dashboard" },
  { href: "/cobertura", label: "Cobertura", icon: "my_location" },
  { href: "/analise", label: "Análise", icon: "analytics" },
  { href: "/planner", label: "Planner", icon: "calendar_month" },
  { href: "/estudar", label: "Estudar", icon: "menu_book" },
  { href: "/revisao-ativa", label: "Revisão Ativa", icon: "psychology" },
  { href: "/simulado", label: "Simulados", icon: "description" },
];

export default function TopNav() {
  const { user, isLoaded } = useUser();
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const pathname = usePathname();
  const router = useRouter();
  const { isZenMode, toggleZenMode } = useZenMode();
  const menuButtonRef = useRef<HTMLButtonElement>(null);
  const drawerRef = useRef<HTMLDivElement>(null);

  const handleNavClick = (e: React.MouseEvent, href: string) => {
    e.preventDefault();
    setIsMobileMenuOpen(false);
    router.push(href);
  };

  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (isMobileMenuOpen && event.key === "Escape") {
        setIsMobileMenuOpen(false);
        return;
      }

      const tag = (event.target as HTMLElement).tagName;
      if (tag === "INPUT" || tag === "TEXTAREA") return;
      if (event.key.toLowerCase() === "z" && !event.ctrlKey && !event.metaKey && !event.altKey) {
        event.preventDefault();
        toggleZenMode();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [toggleZenMode, isMobileMenuOpen]);

  // Focus trap, focus restoration and background scroll lock.
  useEffect(() => {
    if (!isMobileMenuOpen) return;
    const previousOverflow = document.body.style.overflow;
    const opener = menuButtonRef.current;
    document.body.style.overflow = "hidden";
    const drawer = drawerRef.current;
    const controls = () => Array.from(drawer?.querySelectorAll<HTMLElement>('a[href], button:not([disabled])') || []);
    controls()[0]?.focus();
    const trapFocus = (event: KeyboardEvent) => {
      if (event.key !== "Tab") return;
      const items = controls();
      if (!items.length) return;
      const first = items[0];
      const last = items[items.length - 1];
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    };
    document.addEventListener("keydown", trapFocus);
    return () => {
      document.removeEventListener("keydown", trapFocus);
      document.body.style.overflow = previousOverflow;
      opener?.focus();
    };
  }, [isMobileMenuOpen]);

  return (
    <>
      <header className="app-top-nav md:hidden flex justify-between items-center w-full px-5 py-3 h-16 bg-surface/50 backdrop-blur-2xl border-b border-border/50 z-10 sticky top-0 transition-all duration-300 shadow-sm">
        <h1 className="font-semibold text-lg text-foreground tracking-tight flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-primary text-primary-foreground flex items-center justify-center">
            <span className="material-symbols-outlined text-[16px]" data-icon="local_hospital">local_hospital</span>
          </div>
          MedQuest
        </h1>
        <div className="flex items-center gap-2">
          <button
            onClick={toggleZenMode}
            className="text-muted-foreground hover:bg-surface-variant/50 rounded-md p-2 transition-colors flex items-center justify-center cursor-pointer"
            title={isZenMode ? "Sair do Modo Zen" : "Entrar no Modo Zen (Z)"}
            aria-label={isZenMode ? "Sair do modo Zen" : "Entrar no modo Zen"}
            aria-pressed={isZenMode}
          >
            <span className="material-symbols-outlined text-[20px]">{isZenMode ? "fullscreen_exit" : "fullscreen"}</span>
          </button>
          <div className="scale-90 opacity-80"><ThemeToggle /></div>
          <button 
            ref={menuButtonRef}
            onClick={() => setIsMobileMenuOpen(true)}
            className="text-muted-foreground hover:bg-surface-variant/50 rounded-md p-2 transition-colors flex items-center justify-center cursor-pointer"
            aria-label="Abrir menu principal"
            aria-expanded={isMobileMenuOpen}
            aria-controls="mobile-navigation-drawer"
          >
            <span className="material-symbols-outlined text-[20px]" data-icon="menu">menu</span>
          </button>
          <button 
            onClick={() => setIsModalOpen(true)}
            className="relative w-8 h-8 rounded-full bg-muted overflow-hidden ring-1 ring-border shadow-sm flex items-center justify-center cursor-pointer hover:opacity-85 transition-opacity focus:outline-none focus:ring-primary/50 ml-1"
            aria-label="Abrir minha conta"
          >
            {isLoaded && user?.imageUrl ? (
              <Image src={user.imageUrl} alt="Avatar" fill sizes="32px" className="object-cover" />
            ) : (
              <span className="material-symbols-outlined text-[18px] text-muted-foreground" data-icon="person">person</span>
            )}
          </button>
        </div>
      </header>
      
      {/* Mobile Drawer Overlay */}
      {isMobileMenuOpen && (
        <div 
          className="fixed inset-0 bg-black/60 backdrop-blur-sm z-40 md:hidden transition-opacity"
          onClick={() => setIsMobileMenuOpen(false)}
        />
      )}
      
      {/* Mobile Drawer */}
      {isMobileMenuOpen && <div
        ref={drawerRef}
        id="mobile-navigation-drawer"
        role="dialog"
        aria-modal="true"
        aria-labelledby="mobile-menu-title"
        className="fixed top-0 left-0 h-full w-[min(20rem,85vw)] bg-background/95 backdrop-blur-2xl z-50 shadow-2xl md:hidden border-r border-border/50 flex flex-col"
      >
        <div className="flex items-center justify-between p-4 border-b border-border/50">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-primary text-primary-foreground flex items-center justify-center shadow-sm">
              <span className="material-symbols-outlined text-[16px]" data-icon="local_hospital">local_hospital</span>
            </div>
            <h2 id="mobile-menu-title" className="font-semibold text-lg text-foreground tracking-tight">Menu</h2>
          </div>
          <button 
            id="mobile-menu-close"
            onClick={() => setIsMobileMenuOpen(false)}
            className="p-2 rounded-md hover:bg-surface-variant/50 transition-colors text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/20"
            aria-label="Fechar menu"
          >
            <span className="material-symbols-outlined text-[20px]">close</span>
          </button>
        </div>
        <nav className="flex-1 overflow-y-auto p-4 space-y-1.5" aria-label="Navegação principal">
          {NAV_ITEMS.map((item) => {
            const isActive = pathname === item.href;
            return (
              <Link 
                key={item.href} 
                href={item.href}
                onClick={(e) => handleNavClick(e, item.href)}
                aria-current={isActive ? "page" : undefined}
                className={clsx(
                  "flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all duration-200 text-sm font-medium",
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
      </div>}

      <AccountModal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} />
    </>
  );
}
