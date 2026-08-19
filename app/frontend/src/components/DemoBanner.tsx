"use client";

import { useUser } from "@clerk/nextjs";
import { useRouter } from "next/navigation";

export function DemoBanner() {
  const { user, isLoaded } = useUser();
  const router = useRouter();

  if (!isLoaded || user) return null;

  const exitDemoMode = () => {
    document.cookie = "medquest_demo=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT";
    router.refresh();
  };

  return (
    <div className="w-full bg-primary/10 border-b border-primary/20 text-primary px-4 py-2 text-sm flex items-center justify-center gap-2 font-medium z-50">
      <span className="material-symbols-outlined text-lg">info</span>
      <span>Você está no Modo Demonstração. O progresso é temporário.</span>
      <button onClick={exitDemoMode} className="ml-2 font-bold underline underline-offset-2 hover:text-primary-fixed">
        Sair
      </button>
    </div>
  );
}
