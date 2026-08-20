import { useCallback, useSyncExternalStore } from 'react';

const ZEN_MODE_EVENT = 'zen-mode-changed';

function subscribe(onStoreChange: () => void) {
  window.addEventListener(ZEN_MODE_EVENT, onStoreChange);
  return () => window.removeEventListener(ZEN_MODE_EVENT, onStoreChange);
}

function getSnapshot() {
  return document.body.classList.contains('zen-mode');
}

function getServerSnapshot() {
  return false;
}

export function useZenMode() {
  const isZenMode = useSyncExternalStore(subscribe, getSnapshot, getServerSnapshot);

  const toggleZenMode = useCallback(() => {
    const next = !getSnapshot();
    document.body.classList.toggle('zen-mode', next);
    window.dispatchEvent(new Event(ZEN_MODE_EVENT));
  }, []);

  return { isZenMode, toggleZenMode };
}
