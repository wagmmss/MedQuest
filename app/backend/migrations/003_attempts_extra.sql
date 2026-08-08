-- Migration 003: dados que devem ser coletados JÁ (dado não coletado é perdido pra sempre).
-- time_spent_ms: tempo por questão (destrava "você leva 3x mais em Cardiologia").
-- confidence: chutei / dúvida / certeza (separa acerto por sorte de conhecimento real).
ALTER TABLE attempts ADD COLUMN time_spent_ms INTEGER;
ALTER TABLE attempts ADD COLUMN confidence TEXT;
