import { test, expect } from '@playwright/test';

test.describe('i18n locale routing', () => {
  test('redirects root to /en', async ({ page }) => {
    await page.goto('/');
    await expect(page).toHaveURL(/\/en/);
  });

  test('locale switcher changes to French', async ({ page }) => {
    await page.goto('/en');
    // Click the language switcher button (FR)
    const langSwitcher = page.getByRole('button', { name: /fr/i });
    await langSwitcher.click();
    await expect(page).toHaveURL(/\/fr/);
  });

  test('French locale renders French content', async ({ page }) => {
    await page.goto('/fr');
    // Navbar should contain French translations
    // French Navbar.home = "Accueil", Navbar.explore = "Explorer"
    await expect(page.locator('nav')).toContainText(/Accueil|Explorer/);
  });

  test('API routes are not locale-prefixed', async ({ page }) => {
    const response = await page.goto('/api/stripe/webhook');
    // Should NOT redirect to /en/api/...
    expect(page.url()).not.toContain('/en/api/');
    expect(page.url()).not.toContain('/fr/api/');
  });

  test('login page works under locale', async ({ page }) => {
    await page.goto('/en/login');
    // Login form should render — Stack Auth SignIn component renders a form
    await expect(page.locator('form, [data-testid="sign-in"], input[type="email"], input[name="email"]').first()).toBeVisible({ timeout: 10000 });
  });
});
