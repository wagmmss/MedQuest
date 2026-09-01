import { test, expect } from '@playwright/test';

const MOCK_RADAR_DATA = {
  institution: {
    code: 'USP-SP',
    label: 'USP - São Paulo',
    total_available: 500,
    total_answered: 45,
    coverage: 0.09,
    total_attempts: 12,
    total_correct: 8,
    accuracy: 0.6667,
    ci_lower: 0.3906,
    ci_upper: 0.8619,
    sample_status: 'insufficient',
    areas: [
      {
        area: 'Clínica Médica',
        available: 100,
        answered: 10,
        coverage: 0.1,
        attempts: 12,
        correct: 8,
        accuracy: 0.6667,
        ci_lower: 0.3906,
        ci_upper: 0.8619,
        sample_status: 'insufficient',
        priority_topics: [
          {
            subtema: 'Cardiologia',
            available: 20,
            answered: 2,
            attempts: 3,
            correct: 1,
            accuracy: 0.3333,
            gap_type: 'low_accuracy',
            study_url: '/estudar?institution=USP-SP&area=Cl%C3%ADnica+M%C3%A9dica&subtema=Cardiologia&status=all&limit=20',
            simulado_url: '/simulado?institutions=USP-SP&area=Cl%C3%ADnica+M%C3%A9dica',
            review_url: '/revisao-ativa',
          },
        ],
      },
      {
        area: 'Cirurgia',
        available: 100,
        answered: 5,
        coverage: 0.05,
        attempts: 0,
        correct: 0,
        accuracy: null,
        ci_lower: null,
        ci_upper: null,
        sample_status: 'insufficient',
        priority_topics: [
          {
            subtema: 'Trauma Abdominal',
            available: 15,
            answered: 0,
            attempts: 0,
            correct: 0,
            accuracy: null,
            gap_type: 'unanswered',
            study_url: '/estudar?institution=USP-SP&area=Cirurgia&subtema=Trauma+Abdominal&status=all&limit=20',
            simulado_url: '/simulado?institutions=USP-SP&area=Cirurgia',
            review_url: '/revisao-ativa',
          },
        ],
      },
    ],
  },
  comparison: {
    type: 'global',
    code: null,
    label: 'Desempenho Geral',
    total_available: 2000,
    total_answered: 150,
    coverage: 0.075,
    total_attempts: 180,
    total_correct: 135,
    accuracy: 0.75,
    ci_lower: 0.6816,
    ci_upper: 0.8081,
    sample_status: 'reliable',
    areas: [
      {
        area: 'Clínica Médica',
        available: 400,
        answered: 40,
        coverage: 0.1,
        attempts: 60,
        correct: 45,
        accuracy: 0.75,
        ci_lower: 0.6277,
        ci_upper: 0.8422,
        sample_status: 'reliable',
        priority_topics: [],
      },
      {
        area: 'Cirurgia',
        available: 400,
        answered: 20,
        coverage: 0.05,
        attempts: 25,
        correct: 18,
        accuracy: 0.72,
        ci_lower: 0.5242,
        ci_upper: 0.8572,
        sample_status: 'forming',
        priority_topics: [],
      },
    ],
  },
  disclaimer: 'As métricas refletem exclusivamente o histórico resolvido no MedQuest.',
  sample_thresholds: {
    insufficient: '< 20 tentativas (conclusões bloqueadas)',
    forming: '20 a 49 tentativas',
    reliable: '≥ 50 tentativas',
  },
};

test.describe('Radar Comparativo de Bancas no Dashboard Analítico (/analise)', () => {
  test.beforeEach(async ({ context, page }) => {
    await context.addCookies([
      { name: 'medquest_demo', value: '1', domain: 'localhost', path: '/' },
    ]);
    await page.addInitScript(() => localStorage.setItem('medquest_onboarding_v1', 'done'));
  });

  test('renderiza seção do radar, alerta de amostra insuficiente e alterna entre gráfico e tabela acessível', async ({ page }) => {
    page.on('pageerror', err => console.log('PAGE ERROR:', err.message, err.stack));
    page.on('console', msg => console.log('BROWSER LOG:', msg.text()));

    await page.route('**/api/**', async (route) => {

      const url = new URL(route.request().url());
      if (url.pathname.includes('/stats/institution-radar')) {
        return route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(MOCK_RADAR_DATA),
        });
      }
      if (url.pathname.endsWith('/api/stats/timeline')) {
        return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify([]) });
      }
      if (url.pathname.endsWith('/api/stats/breakdown')) {
        return route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify([
            { key: 'USP-SP', label: 'USP - São Paulo', attempts: 12, correct: 8, accuracy: 0.67 },
            { key: 'UNICAMP', label: 'Unicamp', attempts: 5, correct: 4, accuracy: 0.8 },
          ]),
        });
      }
      if (url.pathname.endsWith('/api/stats/exam-readiness')) {
        return route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            institution: 'USP-SP',
            coverage: 0.09,
            answered: 45,
            available: 500,
            areas: [],
            disclaimer: 'Teste',
          }),
        });
      }
      return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({}) });
    });

    await page.goto('/analise');

    // 1. Confirma renderização do título da seção
    await expect(page.locator('h2:has-text("Radar Comparativo de Bancas")')).toBeVisible({ timeout: 10000 });

    // 2. Confirma exibição do alerta de amostra insuficiente (< 20 tentativas)
    await expect(page.locator('text=Amostra em estágio inicial (12 tentativas)')).toBeVisible();
    await expect(page.locator('text=Com menos de 20 tentativas nesta instituição')).toBeVisible();

    // 3. Confirma exibição do gráfico nativo com intervalo de Wilson
    await expect(page.locator('text=Acurácia e Intervalo de Incerteza (95% CI) por Área')).toBeVisible();
    await expect(page.locator('svg[aria-label="Gráfico de acurácia por área para USP - São Paulo"]')).toBeVisible();

    // 4. Alterna para visualização em Tabela Acessível

    await page.click('button[aria-label="Visualização em tabela acessível"]');

    // 5. Confirma colunas e valores na tabela semântica
    const table = page.locator('table[role="table"]');
    await expect(table).toBeVisible();
    await expect(table.getByRole('columnheader', { name: 'Grande Área' })).toBeVisible();
    await expect(table.getByRole('columnheader', { name: 'Intervalo de Incerteza (95% CI)' })).toBeVisible();
    await expect(table.getByRole('rowheader', { name: 'Clínica Médica' })).toBeVisible();
    await expect(table.locator('text=[39% – 86%]')).toBeVisible();
    await expect(table.locator('text=Amostra Insuficiente (12 tent.)')).toBeVisible();


    // 6. Confirma cartões de Ações Imediatas em até 2 cliques
    const radarSection = page.locator('section:has-text("Radar Comparativo de Bancas")');
    await expect(radarSection.locator('text=Ações Imediatas para Fechar Lacunas em USP - São Paulo')).toBeVisible();
    await expect(radarSection.locator('h4:has-text("Cardiologia")')).toBeVisible();

    // 7. Confirma atributos e URLs dos botões de ação direta
    const studyButton = radarSection.locator('a:has-text("Estudar Tema")').first();
    await expect(studyButton).toBeVisible();
    await expect(studyButton).toHaveAttribute('href', /.*\/estudar\?institution=USP-SP.*/);

    const simuladoButton = radarSection.locator('a:has-text("Simulado")').first();
    await expect(simuladoButton).toBeVisible();
    await expect(simuladoButton).toHaveAttribute('href', /.*\/simulado\?institutions=USP-SP.*/);

    // 8. Confirma disparo não-bloqueante da telemetria de ação autenticada ao interagir
    let trackedAction: string | null = null;
    await page.route('**/api/stats/institution-radar/action', async (route) => {
      const postData = route.request().postDataJSON();
      trackedAction = postData?.action;
      return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ success: true }) });
    });

    await studyButton.click();
    expect(trackedAction).toBe('study');
  });
});

