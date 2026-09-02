/**
 * Cliente TypeScript para integração local com AnkiConnect (http://127.0.0.1:8765).
 * Permite listar baralhos locais e importar notas diretamente no MedQuest.
 */

export interface AnkiConnectNote {
  noteId: number;
  modelName: string;
  tags: string[];
  fields: Record<string, { value: string; order: number }>;
}

export interface AnkiExtractedCard {
  front: string;
  back: string;
  deck_name: string;
  tags: string[];
  anki_nid: number;
}

export interface AnkiConnectOptions {
  url?: string;
  apiKey?: string;
}

export const DEFAULT_ANKICONNECT_URL = "http://127.0.0.1:8765";
export const FALLBACK_ANKICONNECT_URL = "http://localhost:8765";

export async function ankiConnectInvoke<T>(
  action: string,
  params: Record<string, unknown> = {},
  options?: AnkiConnectOptions
): Promise<T> {
  const url = options?.url || DEFAULT_ANKICONNECT_URL;
  const bodyPayload: Record<string, unknown> = {
    action,
    version: 6,
    params,
  };
  if (options?.apiKey?.trim()) {
    bodyPayload.key = options.apiKey.trim();
  }

  // 1. Tenta chamada direta ao AnkiConnect local
  try {
    const res = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(bodyPayload),
      signal: AbortSignal.timeout(4000),
    });

    if (res.ok) {
      const data = await res.json();
      if (data.error) {
        throw new Error(data.error);
      }
      return data.result as T;
    }
  } catch (directErr) {
    // Se não for erro de autenticação explícito, tenta o proxy do servidor
    const errMsg = String(directErr);
    if (errMsg.toLowerCase().includes("valid api key")) {
      throw directErr;
    }
  }

  // 2. Fallback automático para o proxy server-side do Next.js (bypassa CORS e PNA)
  try {
    const proxyRes = await fetch("/api/ankiconnect/proxy", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        ...bodyPayload,
        url,
      }),
      signal: AbortSignal.timeout(6000),
    });

    if (proxyRes.ok) {
      const data = await proxyRes.json();
      if (data.error) {
        throw new Error(data.error);
      }
      return data.result as T;
    }
  } catch {
    // continua para o fallback final
  }

  // 3. Fallback para o backend Flask
  const flaskProxyRes = await fetch("/api/flashcards/ankiconnect/proxy", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      ...bodyPayload,
      url,
    }),
    signal: AbortSignal.timeout(6000),
  });

  if (!flaskProxyRes.ok) {
    let errDetail = flaskProxyRes.statusText;
    try {
      const j = await flaskProxyRes.json();
      if (j.error) errDetail = j.error;
    } catch {
      // ignore
    }
    throw new Error(`Falha ao conectar ao AnkiConnect: ${errDetail}`);
  }

  const flaskData = await flaskProxyRes.json();
  if (flaskData.error) {
    throw new Error(flaskData.error);
  }

  return flaskData.result as T;
}

export async function checkAnkiConnect(
  options?: AnkiConnectOptions
): Promise<{
  connected: boolean;
  version?: number;
  activeUrl?: string;
  error?: string;
  errorType?: "cors" | "connection_refused" | "auth" | "unknown";
}> {
  const primaryUrl = options?.url || DEFAULT_ANKICONNECT_URL;
  const urlsToTry = [primaryUrl];
  if (!options?.url && primaryUrl !== FALLBACK_ANKICONNECT_URL) {
    urlsToTry.push(FALLBACK_ANKICONNECT_URL);
  }

  let lastError = "";
  for (const url of urlsToTry) {
    try {
      const version = await ankiConnectInvoke<number>("version", {}, { ...options, url });
      return { connected: true, version, activeUrl: url };
    } catch (err) {
      lastError = err instanceof Error ? err.message : String(err);
      if (lastError.toLowerCase().includes("valid api key") || lastError.toLowerCase().includes("api key")) {
        return {
          connected: false,
          activeUrl: url,
          error: "Chave de API necessária ou inválida no AnkiConnect.",
          errorType: "auth",
        };
      }
    }
  }

  const isCorsOrRefused = lastError.includes("Failed to fetch") || lastError.includes("NetworkError") || lastError.includes("Network request failed");
  return {
    connected: false,
    error: lastError || "Não foi possível conectar ao AnkiConnect",
    errorType: isCorsOrRefused ? "cors" : "unknown",
  };
}

export async function getAnkiDecks(options?: AnkiConnectOptions): Promise<string[]> {
  const decks = await ankiConnectInvoke<string[]>("deckNames", {}, options);
  return (decks || []).filter(d => d !== "Default");
}

function cleanHtml(html: string): string {
  if (!html) return "";
  let s = html;
  s = s.replace(/<!--[\s\S]*?-->/g, "");
  s = s.replace(/<br\s*\/?>/gi, "\n");
  s = s.replace(/<\/p>/gi, "\n\n");
  s = s.replace(/<\/div>/gi, "\n");
  s = s.replace(/<\/li>/gi, "\n");
  s = s.replace(/<li[^>]*>/gi, "• ");
  s = s.replace(/<b\b[^>]*>(.*?)<\/b>/gi, "**$1**");
  s = s.replace(/<strong\b[^>]*>(.*?)<\/strong>/gi, "**$1**");
  s = s.replace(/<i\b[^>]*>(.*?)<\/i>/gi, "*$1*");
  s = s.replace(/<em\b[^>]*>(.*?)<\/em>/gi, "*$1*");
  s = s.replace(/<[^>]+>/g, "");
  s = s.replace(/&nbsp;/g, " ");
  s = s.replace(/&amp;/g, "&");
  s = s.replace(/&lt;/g, "<");
  s = s.replace(/&gt;/g, ">");
  s = s.replace(/&quot;/g, '"');
  s = s.replace(/&#39;/g, "'");
  s = s.replace(/\r\n|\r/g, "\n");
  s = s.replace(/\n{3,}/g, "\n\n");
  return s.trim();
}

export async function fetchDeckCards(
  deckName: string,
  maxNotes: number = 500,
  options?: AnkiConnectOptions
): Promise<AnkiExtractedCard[]> {
  const query = `deck:"${deckName}"`;
  const noteIds = await ankiConnectInvoke<number[]>("findNotes", { query }, options);

  if (!noteIds || noteIds.length === 0) {
    return [];
  }

  const selectedIds = noteIds.slice(0, maxNotes);
  const notesInfo = await ankiConnectInvoke<AnkiConnectNote[]>("notesInfo", { notes: selectedIds }, options);

  const cards: AnkiExtractedCard[] = [];

  for (const n of notesInfo) {
    if (!n.fields) continue;

    const fieldEntries = Object.entries(n.fields).sort((a, b) => (a[1].order ?? 0) - (b[1].order ?? 0));
    if (fieldEntries.length === 0) continue;

    const frontRaw = fieldEntries[0][1]?.value || "";
    const backRawParts = fieldEntries.slice(1).map(e => e[1]?.value || "").filter(Boolean);

    const front = cleanHtml(frontRaw);
    const back = backRawParts.map(cleanHtml).filter(Boolean).join("\n\n");

    if (!front) continue;

    cards.push({
      front,
      back,
      deck_name: deckName,
      tags: n.tags || [],
      anki_nid: n.noteId,
    });
  }

  return cards;
}
