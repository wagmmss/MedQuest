import { PlannerWeek, PlannerTopic } from "@/types/api";

declare global {
  interface Window {
    google?: {
      accounts: {
        oauth2: {
          initTokenClient: (config: {
            client_id: string;
            scope: string;
            callback: (response: { access_token?: string; error?: string }) => void;
          }) => {
            requestAccessToken: () => void;
          };
        };
      };
    };
  }
}

export interface SyncProgress {
  current: number;
  total: number;
  status: string;
}

export async function syncPlanToGoogleCalendarDirectly(
  plan: PlannerWeek[],
  daysPerWeek: number = 6,
  onProgress?: (progress: SyncProgress) => void
): Promise<{ success: boolean; calendarId?: string; error?: string }> {
  const clientId = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID;
  if (!clientId) {
    throw new Error("GOOGLE_CLIENT_ID_MISSING");
  }

  // Carrega o script Google Identity Services se ainda não estiver presente
  if (!window.google?.accounts?.oauth2) {
    await new Promise<void>((resolve, reject) => {
      const existing = document.querySelector('script[src="https://accounts.google.com/gsi/client"]');
      if (existing) {
        resolve();
        return;
      }
      const script = document.createElement("script");
      script.src = "https://accounts.google.com/gsi/client";
      script.async = true;
      script.defer = true;
      script.onload = () => resolve();
      script.onerror = () => reject(new Error("Falha ao carregar o serviço Google Identity Services"));
      document.body.appendChild(script);
    });
  }

  return new Promise((resolve, reject) => {
    try {
      const tokenClient = window.google!.accounts.oauth2.initTokenClient({
        client_id: clientId,
        scope: "https://www.googleapis.com/auth/calendar.events https://www.googleapis.com/auth/calendar",
        callback: async (tokenResponse) => {
          if (tokenResponse.error || !tokenResponse.access_token) {
            return reject(new Error(tokenResponse.error || "Acesso não autorizado pelo usuário"));
          }

          try {
            const accessToken = tokenResponse.access_token;
            onProgress?.({ current: 0, total: 100, status: "Conectando e criando agenda MedQuest..." });

            // 1. Verifica ou cria uma agenda própria editável no Google Calendar
            const calListRes = await fetch("https://www.googleapis.com/calendar/v3/users/me/calendarList", {
              headers: { Authorization: `Bearer ${accessToken}` },
            });
            const calListData = await calListRes.json();
            let targetCalId = "primary";

            const existingCal = calListData.items?.find((c: { summary: string; id: string }) => 
              c.summary === "MedQuest - Cronograma de Residência"
            );

            if (existingCal) {
              targetCalId = existingCal.id;
            } else {
              const createCalRes = await fetch("https://www.googleapis.com/calendar/v3/calendars", {
                method: "POST",
                headers: {
                  Authorization: `Bearer ${accessToken}`,
                  "Content-Type": "application/json",
                },
                body: JSON.stringify({
                  summary: "MedQuest - Cronograma de Residência",
                  description: "Cronograma de estudos e revisões ativas do MedQuest (100% Editável).",
                  timeZone: "America/Sao_Paulo",
                }),
              });
              const newCal = await createCalRes.json();
              if (newCal.id) {
                targetCalId = newCal.id;
              }
            }

            // 2. Prepara todos os eventos de aulas e revisões
            const eventsToInsert: Array<{
              summary: string;
              description: string;
              start: { dateTime: string; timeZone: string };
              end: { dateTime: string; timeZone: string };
            }> = [];

            const origin = typeof window !== "undefined" ? window.location.origin : "";
            const studyDaysCount = Math.max(1, Math.min(7, daysPerWeek));

            for (const week of plan) {
              const weekDate = new Date(week.date);
              for (let tIdx = 0; tIdx < week.topics.length; tIdx++) {
                const topic = week.topics[tIdx];
                const dayOffset = tIdx % studyDaysCount;
                const topicDate = new Date(weekDate.getTime() + dayOffset * 86400000);

                const dtStart = new Date(topicDate);
                dtStart.setHours(8, 0, 0, 0);
                const durationMinutes = Math.max(30, Math.round(topic.estimated_hours * 60));
                const dtEnd = new Date(dtStart.getTime() + durationMinutes * 60000);

                // Evento de Aula
                eventsToInsert.push({
                  summary: `[MedQuest] 📖 ${topic.subtema} (${topic.area})`,
                  description: `📚 Carga: ${topic.estimated_hours}h (Teoria: ${topic.estimated_theory_hours}h + Questões: ${topic.estimated_practice_hours}h)\nSemana ${week.week} • ${topic.area}${origin ? `\n\n🔗 Questões: ${origin}/estudar?subtema=${encodeURIComponent(topic.subtema)}` : ""}`,
                  start: { dateTime: dtStart.toISOString(), timeZone: "America/Sao_Paulo" },
                  end: { dateTime: dtEnd.toISOString(), timeZone: "America/Sao_Paulo" },
                });

                // Revisão 24h
                const rev24Start = new Date(topicDate.getTime() + 86400000);
                rev24Start.setHours(19, 0, 0, 0);
                const rev24End = new Date(topicDate.getTime() + 86400000);
                rev24End.setHours(19, 30, 0, 0);
                eventsToInsert.push({
                  summary: `[MedQuest] 🔄 Revisão 24h: ${topic.subtema}`,
                  description: `🔄 Revisão Ativa de 24h: ${topic.subtema}.${origin ? `\n\n🔗 Revisar: ${origin}/revisao-ativa` : ""}`,
                  start: { dateTime: rev24Start.toISOString(), timeZone: "America/Sao_Paulo" },
                  end: { dateTime: rev24End.toISOString(), timeZone: "America/Sao_Paulo" },
                });

                // Revisão 7d
                const rev7Start = new Date(topicDate.getTime() + 7 * 86400000);
                rev7Start.setHours(19, 0, 0, 0);
                const rev7End = new Date(topicDate.getTime() + 7 * 86400000);
                rev7End.setHours(19, 30, 0, 0);
                eventsToInsert.push({
                  summary: `[MedQuest] 🔄 Revisão 7d: ${topic.subtema}`,
                  description: `🔄 Revisão Ativa de 7 dias: ${topic.subtema}.${origin ? `\n\n🔗 Revisar: ${origin}/revisao-ativa` : ""}`,
                  start: { dateTime: rev7Start.toISOString(), timeZone: "America/Sao_Paulo" },
                  end: { dateTime: rev7End.toISOString(), timeZone: "America/Sao_Paulo" },
                });
              }
            }

            // 3. Inserção progressiva dos eventos na conta do Google
            const total = eventsToInsert.length;
            for (let i = 0; i < total; i++) {
              const ev = eventsToInsert[i];
              onProgress?.({
                current: i + 1,
                total,
                status: `Criando evento ${i + 1} de ${total}: ${ev.summary}...`,
              });

              await fetch(`https://www.googleapis.com/calendar/v3/calendars/${encodeURIComponent(targetCalId)}/events`, {
                method: "POST",
                headers: {
                  Authorization: `Bearer ${accessToken}`,
                  "Content-Type": "application/json",
                },
                body: JSON.stringify(ev),
              });
            }

            resolve({ success: true, calendarId: targetCalId });
          } catch (err) {
            reject(err);
          }
        },
      });

      tokenClient.requestAccessToken();
    } catch (err) {
      reject(err);
    }
  });
}
