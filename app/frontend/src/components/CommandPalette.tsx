"use client";

import { useEffect, useState, useRef } from "react";
import { useRouter } from "next/navigation";
import { Search, Loader2, ArrowRight } from "lucide-react";
import clsx from "clsx";
import { api } from "@/lib/api";
import { SearchResult } from "@/types/api";

export function CommandPalette() {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const router = useRouter();

  useEffect(() => {
    const down = (e: KeyboardEvent) => {
      if ((e.key === "k" || e.key === "K") && (e.metaKey || e.ctrlKey)) {
        e.preventDefault();
        setOpen((open) => !open);
      }
      if (e.key === "Escape") {
        setOpen(false);
      }
    };
    const handleOpen = () => setOpen(true);

    document.addEventListener("keydown", down);
    window.addEventListener("open-command-palette", handleOpen);
    return () => {
      document.removeEventListener("keydown", down);
      window.removeEventListener("open-command-palette", handleOpen);
    };
  }, []);

  useEffect(() => {
    if (open) {
      inputRef.current?.focus();
    } else {
      const timer = setTimeout(() => {
        setQuery("");
        setResults([]);
      }, 0);
      return () => clearTimeout(timer);
    }
  }, [open]);

  useEffect(() => {
    if (!query.trim()) {
      const timer = setTimeout(() => {
        setResults([]);
      }, 0);
      return () => clearTimeout(timer);
    }

    let isMounted = true;
    const timer = setTimeout(async () => {
      if (isMounted) {
        setLoading(true);
        setError(false);
      }
      try {
        const res = await api.questions.search(query, false);
        if (isMounted) setResults(res.slice(0, 5));
      } catch (e) {
        console.error(e);
        if (isMounted) setError(true);
      } finally {
        if (isMounted) setLoading(false);
      }
    }, 300);

    return () => {
      isMounted = false;
      clearTimeout(timer);
    };
  }, [query]);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center pt-[15vh]">
      <div 
        className="fixed inset-0 bg-foreground/20 backdrop-blur-sm" 
        onClick={() => setOpen(false)}
      />
      <div className="relative w-full max-w-xl bg-card rounded-lg shadow-2 border border-border overflow-hidden animate-in fade-in zoom-in-95 duration-200">
        <div className="flex items-center gap-3 px-4 py-3 border-b border-border">
          <Search size={20} className="text-muted-foreground shrink-0" />
          <input
            ref={inputRef}
            type="text"
            className="flex-1 bg-transparent border-none outline-none text-foreground placeholder:text-muted-foreground text-lg"
            placeholder="Buscar questão, tópico ou comando..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
          <kbd className="hidden sm:inline-block text-xs text-muted-foreground bg-muted px-1.5 py-0.5 rounded border border-border">ESC</kbd>
        </div>
        <div className="max-h-[60vh] overflow-y-auto p-2">
          {query.length === 0 ? (
            <div className="px-3 py-8 text-center text-muted-foreground text-sm">
              Tente buscar por &quot;Cardiologia&quot;, &quot;Simulado USP&quot; ou &quot;Revisão&quot;.
            </div>
          ) : loading && results.length === 0 ? (
            <div className="px-3 py-8 text-center text-muted-foreground text-sm flex items-center justify-center gap-2">
              <Loader2 size={16} className="animate-spin" /> Buscando...
            </div>
          ) : error ? (
            <div className="px-3 py-8 text-center text-destructive text-sm">
              Erro ao buscar. Tente novamente.
            </div>
          ) : (
            <div className="flex flex-col gap-1">
              <button 
                className="flex items-center gap-2 px-3 py-2 rounded-md hover:bg-muted text-left text-foreground transition-colors mb-2 border-b border-border pb-3"
                onClick={() => {
                  setOpen(false);
                  router.push(`/buscar?q=${encodeURIComponent(query)}`);
                }}
              >
                <Search size={16} className="text-muted-foreground shrink-0" />
                <span>Ver todos os resultados para &quot;{query}&quot;</span>
                <ArrowRight size={14} className="ml-auto opacity-50" />
              </button>
              
              {results.length > 0 ? (
                <>
                  <div className="px-3 py-1 text-xs font-semibold text-muted-foreground uppercase tracking-wider">Top Resultados</div>
                  {results.map((res) => (
                    <button
                      key={res.id}
                      className="flex flex-col gap-1.5 px-3 py-2.5 rounded-md hover:bg-muted text-left transition-colors"
                      onClick={() => {
                        setOpen(false);
                        router.push(`/estudar?id=${res.id}`);
                      }}
                    >
                      <div className="flex items-center gap-2 text-xs font-medium text-muted-foreground">
                        <span className="bg-primary/10 text-primary px-1.5 py-0.5 rounded">{res.institution_code} {res.year}</span>
                        <span>{res.subtema || res.area}</span>
                      </div>
                      <div 
                        className="text-sm text-foreground line-clamp-2 [&>mark]:bg-warning/30 [&>mark]:text-foreground [&>mark]:rounded-sm [&>mark]:px-0.5"
                        dangerouslySetInnerHTML={{ __html: res.stem_snippet }}
                      />
                    </button>
                  ))}
                </>
              ) : !loading && (
                <div className="px-3 py-8 text-center text-muted-foreground text-sm">
                  Nenhum resultado encontrado.
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
