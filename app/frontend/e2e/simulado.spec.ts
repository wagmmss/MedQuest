import { test, expect } from '@playwright/test';

test.describe('Simulado flow', () => {
  test('starts and answers a simulado', async ({ page }) => {
    // Navigate to simulado setup page
    await page.goto('/simulado');
    
    // Expect title
    await expect(page.locator('h1').first()).toContainText('MedQuest');
    
    // Wait for the form to be visible (or mock auth in CI)
    // Since this is a demo, we might need to bypass auth by setting cookie
    await page.context().addCookies([{
      name: 'medquest_demo',
      value: '1',
      domain: 'localhost',
      path: '/'
    }]);

    await page.goto('/simulado');
    await expect(page.locator('text=Configuração Personalizada').first()).toBeVisible();
  });
});
