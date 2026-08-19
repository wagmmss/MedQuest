"use client";

import { useRouter } from "next/navigation";

export function DemoButton() {
  const router = useRouter();

  const handleDemo = () => {
    document.cookie = "medquest_demo=1; path=/; max-age=86400"; // 1 day
    router.refresh();
  };

  return (
    <button 
      onClick={handleDemo}
      className="mt-6 text-sm font-semibold text-muted-foreground hover:text-primary transition-colors underline underline-offset-4"
    >
      Explorar Modo Demonstração (Sem Login)
    </button>
  );
}
