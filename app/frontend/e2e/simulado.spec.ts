import { test, expect, Page } from '@playwright/test';

const MOCK_SIMULADO_QUESTIONS = [
  { id: 101, institution_code: "USP-SP", year: 2026, area: "Clínica Médica", subtema: "Cardiologia", topic: "Cardiologia" },
  { id: 102, institution_code: "USP-SP", year: 2026, area: "Cirurgia", subtema: "Trauma", topic: "Trauma" },
];

const MOCK_BATCH_DETAILS = {
  questions: [
    {
      id: 101,
      stem: "Paciente com dor torácica aguda em aperto. Qual a conduta inicial?",
      institution_code: "USP-SP",
      year: 2026,
      area: "Clínica Médica",
      subtema: "Cardiologia",
      topic: "Cardiologia",
      correct_letter: "A",
      alternatives: [
        { letter: "A", text: "ECG em até 10 minutos e monitorização" },
        { letter: "B", text: "Alta hospitalar com analgesia simples" },
        { letter: "C", text: "Tomografia computadorizada de crânio" },
        { letter: "D", text: "Ecocardiograma ambulatorial em 30 dias" },
      ],
    },
    {
      id: 102,
      stem: "Vítima de trauma automobilístico com hipotensão e macicez em hemitórax esquerdo.",
      institution_code: "USP-SP",
      year: 2026,
      area: "Cirurgia",
      subtema: "Trauma",
      topic: "Trauma",
      correct_letter: "B",
      alternatives: [
        { letter: "A", text: "Paracentese diagnóstica" },
        { letter: "B", text: "Drenagem torácica em selo d'água à esquerda" },
        { letter: "C", text: "Ressonância magnética de coluna" },
        { letter: "D", text: "Observação clínica em leito de enfermaria" },
      ],
    },
  ],
};

async function mockSimuladoApi(page: Page, onBatchSubmit?: () => void | Promise<void>) {
  await page.route('**/api/**', async (route) => {
    const url = new URL(route.request().url());
    if (url.pathname.endsWith('/api/meta')) {
      return route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          institutions: [{ institution_code: 'USP-SP', n: 10 }],
          years: [{ year: 2026, n: 10 }],
          areas: [{ area: 'Clínica Médica', n: 5 }, { area: 'Cirurgia', n: 5 }],
          subtemas: [],
        }),
      });
    }
    if (url.pathname.includes('/simulado/usp') || url.pathname.endsWith('/api/questions')) {
      return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(MOCK_SIMULADO_QUESTIONS) });
    }
    if (url.pathname.endsWith('/api/questions/batch')) {
      return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(MOCK_BATCH_DETAILS) });
    }
    if (url.pathname.endsWith('/api/questions/101')) {
      return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(MOCK_BATCH_DETAILS.questions[0]) });
    }
    if (url.pathname.endsWith('/api/questions/102')) {
      return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(MOCK_BATCH_DETAILS.questions[1]) });
    }
    if (url.pathname.endsWith('/api/attempt/batch')) {
      await onBatchSubmit?.();
      return route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          results: [
            { question_id: 101, is_correct: true, correct_letter: "A", explanation: "ECG precoce é mandatória na suspeita de SCA.", next_review_date: "2026-08-25T00:00:00Z" },
            { question_id: 102, is_correct: true, correct_letter: "B", explanation: "Hemotórax maciço/volumoso requer drenagem torácica imediata.", next_review_date: "2026-08-25T00:00:00Z" },
          ],
        }),
      });
    }
    return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({}) });
  });
}

test.describe('Fluxo Completo de Simulado', () => {
  test.beforeEach(async ({ context, page }) => {
    await context.addCookies([
      { name: 'medquest_demo', value: '1', domain: 'localhost', path: '/' }
    ]);
    await page.addInitScript(() => localStorage.setItem('medquest_onboarding_v1', 'done'));
  });

  test('inicia, responde e entrega simulado com exibição de resultados', async ({ page }) => {
    // 1. Mock de rotas do backend
    await page.route('**/api/**', async (route) => {
      const url = new URL(route.request().url());
      if (url.pathname.endsWith('/api/meta')) {
        return route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            institutions: [{ institution_code: 'USP-SP', n: 10 }],
            years: [{ year: 2026, n: 10 }],
            areas: [{ area: 'Clínica Médica', n: 5 }, { area: 'Cirurgia', n: 5 }],
            subtemas: [],
          }),
        });
      }
      if (url.pathname.includes('/simulado/usp') || url.pathname.endsWith('/api/questions')) {
        return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(MOCK_SIMULADO_QUESTIONS) });
      }
      if (url.pathname.endsWith('/api/questions/batch')) {
        return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(MOCK_BATCH_DETAILS) });
      }
      if (url.pathname.endsWith('/api/questions/101')) {
        return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(MOCK_BATCH_DETAILS.questions[0]) });
      }
      if (url.pathname.endsWith('/api/questions/102')) {
        return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(MOCK_BATCH_DETAILS.questions[1]) });
      }
      if (url.pathname.endsWith('/api/attempt/batch')) {
        return route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            results: [
              {
                question_id: 101,
                is_correct: true,
                correct_letter: "A",
                explanation: "ECG precoce é mandatória na suspeita de SCA.",
                next_review_date: "2026-08-25T00:00:00Z",
              },
              {
                question_id: 102,
                is_correct: true,
                correct_letter: "B",
                explanation: "Hemotórax maciço/volumoso requer drenagem torácica imediata.",
                next_review_date: "2026-08-25T00:00:00Z",
              },
            ],
          }),
        });
      }
      return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({}) });
    });

    // 2. Navegar para a tela de Simulado
    await page.goto('/simulado', { waitUntil: 'domcontentloaded' });
    await expect(page.locator('button:has-text("Iniciar Simulado")')).toBeVisible({ timeout: 10000 });

    // 3. Iniciar o simulado
    await page.click('button:has-text("Iniciar Simulado")');

    // 4. Responder à 1ª questão
    await expect(page.locator('text=Paciente com dor torácica')).toBeVisible({ timeout: 10000 });
    await page.click('text=ECG em até 10 minutos');

    // 5. Avançar para a 2ª questão
    await page.click('button:has-text("Próxima")');
    await expect(page.locator('text=Vítima de trauma')).toBeVisible({ timeout: 10000 });
    await page.click('text=Drenagem torácica em selo');

    // 6. Abrir modal de finalização do simulado
    await page.click('button:has-text("Finalizar Simulado")');

    // 7. Confirmar entrega no modal
    await expect(page.locator('button:has-text("Entregar Prova")')).toBeVisible({ timeout: 5000 });
    await page.click('button:has-text("Entregar Prova")');

    // 8. Validar tela final de resultados
    await expect(page.locator('text=Nota Final')).toBeVisible({ timeout: 10000 });
    await expect(page.locator('text=100% de Acerto')).toBeVisible();
  });

  test('retoma respostas e posição após recarregar a página', async ({ page }) => {
    await mockSimuladoApi(page);
    await page.goto('/simulado', { waitUntil: 'domcontentloaded' });
    await page.getByRole('button', { name: /Iniciar Simulado/ }).click();

    await expect(page.getByText('Paciente com dor torácica')).toBeVisible();
    await page.getByRole('button', { name: /ECG em até 10 minutos/ }).click();
    await page.getByRole('button', { name: /Próxima/ }).last().click();
    await page.getByRole('button', { name: /Drenagem torácica em selo/ }).click();
    await expect(page.getByRole('button', { name: /Drenagem torácica em selo/ })).toHaveAttribute('aria-pressed', 'true');

    await page.reload({ waitUntil: 'domcontentloaded' });
    await page.getByRole('button', { name: 'Continuar Simulado em Andamento' }).click();

    await expect(page.getByText('Vítima de trauma')).toBeVisible();
    await expect(page.getByRole('button', { name: /Drenagem torácica em selo/ })).toHaveAttribute('aria-pressed', 'true');
  });

  test('bloqueia entrega duplicada e oferece diálogo acessível', async ({ page }) => {
    let submissions = 0;
    await mockSimuladoApi(page, async () => {
      submissions++;
      await new Promise(resolve => setTimeout(resolve, 300));
    });

    await page.goto('/simulado', { waitUntil: 'domcontentloaded' });
    await page.getByRole('button', { name: /Iniciar Simulado/ }).click();
    await expect(page.getByText('Paciente com dor torácica')).toBeVisible();
    await page.getByRole('button', { name: /ECG em até 10 minutos/ }).click();
    await page.getByRole('button', { name: 'Finalizar Simulado' }).click();

    const dialog = page.getByRole('dialog', { name: 'Resumo por Área' });
    await expect(dialog).toBeVisible();
    await expect(dialog.getByRole('button', { name: 'Voltar à Prova' })).toBeFocused();
    await dialog.getByRole('button', { name: 'Entregar Prova' }).dblclick();

    await expect(page.getByText('Nota Final')).toBeVisible();
    expect(submissions).toBe(1);
  });

  test('mantém a prova utilizável em viewport mobile sem rolagem horizontal', async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await mockSimuladoApi(page);
    await page.goto('/simulado', { waitUntil: 'domcontentloaded' });
    await page.getByRole('button', { name: /Iniciar Simulado/ }).click();

    await expect(page.getByText('Paciente com dor torácica')).toBeVisible();
    const answer = page.getByRole('button', { name: /ECG em até 10 minutos/ });
    await answer.click();
    await expect(answer).toHaveAttribute('aria-pressed', 'true');

    const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
    expect(overflow).toBeLessThanOrEqual(1);
    await expect(page.getByRole('button', { name: 'Finalizar Simulado' })).toBeVisible();
  });
});
