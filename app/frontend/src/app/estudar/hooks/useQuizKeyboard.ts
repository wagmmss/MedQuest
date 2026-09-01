import { useEffect } from "react";
import { QuestionDetail, AttemptResult } from "@/types/api";

interface UseQuizKeyboardProps {
  state: "FILTERS" | "LOADING_QUEUE" | "PLAYING" | "RESULTS" | "FINISHED";
  currentDetail: QuestionDetail | null;
  loadingDetail: boolean;
  attemptResult: AttemptResult | null;
  currentIndex: number;
  queue: Array<any>;
  selectedLetter: string | null;
  submitting: boolean;
  handleAttempt: () => void;
  handleDiscursiveReveal: () => void;
  handleReviewFSRS: (conf: "certeza" | "duvida" | "chutei", explicitIsCorrect?: boolean) => void;
  nextQuestion: () => void;
  prevQuestion: () => void;
  navigateQuestion: (direction: "next" | "previous") => void;
  selectAlternative: (letter: string) => void;
}

export function useQuizKeyboard({
  state,
  currentDetail,
  loadingDetail,
  attemptResult,
  currentIndex,
  queue,
  selectedLetter,
  submitting,
  handleAttempt,
  handleDiscursiveReveal,
  handleReviewFSRS,
  nextQuestion,
  prevQuestion,
  navigateQuestion,
  selectAlternative,
}: UseQuizKeyboardProps) {
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      const tag = (e.target as HTMLElement).tagName;
      if (tag === 'INPUT' || tag === 'TEXTAREA') return;
      
      const isButton = tag === 'BUTTON';
      const target = e.target as HTMLButtonElement;
      
      if (isButton && !target.disabled && (e.key === "Enter" || e.key === " ")) {
        return;
      }

      if (state !== "PLAYING" || !currentDetail || loadingDetail) return;

      const key = e.key.toUpperCase();
      const isDiscursive = Boolean(currentDetail.is_discursive || (currentDetail.alternatives || []).length <= 1);
      
      if (!attemptResult) {
        if (isDiscursive) {
          if ((e.ctrlKey || e.metaKey) && key === "ENTER") {
            e.preventDefault();
            handleDiscursiveReveal();
          }
        } else {
          // Alternatives 1-5 or A-E
          const altIndexMap: Record<string, number> = { '1': 0, '2': 1, '3': 2, '4': 3, '5': 4, 'A': 0, 'B': 1, 'C': 2, 'D': 3, 'E': 4 };
          if (key in altIndexMap) {
            const idx = altIndexMap[key];
            if (idx < (currentDetail.alternatives || []).length) {
              selectAlternative(currentDetail.alternatives[idx].letter);
            }
          } else if (key === "ENTER" || key === " ") {
            if (selectedLetter && !submitting) {
              e.preventDefault();
              handleAttempt();
            }
          }
        }
      } else {
        if (attemptResult.is_correct === null) {
          if (key === "3" || key === "A") { e.preventDefault(); handleReviewFSRS("certeza", true); }
          else if (key === "2" || key === "ENTER" || key === " ") { e.preventDefault(); handleReviewFSRS("duvida", true); }
          else if (key === "1") { e.preventDefault(); handleReviewFSRS("chutei", true); }
          else if (key === "E") { e.preventDefault(); handleReviewFSRS("duvida", false); }
        } else if (!attemptResult.next_review_date) {
          if (key === "1") handleReviewFSRS("chutei");
          else if (key === "2" || key === "ENTER" || key === " ") { e.preventDefault(); handleReviewFSRS("duvida"); }
          else if (key === "3") handleReviewFSRS("certeza");
        } else {
          if (key === "ENTER" || key === " " || key === "3" || key === "2" || key === "1") {
            e.preventDefault();
            nextQuestion();
          }
        }
      }

      // Free navigation with arrows (direto com seta esquerda/direita)
      if (e.key === "ArrowLeft") {
        e.preventDefault();
        navigateQuestion("previous");
      } else if (e.key === "ArrowRight") {
        e.preventDefault();
        navigateQuestion("next");
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [state, currentDetail, loadingDetail, attemptResult, currentIndex, queue, selectedLetter, submitting, handleAttempt, handleDiscursiveReveal, handleReviewFSRS, nextQuestion, prevQuestion, navigateQuestion, selectAlternative]);
}
