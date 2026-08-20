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

export class MedQuestDB extends Dexie {
  questions!: Table<QuestionDetail & { _owner_id: string }, [number, string]>;
  flashcards!: Table<Flashcard & { _owner_id: string }, [number, string]>;
  syncQueue!: Table<SyncItem, string>;

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
              if (s.options) {
                const opts = s.options as any;
                s.method = opts.method ? opts.method.toUpperCase() : (s.method || "POST");
                
                let cType = "application/json";
                if (opts.headers) {
                  if (typeof opts.headers.get === "function") {
                    cType = opts.headers.get("content-type") || cType;
                  } else if (Array.isArray(opts.headers)) {
                    const f = opts.headers.find(([k]: [string]) => k.toLowerCase() === "content-type");
                    if (f) cType = f[1];
                  } else if (typeof opts.headers === "object") {
                    for (const [k, v] of Object.entries(opts.headers)) {
                      if (k.toLowerCase() === "content-type" && typeof v === "string") cType = v;
                    }
                  }
                }
                s.content_type = cType;

                let rawBody = opts.body;
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
  }
}

export const localDb = typeof window !== "undefined" ? new MedQuestDB() : (null as unknown as MedQuestDB);
