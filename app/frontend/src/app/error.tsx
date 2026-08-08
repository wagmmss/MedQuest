"use client";

import { AlertTriangle, RefreshCcw } from "lucide-react";
import { useEffect } from "react";

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <div className="flex-1 flex flex-col items-center justify-center min-h-[400px] p-6 text-center animate-in fade-in duration-300">
      <div className="bg-destructive/10 p-4 rounded-full mb-4">
        <AlertTriangle className="text-destructive w-10 h-10" />
      </div>
      <h2 className="text-xl font-bold mb-2">Algo deu errado</h2>
      <p className="text-muted-foreground mb-6 max-w-md">
        Não foi possível carregar os dados. Verifique se o servidor backend está rodando na porta 5050.
      </p>
      <button
        onClick={() => reset()}
        className="flex items-center gap-2 bg-primary text-primary-foreground px-4 py-2 rounded-md hover:bg-primary/90 transition-colors font-medium"
      >
        <RefreshCcw size={16} />
        Tentar novamente
      </button>
    </div>
  );
}
