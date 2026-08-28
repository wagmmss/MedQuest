"use client";

import React from "react";
import { Maximize } from "lucide-react";

interface FormattedContentProps {
  content: string;
  className?: string;
  onImageClick?: (url: string) => void;
}

export function normalizeImageSrc(url: string | null | undefined): string {
  if (!url) return "";
  let src = url.trim().replace(/^\/api\/images\/images\//, "/api/images/");
  src = src
    .replace(/MedQuest-assets\.s3\.sa-east-1\.amazonaws\.com/gi, "medcof-assets.s3.sa-east-1.amazonaws.com")
    .replace(/MedQuest-assets\.s3\.amazonaws\.com/gi, "medcof-assets.s3.amazonaws.com")
    .replace(/cdn\.MedQuest\.com\.br/gi, "cdn.medway.com.br")
    .replace(/www\.MedQuest\.com\.br/gi, "www.medway.com.br");
  if (!src.startsWith("http://") && !src.startsWith("https://") && !src.startsWith("/api/") && !src.startsWith("/")) {
    src = `/api/images/${src}`;
  }
  return src;
}

/**
 * Extracts all image URLs/filenames referenced in a markdown text.
 */
export function extractImageUrlsFromMarkdown(text: string | null | undefined): Set<string> {
  const set = new Set<string>();
  if (!text) return set;
  const matches = Array.from(text.matchAll(/!\[.*?\]\((.*?)\)|<img\b[^>]*\bsrc=['"]([^'"]+)['"]/gi));
  for (const m of matches) {
    const raw = (m[1] || m[2] || "").trim();
    if (raw) {
      set.add(raw);
      set.add(normalizeImageSrc(raw));
      const fn = raw.split("/").pop();
      if (fn) set.add(fn);
    }
  }
  return set;
}

/**
 * Filters an array of images, removing those already embedded in the markdown text.
 */
export function filterExtraImages(images: string[] | null | undefined, text: string | null | undefined): string[] {
  if (!images || !Array.isArray(images) || images.length === 0) return [];
  const textImages = extractImageUrlsFromMarkdown(text);
  if (textImages.size === 0) return images;

  return images.filter(img => {
    if (!img) return false;
    const trimmed = img.trim();
    const normalized = normalizeImageSrc(trimmed);
    const fn = trimmed.split("/").pop() || "";
    if (textImages.has(trimmed) || textImages.has(normalized) || (fn && textImages.has(fn))) {
      return false;
    }
    for (const tImg of Array.from(textImages)) {
      if (tImg.includes(trimmed) || trimmed.includes(tImg) || (fn && tImg.includes(fn))) {
        return false;
      }
    }
    return true;
  });
}

/**
 * Parses inline formatting: bold (**text**), italic (*text*), math ($math$), links ([text](url)), and inline images.
 */
function renderInline(
  text: string,
  onImageClick?: (url: string) => void
): React.ReactNode {
  // Regex to match images, bold, math, links
  const tokenRegex = /(!\[.*?\]\(.*?\)|<img\b[^>]*\bsrc\s*=\s*['"][^'"]+['"][^>]*>|\*\*.*?\*\*|\$[^\$]+\$|\[.*?\]\(.*?\))/g;
  const parts = text.split(tokenRegex);

  return parts.map((part, idx) => {
    if (!part) return null;

    // 1. Markdown Image: ![alt](url)
    const mdImgMatch = part.match(/^!\[(.*?)\]\((.*?)\)$/);
    if (mdImgMatch) {
      const alt = mdImgMatch[1];
      const src = normalizeImageSrc(mdImgMatch[2]);
      const isFileNameAlt = !alt || /\.(png|jpe?g|webp|gif|svg|blob)$/i.test(alt) || /^(image|figura|blob|imagem)$/i.test(alt) || alt === "Figura Explicativa";
      return (
        <span key={idx} className="block my-3 text-center">
          <span 
            className="inline-block relative group rounded-xl overflow-hidden border border-border bg-muted/20 cursor-zoom-in hover:shadow-md transition-all max-w-full"
            onClick={() => onImageClick && onImageClick(src)}
          >
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img 
              src={src} 
              alt={alt || "Figura"} 
              className="w-full h-auto object-contain max-h-[350px] mx-auto hover:scale-[1.02] transition-transform duration-300 rounded-lg"
            />
            <span className="absolute inset-0 bg-black/0 group-hover:bg-black/10 transition-colors flex items-center justify-center pointer-events-none">
              <Maximize size={20} className="text-white opacity-0 group-hover:opacity-100 transition-opacity drop-shadow-md" />
            </span>
          </span>
          {!isFileNameAlt && (
            <span className="block text-xs text-muted-foreground mt-1 text-center italic">{alt}</span>
          )}
        </span>
      );
    }

    // 2. HTML Image: <img src="..." />
    const htmlImgMatch = part.match(/<img\b[^>]*\bsrc\s*=\s*['"]([^'"]+)['"][^>]*>/i);
    if (htmlImgMatch) {
      const src = normalizeImageSrc(htmlImgMatch[1]);
      return (
        <span key={idx} className="block my-3 text-center">
          <span 
            className="inline-block relative group rounded-xl overflow-hidden border border-border bg-muted/20 cursor-zoom-in hover:shadow-md transition-all max-w-full"
            onClick={() => onImageClick && onImageClick(src)}
          >
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img 
              src={src} 
              alt="Figura" 
              className="w-full h-auto object-contain max-h-[350px] mx-auto hover:scale-[1.02] transition-transform duration-300 rounded-lg"
            />
            <span className="absolute inset-0 bg-black/0 group-hover:bg-black/10 transition-colors flex items-center justify-center pointer-events-none">
              <Maximize size={20} className="text-white opacity-0 group-hover:opacity-100 transition-opacity drop-shadow-md" />
            </span>
          </span>
        </span>
      );
    }

    // 3. Bold: **text**
    if (part.startsWith("**") && part.endsWith("**")) {
      const inner = part.slice(2, -2);
      // If bold wraps an image, recurse to render the image properly
      if (inner.includes("![") || inner.includes("<img")) {
        return <React.Fragment key={idx}>{renderInline(inner, onImageClick)}</React.Fragment>;
      }
      return (
        <strong key={idx} className="font-bold text-foreground">
          {inner}
        </strong>
      );
    }

    // 4. Math: $math$
    if (part.startsWith("$") && part.endsWith("$")) {
      return (
        <span key={idx} className="font-mono italic px-1 bg-muted/60 rounded text-sm text-primary">
          {part.slice(1, -1)}
        </span>
      );
    }

    // 5. Link: [text](url)
    const linkMatch = part.match(/^\[(.*?)\]\((.*?)\)$/);
    if (linkMatch) {
      return (
        <a 
          key={idx} 
          href={linkMatch[2]} 
          target="_blank" 
          rel="noopener noreferrer" 
          className="text-primary underline hover:text-primary/80 transition-colors"
        >
          {linkMatch[1]}
        </a>
      );
    }

    return <React.Fragment key={idx}>{part}</React.Fragment>;
  });
}

export function preprocessMarkdown(content: string): string {
  if (!content) return "";
  let raw = content.replace(/\\n/g, "\n");
  // Unwrap **![]()** or **<img>**
  raw = raw.replace(/\*\*(!\[.*?\]\(.*?\))\*\*/g, "\n\n$1\n\n");
  raw = raw.replace(/\*\*(<img\b[^>]*>)\*\*/g, "\n\n$1\n\n");
  raw = raw.replace(/\/api\/images\/images\//g, "/api/images/").trim();

  // 1. Convert HTML tables if any exist
  raw = raw.replace(/<table\b[^>]*>[\s\S]*?<\/table>/gi, (tableHtml) => {
    const t = tableHtml.replace(/<\/?(?:table|tbody|thead)[^>]*>/gi, "");
    const trMatches = Array.from(t.matchAll(/<tr[^>]*>([\s\S]*?)<\/tr>/gi));
    const rows: string[] = [];
    if (trMatches.length > 0) {
      for (const tr of trMatches) {
        const cellsStr = tr[1].replace(/\s*\n\s*/g, " ").trim();
        if (cellsStr.includes("|")) {
          const parts = cellsStr.split("|").map(p => p.trim()).filter(Boolean);
          rows.push("| " + parts.join(" | ") + " |");
        } else {
          const tds = Array.from(cellsStr.matchAll(/<(?:td|th)[^>]*>([\s\S]*?)<\/(?:td|th)>/gi));
          if (tds.length > 0) {
            rows.push("| " + tds.map(td => td[1].trim()).join(" | ") + " |");
          }
        }
      }
    }
    if (rows.length > 0) {
      const colsCount = (rows[0].match(/\|/g) || []).length - 1;
      const hasSep = rows.some(r => /^\|\s*[-:\s|]+\s*\|$/.test(r));
      if (!hasSep) {
        const sepRow = "| " + Array(Math.max(1, colsCount)).fill("---").join(" | ") + " |";
        rows.splice(1, 0, sepRow);
      }
      return "\n\n" + rows.join("\n") + "\n\n";
    }
    return tableHtml;
  });

  // 2. Convert HTML headings
  raw = raw.replace(/<h1\b[^>]*>(.*?)<\/h1>/gi, "\n# $1\n");
  raw = raw.replace(/<h2\b[^>]*>(.*?)<\/h2>/gi, "\n## $1\n");
  raw = raw.replace(/<h3\b[^>]*>(.*?)<\/h3>/gi, "\n### $1\n");
  raw = raw.replace(/<h4\b[^>]*>(.*?)<\/h4>/gi, "\n#### $1\n");
  raw = raw.replace(/<h5\b[^>]*>(.*?)<\/h5>/gi, "\n##### $1\n");
  raw = raw.replace(/<h6\b[^>]*>(.*?)<\/h6>/gi, "\n###### $1\n");

  // 3. Convert HTML formatting to Markdown
  raw = raw.replace(/<(?:strong|b)\b[^>]*>(.*?)<\/(?:strong|b)>/gis, "**$1**");
  raw = raw.replace(/<(?:em|i)\b[^>]*>(.*?)<\/(?:em|i)>/gis, "*$1*");
  raw = raw.replace(/<p\b[^>]*>(.*?)<\/p>/gis, "\n\n$1\n\n");
  raw = raw.replace(/<br\s*\/?>/gi, "\n");
  raw = raw.replace(/<li\b[^>]*>(.*?)<\/li>/gis, "\n* $1");
  raw = raw.replace(/<\/?(?:ul|ol)\b[^>]*>/gi, "\n");
  raw = raw.replace(/<\/?(?:span|div|section|article|font|center)\b[^>]*>/gi, "");

  // 4. HTML Entities
  raw = raw
    .replace(/&nbsp;/gi, " ")
    .replace(/&gt;/gi, ">")
    .replace(/&lt;/gi, "<")
    .replace(/&quot;/gi, '"')
    .replace(/&#39;/gi, "'")
    .replace(/&amp;/gi, "&");

  // 5. Clean up boilerplate greetings
  raw = raw.replace(/Bons estudos!Com carinho,\s*equipe pedag[oó]gica/gi, "");

  return raw;
}

/**
 * Robust markdown block parser supporting tables (Katomart-style), headings, lists, quotes, and paragraphs.
 */
export function FormattedContent({ content, className = "", onImageClick }: FormattedContentProps) {
  if (!content) return null;

  const raw = preprocessMarkdown(content);
  const lines = raw.split("\n");

  const blocks: React.ReactNode[] = [];
  let currentParagraph: string[] = [];
  let tableRows: string[][] = [];
  let tableHasHeader = false;
  let listItems: string[] = [];
  let listType: "ul" | "ol" | null = null;

  const flushParagraph = () => {
    if (currentParagraph.length > 0) {
      const text = currentParagraph.join("\n").trim();
      if (text) {
        blocks.push(
          <p key={`p-${blocks.length}`} className="leading-relaxed">
            {renderInline(text, onImageClick)}
          </p>
        );
      }
      currentParagraph = [];
    }
  };

  const flushList = () => {
    if (listItems.length > 0 && listType) {
      const items = [...listItems];
      const isOrdered = listType === "ol";
      blocks.push(
        isOrdered ? (
          <ol key={`list-${blocks.length}`} className="list-decimal pl-5 space-y-1 leading-relaxed">
            {items.map((item, idx) => (
              <li key={idx}>{renderInline(item, onImageClick)}</li>
            ))}
          </ol>
        ) : (
          <ul key={`list-${blocks.length}`} className="list-disc pl-5 space-y-1 leading-relaxed">
            {items.map((item, idx) => (
              <li key={idx}>{renderInline(item, onImageClick)}</li>
            ))}
          </ul>
        )
      );
      listItems = [];
      listType = null;
    }
  };

  const flushTable = () => {
    if (tableRows.length > 0) {
      const rows = [...tableRows];
      const headerRow = tableHasHeader ? rows[0] : null;
      const bodyRows = tableHasHeader ? rows.slice(1) : rows;

      blocks.push(
        <div key={`table-${blocks.length}`} className="my-4 overflow-x-auto rounded-xl border border-border bg-card/50 shadow-sm">
          <table className="w-full text-left text-sm md:text-base border-collapse">
            {headerRow && (
              <thead className="bg-muted/80 text-foreground font-semibold border-b border-border">
                <tr>
                  {headerRow.map((cell, ci) => (
                    <th key={ci} className="px-4 py-3 border-r border-border last:border-r-0 font-bold">
                      {renderInline(cell, onImageClick)}
                    </th>
                  ))}
                </tr>
              </thead>
            )}
            <tbody className="divide-y divide-border">
              {bodyRows.map((row, ri) => (
                <tr key={ri} className="hover:bg-muted/30 transition-colors">
                  {row.map((cell, ci) => (
                    <td key={ci} className="px-4 py-2.5 border-r border-border last:border-r-0">
                      {renderInline(cell, onImageClick)}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      );
      tableRows = [];
      tableHasHeader = false;
    }
  };

  for (let i = 0; i < lines.length; i++) {
    const rawLine = lines[i];
    const line = rawLine.trim();

    if (!line) {
      flushParagraph();
      flushList();
      flushTable();
      continue;
    }

    // 1. Table Row: starts with |
    if (line.startsWith("|")) {
      flushParagraph();
      flushList();

      const cells = line
        .replace(/^\|/, "")
        .replace(/\|$/, "")
        .split("|")
        .map(c => c.trim());

      // Check if separator row (e.g. |---|---|)
      if (cells.every(c => /^:?-{3,}:?$/.test(c))) {
        tableHasHeader = true;
      } else {
        tableRows.push(cells);
      }
      continue;
    } else {
      flushTable();
    }

    // 2. Heading: ### Heading
    const headingMatch = line.match(/^(#{1,6})\s+(.+)$/);
    if (headingMatch) {
      flushParagraph();
      flushList();
      const level = headingMatch[1].length;
      const text = headingMatch[2];
      const Tag = level === 1 ? "h2" : level === 2 ? "h3" : "h4";
      blocks.push(
        <Tag key={`h-${blocks.length}`} className="font-bold text-foreground mt-4 mb-2">
          {renderInline(text, onImageClick)}
        </Tag>
      );
      continue;
    }

    // 3. Bullet List: - or *
    const bulletMatch = line.match(/^[-*•]\s+(.+)$/);
    if (bulletMatch) {
      flushParagraph();
      if (listType !== "ul") {
        flushList();
        listType = "ul";
      }
      listItems.push(bulletMatch[1]);
      continue;
    }

    // 4. Numbered List: 1.
    const numMatch = line.match(/^\d+[.)]\s+(.+)$/);
    if (numMatch) {
      flushParagraph();
      if (listType !== "ol") {
        flushList();
        listType = "ol";
      }
      listItems.push(numMatch[1]);
      continue;
    }

    // 5. Blockquote: >
    const quoteMatch = line.match(/^>\s*(.+)$/);
    if (quoteMatch) {
      flushParagraph();
      flushList();
      blocks.push(
        <blockquote key={`quote-${blocks.length}`} className="border-l-4 border-primary/40 pl-4 italic text-muted-foreground my-2">
          {renderInline(quoteMatch[1], onImageClick)}
        </blockquote>
      );
      continue;
    }

    // 6. Regular paragraph line
    flushList();
    currentParagraph.push(rawLine);
  }

  flushParagraph();
  flushList();
  flushTable();

  return <div className={`space-y-3 ${className}`}>{blocks}</div>;
}
