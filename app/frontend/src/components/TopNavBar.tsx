"use client";

import { UserButton } from "@clerk/nextjs";

export function TopNavBar() {
  return (
    <header className="md:hidden flex justify-between items-center w-full px-6 py-3 h-16 bg-surface border-b border-outline-variant z-10 sticky top-0">
      <h1 className="font-headline-md text-headline-md font-bold text-primary">MedQuest</h1>
      <div className="flex items-center gap-4">
        <button className="text-on-surface-variant hover:bg-surface-container-low rounded-full p-2 transition-colors flex items-center justify-center">
          <span className="material-symbols-outlined" data-icon="menu">menu</span>
        </button>
        <UserButton appearance={{ elements: { userButtonAvatarBox: "w-8 h-8" } }} />
      </div>
    </header>
  );
}
