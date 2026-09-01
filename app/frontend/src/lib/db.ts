import Dexie, { Table } from "dexie";
import { QuestionDetail, Flashcard } from "@/types/api";

declare global {
  interface Window {
    Clerk?: {
      user?: {
        id: string;
      };
    };
  }
}

/**
 * Retorna o identificador de proprietário dos dados locais (IndexedDB).
 * Se o usuário estiver autenticado no Clerk, retorna seu ID real.
 * Caso contrário, retorna o UUID persistente de visitante em localStorage.
 */
export function getLocalOwnerId(): string {
  if (typeof window === "undefined") {
    return "ssr_dummy_owner";
  }
  const clerkUser = window.Clerk?.user?.id;
  if (clerkUser) return clerkUser;

  let ownerId = localStorage.getItem("medquest_local_owner");
  if (!ownerId || ownerId === "guest" || ownerId === "server") {
    ownerId = crypto.randomUUID();
    localStorage.setItem("medquest_local_owner", ownerId);
  }
  return ownerId;
}

export interface SyncItem {
  id: string;
  owner_id: string;
  endpoint: string;
  method: string;
  body: string | null;
  content_type: string;
  created_at: number;
  retry_count: number;
  next_retry_at: number;
  status: "pending" | "failed" | "completed";
  last_error?: string;
  idempotency_key: string;
}

export interface SimuladoPackage {
  id: string;
  owner_id: string;
  name: string;
  config: {
    institutions?: string[];
    years?: string[];
    questions_per_area?: number;
    duration_minutes?: number;
    force_4_options?: boolean;
    [key: string]: unknown;
  };
  question_ids: number[];
  questions_count: number;
  details_count: number;
  images_count: number;
  estimated_size_bytes: number;
  status: "downloading" | "ready" | "incomplete" | "expired" | "quota_exceeded";
  download_progress: number;
  created_at: number;
  updated_at: number;
  expires_at: number;
  version: number;
  last_error?: string;
}

export function isPackageValid(pkg: SimuladoPackage | null | undefined): { valid: boolean; reason?: string } {
  if (!pkg) return { valid: false, reason: "Nenhum pacote encontrado" };
  if (pkg.status !== "ready") {
    if (pkg.status === "downloading") return { valid: false, reason: "Download em andamento" };
    if (pkg.status === "incomplete") return { valid: false, reason: "Pacote incompleto" };
    if (pkg.status === "quota_exceeded") return { valid: false, reason: "Espaço insuficiente em disco" };
    return { valid: false, reason: "Pacote não está pronto" };
  }
  if (Date.now() > pkg.expires_at) {
    return { valid: false, reason: "Pacote expirado" };
  }
  if (pkg.questions_count === 0 || pkg.details_count < pkg.questions_count) {
    return { valid: false, reason: "Pacote incompleto ou inconsistente" };
  }
  return { valid: true };
}

export class MedQuestDB extends Dexie {
  questions!: Table<QuestionDetail & { _owner_id: string }, [number, string]>;
  flashcards!: Table<Flashcard & { _owner_id: string }, [number, string]>;
  syncQueue!: Table<SyncItem, string>;
  simuladoPackages!: Table<SimuladoPackage, string>;

  constructor() {
    super("MedQuestDB_v2");

    this.version(1).stores({
      questions: "[id+_user_id], id, institution_code, year, area, subtema",
      flashcards: "[id+_user_id], id, question_id, next_review_date",
      syncQueue: "id, user_id, timestamp",
    });

    this.version(2)
      .stores({
        questions: "[id+_owner_id], id, _owner_id, institution_code, year, area, subtema",
        flashcards: "[id+_owner_id], id, _owner_id, question_id, next_review_date",
        syncQueue: "id, owner_id, status, next_retry_at, created_at",
      })
      .upgrade((trans) => {
        const currentGuestOwner = getLocalOwnerId();

        return Promise.all([
          trans
            .table("questions")
            .toCollection()
            .modify((q: Record<string, unknown>) => {
              const oldUserId = (q._user_id as string) || "1";
              if (oldUserId.startsWith("user_")) {
                q._owner_id = oldUserId;
              } else {
                q._owner_id = currentGuestOwner;
              }
              delete q._user_id;
            }),
          trans
            .table("flashcards")
            .toCollection()
            .modify((f: Record<string, unknown>) => {
              const oldUserId = (f._user_id as string) || "1";
              if (oldUserId.startsWith("user_")) {
                f._owner_id = oldUserId;
              } else {
                f._owner_id = currentGuestOwner;
              }
              delete f._user_id;
            }),
          trans
            .table("syncQueue")
            .toCollection()
            .modify((s: Record<string, unknown>) => {
              const oldUserId = (s.user_id as string) || "1";
              s.owner_id = oldUserId.startsWith("user_") ? oldUserId : currentGuestOwner;
              delete s.user_id;
              s.status = s.status || "pending";
              s.retry_count = s.retry_count || 0;
              s.next_retry_at = s.next_retry_at || Date.now();
              s.created_at = s.timestamp || Date.now();
              delete s.timestamp;
              s.idempotency_key = s.idempotency_key || crypto.randomUUID();

              // v2 bug: loss of method and content-type from options
              if (typeof s.options === "object" && s.options !== null) {
                const opts = s.options as Record<string, unknown>;
                s.method = typeof opts.method === "string"
                  ? opts.method.toUpperCase()
                  : (s.method || "POST");

                let cType = "application/json";
                const oldHeaders = opts.headers;
                if (oldHeaders instanceof Headers) {
                  cType = oldHeaders.get("content-type") || cType;
                } else if (Array.isArray(oldHeaders)) {
                  for (const entry of oldHeaders) {
                    if (Array.isArray(entry) && typeof entry[0] === "string" &&
                        entry[0].toLowerCase() === "content-type" && typeof entry[1] === "string") {
                      cType = entry[1];
                      break;
                    }
                  }
                } else if (typeof oldHeaders === "object" && oldHeaders !== null) {
                    for (const [k, v] of Object.entries(oldHeaders)) {
                      if (k.toLowerCase() === "content-type" && typeof v === "string") cType = v;
                    }
                }
                s.content_type = cType;

                const rawBody = opts.body;
                if (typeof rawBody === "string") {
                  s.body = rawBody;
                } else if (rawBody !== undefined && rawBody !== null) {
                  try { s.body = JSON.stringify(rawBody); } catch { s.body = null; }
                } else {
                  s.body = null;
                }
                delete s.options;
              } else {
                s.method = s.method || "POST";
                s.content_type = s.content_type || "application/json";
              }
            }),
        ]);
      });

    this.version(3)
      .stores({
        questions: "[id+_owner_id], id, _owner_id, institution_code, year, area, subtema",
        flashcards: "[id+_owner_id], id, _owner_id, question_id, next_review_date",
        syncQueue: "id, owner_id, status, next_retry_at, created_at",
      })
      .upgrade((trans) => {
        return trans.table("syncQueue").toCollection().modify((s: Record<string, unknown>) => {
          // If upgrading from v2, fix double-serialized body
          if (typeof s.body === "string" && s.body.startsWith('"') && s.body.endsWith('"')) {
            try {
              const parsed = JSON.parse(s.body);
              if (typeof parsed === "string") {
                s.body = parsed;
              }
            } catch {
              // ignore
            }
          }
        });
      });

    this.version(4)
      .stores({
        questions: "[id+_owner_id], id, _owner_id, institution_code, year, area, subtema",
        flashcards: "[id+_owner_id], id, _owner_id, question_id, next_review_date",
        syncQueue: "id, owner_id, status, next_retry_at, created_at",
        simuladoPackages: "id, owner_id, status, expires_at, created_at",
      });
  }
}

export const localDb = typeof window !== "undefined" ? new MedQuestDB() : (null as unknown as MedQuestDB);

if (typeof window !== "undefined" && localDb) {
  (window as unknown as { localDb?: MedQuestDB }).localDb = localDb;
}
