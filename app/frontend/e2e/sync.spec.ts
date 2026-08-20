import { test, expect } from '@playwright/test';

const MOCK_META = {
  total_questions: 1,
  institutions: [{ institution_code: "USP", n: 1 }],
  years: [{ year: 2025, n: 1 }],
  areas: [{ area: "Clínica Médica", n: 1 }],
  subtemas: [{ subtema: "HAS", n: 1 }],
};

const MOCK_QUESTION_LIST = [
  { id: 1, institution_code: "USP", year: 2025, area: "Clínica Médica", subtema: "HAS", topic: "HAS" },
];

const MOCK_QUESTION_DETAIL = {
  id: 1,
  stem: "Qual o tratamento de primeira linha para HAS estágio 1 em jovem sem comorbidades?",
  institution_code: "USP",
  institution_label: "USP",
  year: 2025,
  area: "Clínica Médica",
  subtema: "HAS",
  topic: "HAS",
  correct_letter: "B",
  alternatives: [
    { letter: "A", text: "Iniciar tripla terapia imediatamente" },
    { letter: "B", text: "Mudança de estilo de vida e monoterapia se necessário" },
  ],
};

test.describe('Offline Sync e Resiliência', () => {
  test.beforeEach(async ({ context }) => {
    await context.addCookies([
      { name: 'medquest_demo', value: '1', domain: 'localhost', path: '/' }
    ]);
  });

  test('enfileira tentativa offline, grava no IndexedDB e sincroniza ao reconectar', async ({ page }) => {
    let attemptReceivedCount = 0;
    let shouldFailAttempt = true;

    await page.route('**/api/**', async (route) => {
      const url = new URL(route.request().url());
      if (url.pathname.endsWith('/api/meta')) {
        return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(MOCK_META) });
      }
      if (url.pathname.endsWith('/api/questions')) {
        return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(MOCK_QUESTION_LIST) });
      }
      if (url.pathname.endsWith('/api/questions/1')) {
        return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(MOCK_QUESTION_DETAIL) });
      }
      if (url.pathname.endsWith('/api/questions/1/attempt')) {
        if (shouldFailAttempt) {
          return route.abort('failed');
        }
        attemptReceivedCount++;
        return route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            is_correct: true,
            correct_letter: "B",
            explanation: "Comentário da questão 1",
            next_review_date: "2026-08-25T00:00:00Z",
          }),
        });
      }
      return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({}) });
    });

    // 1. Abrir a página de estudo
    await page.goto('/estudar?area=Cl%C3%ADnica+M%C3%A9dica');

    // 2. Aguardar a questão carregar
    await expect(page.locator('text=Qual o tratamento de primeira linha')).toBeVisible({ timeout: 10000 });

    // 3. Selecionar a alternativa B
    await page.click('text=Mudança de estilo de vida');

    // 4. Confirmar resposta enquanto a requisição de tentativa falha
    await page.click('button:has-text("Confirmar Resposta")');

    // 5. Verificar que a mensagem informativa de offline é exibida
    await expect(page.locator('text=Resposta Salva Offline')).toBeVisible({ timeout: 5000 });

    // 6. Verificar que a tentativa foi gravada na fila offline
    await expect.poll(async () => {
      return await page.evaluate(async () => {
        const win = window as unknown as { syncManager?: { getPendingCount: () => Promise<number> } };
        return win.syncManager ? await win.syncManager.getPendingCount() : 0;
      });
    }, { timeout: 10000 }).toBe(1);

    // 7. Restaurar a conexão (mock passa a responder 200)
    shouldFailAttempt = false;

    // 8. Disparar sincronização
    await page.evaluate(async () => {
      const win = window as unknown as { syncManager?: { sync: (force?: boolean) => Promise<void> } };
      if (win.syncManager) {
        await win.syncManager.sync(true);
      }
    });

    // 9. Confirmar que a requisição chegou exatamente uma vez ao backend
    expect(attemptReceivedCount).toBe(1);

    // 10. Confirmar que o item foi removido da fila de pendentes
    await expect.poll(async () => {
      return await page.evaluate(async () => {
        const win = window as unknown as { syncManager?: { getPendingCount: () => Promise<number> } };
        return win.syncManager ? await win.syncManager.getPendingCount() : 0;
      });
    }, { timeout: 10000 }).toBe(0);
  });

  test('marca erro 4xx não-retentável como falha terminal visível', async ({ page }) => {
    let return400 = false;

    await page.route('**/api/**', async (route) => {
      const url = new URL(route.request().url());
      if (url.pathname.endsWith('/api/meta')) {
        return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(MOCK_META) });
      }
      if (url.pathname.endsWith('/api/questions')) {
        return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(MOCK_QUESTION_LIST) });
      }
      if (url.pathname.endsWith('/api/questions/1')) {
        return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(MOCK_QUESTION_DETAIL) });
      }
      if (url.pathname.endsWith('/api/questions/1/attempt')) {
        if (return400) {
          return route.fulfill({
            status: 400,
            contentType: 'application/json',
            body: JSON.stringify({ error: "Payload inválido" }),
          });
        }
        return route.abort('failed');
      }
      return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({}) });
    });

    await page.goto('/estudar?area=Cl%C3%ADnica+M%C3%A9dica');
    await expect(page.locator('text=Qual o tratamento de primeira linha')).toBeVisible({ timeout: 10000 });

    await page.click('text=Mudança de estilo de vida');
    await page.click('button:has-text("Confirmar Resposta")');
    await expect(page.locator('text=Resposta Salva Offline')).toBeVisible({ timeout: 5000 });

    // Habilitar retorno 400 ao tentar sincronizar
    return400 = true;

    // Disparar sincronização
    await page.evaluate(async () => {
      const win = window as unknown as { syncManager?: { sync: (force?: boolean) => Promise<void> } };
      if (win.syncManager) {
        await win.syncManager.sync(true);
      }
    });

    // Verificar que o item passou para a lista de falhas terminais
    await expect.poll(async () => {
      return await page.evaluate(async () => {
        const win = window as unknown as { syncManager?: { getFailedItems: () => Promise<unknown[]> } };
        if (win.syncManager) {
          const failed = await win.syncManager.getFailedItems();
          return failed.length;
        }
        return 0;
      });
    }, { timeout: 10000 }).toBe(1);
  });
});
