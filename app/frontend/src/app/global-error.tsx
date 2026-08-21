"use client";

import { useEffect } from "react";
import { AlertTriangle, Home, RotateCcw } from "lucide-react";
import Link from "next/link";

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    // Log error to backend
    const logError = async () => {
      try {
        await fetch("/api/logs/error", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            error: error.message,
            info: { digest: error.digest },
            url: window.location.href,
          }),
        });
      } catch (err) {
        console.error("Failed to send error log:", err);
      }
    };
    logError();
  }, [error]);

  return (
    <html lang="pt-BR">
      <body className="antialiased bg-background text-foreground h-screen w-screen flex flex-col items-center justify-center p-6">
        <div className="max-w-md w-full bg-card border border-border rounded-2xl shadow-xl p-8 flex flex-col items-center text-center">
          <div className="w-16 h-16 bg-destructive/10 text-destructive rounded-full flex items-center justify-center mb-6">
            <AlertTriangle size={32} />
          </div>
          
          <h1 className="text-2xl font-bold text-foreground mb-2">
            Ocorreu um erro crítico
          </h1>
          
          <p className="text-muted-foreground mb-8">
            Nossa equipe já foi notificada. Tente recarregar a página ou volte para o início.
          </p>

          <div className="flex flex-col w-full gap-3">
            <button
              onClick={() => reset()}
              className="w-full flex items-center justify-center gap-2 bg-primary text-primary-foreground font-semibold py-3 px-4 rounded-xl hover:bg-primary/90 transition-colors"
            >
              <RotateCcw size={18} />
              Tentar Novamente
            </button>
            
            <Link
              href="/"
              className="w-full flex items-center justify-center gap-2 bg-muted text-foreground font-semibold py-3 px-4 rounded-xl hover:bg-muted/80 transition-colors"
            >
              <Home size={18} />
              Voltar ao Início
            </Link>
          </div>
        </div>
      </body>
    </html>
  );
}
