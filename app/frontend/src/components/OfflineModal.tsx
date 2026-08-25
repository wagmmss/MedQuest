"use client";

import { useEffect, useRef } from "react";
import { OfflinePanel } from "./OfflinePanel";
import { X } from "lucide-react";

interface OfflineModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function OfflineModal({ isOpen, onClose }: OfflineModalProps) {
  const modalRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape" && isOpen) {
        onClose();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, onClose]);

  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "";
    }
    return () => {
      document.body.style.overflow = "";
    };
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <div 
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-in fade-in duration-200"
      onClick={(e) => {
        if (modalRef.current && !modalRef.current.contains(e.target as Node)) {
          onClose();
        }
      }}
      role="dialog"
      aria-modal="true"
      aria-labelledby="offline-modal-title"
    >
      <div 
        ref={modalRef} 
        className="relative w-full max-w-2xl bg-card border border-border rounded-3xl shadow-2xl overflow-hidden max-h-[90vh] flex flex-col animate-in zoom-in-95 duration-200"
      >
        <button
          onClick={onClose}
          className="absolute top-4 right-4 z-10 p-2 rounded-xl text-muted-foreground hover:text-foreground hover:bg-muted/80 transition-colors cursor-pointer"
          aria-label="Fechar modal de modo plantão"
        >
          <X size={20} />
        </button>

        <div className="overflow-y-auto p-2 sm:p-4">
          <OfflinePanel onClose={onClose} />
        </div>
      </div>
    </div>
  );
}
