import Dexie, { Table } from 'dexie';
import { QuestionDetail, Flashcard } from '@/types/api';

export function getUserId(): string {
  if (typeof window === "undefined") return "server";
  const clerkUser = (window as any).Clerk?.user?.id;
  if (clerkUser) return clerkUser;
  
  let guestId = localStorage.getItem("mq_guest_id");
  if (!guestId) {
    guestId = Math.random().toString(36).substring(2, 15);
    localStorage.setItem("mq_guest_id", guestId);
  }
  return `guest_${guestId}`;
}

export interface SyncItem {
  id: string;
  user_id: string;
  endpoint: string;
  options: RequestInit;
  timestamp: number;
}

export class MedQuestDB extends Dexie {
  questions!: Table<QuestionDetail & { _user_id: string }, [number, string]>;
  flashcards!: Table<Flashcard & { _user_id: string }, [number, string]>;
  syncQueue!: Table<SyncItem, string>;

  constructor() {
    super('MedQuestDB_v2');
    this.version(1).stores({
      questions: '[id+_user_id], id, institution_code, year, area, subtema',
      flashcards: '[id+_user_id], id, question_id, next_review_date',
      syncQueue: 'id, user_id, timestamp'
    });
  }
}

export const localDb = typeof window !== "undefined" ? new MedQuestDB() : null as unknown as MedQuestDB;
