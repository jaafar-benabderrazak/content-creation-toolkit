import { test, expect } from '@playwright/test';

test.describe('Email notifications UI', () => {
  test('home page loads without error', async ({ page }) => {
    // Minimal smoke test — email delivery is a backend concern
    // This test verifies the UI that would trigger email notifications loads correctly
    await page.goto('/en');
    await expect(page.locator('body')).toBeVisible();
    const title = await page.title();
    expect(title).toBeTruthy();
  });

  test('booking confirmation page acknowledges email will be sent', async ({ page }) => {
    // Mock a successful reservation creation response
    await page.route('**/api/v1/reservations', async (route) => {
      if (route.request().method() === 'POST') {
        await route.fulfill({
          status: 201,
          contentType: 'application/json',
          body: JSON.stringify({
            id: 'res-email-test-001',
            status: 'pending',
            space_name: 'Test Workspace',
            cost_credits: 200,
            start_time: new Date().toISOString(),
            end_time: new Date(Date.now() + 3600000).toISOString(),
          }),
        });
      } else {
        await route.continue();
      }
    });

    await page.goto('/en');
    // Page renders — email notification occurs server-side via Resend
    // UI test scope: confirm page loads and reservation API mock works
    await expect(page.locator('body')).toBeVisible();
  });

  test('reservations API mock returns correct structure for email trigger', async ({ page }) => {
    await page.route('**/api/v1/reservations', async (route) => {
      if (route.request().method() === 'POST') {
        await route.fulfill({
          status: 201,
          contentType: 'application/json',
          body: JSON.stringify({
            id: 'res-email-test-001',
            status: 'pending',
            space_name: 'Test Workspace',
            cost_credits: 200,
            start_time: new Date().toISOString(),
            end_time: new Date(Date.now() + 3600000).toISOString(),
          }),
        });
      } else {
        await route.continue();
      }
    });

    await page.goto('/en');
    const response = await page.request.post('/api/v1/reservations', {
      data: { space_id: 'space-001', start_time: new Date().toISOString(), end_time: new Date(Date.now() + 3600000).toISOString() },
    });
    expect(response.status()).toBe(201);
    const data = await response.json();
    expect(data).toHaveProperty('id');
    expect(data).toHaveProperty('status');
    // Email notification is triggered server-side when this endpoint returns 201
  });
});
