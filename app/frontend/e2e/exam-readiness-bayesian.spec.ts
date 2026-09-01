import { test, expect } from '@playwright/test';

test.describe('Prontidão de Prova Bayesiana por Edital', () => {
  test('renderiza prontidão estimada, intervalo de credibilidade e fatores determinantes sem promessa de aprovação', async ({ page }) => {
    // Intercepta e mocka as chamadas de API no frontend
    await page.route('**/api/**', async (route) => {

      const url = new URL(route.request().url());

      if (url.pathname.endsWith('/api/stats/exam-readiness')) {
        return route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            institution: 'USP-SP',
            institution_label: 'USP - São Paulo',
            coverage: 0.25,
            answered: 25,
            available: 100,
            readiness_score: 0.684,
            ci_lower: 0.542,
            ci_upper: 0.812,
            evidence_status: 'insufficient',
            edital_profile: {
              institution_code: 'USP-SP',
              institution_label: 'USP - São Paulo',
              version: '2025.1',
              validity_period: '2025-2026',
              curation_source: 'Curadoria Técnica MedQuest — Prova de Acesso Direto R1 (FMUSP)',
              status: 'validated',
              weights: {
                'Clínica Médica': 0.20,
                'Cirurgia': 0.20,
                'Ginecologia e Obstetrícia': 0.20,
                'Pediatria': 0.20,
                'Medicina Preventiva': 0.20,
              },
            },
            areas: [
              {
                area: 'Clínica Médica',
                available: 20,
                answered: 10,
                coverage: 0.5,
                attempts: 12,
                correct: 9,
                accuracy: 0.75,
                posterior_mean: 0.7143,
                ci_lower: 0.478,
                ci_upper: 0.95,
                weight: 0.20,
                sample: 'limited',
                sample_status: 'forming',
                action: '/estudar?area=Cl%C3%ADnica+M%C3%A9dica&status=new&limit=20',
              },
              {
                area: 'Cirurgia',
                available: 20,
                answered: 2,
                coverage: 0.1,
                attempts: 2,
                correct: 1,
                accuracy: 0.5,
                posterior_mean: 0.5,
                ci_lower: 0.1,
                ci_upper: 0.9,
                weight: 0.20,
                sample: 'limited',
                sample_status: 'insufficient',
                action: '/estudar?area=Cirurgia&status=new&limit=20',
              },
              {
                area: 'Ginecologia e Obstetrícia',
                available: 20,
                answered: 5,
                coverage: 0.25,
                attempts: 5,
                correct: 4,
                accuracy: 0.8,
                posterior_mean: 0.7143,
                ci_lower: 0.38,
                ci_upper: 0.95,
                weight: 0.20,
                sample: 'limited',
                sample_status: 'forming',
                action: '/estudar?area=Ginecologia+e+Obstetr%C3%ADcia&status=new&limit=20',
              },
              {
                area: 'Pediatria',
                available: 20,
                answered: 4,
                coverage: 0.2,
                attempts: 4,
                correct: 3,
                accuracy: 0.75,
                posterior_mean: 0.6667,
                ci_lower: 0.3,
                ci_upper: 0.95,
                weight: 0.20,
                sample: 'limited',
                sample_status: 'insufficient',
                action: '/estudar?area=Pediatria&status=new&limit=20',
              },
              {
                area: 'Medicina Preventiva',
                available: 20,
                answered: 4,
                coverage: 0.2,
                attempts: 2,
                correct: 1,
                accuracy: 0.5,
                posterior_mean: 0.5,
                ci_lower: 0.1,
                ci_upper: 0.9,
                weight: 0.20,
                sample: 'limited',
                sample_status: 'insufficient',
                action: '/estudar?area=Medicina+Preventiva&status=new&limit=20',
              },
            ],
            key_factors: [
              {
                area: 'Cirurgia',
                impact: 'Peso de 20% no edital com apenas 2 tentativa(s) observada(s).',
                recommendation: 'Resolver pelo menos 3 questão(ões) em Cirurgia para calibrar a evidência.',
                factor_type: 'low_sample',
              },
            ],
            limitations: [
              'A prontidão estimada reflete exclusivamente as questões resolvidas no MedQuest sob o perfil de edital configurado.',
              'Não constitui probabilidade de aprovação, garantia de classificação ou nota de corte oficial.',
            ],
            disclaimer: 'Prontidão estimada calculada via modelo Beta-Binomial ponderado por edital. Não reflete probabilidade de aprovação.',
          }),
        });
      }

      if (url.pathname.endsWith('/api/stats/timeline')) {
        return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify([]) });
      }
      if (url.pathname.endsWith('/api/stats/weak-topics')) {
        return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify([]) });
      }
      if (url.pathname.endsWith('/api/stats/breakdown')) {
        return route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify([
            { key: 'USP-SP', label: 'USP - São Paulo', attempts: 25, correct: 18, accuracy: 0.72 },
          ]),
        });
      }
      if (url.pathname.endsWith('/api/stats/distractors')) {
        return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify([]) });
      }
      if (url.pathname.endsWith('/api/stats/predictive-score')) {
        return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ projected_score: 68, target_score: 80, areas: [] }) });
      }
      if (url.pathname.endsWith('/api/stats/at-risk')) {
        return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify([]) });
      }
      if (url.pathname.endsWith('/api/stats/learning-profile')) {
        return route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            summary: { total_studied: 25, retention_rate: 0.8, reviews_due: 0, target_score: null, exam_date: null },
            topics: [],
            method: { deterministic: true, signals: [] },
          }),
        });
      }
      if (url.pathname.endsWith('/api/stats/institution-radar')) {
        return route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            institution: {
              code: 'USP-SP',
              label: 'USP - São Paulo',
              total_attempts: 25,
              total_correct: 18,
              accuracy: 0.72,
              sample_status: 'forming',
              areas: [],
            },
            comparison: null,
          }),
        });
      }

      return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({}) });
    });


    page.on('pageerror', err => console.log('PAGE ERROR:', err.message, err.stack));
    page.on('console', msg => console.log('BROWSER LOG:', msg.text()));

    await page.goto('/analise');


    // 1. Confirma renderização do cabeçalho da seção
    await expect(page.locator('h2:has-text("Prontidão Estimada por Edital")')).toBeVisible({ timeout: 15000 });

    // 2. Seleciona o edital USP-SP para disparar fetch com os dados mockados
    const select = page.locator('select[aria-label="Selecionar edital da instituição"]');
    await expect(select).toBeVisible();
    await select.selectOption('USP-SP');

    const section = page.locator('section:has-text("Prontidão Estimada por Edital")');

    // 3. Confirma indicador de prontidão e intervalo de credibilidade
    await expect(section.locator('text=68%')).toBeVisible({ timeout: 10000 });
    await expect(section.locator('text=[54% – 81%]')).toBeVisible();

    // 4. Confirma badges de evidência e status do perfil
    await expect(section.locator('text=Evidência Inicial')).toBeVisible();
    await expect(section.locator('text=Validado')).toBeVisible();
    await expect(section.locator('text=USP - São Paulo (v2025.1)')).toBeVisible();


    // 4. Confirma aviso educativo de amostra preliminar
    await expect(section.locator('text=Amostra Preliminar')).toBeVisible();
    await expect(section.locator('text=Com poucas tentativas nas áreas ponderadas')).toBeVisible();

    // 5. Confirma fatores determinantes e recomendações
    await expect(section.locator('text=Fatores Determinantes para Calibrar a Evidência')).toBeVisible();
    await expect(section.locator('text=Resolver pelo menos 3 questão(ões) em Cirurgia')).toBeVisible();

    // 6. Confirma botões de ação para estudar área
    const studyButtons = section.locator('a:has-text("Estudar Área")');
    await expect(studyButtons.first()).toBeVisible();
    await expect(studyButtons.first()).toHaveAttribute('href', /.*\/estudar\?area=.*/);

    // 7. Garante ausência estrita de termos proibidos (sem promessa de aprovação)
    const pageContent = await page.content();
    expect(pageContent).not.toContain('chance de passar');
    expect(pageContent).not.toContain('probabilidade de aprovação');
    expect(pageContent).not.toContain('garantia de aprovação');
  });
});
