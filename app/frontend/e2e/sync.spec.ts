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
  test.beforeEach(async ({ context, page }) => {
    await context.addCookies([
      { name: 'medquest_demo', value: '1', domain: 'localhost', path: '/' }
    ]);
    await page.addInitScript(() => localStorage.setItem('medquest_onboarding_v1', 'done'));
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

  test('inicia e responde simulado 100% offline a partir de questões em cache local', async ({ page }) => {
    const TEST_OWNER = 'test_owner_offline';
    await page.addInitScript((owner) => {
      localStorage.setItem('medquest_local_owner', owner);
    }, TEST_OWNER);

    // Mock de rotas abortadas para simular desconexão total durante o simulado
    await page.route('**/api/meta**', async (route) => route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(MOCK_META) }));
    await page.route('**/api/simulado/**', async (route) => route.abort('failed'));
    await page.route('**/api/questions/**', async (route) => route.abort('failed'));
    await page.route('**/api/attempt/**', async (route) => route.abort('failed'));

    // 1. Acessa /simulado, aguarda o localDb carregar, popula e recarrega
    await page.goto('/simulado');
    await page.waitForFunction(() => typeof (window as any).localDb !== 'undefined');
    await page.evaluate(async ({ mockQuestion, ownerId }) => {
      const win = window as any;
      await win.localDb.questions.put({
        ...mockQuestion,
        _owner_id: ownerId,
      });
    }, { mockQuestion: MOCK_QUESTION_DETAIL, ownerId: TEST_OWNER });
    await page.reload();

    // 2. Inicia o simulado offline
    await expect(page.locator('button:has-text("Iniciar Simulado")')).toBeVisible({ timeout: 10000 });
    await page.click('button:has-text("Iniciar Simulado")');

    // 3. Verifica que a questão carregou a partir do cache local
    await expect(page.locator('text=Qual o tratamento de primeira linha')).toBeVisible({ timeout: 10000 });

    // 4. Responde e finaliza
    await page.click('text=Mudança de estilo de vida');
    await page.click('button:has-text("Finalizar Simulado")');
    await page.click('button:has-text("Entregar Prova")');

    // 5. Confirma exibição de sucesso offline
    await expect(page.locator('text=Simulado Salvo Offline')).toBeVisible({ timeout: 10000 });
  });

  test('permite revisar flashcards 100% offline sem travamento', async ({ page }) => {
    const TEST_OWNER = 'test_owner_flashcard';
    await page.addInitScript((owner) => {
      localStorage.setItem('medquest_local_owner', owner);
    }, TEST_OWNER);

    await page.route('**/api/meta**', async (route) => route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(MOCK_META) }));
    await page.route('**/api/flashcards/**', async (route) => route.abort('failed'));

    // 1. Acessa /revisao-ativa, aguarda localDb, popula e recarrega
    await page.goto('/revisao-ativa');
    await page.waitForFunction(() => typeof (window as any).localDb !== 'undefined');
    await page.evaluate(async (ownerId) => {
      const win = window as any;
      await win.localDb.flashcards.put({
        id: 101,
        question_id: 1,
        front: "O tratamento de primeira linha de HAS é {{c1::estilo de vida}}.",
        back: "Mudança de estilo de vida e monitoramento.",
        next_review_date: "2026-08-20T00:00:00Z",
        _owner_id: ownerId,
      });
    }, TEST_OWNER);
    await page.reload();

    // 2. Verifica a tela de flashcards offline carregada
    await expect(page.locator('text=Clique para Revelar')).toBeVisible({ timeout: 10000 });

    // 3. Revela e responde
    await page.click('text=Clique para Revelar');
    await expect(page.locator('button:has-text("Fácil")')).toBeVisible({ timeout: 5000 });
    await page.click('button:has-text("Fácil")');

    // 4. Confirma que avançou para "Tudo Revisado"
    await expect(page.locator('text=Tudo Revisado!')).toBeVisible({ timeout: 10000 });
  });
});
