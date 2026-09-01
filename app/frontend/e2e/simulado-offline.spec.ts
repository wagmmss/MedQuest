import { test, expect } from '@playwright/test';

const MOCK_META = {
  total_questions: 2,
  institutions: [{ institution_code: "USP-SP", n: 2 }],
  years: [{ year: 2026, n: 2 }],
  areas: [{ area: "Clínica Médica", n: 1 }, { area: "Cirurgia", n: 1 }],
  subtemas: [{ subtema: "Cardiologia", n: 1 }, { subtema: "Trauma", n: 1 }],
};

const MOCK_SIMULADO_QUESTIONS = [
  { id: 201, institution_code: "USP-SP", year: 2026, area: "Clínica Médica", subtema: "Cardiologia", topic: "Cardiologia" },
  { id: 202, institution_code: "USP-SP", year: 2026, area: "Cirurgia", subtema: "Trauma", topic: "Trauma" },
];

const MOCK_BATCH_DETAILS = {
  questions: [
    {
      id: 201,
      stem: "Paciente idoso com dispneia progressiva aos esforços e B3 audível. Qual o diagnóstico provável?",
      institution_code: "USP-SP",
      institution_label: "USP-SP",
      year: 2026,
      area: "Clínica Médica",
      subtema: "Cardiologia",
      topic: "Cardiologia",
      correct_letter: "A",
      alternatives: [
        { letter: "A", text: "Insuficiência cardíaca descompensada" },
        { letter: "B", text: "Pneumonia comunitária típica" },
        { letter: "C", text: "Embolia pulmonar maciça" },
        { letter: "D", text: "Crise asmática grave" },
      ],
      explanation: "A presença de terceira bulha (B3) e dispneia progressiva é clássica de IC.",
      images: ["cardio_ecg_sample.png"],
    },
    {
      id: 202,
      stem: "Paciente politraumatizado com dor abdominal e sinal de Cullen presente.",
      institution_code: "USP-SP",
      institution_label: "USP-SP",
      year: 2026,
      area: "Cirurgia",
      subtema: "Trauma",
      topic: "Trauma",
      correct_letter: "C",
      alternatives: [
        { letter: "A", text: "Apendicite aguda supurada" },
        { letter: "B", text: "Colecistite calculosa aguda" },
        { letter: "C", text: "Hemorragia retroperitoneal por trauma" },
        { letter: "D", text: "Úlcera péptica perfurada" },
      ],
      explanation: "O sinal de Cullen (equimose periumbilical) sugere hemoperitônio/hemorragia retroperitoneal.",
      images: [],
    },
  ],
};

test.describe('Simulado 100% Offline com Pré-download e Sincronização Posterior', () => {
  test.beforeEach(async ({ context, page }) => {
    await context.addCookies([
      { name: 'medquest_demo', value: '1', domain: 'localhost', path: '/' }
    ]);
    await page.addInitScript(() => localStorage.setItem('medquest_onboarding_v1', 'done'));
  });

  test('baixa pacote offline, executa sem rede, recarrega, finaliza offline e sincroniza ao reconectar', async ({ page }) => {
    let attemptReceivedCount = 0;
    let isNetworkOnline = true;

    // 1. Configurar rotas da API
    await page.route('**/api/**', async (route) => {
      const url = new URL(route.request().url());

      if (!isNetworkOnline) {
        return route.abort('failed');
      }

      if (url.pathname.endsWith('/api/meta')) {
        return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(MOCK_META) });
      }
      if (url.pathname.includes('/simulado/usp') || url.pathname.includes('/simulado/custom') || url.pathname.endsWith('/api/questions')) {
        return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(MOCK_SIMULADO_QUESTIONS) });
      }
      if (url.pathname.endsWith('/api/questions/batch')) {
        return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(MOCK_BATCH_DETAILS) });
      }
      if (url.pathname.endsWith('/api/questions/201')) {
        return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(MOCK_BATCH_DETAILS.questions[0]) });
      }
      if (url.pathname.endsWith('/api/questions/202')) {
        return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(MOCK_BATCH_DETAILS.questions[1]) });
      }
      if (url.pathname.endsWith('/api/images/cardio_ecg_sample.png')) {
        return route.fulfill({ status: 200, contentType: 'image/png', body: Buffer.from('') });
      }
      if (url.pathname.endsWith('/api/attempt/batch') || url.pathname.endsWith('/api/questions/attempts/batch')) {
        attemptReceivedCount++;
        return route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            results: [
              {
                question_id: 201,
                is_correct: true,
                correct_letter: "A",
                explanation: "A presença de terceira bulha (B3) e dispneia progressiva é clássica de IC.",
                next_review_date: "2026-09-10T00:00:00Z",
              },
              {
                question_id: 202,
                is_correct: true,
                correct_letter: "C",
                explanation: "O sinal de Cullen sugere hemorragia retroperitoneal.",
                next_review_date: "2026-09-10T00:00:00Z",
              },
            ],
          }),
        });
      }
      return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({}) });
    });

    // 2. Acessar a página de simulado online
    await page.goto('/simulado');
    await expect(page.locator('button:has-text("Iniciar Simulado")')).toBeVisible({ timeout: 10000 });

    // 3. Executar pré-download explícito do simulado para uso offline
    await expect(page.locator('button:has-text("Baixar este Simulado para Uso Offline")')).toBeVisible();
    await page.click('button:has-text("Baixar este Simulado para Uso Offline")');

    // 4. Aguardar o download concluir e validar exibição do badge "Pronto Offline"
    await expect(page.locator('text=Pronto Offline')).toBeVisible({ timeout: 15000 });

    // 5. DESLIGAR A REDE (Simular desconexão total de API e serviços)
    isNetworkOnline = false;

    // 6. Iniciar o simulado 100% offline
    await page.click('button:has-text("Iniciar Simulado")');

    // 7. Responder à 1ª questão offline
    await expect(page.locator('text=Paciente idoso com dispneia')).toBeVisible({ timeout: 10000 });
    await page.click('text=Insuficiência cardíaca descompensada');

    // 8. Avançar para a 2ª questão
    await page.click('button:has-text("Próxima")');
    await expect(page.locator('text=Paciente politraumatizado')).toBeVisible({ timeout: 10000 });
    await page.click('text=Hemorragia retroperitoneal');

    // 9. RECARREGAR A PÁGINA e verificar retomada offline a partir do IndexedDB
    await page.reload();
    await expect(page.locator('button:has-text("Continuar Andamento")')).toBeVisible({ timeout: 10000 });
    await page.click('button:has-text("Continuar Andamento")');

    // 10. Confirmar que a resposta da 2ª questão e a 1ª questão foram preservadas
    await expect(page.locator('text=Paciente politraumatizado')).toBeVisible();
    await expect(page.locator('button:has-text("Hemorragia retroperitoneal")')).toHaveAttribute('aria-pressed', 'true');

    // 11. Finalizar e entregar o simulado sem rede
    await page.click('button:has-text("Finalizar Simulado")');
    await expect(page.locator('button:has-text("Entregar Prova")')).toBeVisible({ timeout: 5000 });
    await page.click('button:has-text("Entregar Prova")');

    // 12. Validar tela de "Simulado Salvo Offline" e enfileiramento na syncQueue
    await expect(page.locator('text=Simulado Salvo Offline')).toBeVisible({ timeout: 10000 });
    expect(attemptReceivedCount).toBe(0); // Nenhuma requisição enviada ao servidor ainda

    // 13. RECONECTAR A REDE
    isNetworkOnline = true;

    // 14. Disparar sincronização
    await page.evaluate(async () => {
      const win = window as unknown as { syncManager?: { sync: (force?: boolean) => Promise<void> } };
      if (win.syncManager) {
        await win.syncManager.sync(true);
      }
    });

    // 15. Validar transição automática para a tela de resultados oficiais
    await expect(page.locator('text=Nota Final')).toBeVisible({ timeout: 10000 });
    await expect(page.locator('text=100% de Acerto')).toBeVisible();
    expect(attemptReceivedCount).toBe(1); // Exatamente 1 lote enviado ao backend (idempotente)
  });
});
