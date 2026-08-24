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

test.beforeEach(async ({ page, context }) => {
  await context.addCookies([
    { name: 'medquest_demo', value: '1', domain: 'localhost', path: '/' },
    { name: 'medquest_demo', value: '1', domain: '127.0.0.1', path: '/' },
  ]);
  await page.addInitScript(() => localStorage.setItem('medquest_onboarding_v1', 'done'));
});

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

test('remove botão de IA e permite gerar flashcard após erro', async ({ page, context }) => {
  await context.addCookies([{ name: 'medquest_demo', value: '1', domain: 'localhost', path: '/' }]);
  
  let flashcardGenerated = false;
  await page.route('**/api/**', async route => {
    const path = new URL(route.request().url()).pathname;
    if (path.endsWith('/api/meta')) {
      return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(META) });
    }
    if (path.endsWith('/api/questions/1/attempt')) {
      return route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ is_correct: false, correct_letter: 'B', explanation: 'Tratamento individualizado.', next_review_date: null }),
      });
    }
    if (path.endsWith('/api/flashcards/preview')) {
      return route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          front: 'Neste caso clínico, a conduta indicada é {{c1::Mudança de estilo de vida}}.',
          back: 'Tratamento individualizado.',
          context: 'HAS'
        })
      });
    }
    if (path.endsWith('/api/flashcards/save') || path.endsWith('/api/flashcards/generate')) {
      flashcardGenerated = true;
      return route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: 42,
          question_id: 1,
          front: 'Neste caso clínico, a conduta indicada é {{c1::Mudança de estilo de vida}}.',
          back: 'Tratamento individualizado.',
          context: 'HAS'
        })
      });
    }
    if (path.endsWith('/api/questions/1')) {
      return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(QUESTION) });
    }
    if (path.endsWith('/api/questions')) {
      return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify([{ id: 1, institution_code: 'USP', year: 2025, area: 'Clínica Médica', subtema: 'HAS', topic: 'HAS' }]) });
    }
    return route.fulfill({ status: 200, contentType: 'application/json', body: '{}' });
  });

  await page.goto('/estudar?area=Cl%C3%ADnica+M%C3%A9dica', { waitUntil: 'domcontentloaded' });
  // Clica na alternativa errada (A)
  await page.getByRole('button', { name: /Internação imediata/ }).click();
  await page.getByRole('button', { name: 'Confirmar Resposta' }).click();

  // Verifica que o botão de explicar com IA NÃO existe
  await expect(page.getByRole('button', { name: /Explicar com IA/i })).not.toBeVisible();

  // Verifica e clica no botão de gerar flashcard
  const flashcardBtn = page.getByRole('button', { name: /Gerar Flashcard|Criar Flashcard/i });
  await expect(flashcardBtn).toBeVisible();
  await flashcardBtn.click();

  // Salva o flashcard editável
  const saveBtn = page.getByRole('button', { name: /Salvar Flashcard/i });
  await expect(saveBtn).toBeVisible();
  await saveBtn.click();

  // Verifica que o flashcard foi gerado e exibido
  await expect(page.getByText('Flashcard Salvo na Revisão Ativa!')).toBeVisible();
  await expect(page.getByText(/conduta indicada é/i)).toBeVisible();
  expect(flashcardGenerated).toBe(true);
});

test('clicar em voltar limpa a sessão e reload mantém na tela de filtros', async ({ page, context }) => {
  await context.addCookies([{ name: 'medquest_demo', value: '1', domain: 'localhost', path: '/' }]);
  await mockStudyApi(page);

  await page.goto('/estudar?area=Cl%C3%ADnica+M%C3%A9dica', { waitUntil: 'domcontentloaded' });
  await expect(page.getByText('Qual o tratamento inicial')).toBeVisible();

  // Clica em Voltar
  await page.getByRole('button', { name: '← Voltar' }).click();
  await expect(page.getByText('Filtros de Estudo')).toBeVisible();

  // Recarrega a página
  await page.reload({ waitUntil: 'domcontentloaded' });

  // Deve permanecer na tela de filtros sem carregar automaticamente a questão anterior
  await expect(page.getByText('Filtros de Estudo')).toBeVisible();
  await expect(page.getByText('Qual o tratamento inicial')).not.toBeVisible();
});

test('navegar para /estudar com sessão salva exibe banner de retomada na tela de filtros', async ({ page, context }) => {
  await context.addCookies([{ name: 'medquest_demo', value: '1', domain: 'localhost', path: '/' }]);
  await mockStudyApi(page);

  // Inicia uma sessão com filtros
  await page.goto('/estudar?area=Cl%C3%ADnica+M%C3%A9dica', { waitUntil: 'domcontentloaded' });
  await expect(page.getByText('Qual o tratamento inicial')).toBeVisible();
  const alternative = page.getByRole('button', { name: /Mudança de estilo de vida/ });
  await alternative.click();
  await expect(alternative).toHaveAttribute('aria-pressed', 'true');

  // Limpa sessionStorage (simulando troca de abas/navegação intencional para /estudar)
  await page.evaluate(() => sessionStorage.removeItem('medquest_active_quiz'));

  // Navega intencionalmente para /estudar
  await page.goto('/estudar', { waitUntil: 'domcontentloaded' });

  // Deve estar na tela de Filtros de Estudo exibindo o banner de retomada
  await expect(page.getByText('Filtros de Estudo')).toBeVisible();
  await expect(page.getByText('Sessão de Estudos em Andamento')).toBeVisible();
  await expect(page.getByRole('button', { name: 'Continuar Sessão' })).toBeVisible();

  // Clica para continuar a sessão anterior
  await page.getByRole('button', { name: 'Continuar Sessão' }).click();

  // Deve retornar para a questão com a alternativa selecionada
  await expect(page.getByText('Qual o tratamento inicial')).toBeVisible();
  await expect(page.getByRole('button', { name: /Mudança de estilo de vida/ })).toHaveAttribute('aria-pressed', 'true');
});
