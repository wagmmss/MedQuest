"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Search, Loader2, BookOpen, X } from "lucide-react";
import { api } from "@/lib/api";
import { SearchResult } from "@/types/api";

export function BuscarClient({ initialQuery }: { initialQuery: string }) {
  const [query, setQuery] = useState(initialQuery);
  const [semantic, setSemantic] = useState(true);
  const [results, setResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  useEffect(() => {
    if (!query.trim()) {
      const timer = setTimeout(() => {
        setResults([]);
      }, 0);
      return () => clearTimeout(timer);
    }

    let isMounted = true;
    const timer = setTimeout(async () => {
      if (isMounted) setLoading(true);
      try {
        const res = await api.questions.search(query, semantic);
        if (isMounted) setResults(res);
      } catch (e) {
        console.error(e);
      } finally {
        if (isMounted) setLoading(false);
      }
    }, semantic ? 1000 : 400);

    return () => {
      isMounted = false;
      clearTimeout(timer);
    };
  }, [query, semantic]);

  return (
    <div className="max-w-4xl mx-auto w-full flex flex-col gap-6 pb-12">
      {/* Top Search Header */}
      <div className="bg-card border border-border shadow-1 rounded-xl p-6 md:p-8 flex flex-col gap-6 text-center">
        <div className="w-16 h-16 bg-primary/20 text-primary rounded-2xl flex items-center justify-center mx-auto mb-2">
          <Search size={32} />
        </div>
        <div>
          <h2 className="text-h2 font-bold text-foreground mb-2">Busca de Questões</h2>
          <p className="text-muted-foreground">Pesquise por palavras-chave, temas, ou termos médicos.</p>
        </div>
        
        <div className="flex items-center justify-center gap-3 mt-2">
          <button 
            type="button"
            onClick={() => setSemantic(!semantic)}
            role="switch"
            aria-checked={semantic}
            aria-label="Alternar busca semântica"
            className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${semantic ? 'bg-primary' : 'bg-muted-foreground/30'}`}
          >
            <span className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${semantic ? 'translate-x-6' : 'translate-x-1'}`} />
          </button>
          <span className="text-sm font-medium text-foreground flex items-center gap-1">
            <span className="text-primary font-bold">✨</span> Busca Semântica (IA)
          </span>
        </div>
        
        <div className="relative max-w-2xl w-full mx-auto mt-2">
          <div className="absolute inset-y-0 left-4 flex items-center pointer-events-none">
            <Search size={20} className="text-muted-foreground" />
          </div>
          <input
            type="text"
            className="w-full bg-input border border-border rounded-full py-4 pl-12 pr-12 text-lg text-foreground focus:outline-none focus:ring-2 focus:ring-primary shadow-sm"
            placeholder="Digite para buscar..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            autoFocus
          />
          <div className="absolute inset-y-0 right-4 flex items-center gap-2">
            {loading && (
              <Loader2 size={20} className="text-primary animate-spin" />
            )}
            {query.length > 0 && !loading && (
              <button
                type="button"
                onClick={() => setQuery("")}
                className="p-1 rounded-full hover:bg-muted transition-colors text-muted-foreground hover:text-foreground"
                aria-label="Limpar busca"
              >
                <X size={18} />
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Results Section */}
      {query.trim().length > 0 && (
        <div className="flex flex-col gap-4">
          <div className="text-sm font-medium text-muted-foreground px-2">
            {loading ? "Buscando..." : `${results.length} resultados encontrados para "${query}"`}
          </div>
          
          <div className="flex flex-col gap-4">
            {results.map((res) => (
              <Link 
                key={res.id}
                href={`/estudar?id=${res.id}`}
                className="bg-card border border-border shadow-sm rounded-xl p-5 hover:border-primary/50 hover:shadow-md cursor-pointer transition-all flex flex-col gap-3 group"
              >
                <div className="flex flex-wrap items-center gap-2 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                  <span className="bg-primary/10 text-primary px-2 py-1 rounded">{res.institution_code} {res.year}</span>
                  <span className="bg-muted px-2 py-1 rounded">{res.area}</span>
                  <span className="bg-muted px-2 py-1 rounded">{res.subtema}</span>
                </div>
                
                <div 
                  className="text-foreground text-body-m leading-relaxed [&>mark]:bg-warning/30 [&>mark]:text-foreground [&>mark]:rounded-sm [&>mark]:px-0.5 group-hover:text-primary transition-colors"
                  dangerouslySetInnerHTML={{ __html: res.stem_snippet }}
                />
                
                {res.exp_snippet && (
                  <div className="mt-2 bg-muted/50 rounded-lg p-3 text-sm text-muted-foreground flex items-start gap-2 border border-border/50">
                    <BookOpen size={16} className="shrink-0 mt-0.5 opacity-70" />
                    <div 
                      className="line-clamp-2 [&>mark]:bg-warning/30 [&>mark]:text-foreground [&>mark]:rounded-sm [&>mark]:px-0.5"
                      dangerouslySetInnerHTML={{ __html: res.exp_snippet }}
                    />
                  </div>
                )}
              </Link>
            ))}
            
            {!loading && results.length === 0 && (
              <div className="bg-card border border-border border-dashed shadow-sm rounded-xl p-16 text-center flex flex-col items-center justify-center gap-4 animate-in fade-in zoom-in-95 duration-500">
                <div className="w-20 h-20 bg-muted/50 rounded-full flex items-center justify-center mb-2">
                  <Search size={32} className="text-muted-foreground/50" />
                </div>
                <h3 className="text-xl font-bold text-foreground">Nenhuma questão encontrada</h3>
                <p className="text-muted-foreground text-base max-w-md">
                  Não encontramos resultados para "<strong className="text-foreground">{debouncedQuery}</strong>". 
                  Tente usar palavras-chave mais curtas, remover filtros ou buscar por sinônimos.
                </p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
