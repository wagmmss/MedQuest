import { test, expect, Page } from '@playwright/test';

const META = {
  total_questions: 1,
  answered_questions: 0,
  institutions: [{ institution_code: "USP", n: 1 }],
  years: [{ year: 2025, n: 1 }],
  areas: [{ area: "Clínica Médica", n: 1 }],
  subtemas: [{ subtema: "HAS", n: 1 }],
  sources: [],
  specialties: [],
};

const QUESTION = {
  id: 1,
  stem: "Qual o tratamento inicial da hipertensão arterial?",
  institution_code: "USP",
  institution_label: "USP",
  year: 2025,
  area: "Clínica Médica",
  subtema: "HAS",
  topic: "HAS",
  correct_letter: "B",
  alternatives: [
    { letter: "A", text: "Internação imediata para todos" },
    { letter: "B", text: "Mudança de estilo de vida e tratamento individualizado" },
  ],
};

async function mockStudyApi(
  page: Page,
  onAttempt?: () => void | Promise<void>,
  failFirstDetail = false,
) {
  let detailRequests = 0;
  await page.route('**/api/**', async route => {
    const path = new URL(route.request().url()).pathname;
    if (path.endsWith('/api/meta')) {
      return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(META) });
    }
    if (path.endsWith('/api/questions/1/attempt')) {
      await onAttempt?.();
      return route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ is_correct: true, correct_letter: 'B', explanation: 'Tratamento individualizado.', next_review_date: null }),
      });
    }
    if (path.endsWith('/api/questions/1')) {
      detailRequests++;
      if (failFirstDetail && detailRequests === 1) {
        return route.fulfill({ status: 503, contentType: 'application/json', body: '{"error":"temporary"}' });
      }
      return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(QUESTION) });
    }
    if (path.endsWith('/api/questions')) {
      return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify([{ id: 1, institution_code: 'USP', year: 2025, area: 'Clínica Médica', subtema: 'HAS', topic: 'HAS' }]) });
    }
    return route.fulfill({ status: 200, contentType: 'application/json', body: '{}' });
  });
}

test('retoma questão e alternativa ainda não enviada após reload', async ({ page, context }) => {
  await context.addCookies([{ name: 'medquest_demo', value: '1', domain: 'localhost', path: '/' }]);
  await mockStudyApi(page);

  await page.goto('/estudar?area=Cl%C3%ADnica+M%C3%A9dica', { waitUntil: 'domcontentloaded' });
  const alternative = page.getByRole('button', { name: /Mudança de estilo de vida/ });
  await alternative.click();
  await expect(alternative).toHaveAttribute('aria-pressed', 'true');

  await page.goto('/estudar?area=Cl%C3%ADnica+M%C3%A9dica', { waitUntil: 'domcontentloaded' });

  await expect(page.getByText('Qual o tratamento inicial')).toBeVisible();
  await expect(page.getByRole('button', { name: /Mudança de estilo de vida/ })).toHaveAttribute('aria-pressed', 'true');
});

test('impede envio duplicado da mesma tentativa por clique duplo', async ({ page, context }) => {
  await context.addCookies([{ name: 'medquest_demo', value: '1', domain: 'localhost', path: '/' }]);
  let attempts = 0;
  await mockStudyApi(page, async () => {
    attempts++;
    await new Promise(resolve => setTimeout(resolve, 300));
  });

  await page.goto('/estudar?area=Cl%C3%ADnica+M%C3%A9dica', { waitUntil: 'domcontentloaded' });
  await page.getByRole('button', { name: /Mudança de estilo de vida/ }).click();
  await page.getByRole('button', { name: 'Confirmar Resposta' }).dblclick();

  await expect(page.getByText('Resposta Correta!')).toBeVisible();
  expect(attempts).toBe(1);
});

test('mostra erro recuperável quando uma questão falha ao carregar', async ({ page, context }) => {
  await context.addCookies([{ name: 'medquest_demo', value: '1', domain: 'localhost', path: '/' }]);
  await mockStudyApi(page, undefined, true);

  await page.goto('/estudar?area=Cl%C3%ADnica+M%C3%A9dica', { waitUntil: 'domcontentloaded' });
  await expect(page.getByRole('alert').filter({ hasText: 'Erro ao carregar a questão' })).toBeVisible();
  await page.getByRole('button', { name: 'Tentar novamente' }).click();

  await expect(page.getByText('Qual o tratamento inicial')).toBeVisible();
});
