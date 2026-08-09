"use client";

import { useState } from "react";
import { useUser } from "@clerk/nextjs";
import { AccountModal } from "./AccountModal";

export default function TopNav() {
  const { user, isLoaded } = useUser();
  const [isModalOpen, setIsModalOpen] = useState(false);

  return (
    <>
      <header className="md:hidden flex justify-between items-center w-full px-6 py-3 h-16 bg-surface border-b border-outline-variant z-10 sticky top-0">
        <h1 className="font-headline-md text-headline-md font-bold text-primary">MedQuest</h1>
        <div className="flex items-center gap-4">
          <button className="text-on-surface-variant hover:bg-surface-container-low rounded-full p-2 transition-colors flex items-center justify-center cursor-pointer">
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
      
      <AccountModal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} />
    </>
  );
}

