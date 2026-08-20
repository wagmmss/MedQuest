import React, { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";

interface ImageViewerProps {
  src: string;
  alt?: string;
  isOpen: boolean;
  onClose: () => void;
}

export function ImageViewer({ src, alt, isOpen, onClose }: ImageViewerProps) {
  const [scale, setScale] = useState(1);

  // Fecha o visualizador ao pressionar Esc
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape" && isOpen) {
        onClose();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, onClose]);

  // Reseta o scale ao fechar
  useEffect(() => {
    if (!isOpen) {
      setTimeout(() => setScale(1), 300);
    }
  }, [isOpen]);

  const handleWheel = (e: React.WheelEvent) => {
    if (e.deltaY < 0) {
      setScale((prev) => Math.min(prev + 0.25, 4));
    } else {
      setScale((prev) => Math.max(prev - 0.25, 1));
    }
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.2 }}
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/90 backdrop-blur-sm"
          onClick={onClose}
          onWheel={handleWheel}
        >
          {/* Botão de Fechar */}
          <button
            onClick={onClose}
            className="absolute top-6 right-6 text-white/70 hover:text-white transition-colors bg-black/50 p-2 rounded-full"
            aria-label="Fechar"
          >
            <span className="material-symbols-outlined text-2xl">close</span>
          </button>

          {/* Controles de Zoom */}
          <div 
            className="absolute bottom-6 flex items-center gap-4 bg-black/60 px-4 py-2 rounded-full text-white/90"
            onClick={(e) => e.stopPropagation()}
          >
            <button 
              onClick={() => setScale((s) => Math.max(s - 0.5, 1))}
              className="p-1 hover:bg-white/20 rounded-full transition-colors"
            >
              <span className="material-symbols-outlined text-xl">zoom_out</span>
            </button>
            <span className="text-sm font-medium min-w-[3rem] text-center">
              {Math.round(scale * 100)}%
            </span>
            <button 
              onClick={() => setScale((s) => Math.min(s + 0.5, 4))}
              className="p-1 hover:bg-white/20 rounded-full transition-colors"
            >
              <span className="material-symbols-outlined text-xl">zoom_in</span>
            </button>
          </div>

          <motion.img
            src={src}
            alt={alt || "Imagem ampliada"}
            className="max-w-[95vw] max-h-[95vh] object-contain cursor-grab active:cursor-grabbing rounded-lg shadow-2xl"
            drag
            dragConstraints={{ left: -500, right: 500, top: -500, bottom: 500 }}
            dragElastic={0.1}
            style={{ scale }}
            onClick={(e) => e.stopPropagation()}
            initial={{ scale: 0.8, opacity: 0 }}
            animate={{ scale, opacity: 1 }}
            exit={{ scale: 0.8, opacity: 0 }}
            transition={{ type: "spring", damping: 25, stiffness: 300 }}
          />
        </motion.div>
      )}
    </AnimatePresence>
  );
}
