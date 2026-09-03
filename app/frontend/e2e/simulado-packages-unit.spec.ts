import { test, expect } from '@playwright/test';

const MOCK_META = {
  total_questions: 10,
  institutions: [{ institution_code: 'USP-SP', n: 10 }],
  years: [{ year: 2026, n: 10 }],
  areas: [{ area: 'Clínica Médica', n: 5 }, { area: 'Cirurgia', n: 5 }],
  subtemas: [],
};

test.describe('Validações Unitárias e de Integridade de Pacotes Offline', () => {
  test.beforeEach(async ({ context, page }) => {
    const baseURL = process.env.PLAYWRIGHT_BASE_URL || 'http://127.0.0.1:3100';
    await context.addCookies([
      { name: 'medquest_demo', value: '1', url: baseURL }
    ]);
    await page.addInitScript(() => localStorage.setItem('medquest_onboarding_v1', 'done'));
  });

  test('impede iniciar simulado a partir de pacote incompleto ou corrompido', async ({ page }) => {
    const TEST_OWNER = 'user_corrupt_test';
    await page.addInitScript((owner) => {
      localStorage.setItem('medquest_local_owner', owner);
    }, TEST_OWNER);

    let shouldAbortApi = false;

    await page.route('**/api/**', async (route) => {
      const url = new URL(route.request().url());
      if (shouldAbortApi) {
        return route.abort('failed');
      }
      if (url.pathname.endsWith('/api/meta')) {
        return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(MOCK_META) });
      }
      return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({}) });
    });

    await page.goto('/simulado');
    await page.waitForFunction(() => typeof (window as unknown as { localDb?: unknown }).localDb !== 'undefined');

    // Grava pacote com status 'incomplete'
    await page.evaluate(async (ownerId) => {
      const win = window as unknown as { localDb: { simuladoPackages: { put: (item: unknown) => Promise<unknown> } } };
      await win.localDb.simuladoPackages.put({
        id: 'pkg_incomplete',
        owner_id: ownerId,
        name: 'Simulado Incompleto',
        config: {},
        question_ids: [1, 2, 3],
        questions_count: 3,
        details_count: 1, // Apenas 1 detalhe baixado
        images_count: 0,
        estimated_size_bytes: 500,
        status: 'incomplete',
        download_progress: 33,
        created_at: Date.now(),
        updated_at: Date.now(),
        expires_at: Date.now() + 86400000,
        version: 1,
      });
    }, TEST_OWNER);

    shouldAbortApi = true;
    await page.reload();

    // Tentar iniciar sem rede
    await expect(page.locator('button:has-text("Iniciar Simulado")')).toBeVisible({ timeout: 10000 });
    await page.click('button:has-text("Iniciar Simulado")');

    // Deve bloquear e permanecer na tela START
    await expect(page.locator('h2:has-text("Novo Simulado"), h2:has-text("Simulado Personalizado")')).toBeVisible({ timeout: 5000 });
  });

  test('rejeita pacote expirado após validade de 30 dias', async ({ page }) => {
    const TEST_OWNER = 'user_expired_test';
    await page.addInitScript((owner) => {
      localStorage.setItem('medquest_local_owner', owner);
    }, TEST_OWNER);

    let shouldAbortApi = false;

    await page.route('**/api/**', async (route) => {
      const url = new URL(route.request().url());
      if (shouldAbortApi) {
        return route.abort('failed');
      }
      if (url.pathname.endsWith('/api/meta')) {
        return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(MOCK_META) });
      }
      return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({}) });
    });

    await page.goto('/simulado');
    await page.waitForFunction(() => typeof (window as unknown as { localDb?: unknown }).localDb !== 'undefined');

    // Grava pacote expirado (expires_at no passado)
    await page.evaluate(async (ownerId) => {
      const win = window as unknown as { localDb: { simuladoPackages: { put: (item: unknown) => Promise<unknown> } } };
      await win.localDb.simuladoPackages.put({
        id: 'pkg_expired',
        owner_id: ownerId,
        name: 'Simulado Expirado',
        config: {},
        question_ids: [1, 2],
        questions_count: 2,
        details_count: 2,
        images_count: 0,
        estimated_size_bytes: 1000,
        status: 'ready',
        download_progress: 100,
        created_at: Date.now() - 40 * 86400000,
        updated_at: Date.now() - 40 * 86400000,
        expires_at: Date.now() - 10 * 86400000, // Expirado há 10 dias
        version: 1,
      });
    }, TEST_OWNER);

    shouldAbortApi = true;
    await page.reload();

    // Tentar iniciar offline
    await expect(page.locator('button:has-text("Iniciar Simulado")')).toBeVisible({ timeout: 10000 });
    await page.click('button:has-text("Iniciar Simulado")');

    // Deve bloquear início
    await expect(page.locator('h2:has-text("Novo Simulado"), h2:has-text("Simulado Personalizado")')).toBeVisible({ timeout: 5000 });
  });

  test('garante isolamento multiusuário de pacotes offline', async ({ page }) => {
    await page.route('**/api/**', async (route) => {
      const url = new URL(route.request().url());
      if (url.pathname.endsWith('/api/meta')) {
        return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(MOCK_META) });
      }
      return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({}) });
    });

    await page.goto('/simulado');
    await page.waitForFunction(() => typeof (window as unknown as { localDb?: unknown }).localDb !== 'undefined');

    // Popula pacote para o Usuário A
    await page.evaluate(async () => {
      const win = window as unknown as { localDb: { simuladoPackages: { put: (item: unknown) => Promise<unknown> } } };
      await win.localDb.simuladoPackages.put({
        id: 'pkg_user_a',
        owner_id: 'user_alpha',
        name: 'Simulado do Usuário Alpha',
        config: {},
        question_ids: [10],
        questions_count: 1,
        details_count: 1,
        images_count: 0,
        estimated_size_bytes: 500,
        status: 'ready',
        download_progress: 100,
        created_at: Date.now(),
        updated_at: Date.now(),
        expires_at: Date.now() + 86400000,
        version: 1,
      });
    });

    // Simula login do Usuário B
    await page.addInitScript(() => {
      localStorage.setItem('medquest_local_owner', 'user_beta');
    });
    await page.reload();

    // Verifica que o Usuário B não vê o pacote do Usuário A
    await expect(page.locator('text=Simulado do Usuário Alpha')).not.toBeVisible();
  });

  test('imagem indisponível não bloqueia pacote de questões e registra aviso', async ({ page }) => {
    const TEST_OWNER = 'user_img_integrity_test';
    await page.addInitScript((owner) => {
      localStorage.setItem('medquest_local_owner', owner);
    }, TEST_OWNER);

    await page.route('**/api/**', async (route) => {
      const url = new URL(route.request().url());
      if (url.pathname.endsWith('/api/meta')) {
        return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(MOCK_META) });
      }
      if (url.pathname.includes('/simulado')) {
        return route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify([{ id: 501, institution_code: 'USP-SP', year: 2026, area: 'Clínica Médica', subtema: 'Cardio' }]),
        });
      }
      if (url.pathname.endsWith('/api/questions/batch')) {
        return route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            questions: [
              {
                id: 501,
                stem: 'Questão com imagem indisponível no servidor',
                institution_code: 'USP-SP',
                year: 2026,
                area: 'Clínica Médica',
                subtema: 'Cardio',
                correct_letter: 'A',
                alternatives: [{ letter: 'A', text: 'Opção A' }],
                explanation: 'Explicação A',
                images: ['missing_ecg_scan.png'],
              },
            ],
          }),
        });
      }
      if (url.pathname.includes('missing_ecg_scan.png')) {
        // A imagem é complementar: uma falha não pode impedir as questões de funcionar offline.
        return route.fulfill({ status: 404, body: 'Image Not Found' });
      }
      return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({}) });
    });

    await page.goto('/simulado');
    await page.waitForFunction(() => typeof (window as unknown as { localDb?: unknown }).localDb !== 'undefined');

    // 1. Grava um pacote anterior compatível para garantir que o novo download o substitui.
    await page.evaluate(async (ownerId) => {
      const win = window as unknown as { localDb: { simuladoPackages: { put: (item: unknown) => Promise<unknown> } } };
      await win.localDb.simuladoPackages.put({
        id: 'pkg_previous_valid',
        owner_id: ownerId,
        name: 'Simulado Válido Anterior',
        config: {},
        question_ids: [100],
        questions_count: 1,
        details_count: 1,
        images_count: 0,
        estimated_size_bytes: 500,
        status: 'ready',
        download_progress: 100,
        created_at: Date.now() - 1000,
        updated_at: Date.now() - 1000,
        expires_at: Date.now() + 86400000,
        version: 2,
        shell_cached: true,
      });
    }, TEST_OWNER);

    // 2. Executa download que encontrará uma imagem indisponível.
    const downloadResult = await page.evaluate(async () => {
      const sp = (window as unknown as { simuladoPackage: {
        downloadSimuladoPackage: (cfg: unknown) => Promise<unknown>;
        getReadySimuladoPackage: () => Promise<{ id?: string } | null>;
        listSimuladoPackages: () => Promise<Array<{
          id: string;
          status: string;
          shell_cached?: boolean;
          image_failures_count?: number;
        }>>;
      } }).simuladoPackage;

      let caughtError = '';
      try {
        await sp.downloadSimuladoPackage({ questions_per_area: 1, institutions: ['USP-SP'] });
      } catch (err) {
        caughtError = err instanceof Error ? err.message : String(err);
      }
      const ready = await sp.getReadySimuladoPackage();
      const all = await sp.listSimuladoPackages();
      return {
        caughtError,
        readyId: ready?.id,
        totalPackages: all.length,
        packages: all.map(p => ({
          id: p.id,
          status: p.status,
          shellCached: p.shell_cached,
          imageFailures: p.image_failures_count,
        })),
      };
    });

    expect(downloadResult.caughtError).toBe('');
    expect(downloadResult.readyId).not.toBe('pkg_previous_valid');
    const downloadedPkg = downloadResult.packages.find(p => p.id !== 'pkg_previous_valid');
    expect(downloadedPkg?.status).toBe('ready');
    expect(downloadedPkg?.shellCached).toBe(true);
    expect(downloadedPkg?.imageFailures).toBe(1);
  });

  test('lote parcial de detalhes não grava status ready e impede início do simulado', async ({ page }) => {
    const TEST_OWNER = 'user_partial_batch_test';
    await page.addInitScript((owner) => {
      localStorage.setItem('medquest_local_owner', owner);
    }, TEST_OWNER);

    await page.route('**/api/**', async (route) => {
      const url = new URL(route.request().url());
      if (url.pathname.endsWith('/api/meta')) {
        return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(MOCK_META) });
      }
      if (url.pathname.includes('/simulado')) {
        return route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify([
            { id: 601, institution_code: 'USP-SP', year: 2026, area: 'Clínica Médica', subtema: 'Cardio' },
            { id: 602, institution_code: 'USP-SP', year: 2026, area: 'Cirurgia', subtema: 'Trauma' },
          ]),
        });
      }
      if (url.pathname.endsWith('/api/questions/batch')) {
        // Retorna apenas 1 detalhe ao invés dos 2 solicitados (lote parcial corrompido)
        return route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            questions: [
              {
                id: 601,
                stem: 'Questão 601 detalhada',
                institution_code: 'USP-SP',
                year: 2026,
                area: 'Clínica Médica',
                subtema: 'Cardio',
                correct_letter: 'A',
                alternatives: [{ letter: 'A', text: 'Opção A' }],
                explanation: 'Explicação A',
                images: [],
              },
            ],
          }),
        });
      }
      return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({}) });
    });

    await page.goto('/simulado');
    await page.waitForFunction(() => typeof (window as unknown as { localDb?: unknown }).localDb !== 'undefined');

    const downloadResult = await page.evaluate(async () => {
      const sp = (window as unknown as { simuladoPackage: {
        downloadSimuladoPackage: (cfg: unknown) => Promise<unknown>;
        getReadySimuladoPackage: () => Promise<unknown>;
        listSimuladoPackages: () => Promise<Array<{ id: string; status: string }>>;
      } }).simuladoPackage;

      let caughtError = '';
      try {
        await sp.downloadSimuladoPackage({ questions_per_area: 1, institutions: ['USP-SP'] });
      } catch (err) {
        caughtError = err instanceof Error ? err.message : String(err);
      }
      const ready = await sp.getReadySimuladoPackage();
      const all = await sp.listSimuladoPackages();
      return { caughtError, readyPkg: ready, totalPackages: all.length, statuses: all.map(p => p.status) };
    });

    expect(downloadResult.caughtError).toContain('Lote parcial de detalhes');
    expect(downloadResult.readyPkg).toBeNull();
    expect(downloadResult.statuses).toContain('incomplete');
  });

  test('OFFLINE_SUBMITTED com sync bem-sucedido transiciona para RESULTS e nunca START', async ({ page }) => {
    await page.route('**/api/**', async (route) => {
      const url = new URL(route.request().url());
      if (url.pathname.endsWith('/api/meta')) {
        return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(MOCK_META) });
      }
      return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({}) });
    });

    await page.goto('/simulado');
    await page.waitForFunction(() => typeof (window as unknown as { localDb?: unknown }).localDb !== 'undefined');

    // 1. Simula estado OFFLINE_SUBMITTED diretamente no localStorage com a chave v2 correta
    await page.evaluate(() => {
      const owner = localStorage.getItem('medquest_local_owner') || 'default';
      const key = `medquest_simulado_state_v2:${owner}`;
      const state = {
        version: 2,
        state: 'OFFLINE_SUBMITTED',
        queue: [
          { id: 901, institution_code: 'USP-SP', year: 2026, area: 'Clínica Médica', subtema: 'Cardio' }
        ],
        answers: { 901: 'A' },
        deadlineAt: Date.now() + 3600000,
        currentIndex: 0,
        resultsMap: {},
        flagged: {},
        force4Options: false,
        queueId: 'mock-sync-queue-id-901',
        sessionId: 'mock-session-901',
        plannedDurationSeconds: 3600,
        savedAt: Date.now(),
      };
      localStorage.setItem(key, JSON.stringify(state));
    });


    await page.reload();

    // 2. Clica em Continuar Andamento e confirma exibição da tela de Simulado Salvo Offline
    await expect(page.locator('button:has-text("Continuar Andamento")')).toBeVisible({ timeout: 10000 });
    await page.click('button:has-text("Continuar Andamento")');
    await expect(page.locator('text=Simulado Salvo Offline')).toBeVisible({ timeout: 10000 });

    // 3. Dispara evento sync-item-success com os resultados corrigidos
    await page.evaluate(() => {
      window.dispatchEvent(
        new CustomEvent('sync-item-success', {
          detail: {
            id: 'mock-sync-queue-id-901',
            endpoint: '/api/attempt/batch',
            method: 'POST',
            data: {
              results: [
                {
                  question_id: 901,
                  is_correct: true,
                  correct_letter: 'A',
                  explanation: 'Explicação da questão 901.',
                },
              ],
            },
          },
        })
      );
    });

    // 4. Confirma transição estrita para RESULTS e permanência estável
    await expect(page.locator('text=Nota Final')).toBeVisible({ timeout: 10000 });
    await expect(page.locator('text=100% de Acerto')).toBeVisible();

    // 5. Aguarda 2 segundos para garantir que nenhum temporizador ou checkAndSync residual reverta para START
    await page.waitForTimeout(2000);
    await expect(page.locator('text=Nota Final')).toBeVisible();
    await expect(page.locator('h2:has-text("Novo Simulado")')).not.toBeVisible();
  });

});
