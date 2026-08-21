"use client";

import { useEffect, useRef, useState } from "react";
import { useUser } from "@clerk/nextjs";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
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
      <header className="app-top-nav md:hidden flex justify-between items-center w-full px-6 py-3 h-16 bg-surface/90 backdrop-blur-xl border-b border-outline-variant z-10 sticky top-0 transition-all duration-300">
        <h1 className="font-headline-md text-headline-md font-bold text-primary">MedQuest</h1>
        <div className="flex items-center gap-4">
          <button
            onClick={toggleZenMode}
            className="text-on-surface-variant hover:bg-surface-container-low rounded-full p-2 transition-colors flex items-center justify-center cursor-pointer"
            title={isZenMode ? "Sair do Modo Zen" : "Entrar no Modo Zen (Z)"}
            aria-label={isZenMode ? "Sair do modo Zen" : "Entrar no modo Zen"}
            aria-pressed={isZenMode}
          >
            <span className="material-symbols-outlined">{isZenMode ? "fullscreen_exit" : "fullscreen"}</span>
          </button>
          <ThemeToggle />
          <button 
            ref={menuButtonRef}
            onClick={() => setIsMobileMenuOpen(true)}
            className="text-on-surface-variant hover:bg-surface-container-low rounded-full p-2 transition-colors flex items-center justify-center cursor-pointer"
            aria-label="Abrir menu principal"
            aria-expanded={isMobileMenuOpen}
            aria-controls="mobile-navigation-drawer"
          >
            <span className="material-symbols-outlined" data-icon="menu">menu</span>
          </button>
          <button 
            onClick={() => setIsModalOpen(true)}
            className="relative w-8 h-8 rounded-full bg-surface-container-high overflow-hidden border border-outline-variant/30 flex items-center justify-center cursor-pointer hover:opacity-85 transition-opacity focus:outline-none focus:border-outline"
            aria-label="Abrir minha conta"
          >
            {isLoaded && user?.imageUrl ? (
              <Image src={user.imageUrl} alt="Avatar" fill sizes="32px" className="object-cover" />
            ) : (
              <span className="material-symbols-outlined text-lg" data-icon="person">person</span>
            )}
          </button>
        </div>
      </header>
      
      {/* Mobile Drawer Overlay */}
      {isMobileMenuOpen && (
        <div 
          className="fixed inset-0 bg-black/50 z-40 md:hidden"
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
        className="fixed top-0 left-0 h-full w-[min(20rem,85vw)] bg-surface z-50 shadow-2xl md:hidden"
      >
        <div className="flex items-center justify-between p-4 border-b border-outline-variant">
          <h2 id="mobile-menu-title" className="font-headline-sm font-bold text-primary">Menu</h2>
          <button 
            id="mobile-menu-close"
            onClick={() => setIsMobileMenuOpen(false)}
            className="p-2 rounded-full hover:bg-surface-container-low transition-colors text-on-surface focus:outline-none focus:ring-2 focus:ring-primary"
            aria-label="Fechar menu"
          >
            <span className="material-symbols-outlined">close</span>
          </button>
        </div>
        <nav className="p-4 space-y-2" aria-label="Navegação principal">
          {NAV_ITEMS.map((item) => {
            const isActive = pathname === item.href;
            return (
              <Link 
                key={item.href} 
                href={item.href}
                onClick={(e) => handleNavClick(e, item.href)}
                aria-current={isActive ? "page" : undefined}
                className={`flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${
                  isActive 
                    ? "bg-primary-container text-on-primary-container font-medium" 
                    : "text-on-surface-variant hover:bg-surface-container hover:text-on-surface"
                }`}
              >
                <span className="material-symbols-outlined" data-icon={item.icon}>{item.icon}</span>
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
