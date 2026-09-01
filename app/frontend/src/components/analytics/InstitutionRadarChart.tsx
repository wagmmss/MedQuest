"use client";

import React, { useState } from "react";
import { RadarInstitutionData } from "@/types/api";
import clsx from "clsx";


interface InstitutionRadarChartProps {
  institution: RadarInstitutionData;
  comparison?: (RadarInstitutionData & { type: "global" | "institution" }) | null;
}

export function InstitutionRadarChart({
  institution,
  comparison,
}: InstitutionRadarChartProps) {
  const [hoveredIdx, setHoveredIdx] = useState<number | null>(null);

  const compMap = React.useMemo(() => {
    return new Map((comparison?.areas || []).map(a => [a.area, a]));
  }, [comparison]);

  const areas = institution.areas || [];

  // Chart dimensions
  const height = 240;
  const paddingLeft = 45;
  const paddingRight = 20;
  const paddingTop = 25;
  const paddingBottom = 40;
  const plotWidth = 500 - paddingLeft - paddingRight;
  const plotHeight = height - paddingTop - paddingBottom;

  const barGroupWidth = plotWidth / Math.max(1, areas.length);
  const primaryBarWidth = Math.min(28, barGroupWidth * 0.35);
  const compBarWidth = Math.min(22, barGroupWidth * 0.28);

  const getY = (val: number) => {
    const clamped = Math.max(0, Math.min(100, val));
    return paddingTop + plotHeight - (clamped / 100) * plotHeight;
  };

  const y70 = getY(70);

  return (
    <div className="w-full bg-card rounded-2xl border border-border p-5 flex flex-col gap-3 min-w-0">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-border/50 pb-3">
        <div>
          <h3 className="text-sm font-bold text-foreground">
            Acurácia e Intervalo de Incerteza (95% CI) por Área
          </h3>
          <p className="text-xs text-muted-foreground">
            As barras de erro representam a incerteza estatística de Wilson para cada grande área.
          </p>
        </div>
        <div className="flex items-center gap-4 text-xs">
          <div className="flex items-center gap-1.5 font-medium text-foreground">
            <span className="w-3 h-3 rounded-xs bg-primary inline-block" />
            <span>{institution.label}</span>
          </div>
          {comparison && (
            <div className="flex items-center gap-1.5 font-medium text-muted-foreground">
              <span className="w-3 h-3 rounded-xs bg-muted-foreground/40 inline-block" />
              <span>{comparison.type === "global" ? "Desempenho Geral" : comparison.label}</span>
            </div>
          )}
        </div>
      </div>

      {/* SVG Chart Container */}
      <div className="w-full relative overflow-hidden">
        <svg
          viewBox="0 0 500 240"
          className="w-full h-auto max-h-[300px] select-none"
          role="img"
          aria-label={`Gráfico de acurácia por área para ${institution.label}`}
        >
          {/* Grid lines */}
          {[0, 25, 50, 75, 100].map(level => {
            const y = getY(level);
            return (
              <g key={level}>
                <line
                  x1={paddingLeft}
                  y1={y}
                  x2={500 - paddingRight}
                  y2={y}
                  stroke="currentColor"
                  className="text-border/60"
                  strokeDasharray={level === 0 || level === 100 ? "none" : "3 3"}
                  strokeWidth="1"
                />
                <text
                  x={paddingLeft - 8}
                  y={y + 3}
                  textAnchor="end"
                  className="text-[10px] fill-muted-foreground font-mono"
                >
                  {level}%
                </text>
              </g>
            );
          })}

          {/* 70% Reference Line */}
          <line
            x1={paddingLeft}
            y1={y70}
            x2={500 - paddingRight}
            y2={y70}
            stroke="var(--warning)"
            strokeDasharray="4 3"
            strokeWidth="1.5"
            opacity="0.7"
          />
          <text
            x={500 - paddingRight - 4}
            y={y70 - 4}
            textAnchor="end"
            className="text-[9px] font-bold fill-warning"
          >
            Meta 70%
          </text>

          {/* Bars and Error Margins */}
          {areas.map((area, idx) => {
            const comp = compMap.get(area.area);
            const acc = area.accuracy !== null ? Math.round(area.accuracy * 100) : null;
            const compAcc = comp && comp.accuracy !== null ? Math.round(comp.accuracy * 100) : null;
            const ciLow = area.ci_lower !== null ? Math.round(area.ci_lower * 100) : null;
            const ciHigh = area.ci_upper !== null ? Math.round(area.ci_upper * 100) : null;

            const groupCenterX = paddingLeft + idx * barGroupWidth + barGroupWidth / 2;
            const primaryX = comparison ? groupCenterX - primaryBarWidth - 2 : groupCenterX - primaryBarWidth / 2;
            const compX = groupCenterX + 2;

            const primaryY = acc !== null ? getY(acc) : getY(0);
            const primaryH = acc !== null ? (height - paddingBottom - primaryY) : 0;

            const compY = compAcc !== null ? getY(compAcc) : getY(0);
            const compH = compAcc !== null ? (height - paddingBottom - compY) : 0;

            const isHovered = hoveredIdx === idx;
            const shortName = area.area
              .replace("Ginecologia e Obstetrícia", "G.O.")
              .replace("Medicina Preventiva", "Preventiva");

            return (
              <g
                key={area.area}
                className="cursor-pointer transition-opacity"
                onMouseEnter={() => setHoveredIdx(idx)}
                onMouseLeave={() => setHoveredIdx(null)}
              >
                {/* Hover Background Highlight */}
                {isHovered && (
                  <rect
                    x={paddingLeft + idx * barGroupWidth + 2}
                    y={paddingTop}
                    width={barGroupWidth - 4}
                    height={plotHeight}
                    fill="currentColor"
                    className="text-muted/30 rounded-lg"
                    rx="6"
                  />
                )}

                {/* Primary Bar */}
                {acc !== null && (
                  <rect
                    x={primaryX}
                    y={primaryY}
                    width={primaryBarWidth}
                    height={Math.max(2, primaryH)}
                    fill="var(--primary)"
                    rx="4"
                    className="transition-all"
                  />
                )}

                {/* Comparison Bar */}
                {comparison && compAcc !== null && (
                  <rect
                    x={compX}
                    y={compY}
                    width={compBarWidth}
                    height={Math.max(2, compH)}
                    fill="currentColor"
                    className="text-muted-foreground/35"
                    rx="3"
                  />
                )}

                {/* Wilson CI Error Bar (vertical line + caps) */}
                {ciLow !== null && ciHigh !== null && acc !== null && (
                  <g className="text-foreground">
                    <line
                      x1={primaryX + primaryBarWidth / 2}
                      y1={getY(ciHigh)}
                      x2={primaryX + primaryBarWidth / 2}
                      y2={getY(ciLow)}
                      stroke="currentColor"
                      strokeWidth="1.5"
                      className="text-foreground/80"
                    />
                    {/* Top tick */}
                    <line
                      x1={primaryX + primaryBarWidth / 2 - 4}
                      y1={getY(ciHigh)}
                      x2={primaryX + primaryBarWidth / 2 + 4}
                      y2={getY(ciHigh)}
                      stroke="currentColor"
                      strokeWidth="1.5"
                      className="text-foreground/80"
                    />
                    {/* Bottom tick */}
                    <line
                      x1={primaryX + primaryBarWidth / 2 - 4}
                      y1={getY(ciLow)}
                      x2={primaryX + primaryBarWidth / 2 + 4}
                      y2={getY(ciLow)}
                      stroke="currentColor"
                      strokeWidth="1.5"
                      className="text-foreground/80"
                    />
                  </g>
                )}

                {/* X Axis Label */}
                <text
                  x={groupCenterX}
                  y={height - paddingBottom + 16}
                  textAnchor="middle"
                  className={clsx(
                    "text-[10px] font-semibold transition-colors",
                    isHovered ? "fill-primary font-bold" : "fill-foreground"
                  )}
                >
                  {shortName}
                </text>
                <text
                  x={groupCenterX}
                  y={height - paddingBottom + 28}
                  textAnchor="middle"
                  className="text-[9px] fill-muted-foreground font-mono"
                >
                  {acc !== null ? `${acc}%` : "—"}
                </text>
              </g>
            );
          })}
        </svg>

        {/* Interactive Tooltip Card */}
        {hoveredIdx !== null && areas[hoveredIdx] && (
          <div className="mt-2 p-3 rounded-xl border border-border bg-card/95 backdrop-blur-xs text-xs space-y-1 shadow-md animate-in fade-in duration-200">
            <div className="flex items-center justify-between">
              <span className="font-bold text-foreground">{areas[hoveredIdx].area}</span>
              <span className="text-muted-foreground">Cobertura: {Math.round(areas[hoveredIdx].coverage * 100)}%</span>
            </div>
            <div className="flex flex-wrap items-center gap-4 text-xs pt-1 border-t border-border">
              <div>
                <span className="text-primary font-semibold">{institution.label}: </span>
                <span className="font-bold text-foreground">
                  {areas[hoveredIdx].accuracy !== null ? `${Math.round(areas[hoveredIdx].accuracy! * 100)}%` : "Sem tentativas"}
                </span>
                <span className="text-muted-foreground"> ({areas[hoveredIdx].attempts} tentativas)</span>
              </div>
              {areas[hoveredIdx].ci_lower !== null && areas[hoveredIdx].ci_upper !== null && (
                <div className="text-muted-foreground">
                  <span>95% CI: </span>
                  <span className="font-mono text-foreground font-semibold">
                    [{Math.round(areas[hoveredIdx].ci_lower! * 100)}% – {Math.round(areas[hoveredIdx].ci_upper! * 100)}%]
                  </span>
                </div>
              )}
              {comparison && compMap.get(areas[hoveredIdx].area) && (
                <div className="text-muted-foreground">
                  <span>{comparison.type === "global" ? "Desempenho Geral" : comparison.label}: </span>
                  <span className="font-semibold text-foreground">
                    {compMap.get(areas[hoveredIdx].area)!.accuracy !== null
                      ? `${Math.round(compMap.get(areas[hoveredIdx].area)!.accuracy! * 100)}%`
                      : "—"}
                  </span>
                </div>
              )}
            </div>
            {areas[hoveredIdx].sample_status === "insufficient" && (
              <p className="text-[11px] text-amber-600 dark:text-amber-400 font-medium pt-0.5">
                ⚠️ Amostra insuficiente (&lt; 20 tentativas). Alta incerteza estatística.
              </p>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
