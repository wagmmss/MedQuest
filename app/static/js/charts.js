// Gráficos SVG simples, sem dependências externas.

function svgEl(tag, attrs) {
  const el = document.createElementNS("http://www.w3.org/2000/svg", tag);
  for (const k in attrs) el.setAttribute(k, attrs[k]);
  return el;
}

function pct(n) {
  return Math.round(n * 100) + "%";
}

// Gráfico de barras horizontais: acurácia (0-1) por categoria, com rótulo e n de tentativas.
function renderBarChart(container, rows, { labelKey = "label", accKey = "accuracy", nKey = "attempts" } = {}) {
  container.innerHTML = "";
  if (!rows || rows.length === 0) {
    container.innerHTML = '<div class="empty-note">Sem dados suficientes ainda. Responda algumas questões para ver este gráfico.</div>';
    return;
  }
  const rowH = 34;
  const width = 640;
  const height = rows.length * rowH + 10;
  const labelW = 170;
  const barMaxW = width - labelW - 70;

  const svg = svgEl("svg", { viewBox: `0 0 ${width} ${height}`, role: "img" });

  rows.forEach((r, i) => {
    const y = i * rowH + 8;
    const barW = Math.max(2, r[accKey] * barMaxW);
    const color = r[accKey] >= 0.7 ? "var(--correct)" : r[accKey] >= 0.5 ? "var(--amber)" : "var(--wrong)";

    const label = svgEl("text", { x: 0, y: y + 14, "font-size": 12, fill: "var(--text)" });
    let labelText = String(r[labelKey] ?? "—");
    if (labelText.length > 24) labelText = labelText.slice(0, 23) + "…";
    label.textContent = labelText;
    svg.appendChild(label);

    const track = svgEl("rect", {
      x: labelW, y, width: barMaxW, height: 18, rx: 4, fill: "var(--surface-2)",
    });
    svg.appendChild(track);

    const bar = svgEl("rect", {
      x: labelW, y, width: barW, height: 18, rx: 4, fill: color,
    });
    svg.appendChild(bar);

    const valText = svgEl("text", {
      x: labelW + barMaxW + 8, y: y + 14, "font-size": 12, fill: "var(--text-muted)",
    });
    valText.textContent = `${pct(r[accKey])} (${r[nKey]})`;
    svg.appendChild(valText);
  });

  container.appendChild(svg);
}

// Gráfico de linha: evolução da acurácia ao longo do tempo (0-1 por dia).
function renderLineChart(container, rows, { xKey = "day", yKey = "accuracy", nKey = "attempts" } = {}) {
  container.innerHTML = "";
  if (!rows || rows.length < 2) {
    container.innerHTML = '<div class="empty-note">Continue estudando por alguns dias para ver a evolução aqui.</div>';
    return;
  }
  const width = 700, height = 220, pad = { top: 16, right: 16, bottom: 28, left: 36 };
  const plotW = width - pad.left - pad.right;
  const plotH = height - pad.top - pad.bottom;

  const svg = svgEl("svg", { viewBox: `0 0 ${width} ${height}` });

  // eixo y (0%, 50%, 100%)
  [0, 0.5, 1].forEach((v) => {
    const y = pad.top + plotH * (1 - v);
    svg.appendChild(svgEl("line", {
      x1: pad.left, x2: width - pad.right, y1: y, y2: y,
      stroke: "var(--border)", "stroke-width": 1,
    }));
    const t = svgEl("text", { x: 4, y: y + 4, "font-size": 10, fill: "var(--text-muted)" });
    t.textContent = pct(v);
    svg.appendChild(t);
  });

  const stepX = plotW / (rows.length - 1);
  const points = rows.map((r, i) => {
    const x = pad.left + i * stepX;
    const y = pad.top + plotH * (1 - r[yKey]);
    return [x, y];
  });

  const pathD = points.map((p, i) => (i === 0 ? "M" : "L") + p[0].toFixed(1) + "," + p[1].toFixed(1)).join(" ");
  svg.appendChild(svgEl("path", { d: pathD, fill: "none", stroke: "var(--primary)", "stroke-width": 2.5 }));

  points.forEach(([x, y], i) => {
    const c = svgEl("circle", { cx: x, cy: y, r: 3.5, fill: "var(--primary)" });
    const title = svgEl("title", {});
    title.textContent = `${rows[i][xKey]}: ${pct(rows[i][yKey])} (${rows[i][nKey]} questões)`;
    c.appendChild(title);
    svg.appendChild(c);
  });

  // rótulos de eixo x: primeiro, meio, último
  [0, Math.floor((rows.length - 1) / 2), rows.length - 1].forEach((idx) => {
    const t = svgEl("text", {
      x: points[idx][0], y: height - 6, "font-size": 10, fill: "var(--text-muted)", "text-anchor": "middle",
    });
    t.textContent = rows[idx][xKey];
    svg.appendChild(t);
  });

  container.appendChild(svg);
}
