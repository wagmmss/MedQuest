import { useState, useEffect, useCallback } from 'react';

export function useZenMode() {
  const [isZenMode, setIsZenMode] = useState(false);

  // Sincroniza o estado inicial lendo a classe do body
  useEffect(() => {
    setIsZenMode(document.body.classList.contains('zen-mode'));
  }, []);

  const toggleZenMode = useCallback(() => {
    setIsZenMode((prev) => {
      const next = !prev;
      if (next) {
        document.body.classList.add('zen-mode');
      } else {
        document.body.classList.remove('zen-mode');
      }
      // Dispara um evento customizado para avisar outros componentes (como QuizClient)
      window.dispatchEvent(new CustomEvent('zen-mode-changed', { detail: next }));
      return next;
    });
  }, []);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Ignora se estiver digitando em inputs
      const tag = (e.target as HTMLElement).tagName;
      if (tag === 'INPUT' || tag === 'TEXTAREA') return;

      // Atalho 'z' para Zen Mode
      if (e.key.toLowerCase() === 'z' && !e.ctrlKey && !e.metaKey && !e.altKey) {
        e.preventDefault();
        toggleZenMode();
      }
    };

    const handleCustomEvent = (e: Event) => {
      const customEvent = e as CustomEvent;
      setIsZenMode(customEvent.detail);
      if (customEvent.detail) {
        document.body.classList.add('zen-mode');
      } else {
        document.body.classList.remove('zen-mode');
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    window.addEventListener('zen-mode-changed', handleCustomEvent);
    
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
      window.removeEventListener('zen-mode-changed', handleCustomEvent);
    };
  }, [toggleZenMode]);

  return { isZenMode, toggleZenMode };
}
