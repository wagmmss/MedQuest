"use client";

import { AlertTriangle, RefreshCcw } from "lucide-react";
import { useEffect, useState } from "react";

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  const [isRetrying, setIsRetrying] = useState(false);

  useEffect(() => {
    console.error(error);
    void fetch("/api/logs/error", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        error: error.message,
        info: { digest: error.digest },
        url: window.location.href,
      }),
    }).catch(() => undefined);
  }, [error]);

  const retry = () => {
    setIsRetrying(true);
    reset();
    // `reset` only retries the current error boundary. Reloading also fetches
    // fresh route data when the failure originated from a stale request/cache.
    window.location.reload();
  };

  return (
    <div className="flex-1 flex flex-col items-center justify-center min-h-[400px] p-6 text-center animate-in fade-in duration-300">
      <div className="bg-destructive/10 p-4 rounded-full mb-4">
        <AlertTriangle className="text-destructive w-10 h-10" />
      </div>
      <h2 className="text-xl font-bold mb-2">Algo deu errado</h2>
      <p className="text-muted-foreground mb-6 max-w-md">
        Não foi possível carregar os dados no momento. Tente novamente em alguns instantes.
      </p>
      <button
        type="button"
        onClick={retry}
        disabled={isRetrying}
        className="flex items-center gap-2 bg-primary text-primary-foreground px-4 py-2 rounded-md hover:bg-primary/90 transition-colors font-medium disabled:cursor-wait disabled:opacity-70"
      >
        <RefreshCcw className={isRetrying ? "animate-spin" : undefined} size={16} />
        {isRetrying ? "Recarregando..." : "Tentar novamente"}
      </button>
    </div>
  );
}
