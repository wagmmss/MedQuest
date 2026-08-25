import React, { useState, useMemo } from "react";
import { ChevronRight, ChevronDown, Check } from "lucide-react";
import clsx from "clsx";
import { plannerData } from "@/lib/plannerData";

interface SubjectTreeSelectorProps {
  selectedSubtemas: string[];
  onChange: (newSelection: string[]) => void;
  availableSubtemas?: { subtema: string; n: number }[];
}

export function SubjectTreeSelector({ selectedSubtemas, onChange, availableSubtemas }: SubjectTreeSelectorProps) {
  const [expandedAreas, setExpandedAreas] = useState<Record<string, boolean>>({});
  const [expandedThemes, setExpandedThemes] = useState<Record<string, boolean>>({});

  // Map of available subtemas and their counts
  const availableMap = useMemo(() => {
    const map = new Map<string, number>();
    if (availableSubtemas) {
      availableSubtemas.forEach(s => map.set(s.subtema, s.n));
    }
    return map;
  }, [availableSubtemas]);

  // Keep the complete curricular tree visible. Previously, themes without
  // questions in the current filter were removed altogether, which made the
  // catalogue look incomplete and hid useful study-plan context.
  const tree = useMemo(() => {
    return plannerData.map(areaData => {
      const macroThemes = (areaData.macroThemes || []).map(macro => {
        const details = macro.dbSubtemas || [];
        // These are the only details that can be selected: selecting an
        // unavailable one would start an empty session.
        const activeDetails = details.filter(d => !availableSubtemas || availableMap.has(d));
        return {
          ...macro,
          details,
          activeDetails
        };
      });
      
      return {
        ...areaData,
        macroThemes
      };
    }).filter(areaData => areaData.macroThemes.length > 0);
  }, [availableMap, availableSubtemas]);

  const toggleArea = (area: string) => {
    setExpandedAreas(prev => ({ ...prev, [area]: !prev[area] }));
  };

  const toggleTheme = (theme: string) => {
    setExpandedThemes(prev => ({ ...prev, [theme]: !prev[theme] }));
  };

  const isDetailSelected = (detail: string) => selectedSubtemas.includes(detail);

  const getThemeSelectionState = (details: string[]) => {
    if (details.length === 0) return "none";
    const selectedCount = details.filter(isDetailSelected).length;
    if (selectedCount === 0) return "none";
    if (selectedCount === details.length) return "all";
    return "partial";
  };

  const toggleDetail = (detail: string) => {
    if (isDetailSelected(detail)) {
      onChange(selectedSubtemas.filter(s => s !== detail));
    } else {
      onChange([...selectedSubtemas, detail]);
    }
  };

  const toggleThemeSelection = (details: string[], currentState: "none" | "partial" | "all") => {
    if (currentState === "all") {
      // Deselect all
      onChange(selectedSubtemas.filter(s => !details.includes(s)));
    } else {
      // Select all active details
      const newSelection = new Set([...selectedSubtemas, ...details]);
      onChange(Array.from(newSelection));
    }
  };

  if (tree.length === 0) {
    return (
      <div className="text-sm text-muted-foreground p-4 text-center bg-muted/20 rounded-lg border border-border mt-3">
        Nenhum tema disponível com questões para os filtros selecionados.
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-2 mt-3 max-h-[500px] overflow-y-auto overscroll-contain pr-2 custom-scrollbar">
      {tree.map(area => (
        <div key={area.area} className="shrink-0 border border-border rounded-lg overflow-hidden bg-card">
          <div 
            className="flex items-center gap-2 px-4 py-3 bg-muted/30 cursor-pointer hover:bg-muted/50 transition-colors select-none"
            onClick={() => toggleArea(area.area)}
          >
            {expandedAreas[area.area] ? <ChevronDown size={18} /> : <ChevronRight size={18} />}
            <span className="font-bold text-foreground text-sm uppercase tracking-wider">{area.area}</span>
            <span className="ml-auto text-xs font-semibold bg-background px-2 py-1 rounded border border-border">
              {area.macroThemes.reduce((acc, m) => acc + m.details.length, 0)} tópicos
            </span>
          </div>
          
          {expandedAreas[area.area] && (
            <div className="flex flex-col border-t border-border bg-background">
              {area.macroThemes.map(macro => {
                const selState = getThemeSelectionState(macro.activeDetails);
                const themeKey = `${area.area}::${macro.theme}`;
                const isExpanded = expandedThemes[themeKey];
                // A theme that maps to itself has no useful child level. Render it
                // as a selectable leaf instead of showing the same name twice.
                const isDirectTheme = macro.details.length === 1 && macro.details[0] === macro.theme;
                const directThemeCount = isDirectTheme ? availableMap.get(macro.theme) || 0 : 0;
                const hasAvailableDetails = macro.activeDetails.length > 0;
                
                return (
                  <div key={macro.theme} className="border-b border-border last:border-0">
                    <div className="flex items-center gap-2 px-4 py-2 hover:bg-muted/20 transition-colors">
                      {isDirectTheme ? (
                        <div className="w-6 shrink-0" aria-hidden="true" />
                      ) : (
                        <button
                          type="button"
                          className="cursor-pointer p-1 text-muted-foreground hover:text-foreground"
                          onClick={() => toggleTheme(themeKey)}
                          aria-label={isExpanded ? `Recolher ${macro.theme}` : `Expandir ${macro.theme}`}
                        >
                          {isExpanded ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
                        </button>
                      )}
                      
                      <label className="flex items-center gap-3 flex-1 cursor-pointer select-none group py-1">
                        <div className="relative flex items-center shrink-0">
                          <input 
                            type="checkbox"
                            className="sr-only peer"
                            checked={selState === "all"}
                            disabled={!hasAvailableDetails}
                            ref={input => {
                              if (input) input.indeterminate = selState === "partial";
                            }}
                            onChange={() => toggleThemeSelection(macro.activeDetails, selState)}
                          />
                          <div className={clsx(
                            "w-4 h-4 border border-muted-foreground/50 rounded transition-colors flex items-center justify-center group-hover:border-primary/50",
                            (selState === "all" || selState === "partial") ? "bg-primary border-primary" : "bg-card",
                            !hasAvailableDetails && "opacity-40"
                          )}>
                            {selState === "all" && <Check size={12} className="text-primary-foreground" strokeWidth={4} />}
                            {selState === "partial" && <div className="w-2 h-0.5 bg-primary-foreground rounded-full" />}
                          </div>
                        </div>
                        <span className={clsx(
                          "text-sm font-semibold transition-colors flex-1 flex items-center gap-2",
                          hasAvailableDetails ? "text-foreground/90 group-hover:text-foreground" : "text-muted-foreground/60"
                        )}>
                          {macro.theme}
                          {macro.highYield && <span title="Tema de Alto Rendimento" className="text-[10px]">🔥</span>}
                        </span>
                        {isDirectTheme && (
                          <span className="text-xs text-muted-foreground/60 shrink-0 tabular-nums">
                            {directThemeCount > 0 ? `${directThemeCount} q` : "Sem questões"}
                          </span>
                        )}
                      </label>
                    </div>
                    
                    {isExpanded && (
                      <div className="flex flex-col pl-12 pr-4 py-2 bg-muted/10 gap-1.5 border-t border-border/30">
                        {macro.details.map(detail => {
                          const count = availableMap.get(detail) || 0;
                          const isAvailable = !availableSubtemas || availableMap.has(detail);
                          return (
                            <label key={detail} className={clsx(
                              "flex items-start gap-3 py-1",
                              isAvailable ? "cursor-pointer group/item" : "cursor-not-allowed opacity-50"
                            )}>
                              <div className="relative flex items-center shrink-0 mt-0.5">
                                <input 
                                  type="checkbox"
                                  className="peer sr-only"
                                  checked={isDetailSelected(detail)}
                                  disabled={!isAvailable}
                                  onChange={() => toggleDetail(detail)}
                                />
                                <div className="w-4 h-4 border border-muted-foreground/30 rounded-sm transition-colors peer-checked:bg-primary peer-checked:border-primary flex items-center justify-center group-hover/item:border-primary/50">
                                  <Check size={10} className={clsx("text-primary-foreground transition-opacity", isDetailSelected(detail) ? "opacity-100" : "opacity-0")} strokeWidth={4} />
                                </div>
                              </div>
                              <span className={clsx(
                                "text-sm transition-colors flex-1",
                                isDetailSelected(detail) ? "text-foreground font-medium" : "text-muted-foreground"
                              )}>
                                {detail}
                              </span>
                              <span className="text-xs text-muted-foreground/60 shrink-0 tabular-nums mt-0.5">
                                {count > 0 ? `${count} q` : "Sem questões"}
                              </span>
                            </label>
                          );
                        })}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
