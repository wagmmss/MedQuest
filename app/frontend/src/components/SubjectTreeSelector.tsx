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

  // Precompute the tree filtering out empty themes
  const tree = useMemo(() => {
    return plannerData.map(areaData => {
      const macroThemes = (areaData.macroThemes || []).map(macro => {
        // Only include details that have available questions (if availableSubtemas is provided)
        const activeDetails = (macro.dbSubtemas || []).filter(d => !availableSubtemas || availableMap.has(d));
        return {
          ...macro,
          activeDetails
        };
      }).filter(macro => macro.activeDetails.length > 0);
      
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
              {area.macroThemes.reduce((acc, m) => acc + m.activeDetails.length, 0)} tópicos
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
                const isDirectTheme = macro.activeDetails.length === 1 && macro.activeDetails[0] === macro.theme;
                const directThemeCount = isDirectTheme ? availableMap.get(macro.theme) || 0 : 0;
                
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
                            ref={input => {
                              if (input) input.indeterminate = selState === "partial";
                            }}
                            onChange={() => toggleThemeSelection(macro.activeDetails, selState)}
                          />
                          <div className={clsx(
                            "w-4 h-4 border border-muted-foreground/50 rounded transition-colors flex items-center justify-center group-hover:border-primary/50",
                            (selState === "all" || selState === "partial") ? "bg-primary border-primary" : "bg-card"
                          )}>
                            {selState === "all" && <Check size={12} className="text-primary-foreground" strokeWidth={4} />}
                            {selState === "partial" && <div className="w-2 h-0.5 bg-primary-foreground rounded-full" />}
                          </div>
                        </div>
                        <span className="text-sm font-semibold text-foreground/90 group-hover:text-foreground transition-colors flex-1 flex items-center gap-2">
                          {macro.theme}
                          {macro.highYield && <span title="Tema de Alto Rendimento" className="text-[10px]">🔥</span>}
                        </span>
                        {isDirectTheme && (
                          <span className="text-xs text-muted-foreground/60 shrink-0 tabular-nums">
                            {directThemeCount} q
                          </span>
                        )}
                      </label>
                    </div>
                    
                    {isExpanded && (
                      <div className="flex flex-col pl-12 pr-4 py-2 bg-muted/10 gap-1.5 border-t border-border/30">
                        {macro.activeDetails.map(detail => {
                          const count = availableMap.get(detail) || 0;
                          return (
                            <label key={detail} className="flex items-start gap-3 cursor-pointer group/item py-1">
                              <div className="relative flex items-center shrink-0 mt-0.5">
                                <input 
                                  type="checkbox"
                                  className="peer sr-only"
                                  checked={isDetailSelected(detail)}
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
                                {count} q
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
