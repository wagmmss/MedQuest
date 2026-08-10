"use client";

import { useState } from "react";
import { useUser } from "@clerk/nextjs";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { AccountModal } from "./AccountModal";
import { ThemeToggle } from "./ThemeToggle";

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

  return (
    <>
      <header className="md:hidden flex justify-between items-center w-full px-6 py-3 h-16 bg-surface border-b border-outline-variant z-10 sticky top-0">
        <h1 className="font-headline-md text-headline-md font-bold text-primary">MedQuest</h1>
        <div className="flex items-center gap-4">
          <ThemeToggle />
          <button 
            onClick={() => setIsMobileMenuOpen(true)}
            className="text-on-surface-variant hover:bg-surface-container-low rounded-full p-2 transition-colors flex items-center justify-center cursor-pointer"
          >
            <span className="material-symbols-outlined" data-icon="menu">menu</span>
          </button>
          <button 
            onClick={() => setIsModalOpen(true)}
            className="w-8 h-8 rounded-full bg-surface-container-high overflow-hidden border border-outline-variant/30 flex items-center justify-center cursor-pointer hover:opacity-85 transition-opacity focus:outline-none focus:border-outline"
          >
            {isLoaded && user?.imageUrl ? (
              <img src={user.imageUrl} alt="Avatar" className="w-full h-full object-cover" />
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
      <div 
        className={`fixed top-0 left-0 h-full w-64 bg-surface z-50 transform transition-transform duration-300 ease-in-out md:hidden ${
          isMobileMenuOpen ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        <div className="flex items-center justify-between p-4 border-b border-outline-variant">
          <h2 className="font-headline-sm font-bold text-primary">Menu</h2>
          <button 
            onClick={() => setIsMobileMenuOpen(false)}
            className="p-2 rounded-full hover:bg-surface-container-low transition-colors text-on-surface"
          >
            <span className="material-symbols-outlined">close</span>
          </button>
        </div>
        <nav className="p-4 space-y-2">
          {NAV_ITEMS.map((item) => {
            const isActive = pathname === item.href;
            return (
              <Link 
                key={item.href} 
                href={item.href}
                onClick={() => setIsMobileMenuOpen(false)}
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
      </div>

      <AccountModal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} />
    </>
  );
}
