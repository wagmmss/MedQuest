import Dexie, { Table } from 'dexie';
import { QuestionDetail, Flashcard } from '@/types/api';

export interface SyncItem {
  id: string;
  endpoint: string;
  options: RequestInit;
  timestamp: number;
}

export class MedQuestDB extends Dexie {
  questions!: Table<QuestionDetail, number>; // id is the primary key
  flashcards!: Table<Flashcard, number>; // id is the primary key
  syncQueue!: Table<SyncItem, string>; // id (UUID) is the primary key

  constructor() {
    super('MedQuestDB');
    this.version(1).stores({
      questions: 'id, institution_code, year, area, subtema',
      flashcards: 'id, question_id, next_review_date',
      syncQueue: 'id, timestamp'
    });
  }
}

// Ensure it's only instantiated on the client side (browser)
export const localDb = typeof window !== "undefined" ? new MedQuestDB() : null as unknown as MedQuestDB;
