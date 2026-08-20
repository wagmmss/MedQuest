import confetti from "canvas-confetti";

export function triggerConfetti() {
  if (typeof window === "undefined") return;

  const today = new Date().toISOString().split("T")[0];
  const lastConfetti = localStorage.getItem("mq_last_confetti");

  if (lastConfetti === today) {
    return; // Already triggered today
  }

  confetti({
    particleCount: 100,
    spread: 70,
    origin: { y: 0.6 }
  });

  localStorage.setItem("mq_last_confetti", today);
}
