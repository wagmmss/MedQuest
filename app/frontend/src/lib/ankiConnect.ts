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

const DEFAULT_ANKICONNECT_URL = "http://127.0.0.1:8765";

export async function ankiConnectInvoke<T>(action: string, params: Record<string, unknown> = {}, url: string = DEFAULT_ANKICONNECT_URL): Promise<T> {
  const res = await fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      action,
      version: 6,
      params,
    }),
  });

  if (!res.ok) {
    throw new Error(`Erro na requisição ao AnkiConnect: ${res.statusText}`);
  }

  const data = await res.json();
  if (data.error) {
    throw new Error(data.error);
  }

  return data.result as T;
}

export async function checkAnkiConnect(url: string = DEFAULT_ANKICONNECT_URL): Promise<{ connected: boolean; version?: number; error?: string }> {
  try {
    const version = await ankiConnectInvoke<number>("version", {}, url);
    return { connected: true, version };
  } catch (err) {
    return {
      connected: false,
      error: err instanceof Error ? err.message : "Não foi possível conectar ao AnkiConnect",
    };
  }
}

export async function getAnkiDecks(url: string = DEFAULT_ANKICONNECT_URL): Promise<string[]> {
  const decks = await ankiConnectInvoke<string[]>("deckNames", {}, url);
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

export async function fetchDeckCards(deckName: string, maxNotes: number = 500, url: string = DEFAULT_ANKICONNECT_URL): Promise<AnkiExtractedCard[]> {
  const query = `deck:"${deckName}"`;
  const noteIds = await ankiConnectInvoke<number[]>("findNotes", { query }, url);

  if (!noteIds || noteIds.length === 0) {
    return [];
  }

  const selectedIds = noteIds.slice(0, maxNotes);
  const notesInfo = await ankiConnectInvoke<AnkiConnectNote[]>("notesInfo", { notes: selectedIds }, url);

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
