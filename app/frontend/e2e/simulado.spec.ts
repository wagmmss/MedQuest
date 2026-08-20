import { test, expect } from '@playwright/test';

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

test.describe('Fluxo Completo de Simulado', () => {
  test.beforeEach(async ({ context }) => {
    await context.addCookies([
      { name: 'medquest_demo', value: '1', domain: 'localhost', path: '/' }
    ]);
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
    await page.goto('/simulado');
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
});
